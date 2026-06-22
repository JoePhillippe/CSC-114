# Access AI Frameworks — California Housing Price Regression

**Course:** CSC-114  
**Notebook:** [Access_AI_Frameworks.ipynb](https://github.com/JoePhillippe/CSC-114/blob/main/Access_AI_Frameworks.ipynb)  
**Framework:** TensorFlow / Keras  
**Dataset:** `keras.datasets.california_housing`

---

## What the Code Does (Step by Step)

The notebook builds a neural network that predicts **California home prices** from neighborhood data.

| Step | What Happens |
|---|---|
| **1. Load Data** | Downloads the built-in California Housing dataset from Keras — already split into train/test sets |
| **2. Normalize Features (X)** | Scales all 8 input features using mean and standard deviation from training data so they are all on a similar scale |
| **3. Normalize Target (Y)** | Scales house prices the same way — this is critical because raw prices ($14,999–$500,001) are too large for the model to train smoothly |
| **4. Build Model** | Creates a 3-layer neural network using Keras Sequential |
| **5. Train** | Runs 30 epochs, evaluating on a 10% validation split each epoch |
| **6. Evaluate** | Tests on unseen data and converts the error back to real dollars |
| **7. Plot** | Charts loss and MAE over all 30 epochs to visualize learning |
| **8. Predict** | Runs 5 sample predictions and compares them to actual prices |

---

## Questions

### What are the different attributes of your dataset? What is the target value?

The dataset describes **California neighborhoods** from the 1990 census. There are **8 input features (attributes)**:

| Feature | Description |
|---|---|
| `MedInc` | Median household income in the block group |
| `HouseAge` | Median age of houses in the block group |
| `AveRooms` | Average number of rooms per household |
| `AveBedrms` | Average number of bedrooms per household |
| `Population` | Total population of the block group |
| `AveOccup` | Average number of household members |
| `Latitude` | Geographic latitude (north/south location) |
| `Longitude` | Geographic longitude (east/west location) |

**Target value:** `MedHouseVal` — the **median house value** in dollars for that block group.  
Range in this dataset: **$14,999 to $500,001**

---

### Is the model regression or classification?

**Regression.**

- A **classification** model predicts a *category* (like the 0–9 digit labels used previously).
- A **regression** model predicts a *continuous number* — in this case, a dollar amount.

The key indicators in the code are:
- The output layer has **1 neuron with no activation function** (`Dense(1)`) — this outputs any real number
- The loss function is **MSE (Mean Squared Error)** — standard for regression
- The metric is **MAE (Mean Absolute Error)** — measures average dollar error

---

### What kind of optimizer was used to train your model? Why?

**Adam** (`optimizer='adam'`)

Adam (Adaptive Moment Estimation) was chosen because:

- It **automatically adjusts the learning rate** for each parameter during training
- It **converges faster** than basic stochastic gradient descent (SGD)
- It handles **sparse gradients and noisy data** well — common in real-world datasets like housing prices
- It requires **very little tuning** — the defaults work well for most problems
- It is the **standard go-to optimizer** for neural networks and is recommended by Keras for beginners

---

### How many epochs of training were required to get your model to predict the most optimal target value?

The model was trained for **30 epochs**.

Looking at the training log, the validation loss continued improving throughout most of the 30 epochs, with the best validation loss appearing around **epoch 25** (`val_loss: 0.2281`). The training loss at epoch 30 reached **0.1905**.

The loss curve in the plot shows the model was still slowly improving at epoch 30, meaning additional epochs could further reduce error — but with diminishing returns.

---

### What was the most accuracy (lowest loss) that was achieved by your model?

From the actual Colab output:

| Metric | Value |
|---|---|
| **Best validation loss (MSE)** | 0.2281 (epoch 25) |
| **Final training loss (MSE)** | 0.1905 (epoch 30) |
| **Test MAE (normalized)** | 0.3058 |
| **Test MAE in real dollars** | **~$35,289** |

**Interpretation:** On unseen test data, the model's predictions are off by approximately **$35,289 on average**. Given that home prices in the dataset range from ~$15,000 to ~$500,000, this is a reasonable first result for a simple 3-layer network trained for only 30 epochs.

Sample predictions from the actual run:

| Predicted | Actual |
|---|---|
| $217,892 | $397,900 |
| $219,504 | $227,900 |
| $167,536 | $172,100 |
| $221,006 | $186,500 |
| $180,112 | $148,900 |

---

### Are you able to save your model, send it inputs, and get a prediction?

**Yes.** The following code saves the trained model and uses it to make a new prediction:

```python
# Save the model
model.save('california_housing_model.keras')

# Load it back
from tensorflow import keras
import numpy as np

loaded_model = keras.models.load_model('california_housing_model.keras')

# Create a sample input — must be normalized using the same stats from training
# Example: MedInc=8.3, HouseAge=41, AveRooms=6.98, AveBedrms=1.02,
#          Population=322, AveOccup=2.56, Lat=37.88, Long=-122.23
sample = np.array([[8.3252, 41.0, 6.9841, 1.0238, 322.0, 2.5556, 37.88, -122.23]])

# Normalize using the same x_mean and x_std from training
sample_norm = (sample - x_mean) / x_std

# Predict (result is normalized — convert back to dollars)
pred_norm = loaded_model.predict(sample_norm)
pred_dollars = (pred_norm.flatten()[0] * y_std) + y_mean
print(f"Predicted house value: ${pred_dollars:,.0f}")
```

The model weights and architecture are fully saved, so predictions can be made at any time without retraining.

---

## Additional Notes

### Why Normalization Matters
The raw target values were in the range $14,999–$500,001. Without normalizing, the model's gradients during training would be enormous, causing unstable training or failure to converge. By scaling both features and targets to a small range near 0, the model trains smoothly.

### Model Architecture Summary
```
Input: 8 features
  ↓
Dense(64, relu)  — 576 trainable parameters
  ↓
Dense(64, relu)  — 4,160 trainable parameters
  ↓
Dense(1)         — 65 trainable parameters
  ↓
Output: 1 predicted price (normalized)

Total parameters: 4,801
```

### Possible Improvements
- Train for more epochs (50–100) to reduce loss further
- Add a `Dropout` layer to reduce overfitting
- Use `EarlyStopping` callback to automatically stop when validation loss stops improving
- Try more hidden layers or more neurons per layer
