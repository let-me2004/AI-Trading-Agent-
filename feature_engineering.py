# feature_engineering.py

import pandas as pd
import pandas_ta as ta
import logging
import logger_setup

logger = logger_setup.setup_logger()

def create_features_and_labels():
    """
    Loads raw data, engineers features, creates labels, and saves the final dataset.
    """
    input_filename = "nifty_5min_raw_data_5_years.csv"
    output_filename = "nifty_ml_training_data.csv"
    
    try:
        logger.info(f"Loading raw data from {input_filename}...")
        df = pd.read_csv(input_filename, index_col='timestamp', parse_dates=True)
        
        if df.empty:
            logger.error("Raw data file is empty. Halting.")
            return

        logger.info(f"Loaded {len(df)} rows. Starting feature engineering...")

        # === 1. FEATURE ENGINEERING (Creating the 'clues') ===
        # We will use pandas-ta to create a variety of technical indicators.
        
        # Momentum Indicators
        df.ta.rsi(length=14, append=True)
        df.ta.macd(fast=12, slow=26, signal=9, append=True)
        
        # Trend Indicators
        df.ta.ema(length=10, append=True)
        df.ta.ema(length=21, append=True)
        df.ta.ema(length=50, append=True)
        df.ta.ema(length=200, append=True)
        
        # Volatility Indicators
        df.ta.bbands(length=20, append=True) # Bollinger Bands
        df.ta.atr(length=14, append=True)   # Average True Range
        
        # Add some custom price-based features
        df['return_1h'] = df['close'].pct_change(periods=12) # 12 * 5min = 1 hour
        df['return_1d'] = df['close'].pct_change(periods=75) # 75 * 5min = 1 trading day

        logger.info("...Feature engineering complete.")

        # === 2. LABEL CREATION (Defining the 'answer') ===
        # We want to predict if the price will be higher or lower in 30 minutes (6 candles).
        logger.info("Creating target labels...")
        
        future_periods = 6 # 6 * 5 minutes = 30 minutes
        
        # This creates a new column with the closing price 6 periods in the future.
        df['future_close'] = df['close'].shift(-future_periods)
        
        # Create the target label: 1 if future price is higher, 0 if it's lower.
        df['target'] = (df['future_close'] > df['close']).astype(int)
        
        logger.info("...Label creation complete.")

        # === 3. FINAL CLEANUP ===
        logger.info("Cleaning up the final dataset...")
        
        # Drop the helper column and any rows with missing data (from indicator calculations)
        df = df.drop(columns=['future_close'])
        df = df.dropna()
        
        logger.info(f"Final dataset contains {len(df)} rows and {len(df.columns)} columns.")

        # Save the final, clean dataset
        df.to_csv(output_filename)
        
        logger.info(f"Successfully saved training data to {output_filename}")

    except FileNotFoundError:
        logger.critical(f"FATAL ERROR: The input file '{input_filename}' was not found.")
    except Exception as e:
        logger.error(f"An error occurred during feature engineering: {e}", exc_info=True)

if __name__ == '__main__':
    create_features_and_labels()