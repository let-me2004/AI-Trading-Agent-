# technical_analyzer.py - FINAL VERSION

import pandas as pd
import logging

logger = logging.getLogger(__name__)

# In technical_analyzer.py, replace this function

def get_technical_analysis(df_5min, df_45min):
    """
    Analyzes dataframes to provide signals for the Confluence Breakout v2 strategy.
    """
    try:
        # --- 45-Minute Analysis (Regime Filter) ---
        if not df_45min.empty:
            ema_50_45min = df_45min['close'].ewm(span=50, adjust=False).mean().iloc[-1]
            latest_price_45min = df_45min['close'].iloc[-1]
            regime = "Bullish" if latest_price_45min > ema_50_45min else "Bearish"
        else:
            regime = "Neutral"
            logger.warning("Could not calculate 45-min regime.")

        # --- 5-Minute Analysis (Entry and Trend Strength) ---
        if not df_5min.empty and len(df_5min) > 14:
            # Breakout Signal
            latest_close = df_5min['close'].iloc[-1]
            previous_high = df_5min['high'].iloc[-2]
            previous_low = df_5min['low'].iloc[-2]
            entry_signal = "No_Signal"
            if latest_close > previous_high: entry_signal = "Bullish_Breakout"
            elif latest_close < previous_low: entry_signal = "Bearish_Breakout"

            # --- ADX Calculation (REFACTORED AND FIXED) ---
            high = df_5min['high']
            low = df_5min['low']
            close = df_5min['close']
            
            plus_dm = high.diff()
            minus_dm = low.diff().mul(-1)
            
            plus_dm[(plus_dm < 0) | (plus_dm <= minus_dm)] = 0
            minus_dm[(minus_dm < 0) | (minus_dm <= plus_dm)] = 0
            
            tr1 = pd.DataFrame(high - low)
            tr2 = pd.DataFrame(abs(high - close.shift(1)))
            tr3 = pd.DataFrame(abs(low - close.shift(1)))
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            atr = tr.ewm(alpha=1/14, adjust=False).mean()

            plus_di = 100 * (plus_dm.ewm(alpha=1/14, adjust=False).mean() / atr)
            minus_di = 100 * (minus_dm.ewm(alpha=1/14, adjust=False).mean() / atr)
            
            dx = (abs(plus_di - minus_di) / (plus_di + minus_di)) * 100
            adx = dx.ewm(alpha=1/14, adjust=False).mean()
            is_strong_trend = adx.iloc[-1] > 20
            # --- END OF FIX ---

        else:
            entry_signal, is_strong_trend, latest_close = "No_Signal", False, 0
            logger.warning("Could not calculate 5-min signals.")

        return {
            "regime": regime,
            "entry_signal": entry_signal,
            "is_strong_trend": is_strong_trend,
            "latest_price": latest_close
        }

    except Exception as e:
        logger.error(f"Error calculating technical analysis: {e}", exc_info=True)
        return { "regime": "Neutral", "entry_signal": "No_Signal", "is_strong_trend": False, "latest_price": 0 }