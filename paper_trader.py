# paper_trader.py - UPGRADED FOR EXIT LOGIC

import datetime

class PaperAccount:
    def __init__(self, initial_balance):
        self.initial_balance = initial_balance
        self.balance = initial_balance
        # The positions dictionary will now store more data
        self.positions = {}  # e.g., {'SYMBOL': {'qty': 10, 'entry_price': 100, 'stop_loss': 80, 'take_profit': 130}}
        self.trade_log = []
        self.trade_count = 0
        print(f"Paper Account initialized with balance: ₹{self.balance:,.2f}")

    def log_trade(self, symbol, side, qty, price, pnl=0):
        self.trade_count += 1
        trade_record = {
            "trade_id": self.trade_count,
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "symbol": symbol,
            "side": side,
            "qty": qty,
            "price": price,
            "pnl": pnl
        }
        self.trade_log.append(trade_record)
        print(f"LOGGED TRADE: {side} {qty} {symbol} @ {price:.2f} | Realized PnL: {pnl:,.2f}")

    def execute_buy(self, symbol, qty, price, stop_loss, take_profit):
        slippage_factor = 1.0005
        fill_price = price * slippage_factor
        cost = qty * fill_price
        
        if self.balance < cost:
            print(f"Execution failed: Insufficient balance to buy {qty} of {symbol}.")
            return False
        
        self.balance -= cost
        
        # We now store the SL and TP along with the position
        self.positions[symbol] = {
            'qty': qty, 
            'entry_price': fill_price,
            'stop_loss': stop_loss,
            'take_profit': take_profit
        }
            
        self.log_trade(symbol, "BUY", qty, fill_price)
        return True

    def execute_sell(self, symbol, qty, price):
        if symbol not in self.positions or self.positions[symbol]['qty'] < qty:
            print(f"Execution failed: Not enough position to sell {qty} of {symbol}.")
            return False

        slippage_factor = 0.9995
        fill_price = price * slippage_factor
        proceeds = qty * fill_price
        self.balance += proceeds
        
        entry_price = self.positions[symbol]['entry_price']
        cost_of_sold_shares = qty * entry_price
        profit_and_loss = proceeds - cost_of_sold_shares
        
        del self.positions[symbol]
            
        self.log_trade(symbol, "SELL", qty, fill_price, pnl=profit_and_loss)
        return True
        
    def get_summary(self):
        print("\n--- Paper Account Summary ---")
        print(f"Current Balance: ₹{self.balance:,.2f}")
        total_pnl = self.balance - self.initial_balance
        print(f"Total Realized PnL: ₹{total_pnl:,.2f}")
        print(f"Open Positions: {len(self.positions)}")
        if self.positions:
            for symbol, data in self.positions.items():
                print(f"  - {symbol}: Qty {data['qty']} @ Avg {data['entry_price']:.2f} | SL: {data['stop_loss']:.2f} | TP: {data['take_profit']:.2f}")
        print("---------------------------\n")