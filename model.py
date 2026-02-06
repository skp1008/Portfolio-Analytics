"""
Combined Stock Prediction Model
Fetches data, processes features, trains model, and generates predictions
"""

import pandas as pd
import numpy as np
import yfinance as yf
from fredapi import Fred
from xgboost import XGBClassifier
from sklearn.utils.class_weight import compute_class_weight
from sklearn.metrics import accuracy_score, log_loss, f1_score
from datetime import datetime, timedelta
import json
import os
from config import FRED_API_KEY


def fetch_stock_data(ticker_list, start_date="2021-01-01"):
    """Fetch stock data for multiple tickers using yfinance."""
    df = yf.download(
        ticker_list,
        start=start_date,
        auto_adjust=False,
        group_by="ticker",
        progress=False
    )
    
    if df.empty:
        return pd.DataFrame()
    
    df = df.stack(level=0).reset_index().rename(columns={"level_1": "Ticker"})
    df["Date"] = pd.to_datetime(df["Date"]).dt.strftime("%Y-%m-%d")
    df = df[["Ticker", "Date", "Open", "High", "Low", "Close", "Adj Close", "Volume"]]
    df = df.sort_values(["Ticker", "Date"]).reset_index(drop=True)
    
    return df


def fetch_fred_data(fred_series_map, start_date="2021-01-01", api_key=None):
    """
    Fetch economic data from FRED API.
    
    Args:
        fred_series_map: Dict mapping FRED series codes to column names
            e.g., {"FEDFUNDS": "Interest_Rate", "CPIAUCSL": "Inflation_Rate", "UNRATE": "Unemployment_Rate"}
        start_date: Start date for data
        api_key: FRED API key (from config if None)
    
    Returns:
        DataFrame with Date and economic variables
    """
    if api_key is None:
        api_key = FRED_API_KEY
    
    fred = Fred(api_key=api_key)
    dfs = []
    
    for code, new_name in fred_series_map.items():
        try:
            s = fred.get_series(code, observation_start=start_date)
            df = pd.DataFrame({"Date": s.index, new_name: s.values})
            dfs.append(df)
        except Exception as e:
            print(f"Warning: Could not fetch {code}: {e}")
            continue
    
    if not dfs:
        return pd.DataFrame()
    
    fred_data = dfs[0]
    for df in dfs[1:]:
        fred_data = fred_data.merge(df, on="Date", how="outer")
    
    fred_data = fred_data.sort_values("Date")
    fred_data["Date"] = pd.to_datetime(fred_data["Date"]).dt.strftime("%Y-%m-%d")
    fred_data.reset_index(drop=True, inplace=True)
    
    # Calculate YoY inflation rate if CPIAUCSL is present
    if "Inflation_Rate" in fred_data.columns:
        # CPIAUCSL is monthly data, so shift by 12 months for YoY calculation
        fred_data_sorted = fred_data.sort_values("Date").copy()
        # For monthly data, approximate 12-month shift
        fred_data_sorted["Inflation_Rate_12mo"] = fred_data_sorted["Inflation_Rate"].shift(12)
        # Calculate YoY percentage change
        fred_data_sorted["Inflation_YoY"] = ((fred_data_sorted["Inflation_Rate"] / fred_data_sorted["Inflation_Rate_12mo"]) - 1) * 100
        fred_data_sorted = fred_data_sorted.drop("Inflation_Rate_12mo", axis=1)
        fred_data = fred_data_sorted
    
    return fred_data


