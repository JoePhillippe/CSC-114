# M2 Practice Chat — Study Buddy Q&A
> Course: CSC 114 · Fayetteville Technical Community College  
> Module 2 Practice Questions — AI-assisted study session  
> Model: Claude (Anthropic)

---

## Q1: Why, when teaching to recognize "Image A or B", do we need three states that we train the model to recognize? I understand that having a third answer of "do not know" is important because the agent may have a very low probability for both A and B.

**A:**  
Your instinct is correct — and it goes deeper than just "I don't know."

A model trained on only two classes (A and B) is forced to pick one, always. The math of a two-output softmax guarantees the probabilities sum to 1.0:

```
P(A) + P(B) = 1.0   ← always, no escape
```

So if you show the model a picture of a cat when it was only trained on dogs vs. cars, it still has to output something like `P(dog)=0.51, P(car)=0.49`. It cannot say "neither." It will confidently misclassify everything outside its training distribution.

Adding a third class — "neither / unknown" — breaks that forced choice:

```
P(A) + P(B) + P(unknown) = 1.0

# Now a truly ambiguous image can legitimately output:
P(A)       = 0.12
P(B)       = 0.09
P(unknown) = 0.79   ← model correctly abstains
```

**Three reasons the third state matters:**

1. **Out-of-distribution inputs** — the model will always see images it was never trained on. Without a third class it has no way to flag them.
2. **Low-confidence cases** — even within A and B, some images are genuinely ambiguous. The third class catches borderline cases rather than forcing a wrong answer.
3. **Safety in real applications** — in cybersecurity, medical imaging, or network anomaly detection, a wrong confident answer is worse than an honest "I don't know." The third state lets downstream systems decide what to do with uncertain predictions.

**Connection to MNIST (Chapter 2):** The MNIST model has 10 output classes — one per digit. If you feed it a letter or a symbol, it will still pick the most similar digit. A real production system would add an 11th "not a digit" class trained on non-digit images.

---

## Q2: Which type of Teachable Machines model did you make? How well did it seem to do compared to other groups' models?

**A:**  
This question refers to an in-class exercise using Google's Teachable Machine (teachablemachine.withgoogle.com) that was missed.

**What Teachable Machine is:** A browser-based tool that lets you train an image, audio, or pose classification model using your webcam — no code required. It uses transfer learning under the hood (a pre-trained model is fine-tuned on your new classes). This is a practical demonstration of the same concepts covered in Chapters 2 and 3.

**The three model types available:**
| Type | What it classifies | Input |
|---|---|---|
| Image | Photos / webcam frames | Camera or uploaded images |
| Audio | Sound clips | Microphone |
| Pose | Body position / gestures | Camera + pose estimation |

**Since the exercise was missed, here is how to complete it independently:**

1. Go to https://teachablemachine.withgoogle.com
2. Click **Get Started → Image Project → Standard image model**
3. Create three classes — for example: Class A, Class B, and "Unknown/Neither"
4. Train 30–50 samples per class using your webcam
5. Test the model and observe the confidence scores
6. Export the model and note accuracy

**What to observe when testing:**
- Does confidence stay high for clear examples?
- What happens when you show something outside the training classes?
- How does the "Unknown" class affect the other confidence scores?

**Note for instructor records:** This question references a missed class session. The independent exercise above covers the same learning objectives.

---

## Q3: What skills and workflows do I personally need to develop in order to work with Python notebooks? (Assume that an IPYNB file is provided by the instructor.)

**A:**  
The core workflow is: **receive IPYNB → run and understand it → add your own code → save to GitHub → reload when needed.**

I need to learn IPYNB and github intergration.  I asked Claude to create this md file and help me understand the workflow.

Here are the specific skills and steps to develop:

---

### Skill 1 — Opening and Running a Provided IPYNB in Colab

```
1. Instructor provides an IPYNB file (download it or get a GitHub link)
2. Go to https://colab.research.google.com
3. File → Open notebook → Upload tab → drag in the IPYNB file
   OR
   File → Open notebook → GitHub tab → paste the repo URL
4. Runtime → Run all   ← runs every cell top to bottom
5. Runtime → Change runtime type → T4 GPU  ← enable for later chapters
```

**Key habit:** Always run cells top to bottom in order. Skipping cells or  
running them out of order causes "variable not defined" errors.

---

### Skill 2 — Reading and Modifying Cells

Each cell is either **Markdown** (text/notes) or **Code** (Python).

```python
# Code cell — click to edit, Shift+Enter to run
import numpy as np
x = np.array([1, 2, 3])
print(x.shape)   # add print statements to inspect values
```

**Develop the habit of adding your own cells after each example:**
```python
# Your experiment cell — inserted after instructor's example
# Change one thing and observe what breaks or changes
x = np.array([[1, 2, 3], [4, 5, 6]])
print(f"shape: {x.shape}, ndim: {x.ndim}")
```

---

### Skill 3 — Saving Your Work to Google Drive First

Before modifying any instructor notebook:
```
File → Save a copy in Drive
```
This creates your own editable copy. The original stays untouched.  
Rename it clearly: `chapter02_my_notes.ipynb`

---

### Skill 4 — Pushing Your IPYNB to GitHub

```bash
# Option A — GitHub web interface (simplest)
1. Go to your repo: github.com/JoePhillippe/CSC-114
2. Navigate to the right folder
3. Add file → Upload files → drag your IPYNB from Drive download
4. Commit changes

# Option B — Git command line (more powerful)
git add chapter02_my_notes.ipynb
git commit -m "Add Chapter 2 notebook with personal experiments"
git push origin main
```

---

### Skill 5 — Reloading from GitHub into Colab

```
1. Go to https://colab.research.google.com
2. File → Open notebook → GitHub tab
3. Paste: https://github.com/JoePhillippe/CSC-114
4. Browse to your IPYNB file and open it
5. File → Save a copy in Drive  ← always do this before editing
```

---

### Skill 6 — The Print-Shape Habit

The single most useful debugging skill for notebooks:

```python
# After every tensor operation, print the shape
print(f"shape: {x.shape}, dtype: {x.dtype}, ndim: {x.ndim}")
```

If a shape is wrong, the error is in the step before. This habit catches  
dimension mismatches before they cause confusing errors 10 cells later.

---

### Recommended Workflow Per Chapter

```
1. Instructor provides IPYNB link
2. Open in Colab → Save a copy in Drive
3. Run all cells once — read outputs, don't modify yet
4. Go back to cell 1 — add print(shape) statements, re-run
5. After each section — insert a new cell, experiment with one change
6. Download from Drive → upload to GitHub repo
7. Next session: reload from GitHub → Save a copy in Drive → continue
```

---

### Skills Summary Table

| Skill | Tool | Where to practice |
|---|---|---|
| Open IPYNB | Google Colab | Chollet's Chapter 2 notebook |
| Run cells in order | Colab Runtime menu | Any chapter notebook |
| Save personal copy | Google Drive | Before every edit session |
| Add experiment cells | Colab code cell | After each textbook example |
| Push to GitHub | GitHub web UI or git CLI | After each study session |
| Reload from GitHub | Colab → GitHub tab | Start of each session |
| Debug with print(shape) | Python print() | Every tensor operation |

---

*AI-assisted study session. Answers generated with Claude (Anthropic).*  
*Personal answers and class observations to be added by student.*
