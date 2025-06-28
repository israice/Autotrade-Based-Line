# autotrade-based-line

## Project Overview
autotrade-based-line is a cryptocurrency data monitoring system that fetches candle data from Binance and processes it through a series of Python scripts. The system runs in a continuous loop, executing each script in sequence based on the configuration in the settings file.

## Features
- Fetches real-time cryptocurrency candle data from Binance Futures API
- Supports perpetual contracts (PERPETUAL market type)
- Configurable symbol, interval, and other settings
- Sequential execution of multiple processing scripts
- Automatic memory management with garbage collection

## Requirements
- Python 3.7+
- Required Python packages:
  - PyYAML
  - aiohttp
  - asyncio

## Project Structure
```
autotrade-based-line/
├── run.py                  # Main script that orchestrates execution
├── settings.yaml           # Configuration settings
├── index.html              # Web page for displaying candlestick chart
├── candles.json            # JSON file with candle data for chart
└── CHECK_CHANGE/
    ├── AA_fetch_candles.py # Script that fetches candle data from Binance
    ├── AA_fetch_candles.json # JSON output of fetched candle data
    ├── AB_print1.py        # Processing script 1
    ├── AC_print2.py        # Processing script 2
    └── AD_print3.py        # Processing script 3
```


## Installation
1. Clone the repository or download the project files
2. Install the required dependencies:
   ```
   pip install pyyaml aiohttp
   ```

## Configuration
Edit the `settings.yaml` file to configure the system:

```yaml
symbol: XRPUSDT           # Trading pair symbol
interval: 1m              # Candle interval (e.g., 1m, 5m, 15m, 1h)
market_type: PERPETUAL    # Market type (currently only PERPETUAL is supported)
exchange: binance         # Exchange (currently only binance is supported)
candles_limit: 2          # Number of candles to fetch
delay: 5                  # Delay between execution cycles (in seconds)
```

## Usage
Run the main script to start the system:

```
python run.py
```

The system will:
1. Fetch candle data from Binance based on the configuration
2. Save the data to `CHECK_CHANGE/AA_fetch_candles.json`
3. Execute the processing scripts in sequence
4. Wait for the configured delay period
5. Repeat the process until interrupted (Ctrl+C)

### Web Interface
The project includes a web interface for visualizing candlestick data as a Japanese candlestick chart using [lightweight-charts](https://github.com/tradingview/lightweight-charts).

- `index.html` loads data from `candles.json` and renders the chart.
- `candles.json` should contain the candle data in JSON format.

#### Launching the Local Web Server
To view the chart, start a local server in the project directory. For example, using Python:

```
python -m http.server 8000
```

Then open [http://localhost:8000/index.html](http://localhost:8000/index.html) in your browser.

## Extending the System
To add additional processing scripts:
1. Create new Python script(s) in the `CHECK_CHANGE` directory
2. Add the script path(s) to the `files` list in `run.py`

## Notes
- The system will handle keyboard interrupts gracefully, completing the current iteration before exiting
- Memory is cleared after each cycle using garbage collection


## Dev
<details>
  <summary>DEV Log</summary>

## v0.0.1
- PROJECT CREATED DATE 2025.06.29
- created run.py that runing check list
- created settings.yaml with all needed settings
- created fetch candles.py that fetching candles from binance
- created clone candles.py that cloning candles file




## FUTURE PLANS
- create config when price hitting the line 

</details>





<details>
  <summary>Github CHEATSHEET</summary>

## CREATE NEW REPOSITORY
git init
git add .
git commit -m "PROJECT CREATED DATE 2025.06.29"
gh repo create

## Load last updates and replace existing local files
git fetch origin; git reset --hard origin/master; git clean -fd  

## Select a hash from the last 10 commits
git log --oneline -n 10  

## Use the hash to get that exact version locally
git fetch origin; git checkout master; git reset --hard 1eaef8b; git clean -fdx  

## Update repository
git add .  
git commit -m "PROJECT CREATED DATE 2025.06.29"  
git push



</details>


