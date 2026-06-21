# CyberOps Associate — Automated Grading Pipeline

A Python-based automated grading system for Cisco CyberOps Associate (CCNA CyberOps) lab submissions. Built to process student `.docx` and `.pdf` lab files, extract embedded screenshots, evaluate answers against a rubric, and generate structured professional feedback documents — all at SOC Level 2 documentation standards.

---

## Project Overview

| Component | Description |
|-----------|-------------|
| **Course** | Cisco CyberOps Associate |
| **Submissions** | Student lab files (`.docx` / `.pdf`) via NDG Networking Academy |
| **Rubric Source** | Lead instructor grading notes (`.txt`) + answer templates (`.docx`) |
| **Output** | Structured feedback `.docx` per student, `grade_log.csv` |
| **API** | Anthropic Claude (via `anthropic` Python package) |
| **Storage** | `I:\Visual_Studio_Code\` (external USB drive) |

---

## Milestones Accomplished

### Phase 1 — Manual Grading Proof of Concept
- Established grading workflow using Claude Projects (web interface)
- Graded Lab 2 manually by uploading student `.docx` files
- Discovered that text extraction alone fails for screenshot-heavy submissions — tables appear empty
- **Solution found:** Unpack `.docx` → parse `word/_rels/document.xml.rels` for rId-to-filename mapping → extract images in document order from `word/document.xml` using regex `r:embed="(rId\d+)"`
- Identified that the first ~11 images in each lab template are instructor-provided examples; student screenshots begin after those
- Generated first color-coded PDF grade report using ReportLab `SimpleDocTemplate` with `platypus` components

### Phase 2 — Grading Logic & Rubric Design
- Established the **SOC Professional Standard scoring convention**: 20 points added to raw scores to reflect the learning curve while grading at professional Level 2 SOC documentation standards
- Every feedback document automatically includes a SOC Standard Notice
- Defined **academic integrity rule**: verbatim copying from Instructor Manual is flagged and penalized; repeat offense = score of 1 for the entire lab
- Identified critical grading logic for screenshot-gated questions:
  - When a lab uses the statement *"Your screenshot is not used to answer the questions below..."*, text answers are graded independently of screenshots
  - Missing screenshots are flagged as a **separate deduction** — they do not zero out the text answer points
  - This required a prompt engineering fix before Labs 4 and 5 were graded
- Defined structured feedback format:
  - Executive summary with color-coded per-question scores
  - Detailed feedback **only** for incorrect answers (four-part format: *What You Submitted → What Was Wrong → Why It Matters → How To Fix It*)
  - Correct answers shown with a checkmark only
  - Both raw score and adjusted score displayed
  - Agent version stamp on every document

### Phase 3 — Pipeline Architecture Design
- Decided on full system design before writing any code (folder structure, naming conventions, roster management, feedback format, API strategy)
- Chose **Option B folder structure**: one script serves multiple course folders
- Established **lab numbers** (not module numbers) throughout all naming and logic
- Designed `grade_log.csv` schema: initials, student name, lab, raw score, adjusted score, regrade version, agent version
- Planned sequential queue processing with version tracking for regraded submissions

### Phase 4 — Script Development

#### `intakeV2.py` ✅ Current Version
- Interactive intake with roster-driven student identification
- Loads `roster.csv` with `utf-8-sig` encoding (handles Excel BOM characters)
- Alphabetically sorted roster display
- Duplicate initials detection with visual flag
- Prompts for lab number (not module number)
- Renames files to `INITIALS_lab##_pending.ext`
- Moves files to queue folder
- Logs all intake events to `intake_log.csv`

#### `grading_agentV4.py` ✅ Current Version
- Watches queue folder every 30 seconds (continuous loop)
- Renders PDF pages as images using `pdf2image` and Poppler
  - Poppler path hardcoded: `C:\poppler\poppler-26.02.0\Library\bin` (bypasses Windows PATH issues)
- Verifies minimum page count before grading
- Sends rendered page images to Claude API for evaluation
- Writes structured feedback `.docx` to `grades/lab##/` folder
- Progress indicators during processing
- Retry logic on API failures
- Regrade version tracking in output filenames and `grade_log.csv`

#### `reprocessV1.py` ✅ Current Version
- Moves processed files back to the queue by lab number
- Appends regrade version suffix (`r2`, `r3`, etc.) to filenames
- Supports queuing multiple labs in a single session
- Integrates with `grade_log.csv` version tracking

---

## Folder Structure

```
I:\Visual_Studio_Code\
├── .env                        # API key (NEVER commit to GitHub)
├── CyberOps_Fall2026\
│   ├── roster.csv              # Student roster (initials, full name)
│   ├── intake\                 # Drop zone for raw student submissions
│   ├── queue\                  # Pending files for grading agent
│   ├── processed\              # Files graded; moved here after grading
│   └── grades\
│       ├── lab02\              # Feedback .docx files for Lab 2
│       ├── lab04\
│       └── grade_log.csv       # Master log of all graded submissions
├── intakeV2.py
├── grading_agentV4.py
└── reprocessV1.py
```

---

## Script Summary — Latest Versions

| Script | Version | Purpose |
|--------|---------|---------|
| `intakeV2.py` | V2 | File intake, rename, queue |
| `grading_agentV4.py` | V4 | Queue-watching grading agent |
| `reprocessV1.py` | V1 | Requeue files for regrading |

---

## Key Dependencies

```bash
pip install anthropic python-dotenv python-docx pdf2image reportlab
```

| Package | Use |
|---------|-----|
| `anthropic` | Claude API calls |
| `python-dotenv` | Load `.env` API key |
| `python-docx` | Write feedback `.docx` files |
| `pdf2image` | Render PDF pages as images for API |
| `reportlab` | PDF grade reports (ReportLab `SimpleDocTemplate` + `platypus`) |
| `Poppler` | Required by `pdf2image` on Windows |

**Poppler (Windows):** Download and extract to `C:\poppler\`. Hardcoded path in grading agent avoids Windows PATH issues.

---

## Grading Standards

### Scoring Convention
- Raw score is evaluated against rubric at **SOC Level 2 professional documentation standards**
- **+20 points** added to raw score = adjusted score shown on feedback
- Both scores appear on every feedback document

### Academic Integrity
- Verbatim copying from the Instructor Manual → penalty applied, flagged in feedback
- Repeat offense → **score of 1 for the entire lab** (no exceptions)

### Screenshot-Gated Questions
- If the lab template contains: *"Your screenshot is not used to answer the questions below..."* — text answers are graded on their own merit
- Missing screenshots are a **separate deduction**, not a zero for the question
- This distinction is enforced in the grading agent prompt

---

## Known Limitations / Future Work

- [ ] Screenshot extraction currently requires `.docx` unpack method; PDFs sent as rendered images
- [ ] Poppler path is hardcoded for Windows — parameterize for portability
- [ ] No GUI; all interaction via terminal
- [ ] `grade_log.csv` is per-course-folder; no cross-course aggregation yet
- [ ] Automated detection of instructor template images (currently assumes first 11 images are template)

---

## Development Approach

All scripts follow an **architecture-first** workflow:

1. Full system design completed (folder structure, naming, roster management, feedback format, API strategy) before any code is written
2. Scripts built iteratively with version suffixes (`V1`, `V2`, `V3`) to track evolution
3. Each version is retained; only the latest version is run in production

---

*Built for Cisco CyberOps Associate instruction. Grading standards reflect SOC Level 2 professional documentation expectations.*
