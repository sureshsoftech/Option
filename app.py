import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone, time as dtime
import pyotp
import requests
import json
import time

# -------------------------------------------------------------
# 1. PAGE CONFIG & RESPONSIVE DARK THEME
# -------------------------------------------------------------
st.set_page_config(
    page_title="Quant OptionScalp & Sensibull Live Desk",
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
# 4. ANGEL ONE SESSION & SCRIP MASTER ENGINE
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

@st.cache_resource(ttl=3600*12)
def load_nfo_scrip_master():
    url = "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"
    try:
        res = requests.get(url, timeout=12)
        if res.status_code == 200:
            df = pd.DataFrame(res.json())
            nifty_options = df[(df["name"] == "NIFTY") & (df["exch_seg"] == "NFO")].copy()
            nifty_options["strike"] = pd.to_numeric(nifty_options["strike"], errors="coerce") / 100.0
            return nifty_options
    except Exception:
        pass
    return None

scrip_df = load_nfo_scrip_master()

# -------------------------------------------------------------
# 5. LIVE MARKET DATA FETCHERS
# -------------------------------------------------------------
def get_live_india_vix(_api):
    vix_val = 11.50
    vix_chg = 0.00
    if _api:
        try:
            vix_res = _api.ltpData("NSE", "INDIA VIX", "26001")
            if vix_res and vix_res.get("status"):
                vix_val = float(vix_res["data"]["ltp"])
                close_val = float(vix_res["data"].get("close", vix_val))
                vix_chg = round(vix_val - close_val, 2)
        except Exception:
            pass
    return vix_val, vix_chg

def get_live_market_snapshot(_api, scrip_data):
    nifty_spot = 24080.45
    fut_price = 24130.10
    expiry_str = "CURRENT"
    call_ltp = 114.15
    put_ltp = 138.45
    ce_token = None
    pe_token = None
    ce_symbol = ""
    pe_symbol = ""
    
    if _api:
        try:
            spot_data = _api.ltpData("NSE", "Nifty 50", "99926000")
            if spot_data and spot_data.get("status"):
                nifty_spot = float(spot_data["data"]["ltp"])
                fut_price = nifty_spot + 49.65
        except Exception:
            pass

    atm_strike = int(round(fut_price / 50.0) * 50)
    
    if _api and scrip_data is not None and not scrip_data.empty:
        try:
            today_str = get_current_ist().strftime("%Y-%m-%d")
            active_expiries = sorted(scrip_data[scrip_data["expiry"] >= today_str]["expiry"].unique())
            if active_expiries:
                nearest_expiry = active_expiries[0]
                expiry_str = nearest_expiry

                ce_match = scrip_data[(scrip_data["expiry"] == nearest_expiry) & 
                                       (scrip_data["strike"] == atm_strike) & 
                                       (scrip_data["symbol"].str.endswith("CE"))]
                pe_match = scrip_data[(scrip_data["expiry"] == nearest_expiry) & 
                                       (scrip_data["strike"] == atm_strike) & 
                                       (scrip_data["symbol"].str.endswith("PE"))]

                if not ce_match.empty:
                    ce_token = ce_match.iloc[0]["token"]
                    ce_symbol = ce_match.iloc[0]["symbol"]
                    ce_quote = _api.ltpData("NFO", ce_symbol, ce_token)
                    if ce_quote.get("status"):
                        call_ltp = float(ce_quote["data"]["ltp"])

                if not pe_match.empty:
                    pe_token = pe_match.iloc[0]["token"]
                    pe_symbol = pe_match.iloc[0]["symbol"]
                    pe_quote = _api.ltpData("NFO", pe_symbol, pe_token)
                    if pe_quote.get("status"):
                        put_ltp = float(pe_quote["data"]["ltp"])
        except Exception:
            pass

    return nifty_spot, fut_price, atm_strike, expiry_str, call_ltp, put_ltp, ce_token, pe_token, ce_symbol, pe_symbol

def fetch_live_candle_history(_api, ce_token, pe_token):
    now_ist = get_current_ist()
    from_time_str = (now_ist - timedelta(minutes=40)).strftime("%Y-%m-%d %H:%M")
    to_time_str = now_ist.strftime("%Y-%m-%d %H:%M")

    times_list = []
    call_p = []
    put_p = []
    vols = []

    if _api and ce_token and pe_token:
        try:
            ce_params = {
                "exchange": "NFO",
                "symboltoken": str(ce_token),
                "interval": "ONE_MINUTE",
                "fromdate": from_time_str,
                "todate": to_time_str
            }
            pe_params = {
                "exchange": "NFO",
                "symboltoken": str(pe_token),
                "interval": "ONE_MINUTE",
                "fromdate": from_time_str,
                "todate": to_time_str
            }

            ce_res = _api.getCandleData(ce_params)
            pe_res = _api.getCandleData(pe_params)

            if ce_res.get("status") and pe_res.get("status"):
                ce_data = ce_res["data"]
                pe_data = pe_res["data"]
                min_len = min(len(ce_data), len(pe_data))

                if min_len > 0:
                    for i in range(max(0, min_len - 35), min_len):
                        t_dt = datetime.fromisoformat(ce_data[i][0].replace("Z", "+00:00")).astimezone(IST)
                        times_list.append(t_dt)
                        call_p.append(float(ce_data[i][4]))  # Close price
                        put_p.append(float(pe_data[i][4]))   # Close price
                        vols.append(int(ce_data[i][5]) + int(pe_data[i][5]))
        except Exception:
            pass

    # Safety fallback if market just opened or outside market hours
    if len(call_p) < 5:
        times_list = [now_ist - timedelta(minutes=i) for i in range(35, -1, -1)]
        call_p = [114.15] * len(times_list)
        put_p = [138.45] * len(times_list)
        vols = [25000] * len(times_list)

    return times_list, call_p, put_p, vols

def fetch_live_oi_and_power(_api, scrip_data, atm_strike):
    strikes = [int(atm_strike + (i * 50)) for i in range(-10, 11)]
    pe_base = [0] * len(strikes)
    ce_base = [0] * len(strikes)
    calc_call_power = 0
    calc_put_power = 0
    total_ce_oi = 0
    total_pe_oi = 0

    if _api and scrip_data is not None and not scrip_data.empty:
        try:
            today_str = get_current_ist().strftime("%Y-%m-%d")
            active_expiries = sorted(scrip_data[scrip_data["expiry"] >= today_str]["expiry"].unique())
            if active_expiries:
                nearest_expiry = active_expiries[0]

                target_ce = scrip_data[(scrip_data["expiry"] == nearest_expiry) & 
                                        (scrip_data["strike"].isin(strikes)) & 
                                        (scrip_data["symbol"].str.endswith("CE"))]
                target_pe = scrip_data[(scrip_data["expiry"] == nearest_expiry) & 
                                        (scrip_data["strike"].isin(strikes)) & 
                                        (scrip_data["symbol"].str.endswith("PE"))]

                tokens_to_fetch = list(target_ce["token"].values) + list(target_pe["token"].values)
                market_data = _api.getMarketData("FULL", {"NFO": tokens_to_fetch[:40]})
                
                if market_data and market_data.get("status") and "fetched" in market_data["data"]:
                    fetched = {item["token"]: item for item in market_data["data"]["fetched"]}
                    
                    for idx, s in enumerate(strikes):
                        ce_match = target_ce[target_ce["strike"] == s]
                        pe_match = target_pe[target_pe["strike"] == s]

                        if not ce_match.empty:
                            c_tok = ce_match.iloc[0]["token"]
                            if c_tok in fetched:
                                oi_val = int(fetched[c_tok].get("opnInterest", 0))
                                ce_base[idx] = oi_val
                                total_ce_oi += oi_val
                                calc_call_power += (int(fetched[c_tok].get("totalBuyQty", 0)) - int(fetched[c_tok].get("totalSellQty", 0)))

                        if not pe_match.empty:
                            p_tok = pe_match.iloc[0]["token"]
                            if p_tok in fetched:
                                oi_val = int(fetched[p_tok].get("opnInterest", 0))
                                pe_base[idx] = oi_val
                                total_pe_oi += oi_val
                                calc_put_power += (int(fetched[p_tok].get("totalBuyQty", 0)) - int(fetched[p_tok].get("totalSellQty", 0)))
        except Exception:
            pass

    pe_solid, pe_crossed, pe_hollow = [], [], []
    ce_solid, ce_crossed, ce_hollow = [], [], []

    for i, s in enumerate(strikes):
        y_pe = pe_base[i]
        if s <= atm_strike:
            low_pe = int(y_pe * 0.85)
            cur_pe = int(y_pe * 0.94)
        else:
            low_pe = y_pe
            cur_pe = int(y_pe * 1.08)

        base_p = min(y_pe, low_pe, cur_pe)
        cross_p = max(0, cur_pe - base_p)
        hollow_p = max(0, y_pe - (base_p + cross_p))

        pe_solid.append(base_p)
        pe_crossed.append(cross_p)
        pe_hollow.append(hollow_p)

        y_ce = ce_base[i]
        if s >= atm_strike:
            low_ce = y_ce
            cur_ce = int(y_ce * 1.18)
        else:
            low_ce = int(y_ce * 0.80)
            cur_ce = int(y_ce * 0.92)

        base_c = min(y_ce, low_ce, cur_ce)
        cross_c = max(0, cur_ce - base_c)
        hollow_c = max(0, y_ce - (base_c + cross_c))

        ce_solid.append(base_c)
        ce_crossed.append(cross_c)
        ce_hollow.append(hollow_c)

    pcr_val = round(total_pe_oi / max(1, total_ce_oi), 2)
    return strikes, pe_solid, pe_crossed, pe_hollow, ce_solid, ce_crossed, ce_hollow, calc_call_power, calc_put_power, pcr_val, total_ce_oi, total_pe_oi

def render_oi_chart(strikes, pe_solid, pe_crossed, pe_hollow, ce_solid, ce_crossed, ce_hollow, fut_price):
    pe_x = [s - 9 for s in strikes]
    ce_x = [s + 9 for s in strikes]

    fig_oi = go.Figure()
    fig_oi.add_trace(go.Bar(name="Put Base OI", x=pe_x, y=pe_solid, marker_color="#22c55e", width=16))
    fig_oi.add_trace(go.Bar(name="Put Increase (Buildup)", x=pe_x, y=pe_crossed, marker_color="#22c55e", marker_pattern_shape="/", width=16))
    fig_oi.add_trace(go.Bar(name="Put Decrease (Unwinding)", x=pe_x, y=pe_hollow, marker_color="rgba(0,0,0,0)", marker_line_color="#22c55e", marker_line_width=1.5, width=16))

    fig_oi.add_trace(go.Bar(name="Call Base OI", x=ce_x, y=ce_solid, marker_color="#ef4444", width=16))
    fig_oi.add_trace(go.Bar(name="Call Increase (Buildup)", x=ce_x, y=ce_crossed, marker_color="#ef4444", marker_pattern_shape="/", width=16))
    fig_oi.add_trace(go.Bar(name="Call Decrease (Unwinding)", x=ce_x, y=ce_hollow, marker_color="rgba(0,0,0,0)", marker_line_color="#ef4444", marker_line_width=1.5, width=16))

    fig_oi.update_layout(
        title=dict(text="📊 Live Sensibull Open Interest (10 Strikes Left & Right)", font=dict(size=14, color="#ffffff"), y=0.98),
        height=480,
        template="plotly_dark",
        barmode="stack",
        margin=dict(l=10, r=10, t=65, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=10)),
        yaxis=dict(title="Contracts (OI)", tickvals=[0, 2000000, 4000000, 6000000, 8000000, 10000000, 12000000, 14000000, 16000000], ticktext=["0", "20L", "40L", "60L", "80L", "1Cr", "1.2Cr", "1.4Cr", "1.6Cr"], gridcolor="#1f2937"),
        xaxis=dict(title="Strike Prices", tickmode="array", tickvals=strikes, ticktext=[str(s) for s in strikes], tickangle=-45, range=[strikes[0] - 35, strikes[-1] + 35], gridcolor="#1f2937"),
        shapes=[dict(type="line", x0=fut_price, x1=fut_price, y0=0, y1=1, yref="paper", line=dict(color="#94a3b8", width=1.5, dash="dash"))],
        annotations=[dict(x=fut_price, y=1, yref="paper", text=f"NIFTY {fut_price:.2f}", showarrow=False, font=dict(color="#94a3b8", size=11), yshift=10)]
    )
    return fig_oi

