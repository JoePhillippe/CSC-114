# Cisco CyberOps Automated Grading Pipeline

An AI-powered grading pipeline for Cisco Cyber Operations Associate labs. Built with Python and the Anthropic Claude API. Designed as a pilot for department-wide adoption of AI-assisted grading.

---

## Overview

This pipeline automates grading of student lab submissions for the Cisco CyberOps Associate course. Students submit labs as PDF or DOCX files through Canvas. The pipeline intakes submissions, renames them consistently, renders PDF pages as images, sends them to the Claude API for grading against an answer template and rubric, and produces a structured feedback document for each student.

The system was built iteratively by an IT instructor learning Python scripting and AI agent development. Each script version solves a real grading problem discovered in production use.

---

## Problem Statement

- 29 students per semester submitting 14 labs each
- Labs contain text answers AND screenshots pasted into Word then saved as PDF
- Manual grading via Claude.ai Projects hit context limits with a single student per chat
- Student files had non-unique names making batch processing impossible
- No consistent feedback format across submissions
- Grading to professional SOC Level 2 standards requires detailed, specific feedback

---

## Current Scripts

| Script | Purpose |
|---|---|
| `intakeV2.py` | Interactive intake — renames and queues student submissions |
| `grading_agentV6.py` | Renders PDFs as images and submits batch grading job |
| `batch_retrieveV2.py` | Runs continuously — retrieves completed batch results every 24 hours |
| `reprocessV1.py` | Moves processed files back to queue for regrading with version tracking |

---

## Solution Architecture

```
Canvas (manual download)
        ↓
   intake/                  ← raw student files dropped here
        ↓
  intakeV2.py               ← interactive intake script
        ↓
   queue/                   ← renamed files with consistent naming
        ↓
  grading_agentV6.py        ← renders PDFs, submits batch to Claude API
        ↓
  Anthropic Batch API       ← processes overnight, 50% cost savings
        ↓
  batch_retrieveV2.py       ← runs continuously, retrieves results every 24 hours
        ↓
  grades/lab##/             ← feedback DOCX per student per lab
        ↓
Canvas (manual upload)      ← attach feedback to student submission
```

---

## Daily Workflow

### Setting Up a New Semester
1. Create a course folder under `I:\Visual_Studio_Code\` — example: `CyberOps_Fall2026`
2. Place `roster.csv` inside the course folder
3. Place answer templates and grading notes in the `templates\` subfolder
4. All other folders are created automatically on first run

### Grading Day — Morning
```
# Step 1 — Download student submissions from Canvas manually
# Drop all downloaded files into:
#   I:\Visual_Studio_Code\CyberOps_Fall2026\intake\

# Step 2 — Run intake script
python intakeV2.py
# Select course folder
# For each file: enter student initials, confirm name, enter lab number
# Files move to queue\ with consistent naming: AF_lab02_pending.pdf
```

### Grading Day — After Intake
```
# Step 3 — Submit batch grading job
python grading_agentV6.py
# Select course folder
# Confirm submission of all queued files
# Script renders PDFs as images, submits to Anthropic Batch API
# Completes in minutes regardless of class size
# Submissions move to processed\
```

### Grading Day — Leave Running Overnight
```
# Step 4 — Start continuous retrieval watcher
python batch_retrieveV2.py
# Select course folder
# Script checks every 24 hours for completed batch results
# Writes feedback DOCX to grades\lab##\ when results arrive
# Stops automatically when all jobs are complete
# Press Ctrl+C to stop early — run again to resume
```

### Next Morning — Results Ready
```
grades\lab02\
    AF_lab02_feedback.docx
    AJ_lab02_feedback.docx
    AP_lab02_feedback.docx
    ...

# Step 5 — Upload feedback to Canvas
# Open each feedback DOCX and attach to the matching student submission
```

### Regrading Workflow
```
# When grading prompt is improved or screenshot detection changes:

