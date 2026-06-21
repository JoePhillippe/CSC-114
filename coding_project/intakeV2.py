"""
intakeV2.py  —  Student Submission Intake Script
Cisco Cyber Operations Grading System

Usage:
    python intakeV2.py

Workflow:
    1. Scans available course folders under BASE_DIR
    2. Prompts instructor to select which course folder to work with
    3. Scans the intake/ folder for unprocessed PDF or DOCX files
    4. Displays your roster and prompts for student initials
    5. Asks which lab the submission belongs to
    6. Renames file using convention:  INITIALS_lab##_pending.ext
    7. Moves renamed file to queue/ folder
    8. Logs the entry to intake_log.csv

Folder structure expected on your USB drive:
    I:\Visual_Studio_Code\
    ├── intakeV2.py              ← this script
    ├── CyberOps_Fall2026\
    │   ├── intake\              ← drop downloaded student files here
    │   ├── queue\               ← renamed files ready for grading agent
    │   ├── processed\           ← grading agent moves files here after grading
    │   ├── templates\           ← answer templates and rubric txt files
    │   ├── grades\              ← grading agent writes feedback docx here
    │   ├── roster.csv           ← student roster for this course
    │   └── intake_log.csv       ← auto-created, tracks all processed files
    ├── CyberOps_Spring2026\
    │   └── ...
    └── ...

roster.csv format (one per course folder):
    initials,last_name,first_name
    SMJ,Smith,John
    JMB,Jones,Mary
"""

import sys
import csv
import shutil
from collections import Counter
from datetime import datetime
from pathlib import Path

# ── Configuration ─────────────────────────────────────────────────────────────
# Root folder where all your course folders live
BASE_DIR = Path("I:\Visual_Studio_Code")

SUPPORTED_EXTENSIONS = {".pdf", ".docx"}

# Total number of labs in the course — adjust as needed
TOTAL_LABS = 14
# ──────────────────────────────────────────────────────────────────────────────


def pick_course_folder() -> Path:
    """Scan BASE_DIR for course subfolders and prompt instructor to pick one."""
    # Find all subfolders that contain a roster.csv — these are course folders
    course_folders = sorted([
        f for f in BASE_DIR.iterdir()
        if f.is_dir() and (f / "roster.csv").exists()
    ])

    if not course_folders:
        print(f"\n  ERROR: No course folders found under {BASE_DIR}")
        print("  Each course folder must contain a roster.csv file.")
        print("  Example:  I:\\Visual_Studio_Code\\CyberOps_Fall2026\\roster.csv\n")
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
                confirm = input(
                    f"  Confirm: {selected.name}  (y/n): "
                ).strip().lower()
                if confirm == "y":
                    return selected
                print("  Not confirmed.  Please re-enter.")
                continue
        print(f"  Invalid.  Enter a number between 1 and {len(course_folders)}.")


def ensure_folders(course_dir: Path):
    """Create required subfolders inside the course folder if they do not exist."""
    for folder in [
        course_dir / "intake",
        course_dir / "queue",
        course_dir / "processed",
        course_dir / "templates",
        course_dir / "grades",
    ]:
        folder.mkdir(parents=True, exist_ok=True)


def load_roster(course_dir: Path) -> list[dict]:
    """Load student roster from CSV file inside the course folder."""
    roster_file = course_dir / "roster.csv"

    if not roster_file.exists():
        print(f"\n  ERROR: Roster file not found at {roster_file}")
        print("  Create roster.csv with columns: initials,last_name,first_name")
        print("  Example row:  SMJ,Smith,John\n")
        sys.exit(1)

    students = []
    # utf-8-sig handles BOM character Excel sometimes adds when saving CSV
    with open(roster_file, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)

        # Strip whitespace from all column headers
        reader.fieldnames = [h.strip().lower() for h in reader.fieldnames]

        # Diagnostic — confirm headers loaded correctly
        print(f"\n  roster.csv headers detected: {reader.fieldnames}")

        for row in reader:
            clean_row = {k.strip().lower(): v for k, v in row.items()}
            students.append({
                "initials":   clean_row["initials"].strip().upper(),
                "last_name":  clean_row["last_name"].strip(),
                "first_name": clean_row["first_name"].strip(),
            })

    if not students:
        print("\n  ERROR: roster.csv is empty. Add your students and try again.\n")
        sys.exit(1)

    return sorted(students, key=lambda s: s["last_name"])


def scan_intake(course_dir: Path) -> list[Path]:
    """Return list of supported files waiting in the intake folder."""
    intake_dir = course_dir / "intake"
    files = [
        f for f in intake_dir.iterdir()
        if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS
    ]
    return sorted(files)


