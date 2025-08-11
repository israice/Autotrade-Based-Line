#!/usr/bin/env python3
"""
Binance REST API Client for XRPUSDT Perpetual Futures Candlestick Data
Polls Binance REST API every 0.5 seconds for current 1-minute candlestick data.
"""

import json
import logging
import asyncio
import aiohttp
import subprocess
import sys
from datetime import datetime
from typing import Dict, Any, Optional
import signal
import time

# ============================================================================
# Configuration Settings
# ============================================================================

SYMBOL = "XRPUSDT"
TIMEFRAME = "1m"
OUTPUT_FILE = "test.json"
REST_ENDPOINT = "https://fapi.binance.com/fapi/v1/klines"
POLLING_INTERVAL = 0.5
RESTART_INTERVAL = 120
RESTART_DELAY = 10
MAX_REQUESTS_PER_MINUTE = 96  # 80% of 120 theoretical max

# Rate limit backoff settings
RATE_LIMIT_BACKOFF_BASE = 2  # Base seconds for exponential backoff
RATE_LIMIT_MAX_BACKOFF = 60  # Maximum backoff time in seconds
REQUEST_WEIGHT_PER_CALL = 1

# Scripts to execute when candle is closed
SCRIPTS = [
    "CORE/BACKEND/Z_TOOLS/message_checked.py",
]

# HTTP request timeout in seconds
REQUEST_TIMEOUT = 10

# Logging configuration
LOG_LEVEL = logging.INFO
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"

# ============================================================================
# Global Variables
# ============================================================================

is_running = True
last_candle_close_time = None
script_start_time = None
shutdown_requested = False
last_sigint_time = 0
force_shutdown = False
restart_delayed = False
delayed_restart_time = None

request_count = 0
request_weight_used = 0
minute_start_time = time.time()
consecutive_failures = 0

# ============================================================================
# Logging Setup
# ============================================================================

logging.basicConfig(level=LOG_LEVEL, format=LOG_FORMAT)
logger = logging.getLogger(__name__)

# ============================================================================
# Signal Handlers
# ============================================================================

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully with double Ctrl+C force shutdown."""
    global is_running, shutdown_requested, last_sigint_time, force_shutdown
    
    current_time = time.time()
    
    if signum == signal.SIGINT:
        if shutdown_requested and (current_time - last_sigint_time) <= 2.0:
            logger.info("Double Ctrl+C detected. Force shutdown initiated...")
            force_shutdown = True
            is_running = False
            sys.exit(0)
        else:
            logger.info("Received SIGINT. Press Ctrl+C again within 2 seconds to force shutdown...")
            shutdown_requested = True
            last_sigint_time = current_time
            is_running = False
    else:
        logger.info(f"Received signal {signum}. Initiating graceful shutdown...")
        is_running = False
        shutdown_requested = True

# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# ============================================================================
# Script Execution Functions
# ============================================================================

def execute_scripts():
    """Execute the list of Python scripts when candle is closed."""
    logger.info("Candle closed. Executing scripts...")
    
    for script_path in SCRIPTS:
        try:
            result = subprocess.run([sys.executable, script_path], 
                                  capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                # Display actual script output if available
                if result.stdout.strip():
                    print(result.stdout.strip())
                else:
                    logger.info(f"Script executed successfully (no output): {script_path}")
            else:
                logger.error(f"Script failed: {script_path}")
                if result.stderr.strip():
                    print(f"Error output: {result.stderr.strip()}")
                
        except subprocess.TimeoutExpired:
            logger.error(f"Script timeout: {script_path}")
        except FileNotFoundError:
            logger.error(f"Script not found: {script_path}")
        except Exception as e:
            logger.error(f"Error executing {script_path}: {e}")

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
# Rate Limiting Functions
# ============================================================================

def reset_rate_limit_counters():
    """Reset rate limiting counters every minute."""
    global request_count, request_weight_used, minute_start_time
    current_time = time.time()
    
    if current_time - minute_start_time >= 60:
        request_count = 0
        request_weight_used = 0
        minute_start_time = current_time
        logger.debug(f"Rate limit counters reset")

def check_rate_limits() -> bool:
    """Check if we're approaching rate limits."""
    reset_rate_limit_counters()
    
    if request_count >= MAX_REQUESTS_PER_MINUTE:
        logger.warning(f"Approaching request limit: {request_count}/{MAX_REQUESTS_PER_MINUTE}")
        return False
    
    return True

def calculate_backoff_delay(failure_count: int) -> float:
    """Calculate exponential backoff delay."""
    delay = min(RATE_LIMIT_BACKOFF_BASE ** failure_count, RATE_LIMIT_MAX_BACKOFF)
    return delay

# ============================================================================
# REST API Functions
# ============================================================================

