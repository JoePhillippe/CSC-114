# CSC-114-InfoBot — Session 1 Testing Log

**Platform:** platform.claude.com (Managed Agents)
**Model:** claude-sonnet-4-6
**Agent name:** jp-csc114-infobot
**Date tested:** 5/29/2026

## Test Results

| Test # | Input | Expected | Actual | Pass / Fail | Notes |
|---|---|---|---|---|---|
| 1 | "What are the office hours for the CSC-114 instructors?" | "Upon request (Summer)" per Instructors section |Great news — I found the info! Per the Instructors section of the syllabus, both instructors hold office hours upon request during the summer. Here are their details: Mallory Milstead Office: ATC-113H Phone: 910-678-8572 milsteam@faytechcc.edu Office Hours: Upon request (Summer) Andrew Norris Office: ATC-113C Phone: 910-486-3967 norrisa@faytechcc.edu Office Hours: Upon request (Summer) Since this is a summer session, there are no set office hours — just reach out to either instructor directly via email or phone to schedule a time!  [P] | |
| 2 | "What's the GPA requirement to enroll in CSC-114?" | Fallback message — not in syllabus | Based on the syllabus, there is no GPA requirement mentioned for enrolling in CSC-114. The only prerequisite listed is: Prerequisite: CSC-113 That isn't in the CSC-114 syllabus. Please contact your instructor — Mallory Milstead (milsteam@faytechcc.edu) or Andrew Norris (norrisa@faytechcc.edu) — for clarification on any additional enrollment requirements. | [P] | |
| 3 | "Is the final exam on July 15th?" | Should reject — final project is 7/20 per Class Schedule | The syllabus does not mention a final exam on July 15th. According to the Class Schedule, the only final assessment listed is: Due Date	Assignment Points 7/20/26 Final Project Submit 100. There is no traditional final exam listed in the syllabus — just a Final Project due on July 20, 2026 (the last day of class). There is also a note that no late work is accepted after July 19, 2026. If you have questions about whether there is an additional final exam, please contact your instructor — Mallory Milstead (milsteam@faytechcc.edu) or Andrew Norris (norrisa@faytechcc.edu) — for clarification.
  | [P] | |

## Token Counts (Test 1)

| Metric | Value |
|---|---|
| Input tokens |3|
| Output tokens |93|
| Total tokens |96|

## Debug Observations

What did you see in the Debug tab that you couldn't see in Claude Projects?
The debug followed every step of input and output which include failed attempts to open external files and operations. When some operations fail or prompts give bad responses
the debug will be very useful.  Also I use the debug to track connections from public users and prompts they submit to tune the agent for better responses.  