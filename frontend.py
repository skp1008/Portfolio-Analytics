"""
Streamlit Frontend for Stock Analysis Dashboard
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import json
import os


def load_cached_results():
    """Load cached model results."""
    cache_file = "cached_results.json"
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r') as f:
                return json.load(f)
        except:
            return None
    return None


def get_stock_data_for_period(stock_data_df, ticker, period_start, period_end):
    """Get stock data for a specific period."""
    ticker_data = stock_data_df[stock_data_df["Ticker"] == ticker].copy()
    ticker_data["Date"] = pd.to_datetime(ticker_data["Date"])
    
    mask = (ticker_data["Date"] >= pd.to_datetime(period_start)) & (ticker_data["Date"] <= pd.to_datetime(period_end))
    period_data = ticker_data[mask].copy()
    
    if len(period_data) == 0:
        return None, None
    
    period_data = period_data.sort_values("Date")
    
    if len(period_data) > 0:
        start_price = period_data["Adj Close"].iloc[0]
        end_price = period_data["Adj Close"].iloc[-1]
        pct_change = ((end_price / start_price) - 1) * 100
    else:
        pct_change = 0
    
    return period_data, pct_change


def calculate_stock_stats(stock_data_df, ticker, current_date):
    """Calculate key stock statistics."""
    ticker_data = stock_data_df[stock_data_df["Ticker"] == ticker].copy()
    ticker_data["Date"] = pd.to_datetime(ticker_data["Date"])
    ticker_data = ticker_data.sort_values("Date")
    
    current_idx = ticker_data[ticker_data["Date"] <= pd.to_datetime(current_date)]
    if len(current_idx) == 0:
        return {}
    
    current_price = current_idx["Adj Close"].iloc[-1]
    
    # 1 Year return
    one_year_ago = pd.to_datetime(current_date) - timedelta(days=365)
    one_year_data = ticker_data[ticker_data["Date"] >= one_year_ago]
    if len(one_year_data) > 0:
        one_year_return = ((current_price / one_year_data["Adj Close"].iloc[0]) - 1) * 100
    else:
        one_year_return = None
    
    # Volatility (annualized)
    returns = ticker_data["Adj Close"].pct_change().dropna()
    if len(returns) > 0:
        volatility = returns.std() * np.sqrt(252) * 100  # Annualized
    else:
        volatility = None
    
    # 52-week high/low
    fifty_two_weeks = ticker_data[ticker_data["Date"] >= one_year_ago]
    if len(fifty_two_weeks) > 0:
        week_high = fifty_two_weeks["Adj Close"].max()
        week_low = fifty_two_weeks["Adj Close"].min()
    else:
        week_high = None
        week_low = None
    
    # Current vs 52-week
    if week_high and week_low:
        vs_high = ((current_price / week_high) - 1) * 100
        vs_low = ((current_price / week_low) - 1) * 100
    else:
        vs_high = None
        vs_low = None
    
    return {
        "current_price": current_price,
        "one_year_return": one_year_return,
        "volatility": volatility,
        "week_high": week_high,
        "week_low": week_low,
        "vs_52w_high": vs_high,
        "vs_52w_low": vs_low
    }


def get_company_name(ticker):
    """Get company name for ticker (placeholder - can be enhanced with API)."""
    names = {
        "NVDA": "NVIDIA Corporation",
        "ORCL": "Oracle Corporation",
        "THAR": "Tharimmune Inc.",
        "SOFI": "SoFi Technologies Inc.",
        "RR": "Rolls-Royce Holdings plc",
        "RGTI": "Rigetti Computing Inc."
    }
    return names.get(ticker, ticker)


def render_stock_summary_bar(ticker, current_price, pct_change, dollar_change, current_date):
    """Render professional stock summary header bar."""
    company_name = get_company_name(ticker)
    change_color = "#10b981" if pct_change >= 0 else "#ef4444"
    change_sign = "+" if pct_change >= 0 else ""
    
    # Determine market status (simplified - assumes market is open if data is recent)
    last_update = pd.to_datetime(current_date)
    now = datetime.now()
    hours_diff = (now - last_update).total_seconds() / 3600
    market_status = "Open" if hours_diff < 24 else "Closed"
    
    st.markdown(f"""
    <div style="
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        border: 1px solid #334155;
        border-radius: 8px;
        padding: 1.5rem 2rem 1rem 2rem;
        margin-bottom: 0.5rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
    ">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 2rem;">
            <div style="flex: 1; min-width: 200px; display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <div style="font-family: 'Inter', 'SF Pro Display', -apple-system, sans-serif; font-size: 0.875rem; color: #94a3b8; margin-bottom: 0.5rem;">
                        {company_name}
                    </div>
                    <div style="font-family: 'Inter', 'SF Pro Display', -apple-system, sans-serif; font-size: 2rem; font-weight: 700; color: #f1f5f9; letter-spacing: -0.02em;">
                        {ticker}
                    </div>
                </div>
                <div style="text-align: right;">
                    <div style="font-family: 'Inter', 'SF Pro Display', -apple-system, sans-serif; font-size: 2.5rem; font-weight: 700; color: #f1f5f9; margin-bottom: 0.5rem;">
                        ${current_price:.2f}
                    </div>
                    <div style="font-family: 'Inter', 'SF Pro Display', -apple-system, sans-serif; font-size: 1.125rem; font-weight: 600; color: {change_color}; margin-bottom: 0.5rem;">
                        {change_sign}{dollar_change:.2f} ({change_sign}{pct_change:.2f}%)
                    </div>
                    <div style="font-family: 'Inter', 'SF Pro Display', -apple-system, sans-serif; font-size: 0.75rem; color: #64748b; margin-bottom: 0.25rem;">
                        Market: <span style="color: #10b981;">{market_status}</span>
                    </div>
                    <div style="font-family: 'Inter', 'SF Pro Display', -apple-system, sans-serif; font-size: 0.75rem; color: #64748b;">
                        Updated: {last_update.strftime('%Y-%m-%d %H:%M')}
                    </div>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)


