# news_handler.py - FINAL DEFINITIVE VERSION (using yfinance)

import yfinance as yf
import logging
import logger_setup

logger = logging.getLogger(__name__)

def get_latest_headlines(stock_symbol, count=5):
    """
    Fetches recent news headlines for a specific stock symbol using yfinance.
    Parses the nested JSON structure correctly.
    :param stock_symbol: The stock symbol (e.g., "RELIANCE", "SBIN").
    :param count: The number of headlines to return.
    :return: A list of headline strings.
    """
    try:
        # Append .NS for National Stock Exchange symbols
        ticker_symbol = f"{stock_symbol}.NS"
        
        # Create a Ticker object
        ticker = yf.Ticker(ticker_symbol)
        
        # Fetch the news
        news_list = ticker.news
        
        if not news_list:
            logger.info(f"   ...No news found for {stock_symbol} via yfinance.")
            return []
            
        # Correctly parse the nested data structure with safety checks
        headlines = []
        for article in news_list[:count]:
            content = article.get('content', {})
            title = content.get('title')
            
            if title: # Only add the headline if it's not empty
                headlines.append(title)
                
        return headlines

    except Exception as e:
        logger.error(f"An error occurred in yfinance news handler for {stock_symbol}: {e}", exc_info=False)
        return []

# --- Test Block ---
if __name__ == '__main__':
    logger = logger_setup.setup_logger()
    logger.info("--- Standalone yfinance News Handler Test ---")
    
    test_symbol = "RELIANCE"
    headlines = get_latest_headlines(test_symbol)
    
    if headlines:
        logger.info(f"Successfully fetched headlines for {test_symbol}:")
        for i, headline in enumerate(headlines, 1):
            logger.info(f"{i}. {headline}")
    else:
        logger.info(f"Test complete. No recent headlines found for {test_symbol}.")