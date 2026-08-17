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

st.set_page_config(
    page_title="Quant OptionScalp Dashboard",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom Mobile CSS
st.markdown("""
<style>
    .stApp { background-color: #0b0e14; color: #ffffff; }
    .metric-grid { display: flex; flex-direction: row; gap: 6px; margin-bottom: 12px; }
    .metric-card { flex: 1; padding: 8px 4px; border-radius: 6px; text-align: center; font-size: 13px; font-weight: bold; }
    .status-bullish { background-color: #006622; color: #ffffff; }
    .status-bearish { background-color: #8b0000; color: #ffffff; }
    .status-wait { background-color: #996600; color: #ffffff; }
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------------------
# REALISTIC OPTION & STRADDLE SIMULATION ENGINE
# -------------------------------------------------------------
@st.cache_data(ttl=2)
def get_market_data():
    now = datetime.now()
    n_bars = 45
    times = [now - timedelta(minutes=i) for i in range(n_bars, -1, -1)]
    
    np.random.seed(int(now.minute) + 10)
    
    # 1. Option Prices with Mean-Reversion
    base_put, base_call = 75.0, 115.0
    put_walk = np.cumsum(np.random.randn(len(times)) * 1.8)
    call_walk = np.cumsum(np.random.randn(len(times)) * 1.4)
    
    put_prices = np.maximum(20.0, base_put + put_walk)
    call_prices = np.maximum(20.0, base_call - call_walk)
    
    volumes = np.random.randint(1500, 8500, size=len(times))
    
    # 2. Strike Volume POCs
    put_poc = float(np.round(np.average(put_prices, weights=volumes), 2))
    call_poc = float(np.round(np.average(call_prices, weights=volumes), 2))
    
    # 3. Synthetic Combined Straddle & Cumulative VWAP
    straddle_price = put_prices + call_prices
    cum_vol = np.cumsum(volumes)
    straddle_vwap = np.cumsum(straddle_price * volumes) / cum_vol
    straddle_tloc = float(np.round(np.mean(straddle_price[:15]), 2))
    
    # 4. SMI / Delta Force
    delta_force = np.convolve(np.random.randn(len(times)) * 2.5, np.ones(3)/3, mode='same')
    
    # 5. Trend Scalper (TS) Double Dots (Fires when Put reclaims POC with positive delta)
    ts_dots = np.full(len(times), np.nan)
    for i in range(1, len(times)):
        if (put_prices[i] >= put_poc) and (delta_force[i] > 0.5):
            ts_dots[i] = put_prices[i] + 1.2

    df = pd.DataFrame({
        "time": times,
        "put_price": put_prices,
        "call_price": call_prices,
        "straddle": straddle_price,
        "straddle_vwap": straddle_vwap,
        "delta_force": delta_force,
        "ts_dots": ts_dots
    })
    return df, put_poc, call_poc, straddle_tloc

df, put_poc, call_poc, straddle_tloc = get_market_data()

# -------------------------------------------------------------
# TOP COMPACT METRIC CARDS
# -------------------------------------------------------------
st.title("⚡ Quant OptionScalp Dashboard")

st.markdown(f"""
<div class="metric-grid">
    <div class="metric-card status-bearish">PUT POC: ₹{put_poc:.2f}</div>
    <div class="metric-card status-bullish">CALL POC: ₹{call_poc:.2f}</div>
    <div class="metric-card status-wait">TLOC: ₹{straddle_tloc:.2f}</div>
    <div class="metric-card status-bearish">TREND: BEARISH</div>
    <div class="metric-card status-wait">STATUS: MIXED</div>
</div>
""", unsafe_allow_html=True)

# -------------------------------------------------------------
# MULTI-PANE CHART SETUP
# -------------------------------------------------------------
fig = make_subplots(
    rows=3, cols=1,
    shared_xaxes=True,
    vertical_spacing=0.04,
    row_heights=[0.52, 0.28, 0.20],
    subplot_titles=("Dual Option vs POC", "Combined Straddle vs VWAP & TLOC", "SMI Institutional Force")
)

# Pane 1: Options & POCs
fig.add_trace(go.Scatter(x=df["time"], y=df["put_price"], name="PUT CMP", line=dict(color="#ff4d4d", width=2)), row=1, col=1)
fig.add_trace(go.Scatter(x=df["time"], y=df["call_price"], name="CALL CMP", line=dict(color="#00ff7f", width=2)), row=1, col=1)
fig.add_hline(y=put_poc, line_dash="dash", line_color="#ff9999", annotation_text=f"PUT POC ({put_poc})", row=1, col=1)
fig.add_hline(y=call_poc, line_dash="dash", line_color="#99ff99", annotation_text=f"CALL POC ({call_poc})", row=1, col=1)
fig.add_trace(go.Scatter(x=df["time"], y=df["ts_dots"], mode="markers", marker=dict(color="#00ff00", size=7, symbol="circle"), name="TS Trigger Dot"), row=1, col=1)

# Pane 2: Straddle vs VWAP & TLOC
fig.add_trace(go.Scatter(x=df["time"], y=df["straddle"], name="Straddle (CE+PE)", line=dict(color="#ffa500", width=1.5)), row=2, col=1)
fig.add_trace(go.Scatter(x=df["time"], y=df["straddle_vwap"], name="Straddle VWAP", line=dict(color="#ffff00", dash="dot", width=1.5)), row=2, col=1)
fig.add_hline(y=straddle_tloc, line_dash="dash", line_color="#ff4444", annotation_text=f"TLOC ({straddle_tloc})", row=2, col=1)

# Pane 3: Dynamic SMI Force Bars
bar_colors = np.where(df["delta_force"] >= 0, "#00ff7f", "#ff4d4d")
fig.add_trace(go.Bar(x=df["time"], y=df["delta_force"], marker_color=bar_colors, name="SMI Delta"), row=3, col=1)

fig.update_layout(
    height=660,
    template="plotly_dark",
    margin=dict(l=8, r=8, t=26, b=8),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
)

st.plotly_chart(fig, use_container_width=True)

# -------------------------------------------------------------
# POWER HISTORY
# -------------------------------------------------------------
st.subheader("📊 Power History (5 Strike Matrix)")

power_data = {
    "Time": ["11:31 AM", "11:30 AM", "11:29 AM", "11:28 AM", "11:27 AM"],
    "Call Power (CE Contracts)": ["-5,92,558", "-5,61,119", "-5,61,119", "-4,91,657", "-4,73,160"],
    "Put Power (PE Contracts)": ["+16,16,893", "+15,61,832", "+15,61,832", "+14,16,448", "+13,86,372"],
    "Market Sentiment": ["🔴 Put Buyers Strong", "🔴 Put Buyers Strong", "🔴 Put Buyers Strong", "🔴 Put Buyers Strong", "🔴 Put Buyers Strong"]
}

st.table(pd.DataFrame(power_data))
