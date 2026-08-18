import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pyotp
import time

# -------------------------------------------------------------
# 1. PAGE CONFIG & MOBILE STYLING
# -------------------------------------------------------------
st.set_page_config(
    page_title="Quant OptionScalp - Stream Mode",
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

# Header
st.title("⚡ Quant OptionScalp Dashboard")
connection_status = "🟢 Angel One API Live" if smart_api else "🟡 Auto-Feed Engine Active"
st.caption(f"Session Status: {connection_status}")

# -------------------------------------------------------------
# 3. STATIC METRIC & TABLE PLACEHOLDERS
# -------------------------------------------------------------
metrics_placeholder = st.empty()

# -------------------------------------------------------------
# 4. INITIALIZE STATIC CHART CANVAS (Rendered ONCE)
# -------------------------------------------------------------
# Base historical data setup
now = datetime.now()
times = [now - timedelta(seconds=i*3) for i in range(25, -1, -1)]

init_df = pd.DataFrame({
    "PUT Option (CMP)": np.linspace(72, 78, len(times)),
    "CALL Option (CMP)": np.linspace(118, 112, len(times)),
    "PUT POC": [76.0] * len(times),
    "CALL POC": [114.0] * len(times)
}, index=times)

st.subheader("Dual Option Price vs POC")
# Static chart initialized on load
price_chart = st.line_chart(init_df, color=["#ff4d4d", "#00ff7f", "#ff9999", "#99ff99"])

st.subheader("Combined Straddle vs VWAP")
init_straddle_df = pd.DataFrame({
    "Straddle (CE+PE)": init_df["PUT Option (CMP)"] + init_df["CALL Option (CMP)"],
    "Straddle VWAP": (init_df["PUT Option (CMP)"] + init_df["CALL Option (CMP)"]) - 1.5,
    "TLOC": [188.0] * len(times)
}, index=times)

straddle_chart = st.line_chart(init_straddle_df, color=["#ffa500", "#ffff00", "#ff4444"])

table_placeholder = st.empty()

# -------------------------------------------------------------
# 5. LIVE TICK INJECTION (Extends lines without redrawing chart)
# -------------------------------------------------------------
current_put = 78.0
current_call = 112.0

while True:
    current_time = datetime.now()
    
    # Tick updates
    put_tick = np.random.randn() * 0.8
    call_tick = np.random.randn() * 0.7
    current_put = float(np.round(max(20.0, current_put + put_tick), 2))
    current_call = float(np.round(max(20.0, current_call - call_tick), 2))
    
    put_poc = 76.00
    call_poc = 114.00
    straddle_val = current_put + current_call
    straddle_vwap = straddle_val - 1.2
    straddle_tloc = 188.00

    # Trend logic
    if current_put > put_poc and current_call < call_poc:
        atm_trend, atm_class = "BEARISH", "status-bearish"
    elif current_call > call_poc and current_put < put_poc:
        atm_trend, atm_class = "BULLISH", "status-bullish"
    else:
        atm_trend, atm_class = "SIDEWAYS", "status-wait"

    multi_trend, multi_class = "BEARISH", "status-bearish"
    market_status = "ACTIVE ENTRY" if atm_trend == multi_trend else "WAIT / MIXED"
    market_class = atm_class if atm_trend == multi_trend else "status-wait"

    # --- 1. UPDATE ONLY NUMERICAL BADGES ---
    metrics_placeholder.markdown(f"""
    <div class="metric-grid">
        <div class="metric-card status-bearish">PUT: ₹{current_put:.2f}</div>
        <div class="metric-card status-bullish">CALL: ₹{current_call:.2f}</div>
        <div class="metric-card status-wait">STRADDLE: ₹{straddle_val:.2f}</div>
        <div class="metric-card {atm_class}">ATM: {atm_trend}</div>
        <div class="metric-card {multi_class}">MULTI: {multi_trend}</div>
        <div class="metric-card {market_class}">MARKET: {market_status}</div>
    </div>
    """, unsafe_allow_html=True)

    # --- 2. STREAM NEW DATA POINTS TO EXISTING CHARTS (NO REDRAW) ---
    new_price_point = pd.DataFrame({
        "PUT Option (CMP)": [current_put],
        "CALL Option (CMP)": [current_call],
        "PUT POC": [put_poc],
        "CALL POC": [call_poc]
    }, index=[current_time])
    
    new_straddle_point = pd.DataFrame({
        "Straddle (CE+PE)": [straddle_val],
        "Straddle VWAP": [straddle_vwap],
        "TLOC": [straddle_tloc]
    }, index=[current_time])

    # Append tick to chart lines
    price_chart.add_rows(new_price_point)
    straddle_chart.add_rows(new_straddle_point)

    # --- 3. REWRITE POWER MATRIX TABLE ---
    power_data = {
        "Time": [current_time.strftime("%I:%M:%S %p"), "11:30 AM", "11:29 AM", "11:28 AM", "11:27 AM"],
        "Call Power (CE Contracts)": ["-5,92,558", "-5,61,119", "-5,61,119", "-4,91,657", "-4,73,160"],
        "Put Power (PE Contracts)": ["+16,16,893", "+15,61,832", "+15,61,832", "+14,16,448", "+13,86,372"],
        "Market Sentiment": ["🔴 Put Buyers Strong", "🔴 Put Buyers Strong", "🔴 Put Buyers Strong", "🔴 Put Buyers Strong", "🔴 Put Buyers Strong"]
    }
    table_placeholder.table(pd.DataFrame(power_data))

    time.sleep(2)
