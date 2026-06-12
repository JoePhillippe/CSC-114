# Chapter 3 — Introduction to TensorFlow, PyTorch, JAX, and Keras
> **Deep Learning with Python, 3rd Ed.** — Chollet  
> Course: CSC 114 · Fayetteville Technical Community College  
> Textbook: https://deeplearningwithpython.io/chapters/chapter03_introduction-to-ml-frameworks  
> Colab: https://colab.research.google.com/github/fchollet/deep-learning-with-python-notebooks/blob/master/chapter03_introduction-to-ml-frameworks.ipynb

---

## Teaching Goal
Understand how the math from Chapter 2 maps to real framework code.  
By the end of this chapter you can implement gradient descent from scratch  
in TensorFlow — without using `model.fit()` as a black box.

---

## 1. The Framework Landscape — Why So Many?

Chapter 2 showed you the *concepts* — tensors, weights, gradients, backprop.  
Chapter 3 shows you the *tools* those concepts live in.

Every major deep learning framework must solve three problems:

| Problem | What it means |
|---------|--------------|
| Automatic differentiation | Compute gradients without writing them by hand |
| GPU/hardware execution | Run tensor math on fast silicon, not just CPU |
| Distributed computation | Spread work across multiple GPUs or machines |

Without all three, modern deep learning is not practical.

### Framework Timeline (Quick Reference)

```
2009 — Theano      First autodiff + GPU framework. Now dead, but ancestor of all.
2015 — Keras       High-level API on top of Theano. Chollet's project.
2015 — TensorFlow  Google. Production scale. Keras added TF support immediately.
2016 — PyTorch     Meta. Research-friendly. Grew to dominate academia.
2018 — JAX         Google. Minimalist. Fast. Researcher favorite.
```

**Key insight for teaching:** Students often ask "which one should I learn?"  
Answer: Keras — because it runs on top of all three backends (TF, PyTorch, JAX).  
Learning Keras means your code is framework-portable.

---

## 2. How the Frameworks Relate — The Stack

Think of it as two layers:

```
┌─────────────────────────────────────┐
│           K E R A S                 │  ← High level: layers, models, training
│  (layers, models, fit, compile...)  │
└──────────┬──────────────────────────┘
           │ runs on one of:
    ┌──────┴──────┬──────────┐
    │ TensorFlow  │ PyTorch  │  JAX
    │  (default)  │          │
    └─────────────┴──────────┘
         Low level: tensors, gradients, GPU ops
```

**The house analogy from the book:**  
- TensorFlow / PyTorch / JAX = raw building materials (bricks, steel, wiring)  
- Keras = prefabricated building kit (walls, doors, windows already assembled)

You can build a house from raw materials — but the kit is faster for most jobs.

**C++ parallel:** TensorFlow/PyTorch/JAX are like the C++ standard library.  
Keras is like a framework built on top of it (like Qt on top of C++).  
You can drop down to raw C++ when needed — same with raw TF/PyTorch ops in Keras.

---

## 3. TensorFlow Core Concepts

### 3.1 Constant Tensors — Immutable by Default

```python
import tensorflow as tf

# Equivalent to np.ones / np.zeros
tf.ones(shape=(2, 1))     # [[1.], [1.]]
tf.zeros(shape=(2, 1))    # [[0.], [0.]]
tf.constant([1, 2, 3], dtype="float32")  # from Python list

# Random tensors — weights start as random in Chapter 2's network
x = tf.random.normal(shape=(3, 1), mean=0., stddev=1.)
x = tf.random.uniform(shape=(3, 1), minval=0., maxval=1.)
```

**Critical difference from NumPy:** TF tensors are **immutable** — you cannot  
do `x[0, 0] = 5.0`. This will raise an error. This is by design for GPU performance.

```python
# NumPy — works fine
x = np.ones((2, 2))
x[0, 0] = 0.0   # ✓

# TensorFlow — raises error
x = tf.ones((2, 2))
x[0, 0] = 0.0   # ✗ EagerTensor does not support item assignment
```

**Why immutable?** On a GPU, tensors live in device memory. Arbitrary in-place  
mutation would require constant CPU↔GPU sync — kills performance.  
Same reason C++ `const` exists for shared data structures.

