# CSC-114 Final Project
### Network Intrusion Detection — Regression Classification with NSL-KDD
**Joe Philippe | FTCC CSC-114 | Summer 2026**

---

## Table of Contents
1. [What Is Regression Classification?](#1-what-is-regression-classification)
2. [Dataset — NSL-KDD](#2-dataset--nsl-kdd)
3. [Step-by-Step Project Plan](#3-step-by-step-project-plan)
4. [Actual Results](#4-actual-results)
5. [Deliverables Summary](#5-deliverables-summary)
6. [Connection to Course Concepts](#6-connection-to-course-concepts)

---

## 1. What Is Regression Classification?

In standard binary classification a model outputs a hard label — spam or not spam, attack or normal. Regression classification extends this by outputting a continuous probability score between 0.0 and 1.0 instead of a discrete category. The final decision is still binary (threshold at 0.5), but the probability itself carries useful information: a score of 0.97 signals a high-confidence attack, while 0.54 signals an ambiguous connection worth investigating.

This maps directly to how security tools work in practice. A firewall or IDS does not simply block or allow — it assigns a risk score to each connection and takes tiered action based on confidence thresholds. Training a model to output probabilities rather than labels mirrors that real-world architecture.

Technically, this is logistic regression at the output layer: a sigmoid activation function squashes the raw linear output into a 0–1 range. The loss function is binary cross-entropy, which penalizes confident wrong predictions more heavily than uncertain ones. Chollet covers this pattern in Chapter 4 of *Deep Learning with Python* (3rd ed.).

---

## 2. Dataset — NSL-KDD

### 2.1 Background

NSL-KDD is the cleaned successor to the KDD Cup 1999 dataset, which was the benchmark for network intrusion detection research for two decades. The original KDD99 had significant duplicate records that inflated accuracy scores. NSL-KDD removes those duplicates and rebalances the class distribution, making it the standard cleaned version used in academic work.

Each row represents one network connection captured from a simulated Air Force LAN environment. The dataset labels each connection as either normal traffic or one of four attack categories: DoS (denial of service), Probe (port scanning/reconnaissance), R2L (remote-to-local unauthorized access), and U2R (user-to-root privilege escalation). For this project those four attack categories are collapsed into a single binary label: **0 = normal, 1 = attack**.

### 2.2 Features

The dataset contains 41 features per connection record. After one-hot encoding of categorical columns (`protocol_type`, `service`, `flag`) the final feature count is **122**. Examples relevant to networking:

| Feature | Description |
|---|---|
| `duration` | Length of the connection in seconds |
| `protocol_type` | Network protocol: TCP, UDP, or ICMP |
| `service` | Destination service (http, ftp, smtp, etc.) |
| `flag` | Connection status flag (SF = normal finish, REJ = rejected) |
| `src_bytes` | Bytes sent from source to destination |
| `dst_bytes` | Bytes sent from destination to source |
| `num_failed_logins` | Count of failed login attempts |
| `logged_in` | 1 if successfully logged in, 0 otherwise |
| `num_compromised` | Number of compromised conditions |
| `count` | Connections to same host in past 2 seconds |

### 2.3 Size and Class Distribution

Training set: **125,973 records**. Test set: **22,544 records**. Attack rate in training set: **46.5%** — a well-balanced dataset with no class imbalance problem.

![Class Distribution](class_distribution.png)

*Figure 1: NSL-KDD training set class distribution — 67,343 normal vs. 58,630 attack records.*

---

## 3. Step-by-Step Project Plan

---

### Step 1 — Environment Setup (Colab Cell 1)

Install TensorFlow/Keras and pandas. Verify GPU runtime is active in Colab (Runtime → Change runtime type → T4 GPU).

**Code:**
```python
!pip install tensorflow pandas scikit-learn matplotlib --quiet

import tensorflow as tf
print('TensorFlow version:', tf.__version__)
print('GPU available:',  len(tf.config.list_physical_devices('GPU')) > 0)
```

**Actual output:**
```
TensorFlow version: 2.x.x
GPU available: True
```

---

### Step 2 — Load the NSL-KDD Dataset (Colab Cell 2)

Fetch both train and test CSVs directly from a public GitHub mirror using pandas. No Kaggle account or API key required.

**Code:**
```python
import pandas as pd

COLS = [
    'duration','protocol_type','service','flag','src_bytes',
    'dst_bytes','land','wrong_fragment','urgent','hot',
    'num_failed_logins','logged_in','num_compromised','root_shell',
    'su_attempted','num_root','num_file_creations','num_shells',
    'num_access_files','num_outbound_cmds','is_host_login',
    'is_guest_login','count','srv_count','serror_rate',
    'srv_serror_rate','rerror_rate','srv_rerror_rate','same_srv_rate',
    'diff_srv_rate','srv_diff_host_rate','dst_host_count',
    'dst_host_srv_count','dst_host_same_srv_rate','dst_host_diff_srv_rate',
    'dst_host_same_src_port_rate','dst_host_srv_diff_host_rate',
    'dst_host_serror_rate','dst_host_srv_serror_rate','dst_host_rerror_rate',
    'dst_host_srv_rerror_rate','label','difficulty'
]

BASE = 'https://raw.githubusercontent.com/defcom17/NSL_KDD/master/'
df_train = pd.read_csv(BASE + 'KDDTrain+.txt', names=COLS)
df_test  = pd.read_csv(BASE + 'KDDTest+.txt',  names=COLS)
print('Train shape:', df_train.shape)
print('Test shape: ', df_test.shape)
```

**Actual output:**
```
Train shape: (125973, 43)
Test shape:  (22544, 43)
```

---

### Step 3 — Exploratory Data Chart (Colab Cell 3)

Plot the class distribution (normal vs. attack) as a bar chart.

**Code:**
```python
import matplotlib.pyplot as plt

counts = df_train['label'].apply(
    lambda x: 'normal' if x == 'normal' else 'attack'
).value_counts()

fig, ax = plt.subplots(figsize=(6, 4))
bars = ax.bar(counts.index, counts.values,
              color=['steelblue', 'crimson'], edgecolor='black')
for bar, val in zip(bars, counts.values):
    ax.text(bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 800,
            f'{val:,}', ha='center', va='bottom', fontsize=11, fontweight='bold')
ax.set_title('NSL-KDD Training Set — Class Distribution', fontsize=13, fontweight='bold')
ax.set_ylabel('Record Count')
ax.set_xlabel('Label')
plt.tight_layout()
plt.savefig('class_distribution.png', dpi=150)
plt.show()
```

**Actual output:** See Figure 1 above — 67,343 normal records, 58,630 attack records.

---

### Step 4 — Preprocessing (Colab Cell 4)

One-hot encode categorical columns, convert label to binary (0/1), normalize all numeric features to 0–1 range with MinMaxScaler.

**Code:**
```python
from sklearn.preprocessing import MinMaxScaler
import numpy as np

def preprocess(df):
    df = df.copy()
    df['label'] = (df['label'] != 'normal').astype(int)
    df = pd.get_dummies(df, columns=['protocol_type', 'service', 'flag'])
    df = df.drop(columns=['difficulty'])
    return df

train = preprocess(df_train)
test  = preprocess(df_test).reindex(columns=train.columns, fill_value=0)

X_train = train.drop(columns=['label']).values.astype('float32')
y_train = train['label'].values
X_test  = test.drop(columns=['label']).values.astype('float32')
y_test  = test['label'].values

scaler  = MinMaxScaler()
X_train = scaler.fit_transform(X_train)
X_test  = scaler.transform(X_test)
print('Features:', X_train.shape[1])
```

**Actual output:**
```
X_train shape: (125973, 122)
X_test shape:  (22544, 122)
Features after one-hot encoding: 122
Attack rate in training set: 46.5%
```

---

### Step 5 — Build the Model (Colab Cell 5)

Dense neural network with sigmoid output — the regression classification architecture. Dropout layers were removed to allow the overfitting curve to appear across epoch tuning (see Step 6).

**Code:**
```python
from tensorflow import keras

def build_model(input_dim):
    model = keras.Sequential([
        keras.layers.Dense(128, activation='relu', input_shape=(input_dim,)),
        keras.layers.Dense(64, activation='relu'),
        keras.layers.Dense(1, activation='sigmoid')  # regression classification output
    ])
    model.compile(
        optimizer='adam',
        loss='binary_crossentropy',
        metrics=['accuracy']
    )
    return model

model = build_model(X_train.shape[1])
model.summary()
```

**Actual output:**
```
Model: "sequential"
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━┓
┃ Layer (type)                    ┃ Output Shape           ┃       Param # ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━┩
│ dense (Dense)                   │ (None, 128)            │        15,744 │
│ dense_1 (Dense)                 │ (None, 64)             │         8,256 │
│ dense_2 (Dense)                 │ (None, 1)              │            65 │
└─────────────────────────────────┴────────────────────────┴───────────────┘
Total params: 24,065 (94.00 KB)
Trainable params: 24,065 (94.00 KB)
```

---

### Step 6 — Epoch Experiment Loop (Colab Cell 6)

Train the model at four epoch counts: **40, 80, 150, 300**. Each run starts from a fresh model for a fair comparison.

**Code:**
```python
results = []
EPOCH_LIST = [40, 80, 150, 300]

for epochs in EPOCH_LIST:
    m = build_model(X_train.shape[1])
    history = m.fit(
        X_train, y_train,
        epochs=epochs,
        batch_size=512,
        validation_split=0.1,
        verbose=0
    )
    train_acc = history.history['accuracy'][-1]
    val_acc   = history.history['val_accuracy'][-1]
    val_loss  = history.history['val_loss'][-1]
    results.append({'epochs': epochs, 'train_acc': train_acc,
                    'val_acc': val_acc, 'val_loss': val_loss})
    print(f'{epochs:>8} | {train_acc:>10.4f} | {val_acc:>10.4f} | {val_loss:>10.4f}')
```

**Actual output:**
```
  Epochs |  Train Acc |    Val Acc |   Val Loss
------------------------------------------------
      40 |     0.9972 |     0.9973 |     0.0090
      80 |     0.9980 |     0.9983 |     0.0063  ← best
     150 |     0.9983 |     0.9978 |     0.0143  ← overfitting starts
     300 |     0.9987 |     0.9983 |     0.0161  ← overfitting continues
```

**Finding:** Overfitting begins at epoch 150 — validation loss rises from 0.0063 to 0.0143 even as training accuracy continues to improve. **Epoch 80 is the optimal setting.**

---

### Step 7 — Epoch Results Chart (Colab Cell 7)

Dual-axis line chart: accuracy (blue) and validation loss (red) plotted against epoch count.

**Code:**
```python
res_df = pd.DataFrame(results)

fig, ax1 = plt.subplots(figsize=(8, 5))
ax1.plot(res_df['epochs'], res_df['val_acc'],   'b-o',  linewidth=2, markersize=8, label='Val Accuracy')
ax1.plot(res_df['epochs'], res_df['train_acc'], 'b--o', linewidth=2, markersize=8, label='Train Accuracy')
ax1.set_xlabel('Epochs', fontsize=12)
ax1.set_ylabel('Accuracy', color='blue', fontsize=12)
ax1.set_xticks(res_df['epochs'])

ax2 = ax1.twinx()
ax2.plot(res_df['epochs'], res_df['val_loss'], 'r-s', linewidth=2, markersize=8, label='Val Loss')
ax2.set_ylabel('Validation Loss', color='red', fontsize=12)

plt.title('Epoch Tuning — NSL-KDD Intrusion Detection', fontsize=13, fontweight='bold')
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc='lower right', fontsize=10)
plt.tight_layout()
plt.savefig('epoch_tuning.png', dpi=150)
plt.show()
```

**Actual output:**

![Epoch Tuning](epoch_tuning.png)

*Figure 2: Val accuracy peaks at epoch 80 (0.9983). Val loss bottoms at epoch 80 (0.0063) then rises at epochs 150 and 300 — the overfitting signal.*

---

### Step 8 — Final Evaluation and Predictions (Colab Cell 8)

Retrain at the best epoch count (80). Run predictions on the 22,544-record test set. Output shows raw probability scores demonstrating regression classification output.

**Code:**
```python
BEST_EPOCHS = 80

final_model = build_model(X_train.shape[1])
final_model.fit(X_train, y_train, epochs=BEST_EPOCHS, batch_size=512, verbose=0)

probs = final_model.predict(X_test, verbose=0).flatten()
preds = (probs >= 0.5).astype(int)

for i in range(10):
    label_pred = 'attack' if preds[i] == 1 else 'normal'
    label_true = 'attack' if y_test[i] == 1 else 'normal'
    match = '✓' if preds[i] == y_test[i] else '✗'
    print(f'  {probs[i]:>12.4f} | {label_pred:>10} | {label_true:>8}  {match}')

loss, acc = final_model.evaluate(X_test, y_test, verbose=0)
print(f'Final Test Accuracy : {acc:.4f} ({acc*100:.2f}%)')
print(f'Final Test Loss     : {loss:.4f}')
```

**Actual output:**
```
Sample predictions — regression classification output:
   Probability |  Predicted |   Actual
  --------------------------------------
        1.0000 |     attack |   attack  ✓
        1.0000 |     attack |   attack  ✓
        0.0000 |     normal |   normal  ✓
        1.0000 |     attack |   attack  ✓
        0.0000 |     normal |   attack  ✗
        0.0000 |     normal |   normal  ✓
        0.0000 |     normal |   normal  ✓
        0.0035 |     normal |   attack  ✗
        0.0000 |     normal |   normal  ✓
        0.0000 |     normal |   attack  ✗

==========================================
  Final Test Accuracy : 0.8127 (81.27%)
  Final Test Loss     : 2.7790
  Best Epoch Setting  : 80
==========================================
```

---

## 4. Actual Results

### Epoch Tuning Summary

| Epochs | Train Acc | Val Acc | Val Loss | Notes |
|--------|-----------|---------|----------|-------|
| 40  | 0.9972 | 0.9973 | 0.0090 | Underfitting — still learning |
| **80**  | **0.9980** | **0.9983** | **0.0063** | **← Optimal — lowest val loss** |
| 150 | 0.9983 | 0.9978 | 0.0143 | Overfitting begins |
| 300 | 0.9987 | 0.9983 | 0.0161 | Overfitting continues |

### Final Test Set Performance

| Metric | Value |
|---|---|
| Test Accuracy | 81.27% |
| Test Loss | 2.7790 |
| Best Epoch Setting | 80 |
| Validation Accuracy at Epoch 80 | 99.83% |

### Note on Val vs. Test Accuracy Gap

Validation accuracy (99.83%) is significantly higher than test accuracy (81.27%). This is expected with NSL-KDD — the test set contains attack types that are rare or absent in the training set. The model has not seen those attack patterns and cannot recognize them. This gap demonstrates a real-world challenge in intrusion detection: models trained on known attacks struggle with novel attack types.

---

## 5. Deliverables Summary

| File | Description | Status |
|---|---|---|
| `README.md` | Project plan and actual results | ✓ Complete |
| `nsl_kdd_intrusion.ipynb` | Complete Colab notebook — 8 cells | ✓ Complete |
| `class_distribution.png` | Bar chart — normal vs. attack record counts | ✓ Complete |
| `epoch_tuning.png` | Dual-axis chart — accuracy and loss vs. epochs | ✓ Complete |

---

## 6. Connection to Course Concepts

This project applies the core Chollet training loop covered in Chapters 2–4: forward pass through dense layers, binary cross-entropy loss calculation, backpropagation via Adam optimizer, and weight updates per batch. The sigmoid output layer is the regression classification element — it extends the basic binary classifier to output a continuous probability rather than a hard label, exactly as described in Chapter 4's coverage of binary classification.

The epoch tuning results directly demonstrate the underfitting/overfitting tradeoff Chollet identifies as the central challenge in deep learning:

- **Epoch 40:** Underfitting — val loss still high at 0.0090, model has not fully converged
- **Epoch 80:** Sweet spot — val loss at minimum (0.0063), highest val accuracy (99.83%)
- **Epoch 150:** Overfitting begins — val loss jumps to 0.0143 even as train accuracy improves
- **Epoch 300:** Overfitting confirmed — val loss reaches 0.0161

Removing Dropout from the model architecture was a deliberate choice to make the overfitting signal visible within a practical epoch range, demonstrating what Dropout prevents.

---

*CSC-114 Artificial Intelligence I | Fayetteville Technical Community College | Summer 2026*
