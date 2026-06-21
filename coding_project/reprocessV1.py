"""
reprocessV1.py  —  Reprocess / Regrade Script
Cisco Cyber Operations Grading System

Usage:
    python reprocessV1.py

Workflow:
    1. Prompts you to select which course folder to work with
    2. Asks which lab number to regrade
    3. Scans processed/ folder for all files matching that lab
    4. Shows list of files found and confirms before moving
    5. Renames files with next regrade version (r2, r3, etc.)
    6. Moves files to queue/ for grading agent to pick up
    7. Asks if you want to queue another lab
    8. Repeat until done — then start grading_agentV3.py

File naming:
    processed/AF_lab04_pending.pdf         original
    processed/AF_lab04_pending_r2.pdf      first regrade
    queue/AF_lab04_pending_r2.pdf          moved to queue
    grades/lab04/AF_lab04_feedback_r2.docx regraded feedback

Dependencies:
    No additional packages required beyond standard library
"""

import re
import sys
import shutil
from pathlib import Path

# ── Configuration ─────────────────────────────────────────────────────────────
BASE_DIR   = Path("I:/Visual_Studio_Code")
TOTAL_LABS = 14
# ──────────────────────────────────────────────────────────────────────────────


def pick_course_folder() -> Path:
    """Scan BASE_DIR for course subfolders and prompt instructor to pick one."""
    course_folders = sorted([
        f for f in BASE_DIR.iterdir()
        if f.is_dir() and (f / "roster.csv").exists()
    ])

    if not course_folders:
        print(f"\n  ERROR: No course folders found under {BASE_DIR}")
        sys.exit(1)

    print("\n  ── Course Folders Found ────────────────────────────")
    for i, folder in enumerate(course_folders, start=1):
        print(f"  {i:>3}.  {folder.name}")
    print("  ────────────────────────────────────────────────────")

    while True:
        raw = input("\n  Enter course number: ").strip()
        if raw.isdigit():
            num = int(raw)
            if 1 <= num <= len(course_folders):
                selected = course_folders[num - 1]
                confirm  = input(
                    f"  Confirm: {selected.name}  (y/n): "
                ).strip().lower()
                if confirm == "y":
                    return selected
                print("  Not confirmed.  Please re-enter.")
                continue
        print(f"  Invalid.  Enter a number between 1 and {len(course_folders)}.")


def pick_lab() -> str:
    """Prompt instructor to enter lab number. Returns zero-padded string."""
    while True:
        raw = input(f"\n  Enter lab number to regrade (1 – {TOTAL_LABS}): ").strip()
        if raw.isdigit():
            num = int(raw)
            if 1 <= num <= TOTAL_LABS:
                return f"{num:02d}"
        print(f"  Invalid.  Enter a number between 1 and {TOTAL_LABS}.")


def get_next_regrade_version(filename: str) -> str:
    """
    Determine the next regrade version suffix for a filename.

    Examples:
        AF_lab04_pending.pdf       ->  r2  (first regrade)
        AF_lab04_pending_r2.pdf    ->  r3  (second regrade)
        AF_lab04_pending_r3.pdf    ->  r4  (third regrade)
    """
    stem  = Path(filename).stem   # e.g. AF_lab04_pending_r2
    match = re.search(r'_r(\d+)$', stem)
    if match:
        current = int(match.group(1))
        return f"r{current + 1}"
    return "r2"   # first regrade


def build_new_filename(original: Path, next_version: str) -> str:
    """
    Build the new filename with regrade version inserted before extension.

    Examples:
        AF_lab04_pending.pdf     + r2  ->  AF_lab04_pending_r2.pdf
        AF_lab04_pending_r2.pdf  + r3  ->  AF_lab04_pending_r3.pdf
    """
    stem = original.stem
    ext  = original.suffix.lower()

    # Remove existing regrade suffix if present before adding new one
    stem = re.sub(r'_r\d+$', '', stem)
    return f"{stem}_{next_version}{ext}"


def find_lab_files(course_dir: Path, lab_str: str) -> list[Path]:
    """
    Scan processed/ folder for all submission files matching the lab number.
    Matches both original and previously regraded files.

    Matches:
        AF_lab04_pending.pdf
        AF_lab04_pending_r2.pdf
        AF_lab04_pending_r3.pdf
    """
    processed_dir = course_dir / "processed"
    if not processed_dir.exists():
        return []

    pattern = re.compile(
        rf'^[A-Z0-9]+_lab{lab_str}_pending',
        re.IGNORECASE
    )

    return sorted([
        f for f in processed_dir.iterdir()
        if f.is_file()
        and f.suffix.lower() in {".pdf", ".docx"}
        and pattern.match(f.name)
    ])


def queue_lab(course_dir: Path, lab_str: str) -> int:
    """
    Find all processed files for a lab, show them, confirm, then move to queue.
    Returns number of files queued.
    """
    lab_num = int(lab_str)
    files   = find_lab_files(course_dir, lab_str)

    if not files:
        print(f"\n  No processed files found for Lab {lab_num}.")
        print(f"  Check that processed/ folder contains files matching:")
        print(f"  [INITIALS]_lab{lab_str}_pending.*")
        return 0

    print(f"\n  ── Files Found for Lab {lab_num} ────────────────────")
    for i, f in enumerate(files, start=1):
        version = get_next_regrade_version(f.name)
        new_name = build_new_filename(f, version)
        print(f"  {i:>3}.  {f.name}")
        print(f"         → queue as: {new_name}")
    print(f"  ────────────────────────────────────────────────────")
    print(f"\n  Total: {len(files)} file(s) will be moved to queue.")

    confirm = input("\n  Move all to queue for regrading? (y/n): ").strip().lower()
    if confirm != "y":
        print("  Cancelled.  No files moved.")
        return 0

    queue_dir = course_dir / "queue"
    queue_dir.mkdir(exist_ok=True)

    moved = 0
    for f in files:
        next_version = get_next_regrade_version(f.name)
        new_name     = build_new_filename(f, next_version)
        dest         = queue_dir / new_name

        # Safety check — do not overwrite if already in queue
        if dest.exists():
            print(f"  WARNING: {new_name} already in queue — skipping.")
            continue

        shutil.move(str(f), str(dest))
        print(f"  ✓  {f.name}  →  {new_name}")
        moved += 1

    print(f"\n  {moved} file(s) moved to queue for Lab {lab_num}.")
    return moved


def main():
    print("\n" + "="*54)
    print("  Cisco Cyber Ops  —  Reprocess Script V1")
    print("="*54)

    course_dir  = pick_course_folder()
    total_queued = 0

    print(f"\n  Working in:  {course_dir.name}")

    while True:
        lab_str = pick_lab()
        queued  = queue_lab(course_dir, lab_str)
        total_queued += queued

        again = input(
            "\n  Queue another lab for regrading? (y/n): "
        ).strip().lower()
        if again != "y":
            break

    print(f"\n{'='*54}")
    print(f"  Done.  {total_queued} total file(s) queued for regrading.")
    print(f"  Start grading_agentV3.py to process the queue.")
    print(f"{'='*54}\n")


if __name__ == "__main__":
    main()
