# Cisco CyberOps Automated Grading Pipeline

An AI-powered grading pipeline for Cisco Cyber Operations Associate labs. Built with Python and the Anthropic Claude API. Designed as a pilot for department-wide adoption of AI-assisted grading.

---

## Overview

This pipeline automates grading of student lab submissions for the Cisco CyberOps Associate course. Students submit labs as PDF or DOCX files through Canvas. The pipeline intakes submissions, renames them consistently, renders PDF pages as images, sends them to the Claude API for grading against an answer key and rubric, and produces a structured feedback document for each student.

The system was built iteratively by an IT instructor learning Python scripting and AI agent development. Each script version solves a real grading problem discovered in production use.

---

## Problem Statement

- 29 students per semester submitting 14 labs each
- Labs contain text answers AND screenshots pasted into Word then saved as PDF
- Manual grading via Claude.ai Projects hit context limits with a single student per chat
- Student files had non-unique names making batch processing impossible
- No consistent feedback format across submissions
- Grading to professional SOC Level 2 standards requires detailed, specific feedback
- AI agent cannot reliably grade screenshot-dependent questions by pixel comparison alone

---

## Current Scripts

| Script | Purpose |
|---|---|
| `intakeV2.py` | Interactive intake -- renames and queues student submissions |
| `grading_agentV8.py` | Renders PDFs as images, auto-splits large batches, submits to Batch API |
| `batch_retrieveV2.py` | Runs continuously -- retrieves completed batch results every 24 hours |
| `reprocessV1.py` | Moves processed files back to queue for regrading with version tracking |
| `lab_answer_keyV4.py` | Answer Key Pipeline Step 1 -- extracts text answers and transcribes screenshots from all lab templates via Batch API vision analysis |

---

## Solution Architecture

```
Canvas (manual download)
        |
   intake/                  <- raw student files dropped here
        |
  intakeV2.py               <- interactive intake script
        |
   queue/                   <- renamed files with consistent naming
        |
  grading_agentV8.py        <- renders PDFs, submits batch to Claude API
        |
  Anthropic Batch API       <- processes overnight, 90% cost savings
        |
  batch_retrieveV2.py       <- runs continuously, retrieves results every 24 hours
        |
  grades/lab##/             <- feedback DOCX per student per lab
        |
Canvas (manual upload)      <- attach feedback to student submission
```

---

## Answer Key Pipeline

### Why the Answer Key Pipeline Was Created

During the pilot semester, manual verification of AI-graded results revealed that the grading agent cannot reliably grade screenshot-dependent questions. The agent compares a student screenshot against an instructor screenshot with no reference text -- leading to incorrect deductions on questions the student answered correctly.

The Answer Key Pipeline solves this by pre-processing instructor templates into a structured answer key before the semester begins. Terminal output and command results are transcribed to text by the Claude vision API. Charts and topology diagrams that cannot be text-represented are kept as images for instructor review. The grading agent (future V9) then compares student answers against known correct text answers rather than interpreting raw images.

### Three-Step Plan

| Step | Script | Status | Purpose |
|---|---|---|---|
| 1 | `lab_answer_keyV4.py` | Complete | Extract text answers and transcribe screenshots from all templates |
| 2 | `lab_answer_keyV4.py` (update) | Planned | Add grading notes to each question in the answer key |
| 3 | `grading_agentV9.py` | Planned | Grade student submissions against answer key instead of raw template |

### Step 1 -- lab_answer_keyV4.py

Scans `templates/` for all `2026SU_Lab_#_-_ILM.docx` files and processes each one in two phases.

**Phase 1 -- Submit (runs immediately):**
- Unpacks each DOCX and walks document XML in order
- Waits for the Objectives / Part 1 header before collecting slots (preamble guard)
- Detects screenshot slot labels directly: `Part 1h [Insert a screenshot...]`
- Detects text answer slots directly: `[Insert your answer below]`
- Skips images smaller than 400x200 pixels (logos, icons, decorative elements)
- Submits one Batch API vision job covering all screenshot slots across all labs
- Saves state file: `templates/answer_keys/answer_key_batch_state.json`

