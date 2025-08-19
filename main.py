# ==============================================================================
# main.py - FINAL MASTER VERSION
# Protocol: "Confluence Breakout v2 with ML Filter"
# ==============================================================================

# --- Module Imports ---
import llm_handler, risk_manager, config, news_handler, fyers_client, logger_setup, paper_trader, technical_analyzer
import time, datetime, logging
import pandas_ta as ta # The missing import

# --- Configuration ---
DEBUG_MODE = False # Set to False for live, scheduled runs

def run_bot_cycle(fyers, paper_account):
    """
    Contains the logic for a single trading cycle.
    """
    logger.info("--- New Cycle Started ---")
    
    # STEP 0 - POSITION MANAGEMENT
    logger.info("[Step 0] Managing open positions...")
    now = datetime.datetime.now()
    eod_exit_time = now.replace(hour=15, minute=15, second=0, microsecond=0)
    open_positions = list(paper_account.positions.keys())

    if not open_positions:
        logger.info("   ...No open positions to manage.")
    else:
        for symbol in open_positions:
            position_data = paper_account.positions[symbol]
            logger.info(f"   ...Checking position: {symbol}")
            # EOD Exit Check first
            if now >= eod_exit_time and not DEBUG_MODE:
                logger.warning(f"   ---> END-OF-DAY EXIT TRIGGERED for {symbol}. Forcing sale.")
                live_quote = fyers.quotes({"symbols": symbol})
                live_price = live_quote['d'][0]['v']['lp'] if live_quote.get('s') == 'ok' else position_data['entry_price']
                paper_account.execute_sell(symbol, position_data['qty'], live_price)
                continue
            # SL/TP Check
            try:
                live_quote = fyers.quotes({"symbols": symbol})
                if live_quote.get('s') == 'ok' and len(live_quote['d']) > 0:
                    live_price = live_quote['d'][0]['v']['lp']
                    if live_price <= position_data['stop_loss']:
                        logger.info(f"   ---> STOP-LOSS TRIGGERED for {symbol} at {live_price}")
                        paper_account.execute_sell(symbol, position_data['qty'], live_price)
                    elif live_price >= position_data['take_profit']:
                        logger.info(f"   ---> TAKE-PROFIT TRIGGERED for {symbol} at {live_price}")
                        paper_account.execute_sell(symbol, position_data['qty'], live_price)
            except Exception as e:
                logger.error(f"   ...Error fetching quote for open position: {e}", exc_info=True)

    # Do not look for new trades if we are past the EOD entry cutoff
    if now.time() >= eod_exit_time.time() and not DEBUG_MODE:
        logger.info("   ...Past EOD time. No new trades will be initiated.")
        paper_account.get_summary()
        return
    # Or if we are already holding a position
    if len(paper_account.positions) > 0:
        logger.info("   ...Holding existing position. Not looking for new trades.")
        paper_account.get_summary()
        return

    # STEP 1: GATHER & SANITIZE DATA
    # STEP 1: GATHER DATA (NIFTY + SECTOR)
    logger.info("[Step 1] Gathering multi-timeframe market and sector data...")
    try:
        end_date = datetime.date.today()
        start_date = end_date - datetime.timedelta(days=10)
        
        df_5min_raw = fyers_client.get_historical_data(fyers, "NSE:NIFTY50-INDEX", "5", start_date, end_date)
        df_45min_raw_nifty = fyers_client.get_historical_data(fyers, "NSE:NIFTY50-INDEX", "45", start_date, end_date)
        df_45min_raw_sector = fyers_client.get_historical_data(fyers, "NSE:NIFTYBANK-INDEX", "45", start_date, end_date)

        df_5min = df_5min_raw[~df_5min_raw.index.duplicated(keep='first')].copy()
        df_45min_nifty = df_45min_raw_nifty[~df_45min_raw_nifty.index.duplicated(keep='first')].copy()
        df_45min_sector = df_45min_raw_sector[~df_45min_raw_sector.index.duplicated(keep='first')].copy()

        if df_5min.empty or df_45min_nifty.empty or df_45min_sector.empty:
            logger.warning("   ...Could not fetch complete data. Skipping cycle.")
            return
    except Exception as e:
        logger.error(f"   ...Error during data gathering: {e}", exc_info=True)
        return

    # STEP 2: PERFORM ANALYSIS
    logger.info("[Step 2] Performing full spectrum analysis...")
    import sentiment_engine # Import the correct engine
    
    # 2a. Quantitative Analysis (NIFTY + SECTOR)
    technicals = technical_analyzer.get_technical_analysis(df_5min, df_45min_nifty, df_45min_sector)
    logger.info(f"   ...Quantitative: NIFTY Regime='{technicals.get('nifty_regime')}', Sector Regime='{technicals.get('sector_regime')}', Signal='{technicals.get('entry_signal')}'")

    # 2b. Qualitative Analysis (WEIGHTED SENTIMENT)
    sentiment_score = sentiment_engine.get_nifty50_sentiment_score()
    
    # STEP 3: FINAL CONFLUENCE CHECK
    logger.info("[Step 3] Executing Weighted Confluence Protocol...")
    SENTIMENT_THRESHOLD = 0.005 # Our threshold for the weighted score
    trade_type = None

    # Bullish Confluence
    if (technicals.get('nifty_regime') == "Bullish" and
        technicals.get('sector_regime') == "Bullish" and
        technicals.get('entry_signal') == "Bullish_Breakout" and
        sentiment_score > SENTIMENT_THRESHOLD):
        logger.info(f"   ...[CONFIRMED] All signals aligned for a BULLISH trade. (Sentiment Score: {sentiment_score:.4f})")
        trade_type = "CE"

    # Bearish Confluence
    elif (technicals.get('nifty_regime') == "Bearish" and
          technicals.get('sector_regime') == "Bearish" and
          technicals.get('entry_signal') == "Bearish_Breakout" and
          sentiment_score < -SENTIMENT_THRESHOLD):
        logger.info(f"   ...[CONFIRMED] All signals aligned for a BEARISH trade. (Sentiment Score: {sentiment_score:.4f})")
        trade_type = "PE"
        
    else:
        logger.info(f"   ...No confluence of signals. Standing down. (Sentiment Score: {sentiment_score:.4f})")

    # STEP 4: EXECUTION
    if trade_type:
        logger.info(f"[Step 4] Actionable signal confirmed. Finding ATM {trade_type} option...")
        selected_option = fyers_client.find_nifty_option_by_offset(fyers, option_type=trade_type, offset=0)
        if selected_option and selected_option['ltp'] > 0:
            entry_price, stop_loss_price, take_profit_price = selected_option['ltp'], selected_option['ltp'] * 0.80, selected_option['ltp'] * 1.40
            trade_details = risk_manager.calculate_trade_details(paper_account.balance, config.RISK_PERCENTAGE, entry_price, stop_loss_price)
            if trade_details.get("is_trade_valid"):
                logger.info(f"   ---> (SIMULATION MODE: Sending BUY order for {trade_type} to Paper Trader...)")
                paper_account.execute_buy(selected_option['symbol'], trade_details['position_size'], entry_price, stop_loss_price, take_profit_price)
            else:
                logger.warning(f"   ---> TRADE REJECTED BY RISK MANAGER. Reason: {trade_details.get('reason')}")
        else:
            logger.warning("   ...Could not find a suitable, tradeable option contract.")
    
    paper_account.get_summary()


# MAIN EXECUTION BLOCK
if __name__ == '__main__':
    logger = logger_setup.setup_logger()
    logger.info("====== CognitoTrader Agent Started: Protocol 'Confluence Breakout v2' Engaged ======")
    
    fyers = fyers_client.get_fyers_model()
    
    if fyers:
        paper_account = paper_trader.PaperAccount(initial_balance=config.ACCOUNT_BALANCE)
        logger.info("--- Initialization Complete. Entering Main Operational Loop ---")
        if DEBUG_MODE: logger.info(">>> DEBUG MODE IS ACTIVE. IGNORING MARKET HOURS. <<<")
        
        while True:
            try:
                now = datetime.datetime.now()
                market_open, market_close = datetime.time(9, 15), datetime.time(15, 30)

                if DEBUG_MODE or (market_open <= now.time() <= market_close):
                    run_bot_cycle(fyers, paper_account)
                    wait_time = 30 if DEBUG_MODE else 100
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