"""
lab_answer_keyV4.py
===================
Step 1 of the Answer Key Pipeline - Improved Parser + Vision Analysis.

PURPOSE
-------
Processes all instructor lab templates in the templates/ folder and produces
one structured answer key file per lab.  For each answer slot the script:

  - Extracts typed text answers directly from the DOCX XML
  - For screenshot-only slots: sends the image to Claude via the Batch API
      * Terminal / command output / tables of values  ->  transcribed as text
      * Charts, graphs, topology diagrams             ->  kept as image

Two-phase design (mirrors grading_agentV8 / batch_retrieveV2):
  Phase 1 - SUBMIT:   Unpack templates, extract slots, submit vision batch,
                       save state file.
  Phase 2 - RETRIEVE: Poll batch until complete, write final answer key files.

IMPROVEMENTS OVER V3
---------------------
  1. Preamble guard - numbered items before the Objectives section are
     never treated as question labels.  Eliminates false Q3/Q4 captures
     from the screenshot instruction numbered list at the top of the lab.

  2. Explicit screenshot slot detection - detects Cisco lab screenshot
     label patterns directly:
       "Part 1h [Insert a screenshot...]"
       "Part 2f Screenshot [Insert a screenshot...]"
       "Part 3 Step 2c Screenshot [Insert a screenshot...]"
     Extracts Part, Step, and sub-letter from the label text itself
     rather than relying on surrounding paragraph numbering.

  3. Explicit text answer slot detection - detects:
       "[Insert your answer below]"
       "Usernames [Insert your answer ->>] 5"
     Reads the answer value from the same line (after ->>) or from the
     immediately following non-empty paragraph.

  4. Minimum image size filter - skips images smaller than MIN_IMG_W x
     MIN_IMG_H pixels.  Eliminates logos, icons, and decorative images
     that would otherwise be sent to the vision API unnecessarily.

  5. Instruction image guard - images that appear before the Objectives /
     Part 1 section header are skipped regardless of label context.

USAGE
-----
  python lab_answer_keyV4.py

Run the script once for Phase 1 (submit).
Run the same command again for Phase 2 (retrieve results + write keys).
Phase is auto-detected via presence of the state file.

TEMPLATE FILE NAMING CONVENTION (set by lead instructor)
  2026SU_Lab_#_-_ILM.docx

DEPENDENCIES
  pip install anthropic python-dotenv Pillow

API KEY
  Loaded from I:\\Visual_Studio_Code\\.env  ->  ANTHROPIC_API_KEY=sk-...

VERSION HISTORY
  V1  Initial release - text + screenshot extraction, Markdown output
  V2  Batch API vision analysis - terminal screenshots transcribed to text;
      charts/graphs kept as images; two-phase submit/retrieve architecture
  V3  Improved parser:
        - Preamble guard prevents false question labels before Objectives
        - Direct screenshot slot label detection ("Part Nx [Insert screenshot]")
        - Direct text answer slot detection ("[Insert your answer below]")
        - Minimum image size filter (skips logos/icons < 400x200 px)
        - Instruction image guard (skips images before Part 1 section)
"""

import os
import re
import sys
import glob
import json
import time
import base64
import shutil
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(r"I:\Visual_Studio_Code\.env")
import anthropic

# Force UTF-8 output on Windows
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# -- Configuration -------------------------------------------------------------

TEMPLATES_DIR  = "templates"
OUTPUT_DIR     = os.path.join(TEMPLATES_DIR, "answer_keys")
STATE_FILE     = os.path.join(TEMPLATES_DIR, "answer_keys", "answer_key_batch_state.json")

VISION_MODEL   = "claude-sonnet-4-6"
POLL_INTERVAL  = 60   # seconds between batch status checks

# Images smaller than these dimensions are skipped (logos, icons, bullets)
MIN_IMG_W = 400   # pixels
MIN_IMG_H = 200   # pixels

# -- Vision prompt --------------------------------------------------------------