**Phase 2 -- Retrieve (run again after batch completes):**
- Detects state file and switches to retrieve mode automatically
- Polls batch until complete
- Terminal / command output screenshots -> transcribed as text
- Charts, graphs, topology diagrams -> kept as image (cannot be text)
- Writes `Lab_#_Answer_Key.md` files to `templates/answer_keys/`
- Deletes state file when done

**Run instructions:**
```
# Phase 1 - parse templates and submit batch
python lab_answer_keyV4.py

# Wait for batch to complete (typically under 1 hour)
# Check status at console.anthropic.com -> Batches

# Phase 2 - retrieve results and write answer keys
python lab_answer_keyV4.py
```

Same command both times. Script auto-detects which phase to run.

### Lab Types and Answer Key Format

| Lab Type | Labs | Answer Key Format |
|---|---|---|
| Technical Cisco labs | 2 - 13 | Structured slots with text answers and transcribed screenshots |
| Research / essay labs | 1, 14 | Hand-written rubric files -- no template answer slots |
| AI-prompt lab | 15 | Hand-written rubric file -- created by lead instructor |

Labs 1, 14, and 15 return 0 slots from the parser -- this is correct behavior. Their answer keys are rubric files written manually and placed directly in `templates/answer_keys/`.

### Known Issue -- Vision Transcription Accuracy

The initial batch run identified one transcription accuracy issue: Lab 11 Part 3 Step 2c (a Kibana HTTP-Logs screenshot) was transcribed starting mid-scroll, missing the `@timestamp` and `_id` fields at the top of the entry. The image in the template DOCX is complete -- the issue is the vision prompt not transcribing from the very top of the image.

**Current status:**
- Lab 11 Part 3 Step 2c manually corrected in `Lab_11_Answer_Key.md`
- Improved vision prompt planned for corrective batch run covering all screenshot slots
- Corrective batch will rerun all 37 screenshot slots with the improved prompt

**Grading note for Lab 11 Part 3 Step 2c:**
The lab instructions require students to submit a screenshot showing the `@timestamp` row at the top of the expanded Kibana log entry. If `@timestamp` and `_id` are not visible at the top of the student screenshot, the screenshot does not meet requirements. Only page 1 of 4 of the log entry is required.

### Answer Key Instructor Review (Required Before Grading)

After Step 1 completes, the instructor and lead instructor review each `Lab_#_Answer_Key.md`:

- Verify AI-transcribed text matches what the template shows
- For image slots: confirm the image is correctly identified as visual content
- Correct any slots where the parser misidentified the question label
- For rubric labs (1, 14, 15): verify point values and deduction tables are accurate

---

## Daily Workflow

### Setting Up a New Semester
1. Create a course folder under `I:\Visual_Studio_Code\` -- example: `CyberOps_Fall2026`
2. Place `roster.csv` inside the course folder
3. Place answer templates and grading notes in the `templates\` subfolder
4. Run `lab_answer_keyV4.py` to generate answer keys before the semester starts
5. Review and correct answer key files before grading begins
6. All other folders are created automatically on first run

### Before the Semester -- Generate Answer Keys
```
# Run once per semester before grading begins
# Place all 2026SU_Lab_#_-_ILM.docx files in templates\

# Step 1 - Submit answer key batch
python lab_answer_keyV4.py

# Step 2 - After batch completes, retrieve and write answer keys
python lab_answer_keyV4.py

# Step 3 - Review templates\answer_keys\ and correct any errors
# Step 4 - Copy rubric files for Labs 1, 14, 15 into templates\answer_keys\
```

### Grading Day -- Morning
```
# Step 1 - Download student submissions from Canvas manually
# Drop all downloaded files into:
#   I:\Visual_Studio_Code\CyberOps_Fall2026\intake\