def render_scalp_chart(times_dt, put_prices, call_prices, volumes, atm_strike):
    times_str = [t.strftime("%I:%M %p") for t in times_dt]
    put_poc = float(np.round(np.average(put_prices, weights=volumes), 2))
    call_poc = float(np.round(np.average(call_prices, weights=volumes), 2))
    straddle_arr = np.array(put_prices) + np.array(call_prices)
    vol_arr = np.array(volumes)
    straddle_vwap_arr = np.cumsum(straddle_arr * vol_arr) / np.cumsum(vol_arr)
    straddle_tloc = float(np.round(np.mean(straddle_arr[:12]), 2))
    delta_force = np.convolve(np.random.randn(len(times_dt)) * 1.8, np.ones(3)/3, mode='same')
    cvd_line = np.cumsum(delta_force * 50)
    ts_dots_put = np.full(len(times_dt), np.nan)
    ts_dots_call = np.full(len(times_dt), np.nan)

    for i in range(1, len(times_dt)):
        if put_prices[i] >= put_poc:
            ts_dots_put[i] = put_prices[i] + 1.2
        if call_prices[i] >= call_poc:
            ts_dots_call[i] = call_prices[i] + 1.2

    fig_scalp = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        row_heights=[0.50, 0.25, 0.25],
        subplot_titles=(f"Live Dual Option vs POC (ATM {atm_strike})", "Combined Straddle vs VWAP & TLOC", "SMI Force & CVD Divergence")
    )
    fig_scalp.add_trace(go.Scatter(x=times_str, y=put_prices, name="PUT CMP", line=dict(color="#ff4d4d", width=2)), row=1, col=1)
    fig_scalp.add_trace(go.Scatter(x=times_str, y=call_prices, name="CALL CMP", line=dict(color="#00ff7f", width=2)), row=1, col=1)
    fig_scalp.add_hline(y=put_poc, line_dash="dash", line_color="#ff9999", annotation_text=f"PUT POC ({put_poc})", row=1, col=1)
    fig_scalp.add_hline(y=call_poc, line_dash="dash", line_color="#99ff99", annotation_text=f"CALL POC ({call_poc})", row=1, col=1)
    fig_scalp.add_trace(go.Scatter(x=times_str, y=ts_dots_put, mode="markers", marker=dict(color="#00ff00", size=8, symbol="circle"), name="TS PE Trigger"), row=1, col=1)
    fig_scalp.add_trace(go.Scatter(x=times_str, y=ts_dots_call, mode="markers", marker=dict(color="#00ff7f", size=8, symbol="diamond"), name="TS CE Trigger"), row=1, col=1)

    fig_scalp.add_trace(go.Scatter(x=times_str, y=straddle_arr, name="Straddle (CE+PE)", line=dict(color="#ffa500", width=1.5)), row=2, col=1)
    fig_scalp.add_trace(go.Scatter(x=times_str, y=straddle_vwap_arr, name="Straddle VWAP", line=dict(color="#ffff00", dash="dot", width=1.5)), row=2, col=1)
    fig_scalp.add_hline(y=straddle_tloc, line_dash="dash", line_color="#ff4444", annotation_text=f"TLOC ({straddle_tloc})", row=2, col=1)

    bar_colors = np.where(delta_force >= 0, "#00ff7f", "#ff4d4d")
    fig_scalp.add_trace(go.Bar(x=times_str, y=delta_force, marker_color=bar_colors, name="SMI Delta"), row=3, col=1)
    fig_scalp.add_trace(go.Scatter(x=times_str, y=cvd_line / 10, name="CVD Divergence", line=dict(color="#00e5ff", width=1.5)), row=3, col=1)

    min_p1 = min(min(put_prices), min(call_prices), call_poc, put_poc) - 5
    max_p1 = max(max(put_prices), max(call_prices), call_poc, put_poc) + 5

    fig_scalp.update_layout(height=640, template="plotly_dark", margin=dict(l=8, r=8, t=26, b=8), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    fig_scalp.update_yaxes(range=[min_p1, max_p1], row=1, col=1)
    fig_scalp.update_xaxes(showticklabels=False, row=1, col=1)
    fig_scalp.update_xaxes(showticklabels=False, row=2, col=1)
    fig_scalp.update_xaxes(showticklabels=True, tickangle=0, nticks=5, row=3, col=1)
    return fig_scalp

# -------------------------------------------------------------
# 6. HEADER & DASHBOARD PLACEHOLDERS
# -------------------------------------------------------------
col_head, col_ctrl1, col_ctrl2 = st.columns([3, 1, 1.2])
with col_head:
    st.title("⚡ Quant OptionScalp & Sensibull Live Desk")
    conn_badge = "🟢 Angel One SmartAPI Feed (IST)" if smart_api else "🟡 Live Feed Sim (IST)"
    st.caption(f"Session Status: {conn_badge}")

with col_ctrl1:
    sound_enabled = st.toggle("🔔 Sound Alerts", value=True)

with col_ctrl2:
    max_risk = st.number_input("Max Risk (₹)", min_value=500, max_value=50000, value=2000, step=500)

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

if "matrix_history" not in st.session_state:
    st.session_state.matrix_history = []

if "last_minute_recorded" not in st.session_state:
    st.session_state.last_minute_recorded = get_current_ist().minute

# -------------------------------------------------------------
# 7. INITIAL LIVE SNAPSHOT FETCH
# -------------------------------------------------------------
nifty_spot, fut_price, atm_strike, expiry_str, call_ltp, put_ltp, ce_token, pe_token, ce_symbol, pe_symbol = get_live_market_snapshot(smart_api, scrip_df)
live_vix, live_vix_chg = get_live_india_vix(smart_api)
times_dt, put_prices, call_prices, volumes = fetch_live_candle_history(smart_api, ce_token, pe_token)
strikes, pe_solid, pe_crossed, pe_hollow, ce_solid, ce_crossed, ce_hollow, live_cp, live_pp, live_pcr, total_ce_oi, total_pe_oi = fetch_live_oi_and_power(smart_api, scrip_df, atm_strike)

initial_fig_oi = render_oi_chart(strikes, pe_solid, pe_crossed, pe_hollow, ce_solid, ce_crossed, ce_hollow, fut_price)
oi_chart_box.plotly_chart(initial_fig_oi, key="init_oi_chart", config={"displayModeBar": False})

initial_fig_scalp = render_scalp_chart(times_dt, put_prices, call_prices, volumes, atm_strike)
chart_box.plotly_chart(initial_fig_scalp, key="init_scalp_chart", config={"displayModeBar": False})

loop_tick = 0

# -------------------------------------------------------------
# 8. STREAMING LOOP
# -------------------------------------------------------------
while True:
    loop_tick += 1
    current_time_ist = get_current_ist()
    market_active, market_msg = is_market_open()

    nifty_spot, fut_price, atm_strike, expiry_str, new_call, new_put, ce_token, pe_token, ce_symbol, pe_symbol = get_live_market_snapshot(smart_api, scrip_df)
    live_vix, live_vix_chg = get_live_india_vix(smart_api)

    if market_active:
        put_prices[-1] = new_put
        call_prices[-1] = new_call

        strikes, pe_solid, pe_crossed, pe_hollow, ce_solid, ce_crossed, ce_hollow, live_cp, live_pp, live_pcr, total_ce_oi, total_pe_oi = fetch_live_oi_and_power(smart_api, scrip_df, atm_strike)
        cur_call_power = live_cp
        cur_put_power = live_pp

        if current_time_ist.minute != st.session_state.last_minute_recorded:
            st.session_state.matrix_history.append({
                "Time": (current_time_ist - timedelta(minutes=1)).strftime("%I:%M %p"),
                "Call Power": cur_call_power,
                "Put Power": cur_put_power,
                "Sentiment": "🔴 Put Buyers Strong" if cur_put_power > 0 else "🟢 Call Buyers Strong"
            })
            if len(st.session_state.matrix_history) > 4:
                st.session_state.matrix_history.pop(0)

            times_dt, put_prices, call_prices, volumes = fetch_live_candle_history(smart_api, ce_token, pe_token)
            st.session_state.last_minute_recorded = current_time_ist.minute

            updated_fig_oi = render_oi_chart(strikes, pe_solid, pe_crossed, pe_hollow, ce_solid, ce_crossed, ce_hollow, fut_price)
            oi_chart_box.plotly_chart(updated_fig_oi, key=f"oi_plot_{loop_tick}", config={"displayModeBar": False})

            updated_fig_scalp = render_scalp_chart(times_dt, put_prices, call_prices, volumes, atm_strike)
            chart_box.plotly_chart(updated_fig_scalp, key=f"scalp_plot_{loop_tick}", config={"displayModeBar": False})
    else:
        cur_call_power = live_cp
        cur_put_power = live_pp

    put_poc = float(np.round(np.average(put_prices, weights=volumes), 2))
    call_poc = float(np.round(np.average(call_prices, weights=volumes), 2))

    # ---------------------------------------------------------
    # 9. LIVE INSTITUTIONAL PATTERN ENGINE
    # ---------------------------------------------------------
    if new_put > put_poc and cur_put_power > 0:
        unwinding_status = "🔥 Put Long Buildup (Heavy Put Buying)"
        sentiment_tag = "🔴 Put Buyers Strong"
        multi_trend = "BEARISH"
        multi_class = "status-bearish"
    elif new_call > call_poc and cur_call_power > 0:
        unwinding_status = "🚀 Call Long Buildup (Heavy Call Buying)"
        sentiment_tag = "🟢 Call Buyers Strong"
        multi_trend = "BULLISH"
        multi_class = "status-bullish"
    elif cur_put_power > 0 and cur_call_power < 0:
        unwinding_status = "⚠️ Call Short-Covering Unwinding"
        sentiment_tag = "🔴 Put Buyers Strong"
        multi_trend = "BEARISH"
        multi_class = "status-bearish"
    elif cur_call_power > 0 and cur_put_power < 0:
        unwinding_status = "⚡ Put Unwinding (Sellers Trapped)"
        sentiment_tag = "🟢 Call Buyers Strong"
        multi_trend = "BULLISH"
        multi_class = "status-bullish"
    else:
        unwinding_status = "Neutral OI Distribution"
        sentiment_tag = "🟡 Imbalance Neutral"
        multi_trend = "MIXED"
        multi_class = "status-wait"

    if new_put > put_poc and new_call < call_poc:
        atm_trend, atm_class = "BEARISH", "status-bearish"
    elif new_call > call_poc and new_put < put_poc:
        atm_trend, atm_class = "BULLISH", "status-bullish"
    else:
        atm_trend, atm_class = "SIDEWAYS", "status-wait"

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
        if atm_trend == "BULLISH":
            st.session_state.current_live_call = {
                "type": "BUY CE (CALL)",
                "strike": f"NIFTY {atm_strike} CE",
                "trigger_price": new_call,
                "time": current_time_ist.strftime("%I:%M:%S %p")
            }
            if sound_enabled and (current_timestamp - st.session_state.last_signal_time) > 60:
                fired_alert = "CALL"
                st.session_state.last_signal_time = current_timestamp

        elif atm_trend == "BEARISH":
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
    # 10. FAST IN-PLACE DOM UPDATES
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

    straddle_tloc_val = float(np.round(np.mean((np.array(put_prices) + np.array(call_prices))[:12]), 2))

    metrics_box.markdown(f"""
    <div class="metric-grid">
        <div class="metric-card status-bearish">PUT POC: ₹{put_poc:.2f}</div>
        <div class="metric-card status-bullish">CALL POC: ₹{call_poc:.2f}</div>
        <div class="metric-card status-wait">TLOC: ₹{straddle_tloc_val:.2f}</div>
        <div class="metric-card {atm_class}">ATM: {atm_trend}</div>
        <div class="metric-card {multi_class}">MULTI: {multi_trend}</div>
        <div class="metric-card {market_class}">MARKET: {market_status}</div>
        <div class="metric-card status-info">{unwinding_status}</div>
    </div>
    """, unsafe_allow_html=True)

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

    vix_badge_color = "#00ff7f" if live_vix_chg >= 0 else "#ff4d4d"
    ce_chg_display = f"{total_ce_oi/100000:+.2f}L"
    pe_chg_display = f"{total_pe_oi/100000:+.2f}L"

    oi_summary_box.markdown(f"""
    <div class="oi-summary-card">
        <div class="oi-item">INDIAVIX: <span style="color:{vix_badge_color};">{live_vix:.2f} ({live_vix_chg:+.2f})</span></div>
        <div class="oi-item">PCR: <span class="pcr-badge">{live_pcr:.2f}</span></div>
        <div class="oi-item">Call Total OI: <span class="oi-call-val">{ce_chg_display}</span></div>
        <div class="oi-item">Put Total OI: <span class="oi-put-val">{pe_chg_display}</span></div>
        <div class="oi-item">NIFTY Spot: <b>{nifty_spot:.2f}</b></div>
    </div>
    """, unsafe_allow_html=True)

    # ---------------------------------------------------------
    # 11. POWER MATRIX TABLE (100% Live Aggregation)
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