VISION_PROMPT = """You are reading an instructor answer key screenshot from a Cisco networking lab.

Examine this image carefully and decide:

CASE A - The image shows text-based content that can be fully represented as text:
  - Terminal / command-line output
  - Command results (ping, traceroute, ipconfig, ifconfig, show commands, etc.)
  - Tables of IP addresses, MAC addresses, port numbers, or similar values
  - Wireshark packet capture windows or TCP stream windows
  - Kibana log entry details or dashboard text values
  - Configuration text or file contents
  - Any output where the meaningful information IS the text shown

CASE B - The image shows visual content that CANNOT be fully represented as text:
  - Network topology diagrams
  - Charts or graphs (bar charts, line graphs, pie charts)
  - Diagrams with shapes, arrows, or layout that carries meaning
  - Dashboard overview screenshots where the visual layout is the answer
  - Any image where the visual structure itself is the answer

Respond with ONLY a JSON object - no other text, no markdown fences:

For CASE A (text content):
{
  "type": "text",
  "content": "exact transcription of all text shown in the image, preserving line breaks with \\n"
}

For CASE B (visual content):
{
  "type": "image",
  "description": "one sentence describing what the image shows"
}

Transcribe EVERY character you can read for Case A.  Accuracy matters because
this will be used as the grading answer key."""

# -- XML namespace helpers ------------------------------------------------------

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
A = "http://schemas.openxmlformats.org/drawingml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"


def para_text(p):
    return "".join(t.text or "" for t in p.iter(f"{{{W}}}t")).strip()


def get_img_rids(p):
    rids = []
    for blip in p.iter(f"{{{A}}}blip"):
        rid = blip.get(f"{{{R}}}embed", "")
        if rid:
            rids.append(rid)
    for img in p.iter("{urn:schemas-microsoft-com:vml}imagedata"):
        rid = img.get(f"{{{R}}}id", "")
        if rid:
            rids.append(rid)
    return rids


def load_rels(unpack_dir):
    path = os.path.join(unpack_dir, "word", "_rels", "document.xml.rels")
    rels = {}
    if os.path.exists(path):
        for rel in ET.parse(path).getroot():
            rels[rel.get("Id", "")] = rel.get("Target", "")
    return rels


def resolve_media(rid, rels, unpack_dir):
    """Return absolute path to media file, or None if not found."""
    target = rels.get(rid, "")
    if not target:
        return None
    path = os.path.join(unpack_dir, "word", target)
    return path if os.path.exists(path) else None


def image_dimensions(path):
    """Return (width, height) or (0, 0) on failure."""
    try:
        from PIL import Image
        return Image.open(path).size
    except Exception:
        return (0, 0)


# -- Screenshot slot label patterns --------------------------------------------
# Cisco lab templates use lines like:
#   "Part 1h [Insert a screenshot...]"
#   "Part 2f Screenshot [Insert a screenshot...]"
#   "Part 3 Step 2c Screenshot for Questions 1 and 2 [Insert a screenshot...]"
#   "Part 4 Step 3c [Insert a screenshot...]"
#
# Capture groups: part_num, step_num (optional), sub_letter (optional)

RE_SCREENSHOT_LABEL = re.compile(
    r"Part\s+(\d+)\s*"           # "Part 3"
    r"(?:Step\s+(\d+))?"         # optional "Step 2"
    r"([a-zA-Z]?)"               # optional sub-letter "c"
    r"[^[]*"                     # any words (Screenshot, Question N, etc.)
    r"\[Insert\s+(?:a\s+)?screenshot",
    re.IGNORECASE,
)

# Text answer slot: "[Insert your answer below]" or "Field [Insert your answer ->>] value"
RE_ANSWER_SLOT = re.compile(r"\[Insert your answer", re.IGNORECASE)

# Inline answer after ->>:  "Usernames [Insert your answer ->>]  5"
RE_INLINE_ANSWER = re.compile(r"\[Insert your answer\s*->>\]\s*(.*)", re.IGNORECASE)

