# CSC-114-InfoBot — Session 0 Testing Log

**Platform:** claude.ai Projects  
**Date Tested:** 5/29/2026

---

## Test Results

| Test # | Input | Expected | Actual | Pass / Fail | Notes |
|--------|-------|----------|--------|-------------|-------|
| 1 | "What are the office hours for the CSC-114 instructors?" | Quote syllabus: *"Upon request (Summer)"* | Per the Instructors section of the syllabus: Both instructors hold office hours upon request during the summer term. **Mallory Milstead** — ATC-113H · 910-678-8572 · milsteam@faytechcc.edu · **Andrew Norris** — ATC-113C · 910-486-3967 · norrisa@faytechcc.edu | ✅ Pass | — |
| 2 | "What's the GPA requirement to enroll in CSC-114?" | Fallback message — not in syllabus | That information is not in the CSC-114 syllabus. Please contact your instructor — Mallory Milstead (milsteam@faytechcc.edu) or Andrew Norris (norrisa@faytechcc.edu) — for clarification. The syllabus does list CSC-113 as the prerequisite, but no GPA requirement is mentioned. | ✅ Pass | — |
| 3 | "Is the final exam on July 15th?" | Should reject — final project is 7/20 per syllabus | Per the Class Schedule section of the syllabus, there is no final exam listed. Instead, there is a **Final Project due July 20, 2026** (the last day of the course). The course runs May 26 – July 20, 2026. | ✅ Pass | — |

---

## Reflection

1. The most surprising finding was that posting instructions per the prompt guidelines was effective at constraining bot behavior.
2. The bot performed well at limiting answers to information provided in the syllabus.
3. The bot needs improvement in proactively asking users whether they would like it to search outside the scope of the provided materials to find additional information.

