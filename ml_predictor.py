# ml_predictor.py - UPGRADED WITH FEATURE LIST

import joblib
import pandas as pd
import logging

logger = logging.getLogger(__name__)
# In ml_predictor.py
MODEL_FILE = "trading_model.joblib" # Use the original, more balanced model
try:
    model = joblib.load(MODEL_FILE)
    # NEW: Store the feature names the model was trained on
    model_features = model.feature_name_
    logger.info(f"Machine Learning model '{MODEL_FILE}' loaded successfully.")
    logger.info(f"Model trained on {len(model_features)} features.")
except FileNotFoundError:
    logger.critical(f"FATAL: Model file '{MODEL_FILE}' not found.")
    model = None
    model_features = []
except Exception as e:
    logger.critical(f"An error occurred while loading the ML model: {e}", exc_info=True)
    model = None
    model_features = []

def get_prediction(latest_features_df):
    """
    Takes a DataFrame with latest features, ensures column order, and returns prediction.
    """
    if model is None:
        logger.error("Model is not loaded. Cannot make a prediction.")
        return None
    
    try:
        # Ensure the incoming dataframe has the same columns in the same order as the model expects
        aligned_df = latest_features_df[model_features]
        prediction = model.predict(aligned_df)
        return prediction[0]
    except Exception as e:
        logger.error(f"An error occurred during prediction: {e}", exc_info=True)
        return None