# Chapter 2 — The Mathematical Building Blocks of Neural Networks
> **Deep Learning with Python, 3rd Ed.** — Chollet  
> Course: CSC 114 · Fayetteville Technical Community College  
> Textbook: https://deeplearningwithpython.io/chapters/chapter02_mathematical-building-blocks

---

## Teaching Goal
Understand *why* each concept exists, not just *what* it is.  
These notes are written to support future instruction — every section includes a "how to explain this to students" angle.

---

## 1. Tensors — The Universal Data Container

### The C++/Python Analogy
You already know this structure:

| C++ | Python | NumPy/Deep Learning |
|-----|--------|---------------------|
| `int x = 5` | `x = 5` | Scalar — rank-0 tensor |
| `int arr[5]` | `list` / `np.array([...])` | Vector — rank-1 tensor |
| `int arr[3][5]` | list of lists | Matrix — rank-2 tensor |
| `int arr[3][3][5]` | list of list of lists | Rank-3 tensor |

A tensor is just a **multidimensional array with a fixed numeric dtype** — the same mental model you have from C arrays, but with metadata (shape, dtype, ndim) attached.

### The Three Attributes Every Tensor Has

```python
import numpy as np

x = np.array([[[5, 78, 2, 34, 0],
               [6, 79, 3, 35, 1],
               [7, 80, 4, 36, 2]],
              [[5, 78, 2, 34, 0],
               [6, 79, 3, 35, 1],
               [7, 80, 4, 36, 2]],
              [[5, 78, 2, 34, 0],
               [6, 79, 3, 35, 1],
               [7, 80, 4, 36, 2]]])

print(x.ndim)   # 3       → rank / number of axes
print(x.shape)  # (3,3,5) → dimensions along each axis
print(x.dtype)  # int64   → data type of every element
```

**Key insight for teaching:** Students confuse "5D vector" with "5D tensor."  
- A **5D vector** = one axis, five entries along it: `shape=(5,)`  
- A **5D tensor** = five axes: `shape=(a,b,c,d,e)`  
Always say *rank* when you mean number of axes. "Rank-3 tensor" is unambiguous. "3D tensor" is not.

---

## 2. Tensor Ranks in Practice — What Real Data Looks Like

| Data Type | Rank | Shape Pattern | Example |
|-----------|------|---------------|---------|
| Single number | 0 | `()` | A loss value |
| 1D feature vector | 1 | `(features,)` | One network packet's stats |
| Dataset of vectors | 2 | `(samples, features)` | Packet dataset |
| Timeseries / sequences | 3 | `(samples, timesteps, features)` | Network flow logs over time |
| Images | 4 | `(samples, height, width, channels)` | Camera feed |
| Video | 5 | `(samples, frames, height, width, channels)` | CCTV footage |

### Networking / Cybersecurity Parallel
Network intrusion detection data fits naturally into rank-2 tensors:
```python
# 10,000 packets, each described by 41 KDD Cup features
packet_data = np.zeros((10000, 41))   # shape (10000, 41)
```
If you add time dimension (flows over 60 seconds, sampled every second):
```python
flow_data = np.zeros((10000, 60, 41))  # shape (samples, timesteps, features)
```
This is exactly how LSTM-based intrusion detection systems store their input.

### MNIST Concrete Example
```python
from keras.datasets import mnist
(train_images, train_labels), (test_images, test_labels) = mnist.load_data()

train_images.shape  # (60000, 28, 28) → 60k grayscale images, 28×28 pixels
train_images.dtype  # uint8           → values 0–255
train_images.ndim   # 3               → rank-3 tensor
```

---

## 3. Tensor Slicing — This is Just C Array Indexing

You know pointer arithmetic and array slicing from C++. NumPy slicing is the same concept with cleaner syntax.

```python
# Select images 10 through 99 (Python slice: end is exclusive)
my_slice = train_images[10:100]         # shape: (90, 28, 28)

# Same thing, explicit on all axes
my_slice = train_images[10:100, :, :]   # : means "all of this axis"

# Crop all images to bottom-right 14×14 pixels
my_slice = train_images[:, 14:, 14:]

# Crop to center 14×14 (negative index = from end)
my_slice = train_images[:, 7:-7, 7:-7]
```

**The batch axis** (axis 0) is always the samples dimension. Deep learning never
processes the full dataset at once — it slices batches:
```python
batch_size = 128
batch_0 = train_images[:128]            # first batch
batch_1 = train_images[128:256]         # second batch
batch_n = train_images[128*n:128*(n+1)] # nth batch
```
This is why GPU memory matters — the batch size is constrained by VRAM.

---

## 4. Tensor Operations — The Arithmetic of Learning

Every transformation a neural network learns reduces to tensor operations.  
Think of them like the ALU operations in a CPU, but on entire arrays at once.

