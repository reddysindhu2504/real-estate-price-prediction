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
        "State": "...",
        "District": "...",
        "Plot_Type": "..."
    }
    """

    try:

        # create dataframe same as training dataset
        df = pd.DataFrame([{
            "State": str(data.get("State")).strip(),
            "District": str(data.get("District")).strip(),
            "Plot_Type": str(data.get("Plot_Type")).strip()
        }])

        # preprocess
        X = preprocessor.transform(df)

        # ANN prediction (price per sqft)
        y_pred = model.predict(X, verbose=0)[0][0]

        if np.isnan(y_pred) or np.isinf(y_pred):
            return None

        return round(float(y_pred), 2)

    except Exception as e:
        print("❌ LAND PREDICTION ERROR:", e)
        return None