# Step 2 - Run intake script
python intakeV2.py
# Select course folder
# For each file: enter student initials, confirm name, enter lab number
# Files move to queue\ with consistent naming: AF_lab02_pending.pdf
```

### Grading Day -- After Intake
```
# Step 3 - Submit batch grading job
python grading_agentV8.py
# Select course folder
# Confirm submission of all queued files
# Script renders PDFs as images, submits to Anthropic Batch API
# Completes in minutes regardless of class size
# Submissions move to processed\
```

### Grading Day -- Leave Running Overnight
```
# Step 4 - Start continuous retrieval watcher
python batch_retrieveV2.py
# Select course folder
# Script checks every 24 hours for completed batch results
# Writes feedback DOCX to grades\lab##\ when results arrive
# Stops automatically when all jobs are complete
# Press Ctrl+C to stop early -- run again to resume
```

### Next Morning -- Results Ready
```
grades\lab02\
    AF_lab02_feedback.docx
    AJ_lab02_feedback.docx
    AP_lab02_feedback.docx
    ...

# Step 5 - Upload feedback to Canvas
# Open each feedback DOCX and attach to the matching student submission
```

### Regrading Workflow
```
# When grading prompt is improved or screenshot detection changes:

# Step 1 - Queue labs for regrade
python reprocessV1.py
# Select course folder
# Enter lab number -- example: 4
# Script shows all files found and renames them: AF_lab04_pending_r2.pdf
# Asks if you want to queue another lab
# Enter lab number or n to finish

# Step 2 - Submit regrade batch
python grading_agentV8.py

# Step 3 - Retrieve regraded results
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
- Instructor enters student initials -- confirms full name before proceeding
- Asks for lab number
- Renames file to `INITIALS_lab##_pending.ext`
- Moves file to `queue/` folder
- Logs every intake to `intake_log.csv`
- Supports multiple course folders -- selects at startup

**Why initials with confirmation:** Dyslexia-friendly design. Entering initials is faster and less error-prone than typing full names. The confirmation step shows the full name before any file is moved.

**Handles:**
- Excel BOM characters in roster.csv (utf-8-sig encoding)
- Duplicate initials flagged visually (AJ vs AJ2)
- Re-submission detection -- warns if file already logged

---

### grading_agentV8.py
Batch submission agent. Renders all queued PDFs as images, auto-splits into multiple batches if needed, and submits to the Anthropic Batch API.

**What it does:**
- Scans `queue/` folder for pending files
- Renders each PDF page as a JPEG image at 100 DPI using pdf2image and Poppler
- Verifies minimum page count before submitting -- moves failed PDFs to `failed/`
- Extracts answer-only content from the template DOCX (89% token reduction)
- Measures actual rendered size per student submission
- Auto-splits submissions into batches under 200MB if total exceeds limit
- Submits each batch separately -- each gets its own batch ID
- Saves all batch IDs to `batch_jobs.csv`
- Moves submitted files to `processed/`

**Why batch submission:** The Batch API processes jobs asynchronously within 24 hours at 50% of standard token cost. Submit before you leave, collect results next morning.

**Why auto-split:** The Anthropic Batch API has a hard 256MB request size limit. Each student PDF is approximately 3.8MB when rendered at 100 DPI. A full class of 29 students fits in one batch at ~109MB. However when grading two labs simultaneously -- 58 or more submissions -- the total exceeds 256MB and the API rejects the request with a 413 error. The auto-split logic measures each submission's actual size, groups them into chunks under 200MB, and submits each chunk as a separate batch job. `batch_retrieveV2.py` handles multiple batch IDs automatically.

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
- Safe to stop and restart -- completed results are always skipped
- Shows exact time of next check after each cycle

---

### reprocessV1.py
Regrade script. Moves processed files back to queue for regrading with version tracking.

**What it does:**
- Scans `processed/` folder for files matching a lab number
- Renames files with regrade version suffix: `r2`, `r3`, etc.
- Moves files back to `queue/` for the grading agent to pick up

---

### lab_answer_keyV4.py
Answer Key Pipeline Step 1. Processes all instructor lab templates and produces one structured answer key file per lab using Claude Batch API vision analysis.

