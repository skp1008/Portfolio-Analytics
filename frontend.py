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
from urllib.request import urlopen
from PIL import Image


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


def get_stock_logo_url(ticker):
    """Get logo URL for a stock ticker."""
    # Mapping of common tickers to logo URLs (using finnhub or similar services)
    logo_mapping = {
        'AAPL': 'https://logo.clearbit.com/apple.com',
        'MSFT': 'https://logo.clearbit.com/microsoft.com',
        'GOOGL': 'https://logo.clearbit.com/google.com',
        'GOOG': 'https://logo.clearbit.com/google.com',
        'AMZN': 'https://logo.clearbit.com/amazon.com',
        'META': 'https://logo.clearbit.com/meta.com',
        'FB': 'https://logo.clearbit.com/meta.com',
        'TSLA': 'https://logo.clearbit.com/tesla.com',
        'NVDA': 'https://logo.clearbit.com/nvidia.com',
        'JPM': 'https://logo.clearbit.com/jpmorgan.com',
        'JNJ': 'https://logo.clearbit.com/jnj.com',
        'V': 'https://logo.clearbit.com/visa.com',
        'PG': 'https://logo.clearbit.com/pg.com',
        'UNH': 'https://logo.clearbit.com/unitedhealthgroup.com',
        'MA': 'https://logo.clearbit.com/mastercard.com',
        'HD': 'https://logo.clearbit.com/homedepot.com',
        'DIS': 'https://logo.clearbit.com/disney.com',
        'BAC': 'https://logo.clearbit.com/bankofamerica.com',
        'ADBE': 'https://logo.clearbit.com/adobe.com',
        'CMCSA': 'https://logo.clearbit.com/comcast.com',
        'XOM': 'https://logo.clearbit.com/exxonmobil.com',
        'VZ': 'https://logo.clearbit.com/verizon.com',
        'NFLX': 'https://logo.clearbit.com/netflix.com',
        'CRM': 'https://logo.clearbit.com/salesforce.com',
        'PYPL': 'https://logo.clearbit.com/paypal.com',
        'INTC': 'https://logo.clearbit.com/intel.com',
        'TMO': 'https://logo.clearbit.com/thermofisher.com',
        'COST': 'https://logo.clearbit.com/costco.com',
        'CSCO': 'https://logo.clearbit.com/cisco.com',
        'PEP': 'https://logo.clearbit.com/pepsico.com',
    }
    return logo_mapping.get(ticker, None)


def get_company_name(ticker):
    """Get full company name for a stock ticker."""
    company_mapping = {
        'AAPL': 'Apple Inc.',
        'MSFT': 'Microsoft Corporation',
        'GOOGL': 'Alphabet Inc.',
        'GOOG': 'Alphabet Inc.',
        'AMZN': 'Amazon.com Inc.',
        'META': 'Meta Platforms Inc.',
        'FB': 'Meta Platforms Inc.',
        'TSLA': 'Tesla Inc.',
        'NVDA': 'NVIDIA Corporation',
        'JPM': 'JPMorgan Chase & Co.',
        'JNJ': 'Johnson & Johnson',
        'V': 'Visa Inc.',
        'PG': 'The Procter & Gamble Company',
        'UNH': 'UnitedHealth Group Inc.',
        'MA': 'Mastercard Incorporated',
        'HD': 'The Home Depot Inc.',
        'DIS': 'The Walt Disney Company',
        'BAC': 'Bank of America Corp.',
        'ADBE': 'Adobe Inc.',
        'CMCSA': 'Comcast Corporation',
        'XOM': 'Exxon Mobil Corporation',
        'VZ': 'Verizon Communications Inc.',
        'NFLX': 'Netflix Inc.',
        'CRM': 'Salesforce Inc.',
        'PYPL': 'PayPal Holdings Inc.',
        'INTC': 'Intel Corporation',
        'TMO': 'Thermo Fisher Scientific Inc.',
        'COST': 'Costco Wholesale Corporation',
        'CSCO': 'Cisco Systems Inc.',
        'PEP': 'PepsiCo Inc.',
        'ORCL': 'Oracle Corporation',
        'RGTI': 'Rigetti Computing Inc.',
        'RR': 'Rolls-Royce Holdings Plc',
        'SOFI': 'SoFi Technologies Inc.',
        'THAR': 'Tharimmune Inc.',
    }
    return company_mapping.get(ticker, ticker)  # Return ticker if not found


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


