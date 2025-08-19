# sentiment_engine.py - FINAL WEIGHTED VERSION

import pandas as pd
import logging
import news_handler
import llm_handler

logger = logging.getLogger(__name__)

def get_nifty50_sentiment_score():
    """
    Calculates a WEIGHTED sentiment score for the NIFTY 50 index by analyzing
    the news of its top constituents based on their index weightage.
    """
    try:
        weights_df = pd.read_csv("nifty50_weights.csv")
        logger.info(f"Loaded {len(weights_df)} top constituents from nifty50_weights.csv")
    except FileNotFoundError:
        logger.critical("FATAL: nifty50_weights.csv not found. Please create it based on the Indexogram.")
        return 0.0 # Return neutral score on critical failure

    total_weighted_score = 0.0
    
    # Loop through each of the top stocks
    for index, row in weights_df.iterrows():
        symbol = row['Symbol']
        weight = row['Weightage']
        
        # Get news for the specific stock
        headlines = news_handler.get_latest_headlines(symbol, count=3)
        
        if headlines:
            logger.info(f"  -> Analyzing news for {symbol} (Weight: {weight:.2f}%)...")
            headlines_str = " | ".join(headlines)
            tech_str = f"Current news for {symbol}."
            
            analysis = llm_handler.get_market_analysis(tech_str, headlines_str)
            
            if analysis:
                outlook = analysis.get('outlook', 'Neutral')
                confidence = analysis.get('confidence', 0.5)
                
                # Convert outlook to a numerical score (-1, 0, or 1)
                score = 0
                if "Bullish" in outlook: score = 1
                elif "Bearish" in outlook: score = -1
                
                # Weight the score by confidence and the stock's actual index weightage
                weighted_score = score * confidence * (weight / 100.0)
                total_weighted_score += weighted_score
                
                logger.info(f"  -> {symbol} Sentiment: {outlook} | Weighted Score Contribution: {weighted_score:.4f}")

    logger.info(f"--- TOTAL NIFTY 50 WEIGHTED SENTIMENT SCORE: {total_weighted_score:.4f} ---")
    return total_weighted_score