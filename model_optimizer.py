# model_optimizer.py - GPU ACCELERATED VERSION

import pandas as pd
from sklearn.model_selection import RandomizedSearchCV
from lightgbm import LGBMClassifier # Import the new model
from sklearn.metrics import classification_report
import joblib
import logging
import logger_setup

logger = logger_setup.setup_logger()

def optimize_model_gpu():
    """
    Loads the dataset and uses RandomizedSearchCV with the GPU-powered LGBMClassifier
    to find the best hyperparameters.
    """
    data_filename = "nifty_ml_training_data.csv"
    optimized_model_filename = "trading_model_optimized.joblib"

    try:
        logger.info(f"Loading training data from {data_filename}...")
        df = pd.read_csv(data_filename, index_col='timestamp', parse_dates=True)
        
        logger.info("Preparing data...")
        y = df['target']
        X = df.drop(columns=['target'])

        test_set_size = 0.2
        split_index = int(len(X) * (1 - test_set_size))
        X_train, X_test = X[:split_index], X[split_index:]
        y_train, y_test = y[:split_index], y[split_index:]

        logger.info(f"Data ready with {len(X_train)} training samples.")

        # === 1. Define the Parameter Grid for LightGBM ===
        param_grid = {
            "n_estimators": [100, 200, 300, 500],
            "learning_rate": [0.01, 0.05, 0.1],
            "num_leaves": [31, 50, 70],      # A key parameter for LightGBM
            "max_depth": [-1, 5, 10],       # -1 means no limit
            "subsample": [0.8, 0.9, 1.0],
            "colsample_bytree": [0.8, 0.9, 1.0] # Feature fraction
        }
        logger.info("Parameter grid for LightGBM defined.")

        # === 2. Initialize the GPU-powered Model and the Search ===
        # THE CRITICAL CHANGE IS 'device="gpu"'
        model = LGBMClassifier(device="gpu", random_state=42)
        
        random_search = RandomizedSearchCV(
            estimator=model,
            param_distributions=param_grid,
            n_iter=50,
            cv=3,
            verbose=2,
            random_state=42,
            n_jobs=-1
        )

        # === 3. Run the Optimization ===
        logger.info("--- GPU-Accelerated Hyperparameter Optimization Started ---")
        random_search.fit(X_train, y_train)
        logger.info("--- Optimization Complete ---")

        # === 4. Analyze and Evaluate the Best Model ===
        logger.info(f"\nBest parameters found: {random_search.best_params_}")
        best_model = random_search.best_estimator_
        
        logger.info("Evaluating best model performance on the unseen test set...")
        predictions = best_model.predict(X_test)
        
        report = classification_report(y_test, predictions, target_names=['Down (0)', 'Up (1)'])
        logger.info("\n\n--- OPTIMIZED Classification Report (GPU) ---\n" + report)
        
        # === 5. Save the Optimized Model ===
        logger.info(f"\nSaving OPTIMIZED model to {optimized_model_filename}...")
        joblib.dump(best_model, optimized_model_filename)
        logger.info("Optimized model saved successfully.")

    except Exception as e:
        logger.error(f"An error occurred during model optimization: {e}", exc_info=True)
        logger.critical("If the error is related to 'GPU' or 'CUDA', it means the hardware/driver prerequisites are not met.")

if __name__ == '__main__':
    optimize_model_gpu()