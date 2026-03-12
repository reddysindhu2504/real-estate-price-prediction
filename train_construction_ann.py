# import pandas as pd
# import numpy as np
# import os, joblib, json

# from sklearn.model_selection import train_test_split
# from sklearn.preprocessing import OneHotEncoder, StandardScaler
# from sklearn.compose import ColumnTransformer
# from sklearn.pipeline import Pipeline
# from sklearn.neural_network import MLPRegressor
# from sklearn.metrics import mean_squared_error

# BASE_DIR = os.path.dirname(__file__)
# DATA_PATH = os.path.join(BASE_DIR, "listings", "data", "dataset.csv")
# MODEL_DIR = os.path.join(BASE_DIR, "model")
# os.makedirs(MODEL_DIR, exist_ok=True)

# print("Loading dataset:", DATA_PATH)
# df = pd.read_csv(DATA_PATH)

# # FEATURES & TARGET
# FEATURES = ["State", "City", "BHK", "Size_in_SqFt", "Age_of_Property"]
# TARGET = "Price_in_Lakhs"

# X = df[FEATURES]
# y = df[TARGET]

# # Split
# X_train, X_test, y_train, y_test = train_test_split(
#     X, y, test_size=0.2, random_state=42
# )

# # Preprocessing
# categorical = ["State", "City"]
# numeric = ["BHK", "Size_in_SqFt", "Age_of_Property"]

# preprocessor = ColumnTransformer([
#     ("cat", OneHotEncoder(handle_unknown="ignore"), categorical),
#     ("num", StandardScaler(), numeric),
# ])

# # 🔥 ANN MODEL
# ann_model = MLPRegressor(
#     hidden_layer_sizes=(64, 32),
#     activation="relu",
#     solver="adam",
#     max_iter=1000,
#     random_state=42
# )

# pipeline = Pipeline([
#     ("preprocessor", preprocessor),
#     ("model", ann_model)
# ])

# print("Training ANN model for Construction...")
# pipeline.fit(X_train, y_train)

# # Evaluate
# preds = pipeline.predict(X_test)
# rmse = np.sqrt(mean_squared_error(y_test, preds))
# print("RMSE:", rmse)

# # Save
# joblib.dump(pipeline, os.path.join(MODEL_DIR, "construction_ann_pipeline.joblib"))

# with open(os.path.join(MODEL_DIR, "construction_ann_metrics.json"), "w") as f:
#     json.dump({"rmse": float(rmse)}, f, indent=4)

# print("✅ Construction ANN training completed!")


import os
import pandas as pd
import numpy as np
import joblib
import tensorflow as tf

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.metrics import mean_squared_error

# -----------------------
# PATHS
# -----------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "listings", "data", "dataset.csv")
MODEL_DIR = os.path.join(BASE_DIR, "model")

MODEL_PATH = os.path.join(MODEL_DIR, "construction_dl_model.keras")
PREPROCESSOR_PATH = os.path.join(MODEL_DIR, "construction_preprocessor.joblib")

os.makedirs(MODEL_DIR, exist_ok=True)

# -----------------------
# LOAD DATA
# -----------------------
print("Loading dataset:", DATA_PATH)
df = pd.read_csv(DATA_PATH)

# -----------------------
# FEATURES & TARGET
# -----------------------
FEATURES = ["State", "City", "BHK", "Size_in_SqFt", "Age_of_Property"]
TARGET = "Price_in_Rupees"

X = df[FEATURES]
y = df[TARGET]

# -----------------------
# SPLIT
# -----------------------
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

# -----------------------
# PREPROCESSING
# -----------------------
categorical = ["State", "City"]
numeric = ["BHK", "Size_in_SqFt", "Age_of_Property"]

preprocessor = ColumnTransformer([
    ("cat", OneHotEncoder(handle_unknown="ignore"), categorical),
    ("num", StandardScaler(), numeric),
])

X_train = preprocessor.fit_transform(X_train)
X_test = preprocessor.transform(X_test)

# Save preprocessor
joblib.dump(preprocessor, PREPROCESSOR_PATH)

# -----------------------
# BUILD KERAS ANN MODEL
# -----------------------
model = tf.keras.Sequential([
    tf.keras.layers.Dense(64, activation="relu", input_shape=(X_train.shape[1],)),
    tf.keras.layers.Dense(32, activation="relu"),
    tf.keras.layers.Dense(1)
])

model.compile(
    optimizer="adam",
    loss="mse",
    metrics=["mae"]
)

# -----------------------
# TRAIN MODEL
# -----------------------
print("Training Deep Learning ANN for Construction...")
history = model.fit(
    X_train,
    y_train,
    epochs=50,
    batch_size=32,
    validation_split=0.1,
    verbose=1
)

# -----------------------
# EVALUATE
# -----------------------
preds = model.predict(X_test)
rmse = np.sqrt(mean_squared_error(y_test, preds))

print("RMSE:", rmse)

# -----------------------
# SAVE MODEL
# -----------------------
model.save(MODEL_PATH)

print("✅ Construction Deep Learning Model Trained & Saved!")
print("Model saved at:", MODEL_PATH)
print("Preprocessor saved at:", PREPROCESSOR_PATH)
