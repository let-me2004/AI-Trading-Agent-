# test_websocket.py

import fyers_client
import logger_setup
import logging

logger = logger_setup.setup_logger()

def my_tick_handler(tick_data):
    """
    This is our custom function that will be called for every single tick.
    For this test, we will just print the data to the screen.
    """
    logger.info(f"TICK RECEIVED: {tick_data}")


if __name__ == '__main__':
    logger.info("--- WebSocket Test Initialized ---")
    
    # Define the stock we want to watch
    symbols_to_watch = ["NSE:SBIN-EQ"] 
    
    # This is the main call. We tell our fyers_client to start the connection
    # and to call our 'my_tick_handler' function for every update.
    fyers_client.start_level2_websocket(
        symbols=symbols_to_watch,
        on_tick=my_tick_handler
    )