def make_features(df_group, spx_col, vix_col):
    """Create features for a single ticker."""
    x = df_group.sort_values("Date").copy()
    px = x["Adj Close"].astype(float)
    logp = np.log(px)
    
    # Stock's own history (AR1-like features)
    x["r1"] = logp.diff()
    x["r5"] = logp.diff(5)
    x["r15"] = logp.diff(15)
    x["r30"] = logp.diff(30)
    
    r1 = x["r1"]
    x["mom10"] = r1.rolling(10).mean()
    x["mom20"] = r1.rolling(20).mean()
    x["vol20"] = r1.rolling(20).std()
    x["dd30"] = px / px.rolling(30).max() - 1.0
    
    # Market conditions (^GSPC)
    spx_px = x[spx_col].astype(float)
    spx_log = np.log(spx_px)
    x["spx_r1"] = spx_log.diff()
    x["spx_r30"] = spx_log.diff(30)
    x["spx_vol20"] = x["spx_r1"].rolling(20).std()
    
    # Volatility index (^VIX)
    vix = x[vix_col].astype(float)
    x["vix_chg"] = np.log(vix).diff()
    x["vix_lvl"] = vix
    x["risk_off"] = (x["vix_lvl"] > x["vix_lvl"].rolling(60).median()).astype(float)
    
    # Volume features
    vol = x["Volume"].astype(float)
    x["vol_ratio20"] = vol / vol.rolling(20).mean()
    
    # RSI
    delta = px.diff()
    up = delta.clip(lower=0)
    down = (-delta).clip(lower=0)
    rs = up.rolling(14).mean() / down.rolling(14).mean()
    x["rsi14"] = 100 - (100 / (1 + rs))
    
    # Relative strength
    x["rel_str30"] = x["r30"] - x["spx_r30"]
    
    # Day of week
    x["Date_dt"] = pd.to_datetime(x["Date"])
    dow = x["Date_dt"].dt.dayofweek.astype(float)
    x["dow_sin"] = np.sin(2 * np.pi * dow / 7.0)
    x["dow_cos"] = np.cos(2 * np.pi * dow / 7.0)
    x = x.drop("Date_dt", axis=1)
    
    return x