# Objectives / Part 1 section header - marks end of preamble
RE_OBJECTIVES = re.compile(r"^(?:Objectives|Part\s+1\s*:)", re.IGNORECASE)


# -- Core template parser -------------------------------------------------------

def parse_template(docx_path, unpack_base):
    """
    Unpack DOCX and extract answer slots using improved V3 parser.

    Returns (slots, unpack_dir) where each slot is:
      {
        "lab_num":      str,
        "label":        str,   # display label e.g. "Part 1 | Step h"
        "slot_type":    str,   # "screenshot" | "text_answer"
        "text":         str,   # typed answer text (may be "")
        "images":       [str], # absolute paths to extracted image files
      }
    """
    lab_name   = Path(docx_path).stem
    unpack_dir = os.path.join(unpack_base, lab_name)

    if os.path.exists(unpack_dir):
        shutil.rmtree(unpack_dir)
    os.makedirs(unpack_dir, exist_ok=True)

    with zipfile.ZipFile(docx_path, "r") as z:
        z.extractall(unpack_dir)

    m       = re.search(r"Lab_(\d+)_", os.path.basename(docx_path))
    lab_num = m.group(1) if m else "?"

    doc  = ET.parse(os.path.join(unpack_dir, "word", "document.xml"))
    body = doc.getroot().find(f".//{{{W}}}body")
    rels = load_rels(unpack_dir)

    # Flatten body -> sequential paragraph list (body paras + table cell paras)
    all_paras = []
    for child in body:
        tag = child.tag.split("}")[-1]
        if tag == "p":
            all_paras.append(child)
        elif tag == "tbl":
            for row in child.iter(f"{{{W}}}tr"):
                for cell in row.iter(f"{{{W}}}tc"):
                    all_paras.extend(cell.iter(f"{{{W}}}p"))

    slots   = []
    n       = len(all_paras)
    in_body = False   # True after Objectives / Part 1 header - preamble guard

    i = 0
    while i < n:
        p    = all_paras[i]
        text = para_text(p)

        # -- Preamble guard: wait for Objectives / Part 1 ------------------
        if not in_body:
            if RE_OBJECTIVES.search(text):
                in_body = True
            i += 1
            continue

        # -- Screenshot slot label detection -------------------------------
        ss_match = RE_SCREENSHOT_LABEL.search(text)
        if ss_match:
            part_num  = ss_match.group(1)
            step_num  = ss_match.group(2) or ""
            sub_letter = ss_match.group(3).lower() if ss_match.group(3) else ""

            # Build label
            label_parts = [f"Part {part_num}"]
            if step_num:
                label_parts.append(f"Step {step_num}")
            if sub_letter:
                label_parts.append(sub_letter)
            label = " | ".join(label_parts)

            # The image is on the NEXT non-empty paragraph
            img_paths = []
            j = i + 1
            while j < n and j < i + 4:
                next_text = para_text(all_paras[j])
                rids      = get_img_rids(all_paras[j])
                if rids:
                    for rid in rids:
                        path = resolve_media(rid, rels, unpack_dir)
                        if path:
                            w, h = image_dimensions(path)
                            if w >= MIN_IMG_W and h >= MIN_IMG_H:
                                img_paths.append(path)
                    break   # found the image paragraph
                if next_text and not RE_ANSWER_SLOT.search(next_text):
                    break   # hit real content before finding an image
                j += 1

            slots.append({
                "lab_num":   lab_num,
                "label":     label,
                "slot_type": "screenshot",
                "text":      "",
                "images":    img_paths,
            })
            i += 1
            continue

        # -- Text answer slot detection -------------------------------------
        if RE_ANSWER_SLOT.search(text):
            # Build label from surrounding context (best effort)
            # Look backward for the nearest question text (numbered item or
            # question sentence ending in "?")
            label = _find_nearest_question_label(all_paras, i)

            # Check for inline answer after ->>
            inline_match = RE_INLINE_ANSWER.search(text)
            if inline_match:
                # Answer is on the same line: "Usernames [Insert your answer ->>] 5"
                field_name = text.split("[")[0].strip()
                answer_val = inline_match.group(1).strip()
                if field_name:
                    label = f"{label} | {field_name}" if label else field_name
                slots.append({
                    "lab_num":   lab_num,
                    "label":     label,
                    "slot_type": "text_answer",
                    "text":      answer_val,
                    "images":    [],
                })
            else:
                # Answer is on the next non-empty, non-instruction paragraph
                answer_text = ""
                j = i + 1
                while j < n and j < i + 5:
                    ntext = para_text(all_paras[j])
                    if ntext and not _is_instruction_or_prompt(ntext):
                        answer_text = ntext
                        break
                    j += 1

                slots.append({
                    "lab_num":   lab_num,
                    "label":     label,
                    "slot_type": "text_answer",
                    "text":      answer_text,
                    "images":    [],
                })
            i += 1
            continue

        i += 1

    return slots, unpack_dir