def main():
    st.set_page_config(
        page_title="Stock Analysis Dashboard",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # Hide the sidebar completely
    st.markdown("""
        <style>
        section[data-testid="stSidebar"] {
            display: none;
        }
        </style>
    """, unsafe_allow_html=True)
    
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
        .prediction-card {
            background-color: rgba(30, 41, 59, 0.4);
            border: 1px solid rgba(139, 147, 167, 0.15);
            border-radius: 10px;
            padding: 1.5rem;
            margin-bottom: 1rem;
        }
        .prediction-title {
            font-size: 22px;
            font-weight: 600;
            color: #E6EAF2;
            margin-bottom: 1.5rem;
            letter-spacing: -0.02em;
        }
        .probability-row {
            display: flex;
            align-items: baseline;
            justify-content: space-between;
            padding: 0.75rem 0;
            border-bottom: 1px solid rgba(139, 147, 167, 0.1);
        }
        .probability-row:last-child {
            border-bottom: none;
        }
        .probability-label {
            font-size: 14px;
            font-weight: 500;
            color: #8B93A7;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        .probability-value {
            font-size: 32px;
            font-weight: 600;
            color: #E6EAF2;
            letter-spacing: -0.02em;
        }
        .signal-summary-card {
            background-color: rgba(30, 41, 59, 0.3);
            border: 1px solid rgba(139, 147, 167, 0.2);
            border-radius: 8px;
            padding: 1rem;
            margin-top: 0;
        }
        .signal-summary-label {
            font-size: 14px;
            font-weight: 500;
            color: #8B93A7;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 0.5rem;
        }
        .signal-summary-divider {
            height: 1px;
            background: rgba(139, 147, 167, 0.2);
            margin: 0.5rem 0;
        }
        .signal-summary-row {
            font-size: 15px;
            color: #E6EAF2;
            margin: 0.5rem 0;
            line-height: 1.6;
        }
        .signal-action {
            font-weight: 600;
        }
        .signal-buy {
            color: #38C172;
        }
        .signal-short {
            color: #E5533D;
        }
        .signal-hold {
            color: #6B7280;
        }
        .stock-card-button {
            background-color: #1e293b !important;
            border: 2px solid #334155 !important;
            border-radius: 12px !important;
            padding: 1.5rem 1rem !important;
            width: 100% !important;
            height: 140px !important;
            display: flex !important;
            flex-direction: column !important;
            justify-content: center !important;
            align-items: center !important;
            cursor: pointer !important;
            transition: all 0.3s ease !important;
            color: #e0e0e0 !important;
            font-weight: bold !important;
            text-align: center !important;
            box-shadow: none !important;
        }
        .stock-card-button:hover {
            border-color: #3b82f6 !important;
            transform: translateY(-2px) !important;
            box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3) !important;
            background-color: #1e293b !important;
        }
        .stock-card-button.selected {
            border-color: #3b82f6 !important;
            background-color: #1e3a8a !important;
            box-shadow: 0 4px 12px rgba(59, 130, 246, 0.5) !important;
        }
        .stock-logo-img {
            width: 60px !important;
            height: 60px !important;
            border-radius: 50% !important;
            object-fit: contain !important;
            margin-bottom: 0.5rem !important;
            background-color: white !important;
            padding: 5px !important;
        }
        .stock-card-container {
            display: flex;
            gap: 1rem;
            overflow-x: auto;
            padding: 1rem 0;
            margin-bottom: 2rem;
        }
        .stock-card-container::-webkit-scrollbar {
            height: 8px;
        }
        .stock-card-container::-webkit-scrollbar-track {
            background: #1e293b;
            border-radius: 4px;
        }
        .stock-card-container::-webkit-scrollbar-thumb {
            background: #3b82f6;
            border-radius: 4px;
        }
        .stock-card-wrapper {
            display: flex;
            flex-direction: column;
            align-items: center;
            text-align: center;
            width: 100%;
        }
        .period-button-wrapper {
            margin-bottom: 1rem;
        }
        .percentage-change-box {
            display: inline-block;
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
    
    if predictions_df.empty:
        st.error("No predictions available.")
        return
    
    # Initialize session state for stock selection
    if 'selected_ticker' not in st.session_state:
        st.session_state.selected_ticker = None
    
    available_tickers = sorted(predictions_df["Ticker"].unique().tolist())
    
    # Create stock cards section at the top
    st.markdown('<h2 style="text-align: center; font-size: 2.5rem; margin-bottom: 1rem;">Stock Options</h2>', unsafe_allow_html=True)
        
    # Create horizontal scrollable row of stock cards - use all tickers, they'll fit in one row
    num_cards = len(available_tickers)
    cols = st.columns(num_cards)
    
    for idx, ticker in enumerate(available_tickers):
        with cols[idx]:
            is_selected = st.session_state.selected_ticker == ticker
            button_key = f"stock_card_{ticker}"
            
            # Wrapper div for consistent alignment
            st.markdown('<div class="stock-card-wrapper">', unsafe_allow_html=True)
            
            # Display circular logo with first letter for all stocks (larger size)
            st.markdown(f'''
            <div style="width: 75px; height: 75px; border-radius: 50%; 
                        background: linear-gradient(135deg, #3b82f6, #1e3a8a); 
                        display: flex; align-items: center; justify-content: center; 
                        font-size: 30px; font-weight: bold; color: white; 
                        margin: 0 auto 0.5rem auto;">{ticker[0]}</div>
            ''', unsafe_allow_html=True)
            
            # Clickable button with larger font
            st.markdown(f"""
            <style>
            button[key="{button_key}"] {{
                font-size: 16px !important;
                padding: 0.9rem !important;
                min-height: 50px !important;
            }}
            </style>
            """, unsafe_allow_html=True)
            
            if st.button(ticker, key=button_key, use_container_width=True):
                st.session_state.selected_ticker = ticker
                st.rerun()
            
            # Close wrapper div
            st.markdown('</div>', unsafe_allow_html=True)
    
    # Use the selected ticker from stock cards
    if st.session_state.selected_ticker and st.session_state.selected_ticker in available_tickers:
        selected_ticker = st.session_state.selected_ticker
    else:
        # Default to first ticker if none selected
        selected_ticker = available_tickers[0]
        st.session_state.selected_ticker = selected_ticker
    
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
    
    # Movement History Section
    # Initialize selected period in session state
    if 'selected_period' not in st.session_state:
        st.session_state.selected_period = "ytd"
        st.session_state.period_label = "YTD"
    
    # Calculate period for percentage change (need this before displaying company name)
    end_date = pd.to_datetime(current_date)
    if st.session_state.selected_period == "ytd":
        start_date = pd.to_datetime(f"{end_date.year}-01-01")
    elif st.session_state.selected_period is not None:
        start_date = end_date - timedelta(days=st.session_state.selected_period)
    else:
        start_date = stock_data_df["Date"].min()
    
    _, pct_change_top = get_stock_data_for_period(stock_data_df, selected_ticker, start_date, end_date)
    
    # Main content - Company name and ticker with percentage change box
    company_name = get_company_name(selected_ticker)
    
    st.markdown(f"<h1 style='margin-bottom: 0.2rem;'>{company_name}</h1>", unsafe_allow_html=True)
    
    # Create columns for ticker and percentage change box on same line
    ticker_col, change_box_col = st.columns([2, 1])
    
    with ticker_col:
        st.markdown(f"<p style='font-size: 1.8rem; color: #94a3b8; margin-top: 0;'>{selected_ticker}</p>", unsafe_allow_html=True)
    
    with change_box_col:
        if pct_change_top is not None:
            color_top = "#10b981" if pct_change_top >= 0 else "#ef4444"
            triangle_top = "▲" if pct_change_top >= 0 else "▼"
            change_text_top = f"{triangle_top} {pct_change_top:+.2f}%"
            st.markdown(f'<div class="percentage-change-box" style="color: {color_top}; font-size: 1.8rem; font-weight: bold;">{change_text_top}</div>', unsafe_allow_html=True)
    
    st.markdown(f"<p style='font-size: 1.2rem;'>Current Price: ${current_price:.2f} | Date: {current_date}</p>", unsafe_allow_html=True)
    
    # Button configuration
    period_buttons = [
        ("1D", 1, "1 Day"),
        ("15D", 15, "15 Days"),
        ("1M", 30, "1 Month"),
        ("5Y", 1825, "5 Years"),
        ("YTD", "ytd", "YTD")
    ]
    
    # Create wrapper container for period buttons
    st.markdown('<div class="period-button-wrapper">', unsafe_allow_html=True)
    
    # Create columns with buttons on the left, space on right
    col_btn1, col_btn2, col_btn3, col_btn4, col_btn5, col_right = st.columns([1, 1, 1, 1, 1, 3])
    
    # Create buttons with wrapper divs for selected state
    button_cols = [col_btn1, col_btn2, col_btn3, col_btn4, col_btn5]
    
    for idx, (label, period_val, full_label) in enumerate(period_buttons):
        with button_cols[idx]:
            is_selected = st.session_state.selected_period == period_val
            button_key = f"period_btn_{label}"
            
            if st.button(label, key=button_key, use_container_width=True):
                st.session_state.selected_period = period_val
                st.session_state.period_label = full_label
                st.rerun()
    
    with col_right:
        st.write("")  # Empty space on right
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Add CSS for period buttons - styling based on selection
    period_css = ""
    for idx, (label, period_val, full_label) in enumerate(period_buttons):
        is_selected = st.session_state.selected_period == period_val
        if is_selected:
            bg_color = "#000000"
            text_color = "#ffffff"
            hover_bg = "#1a1a1a"
        else:
            bg_color = "#334155"
            text_color = "#e0e0e0"
            hover_bg = "#475569"
        
        # Target buttons in period-button-wrapper by column position
        period_css += f"""
        .period-button-wrapper div[data-testid="column"]:nth-of-type({idx + 1}) button {{
            background-color: {bg_color} !important;
            color: {text_color} !important;
            border: none !important;
            border-radius: 25px !important;
            padding: 0.3rem 0.7rem !important;
            font-weight: bold !important;
            font-size: 12px !important;
            transition: all 0.2s ease !important;
        }}
        .period-button-wrapper div[data-testid="column"]:nth-of-type({idx + 1}) button:hover {{
            background-color: {hover_bg} !important;
        }}
        """
    
    if period_css:
        st.markdown(f"<style>{period_css}</style>", unsafe_allow_html=True)
    
    selected_period = st.session_state.selected_period
    period_label = st.session_state.period_label
    
    # Calculate period (reuse the calculation from above)
    period_data, pct_change = get_stock_data_for_period(stock_data_df, selected_ticker, start_date, end_date)
    
    if period_data is not None and len(period_data) > 0:
        # Display period label only (percentage change moved to top)
        st.markdown(f"**{period_label}**")
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=period_data["Date"],
            y=period_data["Adj Close"],
            mode='lines',
            name=selected_ticker,
            line=dict(color='#3b82f6', width=2),
            fill='tozeroy',
            fillcolor='rgba(59, 130, 246, 0.3)'
        ))
        # Set x-axis format based on period - time format only for 1 Day
        if selected_period == 1:
            xaxis_format = dict(tickformat='%I:%M %p')
        else:
            xaxis_format = dict(tickformat='%b %d, %Y')
        
        fig.update_layout(
            title="",
            xaxis_title="",
            yaxis_title="",
            template="plotly_dark",
            height=400,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            xaxis=xaxis_format,
            margin=dict(t=10)
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Prediction Section
    st.markdown('<div class="prediction-card">', unsafe_allow_html=True)
    st.markdown('<div class="prediction-title">Prediction Analysis</div>', unsafe_allow_html=True)
    
    # Determine dominant probability for hierarchical coloring (outside columns)
    probs = {'Fall': down_prob, 'Rise': up_prob, 'Neutral': flat_prob}
    dominant = max(probs, key=probs.get)
    
    # Muted hierarchical color strategy - only dominant gets strong color
    if dominant == 'Fall':
        fall_color = '#E5533D'  # Strong red for dominant
        rise_color = '#38C172'  # Muted green
        neutral_color = '#6B7280'  # Muted gray
    elif dominant == 'Rise':
        fall_color = '#D8574A'  # Muted red
        rise_color = '#38C172'  # Strong green for dominant
        neutral_color = '#6B7280'  # Muted gray
    else:
        fall_color = '#D8574A'  # Muted red
        rise_color = '#38C172'  # Muted green
        neutral_color = '#6B7280'  # Strong gray for dominant
    
    col1, col2 = st.columns([1.2, 1])
    
    with col1:
        # Donut chart with refined styling
        fig_pie = go.Figure(data=[go.Pie(
            labels=['Fall', 'Rise', 'Neutral'],
            values=[down_prob * 100, up_prob * 100, flat_prob * 100],
            marker=dict(
                colors=[fall_color, rise_color, neutral_color],
                line=dict(width=3, color='rgba(30, 41, 59, 1)')  # Gap between segments (matches card bg)
            ),
            hole=0.65,  # Increased hole size reduces ring thickness by ~30%
            textinfo='none',
            showlegend=False,
            hovertemplate='%{label}<br>%{percent}<extra></extra>'
        )])
        fig_pie.update_layout(
            template=None,
            height=300,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=0, r=0, t=0, b=0),
            font=dict(family='system-ui, -apple-system, sans-serif')
        )
        st.plotly_chart(fig_pie, use_container_width=True, config={'displayModeBar': False})
    
    with col2:
        # Probability summary
        st.markdown(f"""
        <div style="padding-top: 1rem;">
            <div class="probability-row">
                <span class="probability-label">Fall</span>
                <span class="probability-value" style="color: {fall_color};">{down_prob*100:.1f}%</span>
            </div>
            <div class="probability-row">
                <span class="probability-label">Rise</span>
                <span class="probability-value" style="color: {rise_color};">{up_prob*100:.1f}%</span>
            </div>
            <div class="probability-row">
                <span class="probability-label">Neutral</span>
                <span class="probability-value" style="color: {neutral_color};">{flat_prob*100:.1f}%</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Signal Summary Card
    max_prob = max(down_prob, up_prob, flat_prob)
    if max_prob >= 0.6:
        confidence_level = "High"
    elif max_prob >= 0.4:
        confidence_level = "Medium"
    else:
        confidence_level = "Low"
    
    action_color_class = {
        'BUY': 'signal-buy',
        'SHORT': 'signal-short',
        'HOLD': 'signal-hold'
    }.get(action, 'signal-hold')
    
    st.markdown(f"""
    <div class="signal-summary-card">
        <div class="signal-summary-label">Model Bias</div>
        <div class="signal-summary-divider"></div>
        <div class="signal-summary-row">
            Signal: <span class="signal-action {action_color_class}">{action}</span>
        </div>
        <div class="signal-summary-row">
            Confidence: {confidence_level} ({max_prob*100:.1f}%)
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Model Variables Section
    st.header("Model Variables")
    
    st.markdown("""
    The model uses the following key variables:
    - **1. Stock's Own History (AR1-like)**: Historical price movements, returns (1, 5, 15, 30 day), momentum, volatility, RSI, drawdown
    - **2. Overall Market Conditions**: S&P 500 (^GSPC) performance and volatility
    - **3. Industry Conditions**: Via ETFs (XLK, XLF, etc.) and sector performance
    - **4. Economic Variables**: Interest rates, inflation, unemployment rate
    """)
    
    # Economic Conditions Section
    st.header("Economic Conditions")
    
    if economic_data:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            unemployment = economic_data.get("Unemployment_Rate")
            if unemployment is not None:
                st.metric("Unemployment Rate", f"{unemployment:.2f}%")
        
        with col2:
            interest = economic_data.get("Interest_Rate")
            if interest is not None:
                st.metric("Interest Rate", f"{interest:.2f}%")
        
        with col3:
            inflation_yoy = economic_data.get("Inflation_YoY")
            if inflation_yoy is not None:
                st.metric("Inflation Rate (YoY)", f"{inflation_yoy:.2f}%")
            else:
                inflation_raw = economic_data.get("Inflation_Rate")
                if inflation_raw is not None:
                    st.metric("Inflation Rate (Index)", f"{inflation_raw:.2f}")
    
    # Market Performance Section
    st.header("Market Performance (^GSPC)")
    
    if "^GSPC" in market_data:
        spx_data = market_data["^GSPC"]
        spx_dates = pd.to_datetime(spx_data["dates"])
        spx_prices = spx_data["prices"]
        
        fig_spx = go.Figure()
        fig_spx.add_trace(go.Scatter(
            x=spx_dates,
            y=spx_prices,
            mode='lines',
            name='S&P 500',
            line=dict(color='#10b981', width=2)
        ))
        fig_spx.update_layout(
            title="S&P 500 Performance",
            xaxis_title="Date",
            yaxis_title="Price",
            template="plotly_dark",
            height=400,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig_spx, use_container_width=True)
    
    # Backtest Statistics & Stock Info
    st.header("Backtest Statistics & Stock Information")
    
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


if __name__ == "__main__":
    main()