**What it does:**
- Scans `templates/` for all `2026SU_Lab_#_-_ILM.docx` files automatically
- Implements preamble guard -- ignores numbered lists before the Objectives section to prevent false question label captures
- Detects screenshot slot labels directly from Cisco lab template text patterns
- Detects text answer slots directly from `[Insert your answer below]` prompts
- Skips images smaller than 400x200 pixels (logos, icons, decorative elements)
- Submits one Batch API vision job for all screenshot slots across all labs
- Saves state file between phases so the terminal can be closed while batch processes
- On Phase 2: transcribes terminal/command screenshots to text; keeps charts/graphs as images
- Writes `Lab_#_Answer_Key.md` to `templates/answer_keys/`

**Why not pdf2image:** Raw images extracted from `word/media/` are original instructor screenshots at full resolution (up to 1955x1099 pixels). pdf2image renders pages at a fixed 150 DPI (1650x1275) which is lower resolution than the source images and adds surrounding page content as noise. The extracted media files are the better source for vision analysis.

**Windows encoding:** All print statements use ASCII only. Git Bash on Windows uses CP1252 encoding which rejects Unicode box-drawing characters. The script avoids all non-ASCII characters in output.

**Custom ID uniqueness:** Batch API requires unique custom_id per request across the entire batch. IDs include a global sequence number suffix (`_003`) to prevent collisions when two labs produce identical label strings.

---

## Lesson Learned -- Structured Output in Batch Mode

The grading agent required explicit structured output enforcement after early versions produced narrative text instead of the required Q-matrix format. The fix was a strict prompt closing block:

```
CRITICAL: Your response must contain ONLY the Q-matrix lines above.
No exceptions. No narrative before it. No thinking out loud.
```

This is a known pattern when working with faster, cost-optimized models via batch processing -- they require more explicit output constraints than larger models. The lesson learned is that prompt engineering for structured output needs to be tested specifically in the same API mode (real-time vs batch) and with the same model tier used in production, since behavior can differ between them.

The failure was caught during manual verification -- which is exactly why the pilot semester uses a manual review step before grading results are uploaded to Canvas. No student received an incorrect grade as a result.

---

## Cost Analysis

### Before Optimization (V1-V4)
| Item | Detail | Cost Per Student |
|---|---|---|
| Model | claude-opus-4-6 | $5/$25 per MTok |
| Input | 48 pages as images at 150 DPI + full template | ~288,000 tokens |
| Output | 8,192 tokens max | ~4,000 tokens avg |
| **Per student** | | **~$1.50** |
| **Per class per lab** | 29 students | **~$43.50** |
| **Per semester** | 14 labs | **~$609** |

### After Optimization (V5+)
| Optimization | Method | Savings |
|---|---|---|
| Template extraction | Strip instructions, keep answers only | ~89% fewer template tokens |
| Model switch | claude-opus-4-6 -> claude-sonnet-4-6 | 40% cheaper |
| Batch API | Asynchronous processing | 50% off all tokens |
| **Combined** | | **~90% cost reduction** |

| Item | Detail | Cost Per Student |
|---|---|---|
| Model | claude-sonnet-4-6 | $3/$15 per MTok |
| Input | 48 pages at 100 DPI + extracted template (~900 tokens) | ~200,000 tokens |
| Output | 8,192 tokens max | ~3,000 tokens avg |
| **Per student** | | **~$0.15** |
| **Per class per lab** | 29 students | **~$4.35** |
| **Per semester** | 14 labs | **~$61** |

### Answer Key Pipeline Cost
| Item | Detail | Cost |
|---|---|---|
| Vision analysis | 37 screenshots via Batch API | ~$0.05 per run |
| Frequency | Once per semester before grading | Negligible |

### Why Sonnet Over Opus for This Task
Grading a structured lab against a rubric is a pattern-matching and reasoning task, not a frontier reasoning task. Sonnet 4.6 produces grading responses of equivalent quality for this use case at 40% lower cost. The structured output format enforced by the prompt prevents the quality degradation that would affect open-ended generation tasks.