# -- Label helpers --------------------------------------------------------------

def _find_nearest_question_label(all_paras, current_idx):
    """
    Look backward from current_idx to find the nearest question text.
    Returns a label string like "Part 3 | Step 2 | Q1" or a question snippet.
    """
    # First check for a Part N Step N pattern in the preceding 15 paras
    part_step_re = re.compile(
        r"(?:Part\s+(\d+).*?Step\s+(\d+)|Step\s+(\d+).*?Part\s+(\d+))", re.I
    )
    question_re = re.compile(r"^\s*(\d+)\.\s+(.+\?)\s*$")

    # Track Part/Step seen most recently before this index
    current_part = None
    current_step = None
    question_txt = None

    for j in range(max(0, current_idx - 20), current_idx):
        t = para_text(all_paras[j])
        # Part header
        pm = re.search(r"\bPart\s+(\d+)\b", t, re.I)
        if pm and len(t) < 80:
            current_part = pm.group(1)
            current_step = None
        # Step header
        sm = re.search(r"\bStep\s+(\d+)\b", t, re.I)
        if sm and len(t) < 120:
            current_step = sm.group(1)
        # Numbered question
        qm = question_re.match(t)
        if qm:
            question_txt = f"Q{qm.group(1)}"

    label_parts = []
    if current_part:
        label_parts.append(f"Part {current_part}")
    if current_step:
        label_parts.append(f"Step {current_step}")
    if question_txt:
        label_parts.append(question_txt)

    return " | ".join(label_parts) if label_parts else "Answer Slot"


def _is_instruction_or_prompt(text):
    """Return True if text is an instruction line or another answer prompt."""
    if RE_ANSWER_SLOT.search(text):
        return True
    if RE_SCREENSHOT_LABEL.search(text):
        return True
    PREFIXES = (
        "screenshot on", "previous screenshot", "remember", "note:",
        "caution:", "warning:", "click", "navigate", "scroll", "open",
        "from your", "use find", "close the", "part 1", "part 2",
        "part 3", "part 4", "step ", "extra credit",
    )
    tl = text.lower()
    if any(tl.startswith(p) for p in PREFIXES):
        return True
    if len(text) > 250:
        return True
    return False


# -- Image helpers --------------------------------------------------------------

