# ==============================================================================
# main.py - FINAL STRATEGY IMPLEMENTATION: "CONFLUENCE BREAKOUT"
# ==============================================================================

import llm_handler,paper_trader, risk_manager, config, news_handler, fyers_client, technical_analyzer
import time, datetime, logging, logger_setup

# --- Configuration ---
DEBUG_MODE = True # Keep True for pre-market testing, set to False for live run

def run_bot_cycle(fyers, paper_account):
    """
    Contains the logic for a single trading cycle using the Confluence Momentum strategy.
    """
    logger.info("--- New Cycle Started ---")
    logger.info("[Step 0] Managing open positions...")
    open_positions = list(paper_account.positions.keys())
    now = datetime.datetime.now()
    eod_exit_time = now.replace(hour=15, minute=15, second=0, microsecond=0)

    if not open_positions:
        logger.info("   ...No open positions to manage.")
    else:
        for symbol in open_positions:
            position_data = paper_account.positions[symbol]
            logger.info(f"   ...Checking position: {symbol}")

            # --- NEW: End-of-Day Exit Check ---
            if now >= eod_exit_time :
                logger.warning(f"   ---> END-OF-DAY EXIT TRIGGERED for {symbol}. Forcing sale.")
                live_price_quote = fyers.quotes({"symbols": symbol})
                live_price = live_price_quote['d'][0]['v']['lp'] if live_price_quote.get('s') == 'ok' else position_data['entry_price']
                paper_account.execute_sell(symbol, position_data['qty'], live_price)
                continue # Position is closed, move to the next one

            # --- Existing SL/TP Check ---
            try:
                live_quote = fyers.quotes({"symbols": symbol})
                if live_quote.get('s') == 'ok' and len(live_quote['d']) > 0:
                    live_price = live_quote['d'][0]['v']['lp']
                    logger.info(f"   ...Live price for {symbol} is {live_price}")

                    # Check for Stop-Loss
                    if live_price <= position_data['stop_loss']:
                        logger.info(f"   ---> STOP-LOSS TRIGGERED for {symbol} at {live_price}")
                        paper_account.execute_sell(symbol, position_data['qty'], live_price)
                        continue

                    # Check for Take-Profit
                    if live_price >= position_data['take_profit']:
                        logger.info(f"   ---> TAKE-PROFIT TRIGGERED for {symbol} at {live_price}")
                        paper_account.execute_sell(symbol, position_data['qty'], live_price)
                        continue
                else:
                    logger.warning(f"   ...Could not get live quote for open position: {symbol}")
            except Exception as e:
                logger.error(f"   ...Error fetching quote for open position: {e}", exc_info=True)

    # If all positions were closed by the EOD logic, we should not enter new trades
    if len(paper_account.positions) > 0:
        logger.info("   ...Holding existing position. Not looking for new trades.")
        paper_account.get_summary()
        return

    if now.time() >= eod_exit_time.time():
        logger.info("   ...Past EOD time. No new trades will be initiated.")
        paper_account.get_summary()
        return

    # STEP 0 - POSITION MANAGEMENT
    # ... (Your exit logic will be tested and refined here during live paper trading)
    # ...

    # STEP 1: GATHER MULTI-TIMEFRAME DATA

    # STEP 1: GATHER DATA
    logger.info("[Step 1] Gathering multi-timeframe market data...")
    try:
        end_date = datetime.date.today()
        start_date = end_date - datetime.timedelta(days=10)
        df_5min = fyers_client.get_historical_data(fyers, "NSE:NIFTY50-INDEX", "5", start_date, end_date)
        df_45min = fyers_client.get_historical_data(fyers, "NSE:NIFTY50-INDEX", "45", start_date, end_date)
        if df_5min.empty or df_45min.empty:
            logger.warning("   ...Could not fetch complete historical data. Skipping cycle.")
            return
    except Exception as e:
        logger.error(f"   ...Error during data gathering: {e}", exc_info=True)
        return

    # STEP 2: PERFORM FULL-SPECTRUM ANALYSIS
    logger.info("[Step 2] Performing full spectrum analysis...")
    
    # --- 2a: Feature Engineering for ML Model ---
    import technical_analyzer, ml_predictor # Import here to ensure logger is set up
    # Create the same features our model was trained on
    df_5min.ta.rsi(length=14, append=True)
    df_5min.ta.macd(fast=12, slow=26, signal=9, append=True)
    df_5min.ta.ema(length=10, append=True)
    df_5min.ta.ema(length=21, append=True)
    df_5min.ta.ema(length=50, append=True)
    df_5min.ta.ema(length=200, append=True)
    df_5min.ta.bbands(length=20, append=True)
    df_5min.ta.atr(length=14, append=True)
    df_5min['return_1h'] = df_5min['close'].pct_change(periods=12)
    df_5min['return_1d'] = df_5min['close'].pct_change(periods=75)
    df_5min = df_5min.dropna() # Drop rows with NaN values
    
    # Get the latest row of features for prediction
    latest_features = df_5min.tail(1)

    # --- 2b: Get ML Prediction ---
    ml_prediction = ml_predictor.get_prediction(latest_features.drop(columns=['open','high','low','close','volume']))
    logger.info(f"   ...ML Model Prediction: {'UP (1)' if ml_prediction == 1 else 'DOWN (0)' if ml_prediction == 0 else 'Error'}")

    # --- 2c: Get Quantitative & Qualitative Analysis ---
    technicals = technical_analyzer.get_technical_analysis(df_5min, df_45min)
    logger.info(f"   ...Quantitative: Regime='{technicals['regime']}', Signal='{technicals['entry_signal']}', TrendStrong={technicals['is_strong_trend']}")

    news_headlines = " | ".join(news_handler.get_latest_headlines("..."))
    llm_analysis = llm_handler.get_market_analysis(f"NIFTY at {technicals['latest_price']}", news_headlines)
    if not llm_analysis: return
    logger.info(f"   ...Qualitative: Outlook='{llm_analysis['outlook']}', Confidence={llm_analysis['confidence']}")

    # STEP 3: FINAL 5-LAYER CONFLUENCE CHECK
    logger.info("[Step 3] Executing Final Confluence Protocol...")
    trade_type = None

    # Bullish Confluence
    if (technicals['regime'] == "Bullish" and
        technicals['is_strong_trend'] and
        technicals['entry_signal'] == "Bullish_Breakout" and
        llm_analysis['outlook'] in ["Bullish", "Strongly Bullish"] and
        ml_prediction == 1): # <-- THE NEW ML FILTER
        logger.info("   ...[CONFIRMED] All 5 signals aligned for a BULLISH trade.")
        trade_type = "CE"

    # Bearish Confluence
    elif (technicals['regime'] == "Bearish" and
          technicals['is_strong_trend'] and
          technicals['entry_signal'] == "Bearish_Breakout" and
          llm_analysis['outlook'] in ["Bearish", "Strongly Bearish"] and
          ml_prediction == 0): # <-- THE NEW ML FILTER
        logger.info("   ...[CONFIRMED] All 5 signals aligned for a BEARISH trade.")
        trade_type = "PE"
        
    else:
        logger.info("   ...No confluence of signals. Standing down.")
    # STEP 4: EXECUTION
    if trade_type and len(paper_account.positions) == 0:
        logger.info(f"[Step 4] Actionable signal confirmed. Finding ATM {trade_type} option...")
        # ... (rest of the execution logic is the same)
    
    paper_account.get_summary()

