# # listings/predictor_construction_ann.py

# import os
# import joblib
# import pandas as pd
# import numpy as np
# import traceback
# from django.conf import settings

# # ----------------------------------
# # ANN MODEL PATH (Construction)
# # ----------------------------------
# MODEL_PATH = os.path.join(
#     settings.BASE_DIR,
#     "model",
#     "construction_ann_pipeline.joblib"
# )

# try:
#     model = joblib.load(MODEL_PATH)
#     print("🔥 Construction ANN model loaded successfully")
# except Exception as e:
#     print("❌ Failed loading Construction ANN model:", e)
#     model = None


# # ----------------------------------
# # HELPER FUNCTIONS
# # ----------------------------------
# def _to_float(x, default=0.0):
#     try:
#         if x is None or str(x).strip() == "":
#             return float(default)
#         return float(x)
#     except Exception:
#         return float(default)


# def _to_int(x, default=0):
#     try:
#         if x is None or str(x).strip() == "":
#             return int(default)
#         return int(float(x))
#     except Exception:
#         return int(default)


# # ----------------------------------
# # ANN PREDICTION FUNCTION
# # ----------------------------------
# def predict_construction_cost(data):
#     """
#     ANN-based Construction Cost Prediction
#     Returns predicted cost in LAKHS
#     """

#     if model is None:
#         print("❌ Construction ANN model not loaded")
#         return 0.0

#     try:
#         # ----------------------------------
#         # READ INPUT (FROM views.py)
#         # ----------------------------------
#         state = (data.get("state") or "").strip()
#         city = (data.get("city") or "").strip()

#         size_sqft = _to_float(data.get("size_sqft"), 0.0)
#         bhk = _to_int(data.get("bhk"), 0)
#         age = _to_int(data.get("age"), 0)

#         # ----------------------------------
#         # BUILD INPUT DATAFRAME
#         # (MUST MATCH TRAINING COLUMNS)
#         # ----------------------------------
#         input_df = pd.DataFrame([{
#             "State": state,
#             "City": city,
#             "BHK": bhk,
#             "Size_in_SqFt": size_sqft,
#             "Age_of_Property": age
#         }])

#         if settings.DEBUG:
#             print("DEBUG Construction ANN input:")
#             print(input_df)

#         # ----------------------------------
#         # ANN PREDICTION
#         # ----------------------------------
#         y_pred = model.predict(input_df)

#         # If ANN trained on direct Lakhs
#         price_lakhs = float(y_pred[0])

#         if settings.DEBUG:
#             print("DEBUG Construction ANN output (Lakhs):", price_lakhs)

#         return price_lakhs

#     except Exception as e:
#         print("❌ Construction ANN prediction error:", e)
#         traceback.print_exc()
#         return 0.0



# listings/predictor_construction_ann.py

import os
import joblib
import pandas as pd
import numpy as np
import traceback
import tensorflow as tf
from django.conf import settings

# ----------------------------------
# MODEL PATHS (Keras Version)
# ----------------------------------
MODEL_PATH = os.path.join(
    settings.BASE_DIR,
    "model",
    "construction_dl_model.keras"
)

PREPROCESSOR_PATH = os.path.join(
    settings.BASE_DIR,
    "model",
    "construction_preprocessor.joblib"
)

# ----------------------------------
# LOAD MODEL & PREPROCESSOR
# ----------------------------------
try:
    model = tf.keras.models.load_model(MODEL_PATH)
    preprocessor = joblib.load(PREPROCESSOR_PATH)
    print("🔥 Construction DL model loaded successfully")
except Exception as e:
    print("❌ Failed loading Construction DL model:", e)
    model = None
    preprocessor = None


# ----------------------------------
# HELPER FUNCTIONS
# ----------------------------------
def _to_float(x, default=0.0):
    try:
        if x is None or str(x).strip() == "":
            return float(default)
        return float(x)
    except Exception:
        return float(default)


def _to_int(x, default=0):
    try:
        if x is None or str(x).strip() == "":
            return int(default)
        return int(float(x))
    except Exception:
        return int(default)


# ----------------------------------
# PREDICTION FUNCTION
# ----------------------------------
def predict_construction_cost(data):
    """
    Deep Learning ANN Construction Cost Prediction
    Returns predicted cost in LAKHS
    """

    if model is None or preprocessor is None:
        print("❌ Construction DL model not loaded")
        return 0.0

    try:
        # ----------------------------------
        # READ INPUT
        # ----------------------------------
        state = (data.get("state") or "").strip()
        city = (data.get("city") or "").strip()

        size_sqft = _to_float(data.get("size_sqft"), 0.0)
        bhk = _to_int(data.get("bhk"), 0)
        age = _to_int(data.get("age"), 0)

        # ----------------------------------
        # BUILD INPUT DATAFRAME
        # ----------------------------------
        input_df = pd.DataFrame([{
            "State": state,
            "City": city,
            "BHK": bhk,
            "Size_in_SqFt": size_sqft,
            "Age_of_Property": age
        }])

        if settings.DEBUG:
            print("DEBUG Construction DL input:")
            print(input_df)

        # ----------------------------------
        # PREPROCESS
        # ----------------------------------
        X = preprocessor.transform(input_df)

        # ----------------------------------
        # PREDICT
        # ----------------------------------
        y_pred = model.predict(X)

        price_lakhs = float(y_pred[0][0])

# convert lakhs → rupees
        price_rupees = price_lakhs

        return round(price_rupees, 2)


    except Exception as e:
        print("❌ Construction DL prediction error:", e)
        traceback.print_exc()
        return 0.0
