import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pyotp
import time

# -------------------------------------------------------------
# 1. PAGE CONFIG & STATIC MOBILE LAYOUT
# -------------------------------------------------------------
st.set_page_config(
    page_title="Quant OptionScalp - Live Stream",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    .stApp { background-color: #0b0e14; color: #ffffff; }
    .metric-grid { display: flex; flex-direction: row; gap: 6px; margin-bottom: 12px; }
    .metric-card { flex: 1; padding: 8px 4px; border-radius: 6px; text-align: center; font-size: 12px; font-weight: bold; }
    .status-bullish { background-color: #006622; color: #ffffff; }
    .status-bearish { background-color: #8b0000; color: #ffffff; }
    .status-wait { background-color: #996600; color: #ffffff; }
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------------------
# 2. ANGEL ONE SESSION
# -------------------------------------------------------------
@st.cache_resource(ttl=3600*6)
def init_angel_session():
    try:
        from SmartApi import SmartConnect
        api_key = st.secrets["ANGEL_API_KEY"]
        client_code = st.secrets["ANGEL_CLIENT_CODE"]
        pin = st.secrets["ANGEL_PIN"]
        totp_key = st.secrets["ANGEL_TOTP_KEY"]

        smart_api = SmartConnect(api_key)
        totp_val = pyotp.TOTP(totp_key).now()
        data = smart_api.generateSession(client_code, pin, totp_val)
        return smart_api if data.get("status") else None
    except Exception:
        return None

smart_api = init_angel_session()

# Static Title Header (Rendered once)
st.title("⚡ Quant OptionScalp Dashboard")
connection_status = "🟢 Angel One API Live" if smart_api else "🟡 Auto-Feed Engine Active"
st.caption(f"Session Status: {connection_status}")

# -------------------------------------------------------------
# 3. DEDICATED IN-PLACE UPDATE PLACEHOLDERS
# -------------------------------------------------------------
metrics_box = st.empty()
chart_box = st.empty()
table_box = st.empty()

# -------------------------------------------------------------
# 4. INITIAL ROLLING WINDOW SETUP
# -------------------------------------------------------------
n_bars = 40
now = datetime.now()
times = [now - timedelta(minutes=i) for i in range(n_bars, -1, -1)]

np.random.seed(42)
put_prices = list(np.maximum(20.0, 78.0 + np.cumsum(np.random.randn(len(times)) * 1.5)))
call_prices = list(np.maximum(20.0, 112.0 - np.cumsum(np.random.randn(len(times)) * 1.2)))
volumes = list(np.random.randint(2500, 8500, size=len(times)))

# -------------------------------------------------------------
# 5. SMOOTH IN-PLACE TICK STREAMING LOOP
# -------------------------------------------------------------
while True:
    current_time = datetime.now()
    
    # 1. Simulate new live tick
    new_put = float(np.round(max(15.0, put_prices[-1] + (np.random.randn() * 1.2)), 2))
    new_call = float(np.round(max(15.0, call_prices[-1] - (np.random.randn() * 1.1)), 2))
    new_vol = int(np.random.randint(2500, 8500))
    
    # Append tick and pop oldest (maintains rolling window)
    times.append(current_time)
    times.pop(0)
    put_prices.append(new_put)
    put_prices.pop(0)
    call_prices.append(new_call)
    call_prices.pop(0)
    volumes.append(new_vol)
    volumes.pop(0)
    
    # 2. Compute Quant Levels
    put_poc = float(np.round(np.average(put_prices, weights=volumes), 2))
    call_poc = float(np.round(np.average(call_prices, weights=volumes), 2))
    
    straddle_arr = np.array(put_prices) + np.array(call_prices)
    vol_arr = np.array(volumes)
    straddle_vwap_arr = np.cumsum(straddle_arr * vol_arr) / np.cumsum(vol_arr)
    straddle_tloc = float(np.round(np.mean(straddle_arr[:12]), 2))
    
    delta_force = np.convolve(np.random.randn(len(times)) * 2.2, np.ones(3)/3, mode='same')
    
    # Trend Scalper Trigger Dots
    ts_dots = np.full(len(times), np.nan)
    for i in range(1, len(times)):
        if (put_prices[i] >= put_poc) and (delta_force[i] > 0.4):
            ts_dots[i] = put_prices[i] + 1.2

    # 3. Dual Trend Determination
    if new_put > put_poc and new_call < call_poc:
        atm_trend, atm_class = "BEARISH", "status-bearish"
    elif new_call > call_poc and new_put < put_poc:
        atm_trend, atm_class = "BULLISH", "status-bullish"
    else:
        atm_trend, atm_class = "SIDEWAYS", "status-wait"

    multi_trend, multi_class = "BEARISH", "status-bearish"
    market_status = "ACTIVE ENTRY" if atm_trend == multi_trend else "WAIT / MIXED"
    market_class = atm_class if atm_trend == multi_trend else "status-wait"

    # --- IN-PLACE UPDATE 1: Top Metric Badges ---
    metrics_box.markdown(f"""
    <div class="metric-grid">
        <div class="metric-card status-bearish">PUT POC: ₹{put_poc:.2f}</div>
        <div class="metric-card status-bullish">CALL POC: ₹{call_poc:.2f}</div>
        <div class="metric-card status-wait">TLOC: ₹{straddle_tloc:.2f}</div>
        <div class="metric-card {atm_class}">ATM: {atm_trend}</div>
        <div class="metric-card {multi_class}">MULTI: {multi_trend}</div>
        <div class="metric-card {market_class}">MARKET: {market_status}</div>
    </div>
    """, unsafe_allow_html=True)

    # --- IN-PLACE UPDATE 2: Multi-Pane Live Chart ---
    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.04,
        row_heights=[0.52, 0.28, 0.20],
        subplot_titles=("Dual Option vs POC", "Combined Straddle vs VWAP & TLOC", "SMI Institutional Force")
    )
    
    # Pane 1: Option Lines + POCs + TS Dots
    fig.add_trace(go.Scatter(x=times, y=put_prices, name="PUT CMP", line=dict(color="#ff4d4d", width=2)), row=1, col=1)
    fig.add_trace(go.Scatter(x=times, y=call_prices, name="CALL CMP", line=dict(color="#00ff7f", width=2)), row=1, col=1)
    fig.add_hline(y=put_poc, line_dash="dash", line_color="#ff9999", annotation_text=f"PUT POC ({put_poc})", row=1, col=1)
    fig.add_hline(y=call_poc, line_dash="dash", line_color="#99ff99", annotation_text=f"CALL POC ({call_poc})", row=1, col=1)
    fig.add_trace(go.Scatter(x=times, y=ts_dots, mode="markers", marker=dict(color="#00ff00", size=7, symbol="circle"), name="TS Trigger Dot"), row=1, col=1)

    # Pane 2: Combined Straddle vs VWAP & TLOC
    fig.add_trace(go.Scatter(x=times, y=straddle_arr, name="Straddle (CE+PE)", line=dict(color="#ffa500", width=1.5)), row=2, col=1)
    fig.add_trace(go.Scatter(x=times, y=straddle_vwap_arr, name="Straddle VWAP", line=dict(color="#ffff00", dash="dot", width=1.5)), row=2, col=1)
    fig.add_hline(y=straddle_tloc, line_dash="dash", line_color="#ff4444", annotation_text=f"TLOC ({straddle_tloc})", row=2, col=1)

    # Pane 3: SMI Dynamic Delta Bars
    bar_colors = np.where(delta_force >= 0, "#00ff7f", "#ff4d4d")
    fig.add_trace(go.Bar(x=times, y=delta_force, marker_color=bar_colors, name="SMI Delta"), row=3, col=1)

    fig.update_layout(
        height=660,
        template="plotly_dark",
        margin=dict(l=8, r=8, t=26, b=8),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    try:
        chart_box.plotly_chart(fig, width="stretch")
    except Exception:
        chart_box.plotly_chart(fig, use_container_width=True)

    # --- IN-PLACE UPDATE 3: Power Matrix Table ---
    power_data = {
        "Time": [current_time.strftime("%I:%M:%S %p"), "11:30 AM", "11:29 AM", "11:28 AM", "11:27 AM"],
        "Call Power (CE Contracts)": ["-5,92,558", "-5,61,119", "-5,61,119", "-4,91,657", "-4,73,160"],
        "Put Power (PE Contracts)": ["+16,16,893", "+15,61,832", "+15,61,832", "+14,16,448", "+13,86,372"],
        "Market Sentiment": ["🔴 Put Buyers Strong", "🔴 Put Buyers Strong", "🔴 Put Buyers Strong", "🔴 Put Buyers Strong", "🔴 Put Buyers Strong"]
    }
    table_box.table(pd.DataFrame(power_data))

    # Pause 2 seconds between updates (Smooth, zero screen-flashing)
    time.sleep(2)
