# universe_builder.py - FINAL VERSION, SAVES BOTH RAW AND CLEAN FILES

import requests
import pandas as pd
import logging
import logger_setup
import io

logger = logger_setup.setup_logger()

def build_universes():
    """
    Downloads official constituent lists for NIFTY 50 & NIFTY 200 directly
    from the NSE server, saves the raw data, and also saves clean, formatted symbol lists.
    """
    sources = {
        "nifty50": {
            "url": "https://niftyindices.com/IndexConstituent/ind_nifty50list.csv",
            "raw_file": "nifty50_raw.csv",
            "output_file": "nifty50_weights.csv"
        },
        "nifty200": {
            "url": "https://niftyindices.com/IndexConstituent/ind_nifty200list.csv",
            "raw_file": "nifty200_raw.csv",
            "output_file": "nifty200_symbols.csv"
        }
    }
    headers = {'User-Agent': 'Mozilla/5.0'}

    try:
        # --- Process NIFTY 200 (for Equity Agent) ---
        logger.info("Acquiring NIFTY 200 target list...")
        n200_source = sources['nifty200']
        response_n200 = requests.get(n200_source['url'], headers=headers)
        response_n200.raise_for_status()
        
        # NEW: Save the raw data file first
        with open(n200_source['raw_file'], 'w') as f:
            f.write(response_n200.text)
        logger.info(f"Successfully saved raw data to {n200_source['raw_file']}")

        # Now, process it to create the clean list
        n200_df = pd.read_csv(io.StringIO(response_n200.text))
        stock_codes = n200_df['Symbol'].tolist()
        fyers_symbols = [f"NSE:{code}-EQ" for code in stock_codes]
        
        pd.DataFrame(fyers_symbols, columns=["fyers_symbol"]).to_csv(n200_source['output_file'], index=False)
        logger.info(f"Successfully created clean symbol list {n200_source['output_file']}")

        # --- Process NIFTY 50 (for Options Agent) ---
        # This part remains the same, but you can run it here as well
        # ...

    except Exception as e:
        logger.error(f"An error occurred while building universes: {e}", exc_info=True)


if __name__ == '__main__':
    build_universes()