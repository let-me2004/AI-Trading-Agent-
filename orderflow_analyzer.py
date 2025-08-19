# orderflow_analyzer.py

import logging

logger = logging.getLogger(__name__)

class OrderFlowAnalyzer:
    """
    Maintains a live model of the order book for a single symbol and calculates
    the real-time buy/sell imbalance.
    """
    def __init__(self, symbol, imbalance_threshold=30.0, depth=10):
        self.symbol = symbol
        self.imbalance_threshold = imbalance_threshold
        self.depth = depth # How many levels of the order book to use for calculation
        
        # Initialize the state
        self.bids = []
        self.asks = []
        self.last_imbalance_ratio = 0.0
        logger.info(f"OrderFlowAnalyzer initialized for {self.symbol} with threshold {self.imbalance_threshold}%")

    def _calculate_imbalance(self):
        """
        Calculates the imbalance ratio based on the current state of the order book.
        Formula: (TotalBidQty - TotalAskQty) / (TotalBidQty + TotalAskQty)
        """
        if not self.bids or not self.asks:
            return 0.0 # Cannot calculate if one side is empty

        # Sum the quantities for the top N levels of the book
        total_bid_qty = sum(level['volume'] for level in self.bids[:self.depth])
        total_ask_qty = sum(level['volume'] for level in self.asks[:self.depth])

        denominator = total_bid_qty + total_ask_qty
        if denominator == 0:
            return 0.0 # Avoid division by zero

        imbalance = (total_bid_qty - total_ask_qty) / denominator
        
        # Convert to a percentage
        self.last_imbalance_ratio = imbalance * 100
        return self.last_imbalance_ratio

    def process_tick(self, tick_data):
        """
        Processes a new tick from the WebSocket, updates the order book,
        and recalculates the imbalance.
        """
        try:
            # The Fyers WebSocket provides the full order book snapshot in each tick
            if 'bids' in tick_data and 'asks' in tick_data:
                self.bids = tick_data['bids']
                self.asks = tick_data['asks']
                
                # After updating the book, recalculate the imbalance
                self._calculate_imbalance()
            else:
                # This might be a different type of tick (e.g., just price update), we ignore it for now
                pass
        except Exception as e:
            logger.error(f"Error processing tick for {self.symbol}: {e}", exc_info=True)

    def get_signal(self):
        """
        Returns a trade signal based on the latest imbalance ratio.
        """
        if self.last_imbalance_ratio > self.imbalance_threshold:
            return "BUY"
        elif self.last_imbalance_ratio < -self.imbalance_threshold:
            return "SELL"
        else:
            return "NEUTRAL"

# --- This block allows us to test the analyzer directly ---
if __name__ == '__main__':
    import logger_setup
    logger_setup.setup_logger()

    logger.info("--- Standalone Order Flow Analyzer Test ---")
    
    # Create an instance for a test symbol
    analyzer = OrderFlowAnalyzer("NSE:SBIN-EQ", imbalance_threshold=30.0)

    # --- Simulate receiving a tick with a strong buy imbalance ---
    logger.info("\n--- Test Case 1: Strong Buy Imbalance ---")
    buy_heavy_tick = {
        'symbol': 'NSE:SBIN-EQ',
        'bids': [{'price': 100, 'volume': 5000}, {'price': 99, 'volume': 8000}], # Total Bid Qty = 13000
        'asks': [{'price': 101, 'volume': 1000}, {'price': 102, 'volume': 1500}]  # Total Ask Qty = 2500
    }
    analyzer.process_tick(buy_heavy_tick)
    logger.info(f"Calculated Imbalance: {analyzer.last_imbalance_ratio:.2f}%")
    logger.info(f"Generated Signal: {analyzer.get_signal()}")

    # --- Simulate receiving a tick with a strong sell imbalance ---
    logger.info("\n--- Test Case 2: Strong Sell Imbalance ---")
    sell_heavy_tick = {
        'symbol': 'NSE:SBIN-EQ',
        'bids': [{'price': 100, 'volume': 1000}, {'price': 99, 'volume': 1500}], # Total Bid Qty = 2500
        'asks': [{'price': 101, 'volume': 5000}, {'price': 102, 'volume': 8000}]  # Total Ask Qty = 13000
    }
    analyzer.process_tick(sell_heavy_tick)
    logger.info(f"Calculated Imbalance: {analyzer.last_imbalance_ratio:.2f}%")
    logger.info(f"Generated Signal: {analyzer.get_signal()}")

    # --- Simulate a neutral tick ---
    logger.info("\n--- Test Case 3: Neutral Imbalance ---")
    neutral_tick = {
        'symbol': 'NSE:SBIN-EQ',
        'bids': [{'price': 100, 'volume': 5000}],
        'asks': [{'price': 101, 'volume': 5000}]
    }
    analyzer.process_tick(neutral_tick)
    logger.info(f"Calculated Imbalance: {analyzer.last_imbalance_ratio:.2f}%")
    logger.info(f"Generated Signal: {analyzer.get_signal()}")
