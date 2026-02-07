"""
Standalone script to run model and save results for GitHub Actions
This script is designed to run in GitHub Actions and save results to cached_results.json
"""

import sys
import os
import json
import math
from datetime import datetime

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from model import run_model

# GitHub Actions passes FRED_API_KEY via env; local can use config
FRED_API_KEY = os.environ.get("FRED_API_KEY", "")
if not FRED_API_KEY:
    try:
        from config import FRED_API_KEY as _k
        FRED_API_KEY = _k
    except ImportError:
        pass


def main():
    """Run model and save results for frontend."""
    print("🚀 Running Stock Prediction Model (GitHub Actions)")
    print("=" * 60)
    
    # Configuration
    target_tickers = ["NVDA", "ORCL", "THAR", "SOFI", "RR", "RGTI"]
    fred_series_map = {
        "FEDFUNDS": "Interest_Rate",
        "CPIAUCSL": "Inflation_Rate",
        "UNRATE": "Unemployment_Rate"
    }
    market_tickers = ["^GSPC", "^VIX"]
    
    print(f"\n📊 Analyzing {len(target_tickers)} stocks...")
    print(f"   Tickers: {', '.join(target_tickers)}")
    print(f"   Market indicators: {', '.join(market_tickers)}")
    print(f"   Economic variables: {', '.join(fred_series_map.keys())}")
    print("\n⏳ This may take 5-6 minutes...\n")
    
    try:
        # Run model
        results = run_model(
            target_tickers=target_tickers,
            fred_series_map=fred_series_map,
            market_tickers=market_tickers,
            backtest_start_date="2025-01-01",
            horizon=15,
            confidence_threshold=0.6,
            start_date="2021-01-01",
            fred_api_key=FRED_API_KEY
        )
        
        # Convert DataFrames to dicts for JSON serialization (everything the frontend needs)
        results_serializable = {
            "predictions": results["predictions"].to_dict('records'),
            "backtest_results": results["backtest_results"],
            "economic_data": results["economic_data"],
            "market_data": results["market_data"],
            "stock_data": results["stock_data"].to_dict('records'),
            "timestamp": datetime.now().isoformat(),
            "model_run_date": results.get("model_run_date")
        }

        # JSON does not allow NaN; convert to None so it becomes null
        def sanitize_for_json(obj):
            if isinstance(obj, dict):
                return {k: sanitize_for_json(v) for k, v in obj.items()}
            if isinstance(obj, list):
                return [sanitize_for_json(v) for v in obj]
            if isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
                return None
            return obj

        results_serializable = sanitize_for_json(results_serializable)
        
        # Save to public directory for Vercel to serve
        output_dir = "public"
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, "cached_results.json")
        
        with open(output_file, 'w') as f:
            json.dump(results_serializable, f, indent=2, default=str)
        
        print("\n✅ Model completed successfully!")
        print(f"   Predictions generated: {len(results['predictions'])}")
        print(f"   Backtest results: {len(results['backtest_results'])} stocks")
        print(f"   Results saved to: {output_file}")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Error running model: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
