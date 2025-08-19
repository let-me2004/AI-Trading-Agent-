# liquidity_scanner.py

import pandas as pd
import logging
import fyers_client

logger = logging.getLogger(__name__)

def find_top_liquid_stocks(fyers_instance, top_n=5):
    """
    Scans the NIFTY 200 universe to find the most liquid stocks for the day.
    :param fyers_instance: An authenticated FyersModel object.
    :param top_n: The number of top stocks to return.
    :return: A list of the top N liquid stock symbols.
    """
    try:
        # 1. Load our universe of stocks
        universe_df = pd.read_csv("nifty200_symbols.csv")
        symbol_list = universe_df["fyers_symbol"].tolist()
        logger.info(f"Loaded {len(symbol_list)} symbols for liquidity scan.")

        # 2. Fetch live quote data for the entire universe
        logger.info("Fetching bulk quote data for liquidity analysis...")
        quote_data = fyers_instance.quotes({"symbols": ",".join(symbol_list)})

        if quote_data.get('s') != 'ok' or not quote_data.get('d'):
            logger.error(f"Could not fetch bulk quote data. Response: {quote_data}")
            return []

        # 3. Calculate liquidity score for each stock
        liquidity_scores = []
        all_stock_data = quote_data['d']
        
        for stock in all_stock_data:
            details = stock.get('v', {})
            symbol = stock.get('n', 'UNKNOWN')
            
            # Ensure we have all necessary data points
            if not all([details.get('lp'), details.get('volume'), details.get('bid'), details.get('ask')]):
                continue

            last_price = details['lp']
            volume = details['volume']
            bid = details['bid']
            ask = details['ask']

            # Skip stocks with no volume or invalid spreads
            if volume == 0 or ask <= bid:
                continue

            # Calculate our metrics
            turnover = volume * last_price
            spread = ask - bid
            
            # The core liquidity score calculation
            liquidity_score = turnover / spread
            
            liquidity_scores.append({
                "symbol": symbol,
                "score": liquidity_score,
                "turnover": turnover,
                "spread": spread
            })

        if not liquidity_scores:
            logger.warning("...Scan complete. Could not calculate liquidity for any stocks.")
            return []
        
        # 4. Rank the stocks and return the top N
        ranked_stocks = sorted(liquidity_scores, key=lambda x: x['score'], reverse=True)
        
        top_stocks = [stock['symbol'] for stock in ranked_stocks[:top_n]]
        
        logger.info(f"\n--- Top {top_n} Liquid Stocks ---")
        for i, stock in enumerate(ranked_stocks[:top_n], 1):
            logger.info(f"{i}. {stock['symbol']} (Score: {stock['score']:.2f}, Turnover: ₹{stock['turnover']:,.0f}, Spread: {stock['spread']:.2f})")
        logger.info("--------------------------")

        return top_stocks

    except FileNotFoundError:
        logger.critical("FATAL: nifty200_symbols.csv not found. Please run universe_builder.py first.")
        return []
    except Exception as e:
        logger.error(f"An error occurred in the liquidity scanner: {e}", exc_info=True)
        return []


# --- Standalone Test Block ---
if __name__ == '__main__':
    import logger_setup
    logger_setup.setup_logger()

    logger.info("--- Standalone Liquidity Scanner Test ---")
    
    fyers_model = fyers_client.get_fyers_model()

    if fyers_model:
        # This scan should be run after the market has been open for a bit (e.g., at 9:30 AM)
        # to get meaningful volume and turnover data.
        top_targets = find_top_liquid_stocks(fyers_model, top_n=5)
        
        if top_targets:
            logger.info(f"\nScan complete. Recommended targets for today: {top_targets}")
        else:
            logger.info("\nScan complete. No suitable targets found.")
    else:
        logger.critical("Could not authenticate with Fyers. Halting scanner test.")