---

### 3.2 Variables — Mutable State for Weights

Since weights *must* change during training, TF provides `tf.Variable`:

```python
# Create a variable (this is what model weights are internally)
v = tf.Variable(initial_value=tf.random.normal(shape=(3, 1)))

# Assign new value
v.assign(tf.ones((3, 1)))

# Assign to a subset
v[0, 0].assign(3.)

# In-place add/subtract — used in weight update step
v.assign_add(tf.ones((3, 1)))   # equivalent to v += 1
v.assign_sub(tf.ones((3, 1)))   # equivalent to v -= 1
```

**Connection to Chapter 2:** Those 401,408 weights in the MNIST network  
(512×784 + 512 biases + 10×512 + 10 biases) are all `tf.Variable` objects  
under the hood. `model.fit()` calls `assign_sub` on each one every training step.

---

### 3.3 Tensor Operations — Same as Chapter 2, Now in TF

```python
a = tf.ones((2, 2))

tf.square(a)              # element-wise square — same as np.square
tf.sqrt(a)                # element-wise sqrt
a + tf.square(a)          # element-wise add — Python + operator works
tf.matmul(a, a)           # matrix multiply — the Dense layer core operation
tf.concat((a, a), axis=0) # stack tensors — same as np.concatenate
```

The Dense layer from Chapter 2 in raw TensorFlow:
```python
def dense(inputs, W, b):
    return tf.nn.relu(tf.matmul(inputs, W) + b)
    #                  ↑ matrix multiply    ↑ bias add  → relu activation
```
This is **exactly** what `layers.Dense(512, activation="relu")` does internally.  
Keras just wraps it and manages W and b for you.

---

### 3.4 GradientTape — How Backprop Actually Works in Code

This is the most important concept in Chapter 3.  
In Chapter 2 you learned *what* backpropagation does conceptually.  
Here is how you actually *call* it:

```python
# Simple example: gradient of x² with respect to x
input_var = tf.Variable(initial_value=3.0)

with tf.GradientTape() as tape:
    result = tf.square(input_var)   # result = 3² = 9

gradient = tape.gradient(result, input_var)
# gradient = d(x²)/dx at x=3 = 2x = 6
print(gradient)  # 6.0
```

**The tape metaphor:** GradientTape literally records every operation  
performed inside its `with` block — like a video tape. When you call  
`tape.gradient()`, it plays the tape backwards applying the chain rule  
at each recorded operation. This is automatic differentiation.

**C++ analogy:** Think of the tape as an operation log / audit trail.  
Every math op writes an entry. Backprop reads the log in reverse and  
accumulates the chain rule at each step.

#### Watching Constants

By default the tape only watches `tf.Variable` objects (the trainable weights).  
To compute gradients with respect to a plain tensor, you must opt in:

```python
input_const = tf.constant(3.0)

with tf.GradientTape() as tape:
    tape.watch(input_const)    # ← must explicitly watch constants
    result = tf.square(input_const)

gradient = tape.gradient(result, input_const)  # 6.0
```

**Why?** Storing gradient information for every tensor would consume  
enormous memory. The tape only tracks what you tell it to.  
Same logic as selectively instrumenting code for profiling in C++.

#### Second-Order Gradients (Gradient of Gradient)

```python
# Gradient of gradient — acceleration example from the book
time = tf.Variable(0.0)

with tf.GradientTape() as outer_tape:
    with tf.GradientTape() as inner_tape:
        position = 4.9 * time**2          # position = 4.9t²

    speed = inner_tape.gradient(position, time)  # d/dt = 9.8t → 0.0 at t=0

acceleration = outer_tape.gradient(speed, time)  # d²/dt² = 9.8
print(acceleration)  # 9.8 m/s²  ← gravity, as expected
```

Not needed for basic training but important for advanced techniques  
(meta-learning, physics-informed networks). Good to know it exists.

---

### 3.5 Compilation — Making TF Code Fast

By default TF runs eagerly — one Python operation at a time.  
Good for debugging. Slow for training.

