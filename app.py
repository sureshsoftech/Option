import sys
import subprocess

# Auto-install required packages if Streamlit Cloud skipped them
for pkg in ["plotly", "pandas", "numpy", "streamlit-autorefresh"]:
    try:
        __import__(pkg.replace("-", "_"))
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])

import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

try:
    from streamlit_autorefresh import st_autorefresh
    st_autorefresh(interval=3000, key="quant_refresh")
except Exception:
    pass

st.set_page_config(page_title="Quant Option Engine", layout="wide", initial_sidebar_state="collapsed")

# Custom Dark Theme
st.markdown("""
<style>
    .reportview-container, .main { background-color: #0e1117; color: #ffffff; }
    .metric-box { padding: 10px; border-radius: 8px; text-align: center; font-weight: bold; margin-bottom: 8px; }
    .status-bullish { background-color: #008000; color: white; }
    .status-bearish { background-color: #8b0000; color: white; }
    .status-wait { background-color: #b8860b; color: white; }
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------------------
# SYNTHETIC DATA ENGINE
# -------------------------------------------------------------
@st.cache_data(ttl=2)
def get_market_data():
    now = datetime.now()
    times = [now - timedelta(minutes=i) for i in range(40, -1, -1)]
    
    np.random.seed(42)
    put_prices = 80 + np.cumsum(np.random.randn(len(times)) * 1.5)
    call_prices = 110 - np.cumsum(np.random.randn(len(times)) * 1.2)
    
    put_poc = float(np.round(np.mean(put_prices), 2))
    call_poc = float(np.round(np.mean(call_prices), 2))
    
    straddle_price = put_prices + call_prices
    straddle_vwap = np.convolve(straddle_price, np.ones(5)/5, mode='same')
    straddle_tloc = float(np.round(np.mean(straddle_price), 2))
    
    impulse = np.random.randn(len(times))
    ts_dots = np.where(impulse > 0.8, put_prices + 1.5, np.nan)
    
    df = pd.DataFrame({
        'time': times,
        'put_price': put_prices,
        'call_price': call_prices,
        'straddle': straddle_price,
        'straddle_vwap': straddle_vwap,
        'ts_dots': ts_dots
    })
    return df, put_poc, call_poc, straddle_tloc

df, put_poc, call_poc, straddle_tloc = get_market_data()

# -------------------------------------------------------------
# TOP METRICS
# -------------------------------------------------------------
st.title("⚡ Quant OptionScalp Dashboard")

col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.markdown(f'<div class="metric-box status-bearish">PUT POC: ₹{put_poc:.2f}</div>', unsafe_allow_html=True)
with col2:
    st.markdown(f'<div class="metric-box status-bullish">CALL POC: ₹{call_poc:.2f}</div>', unsafe_allow_html=True)
with col3:
    st.markdown(f'<div class="metric-box status-wait">STRADDLE TLOC: ₹{straddle_tloc:.2f}</div>', unsafe_allow_html=True)
with col4:
    st.markdown('<div class="metric-box status-bearish">MULTI-TREND: BEARISH</div>', unsafe_allow_html=True)
with col5:
    st.markdown('<div class="metric-box status-wait">MARKET: WAIT / MIXED</div>', unsafe_allow_html=True)

# -------------------------------------------------------------
# CHARTS (Plotly)
# -------------------------------------------------------------
fig = make_subplots(
    rows=3, cols=1, 
    shared_xaxes=True, 
    vertical_spacing=0.03,
    row_heights=[0.55, 0.25, 0.20],
    subplot_titles=("Dual Option Price vs POC", "Combined Straddle vs VWAP & TLOC", "Trend Scalper Impulse (TS)")
)

fig.add_trace(go.Scatter(x=df['time'], y=df['put_price'], name="PUT Option (CMP)", line=dict(color='#ff4d4d', width=2)), row=1, col=1)
fig.add_trace(go.Scatter(x=df['time'], y=df['call_price'], name="CALL Option (CMP)", line=dict(color='#00ff7f', width=2)), row=1, col=1)
fig.add_hline(y=put_poc, line_dash="dash", line_color="#ff9999", annotation_text=f"PUT POC ({put_poc})", row=1, col=1)
fig.add_hline(y=call_poc, line_dash="dash", line_color="#99ff99", annotation_text=f"CALL POC ({call_poc})", row=1, col=1)
fig.add_trace(go.Scatter(x=df['time'], y=df['ts_dots'], mode='markers', marker=dict(color='#00ff00', size=8, symbol='circle'), name="TS Dot Trigger"), row=1, col=1)

fig.add_trace(go.Scatter(x=df['time'], y=df['straddle'], name="Straddle (CE+PE)", line=dict(color='#ffa500', width=1.5)), row=2, col=1)
fig.add_trace(go.Scatter(x=df['time'], y=df['straddle_vwap'], name="Straddle VWAP", line=dict(color='#ffff00', dash='dot')), row=2, col=1)
fig.add_hline(y=straddle_tloc, line_dash="dash", line_color="#ff4444", annotation_text=f"TLOC ({straddle_tloc})", row=2, col=1)

fig.add_trace(go.Bar(x=df['time'], y=np.sin(np.linspace(0, 10, len(df))), marker_color='#ff4d4d', name="Delta / SMI Force"), row=3, col=1)

fig.update_layout(
    height=650, 
    template="plotly_dark", 
    margin=dict(l=10, r=10, t=30, b=10),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)
st.plotly_chart(fig, use_container_width=True)

# -------------------------------------------------------------
# POWER HISTORY MATRIX
# -------------------------------------------------------------
st.subheader("📊 Power History (5 Strike Matrix)")
power_data = {
    "Time": ["11:31 AM", "11:30 AM", "11:29 AM", "11:28 AM", "11:27 AM"],
    "Call Power (CE Contracts)": ["-5,92,558", "-5,61,119", "-5,61,119", "-4,91,657", "-4,73,160"],
    "Put Power (PE Contracts)": ["+16,16,893", "+15,61,832", "+15,61,832", "+14,16,448", "+13,86,372"],
    "Market Sentiment": ["🔴 Put Buyers Strong", "🔴 Put Buyers Strong", "🔴 Put Buyers Strong", "🔴 Put Buyers Strong", "🔴 Put Buyers Strong"]
}
st.table(pd.DataFrame(power_data))
