# ml_predictor.py

import joblib
import pandas as pd
import logging

logger = logging.getLogger(__name__)
MODEL_FILE = "trading_model.joblib"

try:
    # Load the trained model when the module is first imported
    model = joblib.load(MODEL_FILE)
    logger.info(f"Machine Learning model '{MODEL_FILE}' loaded successfully.")
except FileNotFoundError:
    logger.critical(f"FATAL: The model file '{MODEL_FILE}' was not found. Please run model_training.py first.")
    model = None
except Exception as e:
    logger.critical(f"An error occurred while loading the model: {e}", exc_info=True)
    model = None

def get_prediction(latest_features_df):
    """
    Takes a DataFrame with the latest features and returns the model's prediction.
    :param latest_features_df: A single-row pandas DataFrame with the same columns as the training data.
    :return: 1 for 'Up', 0 for 'Down', or None if an error occurs.
    """
    if model is None:
        logger.error("Model is not loaded. Cannot make a prediction.")
        return None
    
    try:
        # The model expects a DataFrame, so we're already passing the correct format
        prediction = model.predict(latest_features_df)
        # predict() returns an array, so we get the first and only element
        return prediction[0]
    except Exception as e:
        logger.error(f"An error occurred during prediction: {e}", exc_info=True)
        return None