# Step 1 — Queue labs for regrade
python reprocessV1.py
# Select course folder
# Enter lab number — example: 4
# Script shows all files found and renames them: AF_lab04_pending_r2.pdf
# Asks if you want to queue another lab
# Enter lab number or n to finish

# Step 2 — Submit regrade batch
python grading_agentV6.py

# Step 3 — Retrieve regraded results
python batch_retrieveV2.py
# Regraded feedback written as: AF_lab04_feedback_r2.docx
# Original AF_lab04_feedback.docx is preserved
```

---

## Scripts

### intakeV2.py
Interactive intake script. Drops into a terminal session where the instructor processes each downloaded student file one at a time.

**What it does:**
- Scans `intake/` folder for PDF and DOCX files
- Displays full class roster with duplicate initials flagged
- Instructor enters student initials — confirms full name before proceeding
- Asks for lab number
- Renames file to `INITIALS_lab##_pending.ext`
- Moves file to `queue/` folder
- Logs every intake to `intake_log.csv`
- Supports multiple course folders — selects at startup

**Why initials with confirmation:** Dyslexia-friendly design. Entering initials is faster and less error-prone than typing full names. The confirmation step shows the full name before any file is moved.

**Handles:**
- Excel BOM characters in roster.csv (utf-8-sig encoding)
- Duplicate initials flagged visually (AJ vs AJ2)
- Re-submission detection — warns if file already logged

---

### grading_agentV6.py
Batch submission agent. Renders all queued PDFs as images and submits them to the Anthropic Batch API in one job.

**What it does:**
- Scans `queue/` folder for pending files
- Renders each PDF page as a JPEG image at 150 DPI using pdf2image and Poppler
- Verifies minimum page count before submitting — moves failed PDFs to `failed/`
- Extracts answer-only content from the template DOCX (89% token reduction)
- Builds one API request per student with all page images
- Submits entire class as a single batch job
- Saves batch manifest to `batch_jobs.csv`
- Moves submitted files to `processed/`

**Why batch submission:** The Batch API processes jobs asynchronously within 24 hours at 50% of standard token cost. Submit before you leave, collect results next morning.

---

### batch_retrieveV2.py
Continuous retrieval script. Runs in the background checking for completed batch results every 24 hours.