def main():
    st.set_page_config(
        page_title="Stock Analysis Dashboard",
        page_icon=None,
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # Custom CSS for blue-black theme
    st.markdown("""
        <style>
        .main {
            background-color: #0a0e27;
            color: #e0e0e0;
        }
        .stButton>button {
            background-color: #1e3a8a;
            color: white;
            border-radius: 5px;
            border: none;
            padding: 0.5rem 1rem;
        }
        .stButton>button:hover {
            background-color: #3b82f6;
        }
        .metric-card {
            background-color: #1e293b;
            padding: 1rem;
            border-radius: 10px;
            border: 1px solid #334155;
        }
        
        /* Stock selection buttons styling */
        button[key^="stock_btn_"] {
            background-color: #1e293b !important;
            border: 1px solid #334155 !important;
            color: #94a3b8 !important;
            font-weight: 500 !important;
            border-radius: 8px !important;
            padding: 0.75rem 1.25rem !important;
            transition: all 0.2s ease !important;
        }
        
        button[key^="stock_btn_"]:hover {
            background-color: #334155 !important;
            border-color: #475569 !important;
            color: #f1f5f9 !important;
        }
        
        button[key^="stock_btn_"][data-baseweb="button"][kind="primary"] {
            background-color: #1e40af !important;
            border-color: #3b82f6 !important;
            color: #f1f5f9 !important;
        }
        
        button[key^="stock_btn_"][data-baseweb="button"][kind="primary"]:hover {
            background-color: #2563eb !important;
        }
        
        /* Stock icon circles */
        .stock-icon-circle {
            width: 64px;
            height: 64px;
            border-radius: 50%;
            background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            font-size: 1.75rem;
            color: white;
            margin: 0 auto 0.75rem auto;
            box-shadow: 0 2px 8px rgba(59, 130, 246, 0.3);
        }
        
        .stock-icon-circle.selected {
            background: linear-gradient(135deg, #60a5fa 0%, #3b82f6 100%);
            box-shadow: 0 4px 12px rgba(59, 130, 246, 0.5);
        }
        
        .stock-selection-title {
            font-family: 'Inter', 'SF Pro Display', -apple-system, sans-serif;
            font-size: 1rem;
            font-weight: 600;
            color: #94a3b8;
            margin-bottom: 1rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        
        /* Period buttons - closer together */
        button[key^="period_btn_"] {
            padding: 0.5rem 0.75rem !important;
            font-size: 0.875rem !important;
        }
        
        div[data-testid="column"]:has(button[key^="period_btn_"]) {
            padding-left: 0.25rem !important;
            padding-right: 0.25rem !important;
        }
        
        /* Economic Conditions Cards */
        .economic-metrics-container {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 1.5rem;
            margin-top: 1rem;
        }
        
        .economic-metric-card {
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
            border: 1px solid #334155;
            border-radius: 8px;
            padding: 1.5rem;
            text-align: center;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        
        .economic-metric-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 12px -1px rgba(0, 0, 0, 0.4);
        }
        
        .economic-metric-label {
            font-family: 'Inter', 'SF Pro Display', -apple-system, sans-serif;
            font-size: 0.75rem;
            font-weight: 500;
            color: #94a3b8;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 0.75rem;
        }
        
        .economic-metric-value {
            font-family: 'Inter', 'SF Pro Display', -apple-system, sans-serif;
            font-size: 2rem;
            font-weight: 700;
            color: #f1f5f9;
            letter-spacing: -0.02em;
        }
        
        /* Model Variables Card */
        .model-variables-card {
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
            border: 1px solid #334155;
            border-radius: 8px;
            padding: 2rem;
            margin-bottom: 2rem;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
        }
        
        .model-variables-title {
            font-family: 'Inter', 'SF Pro Display', -apple-system, sans-serif;
            font-size: 1.5rem;
            font-weight: 700;
            color: #f1f5f9;
            margin-bottom: 0.5rem;
            letter-spacing: -0.02em;
        }
        
        .model-variables-subtitle {
            font-family: 'Inter', 'SF Pro Display', -apple-system, sans-serif;
            font-size: 0.875rem;
            font-weight: 400;
            color: #94a3b8;
            margin-bottom: 1.5rem;
            line-height: 1.5;
        }
        
        .variable-item {
            padding: 1rem 0;
            border-bottom: 1px solid rgba(51, 65, 85, 0.5);
        }
        
        .variable-item:last-child {
            border-bottom: none;
        }
        
        .variable-label {
            font-family: 'Inter', 'SF Pro Display', -apple-system, sans-serif;
            font-size: 0.9375rem;
            font-weight: 600;
            color: #f1f5f9;
            margin-bottom: 0.375rem;
        }
        
        .variable-description {
            font-family: 'Inter', 'SF Pro Display', -apple-system, sans-serif;
            font-size: 0.875rem;
            font-weight: 400;
            color: #94a3b8;
            line-height: 1.6;
        }
        
        .variable-highlight {
            color: #cbd5e1;
            font-weight: 500;
        }
        
        /* Prediction Analysis Card */
        .prediction-card {
            background: transparent;
            border: none;
            border-radius: 0;
            padding: 0;
            margin: 0;
            box-shadow: none;
        }
        
        .signal-badge {
            display: flex;
            flex-direction: column;
            padding: 2.5rem 2.5rem 2rem 2.5rem;
            border-radius: 8px;
            margin: 0 0 2rem 0;
            width: 100%;
        }
        
        .signal-badge.SHORT {
            background: rgba(239, 68, 68, 0.08);
            border-left: 5px solid #dc2626;
        }
        
        .signal-badge.BUY {
            background: rgba(16, 185, 129, 0.08);
            border-left: 5px solid #10b981;
        }
        
        .signal-badge.HOLD {
            background: rgba(100, 116, 139, 0.08);
            border-left: 5px solid #64748b;
        }
        
        .signal-text {
            font-family: 'Inter', 'SF Pro Display', -apple-system, sans-serif;
            font-size: 3.5rem;
            font-weight: 800;
            color: #f1f5f9;
            letter-spacing: -0.03em;
            line-height: 1;
            margin-bottom: 0.75rem;
        }
        
        .signal-badge.SHORT .signal-text {
            color: #dc2626;
        }
        
        .signal-badge.BUY .signal-text {
            color: #10b981;
        }
        
        .signal-badge.HOLD .signal-text {
            color: #64748b;
        }
        
        .signal-subtitle {
            font-family: 'Inter', 'SF Pro Display', -apple-system, sans-serif;
            font-size: 1rem;
            font-weight: 500;
            color: #cbd5e1;
            letter-spacing: -0.01em;
        }
        
        .probability-row {
            background: #0f172a;
            border: 1px solid #1e293b;
            border-radius: 6px;
            padding: 0.875rem 1rem;
            margin-bottom: 0.625rem;
            transition: all 0.2s ease;
        }
        
        .probability-row:hover {
            background: #1e293b;
            border-color: #334155;
            transform: translateX(2px);
        }
        
        .probability-label {
            font-family: 'Inter', 'SF Pro Display', -apple-system, sans-serif;
            font-size: 0.6875rem;
            color: #64748b;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            margin-bottom: 0.375rem;
            font-weight: 500;
        }
        
        .probability-value {
            font-family: 'Inter', 'SF Pro Display', -apple-system, sans-serif;
            font-size: 1.25rem;
            font-weight: 600;
            color: #f1f5f9;
            margin-bottom: 0.5rem;
        }
        
        .probability-bar {
            height: 3px;
            border-radius: 2px;
            background: rgba(148, 163, 184, 0.08);
            overflow: hidden;
        }
        
        .probability-bar-fill {
            height: 100%;
            border-radius: 2px;
            transition: width 0.8s cubic-bezier(0.4, 0, 0.2, 1);
        }
        
        .probability-bar-fill.rise {
            background: #10b981;
        }
        
        .probability-bar-fill.neutral {
            background: #64748b;
        }
        
        .probability-bar-fill.fall {
            background: #dc2626;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Load cached results
    results = load_cached_results()
    
    if results is None:
        st.error("No cached results found. Please run the model first.")
        st.info("Run: python launcher.py")
        return
    
    # Extract data
    predictions_df = pd.DataFrame(results.get("predictions", []))
    backtest_results = results.get("backtest_results", {})
    economic_data = results.get("economic_data", {})
    market_data = results.get("market_data", {})
    stock_data_df = pd.DataFrame(results.get("stock_data", []))
    model_run_date = results.get("model_run_date")
    
    if predictions_df.empty:
        st.error("No predictions available.")
        return
    
    # Initialize session state for selected ticker
    if 'selected_ticker' not in st.session_state:
        available_tickers = sorted(predictions_df["Ticker"].unique().tolist())
        st.session_state.selected_ticker = available_tickers[0] if available_tickers else None
    
    available_tickers = sorted(predictions_df["Ticker"].unique().tolist())
    
    # Main Title + Model Run Date
    model_run_date_str = f'Model run: {model_run_date}' if model_run_date else ''
    st.markdown(f"""
    <div style="text-align: center; margin: 3rem 0 4rem 0;">
        <h1 style="font-family: 'Inter', 'SF Pro Display', -apple-system, sans-serif; font-size: 3.5rem; font-weight: 800; color: #f1f5f9; letter-spacing: -0.03em; margin-bottom: 0.5rem;">Stock Analysis Platform</h1>
        <p style="font-family: 'Inter', 'SF Pro Display', -apple-system, sans-serif; font-size: 0.875rem; color: #64748b; margin-top: 0.5rem;">{model_run_date_str}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Stock selection section with centered title
    st.markdown('<div style="text-align: center; font-family: \'Inter\', \'SF Pro Display\', -apple-system, sans-serif; font-size: 1.25rem; font-weight: 600; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 2rem; margin-top: 2rem;">Select Stock</div>', unsafe_allow_html=True)
    
    # Create stock selection buttons with circular icons above
    num_cols = len(available_tickers)
    if num_cols > 0:
        cols = st.columns(num_cols)
        
        for idx, ticker in enumerate(available_tickers):
            with cols[idx]:
                is_selected = st.session_state.selected_ticker == ticker
                icon = ticker[0]  # First letter as icon
                icon_class = "selected" if is_selected else ""
                
                # Circular icon above button
                st.markdown(
                    f'<div class="stock-icon-circle {icon_class}">{icon}</div>',
                    unsafe_allow_html=True
                )
                
                # Button without icon prefix
                if st.button(
                    ticker,
                    key=f"stock_btn_{ticker}",
                    type="primary" if is_selected else "secondary",
                    use_container_width=True
                ):
                    st.session_state.selected_ticker = ticker
                    st.rerun()
    
    selected_ticker = st.session_state.selected_ticker
    
    # Get prediction for selected ticker
    ticker_pred = predictions_df[predictions_df["Ticker"] == selected_ticker]
    
    if ticker_pred.empty:
        st.error(f"No prediction available for {selected_ticker}")
        return
    
    pred_row = ticker_pred.iloc[0]
    current_date = pred_row["Date"]
    current_price = pred_row["Adj Close"]
    action = pred_row["Action"]
    down_prob = pred_row["Down"]
    flat_prob = pred_row["Flat"]
    up_prob = pred_row["Up"]
    
    # Calculate daily change for summary bar
    ticker_data = stock_data_df[stock_data_df["Ticker"] == selected_ticker].copy()
    ticker_data["Date"] = pd.to_datetime(ticker_data["Date"])
    ticker_data = ticker_data.sort_values("Date")
    
    current_idx = ticker_data[ticker_data["Date"] <= pd.to_datetime(current_date)]
    if len(current_idx) >= 2:
        prev_price = current_idx["Adj Close"].iloc[-2]
        daily_change_pct = ((current_price / prev_price) - 1) * 100
        daily_change_dollar = current_price - prev_price
    else:
        daily_change_pct = 0
        daily_change_dollar = 0
    
    # Stock Summary Bar
    render_stock_summary_bar(selected_ticker, current_price, daily_change_pct, daily_change_dollar, current_date)
    
    # Period buttons inside summary bar area
    periods = {
        "1 Day": 1,
        "15 Days": 15,
        "1 Month": 30,
        "5 Years": 1825,
        "Max": None
    }
    
    # Initialize session state for selected period
    if 'selected_period_label' not in st.session_state:
        st.session_state.selected_period_label = "Max"
    
    # Period buttons - grouped on left, smaller
    st.markdown('<div style="margin-bottom: 1.5rem;">', unsafe_allow_html=True)
    
    # Create period buttons grouped on left with smaller size
    col1, col2, col3, col4, col5, spacer = st.columns([0.6, 0.6, 0.6, 0.6, 0.6, 4])
    
    period_label = st.session_state.selected_period_label
    
    with col1:
        if st.button("1 Day", key="period_btn_1d", type="primary" if period_label == "1 Day" else "secondary"):
            st.session_state.selected_period_label = "1 Day"
            st.rerun()
    with col2:
        if st.button("15 Days", key="period_btn_15d", type="primary" if period_label == "15 Days" else "secondary"):
            st.session_state.selected_period_label = "15 Days"
            st.rerun()
    with col3:
        if st.button("1 Month", key="period_btn_1m", type="primary" if period_label == "1 Month" else "secondary"):
            st.session_state.selected_period_label = "1 Month"
            st.rerun()
    with col4:
        if st.button("5 Years", key="period_btn_5y", type="primary" if period_label == "5 Years" else "secondary"):
            st.session_state.selected_period_label = "5 Years"
            st.rerun()
    with col5:
        if st.button("Max", key="period_btn_max", type="primary" if period_label == "Max" else "secondary"):
            st.session_state.selected_period_label = "Max"
            st.rerun()
    
    # Get selected period value
    period_label = st.session_state.selected_period_label
    selected_period = periods.get(period_label, None)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Movement History Section - centered header before buttons
    st.markdown('<div style="text-align: center; font-family: \'Inter\', \'SF Pro Display\', -apple-system, sans-serif; font-size: 1.25rem; font-weight: 600; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 1rem; margin-top: 2rem;">Price Movement</div>', unsafe_allow_html=True)
    
    # Calculate period
    end_date = pd.to_datetime(current_date)
    if selected_period is None:
        start_date = stock_data_df["Date"].min()
    else:
        start_date = end_date - timedelta(days=selected_period)
    
    period_data, pct_change = get_stock_data_for_period(stock_data_df, selected_ticker, start_date, end_date)
    
    if period_data is not None and len(period_data) > 0:
        # Determine line color based on net change
        line_color = '#10b981' if pct_change >= 0 else '#ef4444'
        
        # Get previous close for reference line
        period_data_sorted = period_data.sort_values("Date").copy()
        # Ensure Date column is datetime
        period_data_sorted["Date"] = pd.to_datetime(period_data_sorted["Date"])
        previous_close = period_data_sorted["Adj Close"].iloc[0]
        latest_price = period_data_sorted["Adj Close"].iloc[-1]
        latest_date = period_data_sorted["Date"].iloc[-1]
        
        # Calculate daily change for tooltip (change from previous day)
        if len(period_data_sorted) >= 2:
            prev_price = period_data_sorted["Adj Close"].iloc[-2]
            daily_change = latest_price - prev_price
            daily_change_pct = ((latest_price / prev_price) - 1) * 100
        else:
            daily_change = latest_price - previous_close
            daily_change_pct = pct_change if pct_change is not None else 0
        
        # Calculate y-axis range for shorter periods to show movement better
        yaxis_range = None
        if selected_period in [1, 15, 30]:  # 1 Day, 15 Days, 1 Month
            price_min = period_data_sorted["Adj Close"].min()
            price_max = period_data_sorted["Adj Close"].max()
            price_range = price_max - price_min
            # Add 5% padding on each side, but ensure minimum range for very flat lines
            padding = max(price_range * 0.05, price_max * 0.01)  # At least 1% of max price
            yaxis_range = [price_min - padding, price_max + padding]
        
        fig = go.Figure()
        
        # Add area gradient under the line
        fig.add_trace(go.Scatter(
            x=period_data_sorted["Date"],
            y=period_data_sorted["Adj Close"],
            mode='lines',
            name=selected_ticker,
            line=dict(color=line_color, width=2.5),
            fill='tozeroy',
            fillcolor=f'rgba({16 if pct_change >= 0 else 239}, {185 if pct_change >= 0 else 68}, {129 if pct_change >= 0 else 68}, 0.1)',
            hovertemplate='<b>%{fullData.name}</b><br>' +
                         'Date: %{x|%Y-%m-%d %H:%M}<br>' +
                         'Price: $%{y:.2f}<br>' +
                         '<extra></extra>'
        ))
        
        # Highlight latest data point with a dot
        latest_date_formatted = pd.to_datetime(latest_date).strftime("%Y-%m-%d %H:%M") if isinstance(latest_date, str) else latest_date.strftime("%Y-%m-%d %H:%M")
        daily_change_str = f'+${daily_change:.2f} (+{daily_change_pct:.2f}%)' if daily_change >= 0 else f'${daily_change:.2f} ({daily_change_pct:.2f}%)'
        
        fig.add_trace(go.Scatter(
            x=[latest_date],
            y=[latest_price],
            mode='markers',
            name='Latest',
            marker=dict(
                size=10,
                color=line_color,
                line=dict(width=2, color='#0f172a')
            ),
            hovertemplate=f'<b>Latest</b><br>' +
                         f'Date: {latest_date_formatted}<br>' +
                         f'Price: ${latest_price:.2f}<br>' +
                         f'Daily Change: {daily_change_str}<br>' +
                         '<extra></extra>',
            showlegend=False
        ))
        
        fig.update_layout(
            xaxis=dict(
                title="",
                showgrid=False,  # Remove vertical gridlines
                showline=True,
                linecolor='#334155',
                linewidth=1,
                tickfont=dict(color='#94a3b8', size=11, family='Inter, SF Pro Display, -apple-system, sans-serif'),
                type='date',  # Explicitly set as date axis
                tickformat='%H:%M' if selected_period == 1 else '%Y-%m-%d',
                rangeslider=dict(visible=False),
                showspikes=True,
                spikecolor='#64748b',
                spikethickness=1,
                spikedash='dot',
                spikemode='toaxis'
            ),
            yaxis=dict(
                title=dict(
                    text="Price ($)",
                    font=dict(color='#94a3b8', size=12, family='Inter, SF Pro Display, -apple-system, sans-serif')
                ),
                showgrid=True,
                gridcolor='rgba(148, 163, 184, 0.1)',  # Very subtle gridlines
                gridwidth=1,
                showline=True,
                linecolor='#334155',
                linewidth=1,
                tickfont=dict(color='#94a3b8', size=11, family='Inter, SF Pro Display, -apple-system, sans-serif'),
                dtick=None,  # Let plotly auto-space
                nticks=8,  # More ticks for better spacing
                range=yaxis_range if yaxis_range else None,  # Set tighter range for 1-day charts
                showspikes=False  # Disable horizontal spikes, only show vertical
            ),
            template='plotly_dark',
            height=550,  # Increased height
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            hovermode='x unified',
            hoverlabel=dict(
                bgcolor='rgba(15, 23, 42, 0.95)',
                bordercolor='#334155',
                font_size=12,
                font_family='Inter, SF Pro Display, -apple-system, sans-serif'
            ),
            margin=dict(l=60, r=20, t=60, b=40),
            legend=dict(
                orientation='h',
                yanchor='bottom',
                y=1.02,
                xanchor='right',
                x=1,
                font=dict(color='#94a3b8', size=11),
                bgcolor='rgba(0,0,0,0)'
            ),
            transition=dict(
                duration=500,
                easing='cubic-in-out'
            )
        )
        
        st.plotly_chart(fig, use_container_width=True, config={
            'displayModeBar': True,
            'displaylogo': False,
            'modeBarButtonsToRemove': ['pan2d', 'lasso2d'],
            'toImageButtonOptions': {
                'format': 'png',
                'filename': f'{selected_ticker}_chart_{period_label}',
                'height': 550,
                'width': 1200,
                'scale': 2
            }
        })
        
        # Show % change
        if pct_change is not None:
            color = "#10b981" if pct_change >= 0 else "#ef4444"
            st.markdown(f"<p style='text-align: right; color: {color}; font-size: 1.2rem;'><b>Change: {pct_change:+.2f}%</b></p>", unsafe_allow_html=True)
    
    # Prediction Analysis Section
    st.markdown('<div style="text-align: center; font-family: \'Inter\', \'SF Pro Display\', -apple-system, sans-serif; font-size: 1.25rem; font-weight: 600; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 2rem; margin-top: 3rem;">Prediction Analysis</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="prediction-card">', unsafe_allow_html=True)
    
    # Determine dominant prediction and confidence
    max_prob = max(up_prob, flat_prob, down_prob)
    dominant_label = "Rise" if up_prob == max_prob else ("Fall" if down_prob == max_prob else "Neutral")
    confidence = max_prob * 100
    
    # Map action to display signal
    signal_map = {
        "BUY": {"label": "LONG", "class": "BUY", "subtitle": f"Model Confidence: {confidence:.1f}%"},
        "SHORT": {"label": "SHORT", "class": "SHORT", "subtitle": f"Model Confidence: {confidence:.1f}%"},
        "HOLD": {"label": "HOLD", "class": "HOLD", "subtitle": f"Model Confidence: {confidence:.1f}%"}
    }
    
    signal_info = signal_map.get(action, signal_map["HOLD"])
    
    # Primary Signal - Full width, most prominent
    st.markdown(f'''
    <div class="signal-badge {signal_info['class']}">
        <div class="signal-text">{signal_info['label']}</div>
        <div class="signal-subtitle">{signal_info['subtitle']}</div>
    </div>
    ''', unsafe_allow_html=True)
    
    # Two column layout below signal
    col1, col2 = st.columns([1, 1.2])
    
    with col1:
        # Regular pie chart (reverted to previous version)
        fig_pie = go.Figure(data=[go.Pie(
            labels=['Rise', 'Neutral', 'Fall'],
            values=[up_prob * 100, flat_prob * 100, down_prob * 100],
            marker=dict(colors=['#10b981', '#64748b', '#dc2626']),
            textinfo='label+percent',
            hovertemplate='<b>%{label}</b><br>Probability: %{percent}<extra></extra>'
        )])
        fig_pie.update_layout(
            template="plotly_dark",
            height=400,
            margin=dict(l=0, r=0, t=0, b=0),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white', size=12),
            showlegend=True,
            legend=dict(
                orientation="v",
                yanchor="middle",
                y=0.5,
                xanchor="left",
                x=1.1,
                font=dict(color='#94a3b8', size=12)
            )
        )
        st.plotly_chart(fig_pie, use_container_width=True, config={'displayModeBar': False})
    
    with col2:
        st.markdown('<h3 style="font-family: \'Inter\', \'SF Pro Display\', -apple-system, sans-serif; font-size: 0.75rem; font-weight: 600; color: #64748b; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 1.25rem; margin-top: 0.5rem;">Probabilities</h3>', unsafe_allow_html=True)
        
        # Probability rows with progress bars
        probabilities = [
            {"label": "Rise", "value": up_prob * 100, "class": "rise"},
            {"label": "Neutral", "value": flat_prob * 100, "class": "neutral"},
            {"label": "Fall", "value": down_prob * 100, "class": "fall"}
        ]
        
        for prob in probabilities:
            color_map = {
                "rise": "#10b981",
                "neutral": "#64748b",
                "fall": "#dc2626"
            }
            prob_color = color_map[prob["class"]]
            
            st.markdown(f'''
            <div class="probability-row">
                <div class="probability-label">
                    <span>{prob["label"]}</span>
                </div>
                <div class="probability-value" style="color: {prob_color};">
                    {prob["value"]:.1f}%
                </div>
                <div class="probability-bar">
                    <div class="probability-bar-fill {prob['class']}" style="width: {prob['value']}%;"></div>
                </div>
            </div>
            ''', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Market Performance Section
    st.markdown('<div style="text-align: center; font-family: \'Inter\', \'SF Pro Display\', -apple-system, sans-serif; font-size: 1.25rem; font-weight: 600; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 2rem; margin-top: 3rem;">Market Performance</div>', unsafe_allow_html=True)
    
    if "^GSPC" in market_data:
        spx_data = market_data["^GSPC"]
        spx_dates = pd.to_datetime(spx_data["dates"])
        spx_prices = spx_data["prices"]
        
        # Calculate change for S&P 500
        if len(spx_prices) > 1:
            spx_start = spx_prices[0]
            spx_end = spx_prices[-1]
            spx_change = ((spx_end / spx_start) - 1) * 100
            spx_line_color = '#10b981' if spx_change >= 0 else '#ef4444'
        else:
            spx_change = 0
            spx_line_color = '#10b981'
        
        fig_spx = go.Figure()
        
        # Add area gradient under the line
        fig_spx.add_trace(go.Scatter(
            x=spx_dates,
            y=spx_prices,
            mode='lines',
            name='S&P 500',
            line=dict(color=spx_line_color, width=2.5),
            fill='tozeroy',
            fillcolor=f'rgba({16 if spx_change >= 0 else 239}, {185 if spx_change >= 0 else 68}, {129 if spx_change >= 0 else 68}, 0.1)',
            hovertemplate='<b>S&P 500</b><br>Date: %{x|%Y-%m-%d}<br>Price: %{y:.2f}<extra></extra>'
        ))
        
        # Highlight latest data point
        if len(spx_prices) > 0:
            latest_spx_date = spx_dates.iloc[-1] if hasattr(spx_dates, 'iloc') else spx_dates[-1]
            latest_spx_price = spx_prices[-1]
            
            fig_spx.add_trace(go.Scatter(
                x=[latest_spx_date],
                y=[latest_spx_price],
                mode='markers',
                name='Latest',
                marker=dict(
                    size=10,
                    color=spx_line_color,
                    line=dict(width=2, color='#0f172a')
                ),
                hovertemplate=f'<b>Latest</b><br>Date: {latest_spx_date.strftime("%Y-%m-%d") if hasattr(latest_spx_date, "strftime") else latest_spx_date}<br>Price: {latest_spx_price:.2f}<extra></extra>',
                showlegend=False
            ))
        
        fig_spx.update_layout(
            title=dict(
                text="S&P 500 Performance",
                font=dict(size=18, color='#f1f5f9', family='Inter, SF Pro Display, -apple-system, sans-serif')
            ),
            xaxis=dict(
                title="",
                showgrid=False,
                showline=True,
                linecolor='#334155',
                linewidth=1,
                tickfont=dict(color='#94a3b8', size=11, family='Inter, SF Pro Display, -apple-system, sans-serif'),
                type='date',
                tickformat='%Y-%m-%d',
                rangeslider=dict(visible=False),
                showspikes=True,
                spikecolor='#64748b',
                spikethickness=1,
                spikedash='dot',
                spikemode='toaxis'
            ),
            yaxis=dict(
                title=dict(
                    text="Price",
                    font=dict(color='#94a3b8', size=12, family='Inter, SF Pro Display, -apple-system, sans-serif')
                ),
                showgrid=True,
                gridcolor='rgba(148, 163, 184, 0.1)',
                gridwidth=1,
                showline=True,
                linecolor='#334155',
                linewidth=1,
                tickfont=dict(color='#94a3b8', size=11, family='Inter, SF Pro Display, -apple-system, sans-serif'),
                dtick=None,
                nticks=8,
                showspikes=False
            ),
            template='plotly_dark',
            height=550,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            hovermode='x unified',
            hoverlabel=dict(
                bgcolor='rgba(15, 23, 42, 0.95)',
                bordercolor='#334155',
                font_size=12,
                font_family='Inter, SF Pro Display, -apple-system, sans-serif'
            ),
            margin=dict(l=60, r=20, t=80, b=40),
            legend=dict(
                orientation='h',
                yanchor='bottom',
                y=1.02,
                xanchor='right',
                x=1,
                font=dict(color='#94a3b8', size=11),
                bgcolor='rgba(0,0,0,0)'
            ),
            transition=dict(
                duration=500,
                easing='cubic-in-out'
            )
        )
        st.plotly_chart(fig_spx, use_container_width=True, config={
            'displayModeBar': True,
            'displaylogo': False,
            'modeBarButtonsToRemove': ['pan2d', 'lasso2d']
        })
    
    # Backtest Statistics & Stock Info
    st.markdown('<div style="text-align: center; font-family: \'Inter\', \'SF Pro Display\', -apple-system, sans-serif; font-size: 1.25rem; font-weight: 600; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 2rem; margin-top: 3rem;">Backtest Statistics & Stock Information</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Backtest Results")
        if selected_ticker in backtest_results:
            bt = backtest_results[selected_ticker]
            st.metric("Accuracy", f"{bt.get('accuracy', 0)*100:.1f}%")
            st.metric("F1 Score (Macro)", f"{bt.get('f1_macro', 0):.3f}")
            st.metric("Log Loss", f"{bt.get('log_loss', 0):.3f}")
            st.metric("Number of Folds", f"{bt.get('n_folds', 0)}")
    
    with col2:
        st.subheader("Stock Statistics")
        stats = calculate_stock_stats(stock_data_df, selected_ticker, current_date)
        
        if stats.get("one_year_return") is not None:
            st.metric("1 Year Return", f"{stats['one_year_return']:.2f}%")
        
        if stats.get("volatility") is not None:
            st.metric("Volatility (Annualized)", f"{stats['volatility']:.2f}%")
        
        if stats.get("week_high") is not None:
            st.metric("52-Week High", f"${stats['week_high']:.2f}")
        
        if stats.get("week_low") is not None:
            st.metric("52-Week Low", f"${stats['week_low']:.2f}")
        
        if stats.get("vs_52w_high") is not None:
            color = "normal"
            st.metric("vs 52-Week High", f"{stats['vs_52w_high']:.2f}%")
    
    # Economic Conditions Section
    st.markdown('<div style="text-align: center; font-family: \'Inter\', \'SF Pro Display\', -apple-system, sans-serif; font-size: 1.25rem; font-weight: 600; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 2rem; margin-top: 3rem;">Economic Conditions</div>', unsafe_allow_html=True)
    
    if economic_data:
        unemployment = economic_data.get("Unemployment_Rate")
        interest = economic_data.get("Interest_Rate")
        inflation_yoy = economic_data.get("Inflation_YoY")
        inflation_raw = economic_data.get("Inflation_Rate") if inflation_yoy is None else None
        
        unemployment_str = f"{unemployment:.2f}%" if unemployment is not None else "N/A"
        interest_str = f"{interest:.2f}%" if interest is not None else "N/A"
        inflation_str = f"{inflation_yoy:.2f}%" if inflation_yoy is not None else (f"{inflation_raw:.2f}" if inflation_raw is not None else "N/A")
        inflation_label = "Inflation Rate (YoY)" if inflation_yoy is not None else "Inflation Rate (Index)"
        
        st.markdown(f"""
        <div class="economic-metrics-container">
            <div class="economic-metric-card">
                <div class="economic-metric-label">Unemployment Rate</div>
                <div class="economic-metric-value">{unemployment_str}</div>
            </div>
            <div class="economic-metric-card">
                <div class="economic-metric-label">Interest Rate</div>
                <div class="economic-metric-value">{interest_str}</div>
            </div>
            <div class="economic-metric-card">
                <div class="economic-metric-label">{inflation_label}</div>
                <div class="economic-metric-value">{inflation_str}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Add spacing between sections
    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # Model Variables Section (moved to bottom)
    st.markdown('<div style="text-align: center; font-family: \'Inter\', \'SF Pro Display\', -apple-system, sans-serif; font-size: 1.25rem; font-weight: 600; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 2rem; margin-top: 3rem;">Model Variables</div>', unsafe_allow_html=True)
    
    st.markdown("""
    The model uses the following key variables:
    - **1. Stock's Own History (AR1-like)**: Historical price movements, returns (1, 5, 15, 30 day), momentum, volatility, RSI, drawdown
    - **2. Overall Market Conditions**: S&P 500 (^GSPC) performance and volatility
    - **3. Industry Conditions**: Via ETFs (XLK, XLF, etc.) and sector performance
    - **4. Economic Variables**: Interest rates, inflation, unemployment rate
    """)


if __name__ == "__main__":
    main()
