# sector_mapper.py

import pandas as pd
import logging

logger = logging.getLogger(__name__)

# This dictionary maps the industry names from the NSE file to the Fyers index symbols
SECTOR_INDEX_MAP = {
    "FINANCIAL SERVICES": "NSE:NIFTYFINSRV-INDEX",
    "IT": "NSE:NIFTYIT-INDEX",
    "OIL & GAS": "NSE:NIFTYENERGY-INDEX",
    "AUTOMOBILE": "NSE:NIFTYAUTO-INDEX",
    "FMCG": "NSE:NIFTYFMCG-INDEX",
    "HEALTHCARE": "NSE:NIFTYPHARMA-INDEX",
    "METALS": "NSE:NIFTYMETAL-INDEX",
    "CONSUMER DURABLES": "NSE:NIFTYCONSUMER-INDEX",
    # Add other mappings as needed
}

_stock_to_sector_map = None

def _initialize_map():
    """
    Loads the NIFTY 200 constituents file and creates a mapping
    from each stock symbol to its sector index symbol.
    """
    global _stock_to_sector_map
    try:
        df = pd.read_csv("nifty200_raw.csv") # Assumes the raw file from universe_builder is present
        _stock_to_sector_map = {}
        for index, row in df.iterrows():
            symbol = row['Symbol']
            industry = row['Industry'].upper()
            # Find the matching index for the industry
            for sector_keyword, index_symbol in SECTOR_INDEX_MAP.items():
                if sector_keyword in industry:
                    _stock_to_sector_map[f"NSE:{symbol}-EQ"] = index_symbol
                    break
        logger.info("Successfully created stock-to-sector mapping for NIFTY 200.")
    except FileNotFoundError:
        logger.critical("FATAL: nifty200_raw.csv not found. Please run universe_builder.py first.")
        _stock_to_sector_map = {}
    except Exception as e:
        logger.error(f"Error initializing sector map: {e}", exc_info=True)
        _stock_to_sector_map = {}


def get_sector_index_for_stock(fyers_stock_symbol):
    """
    Returns the sector index for a given stock symbol.
    """
    global _stock_to_sector_map
    if _stock_to_sector_map is None:
        _initialize_map()
    
    return _stock_to_sector_map.get(fyers_stock_symbol)