**What it does:**
- Reads `batch_jobs.csv` for pending batch job IDs
- Checks Anthropic API for job completion status every 24 hours
- Downloads results when ready
- Parses structured grading response
- Calculates score by summing individual question scores (not Claude's total estimate)
- Writes feedback DOCX to `grades/lab##/`
- Logs results to `grade_log.csv`
- Updates `batch_jobs.csv` status to completed
- Stops automatically when all pending jobs are complete
- Safe to stop and restart — completed results are always skipped
- Shows exact time of next check after each cycle

---

### reprocessV1.py
Regrade script. Moves processed files back to queue for regrading with version tracking.

**What it does:**
- Scans `processed/` folder for files matching a lab number
- Renames files with regrade version suffix: `r2`, `r3`, etc.
- Moves files back to `queue/` for the grading agent to pick up
- Asks if you want to queue another lab — queue multiple labs in one session
- Supports chaining: run reprocessV1.py then grading_agentV6.py

---

## Feedback Document Structure

Every feedback DOCX contains:

```
[Agent version stamp and date]

GRADING NOTE — PROFESSIONAL SOC STANDARD
[Explanation of 20-point adjustment and why SOC standards apply]

STUDENT FEEDBACK REPORT
Student | Lab | Date

EXECUTIVE SUMMARY
Raw Score:       72 / 96
Adjusted Score:  92 / 96  (96%)

QUESTION SCORE MATRIX
Q: Part 1 Step 3b  | 6/6  | Correct
Q: Part 2 Step 1g  | 4/6  | Source subfield over-expanded
Q: Part 2 Step 2b  | 6/6  | Correct
[one line per question — green for correct, red for deducted]

DETAILED FEEDBACK
[Only for questions with deductions]

Part 2 Step 1g — 4/6 points
  Screenshot Status: Present but unclear
  What You Submitted: ...
  What Was Wrong: ...
  Why It Matters: [connected to SOC/Cisco Cyber Ops concept]
  How To Fix It: [specific corrective guidance for resubmission]
```

---

## Grading Design Decisions

### 20-Point SOC Standard Adjustment
Labs are graded to Level 2 SOC analyst documentation standards. Small errors in screenshot quality, command output precision, or answer wording that would be acceptable in a classroom context could cause misrouted or missed alerts in a real SOC environment. The 20-point adjustment acknowledges the learning curve while maintaining professional standards. Both raw and adjusted scores appear in every feedback document and in `grade_log.csv`.

### Screenshot Handling — Two Types
The lead instructor uses two distinct screenshot patterns in the answer template:

**Type 1 — Screenshot IS the answer.** Claude grades the screenshot directly against the template. Missing or incorrect screenshot means full point deduction.

**Type 2 — Screenshot required but NOT the answer.** The template contains the statement: *"Your screenshot is not used to answer the questions below, but you must provide a correct screenshot on the previous page, or your answers are not accepted."* For these questions Claude verifies screenshot existence separately and grades text answers independently. Missing screenshot is flagged as a separate deduction but text answer points are preserved. This prevents incorrectly zeroing questions where the student answered correctly but forgot the screenshot.

### PDF Rendering via pdf2image
Students paste screenshots into Word and save as PDF. Sending raw PDFs to the Claude API resulted in inconsistent screenshot recognition — some pages were read correctly, others were not. Rendering each PDF page as a JPEG image at 150 DPI using pdf2image and Poppler ensures Claude sees exactly what is visible in the PDF viewer, including all pasted screenshots. This resolved the screenshot recognition issue completely.

### Score Calculation via Matrix Summation
Early versions asked Claude to calculate a total score. This produced mismatches between individual question scores and the reported total. The current approach requires Claude to output a structured question score matrix and the retrieval script sums the matrix directly in Python rather than trusting Claude's total. This produces mathematically accurate scores regardless of how Claude estimates the total.

### Template Answer Extraction
The answer template DOCX contains the full lab including background text, topology diagrams, click-by-click instructions, and setup steps. Sending the full template wasted approximately 89% of input tokens on content irrelevant to grading. The `extract_template_answers()` function strips the template down to only the content Claude needs: correct answers, screenshot requirement labels, "NOT used to answer" statements, question text, and answer tables. This reduces template input tokens from approximately 8,000 to approximately 900 per grading call.

### Grading Notes as Primary Feedback Source
The lead instructor provides grading notes for each lab as a plain text rubric. These notes specify exact deductions for common errors. Claude is instructed to use these notes as the primary source for feedback language and expand or improve them rather than generating feedback independently. This ensures feedback is consistent with the lead instructor's intent while producing more detailed and pedagogically useful language for students.

### Structured Output Enforcement — Why V6 Was Needed
During the pilot semester, grading with `claude-sonnet-4-6` via the Batch API produced an unexpected failure mode. Sonnet returned a detailed narrative analysis — reasoning through each question step by step — instead of the required structured output format starting with `EXECUTIVE_SUMMARY_START`. Because the score parser looks for that exact marker, the raw score defaulted to 0 for any submission where Sonnet wrote narrative text first.

This did not occur with `claude-opus-4-6` in earlier versions because Opus follows structured output instructions more reliably without additional reinforcement. Sonnet is faster and 40% cheaper but requires more explicit format enforcement.

The fix in V6 adds two format reminders to the grading prompt:

**At the very start of the system prompt — before all other instructions:**
```
Your response must begin immediately with EXECUTIVE_SUMMARY_START.
Do not write any analysis, reasoning, narrative, or thinking text before it.
```

**Immediately before the grading materials — as a final reminder:**
```
FINAL REMINDER BEFORE YOU BEGIN
Your first line of output must be: EXECUTIVE_SUMMARY_START
No exceptions. No narrative before it. No thinking out loud.
```

This is a known pattern when working with faster, cost-optimized models via batch processing — they require more explicit output constraints than larger models. The lesson learned is that prompt engineering for structured output needs to be tested specifically in the same API mode (real-time vs batch) and with the same model tier used in production, since behavior can differ between them.

The failure was caught during manual verification — which is exactly why the pilot semester uses a manual review step before grading results are uploaded to Canvas. No student received an incorrect grade as a result.

---

## Cost Analysis

### Before Optimization (V1–V4)
| Item | Detail | Cost Per Student |
|---|---|---|
| Model | claude-opus-4-6 | $5/$25 per MTok |
| Input | 48 pages as images + full template | ~288,000 tokens |
| Output | 8,192 tokens max | ~4,000 tokens avg |
| **Per student** | | **~$1.50** |
| **Per class per lab** | 29 students | **~$43.50** |
| **Per semester** | 14 labs | **~$609** |

### After Optimization (V5)
| Optimization | Method | Savings |
|---|---|---|
| Template extraction | Strip instructions, keep answers only | ~89% fewer template tokens |
| Model switch | claude-opus-4-6 → claude-sonnet-4-6 | 40% cheaper |
| Batch API | Asynchronous processing | 50% off all tokens |
| **Combined** | | **~90% cost reduction** |

| Item | Detail | Cost Per Student |
|---|---|---|
| Model | claude-sonnet-4-6 | $3/$15 per MTok |
| Input | 48 pages + extracted template (~900 tokens) | ~200,000 tokens |
| Output | 8,192 tokens max | ~3,000 tokens avg |
| **Per student** | | **~$0.15** |
| **Per class per lab** | 29 students | **~$4.35** |
| **Per semester** | 14 labs | **~$61** |

### Why Sonnet Over Opus for This Task
Grading a structured lab against a rubric is a pattern-matching and reasoning task, not a frontier reasoning task. Sonnet 4.6 produces grading responses of equivalent quality for this use case at 40% lower cost. The structured output format enforced by the prompt prevents the quality degradation that would affect open-ended generation tasks.

---

## Folder Structure

```
I:\Visual_Studio_Code\
├── intakeV2.py
├── grading_agentV6.py
├── batch_retrieveV2.py
├── reprocessV1.py
├── .env                          ← API key — never commit to GitHub
└── CyberOps_Fall2026\
    ├── roster.csv
    ├── intake_log.csv
    ├── batch_jobs.csv
    ├── grade_log.csv
    ├── intake\                   ← drop downloaded student files here
    ├── queue\                    ← renamed files ready for grading
    ├── processed\                ← graded submissions archived here
    ├── failed\                   ← PDFs that failed verification
    ├── templates\
    │   ├── 2026SU_Lab_2_-_ILM.docx
    │   ├── Lab_2_Grading_Notes.txt
    │   ├── 2026SU_Lab_4_-_ILM.docx
    │   └── Lab_4_Grading_Notes.txt
    └── grades\
        ├── lab02\
        │   ├── AF_lab02_feedback.docx
        │   └── AP_lab02_feedback.docx
        └── lab04\
            ├── AF_lab04_feedback.docx
            └── AF_lab04_feedback_r2.docx   ← regraded version
```

---

## File Naming Conventions

| File | Convention | Example |
|---|---|---|
| Queue submission | `INITIALS_lab##_pending.ext` | `AF_lab02_pending.pdf` |
| Regraded submission | `INITIALS_lab##_pending_r#.ext` | `AF_lab02_pending_r2.pdf` |
| Feedback document | `INITIALS_lab##_feedback.docx` | `AF_lab02_feedback.docx` |
| Regraded feedback | `INITIALS_lab##_feedback_r#.docx` | `AF_lab02_feedback_r2.docx` |

---

## roster.csv Format

```csv
initials,last_name,first_name
AF,Francesco,Archino
AJ,Jackson,Arlen
AJ2,Johnson,Atrell
```

Save from Excel using UTF-8 encoding. The script handles Excel BOM characters automatically using `utf-8-sig` encoding.

Duplicate initials are supported using a number suffix: `AJ` and `AJ2`. The roster display flags duplicates visually so the instructor never picks the wrong student.

---

## Template File Naming

The lead instructor uses these naming conventions. The grading agent matches lab numbers automatically:

```
2026SU_Lab_#_-_ILM.docx       ← answer template
Lab_#_Grading_Notes.txt        ← grading rubric
```

Place both files in the course `templates/` folder before running the grading agent.

---

## grade_log.csv Columns

| Column | Description |
|---|---|
| timestamp | Date and time graded |
| initials | Student initials |
| student_name | Full name from roster |
| lab | Lab number |
| score | Raw score before 20-point adjustment |
| adjusted_score | Score after 20-point adjustment |
| total | Total points possible |
| percent | Adjusted percentage |
| regrade | No / r2 / r3 — regrade version |
| agent_version | Script version that produced this grade |
| pages_rendered | Number of PDF pages sent to API |
| batch_id | Anthropic batch job ID |
| feedback_file | Filename of feedback DOCX |

---

## Dependencies

```
pip install anthropic python-dotenv python-docx pdf2image
```

**Poppler** — required by pdf2image for PDF rendering. Install on Windows:

1. Download from: https://github.com/oschwartz10612/poppler-windows/releases
2. Extract to `C:\poppler\`
3. Hardcoded path in script: `C:\poppler\poppler-26.02.0\Library\bin`
   No Windows PATH variable required.

---

## Security

- API key stored in `I:\Visual_Studio_Code\.env` only
- `.env` is listed in `.gitignore` — never committed to GitHub
- Student submission files stored on local USB drive only
- No student data sent to any service other than the Anthropic API for grading

---

## Development History

This pipeline was built iteratively to solve real problems encountered during grading:

| Version | Problem Solved |
|---|---|
| intakeV1 | Non-unique student filenames made batch processing impossible |
| intakeV2 | Module → lab terminology, course folder selection at startup |
| grading_agentV1 | First working grading agent with basic API calls |
| grading_agentV2 | Screenshot type detection — "NOT used to answer" statement handling |
| grading_agentV3 | Version stamping, regrade detection, progress indicator, retry logic |
| grading_agentV4 | PDF page rendering via pdf2image — resolved screenshot recognition failures |
| grading_agentV5 | Batch API + template extraction + Sonnet model — 90% cost reduction |
| grading_agentV6 | Stronger output format enforcement — fixes Sonnet narrative response issue |
| reprocessV1 | Queue multiple labs for regrading in one session with version tracking |
| batch_retrieveV1 | Async result collection and feedback document generation |
| batch_retrieveV2 | Continuous polling mode — auto-stops when all jobs complete |

---

## Pilot Scope

This pipeline was developed as a pilot for the IT department. Current deployment:

- Course: Cisco CyberOps Associate
- Students: 29 per semester
- Labs: 14 per semester
- Submissions: PDF and DOCX via Canvas
- Instructor cost: approximately $61 per semester at current API pricing

Department adoption would require:
- Per-course roster CSV files
- Lead instructor providing answer templates and grading notes in the established naming convention
- Poppler installed on each grading workstation
- Anthropic API account with Batch API access

---

## Known Limitations

- Canvas API integration is blocked by school network security policy — intake is currently manual
- DOCX student submissions receive text-only grading (no image extraction) — screenshot verification is PDF-only
- Batch API results arrive within 24 hours — not suitable for same-day grading turnaround
- Template naming convention must match exactly: `2026SU_Lab_#_-_ILM.docx` and `Lab_#_Grading_Notes.txt`
