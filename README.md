# Stock Analysis Dashboard

A single-stock analysis system that uses gradient boosting models to predict stock price movements and displays results through a Streamlit dashboard.

## Features

- **Stock Prediction Model**: Gradient boosting model that predicts whether a stock will Rise, Fall, or remain Neutral
- **Interactive Dashboard**: Streamlit-based dashboard with:
  - Movement history charts (1 day, 15 days, 1 month, 5 years, max)
  - Prediction pie chart (Rise/Fall/Neutral probabilities)
  - Action recommendation (BUY/HOLD/SHORT)
  - Model variables explanation
  - Economic conditions display
  - Market performance (S&P 500) chart
  - Backtest statistics and stock information

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API Keys

Edit `config.py` and add your FRED API key:
```python
FRED_API_KEY = "your-fred-api-key-here"
```

Get a free FRED API key from: https://fred.stlouisfed.org/docs/api/api_key.html

### 3. Run the Application

**Important:** Make sure you're in the `Portfolio-Analytics` directory before running the launcher.

```bash
cd Portfolio-Analytics
python launcher.py
```

The launcher will:
- Check and install missing dependencies
- Run the prediction model (or use cached results if recent)
- Launch the Streamlit dashboard in your browser

## How It Works

### Model Pipeline

1. **Data Fetching**: 
   - Fetches stock data using yfinance API
   - Fetches economic variables using FRED API (Interest Rate, Inflation, Unemployment)

2. **Feature Engineering**:
   - **Stock's Own History**: Returns (1, 5, 15, 30 day), momentum, volatility, RSI, drawdown
   - **Market Conditions**: S&P 500 (^GSPC) performance and volatility
   - **Volatility Index**: VIX levels and changes
   - **Economic Variables**: Interest rates, inflation (YoY), unemployment

3. **Model Training**: 
   - XGBoost classifier with 3 classes (Down, Flat, Up)
   - Uses rolling window backtesting for evaluation

4. **Prediction**:
   - Generates probabilities for Rise/Fall/Neutral
   - Provides action recommendation (BUY/HOLD/SHORT) based on confidence threshold

### Caching

- Model results are cached to `cached_results.json`
- Cache is valid for 24 hours (to be updated to daily automated runs later)
- This avoids re-running the 5-6 minute model execution on every launch

## Configuration

Edit `launcher.py` to modify:
- **Target Tickers**: Stocks to analyze (default: NVDA, ORCL, THAR, SOFI, RR, RGTI)
- **Market Tickers**: Market indicators (default: ^GSPC, ^VIX)
- **FRED Series**: Economic variables to fetch
- **Backtest Start Date**: Date to start backtesting
- **Horizon**: Prediction horizon in days (default: 15)
- **Confidence Threshold**: Minimum probability for action recommendation (default: 0.6)

## Project Structure

```
Quant-Project/
├── model.py              # Combined model (data fetching, feature engineering, prediction)
├── frontend.py           # Streamlit dashboard
├── launcher.py           # Main launcher with dependency checking and caching
├── config.py             # Configuration (API keys)
├── requirements.txt      # Python dependencies
├── stock_prediction.ipynb # Original Jupyter notebook
├── cached_results.json   # Cached model results (auto-generated)
└── README.md
```

## Default Stocks

The system analyzes these stocks by default:
- NVDA, ORCL, THAR, SOFI, RR, RGTI

Select any stock from the dropdown in the dashboard to view its analysis.

## Model Variables

The model uses four main categories of variables:

1. **Stock's Own History (AR1-like)**: Historical price movements, returns, momentum, volatility
2. **Overall Market Conditions**: S&P 500 performance and volatility
3. **Industry Conditions**: Sector ETF performance (via market indicators)
4. **Economic Variables**: Interest rates, inflation (YoY), unemployment rate

## Notes

- First run will take 5-6 minutes to fetch data and train models
- Subsequent runs use cached results (valid for 24 hours)
- For production, model will run once daily automatically and use cached results for user requests
