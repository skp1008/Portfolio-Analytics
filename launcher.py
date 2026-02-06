"""
Main Launcher for Stock Analysis Application
Handles dependency checking, model execution with caching, and frontend launch
"""

import os
import sys
import json
import subprocess
from datetime import datetime, timedelta
import importlib.util


def check_dependencies():
    """Check if all required packages are installed."""
    required_packages = [
        'pandas', 'numpy', 'yfinance', 'fredapi', 'xgboost', 
        'scikit-learn', 'streamlit', 'plotly'
    ]
    
    missing = []
    for package in required_packages:
        spec = importlib.util.find_spec(package)
        if spec is None:
            missing.append(package)
    
    if missing:
        print("❌ Missing dependencies:")
        for pkg in missing:
            print(f"   - {pkg}")
        print("\n📦 Installing missing packages...")
        
        # Install missing packages
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing)
            print("✅ Dependencies installed successfully!")
        except subprocess.CalledProcessError:
            print("❌ Error installing dependencies. Please run:")
            print(f"   pip install {' '.join(missing)}")
            return False
    
    return True


def should_rerun_model():
    """Check if model should be rerun based on cache age."""
    cache_file = "cached_results.json"
    
    if not os.path.exists(cache_file):
        return True
    
    # Check cache age
    try:
        cache_time = os.path.getmtime(cache_file)
        cache_age = datetime.now() - datetime.fromtimestamp(cache_time)
        
        # Rerun if cache is older than 1 day (for now, later will be automated daily)
        if cache_age > timedelta(days=1):
            print("⚠️  Cache is older than 1 day. Rerunning model...")
            return True
        
        # Check if cache is valid
        with open(cache_file, 'r') as f:
            cached_data = json.load(f)
            if not cached_data or "predictions" not in cached_data:
                print("⚠️  Cache file is invalid. Rerunning model...")
                return True
        
        print(f"✅ Using cached results (age: {cache_age.seconds // 3600} hours)")
        return False
    except Exception as e:
        print(f"⚠️  Error reading cache: {e}. Rerunning model...")
        return True


def run_model():
    """Run the prediction model and cache results."""
    print("\n" + "="*60)
    print("🚀 Running Stock Prediction Model")
    print("="*60)
    
    try:
        from model import run_model
        from config import FRED_API_KEY
        
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
        
        # Save cache
        with open("cached_results.json", 'w') as f:
            json.dump(results_serializable, f, indent=2, default=str)
        
        print("\n✅ Model completed successfully!")
        print(f"   Predictions generated: {len(results['predictions'])}")
        print(f"   Backtest results: {len(results['backtest_results'])} stocks")
        print("   Results cached to: cached_results.json")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error running model: {e}")
        import traceback
        traceback.print_exc()
        return False


def launch_frontend():
    """Launch Streamlit frontend."""
    print("\n" + "="*60)
    print("🌐 Launching Dashboard")
    print("="*60)
    print("\n📱 Opening dashboard in your browser...")
    print("   💡 TIP: Keep this running and edit frontend.py directly.")
    print("   Streamlit will auto-reload when you save changes!")
    print("   Press Ctrl+C to stop the server\n")
    
    try:
        # Use --server.runOnSave=true for explicit auto-reload
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            "frontend.py",
            "--server.runOnSave=true",
            "--server.fileWatcherType=poll"  # Better file watching
        ], check=True)
    except KeyboardInterrupt:
        print("\n\n👋 Dashboard closed.")
    except Exception as e:
        print(f"\n❌ Error launching frontend: {e}")


def main():
    """Main launcher function."""
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║          Stock Analysis Dashboard - Launcher                  ║
    ╚══════════════════════════════════════════════════════════════╝
    """)
    
    # Step 1: Check dependencies
    print("\n[1/3] Checking dependencies...")
    if not check_dependencies():
        print("\n❌ Failed to install dependencies. Exiting.")
        return
    
    # Step 2: Run model (or use cache)
    print("\n[2/3] Checking model cache...")
    if should_rerun_model():
        if not run_model():
            print("\n❌ Model execution failed. Exiting.")
            return
    else:
        print("✅ Using cached results")
    
    # Step 3: Launch frontend
    print("\n[3/3] Starting frontend...")
    launch_frontend()


if __name__ == "__main__":
    main()