def image_to_base64(img_path, max_width=1400):
    """Load image, resize if needed, return (base64_str, media_type)."""
    from PIL import Image
    import io
    img = Image.open(img_path).convert("RGB")
    if img.width > max_width:
        ratio = max_width / img.width
        img   = img.resize((max_width, int(img.height * ratio)), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    buf.seek(0)
    return base64.standard_b64encode(buf.read()).decode("utf-8"), "image/jpeg"


# -- Phase 1: Submit ------------------------------------------------------------

def phase1_submit(template_files, unpack_base, output_dir, state_path):
    print("\n-- Phase 1: Parsing templates and submitting vision batch --\n")

    all_slots_by_lab = {}
    screenshot_jobs  = []

    for docx_path in template_files:
        m = re.search(r"Lab_(\d+)_", os.path.basename(docx_path))
        if not m:
            print(f"  [SKIP] Cannot parse lab number: {os.path.basename(docx_path)}")
            continue
        lab_num = m.group(1)
        print(f"  Parsing Lab {lab_num}...", end=" ", flush=True)

        slots, _ = parse_template(docx_path, unpack_base)
        all_slots_by_lab[lab_num] = slots

        ss_slots  = [s for s in slots if s["slot_type"] == "screenshot"]
        txt_slots = [s for s in slots if s["slot_type"] == "text_answer"]
        print(f"{len(slots)} slots  ({len(ss_slots)} screenshot, {len(txt_slots)} text)")

        for slot in ss_slots:
            for img_idx, img_path in enumerate(slot["images"]):
                safe = re.sub(r"[^a-zA-Z0-9]", "_", slot["label"])
                # Use a global counter suffix to guarantee uniqueness across
                # all labs even when two labs produce identical label strings
                job_seq = len(screenshot_jobs)
                cid  = f"lab{lab_num}_{safe}_img{img_idx}_{job_seq:03d}"
                screenshot_jobs.append({
                    "custom_id": cid,
                    "lab_num":   lab_num,
                    "label":     slot["label"],
                    "img_path":  img_path,
                    "img_idx":   img_idx,
                })

    if not screenshot_jobs:
        print("\n  No screenshot slots found - writing text-only answer keys.\n")
        os.makedirs(output_dir, exist_ok=True)
        for lab_num, slots in sorted(all_slots_by_lab.items()):
            images_dir = os.path.join(output_dir, f"Lab_{lab_num}_Answer_Key_images")
            write_answer_key(slots, lab_num, output_dir, images_dir, {}, {})
        return

    print(f"\n  {len(screenshot_jobs)} screenshot(s) queued for vision analysis")

    # Build batch requests
    batch_requests = []
    skipped = 0
    for job in screenshot_jobs:
        try:
            b64, media_type = image_to_base64(job["img_path"])
        except Exception as e:
            print(f"  [WARN] Cannot encode {job['custom_id']}: {e}")
            skipped += 1
            continue
        batch_requests.append({
            "custom_id": job["custom_id"],
            "params": {
                "model":      VISION_MODEL,
                "max_tokens": 1500,
                "messages": [{
                    "role": "user",
                    "content": [
                        {"type": "image",
                         "source": {"type": "base64",
                                    "media_type": media_type,
                                    "data": b64}},
                        {"type": "text", "text": VISION_PROMPT},
                    ],
                }],
            },
        })

    if skipped:
        print(f"  [WARN] {skipped} image(s) skipped due to encoding errors")
    if not batch_requests:
        print("  [ERROR] No valid batch requests to submit.")
        sys.exit(1)

    print(f"\n  Submitting batch with {len(batch_requests)} vision request(s)...")
    client = anthropic.Anthropic()
    batch  = client.messages.batches.create(requests=batch_requests)
    print(f"  OK Batch ID: {batch.id}  |  Status: {batch.processing_status}")

    # Serialise state
    os.makedirs(os.path.dirname(state_path), exist_ok=True)
    state = {
        "batch_id":        batch.id,
        "slots_by_lab":    {
            lab: [dict(s, images=s["images"]) for s in slots]
            for lab, slots in all_slots_by_lab.items()
        },
        "screenshot_jobs": screenshot_jobs,
        "submitted_at":    time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    with open(state_path, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)

    print(f"\n  State saved -> {state_path}")
    print("\n-- Phase 1 complete ------------------------------------------")
    print(f"\n  Batch is processing.  Re-run this script to retrieve results.")
    print(f"  Typical completion time: under 1 hour.\n")


# -- Phase 2: Retrieve ----------------------------------------------------------

def phase2_retrieve(state_path, output_dir):
    with open(state_path, encoding="utf-8") as f:
        state = json.load(f)

    batch_id        = state["batch_id"]
    slots_by_lab    = state["slots_by_lab"]
    screenshot_jobs = state["screenshot_jobs"]

    print(f"\n-- Phase 2: Retrieving vision batch results --\n")
    print(f"  Batch ID:     {batch_id}")
    print(f"  Submitted at: {state['submitted_at']}")

    client = anthropic.Anthropic()

    while True:
        batch  = client.messages.batches.retrieve(batch_id)
        status = batch.processing_status
        c      = batch.request_counts
        print(f"  [{time.strftime('%H:%M:%S')}] {status}"
              f"  succeeded={c.succeeded}  processing={c.processing}"
              f"  errored={c.errored}")
        if status == "ended":
            break
        print(f"  Waiting {POLL_INTERVAL}s...")
        time.sleep(POLL_INTERVAL)

    print(f"\n  Collecting results...")
    vision_results = {}
    for result in client.messages.batches.results(batch_id):
        cid = result.custom_id
        if result.result.type == "succeeded":
            raw = "".join(
                b.text for b in result.result.message.content if hasattr(b, "text")
            )
            try:
                clean  = re.sub(r"```(?:json)?|```", "", raw).strip()
                parsed = json.loads(clean)
                vision_results[cid] = parsed
            except json.JSONDecodeError:
                vision_results[cid] = {"type": "text", "content": raw.strip()}
        else:
            err = getattr(result.result, "error", "unknown")
            print(f"  [ERROR] {cid}: {err}")
            vision_results[cid] = {"type": "text",
                                    "content": f"[Vision analysis failed: {err}]"}

    job_lookup = {
        (j["lab_num"], j["label"], j["img_idx"]): j["custom_id"]
        for j in screenshot_jobs
    }

    os.makedirs(output_dir, exist_ok=True)
    print(f"\n  Writing answer key files...\n")
    for lab_num in sorted(slots_by_lab.keys()):
        slots      = slots_by_lab[lab_num]
        images_dir = os.path.join(output_dir, f"Lab_{lab_num}_Answer_Key_images")
        key_path   = write_answer_key(
            slots, lab_num, output_dir, images_dir,
            vision_results, job_lookup,
        )
        print(f"  OK Lab {lab_num}  ->  {os.path.basename(key_path)}")

    os.remove(state_path)
    print(f"\n  State file removed.")
    print("\n-- Phase 2 complete ------------------------------------------")
    print(f"\n  Answer keys written to: {output_dir}")
    print("  Review each Lab_#_Answer_Key.md and correct any errors")
    print("  before proceeding to Step 2 (add grading notes).\n")


# -- Write answer key Markdown --------------------------------------------------

def write_answer_key(slots, lab_num, output_dir, images_dir,
                     vision_results, job_lookup):
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(images_dir, exist_ok=True)

    key_path = os.path.join(output_dir, f"Lab_{lab_num}_Answer_Key.md")
    lines    = [
        f"# Lab {lab_num} Answer Key\n",
        "_Generated by lab_answer_keyV3.py - Review and correct before use in grading._\n",
        "---\n",
    ]

    for slot in slots:
        label     = slot["label"]
        text      = slot["text"].strip()
        imgs      = slot["images"]
        slot_type = slot["slot_type"]

        lines.append(f"## {label}\n")

        # -- Text answer slot -----------------------------------------------
        if slot_type == "text_answer":
            if text:
                lines.append(f"**ANSWER TEXT:**\n```\n{text}\n```\n")
            else:
                lines.append(
                    "**ANSWER TEXT:** _(empty in template - instructor must fill in)_\n"
                )

        # -- Screenshot slot ------------------------------------------------
        elif slot_type == "screenshot":
            if not imgs:
                lines.append(
                    "**SCREENSHOT:** _(no image found after label - check template)_\n"
                )
            else:
                for img_idx, img_path in enumerate(imgs):
                    cid    = job_lookup.get((slot["lab_num"], label, img_idx))
                    vision = vision_results.get(cid) if cid else None

                    if vision and vision.get("type") == "text":
                        transcribed = vision.get("content", "").strip()
                        lines.append(
                            "**ANSWER TEXT** _(transcribed from screenshot - verify accuracy)_:\n"
                            f"```\n{transcribed}\n```\n"
                        )

                    elif vision and vision.get("type") == "image":
                        desc = vision.get("description", "Visual content")
                        img_path_out = _copy_image(
                            img_path, images_dir, lab_num, label, img_idx
                        )
                        if img_path_out:
                            rel = os.path.relpath(img_path_out, output_dir)
                            lines.append("**ANSWER IMAGE** _(visual - cannot be text)_:\n")
                            lines.append(f"![{label}]({rel})\n")
                            lines.append(f"_AI description: {desc}_\n")
                            lines.append(
                                "_Instructor: review image and add grading notes below._\n"
                            )
                        else:
                            lines.append(f"**ANSWER IMAGE:** [Error copying image]\n")

                    else:
                        # No vision result - copy image with review note
                        img_path_out = _copy_image(
                            img_path, images_dir, lab_num, label, img_idx
                        )
                        if img_path_out:
                            rel = os.path.relpath(img_path_out, output_dir)
                            lines.append(
                                "**ANSWER SCREENSHOT** _(vision analysis not available)_:\n"
                            )
                            lines.append(f"![{label}]({rel})\n")
                            lines.append(
                                "_Instructor: open image and add expected answer text below._\n"
                            )
                        else:
                            lines.append("**ANSWER SCREENSHOT:** [Error copying image]\n")

        lines.append("---\n")

    with open(key_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return key_path


def _copy_image(src_path, images_dir, lab_num, label, img_idx):
    """Copy image to images_dir with a clean filename. Returns dest path or None."""
    try:
        ext      = Path(src_path).suffix.lower() or ".jpg"
        safe_lbl = re.sub(r"[^a-zA-Z0-9]", "_", label)
        dst_name = f"Lab{lab_num}_{safe_lbl}_img{img_idx}{ext}"
        dst_path = os.path.join(images_dir, dst_name)
        shutil.copy2(src_path, dst_path)
        return dst_path
    except Exception:
        return None


# -- Main -----------------------------------------------------------------------

def main():
    script_dir    = os.path.dirname(os.path.abspath(__file__))
    templates_dir = os.path.join(script_dir, TEMPLATES_DIR)
    output_dir    = os.path.join(script_dir, OUTPUT_DIR)
    state_path    = os.path.join(script_dir, STATE_FILE)
    unpack_base   = os.path.join(script_dir, "temp_unpack")

    print("\nLab Answer Key Generator - V3")
    print("=" * 60)

    if os.path.exists(state_path):
        print("\nState file found - resuming Phase 2 (batch retrieval).")
        phase2_retrieve(state_path, output_dir)
        return

    print("\nNo state file - starting Phase 1.")

    pattern        = os.path.join(templates_dir, "2026SU_Lab_*_-_ILM.docx")
    template_files = sorted(glob.glob(pattern))

    if not template_files:
        print(f"\n[ERROR] No templates found in: {templates_dir}")
        print(f"  Expected: 2026SU_Lab_#_-_ILM.docx")
        sys.exit(1)

    print(f"\nFound {len(template_files)} template(s):")
    for f in template_files:
        print(f"  {os.path.basename(f)}")

    print(f"\nThis will submit a Batch API vision job for all screenshot slots.")
    confirm = input("Proceed? (y/n): ").strip().lower()
    if confirm != "y":
        print("Cancelled.")
        sys.exit(0)

    phase1_submit(template_files, unpack_base, output_dir, state_path)

    if os.path.exists(unpack_base):
        shutil.rmtree(unpack_base)


if __name__ == "__main__":
    main()
