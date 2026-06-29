# Regression_LLM

**CSC-114 Artificial Intelligence I · Module 4**
*Scalar Regression — California Housing Price Prediction*

---

## What This Project Does

This project builds a scalar regression model using the California Housing
dataset from the 1990 census. The model predicts the **median home price**
of a California district given 8 numeric features per district.

This is a **regression** problem — the model outputs a single continuous
number (a dollar amount), not a category. That makes it fundamentally
different from the binary classification (IMDB sentiment) and multiclass
classification (Reuters topics) models built earlier in the course.

---

## Files

| File | Description |
|---|---|
| `Regression_LLM.ipynb` | Main Jupyter notebook — run this |
| `README.md` | This file |

---

## How to Run

### Option A — Google Colab (recommended)
1. Upload `Regression_LLM.ipynb` to [colab.research.google.com](https://colab.research.google.com)
2. Run all cells top to bottom (Runtime → Run all)
3. The first run downloads the California Housing dataset automatically

### Option B — Local Jupyter
1. Install dependencies (see below)
2. Open a terminal and run: `jupyter notebook`
3. Open `Regression_LLM.ipynb` and run all cells

---

## Dependencies

```bash
pip install tensorflow keras numpy matplotlib
```

> **Backend note:** This notebook explicitly sets the Keras backend to
> **TensorFlow**. The line `os.environ["KERAS_BACKEND"] = "tensorflow"`
> appears at the top of Step 1 and must run before any Keras import.
> If you previously used JAX or PyTorch in another notebook, this cell
> overrides it for this session.

---

## Dataset

**California Housing Prices (small version)**
- Source: 1990 U.S. Census, shipped inside Keras
- 480 training districts, 120 test districts
- 8 features per district: longitude, latitude, median house age,
  population, households, median income, total rooms, total bedrooms
- Target: median home value in dollars ($60,000 – $500,000)

---

## Model Architecture

```
Input (8 features, normalized)
        ↓
Dense(64, activation="relu")
        ↓
Dense(64, activation="relu")
        ↓
Dense(1)            ← no activation — output is unconstrained
        ↓
Predicted price (scaled, multiply by 100,000 for dollars)
```

| Setting | Choice | Reason |
|---|---|---|
| Final activation | None | Regression output must be any value |
| Loss | `mean_squared_error` | Standard regression loss |
| Metric | `mean_absolute_error` | Readable as dollars off |
| Optimizer | `adam` | Reliable default |
| Backend | TensorFlow | Explicitly required |

---

## Validation Strategy

Because the dataset is small (480 training samples), a single
validation split would be unreliable. This project uses
**K-fold cross-validation (k=4)**:

- Divide training data into 4 equal folds
- Train 4 separate models, each using a different fold as validation
- Average the 4 validation scores for a reliable estimate
- Use the averaged epoch curve to find the overfitting point (~epoch 130)

---

## Step-by-Step Execution — Code and Output

### Step 1 — Set the backend to TensorFlow

```python
import os
os.environ["KERAS_BACKEND"] = "tensorflow"  # Force TensorFlow — not JAX, not PyTorch

import numpy as np
import matplotlib.pyplot as plt
import keras
from keras import layers

print("Keras version :", keras.__version__)
print("Backend       :", keras.backend.backend())
```

**Output:**
```
Keras version : 3.13.2
Backend       : tensorflow
```

---

### Step 2 — Load the California Housing dataset

```python
from keras.datasets import california_housing

(train_data, train_targets), (test_data, test_targets) = (
    california_housing.load_data(version="small")
)

print("Training samples :", train_data.shape)
print("Test samples     :", test_data.shape)
print("Sample targets   :", train_targets[:5])
```

**Output:**
```
Downloading data from https://storage.googleapis.com/tensorflow/tf-keras-datasets/california_housing.npz
743530/743530 ━━━━━━━━━━━━━━━━━━━━ 0s 0us/step
Training samples : (480, 8)
Test samples     : (120, 8)
Sample targets   : [228400. 132900.  60000.  95200. 107000.]
```

> The dataset downloads once (~743 KB) on first run and is cached automatically.
> 480 training districts, 120 test districts, 8 features each.

---

### Step 3 — Normalize the features

```python
mean = train_data.mean(axis=0)
std  = train_data.std(axis=0)

x_train = (train_data - mean) / std
x_test  = (test_data  - mean) / std

y_train = train_targets / 100000
y_test  = test_targets  / 100000

print("x_train mean (should be ~0):", x_train.mean(axis=0).round(3))
print("x_train std  (should be ~1):", x_train.std(axis=0).round(3))
print("y_train range: %.2f to %.2f" % (y_train.min(), y_train.max()))
```

**Output:**
```
x_train mean (should be ~0): [ 0.     0.001  0.     0.    -0.    -0.    -0.     0.   ]
x_train std  (should be ~1): [1. 1. 1. 1. 1. 1. 1. 1.]
y_train range: 0.60 to 5.00
```

> Mean is effectively 0 and std is 1 for all 8 features — normalization confirmed.
> Targets scaled to 0.60–5.00 (divide by 100,000; multiply back after training for dollar values).

---

### Step 4 — Define the model

```python
def get_model():
    model = keras.Sequential([
        layers.Dense(64, activation="relu"),
        layers.Dense(64, activation="relu"),
        layers.Dense(1),   # No activation — regression output, any value
    ])
    model.compile(
        optimizer="adam",
        loss="mean_squared_error",
        metrics=["mean_absolute_error"],
    )
    return model

get_model().summary()
```

**Output:**
```
Model: "sequential"
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┓
┃ Layer (type)                    ┃ Output Shape           ┃       Param # ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━┩
│ dense (Dense)                   │ ?                      │   0 (unbuilt) │
├─────────────────────────────────┼────────────────────────┼───────────────┤
│ dense_1 (Dense)                 │ ?                      │   0 (unbuilt) │
├─────────────────────────────────┼────────────────────────┼───────────────┤
│ dense_2 (Dense)                 │ ?                      │   0 (unbuilt) │
└─────────────────────────────────┴────────────────────────┴───────────────┘
Total params: 0 (0.00 B)
Trainable params: 0 (0.00 B)
Non-trainable params: 0 (0.00 B)
```

> Params show 0 (unbuilt) because Keras uses automatic shape inference —
> weights are not created until the first real batch flows through in Step 5.
> This is expected, not an error.

---

### Step 5 — K-fold cross-validation (50 epochs)

```python
k = 4
num_val_samples = len(x_train) // k
num_epochs = 50
all_scores = []

for i in range(k):
    print(f"Processing fold #{i + 1}")
    fold_x_val   = x_train[i * num_val_samples : (i + 1) * num_val_samples]
    fold_y_val   = y_train[i * num_val_samples : (i + 1) * num_val_samples]
    fold_x_train = np.concatenate(
        [x_train[: i * num_val_samples], x_train[(i + 1) * num_val_samples :]], axis=0)
    fold_y_train = np.concatenate(
        [y_train[: i * num_val_samples], y_train[(i + 1) * num_val_samples :]], axis=0)
    model = get_model()
    model.fit(fold_x_train, fold_y_train, epochs=num_epochs, batch_size=16, verbose=0)
    scores = model.evaluate(fold_x_val, fold_y_val, verbose=0)
    val_loss, val_mae = scores
    all_scores.append(val_mae)

print("MAE per fold :", [round(v, 3) for v in all_scores])
print("Average MAE  :", round(np.mean(all_scores), 3))
print("Avg dollars off: $%.0f" % (np.mean(all_scores) * 100000))
```

**Output:**
```
Processing fold #1
Processing fold #2
Processing fold #3
Processing fold #4

MAE per fold : [0.302, 0.299, 0.246, 0.317]
Average MAE  : 0.291
Avg dollars off: $29099
```

> Individual fold scores range from 0.246 to 0.317 — a wide swing that shows why
> a single validation split would be unreliable on this small dataset.
> The average of 0.291 (~$29,099 off) is the reliable number.

---

### Step 6 — K-fold over 200 epochs to find the overfitting point

```python
k = 4
num_val_samples = len(x_train) // k
num_epochs = 200
all_mae_histories = []

for i in range(k):
    print(f"Processing fold #{i + 1}")
    fold_x_val   = x_train[i * num_val_samples : (i + 1) * num_val_samples]
    fold_y_val   = y_train[i * num_val_samples : (i + 1) * num_val_samples]
    fold_x_train = np.concatenate(
        [x_train[: i * num_val_samples], x_train[(i + 1) * num_val_samples :]], axis=0)
    fold_y_train = np.concatenate(
        [y_train[: i * num_val_samples], y_train[(i + 1) * num_val_samples :]], axis=0)
    model = get_model()
    history = model.fit(
        fold_x_train, fold_y_train,
        validation_data=(fold_x_val, fold_y_val),
        epochs=num_epochs, batch_size=16, verbose=0)
    mae_history = history.history["val_mean_absolute_error"]
    all_mae_histories.append(mae_history)

average_mae_history = [
    np.mean([x[i] for x in all_mae_histories]) for i in range(num_epochs)
]
print("Done. Plotting validation MAE curve...")
```

**Output:**
```
Processing fold #1
Processing fold #2
Processing fold #3
Processing fold #4
Done. Plotting validation MAE curve...
```

---

### Step 7 — Plot the validation MAE curve

```python
# Full curve
epochs_full = range(1, len(average_mae_history) + 1)
plt.plot(epochs_full, average_mae_history)
plt.xlabel("Epochs")
plt.ylabel("Validation MAE")
plt.title("K-fold Validation MAE — all 200 epochs")
plt.show()

# Zoomed: drop the first 10 noisy epochs
truncated = average_mae_history[10:]
epochs_zoom = range(10, len(truncated) + 10)
plt.plot(epochs_zoom, truncated)
plt.xlabel("Epochs")
plt.ylabel("Validation MAE")
plt.title("K-fold Validation MAE — epochs 10 onward (zoomed)")
plt.show()
```

**Output — Plot 1 (all 200 epochs):**

- MAE starts near 1.0 at epoch 1 (random weights, terrible predictions)
- Drops sharply through epoch ~25 as the model learns the main patterns
- Flattens around 0.30 for the remainder of the run
- No sharp upward turn — this model plateaus rather than dramatically overfitting

**Output — Plot 2 (epoch 10 onward, zoomed):**

- MAE continues falling steeply from ~0.41 through epoch ~50
- Bottoms out around 0.28–0.29 near epoch 50
- Remains noisy but flat from epoch 75 onward, hovering around 0.29–0.31
- Safe epoch count: **130** (well inside the flat zone, before any risk of overfitting)

---

### Step 8 — Train the final model and evaluate

```python
model = get_model()
model.fit(x_train, y_train, epochs=130, batch_size=16, verbose=0)
test_mse, test_mae = model.evaluate(x_test, y_test, verbose=0)

print("Test MSE        : %.4f" % test_mse)
print("Test MAE        : %.4f" % test_mae)
print("Dollars off avg : $%.0f" % (test_mae * 100000))
```

**Output:**
```
Test MSE        : 0.2859
Test MAE        : 0.2944
Dollars off avg : $29441
```

> Final model trained on all 480 training samples for 130 epochs.
> Evaluated once on the sealed 120-sample test set.
> Off by ~$29,441 on average on prices ranging from $60,000 to $500,000.

---

### Step 9 — Generate predictions on new data

```python
predictions = model.predict(x_test, verbose=0)

print("First 5 predictions vs actual prices:")
print(f"{'Predicted':>12}  {'Actual':>12}  {'Off by':>12}")
print("-" * 42)
for i in range(5):
    pred   = predictions[i][0] * 100000
    actual = y_test[i]         * 100000
    diff   = abs(pred - actual)
    print(f"${pred:>10,.0f}  ${actual:>10,.0f}  ${diff:>10,.0f}")
```

**Output:**
```
First 5 predictions vs actual prices:
   Predicted        Actual        Off by
------------------------------------------
$   250,011  $   218,800  $    31,211
$   182,687  $   218,400  $    35,713
$   115,255  $    93,800  $    21,455
$   211,774  $   173,400  $    38,374
$   203,813  $   229,700  $    25,887
```

> Each output is a single unconstrained number — the regression model's predicted
> median home price in dollars. Individual predictions are off by $21k–$38k,
> consistent with the overall test MAE of ~$29,441.

---

## Actual Run Results Summary

| Step | What was measured | Result |
|---|---|---|
| Step 2 | Dataset loaded | 480 train / 120 test / 8 features |
| Step 3 | Normalization confirmed | Mean ~0, Std ~1, targets 0.60–5.00 |
| Step 5 | K-fold MAE (50 epochs) | Avg $29,099 off |
| Step 7 | Overfitting point | Plateaus ~epoch 50, safe zone to epoch 130 |
| Step 8 | Final test MAE | 0.2944 (~$29,441 off) |
| Step 9 | Sample predictions | $21k–$38k off per district |

---

## Key Concepts Demonstrated

- **Feature normalization** — subtract mean, divide by std, computed from training data only
- **Target scaling** — divide prices by 100,000 to keep values in a small range during training
- **K-fold cross-validation** — reliable evaluation when data is limited
- **Overfitting detection** — watching the validation MAE curve across 200 epochs
- **No output activation** — regression models must not constrain the output range

---

*Source: Chollet & Watson, Deep Learning with Python, 3rd Edition (Manning), Chapter 4.*
*Backend explicitly set to TensorFlow per assignment requirements.*
*Output captured from live Colab run: https://colab.research.google.com/drive/1dCTCEiQxPXmX0LCC3NvFztS58lobaojd*
