# hft_multi_main.py

import fyers_client
import logger_setup
import logging
from orderflow_analyzer import OrderFlowAnalyzer
from paper_trader import PaperAccount
import config
import time
import threading # Import the threading library

# Initialize the logger
logger = logger_setup.setup_logger()

def run_single_stock_agent(symbol):
    """
    This function is the 'brain' for a single stock. It will be run in its own thread.
    """
    logger.info(f"--- Launching agent for target: {symbol} ---")
    
    # Each thread gets its own analyzer and paper account to manage state independently
    analyzer = OrderFlowAnalyzer(symbol, imbalance_threshold=30.0)
    paper_account = PaperAccount(initial_balance=config.ACCOUNT_BALANCE / 5) # Divide capital among agents

    def on_tick_handler(tick_data):
        """
        The tick handler for this specific thread.
        """
        try:
            analyzer.process_tick(tick_data)
            signal = analyzer.get_signal()
            ltp = tick_data.get('ltp', 0)

            # --- Trade Execution Logic ---
            if signal != "NEUTRAL" and not paper_account.positions:
                logger.info(f"[{symbol}] ACTIONABLE SIGNAL: {signal} | Imbalance: {analyzer.last_imbalance_ratio:.2f}%")
                trade_qty = 1
                if signal == "BUY":
                    paper_account.execute_buy(symbol, trade_qty, ltp, 0, 0)
                elif signal == "SELL":
                    logger.warning(f"[{symbol}] Simulating SHORT SELL.")

            # --- Exit Logic ---
            elif signal == "NEUTRAL" and paper_account.positions:
                logger.info(f"[{symbol}] NEUTRAL SIGNAL: Exiting position.")
                open_symbol = list(paper_account.positions.keys())[0]
                position_data = paper_account.positions[open_symbol]
                paper_account.execute_sell(open_symbol, position_data['qty'], ltp)
                paper_account.get_summary()

        except Exception as e:
            logger.error(f"[{symbol}] Error in on_tick_handler: {e}", exc_info=True)

    # Start the WebSocket for this specific symbol
    # This will block and run forever for this thread
    fyers_client.start_level2_websocket(
        symbols=[symbol],
        on_tick=on_tick_handler
    )


if __name__ == '__main__':
    logger.info("====== Multi-Target Order Flow Agent Initializing ======")
    
    # STEP 1: Authenticate and run the liquidity scan to get our targets for the day
    fyers_model = fyers_client.get_fyers_model()
    
    if fyers_model:
        import liquidity_scanner
        # Run the scan to find the top 5 most active stocks
        top_targets = liquidity_scanner.find_top_liquid_stocks(fyers_model, top_n=5)

        if top_targets:
            logger.info(f"--- Top targets for today: {top_targets} ---")
            
            threads = []
            # STEP 2: Launch a separate agent (thread) for each target
            for target_symbol in top_targets:
                # Create a new thread. The 'target' is the function to run, 'args' are its arguments.
                thread = threading.Thread(target=run_single_stock_agent, args=(target_symbol,))
                threads.append(thread)
                thread.start() # Start the thread
                time.sleep(2) # Stagger the connections slightly

            logger.info(f"--- All {len(threads)} agent threads have been launched. ---")
            logger.info("System is now live. Press Ctrl+C to stop all agents.")

            # This main loop just keeps the main program alive
            try:
                while True:
                    time.sleep(10)
            except KeyboardInterrupt:
                logger.info(">>> Main shutdown signal received. All agents will be terminated. <<<")

        else:
            logger.warning("Liquidity scan found no suitable targets. Shutting down.")
    else:
        logger.critical("Could not authenticate with Fyers. Halting agent.")

    logger.info("====== Multi-Target Order Flow Agent Shut Down ======")