### Element-wise Operations (Broadcasting)
```python
# relu: max(x, 0) — applied to every element
import numpy as np
def naive_relu(x):
    assert x.ndim == 2
    x = x.copy()
    for i in range(x.shape[0]):
        for j in range(x.shape[1]):
            x[i, j] = max(x[i, j], 0)
    return x

# NumPy does this without the loop — vectorized, runs on C under the hood
z = np.maximum(x, 0)   # same result, vastly faster
```

**Why this matters for teaching:** The loop version and the vectorized version
are *identical mathematically*. NumPy just runs the loop in compiled C (or CUDA on GPU).
This is why Python is fast enough for deep learning — the hot path is never Python.

### Dot Product (Matrix Multiplication)
The core operation of a Dense layer:

```python
# What a Dense layer does internally:
# output = activation(dot(input, W) + b)
# W = weight matrix, b = bias vector

def naive_dense(input, W, b):
    assert input.ndim == 2   # (batch_size, input_features)
    assert W.ndim == 2       # (input_features, output_features)
    output = np.dot(input, W) + b
    return np.maximum(output, 0)  # ReLU activation
```

Shape rule: `(a, b) dot (b, c) → (a, c)`  
The inner dimensions must match. The outer dimensions become the result shape.  
C++ analogy: like multiplying matrices with compatible dimensions.

### Broadcasting — Implicit Shape Alignment
```python
x = np.ones((64, 3, 32, 10))   # rank-4 tensor
y = np.ones((32, 10))           # rank-2 tensor
z = x + y                       # NumPy broadcasts y across first two axes
# z.shape = (64, 3, 32, 10)
```
Broadcasting saves memory — you don't need to explicitly tile the smaller tensor.

---

## 5. The Engine — Gradient-Based Optimization

**This is the most important concept in the chapter.** Everything else is scaffolding.

### The Problem Statement
Given: a neural network with millions of weights W  
Goal: find values of W that minimize the loss on training data  
Naive approach: try every possible W → computationally impossible  

### The Key Insight — Derivatives Tell You Which Way to Move

If loss is a smooth differentiable function of W, you can compute:
```
∂loss/∂W  →  gradient of the loss with respect to W
```
The gradient points *uphill* (direction of steepest increase).  
Move W in the **negative gradient direction** → loss decreases.

```python
# Conceptual gradient descent (one step)
W = W - learning_rate * gradient_of_loss_wrt_W
```

### Backpropagation — Gradients Flow Backwards

The network is a chain of functions:  
```
input → Layer1 → Layer2 → ... → LayerN → loss
```
Backprop applies the **chain rule** from calculus to compute how each weight
contributed to the loss, layer by layer, working backwards.

**C++ analogy:** Think of it like tracing a call stack backwards to find which
function caused a bug — each layer's contribution to the error is computed
from the layers above it.

```python
# Modern frameworks do this automatically via autodifferentiation
# You never write backprop by hand — TensorFlow/PyTorch handles it
with tf.GradientTape() as tape:
    predictions = model(inputs)
    loss = loss_fn(targets, predictions)

gradients = tape.gradient(loss, model.trainable_weights)
optimizer.apply_gradients(zip(gradients, model.trainable_weights))
```

### Training Loop — The Full Cycle

```
for each epoch:
    for each batch:
        1. Forward pass  → compute predictions
        2. Compute loss  → how wrong are we?
        3. Backward pass → compute gradients (backprop)
        4. Update weights → W = W - lr * gradient
```

In Keras, `model.fit()` handles all four steps:
```python
model.fit(train_images, train_labels, epochs=5, batch_size=128)
```

---

## 6. The First Example End-to-End — MNIST

### Full Working Jupyter Notebook Code

```python
# ── Cell 1: Load data ──────────────────────────────────────────────
from keras.datasets import mnist
(train_images, train_labels), (test_images, test_labels) = mnist.load_data()

# ── Cell 2: Inspect ────────────────────────────────────────────────
print(train_images.shape)  # (60000, 28, 28)
print(train_images.dtype)  # uint8

# ── Cell 3: Preprocess ─────────────────────────────────────────────
# Flatten 28×28 → 784-element vector; scale 0-255 → 0.0-1.0
train_images = train_images.reshape((60000, 28 * 28))
train_images = train_images.astype("float32") / 255
test_images = test_images.reshape((10000, 28 * 28))
test_images = test_images.astype("float32") / 255

# ── Cell 4: Build model ────────────────────────────────────────────
import keras
from keras import layers

model = keras.Sequential([
    layers.Dense(512, activation="relu"),   # Hidden layer: 512 neurons
    layers.Dense(10, activation="softmax"), # Output: 10 probabilities (digits 0-9)
])

# ── Cell 5: Compile ────────────────────────────────────────────────
model.compile(
    optimizer="adam",
    loss="sparse_categorical_crossentropy",
    metrics=["accuracy"],
)

# ── Cell 6: Train ──────────────────────────────────────────────────
model.fit(train_images, train_labels, epochs=5, batch_size=128)

# ── Cell 7: Evaluate ───────────────────────────────────────────────
test_loss, test_acc = model.evaluate(test_images, test_labels)
print(f"test_acc: {test_acc:.4f}")   # ~97.8%

# ── Cell 8: Predict ────────────────────────────────────────────────
predictions = model.predict(test_images[:10])
print(predictions[0].argmax())  # Most likely digit class
```

