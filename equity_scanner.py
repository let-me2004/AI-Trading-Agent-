# equity_scanner.py

import pandas as pd
import logging
import fyers_client # We need this to get an authenticated fyers model for testing

logger = logging.getLogger(__name__)

# --- Scanner Configuration ---
PRICE_SURGE_PERCENT = 1.5
MINIMUM_VOLUME = 500000

def scan_for_surges(fyers_instance):
    """
    Scans the NIFTY 200 universe for stocks meeting surge criteria.
    :param fyers_instance: An authenticated FyersModel object.
    :return: A list of symbols that are surging.
    """
    try:
        # 1. Load our universe of stocks
        universe_df = pd.read_csv("nifty200_symbols.csv")
        symbol_list = universe_df["fyers_symbol"].tolist()
        logger.info(f"Loaded {len(symbol_list)} symbols for scanning.")

        # 2. Fetch live quote data for the entire universe in one call
        logger.info("Fetching bulk quote data for all symbols...")
        quote_data = fyers_instance.quotes({"symbols": ",".join(symbol_list)})

        if quote_data.get('s') != 'ok' or not quote_data.get('d'):
            logger.error(f"Could not fetch bulk quote data. Response: {quote_data}")
            return []

        # 3. Filter the results to find surging stocks
        surging_stocks = []
        all_stock_data = quote_data['d']
        
        for stock in all_stock_data:
            details = stock.get('v', {})
            symbol = stock.get('n', 'UNKNOWN')
            
            # Ensure we have the necessary data points
            if not all([details.get('lp'), details.get('open_price'), details.get('volume')]):
                continue # Skip if data is incomplete

            current_price = details['lp']
            open_price = details['open_price']
            volume = details['volume']

            # --- Applying our filters ---
            # Price Surge Check
            price_change_pct = ((current_price - open_price) / open_price) * 100
            is_price_surging = price_change_pct >= PRICE_SURGE_PERCENT
            
            # Volume Check
            is_liquid_enough = volume > MINIMUM_VOLUME

            if is_price_surging and is_liquid_enough:
                logger.info(f"  --> SURGE DETECTED: {symbol} | Price Change: {price_change_pct:.2f}% | Volume: {volume:,}")
                surging_stocks.append(symbol)

        if not surging_stocks:
            logger.info("...Scan complete. No stocks met the surge criteria in this cycle.")
        
        return surging_stocks

    except FileNotFoundError:
        logger.critical("FATAL: nifty200_symbols.csv not found. Please run get_universe.py first.")
        return []
    except Exception as e:
        logger.error(f"An error occurred in the scanner: {e}", exc_info=True)
        return []


# --- This block allows us to test the scanner directly ---
if __name__ == '__main__':
    import logger_setup
    logger_setup.setup_logger()

    logger.info("--- Standalone Scanner Test Initialized ---")
    
    # We need an authenticated model to run the test
    fyers_model = fyers_client.get_fyers_model()

    if fyers_model:
        # Run the scan
        shortlist = scan_for_surges(fyers_model)
        
        if shortlist:
            logger.info("\n--- SCANNER SHORTLIST ---")
            for i, stock in enumerate(shortlist, 1):
                logger.info(f"{i}. {stock}")
            logger.info("-------------------------")
        else:
            logger.info("\n--- SCANNER RESULT: No surging stocks found. ---")
    else:
        logger.critical("Could not authenticate with Fyers. Halting scanner test.")