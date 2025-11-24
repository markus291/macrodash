import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Global Macro Dashboard", layout="wide")

st.title("🌍 Live Macroeconomic Dashboard")
st.markdown("A real-time view of market proxies for Growth, Inflation, Rates, and Currency.")

# --- SIDEBAR SETTINGS ---
st.sidebar.header("Settings")
lookback_years = st.sidebar.slider("Lookback Period (Years)", 1, 10, 2)
start_date = (datetime.now() - timedelta(days=lookback_years*365)).strftime('%Y-%m-%d')

# --- DATA DEFINITIONS ---
# We use market tickers as proxies for macro events because they are live and free.
tickers = {
    "S&P 500 (Growth Proxy)": "^GSPC",
    "10-Year Treasury Yield (Rates)": "^TNX",
    "USD Index (Currency)": "DX-Y.NYB",
    "Gold (Inflation/Hedge)": "GC=F",
    "Crude Oil (Energy Costs)": "CL=F",
    "VIX (Volatility/Fear)": "^VIX"
}

# --- HELPER FUNCTION TO FETCH DATA ---
@st.cache_data
def get_data(ticker_dict, start):
    data = {}
    for name, symbol in ticker_dict.items():
        df = yf.download(symbol, start=start, progress=False)
        # Normalize: Calculate % change from start of period for comparison
        df['Pct_Change'] = ((df['Close'] - df['Close'].iloc[0]) / df['Close'].iloc[0]) * 100
        data[name] = df
    return data

# Fetch data
try:
    macro_data = get_data(tickers, start_date)
except Exception as e:
    st.error(f"Error fetching data: {e}")
    st.stop()

# --- KEY METRICS ROW ---
st.subheader("Live Market Snapshot")
cols = st.columns(len(tickers))

for i, (name, df) in enumerate(macro_data.items()):
    if not df.empty:
        current_price = df['Close'].iloc[-1]
        prev_price = df['Close'].iloc[-2]
        delta = current_price - prev_price
        
        # Color logic: Green is generally good, but for VIX/Yields, red/green depends on context.
        # Here we just use standard financial coloring (Green = Up, Red = Down).
        cols[i].metric(
            label=name,
            value=f"{current_price:.2f}",
            delta=f"{delta:.2f}"
        )

# --- MAIN CHARTS AREA ---
st.divider()

# Create two columns for layout
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Trend Analysis")
    selected_metrics = st.multiselect(
        "Select Indicators to Compare (Normalized % Return)",
        list(tickers.keys()),
        default=["S&P 500 (Growth Proxy)", "10-Year Treasury Yield (Rates)"]
    )
    
    if selected_metrics:
        fig = go.Figure()
        for metric in selected_metrics:
            df = macro_data[metric]
            fig.add_trace(go.Scatter(x=df.index, y=df['Pct_Change'], mode='lines', name=metric))
        
        fig.update_layout(
            title=f"Relative Performance ({lookback_years} Year Lookback)",
            xaxis_title="Date",
            yaxis_title="Percentage Change (%)",
            hovermode="x unified",
            height=500
        )
        st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("Yield Curve Proxy")
    st.info("Tracking the 'Price of Money'")
    
    # Fetching 2Y vs 10Y specifically for this chart
    try:
        # Note: Yahoo finance symbols for yields can be tricky, using TNX (10y) and IRX (13 week) as proxies 
        # or ZT=F for 2 year futures if available. 
        # For simplicity in this free version, we will plot 10Y Yield trend individually.
        tnx = macro_data["10-Year Treasury Yield (Rates)"]
        
        fig_yield = go.Figure()
        fig_yield.add_trace(go.Scatter(
            x=tnx.index, 
            y=tnx['Close'], 
            fill='tozeroy', 
            name='10Y Yield'
        ))
        fig_yield.update_layout(
            title="10-Year Treasury Yield",
            yaxis_title="Yield (%)",
            height=400
        )
        st.plotly_chart(fig_yield, use_container_width=True)
        
        st.markdown("""
        **Why this matters:**
        Rising yields often hurt growth stocks and increase borrowing costs for companies.
        """)
    except:
        st.write("Yield data currently unavailable.")

# --- ECONOMIC CONTEXT ---
st.divider()
st.subheader("Macro Interpretation Guide")
with st.expander("How to read this dashboard"):
    st.markdown("""
    *   **S&P 500:** Rising = Optimism about economic growth.
    *   **10-Year Yield:** Rising = Market expects higher inflation or stronger growth (or Fed hikes).
    *   **USD Index (DXY):** Strong Dollar = Can hurt US exports and Emerging Markets.
    *   **Gold:** Often rises during high inflation or geopolitical fear.
    *   **VIX:** < 20 = Calm, > 30 = Panic.
    """)