# data_harvester.py - UPGRADED FOR CHUNKED DOWNLOADING

import fyers_client
import logger_setup
import datetime
import pandas as pd
import time

logger = logger_setup.setup_logger()

def harvest_historical_data_chunked():
    """
    Downloads a large historical dataset for ML training purposes by fetching it
    in smaller, sequential chunks to respect API limitations.
    """
    logger.info("--- Data Harvesting Mission (Chunked Mode) Started ---")
    
    fyers = fyers_client.get_fyers_model()
    if not fyers:
        logger.critical("Authentication failed. Halting harvest.")
        return

    # --- Define Parameters ---
    symbol = "NSE:NIFTY50-INDEX"
    timeframe = "5"
    output_filename = "nifty_5min_raw_data_5_years.csv"
    
    # Define the total date range (5 years)
    total_days_to_fetch = 365 * 5
    chunk_size_days = 100 # How many days of data to get in each API call
    
    end_date = datetime.date.today()
    all_chunks = []

    logger.info(f"Preparing to download {total_days_to_fetch} days of data in {chunk_size_days}-day chunks...")

    # Loop backwards in time, in chunks
    for i in range(0, total_days_to_fetch, chunk_size_days):
        range_to = end_date - datetime.timedelta(days=i)
        range_from = range_to - datetime.timedelta(days=chunk_size_days)
        
        logger.info(f"Fetching chunk: {range_from} to {range_to}...")

        # Use our existing, trusted function from fyers_client
        chunk_df = fyers_client.get_historical_data(fyers, symbol, timeframe, range_from, range_to)

        if not chunk_df.empty:
            all_chunks.append(chunk_df)
            logger.info(f"   ...Success! Fetched {len(chunk_df)} candles in this chunk.")
        else:
            logger.warning(f"   ...No data returned for this chunk. It might be a weekend/holiday period.")

        # Be respectful to the API and avoid rate limits
        time.sleep(1) # Wait 1 second between each call

    if not all_chunks:
        logger.error("Failed to download any data. Halting mission.")
        return

    # Combine all the downloaded chunks into one massive DataFrame
    logger.info("All chunks downloaded. Concatenating into a single dataset...")
    master_df = pd.concat(all_chunks)

    # Clean up the final dataset: sort by time and remove any duplicate rows
    master_df = master_df.sort_index().drop_duplicates()

    logger.info(f"Successfully created master dataset with {len(master_df)} total candles.")
    
    # Save the data to a new CSV file
    master_df.to_csv(output_filename)
    
    logger.info(f"Data successfully saved to {output_filename}")
    logger.info("--- Data Harvesting Mission Complete ---")


if __name__ == '__main__':
    harvest_historical_data_chunked()