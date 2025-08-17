#!/usr/bin/env python3
"""
Simple Binance REST API Client for XRPUSDT Perpetual Futures Candlestick Data
Makes a single request, writes data to file and exits.
"""

import json
import logging
import asyncio
import aiohttp
import time
from datetime import datetime
from typing import Dict, Any, Optional

# ============================================================================
# Configuration Settings
# ============================================================================
SYMBOL = "XRPUSDT"
TIMEFRAME = "1m"
OUTPUT_FILE = "test.json"
REST_ENDPOINT = "https://fapi.binance.com/fapi/v1/klines"

# HTTP request timeout in seconds
REQUEST_TIMEOUT = 10

# Logging configuration
LOG_LEVEL = logging.INFO
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"

# ============================================================================
# Logging Setup
# ============================================================================
logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)
logger = logging.getLogger(__name__)

# ============================================================================
# Data Processing Functions
# ============================================================================
def parse_candlestick_data(api_response: list) -> Optional[Dict[str, Any]]:
    """
    Parse REST API response and extract candlestick data.
    
    Args:
        api_response: List containing kline data from REST API
    
    Returns:
        Parsed candlestick data or None if parsing fails
    """
    try:
        if not api_response or len(api_response) == 0:
            return None
        
        # Get the most recent kline data
        kline = api_response[-1]
        
        # Check if we have enough data points
        if len(kline) < 12:
            return None
        
        # Parse kline data according to Binance API format
        parsed_data = {
            "timestamp": datetime.now().isoformat(),
            "symbol": SYMBOL,
            "interval": TIMEFRAME,
            "open_time": int(kline[0]),
            "close_time": int(kline[6]),
            "open_price": float(kline[1]),
            "high_price": float(kline[2]),
            "low_price": float(kline[3]),
            "close_price": float(kline[4]),
            "volume": float(kline[5]),
            "number_of_trades": int(kline[8]),
            "is_kline_closed": int(kline[6]) < int(datetime.now().timestamp() * 1000),
            "quote_asset_volume": float(kline[7]),
            "taker_buy_base_volume": float(kline[9]),
            "taker_buy_quote_volume": float(kline[10])
        }
        
        return parsed_data
        
    except (IndexError, ValueError, TypeError) as e:
        logger.error(f"Failed to extract candlestick data: {e}")
        return None

def write_data_to_file(candlestick_data: Dict[str, Any]) -> bool:
    """
    Write candlestick data to JSON file, overwriting existing content.
    
    Args:
        candlestick_data: Parsed candlestick data
    
    Returns:
        True if write successful, False otherwise
    """
    try:
        with open(OUTPUT_FILE, 'w') as file:
            json.dump(candlestick_data, file, indent=2)
        
        return True
        
    except IOError as e:
        logger.error(f"Failed to write data to file: {e}")
        return False

# ============================================================================
# REST API Functions
# ============================================================================
async def fetch_candlestick_data() -> Optional[Dict[str, Any]]:
    """
    Fetch current candlestick data from Binance REST API.
    
    Returns:
        Parsed candlestick data or None if failed
    """
    try:
        params = {
            'symbol': SYMBOL,
            'interval': TIMEFRAME,
            'limit': 1
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(REST_ENDPOINT, params=params, timeout=REQUEST_TIMEOUT) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info("API request successful")
                    return parse_candlestick_data(data)
                else:
                    logger.error(f"API request failed with status: {response.status}")
                    return None
                    
    except asyncio.TimeoutError:
        logger.error("Request timeout")
        return None
    except Exception as e:
        logger.error(f"Error fetching candlestick data: {e}")
        return None

async def main():
    """Main function to fetch data and write to file."""
    start_time = time.time()
    
    logger.info("Starting Binance REST API Client")
    logger.info(f"Symbol: {SYMBOL}")
    logger.info(f"Time Frame: {TIMEFRAME}")
    
    try:
        candlestick_data = await fetch_candlestick_data()
        
        if candlestick_data:
            if write_data_to_file(candlestick_data):
                execution_time = time.time() - start_time
                logger.info(f"Script completed successfully in {execution_time:.3f} seconds")
                exit(0)
        else:
            logger.error("Failed to fetch candlestick data")
            execution_time = time.time() - start_time
            logger.info(f"Script failed after {execution_time:.3f} seconds")
            exit(1)
            
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        execution_time = time.time() - start_time
        logger.info(f"Script failed with exception after {execution_time:.3f} seconds")
        exit(1)

if __name__ == "__main__":
    asyncio.run(main())