# --- MAIN EXECUTION BLOCK ---
if __name__ == '__main__':
    logger = logger_setup.setup_logger()
    logger.info("====== CognitoTrader Agent Started: Protocol 'Confluence Breakout' Engaged ======")
    
    fyers = fyers_client.get_fyers_model()
    
    if fyers:
        paper_account = paper_trader.PaperAccount(initial_balance=config.ACCOUNT_BALANCE)
        logger.info("--- Initialization Complete. Entering Main Operational Loop ---")
        if DEBUG_MODE: logger.info(">>> DEBUG MODE IS ACTIVE. IGNORING MARKET HOURS. <<<")
        
        while True:
            try:
                now = datetime.datetime.now().time()
                market_open, market_close = datetime.time(9, 15), datetime.time(15, 30)

                if DEBUG_MODE or (market_open <= now <= market_close):
                    run_bot_cycle(fyers, paper_account)
                    wait_time = 30 if DEBUG_MODE else 100 # Shorter wait time for testing
                    logger.info(f"Cycle complete. Waiting for {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    logger.info(f"Market is closed. Waiting...")
                    time.sleep(60)
            except KeyboardInterrupt:
                logger.info(">>> Agent stopped manually by user. Shutting down. <<<")
                break
            except Exception as e:
                logger.error("An uncaught error occurred in the main loop!", exc_info=True)
                time.sleep(60)
    else:
        logger.critical("--- Halting due to Authentication Failure ---")