```python
# Eager (default) — slow but debuggable
def dense(inputs, W, b):
    return tf.nn.relu(tf.matmul(inputs, W) + b)

# Compiled — fast, harder to debug
@tf.function
def dense(inputs, W, b):
    return tf.nn.relu(tf.matmul(inputs, W) + b)

# XLA compiled — fastest, first call takes longer
@tf.function(jit_compile=True)
def dense(inputs, W, b):
    return tf.nn.relu(tf.matmul(inputs, W) + b)
```

**Rule of thumb:** Debug eager first. Add `@tf.function` once code is correct.

**C++ analogy:** Eager mode = interpreted Python. `@tf.function` = compiling  
to native code. XLA = link-time optimization (LTO). Same trade-off:  
compilation overhead upfront, faster execution afterwards.

---

## 4. End-to-End: Linear Classifier in Pure TensorFlow

This is the key exercise in Chapter 3 — implementing gradient descent  
**without** `model.fit()`, so you see every moving part.

```python
import numpy as np
import tensorflow as tf

# ── Generate synthetic 2-class data ───────────────────────────────
num_samples_per_class = 1000
negative_samples = np.random.multivariate_normal(
    mean=[0, 3], cov=[[1, 0.5], [0.5, 1]], size=num_samples_per_class)
positive_samples = np.random.multivariate_normal(
    mean=[3, 0], cov=[[1, 0.5], [0.5, 1]], size=num_samples_per_class)

inputs  = np.vstack((negative_samples, positive_samples)).astype("float32")
targets = np.vstack((np.zeros((1000, 1), dtype="float32"),
                     np.ones( (1000, 1), dtype="float32")))

# ── Create trainable weights ───────────────────────────────────────
W = tf.Variable(tf.random.uniform(shape=(2, 1)))  # 2 input features → 1 output
b = tf.Variable(tf.zeros(shape=(1,)))

# ── Forward pass ──────────────────────────────────────────────────
def model(inputs, W, b):
    return tf.matmul(inputs, W) + b   # linear: no activation

# ── Loss function ─────────────────────────────────────────────────
def mean_squared_error(targets, predictions):
    per_sample_losses = tf.square(targets - predictions)
    return tf.reduce_mean(per_sample_losses)  # scalar loss value

# ── Training step — the four steps from Chapter 2 ─────────────────
learning_rate = 0.1

@tf.function(jit_compile=True)
def training_step(inputs, targets, W, b):
    with tf.GradientTape() as tape:
        predictions = model(inputs, W, b)          # Step 1: forward pass
        loss = mean_squared_error(targets, predictions)  # Step 2: compute loss
    grad_W, grad_b = tape.gradient(loss, [W, b])   # Step 3: backprop
    W.assign_sub(grad_W * learning_rate)            # Step 4: update weights
    b.assign_sub(grad_b * learning_rate)
    return loss

# ── Training loop ─────────────────────────────────────────────────
for step in range(40):
    loss = training_step(inputs, targets, W, b)
    if step % 5 == 0:
        print(f"Step {step:3d} — loss: {loss:.4f}")
```

**This is `model.fit()` unrolled.** Every call to `training_step()` is one  
iteration of the loop that Keras runs automatically. Now you can see exactly  
what happens inside the black box.

---

## 5. The Four-Step Training Loop — Connection to Chapter 2

Chapter 2 described this conceptually. Chapter 3 shows it in code.  
They are identical:

| Chapter 2 concept | Chapter 3 code |
|---|---|
| Forward pass | `predictions = model(inputs, W, b)` |
| Compute loss | `loss = mean_squared_error(targets, predictions)` |
| Backpropagation | `tape.gradient(loss, [W, b])` |
| Weight update | `W.assign_sub(grad_W * learning_rate)` |

When you call `model.fit()` in Keras, it runs this exact loop — just  
abstracted behind a clean API. Understanding this loop is what separates  
someone who *uses* deep learning from someone who *understands* it.

---

## 6. Keras — The High-Level Layer on Top

Keras provides the vocabulary that sits above raw TF/PyTorch/JAX operations:

| Keras concept | What it manages for you |
|---|---|
| `layers.Dense(512)` | Creates W and b as `tf.Variable`, defines the forward pass |
| `model.compile()` | Stores your choice of optimizer, loss, and metrics |
| `model.fit()` | Runs the 4-step training loop for every batch and epoch |
| `model.evaluate()` | Runs forward pass only, computes metrics on test data |
| `model.predict()` | Runs forward pass only, returns raw predictions |

