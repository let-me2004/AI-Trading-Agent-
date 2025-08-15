# fyers_client.py - MASTER VERSION

import os
import webbrowser
import datetime
import pandas as pd
from fyers_apiv3.fyersModel import FyersModel, SessionModel
from config import FYERS_APP_ID, FYERS_SECRET_KEY
import time
import logging

logger = logging.getLogger(__name__)

# --- Configuration ---
REDIRECT_URI = "http://127.0.0.1" 
TOKEN_FILE = "access_token.txt"


def get_historical_data(fyers_instance, symbol, timeframe, start_date, end_date):
    """Fetches historical data and returns it as a pandas DataFrame."""
    try:
        data = {
            "symbol": symbol,
            "resolution": str(timeframe),
            "date_format": "1",
            "range_from": start_date.strftime("%Y-%m-%d"),
            "range_to": end_date.strftime("%Y-%m-%d"),
            "cont_flag": "1"
        }
        response = fyers_instance.history(data=data)
        if response.get("s") == 'ok' and response.get('candles'):
            candles = response['candles']
            df = pd.DataFrame(candles, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
            df = df.sort_values(by='timestamp').set_index('timestamp')
            return df
        else:
            logger.error(f"Could not fetch historical data for {symbol}: {response}")
            return pd.DataFrame()
    except Exception as e:
        logger.error(f"Error in get_historical_data for {symbol}: {e}", exc_info=True)
        return pd.DataFrame()

def get_next_expiry():
    """Calculates the nearest weekly expiry date (Thursday)."""
    today = datetime.date.today()
    days_ahead = (3 - today.weekday() + 7) % 7
    if days_ahead == 0 and datetime.datetime.now().time() > datetime.time(15, 30):
        days_ahead = 7
    expiry_date = today + datetime.timedelta(days=days_ahead)
    return expiry_date.strftime("%y%b%d").upper()

def find_nifty_option_by_offset(fyers_instance, option_type="CE", offset=0):
    """Finds a NIFTY option for the nearest expiry at a given offset from the ATM strike."""
    try:
        nifty_quote_data = {"symbols":"NSE:NIFTY50-INDEX"}
        nifty_quote = fyers_instance.quotes(data=nifty_quote_data)
        if nifty_quote.get('s') != 'ok':
            logger.error("Could not fetch NIFTY spot price.")
            return None
        nifty_spot_price = nifty_quote['d'][0]['v']['lp']
        logger.info(f"   ...NIFTY spot price is {nifty_spot_price}")

        atm_strike = round(nifty_spot_price / 50) * 50
        
        if option_type == "CE":
            target_strike = atm_strike + (offset * 50)
        else:
            target_strike = atm_strike - (offset * 50)
        logger.info(f"   ...Targeting {offset} strike(s) from ATM at {target_strike}")
        
        expiry_str = get_next_expiry()
        symbol = f"NSE:NIFTY{expiry_str}{int(target_strike)}{option_type}"
        logger.info(f"   ...Constructed symbol: {symbol}")

        option_quote_data = {"symbols": symbol}
        option_quote = fyers_instance.quotes(data=option_quote_data)

        if option_quote.get('s') == 'ok' and len(option_quote.get('d', [])) > 0:
            option_data = option_quote['d'][0]['v']
            if option_data.get('lp', 0) > 0:
                 return {"symbol": symbol, "ltp": option_data.get('lp'), "bid": option_data.get('bid'), "ask": option_data.get('ask')}
        
        logger.warning(f"Could not find a valid, tradeable quote for symbol {symbol}.")
        return None
            
    except Exception as e:
        logger.error(f"An error occurred in find_nifty_option_by_offset: {e}", exc_info=True)
        return None

def generate_new_token():
    """Generates a new access token via the manual login flow."""
    try:
        session = SessionModel(client_id=FYERS_APP_ID, secret_key=FYERS_SECRET_KEY, redirect_uri=REDIRECT_URI, response_type="code", grant_type="authorization_code")
        auth_url = session.generate_authcode()
        logger.info("--- NEW FYERS AUTHENTICATION REQUIRED ---")
        logger.info("1. A login page will now open. Please log in.")
        webbrowser.open(auth_url, new=1)
        auth_code = input("2. Paste the auth_code from the redirected URL here and press Enter: ")
        session.set_token(auth_code)
        response = session.generate_token()
        if response and "access_token" in response:
            access_token = response["access_token"]
            logger.info("Access Token generated successfully.")
            with open(TOKEN_FILE, 'w') as f: f.write(access_token)
            return access_token
        else:
            logger.error(f"Failed to generate Access Token. Response: {response}")
            return None
    except Exception as e:
        logger.error(f"Error during new token generation: {e}", exc_info=True)
        return None

def get_fyers_model():
    """Initializes and returns an authenticated FyersModel instance. Handles token expiration automatically."""
    access_token = None
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'r') as f:
            access_token = f.read().strip()

    if access_token:
        fyers = FyersModel(client_id=FYERS_APP_ID, token=access_token, log_path=os.path.join(os.getcwd(), "logs"))
        profile_check = fyers.get_profile()
        
        if profile_check.get('s') == 'ok':
            logger.info("Authentication successful using saved token.")
            return fyers
        else:
            logger.warning("Saved token is invalid or expired. Requesting new token.")
            if os.path.exists(TOKEN_FILE): os.remove(TOKEN_FILE)
    
    new_access_token = generate_new_token()
    if new_access_token:
        fyers = FyersModel(client_id=FYERS_APP_ID, token=new_access_token, log_path=os.path.join(os.getcwd(), "logs"))
        return fyers
    else:
        return None