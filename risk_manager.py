import math

# In risk_manager.py, replace this function

def calculate_trade_details(account_balance, risk_percentage, entry_price, stop_loss_price):
    """
    Calculates the position size and validates a trade based on risk parameters.
    """
    # This check now returns a consistent error format
    if entry_price <= stop_loss_price:
        return {
            "is_trade_valid": False,
            "reason": f"Entry price ({entry_price}) must be > stop-loss price ({stop_loss_price})."
        }

    max_risk_per_trade_rupees = account_balance * (risk_percentage / 100.0)
    risk_per_share_rupees = entry_price - stop_loss_price

    if risk_per_share_rupees <= 0:
        return {"is_trade_valid": False, "reason": "Risk per share is zero or negative."}

    quantity = max_risk_per_trade_rupees / risk_per_share_rupees
    position_size = math.floor(quantity)

    if position_size <= 0:
        return {
            "is_trade_valid": False,
            "reason": "Risk is too high for the given stop-loss. Calculated position size is zero."
            }

    actual_capital_at_risk = position_size * risk_per_share_rupees
    return {
        "is_trade_valid": True,
        "position_size": position_size,
        "max_risk_per_trade_rupees": round(max_risk_per_trade_rupees, 2),
        "actual_capital_at_risk_rupees": round(actual_capital_at_risk, 2),
        "entry_price": entry_price,
        "stop_loss_price": stop_loss_price
    }
# --- This is how we test our module ---
if __name__ == '__main__':
    print("Testing Risk Manager...")

    # --- Scenario 1: A valid trade ---
    print("\n--- SCENARIO 1: Valid Trade ---")
    account_capital = 40000  # Our hard-earned ₹40,000
    risk_percent = 1.0       # The 1% Rule
    option_entry_price = 100.0
    option_stop_loss = 80.0

    trade1 = calculate_trade_details(account_capital, risk_percent, option_entry_price, option_stop_loss)
    print(trade1)


    # --- Scenario 2: Risk is too high for the stop-loss ---
    print("\n--- SCENARIO 2: Risk Too High ---")
    account_capital = 40000
    risk_percent = 1.0
    option_entry_price = 100.0
    option_stop_loss = 98.0  # Very tight stop-loss

    trade2 = calculate_trade_details(account_capital, risk_percent, option_entry_price, option_stop_loss)
    print(trade2)

    # --- Scenario 3: Invalid prices ---
    print("\n--- SCENARIO 3: Invalid Prices ---")
    trade3 = calculate_trade_details(40000, 1.0, 100.0, 105.0)
    print(trade3)

    # --- Scenario 4: Abort Trade - Risk per share exceeds max risk ---
    print("\n--- SCENARIO 4: Abort Trade ---")
    account_capital = 40000
    risk_percent = 1.0
    option_entry_price = 500.0  # An expensive option
    option_stop_loss = 50.0   # A very wide stop-loss

    trade4 = calculate_trade_details(account_capital, risk_percent, option_entry_price, option_stop_loss)
    print(trade4)

    