---

## Folder Structure

```
I:\Visual_Studio_Code\
|-- intakeV2.py
|-- grading_agentV8.py
|-- batch_retrieveV2.py
|-- reprocessV1.py
|-- lab_answer_keyV4.py
|-- .env                          <- API key -- never commit to GitHub
|-- CyberOps_Fall2026\
|   |-- roster.csv
|   |-- intake_log.csv
|   |-- batch_jobs.csv
|   |-- grade_log.csv
|   |-- intake\                   <- drop downloaded student files here
|   |-- queue\                    <- renamed files ready for grading
|   |-- processed\                <- graded submissions archived here
|   |-- failed\                   <- PDFs that failed verification
|   |-- templates\
|   |   |-- 2026SU_Lab_1_-_ILM.docx
|   |   |-- 2026SU_Lab_2_-_ILM.docx
|   |   |-- ...
|   |   |-- 2026SU_Lab_15_-_ILM.docx
|   |   |-- Lab_1_Grading_Notes.txt
|   |   |-- Lab_2_Grading_Notes.txt
|   |   |-- ...
|   |   |-- Lab_15_Grading_Notes.txt
|   |   |-- answer_keys\
|   |       |-- Lab_1_Answer_Key.md       <- hand-written rubric
|   |       |-- Lab_2_Answer_Key.md       <- generated by lab_answer_keyV4.py
|   |       |-- ...
|   |       |-- Lab_13_Answer_Key.md      <- generated by lab_answer_keyV4.py
|   |       |-- Lab_14_Answer_Key.md      <- hand-written rubric
|   |       |-- Lab_15_Answer_Key.md      <- hand-written rubric
|   |       |-- Lab_5_Answer_Key_images\  <- screenshot images kept as visual
|   |       |-- Lab_7_Answer_Key_images\
|   |       |-- ...
|   |-- grades\
|       |-- lab02\
|       |   |-- AF_lab02_feedback.docx
|       |   |-- AP_lab02_feedback.docx
|       |-- lab04\
|           |-- AF_lab04_feedback.docx
|           |-- AF_lab04_feedback_r2.docx   <- regraded version
```

---

## File Naming Conventions

| File | Convention | Example |
|---|---|---|
| Queue submission | `INITIALS_lab##_pending.ext` | `AF_lab02_pending.pdf` |
| Regraded submission | `INITIALS_lab##_pending_r#.ext` | `AF_lab02_pending_r2.pdf` |
| Feedback document | `INITIALS_lab##_feedback.docx` | `AF_lab02_feedback.docx` |
| Regraded feedback | `INITIALS_lab##_feedback_r#.docx` | `AF_lab02_feedback_r2.docx` |
| Lab template | `2026SU_Lab_#_-_ILM.docx` | `2026SU_Lab_2_-_ILM.docx` |
| Grading notes | `Lab_#_Grading_Notes.txt` | `Lab_2_Grading_Notes.txt` |
| Answer key | `Lab_#_Answer_Key.md` | `Lab_2_Answer_Key.md` |

