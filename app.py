"""
Backend API: Flask application to serve portfolio analytics data
This API provides endpoints for the React dashboard to fetch data and metrics.
"""

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import pyodbc
import pandas as pd
import json
import os
from datetime import datetime
from portfolio_metrics import (
    calculate_portfolio_metrics,
    get_azure_connection,
    generate_all_figures,
    load_portfolio_data,
    calculate_returns,
    calculate_drawdown
)
from config import AZURE_SERVER, AZURE_DATABASE, AZURE_USERNAME, AZURE_PASSWORD

app = Flask(__name__, static_folder='dashboard/build', static_url_path='')
CORS(app)

# Default ticker list
DEFAULT_TICKERS = ["AMZN", "AAPL", "META", "NVDA", "GOOGL", "MSFT", "TSLA", "NFLX", "ADBE", "ORCL"]
PORTFOLIO_START_DATE = "2020-01-01"


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "message": "Portfolio Analytics API is running"})


@app.route('/api/tickers', methods=['GET'])
def get_tickers():
    """Get list of available tickers."""
    return jsonify({"tickers": DEFAULT_TICKERS})


@app.route('/api/portfolio/metrics', methods=['GET'])
def get_portfolio_metrics():
    """Get all portfolio metrics."""
    try:
        tickers = request.args.get('tickers', ','.join(DEFAULT_TICKERS)).split(',')
        start_date = request.args.get('start_date', PORTFOLIO_START_DATE)
        end_date = request.args.get('end_date', None)
        
        conn = get_azure_connection()
        metrics = calculate_portfolio_metrics(conn, tickers, start_date, end_date)
        conn.close()
        
        # Convert to JSON-serializable format
        response = {
            "tickers": tickers,
            "start_date": start_date,
            "end_date": metrics['prices'].index[-1].strftime('%Y-%m-%d'),
            "total_return": metrics['total_return'].to_dict(),
            "annualized_return": metrics['annualized_return'].to_dict(),
            "volatility": metrics['volatility'].to_dict(),
            "beta": metrics['beta'].to_dict(),
            "var_95": metrics['var_95'].to_dict(),
            "sharpe_ratio": metrics['sharpe_ratio'].to_dict(),
            "alpha": metrics['alpha'].to_dict(),
            "turnover_rate": metrics['turnover_rate'],
            "performance_summary": metrics['performance_summary'].to_dict('records'),
            "correlation_matrix": metrics['correlation_matrix'].to_dict()
        }
        
        return jsonify(response)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/portfolio/prices', methods=['GET'])
def get_prices():
    """Get price data for time series chart."""
    try:
        tickers = request.args.get('tickers', ','.join(DEFAULT_TICKERS)).split(',')
        start_date = request.args.get('start_date', PORTFOLIO_START_DATE)
        end_date = request.args.get('end_date', None)
        
        conn = get_azure_connection()
        prices_df = load_portfolio_data(conn, tickers, start_date, end_date)
        conn.close()
        
        # Convert to format suitable for frontend
        data = {
            "dates": [d.strftime('%Y-%m-%d') for d in prices_df.index],
            "prices": {}
        }
        
        for ticker in prices_df.columns:
            data["prices"][ticker] = prices_df[ticker].tolist()
        
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/portfolio/returns', methods=['GET'])
def get_returns():
    """Get returns data for time series chart."""
    try:
        tickers = request.args.get('tickers', ','.join(DEFAULT_TICKERS)).split(',')
        start_date = request.args.get('start_date', PORTFOLIO_START_DATE)
        end_date = request.args.get('end_date', None)
        
        conn = get_azure_connection()
        prices_df = load_portfolio_data(conn, tickers, start_date, end_date)
        returns_df = calculate_returns(prices_df)
        conn.close()
        
        # Convert to format suitable for frontend
        data = {
            "dates": [d.strftime('%Y-%m-%d') for d in returns_df.index],
            "returns": {}
        }
        
        for ticker in returns_df.columns:
            data["returns"][ticker] = (returns_df[ticker] * 100).tolist()
        
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/portfolio/drawdown', methods=['GET'])
def get_drawdown():
    """Get drawdown data."""
    try:
        tickers = request.args.get('tickers', ','.join(DEFAULT_TICKERS)).split(',')
        start_date = request.args.get('start_date', PORTFOLIO_START_DATE)
        end_date = request.args.get('end_date', None)
        
        conn = get_azure_connection()
        prices_df = load_portfolio_data(conn, tickers, start_date, end_date)
        drawdown_df = calculate_drawdown(prices_df)
        conn.close()
        
        # Convert to format suitable for frontend
        data = {
            "dates": [d.strftime('%Y-%m-%d') for d in drawdown_df.index],
            "drawdown": {}
        }
        
        for ticker in drawdown_df.columns:
            data["drawdown"][ticker] = drawdown_df[ticker].tolist()
        
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/forecast/predictions', methods=['GET'])
def get_forecast_predictions():
    """Get forecast predictions for a specific ticker."""
    ticker = request.args.get('ticker', 'AAPL')
    
    # Placeholder - will be implemented in forecast_model.py
    # For now, return sample data structure
    sample_predictions = {
        "ticker": ticker,
        "predictions": {
            "tomorrow": {
                "-25%": 0.02,
                "-10%": 0.05,
                "-5%": 0.10,
                "-1%": 0.15,
                "+1%": 0.20,
                "+5%": 0.25,
                "+10%": 0.15,
                "+25%": 0.08
            },
            "one_week": {
                "-25%": 0.03,
                "-10%": 0.08,
                "-5%": 0.12,
                "-1%": 0.17,
                "+1%": 0.18,
                "+5%": 0.22,
                "+10%": 0.12,
                "+25%": 0.08
            },
            "one_month": {
                "-25%": 0.05,
                "-10%": 0.10,
                "-5%": 0.12,
                "-1%": 0.15,
                "+1%": 0.15,
                "+5%": 0.18,
                "+10%": 0.15,
                "+25%": 0.10
            }
        }
    }
    
    return jsonify(sample_predictions)




@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    """Serve React app."""
    if path != "" and os.path.exists(app.static_folder + '/' + path):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

