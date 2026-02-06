import os
import pandas as pd
import numpy as np
import joblib
import tensorflow as tf

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer

# -----------------------
# PATHS
# -----------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_PATH = os.path.join(BASE_DIR, "listings", "data", "up.csv")
MODEL_DIR = os.path.join(BASE_DIR, "model")

MODEL_PATH = os.path.join(MODEL_DIR, "land_dl_model.keras")
PREPROCESSOR_PATH = os.path.join(MODEL_DIR, "land_preprocessor.joblib")

os.makedirs(MODEL_DIR, exist_ok=True)

# -----------------------
# LOAD DATA
# -----------------------
df = pd.read_csv(DATASET_PATH)

# clean numbers
def clean(x):
    x = str(x).lower().replace(",", "").strip()
    if "cr" in x:
        return float(x.replace("cr", "")) * 1e7
    if "l" in x:
        return float(x.replace("l", "")) * 1e5
    return float(x)

df["Area"] = df["Area"].apply(clean)
df["price"] = df["price"].apply(clean)

df = df.dropna()

# -----------------------
# FEATURES
# -----------------------
X = df[["state", "city", "plot_type", "Area"]]
y = df["price"]

# -----------------------
# PREPROCESSOR
# -----------------------
preprocessor = ColumnTransformer([
    ("cat", OneHotEncoder(handle_unknown="ignore"), ["state", "city", "plot_type"]),
    ("num", StandardScaler(), ["Area"])
])

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

X_train = preprocessor.fit_transform(X_train)
X_test = preprocessor.transform(X_test)

joblib.dump(preprocessor, PREPROCESSOR_PATH)

# -----------------------
# ANN MODEL
# -----------------------
model = tf.keras.Sequential([
    tf.keras.layers.Dense(64, activation="relu", input_shape=(X_train.shape[1],)),
    tf.keras.layers.Dense(32, activation="relu"),
    tf.keras.layers.Dense(1)
])

model.compile(optimizer="adam", loss="mse")

model.fit(X_train, y_train, epochs=50, batch_size=32, verbose=1)

model.save(MODEL_PATH)

print("✅ LAND ANN MODEL TRAINED & SAVED")