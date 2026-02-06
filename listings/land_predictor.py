import os
import numpy as np
import pandas as pd
import joblib
import tensorflow as tf
from django.conf import settings

# -------------------------
# PATHS
# -------------------------
MODEL_PATH = os.path.join(settings.BASE_DIR, "model", "land_dl_model.keras")
PREPROCESSOR_PATH = os.path.join(settings.BASE_DIR, "model", "land_preprocessor.joblib")

# -------------------------
# LOAD MODEL & PREPROCESSOR (ONCE)
# -------------------------
model = tf.keras.models.load_model(MODEL_PATH)
preprocessor = joblib.load(PREPROCESSOR_PATH)

print("🔥 Land ANN model loaded successfully")

# -------------------------
# PREDICTION FUNCTION
# -------------------------
def predict_land_price(data):
    """
    data = {
        "state": "...",
        "city": "...",
        "plot_type": "...",
        "Area": "2000"
    }
    """

    try:
        # -------------------------
        # 1️⃣ VALIDATE INPUT
        # -------------------------
        area = data.get("Area")

        if area is None or str(area).strip() == "":
            return None

        area = float(area)
        if area <= 0:
            return None

        # -------------------------
        # 2️⃣ CREATE DATAFRAME (SAME AS TRAINING)
        # -------------------------
        df = pd.DataFrame([{
            "state": str(data.get("state")).strip().lower(),
            "city": str(data.get("city")).strip().lower(),
            "plot_type": str(data.get("plot_type")).strip(),
            "Area": area
        }])

        # -------------------------
        # 3️⃣ PREPROCESS
        # -------------------------
        X = preprocessor.transform(df)

        # -------------------------
        # 4️⃣ ANN PREDICTION
        # -------------------------
        y_pred = model.predict(X, verbose=0)[0][0]

        # -------------------------
        # 5️⃣ SAFETY CHECKS (🚑 FIX FOR ₹ inf)
        # -------------------------
        if np.isnan(y_pred) or np.isinf(y_pred):
            return None

        # unrealistic values guard
        if y_pred <= 0 or y_pred > 1e10:
            return None

        return round(float(y_pred), 2)

    except Exception as e:
        print("❌ LAND PREDICTION ERROR:", e)
        return None