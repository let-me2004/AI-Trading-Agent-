# technical_analyzer.py - FINAL VERSION WITH SECTOR ANALYSIS

import pandas as pd
import logging

logger = logging.getLogger(__name__)

def get_technical_analysis(df_5min, df_45min_nifty, df_45min_sector):
    """
    Analyzes dataframes for NIFTY and a key sector to provide confluent signals.
    """
    analysis = {
        "nifty_regime": "Neutral",
        "sector_regime": "Neutral",
        "entry_signal": "No_Signal",
        "is_strong_trend": False,
        "latest_price": 0
    }
    
    try:
        # --- 45-Minute NIFTY Analysis (Overall Regime) ---
        if not df_45min_nifty.empty:
            ema_50_nifty = df_45min_nifty['close'].ewm(span=50, adjust=False).mean().iloc[-1]
            latest_price_nifty = df_45min_nifty['close'].iloc[-1]
            analysis["nifty_regime"] = "Bullish" if latest_price_nifty > ema_50_nifty else "Bearish"

        # --- 45-Minute Sector Analysis (Sector Regime) ---
        if not df_45min_sector.empty:
            ema_50_sector = df_45min_sector['close'].ewm(span=50, adjust=False).mean().iloc[-1]
            latest_price_sector = df_45min_sector['close'].iloc[-1]
            analysis["sector_regime"] = "Bullish" if latest_price_sector > ema_50_sector else "Bearish"

        # --- 5-Minute Analysis (Entry Trigger & Trend Strength) ---
        if not df_5min.empty and len(df_5min) > 1:
            analysis["latest_price"] = df_5min['close'].iloc[-1]
            # Breakout Signal
            latest_close = df_5min['close'].iloc[-1]
            previous_high = df_5min['high'].iloc[-2]
            previous_low = df_5min['low'].iloc[-2]
            if latest_close > previous_high:
                analysis["entry_signal"] = "Bullish_Breakout"
            elif latest_close < previous_low:
                analysis["entry_signal"] = "Bearish_Breakout"
            
            # ADX placeholder - In a full version, the complex ADX calculation would be here.
            # For our current strategy, we will assume the trend is strong if a breakout occurs.
            if analysis["entry_signal"] != "No_Signal":
                analysis["is_strong_trend"] = True

        return analysis

    except Exception as e:
        logger.error(f"Error calculating technical analysis: {e}", exc_info=True)
        # Return the default neutral values on error
        return analysis