def run_model(
    target_tickers,
    fred_series_map,
    market_tickers,
    backtest_start_date="2025-01-01",
    horizon=15,
    confidence_threshold=0.6,
    start_date="2021-01-01",
    fred_api_key=None
):
    """
    Main function to run the complete prediction pipeline.
    
    Args:
        target_tickers: List of stock tickers to analyze
        fred_series_map: Dict mapping FRED codes to column names
        market_tickers: List of market/ETF tickers (e.g., ["^GSPC", "^VIX"])
        backtest_start_date: Start date for backtesting
        horizon: Prediction horizon in days
        confidence_threshold: Minimum probability for action recommendation
        start_date: Start date for data fetching
        fred_api_key: FRED API key
    
    Returns:
        Dict containing:
            - predictions: DataFrame with predictions for all tickers
            - backtest_results: Dict of backtest results per ticker
            - economic_data: Latest economic variables
            - market_data: Market ticker data
    """
    print("Step 1: Fetching stock data...")
    all_tickers = sorted(set(target_tickers + market_tickers))
    stock_data = fetch_stock_data(all_tickers, start_date)
    
    if stock_data.empty:
        raise ValueError("No stock data fetched")
    
    print("Step 2: Fetching economic data...")
    fred_data = fetch_fred_data(fred_series_map, start_date, fred_api_key)
    
    if fred_data.empty:
        raise ValueError("No economic data fetched")
    
    print("Step 3: Processing features...")
    df = stock_data.copy()
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.sort_values(["Ticker", "Date"]).reset_index(drop=True)
    
    macro = fred_data.copy()
    macro["Date"] = pd.to_datetime(macro["Date"])
    macro = macro.sort_values("Date").reset_index(drop=True)
    
    # Extract market data
    spx_ticker = "^GSPC" if "^GSPC" in market_tickers else market_tickers[0]
    vix_ticker = "^VIX" if "^VIX" in market_tickers else market_tickers[1] if len(market_tickers) > 1 else market_tickers[0]
    
    def context_series(dfx, tkr):
        col = "Close" if tkr == vix_ticker else "Adj Close"
        px = dfx[dfx["Ticker"] == tkr][["Date", col]].copy()
        return px.rename(columns={col: f"PX_{tkr}"})
    
    df = df.merge(context_series(df, spx_ticker), on="Date", how="left")
    df = df.merge(context_series(df, vix_ticker), on="Date", how="left")
    
    df = df[df["Ticker"].isin(target_tickers)].copy()
    df = df.sort_values("Date").reset_index(drop=True)
    
    # Merge economic data
    macro_cols = list(fred_series_map.values())
    df = pd.merge_asof(
        df,
        macro[["Date"] + macro_cols].sort_values("Date"),
        on="Date",
        direction="backward"
    )
    
    df = df.sort_values(["Ticker", "Date"]).reset_index(drop=True)
    
    # Forward fill
    df[f"PX_{spx_ticker}"] = df[f"PX_{spx_ticker}"].ffill()
    df[f"PX_{vix_ticker}"] = df[f"PX_{vix_ticker}"].ffill()
    for c in macro_cols:
        df[c] = df[c].ffill()
    
    # Create features
    df = df.groupby("Ticker", group_keys=False).apply(
        lambda x: make_features(x, f"PX_{spx_ticker}", f"PX_{vix_ticker}")
    ).reset_index(drop=True)
    
    # Define feature columns
    feature_cols = [
        "r1", "r5", "r15", "r30",
        "mom10", "mom20", "vol20",
        "dd30",
        "spx_r1",
        "vix_chg", "vix_lvl",
        "vol_ratio20",
        "rsi14",
        "rel_str30",
        "dow_sin", "dow_cos",
        "spx_vol20",
        "risk_off"
    ] + macro_cols
    
    must_have = ["r1", "vol20", "spx_r1", "vix_lvl", "vol_ratio20", "rsi14", "rel_str30"] + macro_cols
    
    # Create labels
    open_dates = df["Date"].drop_duplicates().sort_values().reset_index(drop=True)
    
    def next_open_date(target_date):
        future = open_dates[open_dates >= target_date]
        if len(future) == 0:
            return None
        return future.iloc[0]
    
    def label_3class(r):
        if r <= -0.01:
            return 0  # Down
        if r >= 0.01:
            return 2  # Up
        return 1  # Flat
    
    df["y"] = np.nan
    df["y_date"] = pd.NaT
    
    for tkr in target_tickers:
        w = df[df["Ticker"] == tkr].copy().sort_values("Date")
        date_to_close = dict(zip(w["Date"].values, w["Adj Close"].values))
        for idx, d in zip(w.index, w["Date"].values):
            tgt = next_open_date(pd.Timestamp(d) + pd.Timedelta(days=horizon))
            if tgt is None:
                continue
            if tgt not in date_to_close:
                continue
            cur = float(df.loc[idx, "Adj Close"])
            future = float(date_to_close[tgt])
            r = (future / cur) - 1.0
            df.loc[idx, "y"] = label_3class(r)
            df.loc[idx, "y_date"] = tgt
    
    print("Step 4: Training models and generating predictions...")
    
    def make_model():
        return XGBClassifier(
            n_estimators=225,
            learning_rate=0.05,
            max_depth=5,
            subsample=0.8,
            colsample_bytree=0.8,
            min_child_weight=5,
            objective="multi:softprob",
            num_class=3,
            eval_metric="mlogloss",
            tree_method="hist",
            random_state=42,
            n_jobs=-1
        )
    
    def class_counts_3(y):
        y = np.asarray(y, dtype=int)
        c = np.bincount(y, minlength=3)
        return int(c[0]), int(c[1]), int(c[2])
    
    # Backtest function
    def backtest_single_ticker(ticker, start_test_date, step=5, min_train_rows=250):
        w = df[df["Ticker"] == ticker].copy().sort_values("Date").reset_index(drop=True)
        start_test_date = pd.to_datetime(start_test_date)
        
        candidate = w[w["Date"] >= start_test_date].copy()
        candidate = candidate[candidate[must_have].notna().all(axis=1)].copy()
        
        if len(candidate) == 0:
            return None, None, None, None
        
        test_dates = candidate["Date"].drop_duplicates().sort_values().iloc[::step]
        
        rows_all = []
        y_true_all = []
        y_pred_all = []
        proba_all = []
        
        for d in test_dates:
            train = w[(w["Date"] < d) & (w["y_date"] <= d)].dropna(subset=feature_cols + ["y"])
            if len(train) < min_train_rows:
                continue
            
            test = w[w["Date"] == d].dropna(subset=feature_cols)
            if len(test) != 1:
                continue
            
            X_tr = train[feature_cols].values
            y_tr = train["y"].astype(int).values
            
            classes = np.unique(y_tr)
            if len(classes) < 2:
                continue
            
            weights = compute_class_weight(class_weight="balanced", classes=classes, y=y_tr)
            w_map = {int(c): float(wt) for c, wt in zip(classes, weights)}
            sample_w = np.array([w_map[int(yy)] for yy in y_tr], dtype=float)
            
            model = make_model()
            model.fit(X_tr, y_tr, sample_weight=sample_w)
            
            proba = model.predict_proba(test[feature_cols].values)
            y_pred = int(np.argmax(proba, axis=1)[0])
            
            tgt = next_open_date(pd.to_datetime(d) + pd.Timedelta(days=horizon))
            if tgt is None:
                continue
            
            future_row = w[w["Date"] == tgt]
            if len(future_row) != 1:
                continue
            
            cur = float(test["Adj Close"].iloc[0])
            fut = float(future_row["Adj Close"].iloc[0])
            y_true = label_3class((fut / cur) - 1.0)
            
            rows_all.append({
                "Date": d,
                "y_true": y_true,
                "y_pred": y_pred,
                "proba": proba[0]
            })
            y_true_all.append(y_true)
            y_pred_all.append(y_pred)
            proba_all.append(proba[0])
        
        if len(rows_all) == 0:
            return None, None, None, None
        
        y_true_arr = np.array(y_true_all, dtype=int)
        y_pred_arr = np.array(y_pred_all, dtype=int)
        proba_arr = np.vstack(proba_all)
        
        accuracy = accuracy_score(y_true_arr, y_pred_arr)
        log_loss_val = log_loss(y_true_arr, proba_arr, labels=[0, 1, 2])
        f1_macro = f1_score(y_true_arr, y_pred_arr, average='macro')
        f1_weighted = f1_score(y_true_arr, y_pred_arr, average='weighted')
        
        true_down, true_flat, true_up = class_counts_3(y_true_arr)
        pred_down, pred_flat, pred_up = class_counts_3(y_pred_arr)
        
        backtest_metrics = {
            "accuracy": float(accuracy),
            "log_loss": float(log_loss_val),
            "f1_macro": float(f1_macro),
            "f1_weighted": float(f1_weighted),
            "true_counts": {"down": true_down, "flat": true_flat, "up": true_up},
            "pred_counts": {"down": pred_down, "flat": pred_flat, "up": pred_up},
            "n_folds": len(rows_all)
        }
        
        return y_true_arr, y_pred_arr, proba_arr, backtest_metrics
    
    # Generate predictions for most recent date
    signal_date = pd.to_datetime(df["Date"].max())
    predictions = []
    backtest_results = {}
    
    for tkr in target_tickers:
        w = df[df["Ticker"] == tkr].copy().sort_values("Date").reset_index(drop=True)
        w["Date"] = pd.to_datetime(w["Date"])
        
        test = w[w["Date"] == signal_date].dropna(subset=feature_cols)
        if len(test) != 1:
            continue
        
        train = w[(w["Date"] < signal_date) & (w["y_date"] <= signal_date)].dropna(subset=feature_cols + ["y"])
        if len(train) < 250:
            continue
        
        X_tr = train[feature_cols].values
        y_tr = train["y"].astype(int).values
        
        classes = np.unique(y_tr)
        if len(classes) < 2:
            continue
        
        weights = compute_class_weight(class_weight="balanced", classes=classes, y=y_tr)
        w_map = {int(c): float(wt) for c, wt in zip(classes, weights)}
        sample_w = np.array([w_map[int(yy)] for yy in y_tr], dtype=float)
        
        model = make_model()
        model.fit(X_tr, y_tr, sample_weight=sample_w)
        
        proba = model.predict_proba(test[feature_cols].values)[0]
        
        tgt = next_open_date(pd.to_datetime(signal_date) + pd.Timedelta(days=horizon))
        if tgt is None:
            tgt = pd.NaT
        
        max_prob = float(np.max(proba))
        pred_class = int(np.argmax(proba))
        
        if max_prob >= confidence_threshold:
            action = "SHORT" if pred_class == 0 else "BUY" if pred_class == 2 else "HOLD"
        else:
            action = "HOLD"
        
        predictions.append({
            "Date": signal_date.strftime("%Y-%m-%d"),
            "Ticker": tkr,
            "Adj Close": float(test["Adj Close"].iloc[0]),
            "Target_Date": tgt.strftime("%Y-%m-%d") if pd.notna(tgt) else None,
            "Down": float(proba[0]),
            "Flat": float(proba[1]),
            "Up": float(proba[2]),
            "Action": action
        })
        
        # Run backtest
        y_true, y_pred, proba_arr, metrics = backtest_single_ticker(tkr, backtest_start_date)
        if metrics:
            backtest_results[tkr] = metrics
    
    predictions_df = pd.DataFrame(predictions)
    
    # Get latest economic data
    latest_economic = macro.iloc[-1].to_dict()
    # Convert date to string for JSON serialization
    if "Date" in latest_economic:
        if hasattr(latest_economic["Date"], 'strftime'):
            latest_economic["Date"] = latest_economic["Date"].strftime("%Y-%m-%d")
        else:
            latest_economic["Date"] = str(latest_economic["Date"])
    
    # Get market data
    market_data_dict = {}
    for market_tkr in market_tickers:
        market_df = stock_data[stock_data["Ticker"] == market_tkr].copy()
        if not market_df.empty:
            dates_list = market_df["Date"].tolist()
            if hasattr(dates_list[0], 'strftime'):
                dates_list = [d.strftime("%Y-%m-%d") if hasattr(d, 'strftime') else str(d) for d in dates_list]
            market_data_dict[market_tkr] = {
                "dates": dates_list,
                "prices": market_df["Adj Close"].tolist() if market_tkr != "^VIX" else market_df["Close"].tolist()
            }
    
    # Convert stock data dates to strings
    stock_data_result = df[df["Ticker"].isin(target_tickers)][["Ticker", "Date", "Adj Close", "Volume"]].copy()
    if len(stock_data_result) > 0:
        stock_data_result["Date"] = pd.to_datetime(stock_data_result["Date"])
        stock_data_result["Date"] = stock_data_result["Date"].dt.strftime("%Y-%m-%d")
    
    # Model run date (when this run completed) for display
    model_run_date = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    return {
        "predictions": predictions_df,
        "backtest_results": backtest_results,
        "economic_data": latest_economic,
        "market_data": market_data_dict,
        "stock_data": stock_data_result,
        "model_run_date": model_run_date
    }


if __name__ == "__main__":
    # Example usage
    target_tickers = ["NVDA", "ORCL", "THAR", "SOFI", "RR", "RGTI"]
    fred_series_map = {
        "FEDFUNDS": "Interest_Rate",
        "CPIAUCSL": "Inflation_Rate",
        "UNRATE": "Unemployment_Rate"
    }
    market_tickers = ["^GSPC", "^VIX"]
    
    results = run_model(
        target_tickers=target_tickers,
        fred_series_map=fred_series_map,
        market_tickers=market_tickers,
        backtest_start_date="2025-01-01",
        horizon=15,
        confidence_threshold=0.6
    )
    
    print("\n=== Predictions ===")
    print(results["predictions"])