**Note:** Lab 1 template was originally named `2026SU_Lab_1_1_.docx` (student download format). Rename to `2026SU_Lab_1_-_ILM.docx` before placing in the templates folder so the parser finds it correctly.

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
2026SU_Lab_#_-_ILM.docx       <- answer template
Lab_#_Grading_Notes.txt        <- grading rubric and deduction notes
Lab_#_Answer_Key.md            <- generated answer key (Step 1 output)
```

Place templates and grading notes in the course `templates/` folder before running the grading agent. Answer keys are written to `templates/answer_keys/` automatically.

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
| regrade | No / r2 / r3 -- regrade version |
| agent_version | Script version that produced this grade |
| pages_rendered | Number of PDF pages sent to API |
| batch_id | Anthropic batch job ID |
| feedback_file | Filename of feedback DOCX |

---

## Dependencies

```
pip install anthropic python-dotenv python-docx pdf2image Pillow
```

**Poppler** -- required by pdf2image for PDF rendering. Install on Windows:

1. Download from: https://github.com/oschwartz10612/poppler-windows/releases
2. Extract to `C:\poppler\`
3. Hardcoded path in script: `C:\poppler\poppler-26.02.0\Library\bin`
   No Windows PATH variable required.

---

## Security

- API key stored in `I:\Visual_Studio_Code\.env` only
- `.env` is listed in `.gitignore` -- never committed to GitHub
- Student submission files stored on local USB drive only
- No student data sent to any service other than the Anthropic API for grading

---

## Development History

This pipeline was built iteratively to solve real problems encountered during grading:

| Version | Problem Solved |
|---|---|
| intakeV1 | Non-unique student filenames made batch processing impossible |
| intakeV2 | Module -> lab terminology, course folder selection at startup |
| grading_agentV1 | First working grading agent with basic API calls |
| grading_agentV2 | Screenshot type detection -- "NOT used to answer" statement handling |
| grading_agentV3 | Version stamping, regrade detection, progress indicator, retry logic |
| grading_agentV4 | PDF page rendering via pdf2image -- resolved screenshot recognition failures |
| grading_agentV5 | Batch API + template extraction + Sonnet model -- 90% cost reduction |
| grading_agentV6 | Stronger output format enforcement + auto-split batches for 256MB API limit |
| grading_agentV7 | Internal version -- same as V6 with version number updated |
| grading_agentV8 | Adjacent page screenshot detection -- fixes false missing screenshot deductions |
| reprocessV1 | Queue multiple labs for regrading in one session with version tracking |
| batch_retrieveV1 | Async result collection and feedback document generation |
| batch_retrieveV2 | Continuous polling mode -- auto-stops when all jobs complete |
| lab_answer_keyV1 | Answer Key Pipeline Step 1 (initial) -- text and raw screenshot extraction from all lab templates |
| lab_answer_keyV2 | Added Batch API vision analysis -- terminal screenshots transcribed to text; charts/graphs kept as images; two-phase submit/retrieve architecture |
| lab_answer_keyV3 | Improved parser -- preamble guard, direct screenshot label detection, direct text answer slot detection, minimum image size filter |
| lab_answer_keyV4 | Fixed Unicode encoding crash on Windows CP1252; fixed duplicate Batch API custom_id collision across labs |

---

## Pilot Scope

This pipeline was developed as a pilot for the IT department. Current deployment:

- Course: Cisco CyberOps Associate
- Students: 29 per semester
- Labs: 15 per semester (Labs 1-15)
- Lab types: Technical Cisco labs (2-13), Research/essay labs (1, 14), AI-prompt lab (15)
- Submissions: PDF and DOCX via Canvas
- Instructor cost: approximately $61 per semester at current API pricing

Department adoption would require:
- Per-course roster CSV files
- Lead instructor providing answer templates and grading notes in the established naming convention
- Poppler installed on each grading workstation
- Anthropic API account with Batch API access

---

## Known Limitations

- Canvas API integration is blocked by school network security policy -- intake is currently manual
- DOCX student submissions receive text-only grading (no image extraction) -- screenshot verification is PDF-only
- Batch API results arrive within 24 hours -- not suitable for same-day grading turnaround
- Template naming convention must match exactly: `2026SU_Lab_#_-_ILM.docx` and `Lab_#_Grading_Notes.txt`
- Lab 1 template uses non-standard filename (`2026SU_Lab_1_1_.docx`) -- must be renamed to `2026SU_Lab_1_-_ILM.docx` before placing in templates folder
- Vision API transcription may miss fields at top of scrolled screenshots -- corrective batch planned with improved prompt
- Labs 1, 14, and 15 answer keys must be written and maintained manually -- parser returns 0 slots for essay and AI-prompt labs by design
- Plagiarism scores for Labs 1, 14, and 15 must be checked manually in Canvas TurnItIn -- not accessible via API
