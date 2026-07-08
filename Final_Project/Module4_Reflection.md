# Module 4 — Reflect: Agent-Assisted Reflection
**CSC-114 Artificial Intelligence I**
**Joe Philippe | FTCC CSC-114 | Summer 2026**

---

## Reflection Question 1
### What did you change during the project, and how did the results change?

**Agent context:**

Two deliberate changes were made during this project:

**Change 1 — Epoch list expanded.**
The initial epoch list was `[5, 10, 20, 40]`. At those settings the model showed no overfitting — accuracy and val loss kept improving at every setting. The epoch list was changed to `[40, 80, 150, 300]` to push the model further and expose the overfitting signal. 

**Change 2 — Dropout layers removed.**
The original model included two Dropout layers (0.3 and 0.2). With Dropout in place the model was too well-regularized — val loss kept dropping even at 300 epochs and no overfitting curve appeared. Removing Dropout allowed the model to begin memorizing training data at higher epoch counts, which made the overfitting visible in the results. 
**Result of those changes:**

| Epochs | Train Acc | Val Acc | Val Loss | Notes |
|--------|-----------|---------|----------|-------|
| 40  | 0.9972 | 0.9973 | 0.0090 | Still learning |
| 80  | 0.9980 | 0.9983 | 0.0063 | Sweet spot |
| 150 | 0.9983 | 0.9978 | 0.0143 | Overfitting begins |
| 300 | 0.9987 | 0.9983 | 0.0161 | Overfitting continues |

Val loss reached its minimum at epoch 80 (0.0063), then climbed at epoch 150 (0.0143) and 300 (0.0161) — producing the clear overfitting curve needed for the project.

---

**🖊 My observations and comments:**

I tried several levels to get to the maximum of 300 Epoch but no overfitting resulted. I instructed Claude AI the I need to show where overfitting would happen. I was informed that the Droput layers were including in Python code to prevent overfitting.  This resulted in change two that removed the dropout layers.  This shows that dropout layers can be included in model to prevent overfitting.


---
---

## Reflection Question 2
### At what point did overfitting appear in your training run, and how did you know from the numbers?

**Agent context:**

Overfitting appeared at **epoch 150**. Here is how to identify it from the actual run numbers:

- At epoch 80: val loss was at its **lowest point — 0.0063**
- At epoch 150: val loss **jumped to 0.0143** — a rise of 0.0080
- At epoch 300: val loss continued rising to **0.0161**

At the same time, training accuracy kept climbing from 0.9980 (epoch 80) to 0.9987 (epoch 300). That gap — training accuracy still improving while validation loss rises — is the definition of overfitting. The model is no longer learning general patterns from the data; it is memorizing the training records and losing the ability to generalize to new connections.

The epoch tuning chart (epoch_tuning.png) shows this visually: the red val loss line bottoms out at epoch 80 then bends upward at epochs 150 and 300, while the blue accuracy lines continue climbing.

---

**🖊 My observations and comments:**

I would have trained the model on many more epoch levels on a real project to find the best fit is between 80 and 150 epochs.

---
---

## Reflection Question 3
### How much of what you built do you genuinely understand versus trusted the agent on — and name one specific part you would struggle to rebuild alone?

**Agent context:**

Areas where the process is clear from the project work:

- **Why sigmoid output:** The last layer uses `Dense(1, activation='sigmoid')` because this is a binary problem — each network connection is either normal (0) or attack (1). Sigmoid squashes the output to a probability between 0.0 and 1.0. A score of 1.0000 means the model is confident it is an attack; 0.0035 means it is almost certain it is normal. This is regression classification — continuous probability output, not a hard label.
- **Why overfitting happened:** Removing Dropout removed the regularization that was preventing the model from memorizing training data. At epoch 150 and beyond the model had seen the training records enough times that it started fitting to noise rather than patterns.
- **Why val loss rising matters more than val accuracy:** Val accuracy can stay high even when the model is overfitting because it is still getting most predictions right. Val loss captures the confidence of wrong predictions — a rising val loss means the model is becoming more confidently wrong on the validation set, even if overall accuracy looks stable.

Areas that would be harder to rebuild without help:

- The preprocessing cell — specifically the `reindex(columns=train.columns, fill_value=0)` step that aligns the test set one-hot columns to match the training set. This handles the case where the test set is missing some one-hot categories that appear in training. The logic is clear in hindsight but would be easy to miss when building from scratch.
- The dual-axis chart in Cell 7 — using `twinx()` to plot accuracy and loss on separate y-axes in the same figure.

---

**🖊 My observations and comments:**

I understand the steps that are being done in the Python code, the statistical methods that are being used and how the model in being trained. I can follow the functions in the code but it would take me a long time to research and build this code without relying on Claude.

---

*CSC-114 Artificial Intelligence I | Fayetteville Technical Community College | Summer 2026*
