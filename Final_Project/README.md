# CSC-114 Final Project Plan
### Network Intrusion Detection — Regression Classification with NSL-KDD
**Joe Philippe | FTCC CSC-114 | Summer 2026**

---

## Table of Contents
1. [What Is Regression Classification?](#1-what-is-regression-classification)
2. [Dataset — NSL-KDD](#2-dataset--nsl-kdd)
3. [Step-by-Step Project Plan](#3-step-by-step-project-plan)
4. [Deliverables Summary](#4-deliverables-summary)
5. [Connection to Course Concepts](#5-connection-to-course-concepts)

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

The dataset contains 41 features per connection record. Examples relevant to networking:

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

### 2.3 Size

Training set: **125,973 records**. Test set: **22,544 records**. Both are available as raw CSV files from a public GitHub mirror, loadable in Colab with a single `pandas.read_csv()` call — no Kaggle account or API key required.

---

## 3. Step-by-Step Project Plan

---

### Step 1 — Environment Setup (Colab Cell 1)

Install TensorFlow/Keras and pandas. Verify GPU runtime is active in Colab (Runtime → Change runtime type → T4 GPU).

**Code:**
```python
!pip install tensorflow pandas scikit-learn matplotlib --quiet
```

**Expected output:** Installation log, no errors.

---

### Step 2 — Load the NSL-KDD Dataset (Colab Cell 2)

Fetch both train and test CSVs directly from the public GitHub mirror using pandas. Assign column names from the KDD feature list.

**Code:**
```python
import pandas as pd

COLS = [
    "duration","protocol_type","service","flag","src_bytes",
    "dst_bytes","land","wrong_fragment","urgent","hot",
    "num_failed_logins","logged_in","num_compromised","root_shell",
    "su_attempted","num_root","num_file_creations","num_shells",
    "num_access_files","num_outbound_cmds","is_host_login",
    "is_guest_login","count","srv_count","serror_rate",
    "srv_serror_rate","rerror_rate","srv_rerror_rate","same_srv_rate",
    "diff_srv_rate","srv_diff_host_rate","dst_host_count",
    "dst_host_srv_count","dst_host_same_srv_rate","dst_host_diff_srv_rate",
    "dst_host_same_src_port_rate","dst_host_srv_diff_host_rate",
    "dst_host_serror_rate","dst_host_srv_serror_rate","dst_host_rerror_rate",
    "dst_host_srv_rerror_rate","label","difficulty"
]

BASE = 'https://raw.githubusercontent.com/defcom17/NSL_KDD/master/'
df_train = pd.read_csv(BASE + 'KDDTrain+.txt', names=COLS)
df_test  = pd.read_csv(BASE + 'KDDTest+.txt',  names=COLS)
print(df_train.shape, df_test.shape)
```

**Expected output:** `(125973, 43)  (22544, 43)`

---

### Step 3 — Exploratory Data Chart (Colab Cell 3)

Plot the class distribution (normal vs. attack) as a bar chart. This is the **first chart deliverable** for the README.

**Code:**
```python
import matplotlib.pyplot as plt

counts = df_train['label'].apply(
    lambda x: 'normal' if x == 'normal' else 'attack'
).value_counts()

counts.plot(kind='bar', color=['steelblue','crimson'], edgecolor='black')
plt.title('NSL-KDD Training Set — Class Distribution')
plt.ylabel('Record Count')
plt.xticks(rotation=0)
plt.tight_layout()
plt.savefig('class_distribution.png', dpi=150)
plt.show()
```

**Expected output:** Bar chart image saved as `class_distribution.png` — screenshot this for the README.

> **Chart placeholder — replace with actual output after running:**
> ![Class Distribution](class_distribution.png)

---

### Step 4 — Preprocessing (Colab Cell 4)

Encode categorical columns (`protocol_type`, `service`, `flag`) with one-hot encoding. Convert the label column to binary (0/1). Normalize all numeric features to 0–1 range using MinMaxScaler.

**Code:**
```python
from sklearn.preprocessing import MinMaxScaler
import numpy as np

def preprocess(df):
    df = df.copy()
    df['label'] = (df['label'] != 'normal').astype(int)
    df = pd.get_dummies(df, columns=['protocol_type','service','flag'])
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

**Expected output:** `Features: ~122` (varies with one-hot expansion)

---

### Step 5 — Build the Model (Colab Cell 5)

Define a dense neural network with sigmoid output. This is the regression classification architecture — `Dense(1, activation='sigmoid')` produces a probability score between 0.0 and 1.0 for each connection.

**Code:**
```python
import tensorflow as tf
from tensorflow import keras

def build_model(input_dim):
    model = keras.Sequential([
        keras.layers.Dense(128, activation='relu', input_shape=(input_dim,)),
        keras.layers.Dropout(0.3),
        keras.layers.Dense(64, activation='relu'),
        keras.layers.Dropout(0.2),
        keras.layers.Dense(1, activation='sigmoid')   # regression classification output
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

**Expected output:** Model summary table showing layer shapes and parameter counts.

---

### Step 6 — Epoch Experiment Loop (Colab Cell 6)

Train the model at four different epoch counts. Record training accuracy, validation accuracy, and validation loss for each run. This is the **core tuning deliverable**.

**Code:**
```python
results = []
EPOCH_LIST = [5, 10, 20, 40]

for epochs in EPOCH_LIST:
    m = build_model(X_train.shape[1])
    history = m.fit(
        X_train, y_train,
        epochs=epochs,
        batch_size=512,
        validation_split=0.1,
        verbose=0
    )
    val_acc   = history.history['val_accuracy'][-1]
    val_loss  = history.history['val_loss'][-1]
    train_acc = history.history['accuracy'][-1]
    results.append({
        'epochs': epochs,
        'train_acc': train_acc,
        'val_acc': val_acc,
        'val_loss': val_loss
    })
    print(f'Epochs {epochs:2d} | train_acc={train_acc:.4f} | val_acc={val_acc:.4f} | val_loss={val_loss:.4f}')
```

**Expected output:** One printed line per epoch count showing accuracy and loss metrics.

> **Results table placeholder — replace with actual output after running:**
>
> | Epochs | Train Acc | Val Acc | Val Loss |
> |--------|-----------|---------|----------|
> | 5  | — | — | — |
> | 10 | — | — | — |
> | 20 | — | — | — |
> | 40 | — | — | — |

---

### Step 7 — Epoch Results Chart (Colab Cell 7)

Plot validation accuracy and validation loss across epoch counts. This is the **second chart deliverable** — it visually shows the underfitting-to-overfitting curve.

**Code:**
```python
import pandas as pd
res_df = pd.DataFrame(results)

fig, ax1 = plt.subplots(figsize=(8,5))
ax1.plot(res_df['epochs'], res_df['val_acc'],   'b-o',  label='Val Accuracy')
ax1.plot(res_df['epochs'], res_df['train_acc'], 'b--o', label='Train Accuracy')
ax1.set_xlabel('Epochs')
ax1.set_ylabel('Accuracy', color='blue')

ax2 = ax1.twinx()
ax2.plot(res_df['epochs'], res_df['val_loss'], 'r-s', label='Val Loss')
ax2.set_ylabel('Validation Loss', color='red')

plt.title('Epoch Tuning — NSL-KDD Intrusion Detection')
fig.legend(loc='lower right', bbox_to_anchor=(0.88, 0.15))
plt.tight_layout()
plt.savefig('epoch_tuning.png', dpi=150)
plt.show()
```

**Expected output:** Dual-axis line chart saved as `epoch_tuning.png` — screenshot this for the README.

> **Chart placeholder — replace with actual output after running:**
> ![Epoch Tuning](epoch_tuning.png)

---

### Step 8 — Final Evaluation and Predictions (Colab Cell 8)

Retrain the model at the best epoch count identified from Step 7. Run predictions on the test set. Print a sample of raw probability scores alongside true labels to demonstrate regression output.

**Code:**
```python
BEST_EPOCHS = 20   # update after running Step 6

final_model = build_model(X_train.shape[1])
final_model.fit(X_train, y_train, epochs=BEST_EPOCHS, batch_size=512, verbose=0)

probs = final_model.predict(X_test).flatten()
preds = (probs >= 0.5).astype(int)

print('Sample predictions (probability | predicted | actual):')
for i in range(10):
    print(f'  {probs[i]:.4f}  |  {preds[i]}  |  {y_test[i]}')

loss, acc = final_model.evaluate(X_test, y_test, verbose=0)
print(f'Test accuracy: {acc:.4f}  |  Test loss: {loss:.4f}')
```

**Expected output:** 10 rows of probability scores plus final test accuracy and loss.

---

## 4. Deliverables Summary

The following will be posted to the `JoePhillippe/CSC-114` GitHub repo:

| File | Description |
|---|---|
| `README.md` | Project explanation, charts, epoch results table, and conclusions |
| `nsl_kdd_intrusion.ipynb` | Complete Colab notebook with all 8 cells |
| `class_distribution.png` | Bar chart of normal vs. attack record counts |
| `epoch_tuning.png` | Dual-axis chart of accuracy and loss across epoch counts |

---

## 5. Connection to Course Concepts

This project applies the core Chollet training loop covered in Chapters 2–4: forward pass through dense layers, binary cross-entropy loss calculation, backpropagation via Adam optimizer, and weight updates per batch. The sigmoid output layer is the regression classification element — it extends the basic binary classifier to output a continuous probability rather than a hard label, exactly as described in Chapter 4's coverage of binary classification.

The epoch tuning section directly demonstrates the underfitting/overfitting tradeoff Chollet identifies as the central challenge in deep learning. Too few epochs: the model has not converged (underfitting, high loss). Too many epochs: the model memorizes training data and validation loss climbs (overfitting). The charts in Steps 3 and 7 make this tradeoff visible.

---

*CSC-114 Artificial Intelligence I | Fayetteville Technical Community College | Summer 2026*