**Why use Keras instead of raw TF?**  
The linear classifier above took ~40 lines for one layer, no metrics,  
no batching, no validation split. The Keras equivalent is 8 lines.  
For research prototyping you might use raw TF — for teaching and  
production work, Keras is almost always the right choice.

---

## 7. Key Vocab Quick Reference

| Term | Meaning |
|------|---------|
| Eager execution | TF default: runs ops immediately, Python-style |
| `tf.Variable` | Mutable tensor — used for trainable weights |
| `tf.constant` | Immutable tensor — used for data |
| `GradientTape` | Records ops for backprop; `.gradient()` plays tape in reverse |
| `tape.watch()` | Manually mark a constant tensor to track gradients for |
| `@tf.function` | Compile a Python function to TF graph — faster execution |
| XLA | Accelerated Linear Algebra — deeper compiler optimization |
| Backend | The low-level engine Keras runs on (TF, PyTorch, or JAX) |
| Batch training | One gradient update using the full dataset |
| Mini-batch training | One gradient update using a small subset (e.g. 128 samples) |

---

## 8. Teaching Notes — Common Student Confusions

1. **"Why can't I just assign to a TF tensor?"** — Immutability is a GPU  
   constraint, not an arbitrary design choice. In-place mutation breaks  
   the computation graph the tape needs to record.

2. **"What's the difference between Keras and TensorFlow?"** — Use the  
   house analogy. Keras is the kit. TF is the raw material. You can build  
   with either, but the kit is faster for standard structures.

3. **"Why do we need GradientTape if Keras does backprop automatically?"**  
   — Keras uses GradientTape internally. Understanding it means you can  
   write custom training loops, custom losses, and custom layers later.

4. **"What does `@tf.function` actually do?"** — It converts your Python  
   function into a computation graph (like a compiled program) that TF  
   can optimize and run faster than interpreted Python.

5. **"Batch vs mini-batch"** — Batch = whole dataset per update (slow per  
   step, fewer steps needed). Mini-batch = small chunk per update (fast  
   per step, more steps needed, better generalization). `model.fit()` uses  
   mini-batch by default via the `batch_size` parameter.

---

## 9. Colab Notes

```
Chapter 3 notebook:
https://colab.research.google.com/github/fchollet/deep-learning-with-python-notebooks/blob/master/chapter03_introduction-to-ml-frameworks.ipynb
```

Suggested Colab experiments for Chapter 3:

```python
# Experiment 1 — verify tensor immutability
x = tf.ones((2, 2))
try:
    x[0, 0] = 5.0
except Exception as e:
    print(type(e).__name__, e)   # See the actual error

# Experiment 2 — watch gradient tape in action
w = tf.Variable(2.0)
with tf.GradientTape() as tape:
    loss = w ** 3              # d/dw of w³ = 3w² = 12 at w=2
grad = tape.gradient(loss, w)
print(grad.numpy())            # Should print 12.0

# Experiment 3 — print shapes at every step of the linear classifier
print(f"inputs:  {inputs.shape}")   # (2000, 2)
print(f"targets: {targets.shape}")  # (2000, 1)
print(f"W:       {W.shape}")        # (2, 1)
print(f"b:       {b.shape}")        # (1,)
predictions = model(inputs, W, b)
print(f"output:  {predictions.shape}")  # (2000, 1)
```

---

## 10. Chapter 2 → Chapter 3 Connections

| Chapter 2 concept | Chapter 3 implementation |
|---|---|
| "Weights are updated by gradient descent" | `W.assign_sub(grad * lr)` |
| "Backpropagation computes gradients" | `tape.gradient(loss, [W, b])` |
| "The training loop runs forward + backward" | `training_step()` function |
| "Dense layer = dot product + bias + activation" | `tf.matmul(inputs, W) + b` then `relu` |
| "Loss measures how wrong we are" | `mean_squared_error()` returns a scalar |

---

*Notes generated while studying alongside the live textbook.*  
*Source: https://deeplearningwithpython.io/chapters/chapter03_introduction-to-ml-frameworks*
