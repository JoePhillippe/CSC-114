!pip install keras keras-hub --upgrade -q

import numpy as np
import tensorflow as tf
from tensorflow import keras
import matplotlib.pyplot as plt

# ── 1. LOAD DATA ──────────────────────────────────────────────
(x_train, y_train), (x_test, y_test) = keras.datasets.california_housing.load_data()

print("Training samples:", x_train.shape)
print("Test samples:    ", x_test.shape)
print("Raw target range: ${:,.0f}  to  ${:,.0f}".format(y_train.min(), y_train.max()))

# ── 2. NORMALIZE FEATURES (x) ─────────────────────────────────
# Compute mean and std from TRAINING data only
x_mean = x_train.mean(axis=0)
x_std  = x_train.std(axis=0)

x_train_norm = (x_train - x_mean) / x_std
x_test_norm  = (x_test  - x_mean) / x_std   # use SAME train stats

# ── 3. NORMALIZE TARGET (y) ───────────────────────────────────
# Scale house prices to 0-1 range so model trains smoothly
y_mean = y_train.mean()
y_std  = y_train.std()

y_train_norm = (y_train - y_mean) / y_std
y_test_norm  = (y_test  - y_mean) / y_std

print("\nNormalized target range: {:.2f}  to  {:.2f}".format(
      y_train_norm.min(), y_train_norm.max()))

# ── 4. BUILD THE MODEL ────────────────────────────────────────
model = keras.Sequential([
    keras.layers.Dense(64, activation='relu', input_shape=(8,)),
    keras.layers.Dense(64, activation='relu'),
    keras.layers.Dense(1)          # single number output = regression
])

model.compile(
    optimizer='adam',
    loss='mse',                    # Mean Squared Error for regression
    metrics=['mae']                # Mean Absolute Error - easier to read
)

model.summary()

# ── 5. TRAIN ──────────────────────────────────────────────────
history = model.fit(
    x_train_norm, y_train_norm,
    epochs=30,
    batch_size=32,
    validation_split=0.1,          # hold out 10% of train for validation
    verbose=1
)

# ── 6. EVALUATE ───────────────────────────────────────────────
loss, mae = model.evaluate(x_test_norm, y_test_norm, verbose=0)

# Convert MAE back to real dollars
mae_dollars = mae * y_std
print("\n--- Test Results ---")
print("MAE (normalized): {:.4f}".format(mae))
print("MAE in dollars:  ${:,.0f}".format(mae_dollars))
print("That means predictions are off by about ${:,.0f} on average".format(mae_dollars))

# ── 7. PLOT TRAINING HISTORY ──────────────────────────────────
plt.figure(figsize=(12, 4))

plt.subplot(1, 2, 1)
plt.plot(history.history['loss'],     label='Train Loss')
plt.plot(history.history['val_loss'], label='Val Loss')
plt.title('Loss (MSE) over Epochs')
plt.xlabel('Epoch')
plt.ylabel('Loss')
plt.legend()

plt.subplot(1, 2, 2)
plt.plot(history.history['mae'],     label='Train MAE')
plt.plot(history.history['val_mae'], label='Val MAE')
plt.title('MAE over Epochs')
plt.xlabel('Epoch')
plt.ylabel('MAE')
plt.legend()

plt.tight_layout()
plt.show()

# ── 8. SAMPLE PREDICTIONS ─────────────────────────────────────
predictions_norm = model.predict(x_test_norm[:5])

# Convert back to dollars
predictions_dollars = (predictions_norm.flatten() * y_std) + y_mean
actual_dollars      = y_test[:5]

print("\n--- Sample Predictions vs Actual ---")
for i in range(5):
    print("Predicted: ${:>10,.0f}   Actual: ${:>10,.0f}".format(
          predictions_dollars[i], actual_dollars[i]))
