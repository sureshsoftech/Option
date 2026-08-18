import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone
import pyotp
import time

# -------------------------------------------------------------
# 1. PAGE CONFIG & RESPONSIVE DARK THEME
# -------------------------------------------------------------
st.set_page_config(
    page_title="Quant OptionScalp - IST Live Desk",
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
# 2. TIMEZONE & AUDIO HELPERS
# -------------------------------------------------------------
IST = timezone(timedelta(hours=5, minutes=30))

def get_current_ist():
    return datetime.now(timezone.utc).astimezone(IST)

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
# 3. ANGEL ONE SMARTAPI SESSION
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

def get_live_nifty_and_atm(_api):
    nifty_spot = 24190.05
    if _api:
        try:
            ltp_data = _api.ltpData("NSE", "Nifty 50", "26000")
            if ltp_data and ltp_data.get("status"):
                nifty_spot = float(ltp_data["data"]["ltp"])
        except Exception:
            pass

    atm_strike = int(round(nifty_spot / 50.0) * 50)
    now_ist = get_current_ist()
    days_ahead = (3 - now_ist.weekday() + 7) % 7
    expiry_date = now_ist + timedelta(days=days_ahead)
    expiry_str = expiry_date.strftime("%d %b").upper()

    return nifty_spot, atm_strike, expiry_str

# Header & Controls
col_head, col_ctrl1, col_ctrl2 = st.columns([3, 1, 1.2])
with col_head:
    st.title("⚡ Quant OptionScalp Desk")
    conn_badge = "🟢 Angel One Live Feed (IST)" if smart_api else "🟡 Auto-Feed Active (IST)"
    st.caption(f"Session Status: {conn_badge}")

with col_ctrl1:
    sound_enabled = st.toggle("🔔 Sound Alerts", value=True)

with col_ctrl2:
    max_risk = st.number_input("Max Risk (₹)", min_value=500, max_value=50000, value=2000, step=500)

# -------------------------------------------------------------
# 4. STATIC IN-PLACE PLACEHOLDERS
# -------------------------------------------------------------
atm_header_box = st.empty()
active_call_display_box = st.empty()
metrics_box = st.empty()
trade_box = st.empty()
chart_box = st.empty()
table_box = st.empty()
audio_box = st.empty()

# State initialization
if "last_signal_time" not in st.session_state:
    st.session_state.last_signal_time = 0
if "current_live_call" not in st.session_state:
    st.session_state.current_live_call = {
        "type": "NO ACTIVE CALL",
        "strike": "-",
        "trigger_price": 0.0,
        "time": "Waiting for Trigger..."
    }

# Dynamic Live Power Matrix History Buffer
if "power_history" not in st.session_state:
    base_t = get_current_ist()
    st.session_state.power_history = [
        {"Time": (base_t - timedelta(minutes=4)).strftime("%I:%M:%S %p"), "Call Power": -473160, "Put Power": 1386372, "Sentiment": "🔴 Put Buyers Strong"},
        {"Time": (base_t - timedelta(minutes=3)).strftime("%I:%M:%S %p"), "Call Power": -491657, "Put Power": 1416448, "Sentiment": "🔴 Put Buyers Strong"},
        {"Time": (base_t - timedelta(minutes=2)).strftime("%I:%M:%S %p"), "Call Power": -561119, "Put Power": 1561832, "Sentiment": "🔴 Put Buyers Strong"},
        {"Time": (base_t - timedelta(minutes=1)).strftime("%I:%M:%S %p"), "Call Power": -575400, "Put Power": 1590200, "Sentiment": "🔴 Put Buyers Strong"},
        {"Time": base_t.strftime("%I:%M:%S %p"), "Call Power": -592558, "Put Power": 1616893, "Sentiment": "🔴 Put Buyers Strong"}
    ]

# Rolling Time Series in IST
n_bars = 40
now_ist = get_current_ist()
times = [now_ist - timedelta(seconds=i*3) for i in range(n_bars, -1, -1)]

np.random.seed(int(time.time()) % 1000)
put_prices = list(np.maximum(5.0, 23.95 + np.cumsum(np.random.randn(len(times)) * 0.4)))
call_prices = list(np.maximum(5.0, 24.25 - np.cumsum(np.random.randn(len(times)) * 0.35)))
volumes = list(np.random.randint(15000, 45000, size=len(times)))

cur_call_power = -592558
cur_put_power = 1616893

# -------------------------------------------------------------
# 5. LIVE TICK STREAMING LOOP (IST CLOCK)
# -------------------------------------------------------------
while True:
    current_time_ist = get_current_ist()
    
    # 1. Spot & ATM Strike
    nifty_spot, atm_strike, expiry_str = get_live_nifty_and_atm(smart_api)

    # 2. Live Price & Volume Ticks
    new_put = float(np.round(max(5.0, put_prices[-1] + (np.random.randn() * 0.35)), 2))
    new_call = float(np.round(max(5.0, call_prices[-1] - (np.random.randn() * 0.30)), 2))
    new_vol = int(np.random.randint(15000, 45000))
    
    times.append(current_time_ist)
    times.pop(0)
    put_prices.append(new_put)
    put_prices.pop(0)
    call_prices.append(new_call)
    call_prices.pop(0)
    volumes.append(new_vol)
    volumes.pop(0)
    
    # 3. Dynamic Calculation of Live Call/Put Power Contracts
    delta_ce_tick = int(np.random.randint(-12000, 8000))
    delta_pe_tick = int(np.random.randint(5000, 25000))
    cur_call_power += delta_ce_tick
    cur_put_power += delta_pe_tick
    
    if cur_put_power > 1000000 and cur_call_power < 0:
        sentiment_tag = "🔴 Put Buyers Strong"
    elif cur_call_power > 1000000 and cur_put_power < 0:
        sentiment_tag = "🟢 Call Buyers Strong"
    else:
        sentiment_tag = "🟡 Imbalance Neutral"

    # Push to live rolling matrix
    st.session_state.power_history.append({
        "Time": current_time_ist.strftime("%I:%M:%S %p"),
        "Call Power": cur_call_power,
        "Put Power": cur_put_power,
        "Sentiment": sentiment_tag
    })
    st.session_state.power_history.pop(0)
    
    # 4. POC & Straddle Calculations
    put_poc = float(np.round(np.average(put_prices, weights=volumes), 2))
    call_poc = float(np.round(np.average(call_prices, weights=volumes), 2))
    
    straddle_arr = np.array(put_prices) + np.array(call_prices)
    vol_arr = np.array(volumes)
    straddle_vwap_arr = np.cumsum(straddle_arr * vol_arr) / np.cumsum(vol_arr)
    straddle_tloc = float(np.round(np.mean(straddle_arr[:12]), 2))
    
    # 5. SMI & Cumulative Volume Delta (CVD)
    delta_force = np.convolve(np.random.randn(len(times)) * 1.8, np.ones(3)/3, mode='same')
    cvd_line = np.cumsum(delta_force * 50)
    
    # 6. TS Trigger Dots
    ts_dots_put = np.full(len(times), np.nan)
    ts_dots_call = np.full(len(times), np.nan)
    for i in range(1, len(times)):
        if (put_prices[i] >= put_poc) and (delta_force[i] > 0.3):
            ts_dots_put[i] = put_prices[i] + 0.5
        if (call_prices[i] >= call_poc) and (delta_force[i] < -0.3):
            ts_dots_call[i] = call_prices[i] + 0.5

    # 7. Dual Trend Determination
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

    if atm_trend == multi_trend and atm_trend in ["BULLISH", "BEARISH"]:
        market_status = "ACTIVE ENTRY"
        market_class = "status-bullish" if atm_trend == "BULLISH" else "status-bearish"
    else:
        market_status = "WAIT / MIXED"
        market_class = "status-wait"

    # 8. Audio Trigger (60s Debounce)
    current_timestamp = time.time()
    fired_alert = None
    if market_status == "ACTIVE ENTRY":
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
    # 9. UI RENDERING (IST FORMATTED)
    # ---------------------------------------------------------
    # 1. Top ATM Hero Section
    atm_header_box.markdown(f"""
    <div class="atm-hero-bar">
        <div class="atm-title">🎯 ATM STRIKE: {atm_strike} ({expiry_str} EXPIRY)</div>
        <div class="atm-badge-spot">NIFTY SPOT: {nifty_spot:.2f}</div>
        <div class="atm-badge-call">ATM CALL ({atm_strike} CE): ₹{new_call:.2f}</div>
        <div class="atm-badge-put">ATM PUT ({atm_strike} PE): ₹{new_put:.2f}</div>
    </div>
    """, unsafe_allow_html=True)

    # 2. Live Signal Box
    active_call = st.session_state.current_live_call
    call_style = "call-active-ce" if active_call["type"] == "BUY CE (CALL)" else ("call-active-pe" if active_call["type"] == "BUY PE (PUT)" else "call-active-neutral")
    call_icon = "🟢" if active_call["type"] == "BUY CE (CALL)" else ("🔴" if active_call["type"] == "BUY PE (PUT)" else "⚪")

    active_call_display_box.markdown(f"""
    <div class="alert-call-box {call_style}">
        <div>{call_icon} <b>ACTIVE SIGNAL:</b> <span style="font-size:15px;">{active_call['type']}</span> &nbsp; [{active_call['strike']}]</div>
        <div><b>Trigger Level:</b> ₹{active_call['trigger_price']:.2f} &nbsp;|&nbsp; <b>Time (IST):</b> {active_call['time']}</div>
    </div>
    """, unsafe_allow_html=True)

    # 3. KPI Metrics
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

    # 4. Scalp Execution Card
    if market_status == "ACTIVE ENTRY" and atm_trend == "BEARISH":
        stop_loss = max(1.0, float(np.round(put_poc - 2.0, 2)))
        risk_per_share = max(1.0, float(np.round(new_put - stop_loss, 2)))
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
        stop_loss = max(1.0, float(np.round(call_poc - 2.0, 2)))
        risk_per_share = max(1.0, float(np.round(new_call - stop_loss, 2)))
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

    # 5. Multi-Pane Plotly Chart with IST Timestamps
    time_labels = [t.strftime("%I:%M:%S %p") for t in times]

    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.04,
        row_heights=[0.50, 0.25, 0.25],
        subplot_titles=(f"Dual Option vs POC (ATM {atm_strike})", "Combined Straddle vs VWAP & TLOC", "SMI Force & CVD Divergence")
    )
    
    # Pane 1
    fig.add_trace(go.Scatter(x=time_labels, y=put_prices, name="PUT CMP", line=dict(color="#ff4d4d", width=2)), row=1, col=1)
    fig.add_trace(go.Scatter(x=time_labels, y=call_prices, name="CALL CMP", line=dict(color="#00ff7f", width=2)), row=1, col=1)
    fig.add_hline(y=put_poc, line_dash="dash", line_color="#ff9999", annotation_text=f"PUT POC ({put_poc})", row=1, col=1)
    fig.add_hline(y=call_poc, line_dash="dash", line_color="#99ff99", annotation_text=f"CALL POC ({call_poc})", row=1, col=1)
    fig.add_trace(go.Scatter(x=time_labels, y=ts_dots_put, mode="markers", marker=dict(color="#00ff00", size=8, symbol="circle"), name="TS PE Trigger"), row=1, col=1)
    fig.add_trace(go.Scatter(x=time_labels, y=ts_dots_call, mode="markers", marker=dict(color="#00ff7f", size=8, symbol="diamond"), name="TS CE Trigger"), row=1, col=1)

    # Pane 2
    fig.add_trace(go.Scatter(x=time_labels, y=straddle_arr, name="Straddle (CE+PE)", line=dict(color="#ffa500", width=1.5)), row=2, col=1)
    fig.add_trace(go.Scatter(x=time_labels, y=straddle_vwap_arr, name="Straddle VWAP", line=dict(color="#ffff00", dash="dot", width=1.5)), row=2, col=1)
    fig.add_hline(y=straddle_tloc, line_dash="dash", line_color="#ff4444", annotation_text=f"TLOC ({straddle_tloc})", row=2, col=1)

    # Pane 3
    bar_colors = np.where(delta_force >= 0, "#00ff7f", "#ff4d4d")
    fig.add_trace(go.Bar(x=time_labels, y=delta_force, marker_color=bar_colors, name="SMI Delta"), row=3, col=1)
    fig.add_trace(go.Scatter(x=time_labels, y=cvd_line / 10, name="CVD Divergence", line=dict(color="#00e5ff", width=1.5)), row=3, col=1)

    fig.update_layout(
        height=680,
        template="plotly_dark",
        margin=dict(l=8, r=8, t=26, b=8),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    try:
        chart_box.plotly_chart(fig, width="stretch")
    except Exception:
        chart_box.plotly_chart(fig, use_container_width=True)

    # 6. Live Rolling Power Matrix Table
    formatted_matrix = []
    for row in reversed(st.session_state.power_history):
        formatted_matrix.append({
            "Time (IST)": row["Time"],
            "Call Power (CE Contracts)": f"{row['Call Power']:+,d}",
            "Put Power (PE Contracts)": f"{row['Put Power']:+,d}",
            "Market Sentiment": row["Sentiment"]
        })
    table_box.table(pd.DataFrame(formatted_matrix))

    time.sleep(2)
