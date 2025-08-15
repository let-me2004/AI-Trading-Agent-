# get_universe.py - UPGRADED FOR AUTOMATED DOWNLOAD

import requests
import pandas as pd
import logging
import logger_setup
import io

logger = logger_setup.setup_logger()

def create_stock_universe_automated():
    """
    Automates the download of the NIFTY 200 constituents CSV from the NSE server,
    formats the symbols for the Fyers API, and saves them to a new CSV.
    """
    output_filename = "nifty200_symbols.csv"

    try:
        # The direct URL to the NSE's CSV download
        url = "https://www.niftyindices.com/IndexConstituent/ind_nifty200list.csv"
        
        # We must send browser-like headers to avoid being blocked
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
        }

        logger.info(f"Attempting to download NIFTY 200 list directly from NSE server...")
        response = requests.get(url, headers=headers)
        response.raise_for_status() # This will raise an error if the download fails

        logger.info("Download successful. Processing data...")

        # Use io.StringIO to treat the downloaded text content as a file
        csv_data = io.StringIO(response.text)
        
        # Load the CSV data into a pandas DataFrame
        df = pd.read_csv(csv_data)
        
        if 'Symbol' not in df.columns:
            logger.error("Critical Error: Downloaded CSV does not contain a 'Symbol' column.")
            return

        stock_codes = df['Symbol'].tolist()
        logger.info(f"Successfully processed {len(stock_codes)} stock codes.")

        # Format the symbols for the Fyers API
        fyers_symbols = [f"NSE:{code}-EQ" for code in stock_codes]

        # Create a new DataFrame and save our clean list
        output_df = pd.DataFrame(fyers_symbols, columns=["fyers_symbol"])
        output_df.to_csv(output_filename, index=False)

        logger.info(f"Successfully created {output_filename} with formatted symbols.")
        logger.info(f"Sample symbols: {fyers_symbols[:5]}")

    except requests.exceptions.RequestException as e:
        logger.error(f"FATAL ERROR: Could not download the file from the NSE server. Error: {e}")
        logger.error("This could be a temporary network issue or the URL may have changed.")
    except Exception as e:
        logger.error(f"An error occurred during universe creation: {e}", exc_info=True)

if __name__ == '__main__':
    create_stock_universe_automated()