### Overfitting — Why Test Accuracy < Training Accuracy
Training accuracy: ~98.9%  
Test accuracy: ~97.8%  
The gap = **overfitting**: the model memorized some training-specific patterns  
that don't generalize. This is covered deeply in Chapter 5.

---

## 7. Preprocessing — Why We Do It

### Reshape: Flatten 2D Images to 1D Vectors
```python
# Dense layers expect rank-2 input: (batch_size, features)
# Our images are rank-3: (60000, 28, 28)
# Flatten the spatial dims: 28 × 28 = 784
train_images = train_images.reshape((60000, 784))
```
Note: We lose spatial information doing this. Convolutional layers (Ch 8-9) fix this.

### Scale: Normalize to [0.0, 1.0]
```python
train_images = train_images.astype("float32") / 255
```
Why? Neural networks train faster and more stably when inputs are small floats.  
Large raw values (0–255 integers) cause exploding gradients during early training.  
This is analogous to normalizing features in classical ML — same principle.

---

## 8. Layer Anatomy

### Dense Layer
```
output = activation(dot(input, W) + b)
```
- `W` = weight matrix, shape `(input_dim, output_dim)` — learned during training
- `b` = bias vector, shape `(output_dim,)` — learned during training
- `activation` = nonlinear function applied element-wise

### Why ReLU?
`relu(x) = max(0, x)` — simple, fast, prevents vanishing gradients  
Without nonlinear activations, stacking layers is mathematically equivalent to a single linear transformation — depth buys nothing.

### Why Softmax on Output?
Converts raw scores → probability distribution summing to 1.  
`softmax(x_i) = exp(x_i) / sum(exp(x_j))`  
Output index with highest probability = predicted class.

---

## 9. Compilation — Three Choices Before Training

```python
model.compile(
    optimizer="adam",                        # How to update weights
    loss="sparse_categorical_crossentropy",  # How to measure error
    metrics=["accuracy"],                    # What to report
)
```

| Choice | Purpose | Chapter 2 Example |
|--------|---------|-------------------|
| Optimizer | Update rule for weights | Adam (adaptive learning rate) |
| Loss function | Scalar measure of prediction error | Cross-entropy for classification |
| Metrics | Human-readable performance | Accuracy |

Details on each: Chapters 3–5.

---

## 10. Key Vocab Quick Reference

| Term | Meaning |
|------|---------|
| Tensor | Multidimensional array of numbers |
| Rank / ndim | Number of axes |
| Shape | Tuple of dimension sizes per axis |
| Scalar | Rank-0 tensor (single number) |
| Vector | Rank-1 tensor |
| Matrix | Rank-2 tensor |
| Batch | Subset of samples processed together |
| Epoch | One full pass through the training data |
| Loss | Scalar measuring how wrong predictions are |
| Gradient | Derivative of loss w.r.t. weights — direction of steepest increase |
| Backpropagation | Algorithm to compute gradients via chain rule |
| Gradient descent | Iteratively move weights opposite to gradient |
| Overfitting | Model performs better on training data than on new data |
| Dense layer | Fully connected layer: every input connected to every output neuron |
| ReLU | `max(0, x)` — most common hidden layer activation |
| Softmax | Converts output scores to probabilities summing to 1 |

---

## 11. Teaching Notes — Common Student Confusions

1. **"5D vector" vs "rank-5 tensor"** — drill this early, it trips everyone up
2. **Gradient direction** — gradient points *up*, we move *down*. Students often reverse this.
3. **Why backprop works** — chain rule from calculus. If you don't know calculus, the intuition is: "each weight gets blamed proportionally for the final error."
4. **What `fit()` actually does** — it's not magic. It's the 4-step loop (forward, loss, backward, update) run `epochs × batches` times.
5. **Overfitting vs underfitting** — introduce the concept here even though Ch 5 covers it. Students will see the gap in their first run and ask.

---

## 12. Jupyter Setup Notes (Anaconda)

```bash
# In Anaconda Prompt — create a dedicated environment
conda create -n dlwp python=3.11
conda activate dlwp
pip install keras tensorflow matplotlib numpy

# Launch notebook
jupyter notebook
```

Each chapter has a companion notebook on GitHub:  
https://github.com/fchollet/deep-learning-with-python-notebooks

> **Tip for teaching:** Have students run cells one at a time and print shapes  
> at each step. `print(x.shape)` after every transform builds tensor intuition fast.

---

*Notes generated while studying alongside the live textbook.*  
*Source: https://deeplearningwithpython.io/chapters/chapter02_mathematical-building-blocks*
