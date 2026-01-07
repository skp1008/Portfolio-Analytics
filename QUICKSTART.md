# Quick Start Guide

## Project Structure

```
Quant-Project/
├── etl_pipeline.py          # ETL pipeline: fetch, clean, store data
├── forecast_model.py        # Gradient boosting forecast model (placeholder)
├── portfolio_metrics.py     # Portfolio analytics calculations
├── app.py                   # Flask backend API
├── config.py                # Configuration (Azure credentials)
├── requirements.txt         # Python dependencies
├── stock_prediction.ipynb   # Original Jupyter notebook
├── dashboard/               # React.js frontend
│   ├── src/
│   │   ├── App.js
│   │   └── components/
│   └── package.json
├── AZURE_SETUP.md          # Azure setup instructions
└── README.md
```

## Quick Setup

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Azure SQL Database

1. Follow instructions in `AZURE_SETUP.md` to create Azure SQL Database
2. Update `config.py` with your Azure credentials

### 3. Run ETL Pipeline

```bash
python etl_pipeline.py
```

This will fetch stock data and store it in Azure SQL Database.

### 4. Start Backend API

```bash
python app.py
```

API runs on `http://localhost:5000`

### 5. Start React Dashboard

```bash
cd dashboard
npm install
npm start
```

Dashboard runs on `http://localhost:3000`

## Workflow

1. **ETL Pipeline** (`etl_pipeline.py`): Fetches latest stock data and stores in Azure
2. **Forecast Model** (`forecast_model.py`): Generates predictions (to be implemented)
3. **Portfolio Metrics** (`portfolio_metrics.py`): Calculates analytics and generates figures
4. **Backend API** (`app.py`): Serves data to React dashboard
5. **React Dashboard**: Displays visualizations and metrics

## Default Tickers

The system tracks these stocks by default:
- AMZN, AAPL, META, NVDA, GOOGL, MSFT, TSLA, NFLX, ADBE, ORCL

## Portfolio Start Date

The portfolio is assumed to have been purchased on **2020-01-01**.

## API Endpoints

- `GET /api/health` - Health check
- `GET /api/tickers` - List available tickers
- `GET /api/portfolio/metrics` - Get all portfolio metrics
- `GET /api/portfolio/prices` - Get price time series data
- `GET /api/portfolio/returns` - Get returns time series data
- `GET /api/portfolio/drawdown` - Get drawdown data
- `GET /api/forecast/predictions?ticker=AAPL` - Get forecast predictions

## Next Steps

1. Implement gradient boosting model in `forecast_model.py`
2. Connect forecast model to save predictions to database
3. Update dashboard to show real forecast data
4. Deploy to Azure App Service (see `AZURE_SETUP.md`)