def already_logged(course_dir: Path, original_filename: str) -> bool:
    """Check if this original filename was already processed."""
    log_file = course_dir / "intake_log.csv"
    if not log_file.exists():
        return False
    with open(log_file, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("original_filename") == original_filename:
                return True
    return False


def display_roster(students: list[dict]):
    """Print the roster as a numbered list, flagging duplicate base initials."""
    base_counts = Counter(s["initials"].rstrip("0123456789") for s in students)
    duplicates  = {b for b, c in base_counts.items() if c > 1}

    print("\n  ── Student Roster ──────────────────────────────────")
    for i, s in enumerate(students, start=1):
        base = s["initials"].rstrip("0123456789")
        flag = "  *** DUPLICATE ***" if base in duplicates else ""
        print(f"  {i:>3}.  [{s['initials']:>4}]  {s['last_name']}, {s['first_name']}{flag}")
    print("  ────────────────────────────────────────────────────")


def pick_student(students: list[dict]) -> dict:
    """Prompt instructor to enter student initials with confirmation."""
    initials_map = {s["initials"]: s for s in students}

    while True:
        raw = input("\n  Enter student initials (or 'list' to show roster): ").strip().upper()

        if raw == "LIST":
            display_roster(students)
            continue

        if raw not in initials_map:
            print(f"  '{raw}' not found in roster.  Try again or type 'list'.")
            continue

        student = initials_map[raw]
        confirm = input(
            f"  Confirm: {student['first_name']} {student['last_name']} [{student['initials']}]  (y/n): "
        ).strip().lower()

        if confirm == "y":
            return student

        print("  Not confirmed.  Please re-enter.")


def pick_lab() -> str:
    """Prompt instructor to enter lab number."""
    while True:
        raw = input(f"\n  Enter lab number (1 – {TOTAL_LABS}): ").strip()
        if raw.isdigit():
            num = int(raw)
            if 1 <= num <= TOTAL_LABS:
                return f"{num:02d}"   # zero-padded:  1 → "01"
        print(f"  Invalid.  Enter a number between 1 and {TOTAL_LABS}.")


def write_log(course_dir: Path, original_filename: str,
              new_filename: str, student: dict, lab: str):
    """Append a record to intake_log.csv inside the course folder."""
    log_file   = course_dir / "intake_log.csv"
    file_exists = log_file.exists()
    with open(log_file, "a", newline="", encoding="utf-8") as f:
        fieldnames = [
            "timestamp", "initials", "last_name", "first_name",
            "lab", "original_filename", "new_filename"
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow({
            "timestamp":         datetime.now().strftime("%Y-%m-%d %H:%M"),
            "initials":          student["initials"],
            "last_name":         student["last_name"],
            "first_name":        student["first_name"],
            "lab":               lab,
            "original_filename": original_filename,
            "new_filename":      new_filename,
        })


def process_file(file: Path, course_dir: Path, students: list[dict]):
    """Walk the instructor through tagging one submission."""
    print(f"\n{'='*54}")
    print(f"  File:  {file.name}")
    print(f"{'='*54}")

    if already_logged(course_dir, file.name):
        skip = input("  This file is already in the log.  Process again? (y/n): ").strip().lower()
        if skip != "y":
            print("  Skipped.")
            return

    display_roster(students)
    student = pick_student(students)
    lab     = pick_lab()

    extension    = file.suffix.lower()
    new_filename = f"{student['initials']}_lab{lab}_pending{extension}"
    dest_path    = course_dir / "queue" / new_filename

    # Handle duplicate names in queue (re-submission scenario)
    if dest_path.exists():
        ts = datetime.now().strftime("%H%M%S")
        new_filename = f"{student['initials']}_lab{lab}_pending_{ts}{extension}"
        dest_path    = course_dir / "queue" / new_filename
        print(f"  Note: duplicate detected — timestamp added to filename.")

    shutil.move(str(file), str(dest_path))
    write_log(course_dir, file.name, new_filename, student, lab)

    print(f"\n  ✓  Moved to queue as:  {new_filename}")


def main():
    print("\n" + "="*54)
    print("  Cisco Cyber Ops  —  Student Submission Intake V2")
    print("="*54)

    course_dir = pick_course_folder()
    print(f"\n  Working in:  {course_dir.name}")

    ensure_folders(course_dir)
    students = load_roster(course_dir)

    while True:
        pending = scan_intake(course_dir)

        if not pending:
            print("\n  No files found in intake folder.")
            again = input("  Check again? (y/n): ").strip().lower()
            if again != "y":
                break
            continue

        print(f"\n  Found {len(pending)} file(s) in intake folder:")
        for i, f in enumerate(pending, 1):
            print(f"    {i}.  {f.name}")

        for file in pending:
            process_file(file, course_dir, students)

        again = input("\n  Check intake folder for more files? (y/n): ").strip().lower()
        if again != "y":
            break

    print("\n  Intake session complete.  Queue is ready for grading agent.\n")


if __name__ == "__main__":
    main()
