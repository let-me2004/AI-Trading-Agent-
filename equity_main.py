# equity_main.py

# --- Module Imports ---
import llm_handler, risk_manager, config, news_handler, fyers_client, logger_setup, paper_trader, equity_scanner
import time, datetime, logging

# --- Configuration ---
DEBUG_MODE = False # Set to False for live, scheduled runs
MAX_OPEN_POSITIONS = 3 # The maximum number of stocks the agent can hold at once

def run_equity_agent_cycle(fyers, paper_account):
    """
    Contains the logic for a single cycle of the Equity Surge agent.
    """
    logger.info("--- New Equity Agent Cycle Started ---")

    # STEP 0: POSITION MANAGEMENT (EOD Exit)
    logger.info("[Step 0] Managing open positions...")
    now = datetime.datetime.now()
    eod_exit_time = now.replace(hour=15, minute=15, second=0, microsecond=0)
    
    if now >= eod_exit_time:
        if paper_account.positions:
            logger.warning(">>> END-OF-DAY EXIT TRIGGERED. Closing all open positions. <<<")
            for symbol in list(paper_account.positions.keys()):
                position_data = paper_account.positions[symbol]
                live_quote = fyers.quotes({"symbols": symbol})
                live_price = live_quote['d'][0]['v']['lp'] if live_quote.get('s') == 'ok' else position_data['entry_price']
                paper_account.execute_sell(symbol, position_data['qty'], live_price)
        logger.info("...Past EOD time. No new trades will be initiated.")
        return

    # STEP 1: RUN THE SCANNER
    logger.info("[Step 1] Running quantitative scanner...")
    shortlist = equity_scanner.scan_for_surges(fyers)
    if not shortlist:
        logger.info("...No stocks passed the quantitative scan.")
        paper_account.get_summary()
        return

    # STEP 2: APPLY SECTOR & SENTIMENT FILTERS
    logger.info(f"[Step 2] Applying Sector and Sentiment filters to {len(shortlist)} stock(s)...")
    final_trade_candidates = []
    import sector_mapper # Import our new module
    import technical_analyzer

    end_date = datetime.date.today()
    start_date = end_date - datetime.timedelta(days=10)

    for symbol in shortlist:
        if symbol in paper_account.positions:
            logger.info(f"   ...Already holding {symbol}. Skipping analysis.")
            continue
        
        # --- NEW: SECTOR CONFLUENCE CHECK ---
        sector_index = sector_mapper.get_sector_index_for_stock(symbol)
        if not sector_index:
            logger.warning(f"   ...No sector mapping found for {symbol}. Skipping.")
            continue

        logger.info(f"   ...Checking sector trend for {symbol} (Sector: {sector_index})")
        df_sector_45min = fyers_client.get_historical_data(fyers, sector_index, "45", start_date, end_date)
        
        # We need a simplified technical check here for the sector
        if not df_sector_45min.empty:
            ema_50_sector = df_sector_45min['close'].ewm(span=50, adjust=False).mean().iloc[-1]
            latest_price_sector = df_sector_45min['close'].iloc[-1]
            sector_regime = "Bullish" if latest_price_sector > ema_50_sector else "Bearish"
        else:
            sector_regime = "Neutral"

        if sector_regime != "Bullish":
            logger.info(f"   ---> REJECTED: {symbol} failed sector check. Sector regime is '{sector_regime}'.")
            continue
        logger.info(f"   ...Sector check PASSED for {symbol}.")
        # ------------------------------------

        # --- QUALITATIVE SENTIMENT CHECK ---
        logger.info(f"   ...Analyzing news for {symbol}...")
        stock_code = symbol.split(':')[1].split('-')[0]
        news_headlines = " | ".join(news_handler.get_latest_headlines(stock_code))
        
        tech_string = f"Stock {stock_code} is surging with strong sector support."
        llm_analysis = llm_handler.get_market_analysis(tech_string, news_headlines)
        
        if llm_analysis and llm_analysis['outlook'] in ["Bullish", "Strongly Bullish"]:
            logger.info(f"   ---> CONFIRMED: {symbol} passed qualitative filter with '{llm_analysis['outlook']}' outlook.")
            final_trade_candidates.append(symbol)
        else:
            logger.info(f"   ---> REJECTED: {symbol} did not pass qualitative filter.")

    # STEP 3: EXECUTION
    logger.info("[Step 3] Executing trades for confirmed candidates...")
    if not final_trade_candidates:
        logger.info("...No stocks passed the final qualitative filter.")
    
    for symbol in final_trade_candidates:
        if len(paper_account.positions) >= MAX_OPEN_POSITIONS:
            logger.warning(f"...Max position limit ({MAX_OPEN_POSITIONS}) reached. Cannot execute trade for {symbol}.")
            break

        logger.info(f"   ...Initiating trade for {symbol}.")
        live_quote = fyers.quotes({"symbols": symbol})
        if live_quote.get('s') == 'ok' and live_quote['d'][0]['v'].get('lp', 0) > 0:
            entry_price = live_quote['d'][0]['v']['lp']
            stop_loss_price = entry_price * 0.98
            take_profit_price = entry_price * 1.04

            trade_details = risk_manager.calculate_trade_details(
                account_balance=paper_account.balance,
                risk_percentage=config.RISK_PERCENTAGE,
                entry_price=entry_price,
                stop_loss_price=stop_loss_price
            )
            
            if trade_details.get("is_trade_valid"):
                logger.info(f"   ---> (SIMULATION MODE: Sending BUY order for {symbol} to Paper Trader...)")
                paper_account.execute_buy(symbol, trade_details['position_size'], entry_price, stop_loss_price, take_profit_price)
            else:
                logger.warning(f"   ---> TRADE REJECTED BY RISK MANAGER for {symbol}. Reason: {trade_details.get('reason')}")
        else:
            logger.warning(f"   ...Could not get a valid live price for {symbol}. Aborting trade.")

    paper_account.get_summary()


# MAIN EXECUTION BLOCK
if __name__ == '__main__':
    logger = logger_setup.setup_logger()
    logger.info("====== Equity Surge Agent Started ======")
    
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
                    run_equity_agent_cycle(fyers, paper_account)
                    wait_time = 60 if DEBUG_MODE else 1000
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