async def fetch_candlestick_data(session: aiohttp.ClientSession) -> Optional[Dict[str, Any]]:
    """
    Fetch current candlestick data from Binance REST API.
    
    Args:
        session: aiohttp client session
        
    Returns:
        Parsed candlestick data or None if failed
    """
    global request_count, request_weight_used, consecutive_failures
    
    try:
        if not check_rate_limits():
            logger.warning("Rate limit check failed. Skipping request.")
            return None
        
        params = {
            'symbol': SYMBOL,
            'interval': TIMEFRAME,
            'limit': 1
        }
        
        async with session.get(REST_ENDPOINT, params=params, timeout=REQUEST_TIMEOUT) as response:
            request_count += 1
            request_weight_used += REQUEST_WEIGHT_PER_CALL
            
            if response.status == 429:
                retry_after = response.headers.get('Retry-After', '60')
                logger.warning(f"Rate limit exceeded (429). Retry after {retry_after} seconds")
                consecutive_failures += 1
                await asyncio.sleep(int(retry_after))
                return None
            elif response.status == 418:
                retry_after = response.headers.get('Retry-After', '120')
                logger.error(f"IP banned (418). Retry after {retry_after} seconds")
                consecutive_failures += 1
                await asyncio.sleep(int(retry_after))
                return None
            elif response.status == 200:
                consecutive_failures = 0  # Reset failure counter on success
                data = await response.json()
                
                used_weight = response.headers.get('X-MBX-USED-WEIGHT-1M', 'N/A')
                logger.debug(f"Request successful. Used weight: {used_weight}")
                
                return parse_candlestick_data(data)
            else:
                logger.error(f"API request failed with status: {response.status}")
                consecutive_failures += 1
                return None
                
    except asyncio.TimeoutError:
        logger.error("Request timeout")
        consecutive_failures += 1
        return None
    except Exception as e:
        logger.error(f"Error fetching candlestick data: {e}")
        consecutive_failures += 1
        return None

async def polling_loop():
    """
    Main polling loop that fetches data every POLLING_INTERVAL seconds.
    """
    global is_running, last_candle_close_time, script_start_time, restart_delayed, delayed_restart_time, consecutive_failures
    
    script_start_time = time.time()
    
    async with aiohttp.ClientSession() as session:
        while is_running:
            try:
                current_time = time.time()
                
                if consecutive_failures > 0:
                    backoff_delay = calculate_backoff_delay(consecutive_failures)
                    logger.info(f"Applying backoff delay: {backoff_delay} seconds (failures: {consecutive_failures})")
                    await asyncio.sleep(backoff_delay)
                
                # Check if restart time is reached
                restart_time_reached = current_time - script_start_time >= RESTART_INTERVAL
                
                # Check if we have a delayed restart
                if delayed_restart_time and current_time >= delayed_restart_time:
                    logger.info(f"Delayed restart time reached. Restarting script...")
                    is_running = False
                    break
                
                candlestick_data = await fetch_candlestick_data(session)
                
                if candlestick_data:
                    if write_data_to_file(candlestick_data):
                        current_close_time = candlestick_data['close_time']
                        is_candle_closed = candlestick_data['is_kline_closed']
                        
                        # Check if restart coincides with candle close
                        if restart_time_reached and not restart_delayed:
                            if is_candle_closed:
                                # Delay restart by RESTART_DELAY seconds
                                delayed_restart_time = current_time + RESTART_DELAY
                                restart_delayed = True
                                logger.info(f"Restart coincides with candle close. Delaying restart by {RESTART_DELAY} seconds...")
                            else:
                                # Normal restart
                                logger.info(f"Restart interval ({RESTART_INTERVAL} seconds) reached. Restarting script...")
                                is_running = False
                                break
                        
                        if (is_candle_closed and 
                            last_candle_close_time != current_close_time):
                            execute_scripts()
                            last_candle_close_time = current_close_time
                    else:
                        logger.error("Failed to write data to file")
                
                if consecutive_failures == 0:
                    await asyncio.sleep(POLLING_INTERVAL)
                
            except Exception as e:
                logger.error(f"Error in polling loop: {e}")
                consecutive_failures += 1
                await asyncio.sleep(POLLING_INTERVAL)

async def main():
    """Main function to start the polling client."""
    global is_running
    
    logger.info("Starting Binance REST API Polling Client for XRPUSDT Perpetual Futures")
    logger.info(f"Symbol: {SYMBOL}")
    logger.info(f"Time Frame: {TIMEFRAME}")
    logger.info(f"Polling Interval: {POLLING_INTERVAL} seconds")
    logger.info(f"Restart Interval: {RESTART_INTERVAL} seconds")
    logger.info(f"Output File: {OUTPUT_FILE}")
    
    try:
        await polling_loop()
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    
    logger.info("Script completed successfully")

def run_with_restart():
    """Run the script with automatic restart functionality."""
    global force_shutdown, restart_delayed, delayed_restart_time
    
    while not force_shutdown:
        try:
            global is_running, shutdown_requested
            is_running = True
            shutdown_requested = False  # Reset shutdown flag for each restart
            restart_delayed = False
            delayed_restart_time = None
            
            asyncio.run(main())
            
            if shutdown_requested and not force_shutdown:
                logger.info("Graceful shutdown completed.")
                break
            elif not force_shutdown:
                logger.info("Restarting script...")
                time.sleep(1)
            
        except KeyboardInterrupt:
            if not shutdown_requested:
                logger.info("Received keyboard interrupt. Shutting down...")
            break
        except Exception as e:
            if not force_shutdown:
                logger.error(f"Fatal error: {e}")
                logger.info("Restarting script after error...")
                time.sleep(5)

if __name__ == "__main__":
    run_with_restart()
