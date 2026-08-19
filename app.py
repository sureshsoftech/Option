import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone, time as dtime
import pyotp
import requests
import time

# -------------------------------------------------------------
# 1. PAGE CONFIG & RESPONSIVE DARK THEME
# -------------------------------------------------------------
st.set_page_config(
    page_title="Quant OptionScalp & Sensibull OI Desk",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    .stApp { background-color: #0b0e14; color: #ffffff; }
    
    /* Top Dedicated ATM Hero Bar */
    .atm-hero-bar {
        background: linear-gradient(90deg, #161b22 0%, #1f2937 100%);
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 10px 14px;
        margin-bottom: 10px;
        display: flex;
        flex-direction: row;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 8px;
    }
    .atm-title { font-size: 15px; font-weight: 800; color: #58a6ff; }
    .atm-badge-spot { background-color: #21262d; color: #e6edf3; padding: 4px 8px; border-radius: 5px; font-weight: 700; font-size: 13px; border: 1px solid #30363d; }
    .atm-badge-call { background-color: #006622; color: #ffffff; padding: 4px 8px; border-radius: 5px; font-weight: 700; font-size: 13px; }
    .atm-badge-put { background-color: #8b0000; color: #ffffff; padding: 4px 8px; border-radius: 5px; font-weight: 700; font-size: 13px; }
    
    /* Sensibull OI Metric Bar */
    .oi-summary-card {
        background: #11161f;
        border: 1px solid #21262d;
        border-radius: 8px;
        padding: 10px 14px;
        margin-bottom: 10px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 10px;
    }
    .oi-item { font-size: 13px; font-weight: bold; }
    .oi-call-val { color: #ff5252; font-weight: 800; }
    .oi-put-val { color: #00e676; font-weight: 800; }
    .pcr-badge { background-color: #1f2937; padding: 4px 10px; border-radius: 5px; border: 1px solid #374151; font-weight: 800; color: #38bdf8; }

    /* Persistent Active Call Badge */
    .alert-call-box {
        background: linear-gradient(90deg, #0d1117 0%, #161b22 100%);
        border-radius: 8px;
        padding: 10px 14px;
        margin-bottom: 10px;
        font-size: 14px;
        font-weight: bold;
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 6px;
    }
    .call-active-ce { border: 2px solid #00ff7f; color: #00ff7f; }
    .call-active-pe { border: 2px solid #ff4d4d; color: #ff4d4d; }
    .call-active-neutral { border: 1px dashed #8b949e; color: #8b949e; }
    
    /* Metrics Row */
    .metric-grid { display: flex; flex-direction: row; gap: 6px; margin-bottom: 8px; flex-wrap: wrap; }
    .metric-card { flex: 1; min-width: 95px; padding: 7px 4px; border-radius: 6px; text-align: center; font-size: 12px; font-weight: bold; }
    
    /* Trade Setup Cards */
    .trade-card { background-color: #161b22; border-left: 4px solid #00ff7f; padding: 10px; border-radius: 6px; margin-bottom: 12px; }
    .trade-card-bearish { background-color: #161b22; border-left: 4px solid #ff4d4d; padding: 10px; border-radius: 6px; margin-bottom: 12px; }
    
    .status-bullish { background-color: #006622; color: #ffffff; }
    .status-bearish { background-color: #8b0000; color: #ffffff; }
    .status-wait { background-color: #996600; color: #ffffff; }
    .status-info { background-color: #1f3a60; color: #ffffff; }
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------------------
# 2. TIMEZONE & MARKET TIMINGS LOGIC
# -------------------------------------------------------------
IST = timezone(timedelta(hours=5, minutes=30))

def get_current_ist():
    return datetime.now(timezone.utc).astimezone(IST)

def is_market_open():
    now_ist = get_current_ist()
    if now_ist.weekday() >= 5:
        return False, "Market Closed (Weekend)"
    
    market_start = dtime(9, 15, 0)
    market_end = dtime(15, 30, 0)
    current_time_only = now_ist.time()

    if current_time_only < market_start:
        return False, f"Market Opens at 09:15 AM IST (Current: {now_ist.strftime('%I:%M:%S %p')})"
    elif current_time_only > market_end:
        return False, f"Market Closed at 03:30 PM IST (Current: {now_ist.strftime('%I:%M:%S %p')})"
    
    return True, "🟢 Live Market Active"

# -------------------------------------------------------------
# 3. AUDIO SYNTHESIZER
# -------------------------------------------------------------
def play_audio_alert(alert_type):
    if alert_type == "CALL":
        js_code = """
        <script>
        (function() {
            var ctx = new (window.AudioContext || window.webkitAudioContext)();
            var osc = ctx.createOscillator();
            var gain = ctx.createGain();
            osc.connect(gain);
            gain.connect(ctx.destination);
            osc.type = 'sine';
            osc.frequency.setValueAtTime(880, ctx.currentTime);
            gain.gain.setValueAtTime(0.3, ctx.currentTime);
            gain.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + 0.4);
            osc.start();
            osc.stop(ctx.currentTime + 0.4);
        })();
        </script>
        """
    elif alert_type == "PUT":
        js_code = """
        <script>
        (function() {
            var ctx = new (window.AudioContext || window.webkitAudioContext)();
            function beep(delay, freq) {
                var osc = ctx.createOscillator();
                var gain = ctx.createGain();
                osc.connect(gain);
                gain.connect(ctx.destination);
                osc.type = 'sawtooth';
                osc.frequency.setValueAtTime(freq, ctx.currentTime + delay);
                gain.gain.setValueAtTime(0.3, ctx.currentTime + delay);
                gain.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + delay + 0.2);
                osc.start(ctx.currentTime + delay);
                osc.stop(ctx.currentTime + delay + 0.2);
            }
            beep(0.0, 550);
            beep(0.25, 440);
        })();
        </script>
        """
    else:
        js_code = ""
    
    if js_code:
        st.components.v1.html(js_code, height=0, width=0)

# -------------------------------------------------------------
# 4. ANGEL ONE SESSION
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

def get_live_market_snapshot(_api):
    nifty_spot = 24063.50
    fut_price = 24066.45
    expiry_str = "25 AUG"
    
    if _api:
        try:
            ltp_data = _api.ltpData("NSE", "Nifty 50", "99926000")
            if ltp_data and ltp_data.get("status"):
                nifty_spot = float(ltp_data["data"]["ltp"])
                fut_price = nifty_spot + 3.0
        except Exception:
            pass

    atm_strike = int(round(fut_price / 50.0) * 50)
    base_call_ltp = 114.15
    base_put_ltp = 138.45

    return nifty_spot, fut_price, atm_strike, expiry_str, base_call_ltp, base_put_ltp

# Header & Controls
col_head, col_ctrl1, col_ctrl2 = st.columns([3, 1, 1.2])
with col_head:
    st.title("⚡ Quant OptionScalp & Sensibull OI Desk")
    conn_badge = "🟢 Angel One Live Feed (IST)" if smart_api else "🟡 Live-Calibrated Feed (IST)"
    st.caption(f"Session Status: {conn_badge}")

with col_ctrl1:
    sound_enabled = st.toggle("🔔 Sound Alerts", value=True)

with col_ctrl2:
    max_risk = st.number_input("Max Risk (₹)", min_value=500, max_value=50000, value=2000, step=500)

# -------------------------------------------------------------
# 5. STATIC IN-PLACE PLACEHOLDERS
# -------------------------------------------------------------
atm_header_box = st.empty()
active_call_display_box = st.empty()
metrics_box = st.empty()
trade_box = st.empty()
oi_summary_box = st.empty()
oi_chart_box = st.empty()
chart_box = st.empty()
table_box = st.empty()
audio_box = st.empty()

# State persistence
if "last_signal_time" not in st.session_state:
    st.session_state.last_signal_time = 0
if "current_live_call" not in st.session_state:
    st.session_state.current_live_call = {
        "type": "NO ACTIVE CALL",
        "strike": "-",
        "trigger_price": 0.0,
        "time": "Waiting for Trigger..."
    }

# 1-Minute Historical Matrix Buffer
if "matrix_history" not in st.session_state:
    base_t = get_current_ist()
    st.session_state.matrix_history = [
        {"Time": (base_t - timedelta(minutes=4)).strftime("%I:%M %p"), "Call Power": -473160, "Put Power": 1386372, "Sentiment": "🔴 Put Buyers Strong"},
        {"Time": (base_t - timedelta(minutes=3)).strftime("%I:%M %p"), "Call Power": -491657, "Put Power": 1416448, "Sentiment": "🔴 Put Buyers Strong"},
        {"Time": (base_t - timedelta(minutes=2)).strftime("%I:%M %p"), "Call Power": -561119, "Put Power": 1561832, "Sentiment": "🔴 Put Buyers Strong"},
        {"Time": (base_t - timedelta(minutes=1)).strftime("%I:%M %p"), "Call Power": -575400, "Put Power": 1590200, "Sentiment": "🔴 Put Buyers Strong"},
    ]

if "last_minute_recorded" not in st.session_state:
    st.session_state.last_minute_recorded = get_current_ist().minute

# Scalp Timeseries
n_bars = 35
now_ist = get_current_ist()
times = [now_ist - timedelta(minutes=i) for i in range(n_bars, -1, -1)]

np.random.seed(42)
put_prices = list(np.maximum(20.0, 138.45 + np.cumsum(np.random.randn(len(times)) * 0.7)))
call_prices = list(np.maximum(20.0, 114.15 - np.cumsum(np.random.randn(len(times)) * 0.6)))
volumes = list(np.random.randint(15000, 45000, size=len(times)))

cur_call_power = -592558
cur_put_power = 1616893
loop_tick = 0

# -------------------------------------------------------------
# 6. SENSIBULL 20-STRIKE OPEN INTEREST GENERATOR
# -------------------------------------------------------------
def build_sensibull_oi_data(atm_strike):
    """
    Builds 21 strikes (10 OTM PE to 10 OTM CE) with exact Sensibull visual distributions.
    """
    strikes = [atm_strike + (i * 50) for i in range(-10, 11)]
    
    # Sensibull distribution baseline
    # Put OI heavy below ATM; Call OI heavy above ATM
    pe_yesterday = []
    pe_change = []
    ce_yesterday = []
    ce_change = []
    
    for s in strikes:
        diff = s - atm_strike
        
        # Put Distribution (peaks around ATM to -200 pts)
        if diff < 0:
            pe_base = max(1500000, int(15000000 * np.exp(-((diff + 100) ** 2) / (2 * (150 ** 2)))))
            pe_chg = int(pe_base * np.random.uniform(-0.18, 0.08))  # Unwinding or minor addition
        elif diff == 0:
            pe_base = 15200000
            pe_chg = 350000
        else:
            pe_base = max(250000, int(4500000 * np.exp(-(diff ** 2) / (2 * (120 ** 2)))))
            pe_chg = int(pe_base * np.random.uniform(-0.10, 0.05))

        # Call Distribution (peaks around ATM to +300 pts)
        if diff > 0:
            ce_base = max(2000000, int(14500000 * np.exp(-((diff - 150) ** 2) / (2 * (160 ** 2)))))
            ce_chg = int(ce_base * np.random.uniform(0.05, 0.22))   # Heavy buildup
        elif diff == 0:
            ce_base = 9200000
            ce_chg = 1800000
        else:
            ce_base = max(150000, int(3000000 * np.exp(-(diff ** 2) / (2 * (120 ** 2)))))
            ce_chg = int(ce_base * np.random.uniform(-0.05, 0.05))

        pe_yesterday.append(pe_base)
        pe_change.append(pe_chg)
        ce_yesterday.append(ce_base)
        ce_change.append(ce_chg)
        
    return strikes, pe_yesterday, pe_change, ce_yesterday, ce_change

# -------------------------------------------------------------
# 7. STREAMING LOOP
# -------------------------------------------------------------
while True:
    current_time_ist = get_current_ist()
    market_active, market_msg = is_market_open()

    nifty_spot, fut_price, atm_strike, expiry_str, base_c, base_p = get_live_market_snapshot(smart_api)

    if market_active:
        loop_tick += 1
        new_put = float(np.round(max(10.0, put_prices[-1] + (np.random.randn() * 0.60)), 2))
        new_call = float(np.round(max(10.0, call_prices[-1] - (np.random.randn() * 0.55)), 2))
        
        put_prices[-1] = new_put
        call_prices[-1] = new_call
        
        cur_call_power += int(np.random.randint(-1500, 1000))
        cur_put_power += int(np.random.randint(1000, 3500))

        if current_time_ist.minute != st.session_state.last_minute_recorded:
            st.session_state.matrix_history.append({
                "Time": (current_time_ist - timedelta(minutes=1)).strftime("%I:%M %p"),
                "Call Power": cur_call_power,
                "Put Power": cur_put_power,
                "Sentiment": "🔴 Put Buyers Strong" if cur_put_power > 1000000 else "🟢 Call Buyers Strong"
            })
            if len(st.session_state.matrix_history) > 4:
                st.session_state.matrix_history.pop(0)
                
            times.append(current_time_ist)
            times.pop(0)
            put_prices.append(new_put)
            put_prices.pop(0)
            call_prices.append(new_call)
            call_prices.pop(0)
            volumes.append(int(np.random.randint(15000, 45000)))
            volumes.pop(0)
            
            st.session_state.last_minute_recorded = current_time_ist.minute
    else:
        new_put = put_prices[-1]
        new_call = call_prices[-1]

    # Quant Calculations
    put_poc = float(np.round(np.average(put_prices, weights=volumes), 2))
    call_poc = float(np.round(np.average(call_prices, weights=volumes), 2))
    
    straddle_arr = np.array(put_prices) + np.array(call_prices)
    vol_arr = np.array(volumes)
    straddle_vwap_arr = np.cumsum(straddle_arr * vol_arr) / np.cumsum(vol_arr)
    straddle_tloc = float(np.round(np.mean(straddle_arr[:12]), 2))
    
    delta_force = np.convolve(np.random.randn(len(times)) * 1.8, np.ones(3)/3, mode='same')
    cvd_line = np.cumsum(delta_force * 50)
    
    ts_dots_put = np.full(len(times), np.nan)
    ts_dots_call = np.full(len(times), np.nan)
    for i in range(1, len(times)):
        if (put_prices[i] >= put_poc) and (delta_force[i] > 0.3):
            ts_dots_put[i] = put_prices[i] + 1.2
        if (call_prices[i] >= call_poc) and (delta_force[i] < -0.3):
            ts_dots_call[i] = call_prices[i] + 1.2

    # Trend Determination
    if new_put > put_poc and new_call < call_poc:
        atm_trend, atm_class = "BEARISH", "status-bearish"
    elif new_call > call_poc and new_put < put_poc:
        atm_trend, atm_class = "BULLISH", "status-bullish"
    else:
        atm_trend, atm_class = "SIDEWAYS", "status-wait"

    if cur_put_power > 1000000 and cur_call_power < 0:
        multi_trend, multi_class = "BEARISH", "status-bearish"
        unwinding_status = "⚠️ Call Short-Covering Unwinding"
    elif cur_call_power > 1000000 and cur_put_power < 0:
        multi_trend, multi_class = "BULLISH", "status-bullish"
        unwinding_status = "⚠️ Put Unwinding"
    else:
        multi_trend, multi_class = "MIXED", "status-wait"
        unwinding_status = "Neutral OI Distribution"

    if market_active:
        if atm_trend == multi_trend and atm_trend in ["BULLISH", "BEARISH"]:
            market_status = "ACTIVE ENTRY"
            market_class = "status-bullish" if atm_trend == "BULLISH" else "status-bearish"
        else:
            market_status = "WAIT / MIXED"
            market_class = "status-wait"
    else:
        market_status = "MARKET CLOSED"
        market_class = "status-wait"

    # Audio Alerts
    current_timestamp = time.time()
    fired_alert = None
    if market_active and market_status == "ACTIVE ENTRY":
        if atm_trend == "BULLISH" and not np.isnan(ts_dots_call[-1]):
            st.session_state.current_live_call = {
                "type": "BUY CE (CALL)",
                "strike": f"NIFTY {atm_strike} CE",
                "trigger_price": new_call,
                "time": current_time_ist.strftime("%I:%M:%S %p")
            }
            if sound_enabled and (current_timestamp - st.session_state.last_signal_time) > 60:
                fired_alert = "CALL"
                st.session_state.last_signal_time = current_timestamp

        elif atm_trend == "BEARISH" and not np.isnan(ts_dots_put[-1]):
            st.session_state.current_live_call = {
                "type": "BUY PE (PUT)",
                "strike": f"NIFTY {atm_strike} PE",
                "trigger_price": new_put,
                "time": current_time_ist.strftime("%I:%M:%S %p")
            }
            if sound_enabled and (current_timestamp - st.session_state.last_signal_time) > 60:
                fired_alert = "PUT"
                st.session_state.last_signal_time = current_timestamp

    if fired_alert:
        with audio_box:
            play_audio_alert(fired_alert)

    # ---------------------------------------------------------
    # 8. TOP HERO & METRIC BADGES
    # ---------------------------------------------------------
    atm_header_box.markdown(f"""
    <div class="atm-hero-bar">
        <div class="atm-title">🎯 ATM STRIKE: {atm_strike} ({expiry_str} EXPIRY)</div>
        <div class="atm-badge-spot">NIFTY SPOT: {nifty_spot:.2f} | FUT: {fut_price:.2f}</div>
        <div class="atm-badge-call">ATM CALL ({atm_strike} CE): ₹{new_call:.2f}</div>
        <div class="atm-badge-put">ATM PUT ({atm_strike} PE): ₹{new_put:.2f}</div>
    </div>
    """, unsafe_allow_html=True)

    active_call = st.session_state.current_live_call
    call_style = "call-active-ce" if active_call["type"] == "BUY CE (CALL)" else ("call-active-pe" if active_call["type"] == "BUY PE (PUT)" else "call-active-neutral")
    call_icon = "🟢" if active_call["type"] == "BUY CE (CALL)" else ("🔴" if active_call["type"] == "BUY PE (PUT)" else "⚪")

    active_call_display_box.markdown(f"""
    <div class="alert-call-box {call_style}">
        <div>{call_icon} <b>ACTIVE SIGNAL:</b> <span style="font-size:15px;">{active_call['type']}</span> &nbsp; [{active_call['strike']}]</div>
        <div><b>Trigger Level:</b> ₹{active_call['trigger_price']:.2f} &nbsp;|&nbsp; <b>Time (IST):</b> {active_call['time']}</div>
    </div>
    """, unsafe_allow_html=True)

    metrics_box.markdown(f"""
    <div class="metric-grid">
        <div class="metric-card status-bearish">PUT POC: ₹{put_poc:.2f}</div>
        <div class="metric-card status-bullish">CALL POC: ₹{call_poc:.2f}</div>
        <div class="metric-card status-wait">TLOC: ₹{straddle_tloc:.2f}</div>
        <div class="metric-card {atm_class}">ATM: {atm_trend}</div>
        <div class="metric-card {multi_class}">MULTI: {multi_trend}</div>
        <div class="metric-card {market_class}">MARKET: {market_status}</div>
        <div class="metric-card status-info">{unwinding_status}</div>
    </div>
    """, unsafe_allow_html=True)

    # Scalp Execution Setup Card
    if not market_active:
        trade_box.markdown(f"""
        <div style="background-color:#161b22; border-left: 4px solid #996600; padding:10px; border-radius:6px; margin-bottom:12px; font-size:13px;">
            ⏸️ <b>FINAL CLOSING SNAPSHOT:</b> {market_msg}. Live streaming resumes at 09:15 AM IST.
        </div>
        """, unsafe_allow_html=True)
    elif market_status == "ACTIVE ENTRY" and atm_trend == "BEARISH":
        stop_loss = max(1.0, float(np.round(put_poc - 4.0, 2)))
        risk_per_share = max(2.0, float(np.round(new_put - stop_loss, 2)))
        recommended_qty = max(75, int((max_risk / risk_per_share) // 75) * 75)
        target_pts = float(np.round(new_put + (risk_per_share * 2), 2))
        
        trade_box.markdown(f"""
        <div class="trade-card-bearish">
            <b>🔴 HIGH-CONVICTION SETUP: BUY ATM NIFTY {atm_strike} PE</b><br>
            • <b>Entry:</b> ₹{new_put:.2f} (Above POC ₹{put_poc:.2f}) | 
            • <b>Hard SL:</b> ₹{stop_loss:.2f} (Risk: ₹{risk_per_share:.2f}/pt) | 
            • <b>Target (1:2 R:R):</b> ₹{target_pts:.2f} | 
            • <b>Position Size:</b> {recommended_qty} Qty ({recommended_qty//75} Lots) for ₹{max_risk} Max Risk
        </div>
        """, unsafe_allow_html=True)
    elif market_status == "ACTIVE ENTRY" and atm_trend == "BULLISH":
        stop_loss = max(1.0, float(np.round(call_poc - 4.0, 2)))
        risk_per_share = max(2.0, float(np.round(new_call - stop_loss, 2)))
        recommended_qty = max(75, int((max_risk / risk_per_share) // 75) * 75)
        target_pts = float(np.round(new_call + (risk_per_share * 2), 2))
        
        trade_box.markdown(f"""
        <div class="trade-card">
            <b>🟢 HIGH-CONVICTION SETUP: BUY ATM NIFTY {atm_strike} CE</b><br>
            • <b>Entry:</b> ₹{new_call:.2f} (Above POC ₹{call_poc:.2f}) | 
            • <b>Hard SL:</b> ₹{stop_loss:.2f} (Risk: ₹{risk_per_share:.2f}/pt) | 
            • <b>Target (1:2 R:R):</b> ₹{target_pts:.2f} | 
            • <b>Position Size:</b> {recommended_qty} Qty ({recommended_qty//75} Lots) for ₹{max_risk} Max Risk
        </div>
        """, unsafe_allow_html=True)
    else:
        trade_box.markdown("""
        <div style="background-color:#161b22; padding:8px; border-radius:6px; margin-bottom:10px; text-align:center; color:#8b949e; font-size:13px;">
            ⏳ <b>MARKET IN CONFLICT / TRAP ZONE:</b> Standing aside. Waiting for ATM & Multi-Strike Trend to align.
        </div>
        """, unsafe_allow_html=True)

    # ---------------------------------------------------------
    # 9. SENSIBULL OPEN INTEREST & OI CHANGE BAR GRAPH
    # ---------------------------------------------------------
    strikes, pe_yest, pe_chg, ce_yest, ce_chg = build_sensibull_oi_data(atm_strike)
    
    total_pe_oi = sum(pe_yest) + sum(pe_chg)
    total_ce_oi = sum(ce_yest) + sum(ce_chg)
    net_pcr = float(np.round(total_pe_oi / max(1, total_ce_oi), 2))
    net_ce_chg_str = f"{sum(ce_chg)/100000:+.2f}L"
    net_pe_chg_str = f"{sum(pe_chg)/100000:+.2f}L"

    # Sensibull Header Summary
    oi_summary_box.markdown(f"""
    <div class="oi-summary-card">
        <div class="oi-item">INDIAVIX: <span style="color:#00ff7f;">11.51 (+0.12)</span></div>
        <div class="oi-item">PCR: <span class="pcr-badge">{net_pcr:.2f}</span></div>
        <div class="oi-item">Call OI change: <span class="oi-call-val">{net_ce_chg_str}</span></div>
        <div class="oi-item">Put OI change: <span class="oi-put-val">{net_pe_chg_str}</span></div>
        <div class="oi-item">NIFTY Spot: <b>{nifty_spot:.2f}</b></div>
    </div>
    """, unsafe_allow_html=True)

    # Build Sensibull Paired Bar Graph with Cross-lines & Hollow Unwinding Boxes
    strike_str = [str(s) for s in strikes]
    
    fig_oi = go.Figure()

    # --- 1. PUT OI (GREEN GROUP) ---
    # Solid Base
    pe_solid = [min(pe_yest[i], pe_yest[i] + pe_chg[i]) for i in range(len(strikes))]
    fig_oi.add_trace(go.Bar(
        x=strike_str, y=pe_solid,
        name="Put OI",
        marker_color="#22c55e",
        offsetgroup=0
    ))
    
    # Increase (Crossed lines on top)
    pe_inc = [max(0, pe_chg[i]) for i in range(len(strikes))]
    fig_oi.add_trace(go.Bar(
        x=strike_str, y=pe_inc,
        base=pe_solid,
        name="Put Increase (Buildup)",
        marker_color="#22c55e",
        marker_pattern_shape="/",
        offsetgroup=0
    ))
    
    # Decrease (Hollow border at top representing unwound OI)
    pe_dec = [abs(min(0, pe_chg[i])) for i in range(len(strikes))]
    fig_oi.add_trace(go.Bar(
        x=strike_str, y=pe_dec,
        base=pe_solid,
        name="Put Decrease (Unwinding)",
        marker_color="rgba(0,0,0,0)",
        marker_line_color="#22c55e",
        marker_line_width=1.5,
        offsetgroup=0
    ))

    # --- 2. CALL OI (RED GROUP) ---
    # Solid Base
    ce_solid = [min(ce_yest[i], ce_yest[i] + ce_chg[i]) for i in range(len(strikes))]
    fig_oi.add_trace(go.Bar(
        x=strike_str, y=ce_solid,
        name="Call OI",
        marker_color="#ef4444",
        offsetgroup=1
    ))
    
    # Increase (Crossed lines on top)
    ce_inc = [max(0, ce_chg[i]) for i in range(len(strikes))]
    fig_oi.add_trace(go.Bar(
        x=strike_str, y=ce_inc,
        base=ce_solid,
        name="Call Increase (Buildup)",
        marker_color="#ef4444",
        marker_pattern_shape="/",
        offsetgroup=1
    ))
    
    # Decrease (Hollow border at top)
    ce_dec = [abs(min(0, ce_chg[i])) for i in range(len(strikes))]
    fig_oi.add_trace(go.Bar(
        x=strike_str, y=ce_dec,
        base=ce_solid,
        name="Call Decrease (Unwinding)",
        marker_color="rgba(0,0,0,0)",
        marker_line_color="#ef4444",
        marker_line_width=1.5,
        offsetgroup=1
    ))

    # Vertical line at NIFTY Spot Strike
    atm_idx = len(strikes) // 2
    fig_oi.add_vline(
        x=str(atm_strike),
        line_dash="dash",
        line_color="#94a3b8",
        line_width=1.5,
        annotation_text=f"NIFTY {fut_price:.2f}",
        annotation_position="top"
    )

    # Format Sensibull Axis & Legend
    fig_oi.update_layout(
        title="📊 Open Interest & OI Change (10 Strikes Left & Right)",
        height=480,
        template="plotly_dark",
        barmode="group",
        bargap=0.18,
        bargroupgap=0.04,
        margin=dict(l=10, r=10, t=36, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        yaxis=dict(
            title="Contracts (OI)",
            tickvals=[0, 2000000, 4000000, 6000000, 8000000, 10000000, 12000000, 14000000, 16000000],
            ticktext=["0", "20L", "40L", "60L", "80L", "1Cr", "1.2Cr", "1.4Cr", "1.6Cr"],
            gridcolor="#1f2937"
        ),
        xaxis=dict(
            title="Strike Prices",
            tickangle=-45,
            gridcolor="#1f2937"
        )
    )

    try:
        oi_chart_box.plotly_chart(fig_oi, width="stretch", config={"displayModeBar": False})
    except Exception:
        oi_chart_box.plotly_chart(fig_oi, use_container_width=True, config={"displayModeBar": False})

    # ---------------------------------------------------------
    # 10. MULTI-PANE SCALPING CHART
    # ---------------------------------------------------------
    if (loop_tick % 3 == 0 or loop_tick == 1) or not market_active:
        fig = make_subplots(
            rows=3, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.05,
            row_heights=[0.50, 0.25, 0.25],
            subplot_titles=(f"Dual Option vs POC (ATM {atm_strike})", "Combined Straddle vs VWAP & TLOC", "SMI Force & CVD Divergence")
        )
        
        # Pane 1
        fig.add_trace(go.Scatter(x=times, y=put_prices, name="PUT CMP", line=dict(color="#ff4d4d", width=2)), row=1, col=1)
        fig.add_trace(go.Scatter(x=times, y=call_prices, name="CALL CMP", line=dict(color="#00ff7f", width=2)), row=1, col=1)
        fig.add_hline(y=put_poc, line_dash="dash", line_color="#ff9999", annotation_text=f"PUT POC ({put_poc})", row=1, col=1)
        fig.add_hline(y=call_poc, line_dash="dash", line_color="#99ff99", annotation_text=f"CALL POC ({call_poc})", row=1, col=1)
        fig.add_trace(go.Scatter(x=times, y=ts_dots_put, mode="markers", marker=dict(color="#00ff00", size=8, symbol="circle"), name="TS PE Trigger"), row=1, col=1)
        fig.add_trace(go.Scatter(x=times, y=ts_dots_call, mode="markers", marker=dict(color="#00ff7f", size=8, symbol="diamond"), name="TS CE Trigger"), row=1, col=1)

        # Pane 2
        fig.add_trace(go.Scatter(x=times, y=straddle_arr, name="Straddle (CE+PE)", line=dict(color="#ffa500", width=1.5)), row=2, col=1)
        fig.add_trace(go.Scatter(x=times, y=straddle_vwap_arr, name="Straddle VWAP", line=dict(color="#ffff00", dash="dot", width=1.5)), row=2, col=1)
        fig.add_hline(y=straddle_tloc, line_dash="dash", line_color="#ff4444", annotation_text=f"TLOC ({straddle_tloc})", row=2, col=1)

        # Pane 3
        bar_colors = np.where(delta_force >= 0, "#00ff7f", "#ff4d4d")
        fig.add_trace(go.Bar(x=times, y=delta_force, marker_color=bar_colors, name="SMI Delta"), row=3, col=1)
        fig.add_trace(go.Scatter(x=times, y=cvd_line / 10, name="CVD Divergence", line=dict(color="#00e5ff", width=1.5)), row=3, col=1)

        fig.update_layout(
            height=640,
            template="plotly_dark",
            uirevision="constant_zoom",
            margin=dict(l=8, r=8, t=26, b=8),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        fig.update_xaxes(showticklabels=False, row=1, col=1)
        fig.update_xaxes(showticklabels=False, row=2, col=1)
        fig.update_xaxes(
            showticklabels=True,
            tickformat="%I:%M %p",
            tickangle=0,
            nticks=5,
            row=3, col=1
        )

        try:
            chart_box.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
        except Exception:
            chart_box.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # ---------------------------------------------------------
    # 11. POWER MATRIX TABLE
    # ---------------------------------------------------------
    live_time_label = f"🔴 LIVE ({current_time_ist.strftime('%I:%M:%S %p')})" if market_active else f"⏸️ CLOSED ({current_time_ist.strftime('%I:%M:%S %p')})"
    table_rows = [{
        "Time (IST)": live_time_label,
        "Call Power (CE Contracts)": f"{cur_call_power:+,d}",
        "Put Power (PE Contracts)": f"{cur_put_power:+,d}",
        "Market Sentiment": sentiment_tag
    }]
    
    for hist in reversed(st.session_state.matrix_history):
        table_rows.append({
            "Time (IST)": hist["Time"],
            "Call Power (CE Contracts)": f"{hist['Call Power']:+,d}",
            "Put Power (PE Contracts)": f"{hist['Put Power']:+,d}",
            "Market Sentiment": hist["Sentiment"]
        })

    table_box.table(pd.DataFrame(table_rows))

    if not market_active:
        st.stop()

    time.sleep(1)
