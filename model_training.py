# model_training.py

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import classification_report
import joblib
import logging
import logger_setup

logger = logger_setup.setup_logger()

def train_model():
    """
    Loads the engineered dataset, trains a model, evaluates it, and saves it.
    """
    data_filename = "nifty_ml_training_data.csv"
    model_filename = "trading_model.joblib"

    try:
        logger.info(f"Loading training data from {data_filename}...")
        df = pd.read_csv(data_filename, index_col='timestamp', parse_dates=True)

        # === 1. Prepare Data for Training ===
        logger.info("Preparing data: Defining features (X) and target (y)...")
        
        # The 'target' column is what we want to predict
        y = df['target']
        # All other columns are the features the model will learn from
        X = df.drop(columns=['target'])

        # === 2. Split Data into Training and Testing Sets ===
        # It is CRITICAL to not shuffle time-series data.
        # We train on the past and test on the most recent, unseen data.
        test_set_size = 0.2 # Use the latest 20% of data for testing
        split_index = int(len(X) * (1 - test_set_size))
        
        X_train, X_test = X[:split_index], X[split_index:]
        y_train, y_test = y[:split_index], y[split_index:]

        logger.info(f"Data split into {len(X_train)} training samples and {len(X_test)} testing samples.")

        # === 3. Initialize and Train the Model ===
        logger.info("Initializing Gradient Boosting Classifier model...")
        # These are some standard starting parameters
        model = GradientBoostingClassifier(
            n_estimators=100,      # Number of decision trees
            learning_rate=0.1,   # How quickly the model learns
            max_depth=3,         # The complexity of each tree
            random_state=42,     # For reproducible results
            verbose=1            # This will print the training progress
        )

        logger.info("--- Model Training Started (This may take several minutes) ---")
        model.fit(X_train, y_train)
        logger.info("--- Model Training Complete ---")

        # === 4. Evaluate the Model ===
        logger.info("Evaluating model performance on the unseen test set...")
        predictions = model.predict(X_test)
        
        report = classification_report(y_test, predictions, target_names=['Down (0)', 'Up (1)'])
        logger.info("\n\n--- Classification Report ---\n" + report)
        
        # === 5. Analyze Feature Importance ===
        logger.info("\n--- Top 10 Most Important Features ---")
        feature_importances = pd.Series(model.feature_importances_, index=X.columns).sort_values(ascending=False)
        logger.info("\n" + feature_importances.head(10).to_string())

        # === 6. Save the Trained Model ===
        logger.info(f"\nSaving trained model to {model_filename}...")
        joblib.dump(model, model_filename)
        logger.info("Model saved successfully.")

    except FileNotFoundError:
        logger.critical(f"FATAL ERROR: The training data file '{data_filename}' was not found.")
    except Exception as e:
        logger.error(f"An error occurred during model training: {e}", exc_info=True)


if __name__ == '__main__':
    train_model()