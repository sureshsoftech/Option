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
import re

# -------------------------------------------------------------
# 1. PAGE CONFIG & RESPONSIVE DARK THEME
# -------------------------------------------------------------
st.set_page_config(
    page_title="SHK TRADE LABS",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    .stApp { background-color: #0b0e14; color: #ffffff; }
    * { transition: none !important; animation: none !important; }
    div[data-testid="stVerticalBlock"] > div { opacity: 1 !important; }
    .stSpinner, [data-testid="stStatusWidget"] { display: none !important; visibility: hidden !important; }

    ::-webkit-scrollbar { width: 14px !important; height: 14px !important; }
    ::-webkit-scrollbar-track { background: #11161f !important; border-left: 1px solid #30363d; }
    ::-webkit-scrollbar-thumb { background-color: #ffffff !important; border-radius: 7px !important; border: 2px solid #11161f !important; }
    ::-webkit-scrollbar-thumb:hover { background-color: #e2e8f0 !important; }
    html, body, [data-testid="stAppViewContainer"] { scrollbar-width: auto !important; scrollbar-color: #ffffff #11161f !important; }

    .top-price-box {
        background: linear-gradient(90deg, #161b22 0%, #1a2230 100%);
        border: 1px solid #30363d; border-radius: 8px; padding: 12px 16px;
        margin-bottom: 12px; display: flex; flex-direction: column; gap: 10px;
    }
    .top-price-row { display: flex; flex-direction: row; align-items: center; flex-wrap: wrap; gap: 12px; }
    .val-badge-neutral { background-color: #21262d; color: #e6edf3; padding: 6px 14px; border-radius: 6px; font-weight: 800; font-size: 15px; border: 1px solid #30363d; letter-spacing: 0.5px; }
    .val-badge-call { background-color: #006622; color: #ffffff; padding: 6px 16px; border-radius: 6px; font-weight: 800; font-size: 15px; letter-spacing: 0.5px; }
    .val-badge-put { background-color: #8b0000; color: #ffffff; padding: 6px 16px; border-radius: 6px; font-weight: 800; font-size: 15px; letter-spacing: 0.5px; }

    .oi-summary-card {
        background: #11161f; border: 1px solid #21262d; border-radius: 8px; padding: 10px 14px;
        margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;
    }
    .oi-item { font-size: 13px; font-weight: bold; }
    .oi-call-val { color: #ff5252; font-weight: 800; }
    .oi-put-val { color: #00e676; font-weight: 800; }
    .pcr-badge { background-color: #1f2937; padding: 4px 10px; border-radius: 5px; border: 1px solid #374151; font-weight: 800; color: #38bdf8; }

    .metric-grid { display: flex; flex-direction: row; gap: 6px; margin-bottom: 8px; flex-wrap: wrap; }
    .metric-card { flex: 1; min-width: 95px; padding: 7px 4px; border-radius: 6px; text-align: center; font-size: 12px; font-weight: bold; }

    .status-bullish { background-color: #006622; color: #ffffff; }
    .status-bearish { background-color: #8b0000; color: #ffffff; }
    .status-wait { background-color: #996600; color: #ffffff; }
    .status-info { background-color: #1f3a60; color: #ffffff; }
    .status-error { background-color: #4b0082; color: #ffffff; }

    .checkpoint-container { background: #11161f; border: 1px solid #21262d; border-radius: 8px; padding: 10px 14px; margin-top: 10px; margin-bottom: 12px; }
    .checkpoint-row { display: flex; justify-content: space-between; align-items: center; padding: 8px 4px; border-bottom: 1px solid #1f2937; font-size: 13px; font-weight: 600; gap: 10px; }
    .checkpoint-row:last-child { border-bottom: none; }
    .cp-val-text { color: #94a3b8; font-size: 12px; font-weight: 700; margin-right: 8px; }

    .badge-bullish-tag { background-color: #00ff7f; color: #000000; padding: 4px 10px; border-radius: 4px; font-weight: 800; font-size: 12px; letter-spacing: 0.5px; display: inline-block; text-align: center; white-space: nowrap; }
    .badge-bearish-tag { background-color: #ff3333; color: #ffffff; padding: 4px 10px; border-radius: 4px; font-weight: 800; font-size: 12px; letter-spacing: 0.5px; display: inline-block; text-align: center; white-space: nowrap; }
    .badge-neutral-tag { background-color: #4b5563; color: #ffffff; padding: 4px 10px; border-radius: 4px; font-weight: 700; font-size: 12px; display: inline-block; text-align: center; white-space: nowrap; }

    .touch-box-group { display: inline-flex; flex-direction: row; align-items: center; }
    .touch-left-green-box { background-color: #000000 !important; color: #ffffff !important; border-top: 2px solid #008000 !important; border-bottom: 2px solid #008000 !important; border-left: 2px solid #008000 !important; border-right: 1px solid #008000 !important; padding: 4px 12px; border-top-left-radius: 6px; border-bottom-left-radius: 6px; font-weight: 900; font-size: 20px; text-align: center; min-width: 44px; line-height: 1.1; }
    .touch-left-green-highlight { background-color: #008000 !important; color: #000000 !important; border-top: 2px solid #008000 !important; border-bottom: 2px solid #008000 !important; border-left: 2px solid #008000 !important; border-right: 1px solid #008000 !important; padding: 4px 12px; border-top-left-radius: 6px; border-bottom-left-radius: 6px; font-weight: 900; font-size: 20px; text-align: center; min-width: 44px; line-height: 1.1; }
    .touch-right-orange-box { background-color: #000000 !important; color: #ffffff !important; border-top: 2px solid #ff9800 !important; border-bottom: 2px solid #ff9800 !important; border-right: 2px solid #ff9800 !important; border-left: 1px solid #ff9800 !important; padding: 4px 12px; border-top-right-radius: 6px; border-bottom-right-radius: 6px; font-weight: 900; font-size: 20px; text-align: center; min-width: 44px; line-height: 1.1; }
    .touch-right-orange-highlight { background-color: #8b0000 !important; color: #ffffff !important; border-top: 2px solid #8b0000 !important; border-bottom: 2px solid #8b0000 !important; border-right: 2px solid #8b0000 !important; border-left: 1px solid #8b0000 !important; padding: 4px 12px; border-top-right-radius: 6px; border-bottom-right-radius: 6px; font-weight: 900; font-size: 20px; text-align: center; min-width: 44px; line-height: 1.1; }

    .power-live-row { display: flex; flex-direction: row; align-items: center; gap: 10px; padding: 10px 4px 4px 4px; font-size: 13px; font-weight: 800; flex-wrap: wrap; }
    .call-buyer-badge { color: #00ff7f; background-color: #0a1f12; padding: 4px 10px; border-radius: 5px; border: 1px solid #008000; font-size: 13px; }
    .put-buyer-badge { color: #ff9800; background-color: #241407; padding: 4px 10px; border-radius: 5px; border: 1px solid #ff9800; font-size: 13px; }

    .breadth-flex-row { display: flex; flex-direction: row; align-items: center; padding: 6px 2px; border-bottom: 1px solid #1f2937; font-size: 14px; gap: 12px; flex-wrap: nowrap !important; width: 100%; }
    .breadth-flex-row:last-child { border-bottom: none; }
    .breadth-label { font-weight: 700; color: #e6edf3; font-size: 14px; min-width: 95px !important; max-width: 105px !important; white-space: nowrap; }

    /* Order Flow Pressure Matrix Styling */
    .flow-table { width: 100%; border-collapse: collapse; font-size: 12px; text-align: center; margin-top: 6px; }
    .flow-table th { background-color: #161b22; color: #94a3b8; padding: 6px 4px; border: 1px solid #21262d; font-weight: 800; }
    .flow-table td { padding: 6px 4px; border: 1px solid #21262d; font-weight: 700; }
    .score-badge-high { background-color: #006622; color: #ffffff; padding: 2px 6px; border-radius: 4px; font-weight: 900; }
    .score-badge-low { background-color: #8b0000; color: #ffffff; padding: 2px 6px; border-radius: 4px; font-weight: 900; }
    .score-badge-mid { background-color: #21262d; color: #94a3b8; padding: 2px 6px; border-radius: 4px; font-weight: 700; }

    /* Custom Border Highlight Badges for Aggression Matrix */
    .hdr-green-border { border: 2px solid #00ff7f !important; padding: 2px 6px; border-radius: 5px; display: inline-block; }
    .hdr-orange-border { border: 2px solid #ff9800 !important; padding: 2px 6px; border-radius: 5px; display: inline-block; }
    .cell-green-border { border: 2px solid #00ff7f !important; border-radius: 4px; display: inline-block; padding: 1px 4px; width: 85%; }
    .cell-orange-border { border: 2px solid #ff9800 !important; border-radius: 4px; display: inline-block; padding: 1px 4px; width: 85%; }
    
    /* ATM Row Prominent Highlighting */
    .atm-matrix-row {
        background-color: #1b2434 !important;
        font-size: 14px !important;
        border-top: 2px solid #38bdf8 !important;
        border-bottom: 2px solid #38bdf8 !important;
    }
    .atm-matrix-row td {
        font-size: 13px !important;
        font-weight: 900 !important;
    }

    .alert-banner {
        background-color: #1e1b4b;
        border: 1px solid #6366f1;
        color: #e0e7ff;
        padding: 6px 12px;
        border-radius: 6px;
        font-size: 12px;
        font-weight: 800;
        margin-bottom: 6px;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    @media (max-width: 480px) {
        .breadth-flex-row { gap: 8px !important; padding: 5px 0px !important; }
        .breadth-label { min-width: 85px !important; max-width: 90px !important; font-size: 13px !important; }
        .touch-left-green-box, .touch-left-green-highlight,
        .touch-right-orange-box, .touch-right-orange-highlight { padding: 3px 10px !important; min-width: 40px !important; font-size: 18px !important; }
    }
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------------------
# 2. INDIAN NUMBER FORMATTER
# -------------------------------------------------------------
def format_indian_number(num):
    try:
        val = int(num)
        sign = "+" if val > 0 else ("-" if val < 0 else "")
        s = str(abs(val))
        if len(s) <= 3:
            return f"{sign}{s}"
        last3 = s[-3:]
        other = s[:-3]
        groups = []
        while len(other) > 2:
            groups.insert(0, other[-2:])
            other = other[:-2]
        if other:
            groups.insert(0, other)
        return f"{sign}{','.join(groups)},{last3}"
    except Exception:
        return str(num)

# -------------------------------------------------------------
# 3. TIMEZONE & EXPIRY PARSER
# -------------------------------------------------------------
IST = timezone(timedelta(hours=5, minutes=30))
MONTH_MAP = {"JAN": 1, "FEB": 2, "MAR": 3, "APR": 4, "MAY": 5, "JUN": 6,
             "JUL": 7, "AUG": 8, "SEP": 9, "OCT": 10, "NOV": 11, "DEC": 12}

def get_current_ist():
    return datetime.now(timezone.utc).astimezone(IST)

def parse_expiry_date(exp_str):
    if not exp_str:
        return None
    s = str(exp_str).strip().upper()
    try:
        match = re.match(r"^(\d{1,2})[-]?([A-Z]{3})[-]?(\d{4})$", s)
        if match:
            return datetime(int(match.group(3)), MONTH_MAP.get(match.group(2), 1), int(match.group(1))).date()
        match_short = re.match(r"^(\d{1,2})([A-Z]{3})(\d{2})$", s)
        if match_short:
            return datetime(2000 + int(match_short.group(3)), MONTH_MAP.get(match_short.group(2), 1), int(match_short.group(1))).date()
        match_iso = re.match(r"^(\d{4})-(\d{2})-(\d{2})$", s)
        if match_iso:
            return datetime(int(match_iso.group(1)), int(match_iso.group(2)), int(match_iso.group(3))).date()
    except Exception:
        pass
    return None

def is_market_open():
    now_ist = get_current_ist()
    if now_ist.weekday() >= 5:
        return False, "Market Closed (Weekend)"
    market_start, market_end = dtime(9, 15, 0), dtime(15, 30, 0)
    current_time_only = now_ist.time()
    if current_time_only < market_start:
        return False, f"Market Opens at 09:15 AM IST (Current: {now_ist.strftime('%I:%M:%S %p')})"
    elif current_time_only > market_end:
        return False, f"Market Closed at 03:30 PM IST (Current: {now_ist.strftime('%I:%M:%S %p')})"
    return True, "🟢 Live Market Active"

# -------------------------------------------------------------
# 4. DIRECT REST API SESSION ENGINE
# -------------------------------------------------------------
SESSION_ERROR_MARKERS = ("AG8001", "AG8002", "AG8003", "invalid token", "session expired", "unauthorized")

class AngelDirectClient:
    def __init__(self, jwt_token, refresh_token, api_key):
        self.jwt_token = jwt_token
        self.refresh_token = refresh_token
        self.api_key = api_key
        self._build_headers()

    def _build_headers(self):
        self.headers = {
            "Authorization": f"Bearer {self.jwt_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-UserType": "USER",
            "X-SourceID": "WEB",
            "X-ClientLocalIP": "127.0.0.1",
            "X-ClientPublicIP": "106.193.147.98",
            "X-MACAddress": "fe80::216e:6507:4b90:3719",
            "X-PrivateKey": self.api_key
        }

    def _looks_like_session_error(self, resp_json):
        if not isinstance(resp_json, dict):
            return False
        msg = str(resp_json.get("message", "")).lower()
        code = str(resp_json.get("errorcode", ""))
        return any(marker.lower() in msg or marker == code for marker in SESSION_ERROR_MARKERS)

    def refresh_session(self):
        try:
            url = "https://apiconnect.angelbroking.com/rest/auth/angelbroking/jwt/v1/generateTokens"
            refresh_headers = {
                "Content-Type": "application/json", "Accept": "application/json",
                "X-UserType": "USER", "X-SourceID": "WEB",
                "X-ClientLocalIP": "127.0.0.1", "X-ClientPublicIP": "106.193.147.98",
                "X-MACAddress": "fe80::216e:6507:4b90:3719", "X-PrivateKey": self.api_key
            }
            payload = {"refreshToken": self.refresh_token}
            r = requests.post(url, headers=refresh_headers, json=payload, timeout=8)
            data = r.json()
            if data.get("status") and "data" in data and "jwtToken" in data["data"]:
                self.jwt_token = data["data"]["jwtToken"]
                self.refresh_token = data["data"].get("refreshToken", self.refresh_token)
                self._build_headers()
                return True
        except Exception:
            pass
        return False

    def ltpData(self, exchange, tradingsymbol, symboltoken):
        url = "https://apiconnect.angelbroking.com/rest/secure/angelbroking/order/v1/getLtpData"
        payload = {"exchange": exchange, "tradingsymbol": tradingsymbol, "symboltoken": str(symboltoken)}
        try:
            r = requests.post(url, headers=self.headers, json=payload, timeout=5)
            data = r.json()
            if self._looks_like_session_error(data) and self.refresh_session():
                r = requests.post(url, headers=self.headers, json=payload, timeout=5)
                data = r.json()
            return data
        except Exception as e:
            return {"status": False, "message": str(e)}

    def getMarketData(self, mode, tokens_dict):
        url = "https://apiconnect.angelbroking.com/rest/secure/angelbroking/market/v1/quote/"
        sanitized_dict = {exch: [str(x) for x in t_list] for exch, t_list in tokens_dict.items()}
        payload = {"mode": mode, "exchangeTokens": sanitized_dict}
        try:
            r = requests.post(url, headers=self.headers, json=payload, timeout=6)
            data = r.json()
            if self._looks_like_session_error(data) and self.refresh_session():
                r = requests.post(url, headers=self.headers, json=payload, timeout=6)
                data = r.json()
            return data
        except Exception as e:
            return {"status": False, "message": str(e)}

def authenticate_angel():
    api_key = str(st.secrets.get("ANGEL_API_KEY", "")).strip()
    client_code = str(st.secrets.get("ANGEL_CLIENT_CODE", "")).strip()
    pin = str(st.secrets.get("ANGEL_PIN", "")).strip()
    totp_key = str(st.secrets.get("ANGEL_TOTP_KEY", "")).strip()

    if not all([api_key, client_code, pin, totp_key]):
        return None, "Missing Streamlit Secrets"

    try:
        totp_val = pyotp.TOTP(totp_key).now()
        login_url = "https://apiconnect.angelbroking.com/rest/auth/angelbroking/user/v1/loginByPassword"
        headers = {
            "Content-Type": "application/json", "Accept": "application/json",
            "X-UserType": "USER", "X-SourceID": "WEB",
            "X-ClientLocalIP": "127.0.0.1", "X-ClientPublicIP": "106.193.147.98",
            "X-MACAddress": "fe80::216e:6507:4b90:3719", "X-PrivateKey": api_key
        }
        payload = {"clientcode": client_code, "password": pin, "totp": totp_val}
        res = requests.post(login_url, headers=headers, json=payload, timeout=8)
        data = res.json()

        if data.get("status") and "data" in data and "jwtToken" in data["data"]:
            client = AngelDirectClient(data["data"]["jwtToken"], data["data"].get("refreshToken", ""), api_key)
            return client, "Connected via Direct REST"
        else:
            return None, f"Angel API: {data.get('message', 'Login Rejected')}"
    except Exception as e:
        return None, f"REST Error: {str(e)}"

if "smart_api_obj" not in st.session_state or st.session_state.smart_api_obj is None:
    smart_api, auth_log = authenticate_angel()
    st.session_state.smart_api_obj = smart_api
    st.session_state.smart_api_log = auth_log
    st.session_state.last_login_ts = time.time()
else:
    smart_api = st.session_state.smart_api_obj
    auth_log = st.session_state.smart_api_log

if smart_api and (time.time() - st.session_state.get("last_login_ts", 0)) > 6 * 3600:
    new_client, new_log = authenticate_angel()
    if new_client:
        st.session_state.smart_api_obj, st.session_state.smart_api_log = new_client, new_log
        st.session_state.last_login_ts = time.time()
        smart_api, auth_log = new_client, new_log

# -------------------------------------------------------------
# 5. SCRIP MASTER & NIFTY EQUITIES / FUTURES LOADER
# -------------------------------------------------------------
NIFTY_50_SYMBOLS = [
    "RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK", "HINDUNILVR", "ITC", "SBIN",
    "BHARTIARTL", "KOTAKBANK", "LT", "AXISBANK", "ASIANPAINT", "MARUTI", "SUNPHARMA",
    "TITAN", "BAJFINANCE", "ULTRACEMCO", "TATAMOTORS", "NESTLEIND", "NTPC", "POWERGRID",
    "M&M", "JSWSTEEL", "TATASTEEL", "ADANIENT", "ADANIPORTS", "COALINDIA", "HCLTECH",
    "ONGC", "BAJAJFINSV", "WIPRO", "TECHM", "GRASIM", "BRITANNIA", "CIPLA", "HEROMOTOCO",
    "DRREDDY", "EICHERMOT", "DIVISLAB", "TATACONSUM", "SBILIFE", "APOLLOHOSP", "HDFCLIFE",
    "BAJAJ-AUTO", "INDUSINDBK", "BPCL", "LTIM", "SHRIRAMFIN", "TRENT"
]

@st.cache_resource(ttl=3600*12)
def load_all_scrip_masters():
    url = "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"
    try:
        res = requests.get(url, timeout=12)
        if res.status_code == 200:
            df = pd.DataFrame(res.json())

            nifty_options = df[(df["name"] == "NIFTY") & (df["exch_seg"] == "NFO") & (df["instrumenttype"] == "OPTIDX")].copy()
            raw_strikes = pd.to_numeric(nifty_options["strike"], errors="coerce").fillna(0.0)
            nifty_options["strike_int"] = raw_strikes.apply(lambda x: int(round(x / 100.0)) if x > 100000 else int(round(x)))
            nifty_options["parsed_date"] = nifty_options["expiry"].apply(parse_expiry_date)

            nifty_futs = df[(df["name"] == "NIFTY") & (df["exch_seg"] == "NFO") & (df["instrumenttype"] == "FUTIDX")].copy()
            nifty_futs["parsed_date"] = nifty_futs["expiry"].apply(parse_expiry_date)

            n50_equities = df[(df["exch_seg"] == "NSE") & (df["symbol"].str.endswith("-EQ")) & (df["name"].isin(NIFTY_50_SYMBOLS))].copy()
            n50_df = n50_equities.drop_duplicates(subset=["name"]).head(50)

            spot_row = df[(df["name"] == "NIFTY") & (df["exch_seg"] == "NSE") & (df["symbol"] == "Nifty 50")]
            spot_token = str(spot_row.iloc[0]["token"]) if not spot_row.empty else "99926000"

            vix_row = df[(df["name"] == "INDIA VIX") & (df["exch_seg"] == "NSE")]
            vix_token = str(vix_row.iloc[0]["token"]) if not vix_row.empty else "26001"

            return nifty_options, n50_df, nifty_futs, spot_token, vix_token
    except Exception:
        pass
    return None, None, None, "99926000", "26001"

scrip_df, nifty50_df, nifty_futs_df, SPOT_TOKEN, VIX_TOKEN = load_all_scrip_masters()

def get_nearest_future_token(futs_df):
    if futs_df is None or futs_df.empty:
        return None, ""
    today_date = get_current_ist().date()
    valid = futs_df[futs_df["parsed_date"] >= today_date].copy()
    if valid.empty:
        return None, ""
    nearest_date = valid["parsed_date"].min()
    row = valid[valid["parsed_date"] == nearest_date].iloc[0]
    return str(row["token"]), str(row["symbol"])

FUT_TOKEN, FUT_SYMBOL = get_nearest_future_token(nifty_futs_df)

# -------------------------------------------------------------
# 6. DATA RETRIEVAL & MARKET SNAPSHOT
# -------------------------------------------------------------
def get_live_india_vix(_api):
    vix_val, vix_chg = 0.0, 0.0
    if _api:
        try:
            vix_res = _api.ltpData("NSE", "INDIA VIX", VIX_TOKEN)
            if vix_res and vix_res.get("status") and "data" in vix_res:
                vix_val = float(vix_res["data"]["ltp"])
                close_val = float(vix_res["data"].get("close", vix_val))
                vix_chg = round(vix_val - close_val, 2)
        except Exception:
            pass
    return vix_val, vix_chg

def get_live_market_snapshot(_api, scrip_data):
    nifty_spot, fut_price, fut_is_real = 0.0, 0.0, False
    expiry_str, call_ltp, put_ltp = "WEEKLY", 0.0, 0.0
    ce_token, pe_token, ce_symbol, pe_symbol = None, None, "", ""
    is_expiry_today = False

    if _api:
        try:
            spot_data = _api.ltpData("NSE", "Nifty 50", SPOT_TOKEN)
            if spot_data and spot_data.get("status") and "data" in spot_data:
                nifty_spot = float(spot_data["data"]["ltp"])
        except Exception:
            pass

        if FUT_TOKEN:
            try:
                fut_data = _api.ltpData("NFO", FUT_SYMBOL, FUT_TOKEN)
                if fut_data and fut_data.get("status") and "data" in fut_data:
                    fut_price = float(fut_data["data"]["ltp"])
                    fut_is_real = True
            except Exception:
                pass

    if not fut_is_real:
        fut_price = nifty_spot

    if nifty_spot == 0.0:
        return 0.0, 0.0, False, 0, expiry_str, 0.0, 0.0, None, None, "", "", False

    atm_strike = int(round(fut_price / 50.0) * 50)

    if _api and scrip_data is not None and not scrip_data.empty:
        try:
            today_date = get_current_ist().date()
            valid_options = scrip_data[scrip_data["parsed_date"] >= today_date].copy()

            if not valid_options.empty:
                nearest_date = valid_options["parsed_date"].min()
                is_expiry_today = (nearest_date == today_date)
                current_exp_df = valid_options[valid_options["parsed_date"] == nearest_date]
                expiry_str = str(current_exp_df.iloc[0]["expiry"])

                ce_match = current_exp_df[(current_exp_df["strike_int"] == atm_strike) & (current_exp_df["symbol"].str.endswith("CE"))]
                pe_match = current_exp_df[(current_exp_df["strike_int"] == atm_strike) & (current_exp_df["symbol"].str.endswith("PE"))]

                if not ce_match.empty:
                    ce_token = str(ce_match.iloc[0]["token"])
                    ce_symbol = str(ce_match.iloc[0]["symbol"])
                    ce_quote = _api.ltpData("NFO", ce_symbol, ce_token)
                    if ce_quote.get("status") and "data" in ce_quote:
                        call_ltp = float(ce_quote["data"]["ltp"])

                if not pe_match.empty:
                    pe_token = str(pe_match.iloc[0]["token"])
                    pe_symbol = str(pe_match.iloc[0]["symbol"])
                    pe_quote = _api.ltpData("NFO", pe_symbol, pe_token)
                    if pe_quote.get("status") and "data" in pe_quote:
                        put_ltp = float(pe_quote["data"]["ltp"])
        except Exception:
            pass

    return (nifty_spot, fut_price, fut_is_real, atm_strike, expiry_str,
            call_ltp, put_ltp, ce_token, pe_token, ce_symbol, pe_symbol, is_expiry_today)

# -------------------------------------------------------------
# 7. LIVE OPEN INTEREST & ORDER FLOW PRESSURE ENGINE
# -------------------------------------------------------------
def _get_intraday_low_store():
    today_str = get_current_ist().date().isoformat()
    store = st.session_state.get("oi_intraday_low")
    if store is None or store.get("date") != today_str:
        store = {"date": today_str, "ce": {}, "pe": {}}
        st.session_state["oi_intraday_low"] = store
    return store

def _get_executed_trades_tracker():
    today_str = get_current_ist().date().isoformat()
    tracker = st.session_state.get("executed_trades_tracker")
    if tracker is None or tracker.get("date") != today_str:
        tracker = {
            "date": today_str,
            "last_state": {},
            "cum_buy_vol": {},
            "cum_sell_vol": {}
        }
        st.session_state["executed_trades_tracker"] = tracker
    return tracker

def calculate_full_chain_max_pain(scrip_data):
    if scrip_data is None or scrip_data.empty:
        return 0
    try:
        today_date = get_current_ist().date()
        valid_options = scrip_data[scrip_data["parsed_date"] >= today_date].copy()
        if valid_options.empty:
            return 0
        nearest_date = valid_options["parsed_date"].min()
        current_exp_df = valid_options[valid_options["parsed_date"] == nearest_date]

        ce_df = current_exp_df[current_exp_df["symbol"].str.endswith("CE")]
        pe_df = current_exp_df[current_exp_df["symbol"].str.endswith("PE")]

        all_strikes = sorted(current_exp_df["strike_int"].unique())
        if not all_strikes:
            return 0

        loss_map = {}
        for test_s in all_strikes:
            total_loss = 0
            for _, r in ce_df.iterrows():
                k, oi = r["strike_int"], float(r.get("opnInterest", r.get("openInterest", 0)))
                if test_s > k and oi > 0:
                    total_loss += (test_s - k) * oi
            for _, r in pe_df.iterrows():
                k, oi = r["strike_int"], float(r.get("opnInterest", r.get("openInterest", 0)))
                if test_s < k and oi > 0:
                    total_loss += (k - test_s) * oi
            loss_map[test_s] = total_loss

        return min(loss_map, key=loss_map.get)
    except Exception:
        return 0

def fetch_live_oi_and_power(_api, scrip_data, atm_strike, spot_price, fut_price):
    if atm_strike == 0:
        return ([], [], [], [], [], [], [], 0, 0, 0.0, 0, 0, {}, {}, {}, 0, 0, 0, False)

    strikes = [int(atm_strike + (i * 50)) for i in range(-10, 11)]
    pe_oi_dict, ce_oi_dict = {s: 0 for s in strikes}, {s: 0 for s in strikes}
    pe_prev_oi_dict, ce_prev_oi_dict = {s: 0 for s in strikes}, {s: 0 for s in strikes}
    pe_has_baseline, ce_has_baseline = {s: False for s in strikes}, {s: False for s in strikes}
    live_cp, live_pp = 0, 0
    atm_ce_real_vol, atm_pe_real_vol = 0, 0
    is_live = False

    fut_basis = fut_price - spot_price
    fut_bullish_bias = 5 if fut_basis > 10 else (-5 if fut_basis < -10 else 0)

    target_matrix_strikes = [atm_strike - 100, atm_strike - 50, atm_strike, atm_strike + 50, atm_strike + 100, atm_strike + 150]

    matrix_flow_data = {
        s: {
            "CE_BUY_VOL": 0, "CE_SELL_VOL": 0, "CE_PRESSURE": 50, "CE_SCORE": 50, "CE_REGIME": "NEUTRAL",
            "PE_BUY_VOL": 0, "PE_SELL_VOL": 0, "PE_PRESSURE": 50, "PE_SCORE": 50, "PE_REGIME": "NEUTRAL",
            "TYPE": "ATM" if s == atm_strike else ("ITM" if s < atm_strike else "OTM")
        } for s in target_matrix_strikes
    }

    exec_tracker = _get_executed_trades_tracker()

    if _api and scrip_data is not None and not scrip_data.empty:
        try:
            today_date = get_current_ist().date()
            valid_options = scrip_data[scrip_data["parsed_date"] >= today_date].copy()

            if not valid_options.empty:
                nearest_date = valid_options["parsed_date"].min()
                current_exp_df = valid_options[valid_options["parsed_date"] == nearest_date]

                target_ce = current_exp_df[(current_exp_df["strike_int"].isin(strikes)) & (current_exp_df["symbol"].str.endswith("CE"))]
                target_pe = current_exp_df[(current_exp_df["strike_int"].isin(strikes)) & (current_exp_df["symbol"].str.endswith("PE"))]

                all_tokens = [str(x) for x in list(target_ce["token"].values) + list(target_pe["token"].values)]
                res = _api.getMarketData("FULL", {"NFO": all_tokens})

                if res and res.get("status") and "fetched" in res.get("data", {}):
                    fetched_items = {str(itm.get("symbolToken", itm.get("token", ""))): itm for itm in res["data"]["fetched"]}

                    tmp_cp, tmp_pp = 0, 0
                    for _, row in target_ce.iterrows():
                        t_str, s_val = str(row["token"]), int(row["strike_int"])
                        if t_str in fetched_items:
                            itm = fetched_items[t_str]
                            oi = int(itm.get("opnInterest", itm.get("openInterest", 0)))
                            ce_oi_dict[s_val] = oi
                            prev_oi = int(itm.get("prevOpenInterest", itm.get("prevOpnInterest", 0)))
                            if prev_oi > 0:
                                ce_prev_oi_dict[s_val] = prev_oi
                                ce_has_baseline[s_val] = True

                            buy_q = int(itm.get("totBuyQuan", itm.get("totalBuyQty", 0)))
                            sell_q = int(itm.get("totSellQuan", itm.get("totalSellQty", 0)))
                            if abs(s_val - atm_strike) <= 100:
                                tmp_cp += (buy_q - sell_q)

                            cur_vol = int(itm.get("tradeVolume", itm.get("volume", 0)))
                            cur_ltp = float(itm.get("ltp", 0.0))
                            close_p = float(itm.get("close", cur_ltp))
                            if s_val == atm_strike:
                                atm_ce_real_vol = cur_vol

                            depth_buy = itm.get("depth", {}).get("buy", [])
                            depth_sell = itm.get("depth", {}).get("sell", [])
                            best_bid = float(depth_buy[0].get("price", 0.0)) if depth_buy else cur_ltp
                            best_ask = float(depth_sell[0].get("price", 0.0)) if depth_sell else cur_ltp

                            if t_str not in exec_tracker["last_state"]:
                                exec_tracker["last_state"][t_str] = {"vol": cur_vol, "ltp": cur_ltp, "last_dir": "BUY"}
                                exec_tracker["cum_buy_vol"][t_str] = 0
                                exec_tracker["cum_sell_vol"][t_str] = 0
                            else:
                                prev_s = exec_tracker["last_state"][t_str]
                                vol_diff = max(0, cur_vol - prev_s["vol"])
                                if vol_diff > 0:
                                    if cur_ltp >= best_ask or cur_ltp > prev_s["ltp"]:
                                        exec_tracker["cum_buy_vol"][t_str] += vol_diff
                                        prev_s["last_dir"] = "BUY"
                                    elif cur_ltp <= best_bid or cur_ltp < prev_s["ltp"]:
                                        exec_tracker["cum_sell_vol"][t_str] += vol_diff
                                        prev_s["last_dir"] = "SELL"
                                    else:
                                        if prev_s["last_dir"] == "BUY":
                                            exec_tracker["cum_buy_vol"][t_str] += vol_diff
                                        else:
                                            exec_tracker["cum_sell_vol"][t_str] += vol_diff

                                prev_s["vol"] = cur_vol
                                prev_s["ltp"] = cur_ltp

                            if s_val in target_matrix_strikes:
                                b_v = exec_tracker["cum_buy_vol"].get(t_str, 0)
                                s_v = exec_tracker["cum_sell_vol"].get(t_str, 0)
                                matrix_flow_data[s_val]["CE_BUY_VOL"] = b_v
                                matrix_flow_data[s_val]["CE_SELL_VOL"] = s_v
                                p_ratio = int(round((b_v / max(1, b_v + s_v)) * 100)) if (b_v + s_v) > 0 else 50
                                matrix_flow_data[s_val]["CE_PRESSURE"] = p_ratio

                                prem_up = cur_ltp >= close_p
                                oi_up = (oi - prev_oi) >= 0 if prev_oi > 0 else True
                                if prem_up and oi_up:
                                    regime = "Long Buildup" if p_ratio >= 55 else "Buildup"
                                elif not prem_up and oi_up:
                                    regime = "Short Buildup"
                                elif prem_up and not oi_up:
                                    regime = "Short Covering"
                                else:
                                    regime = "Long Unwinding"
                                matrix_flow_data[s_val]["CE_REGIME"] = regime

                                raw_score = (p_ratio * 0.40) + ((cur_ltp / max(1.0, close_p) - 1.0) * 100 * 2.5 + 50) * 0.35 + (50 if oi_up else 30) * 0.25 + fut_bullish_bias
                                matrix_flow_data[s_val]["CE_SCORE"] = int(np.clip(raw_score, 0, 100))

                    for _, row in target_pe.iterrows():
                        t_str, s_val = str(row["token"]), int(row["strike_int"])
                        if t_str in fetched_items:
                            itm = fetched_items[t_str]
                            oi = int(itm.get("opnInterest", itm.get("openInterest", 0)))
                            pe_oi_dict[s_val] = oi
                            prev_oi = int(itm.get("prevOpenInterest", itm.get("prevOpnInterest", 0)))
                            if prev_oi > 0:
                                pe_prev_oi_dict[s_val] = prev_oi
                                pe_has_baseline[s_val] = True

                            buy_q = int(itm.get("totBuyQuan", itm.get("totalBuyQty", 0)))
                            sell_q = int(itm.get("totSellQuan", itm.get("totalSellQty", 0)))
                            if abs(s_val - atm_strike) <= 100:
                                tmp_pp += (buy_q - sell_q)

                            cur_vol = int(itm.get("tradeVolume", itm.get("volume", 0)))
                            cur_ltp = float(itm.get("ltp", 0.0))
                            close_p = float(itm.get("close", cur_ltp))
                            if s_val == atm_strike:
                                atm_pe_real_vol = cur_vol

                            depth_buy = itm.get("depth", {}).get("buy", [])
                            depth_sell = itm.get("depth", {}).get("sell", [])
                            best_bid = float(depth_buy[0].get("price", 0.0)) if depth_buy else cur_ltp
                            best_ask = float(depth_sell[0].get("price", 0.0)) if depth_sell else cur_ltp

                            if t_str not in exec_tracker["last_state"]:
                                exec_tracker["last_state"][t_str] = {"vol": cur_vol, "ltp": cur_ltp, "last_dir": "SELL"}
                                exec_tracker["cum_buy_vol"][t_str] = 0
                                exec_tracker["cum_sell_vol"][t_str] = 0
                            else:
                                prev_s = exec_tracker["last_state"][t_str]
                                vol_diff = max(0, cur_vol - prev_s["vol"])
                                if vol_diff > 0:
                                    if cur_ltp >= best_ask or cur_ltp > prev_s["ltp"]:
                                        exec_tracker["cum_buy_vol"][t_str] += vol_diff
                                        prev_s["last_dir"] = "BUY"
                                    elif cur_ltp <= best_bid or cur_ltp < prev_s["ltp"]:
                                        exec_tracker["cum_sell_vol"][t_str] += vol_diff
                                        prev_s["last_dir"] = "SELL"
                                    else:
                                        if prev_s["last_dir"] == "BUY":
                                            exec_tracker["cum_buy_vol"][t_str] += vol_diff
                                        else:
                                            exec_tracker["cum_sell_vol"][t_str] += vol_diff

                                prev_s["vol"] = cur_vol
                                prev_s["ltp"] = cur_ltp

                            if s_val in target_matrix_strikes:
                                b_v = exec_tracker["cum_buy_vol"].get(t_str, 0)
                                s_v = exec_tracker["cum_sell_vol"].get(t_str, 0)
                                matrix_flow_data[s_val]["PE_BUY_VOL"] = b_v
                                matrix_flow_data[s_val]["PE_SELL_VOL"] = s_v
                                p_ratio = int(round((b_v / max(1, b_v + s_v)) * 100)) if (b_v + s_v) > 0 else 50
                                matrix_flow_data[s_val]["PE_PRESSURE"] = p_ratio

                                prem_up = cur_ltp >= close_p
                                oi_up = (oi - prev_oi) >= 0 if prev_oi > 0 else True
                                if prem_up and oi_up:
                                    regime = "Long Buildup" if p_ratio >= 55 else "Buildup"
                                elif not prem_up and oi_up:
                                    regime = "Short Buildup"
                                elif prem_up and not oi_up:
                                    regime = "Short Covering"
                                else:
                                    regime = "Long Unwinding"
                                matrix_flow_data[s_val]["PE_REGIME"] = regime

                                raw_score = (p_ratio * 0.40) + ((cur_ltp / max(1.0, close_p) - 1.0) * 100 * 2.5 + 50) * 0.35 + (50 if oi_up else 30) * 0.25 - fut_bullish_bias
                                matrix_flow_data[s_val]["PE_SCORE"] = int(np.clip(raw_score, 0, 100))

                    live_cp, live_pp = tmp_cp, tmp_pp
                    if sum(ce_oi_dict.values()) > 0 or sum(pe_oi_dict.values()) > 0 or tmp_cp != 0:
                        is_live = True
        except Exception:
            pass

    low_store = _get_intraday_low_store()

    def resolve_phase(side_store, strike, current, baseline, has_baseline):
        if not has_baseline:
            return current, 0, 0
        if strike not in side_store:
            side_store[strike] = baseline
        if current < side_store[strike]:
            side_store[strike] = current
        if current >= baseline:
            side_store[strike] = baseline
            return baseline, current - baseline, 0
        session_low = side_store[strike]
        return session_low, max(0, current - session_low), max(0, baseline - current)

    pe_solid, pe_crossed, pe_hollow = [], [], []
    ce_solid, ce_crossed, ce_hollow = [], [], []

    for s in strikes:
        s_solid, s_crossed, s_hollow = resolve_phase(low_store["pe"], s, pe_oi_dict.get(s, 0), pe_prev_oi_dict.get(s, 0), pe_has_baseline.get(s, False))
        pe_solid.append(s_solid); pe_crossed.append(s_crossed); pe_hollow.append(s_hollow)

        c_solid, c_crossed, c_hollow = resolve_phase(low_store["ce"], s, ce_oi_dict.get(s, 0), ce_prev_oi_dict.get(s, 0), ce_has_baseline.get(s, False))
        ce_solid.append(c_solid); ce_crossed.append(c_crossed); ce_hollow.append(c_hollow)

    total_ce_oi, total_pe_oi = sum(ce_oi_dict.values()), sum(pe_oi_dict.values())
    pcr_val = round(total_pe_oi / max(1, total_ce_oi), 2) if total_ce_oi > 0 else 0.0
    real_max_pain = calculate_full_chain_max_pain(scrip_data)

    return (strikes, pe_solid, pe_crossed, pe_hollow, ce_solid, ce_crossed, ce_hollow,
            live_cp, live_pp, pcr_val, total_ce_oi, total_pe_oi, ce_oi_dict, pe_oi_dict,
            matrix_flow_data, real_max_pain, atm_ce_real_vol, atm_pe_real_vol, is_live)

# -------------------------------------------------------------
# 8. LIVE NIFTY 50 BREADTH (Real Opening Range + Heavyweights)
# -------------------------------------------------------------
TOP_10_HEAVYWEIGHTS = ["HDFCBANK", "RELIANCE", "ICICIBANK", "INFY", "ITC", "TCS", "LT", "AXISBANK", "KOTAKBANK", "BHARTIARTL"]
TOP_3_HEAVYWEIGHTS = ["HDFCBANK", "ICICIBANK", "RELIANCE"]

def fetch_nifty_50_breadth_and_heavyweights(_api, n50_df, prev_cached):
    above_open, below_open, above_15m_high, below_15m_low, heavy3_above, heavy3_below, heavy10_above, heavy10_below = prev_cached

    today_str = get_current_ist().date().isoformat()
    if "opening_15m_orb" not in st.session_state or st.session_state.opening_15m_orb.get("date") != today_str:
        st.session_state.opening_15m_orb = {"date": today_str, "highs": {}, "lows": {}}

    orb_store = st.session_state.opening_15m_orb
    now_t = get_current_ist().time()

    if _api and n50_df is not None and not n50_df.empty:
        try:
            tokens_list = [str(t) for t in list(n50_df["token"].values)[:50]]
            token_to_name = {str(row["token"]): row["name"] for _, row in n50_df.iterrows()}

            a_o, b_o, a_15, b_15 = 0, 0, 0, 0
            h3_a, h3_b = 0, 0
            h10_a, h10_b = 0, 0

            for chunk_i in range(0, len(tokens_list), 25):
                sub_toks = tokens_list[chunk_i:chunk_i+25]
                quote_res = _api.getMarketData("OHLC", {"NSE": sub_toks})

                if quote_res and quote_res.get("status") and "fetched" in quote_res.get("data", {}):
                    for item in quote_res["data"]["fetched"]:
                        tok_id = str(item.get("symbolToken", item.get("token", "")))
                        ltp, opn = float(item.get("ltp", 0)), float(item.get("open", 0))
                        high, low = float(item.get("high", 0)), float(item.get("low", 0))

                        if ltp > 0 and opn > 0:
                            if ltp >= opn:
                                a_o += 1
                            else:
                                b_o += 1

                            if now_t <= dtime(9, 30):
                                orb_store["highs"][tok_id] = high
                                orb_store["lows"][tok_id] = low

                            orb_hi = orb_store["highs"].get(tok_id, high)
                            orb_lo = orb_store["lows"].get(tok_id, low)

                            if ltp >= orb_hi and orb_hi > 0:
                                a_15 += 1
                            elif ltp <= orb_lo and orb_lo > 0:
                                b_15 += 1

                            sym_name = token_to_name.get(tok_id, "")
                            if sym_name in TOP_3_HEAVYWEIGHTS:
                                if ltp >= opn:
                                    h3_a += 1
                                else:
                                    h3_b += 1

                            if sym_name in TOP_10_HEAVYWEIGHTS:
                                if ltp >= opn:
                                    h10_a += 1
                                else:
                                    h10_b += 1

            if (a_o + b_o) > 0:
                above_open, below_open = a_o, b_o
                above_15m_high, below_15m_low = a_15, b_15
                heavy3_above, heavy3_below = h3_a, h3_b
                heavy10_above, heavy10_below = h10_a, h10_b
        except Exception:
            pass

    open_sentiment = "BULLISH" if above_open > 34 else ("BEARISH" if below_open > 34 else "NEUTRAL")
    return above_open, below_open, open_sentiment, above_15m_high, below_15m_low, heavy3_above, heavy3_below, heavy10_above, heavy10_below

# -------------------------------------------------------------
# 9. CHART GENERATION
# -------------------------------------------------------------
def render_oi_chart(strikes, pe_solid, pe_crossed, pe_hollow, ce_solid, ce_crossed, ce_hollow, fut_price):
    if not strikes:
        strikes = [24300 + (i * 50) for i in range(-10, 11)]
        pe_solid = [0] * 21; pe_crossed = [0] * 21; pe_hollow = [0] * 21
        ce_solid = [0] * 21; ce_crossed = [0] * 21; ce_hollow = [0] * 21

    pe_x = [s - 9 for s in strikes]
    ce_x = [s + 9 for s in strikes]

    fig_oi = go.Figure()
    fig_oi.add_trace(go.Bar(name="Put Base OI", x=pe_x, y=pe_solid, marker_color="#22c55e", width=16))
    fig_oi.add_trace(go.Bar(name="Put Increase (Buildup)", x=pe_x, y=pe_crossed, marker_color="#22c55e", marker_pattern_shape="/", marker_pattern_fgcolor="black", width=16))
    fig_oi.add_trace(go.Bar(name="Put Decrease (Unwinding)", x=pe_x, y=pe_hollow, marker_color="rgba(0,0,0,0)", marker_line_color="#22c55e", marker_line_width=1.5, width=16))

    fig_oi.add_trace(go.Bar(name="Call Base OI", x=ce_x, y=ce_solid, marker_color="#ef4444", width=16))
    fig_oi.add_trace(go.Bar(name="Call Increase (Buildup)", x=ce_x, y=ce_crossed, marker_color="#ef4444", marker_pattern_shape="/", marker_pattern_fgcolor="white", width=16))
    fig_oi.add_trace(go.Bar(name="Call Decrease (Unwinding)", x=ce_x, y=ce_hollow, marker_color="rgba(0,0,0,0)", marker_line_color="#ef4444", marker_line_width=1.5, width=16))

    fig_oi.update_layout(
        title=dict(text="📊 Institutional 3-Phase Open Interest (10 Strikes Left & Right)", font=dict(size=14, color="#ffffff"), y=0.98),
        height=480, template="plotly_dark", barmode="stack", margin=dict(l=10, r=10, t=65, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        yaxis=dict(title="Contracts (OI)", tickvals=[0, 2000000, 4000000, 6000000, 8000000, 10000000, 12000000, 14000000, 16000000],
                   ticktext=["0", "20L", "40L", "60L", "80L", "1Cr", "1.2Cr", "1.4Cr", "1.6Cr"], gridcolor="#1f2937", fixedrange=True),
        xaxis=dict(title="Strike Prices", tickmode="array", tickvals=strikes, ticktext=[str(s) for s in strikes], tickangle=-45,
                   range=[strikes[0] - 35, strikes[-1] + 35], gridcolor="#1f2937", fixedrange=True),
        shapes=[dict(type="line", x0=fut_price, x1=fut_price, y0=0, y1=1, yref="paper", line=dict(color="#94a3b8", width=1.5, dash="dash"))],
        annotations=[dict(x=fut_price, y=1, yref="paper", text=f"NIFTY FUT {fut_price:.2f}", showarrow=False, font=dict(color="#94a3b8", size=11), yshift=10)]
    )
    return fig_oi

def render_scalp_chart(times_dt, put_prices, call_prices, volumes, atm_strike):
    if not times_dt or len(times_dt) < 2:
        times_dt = [datetime.now(timezone.utc).astimezone(IST) - timedelta(minutes=i) for i in range(5, -1, -1)]
        put_prices = [0.0] * 6; call_prices = [0.0] * 6; volumes = [1] * 6

    times_str = [t.strftime("%I:%M %p") for t in times_dt]
    put_poc = float(np.round(np.average(put_prices, weights=volumes), 2)) if sum(volumes) > 0 else 0.0
    call_poc = float(np.round(np.average(call_prices, weights=volumes), 2)) if sum(volumes) > 0 else 0.0
    straddle_arr = np.array(put_prices) + np.array(call_prices)
    vol_arr = np.array(volumes)
    straddle_vwap_arr = np.cumsum(straddle_arr * vol_arr) / np.cumsum(vol_arr) if sum(volumes) > 0 else straddle_arr
    straddle_tloc = float(np.round(np.mean(straddle_arr[:12]), 2)) if len(straddle_arr) >= 12 else float(np.round(np.mean(straddle_arr), 2))
    delta_force = np.zeros(len(times_dt))
    cvd_line = np.zeros(len(times_dt))
    ts_dots_put = np.full(len(times_dt), np.nan)
    ts_dots_call = np.full(len(times_dt), np.nan)

    for i in range(1, len(times_dt)):
        if put_prices[i] >= put_poc and put_poc > 0:
            ts_dots_put[i] = put_prices[i] + 1.2
        if call_prices[i] >= call_poc and call_poc > 0:
            ts_dots_call[i] = call_prices[i] + 1.2

    fig_scalp = make_subplots(
        rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.50, 0.25, 0.25],
        subplot_titles=(f"Dual Option vs Real Volume POC (ATM {atm_strike})", "Combined Straddle vs Real VWAP & TLOC", "SMI Force & CVD Divergence")
    )
    fig_scalp.add_trace(go.Scatter(x=times_str, y=put_prices, name="PUT CMP", line=dict(color="#ff4d4d", width=2)), row=1, col=1)
    fig_scalp.add_trace(go.Scatter(x=times_str, y=call_prices, name="CALL CMP", line=dict(color="#00ff7f", width=2)), row=1, col=1)
    fig_scalp.add_hline(y=put_poc, line_dash="dash", line_color="#ff9999", annotation_text=f"PUT POC ({put_poc:.2f})", row=1, col=1)
    fig_scalp.add_hline(y=call_poc, line_dash="dash", line_color="#99ff99", annotation_text=f"CALL POC ({call_poc:.2f})", row=1, col=1)
    fig_scalp.add_trace(go.Scatter(x=times_str, y=ts_dots_put, mode="markers", marker=dict(color="#00ff00", size=8, symbol="circle"), name="TS PE Trigger"), row=1, col=1)
    fig_scalp.add_trace(go.Scatter(x=times_str, y=ts_dots_call, mode="markers", marker=dict(color="#00ff7f", size=8, symbol="diamond"), name="TS CE Trigger"), row=1, col=1)

    fig_scalp.add_trace(go.Scatter(x=times_str, y=straddle_arr, name="Straddle (CE+PE)", line=dict(color="#ffa500", width=1.5)), row=2, col=1)
    fig_scalp.add_trace(go.Scatter(x=times_str, y=straddle_vwap_arr, name="Straddle VWAP", line=dict(color="#ffff00", dash="dot", width=1.5)), row=2, col=1)
    fig_scalp.add_hline(y=straddle_tloc, line_dash="dash", line_color="#ff4444", annotation_text=f"TLOC ({straddle_tloc:.2f})", row=2, col=1)

    bar_colors = np.where(delta_force >= 0, "#00ff7f", "#ff4d4d")
    fig_scalp.add_trace(go.Bar(x=times_str, y=delta_force, marker_color=bar_colors, name="SMI Delta"), row=3, col=1)
    fig_scalp.add_trace(go.Scatter(x=times_str, y=cvd_line / 10, name="CVD Divergence", line=dict(color="#00e5ff", width=1.5)), row=3, col=1)

    min_p1 = max(0, min(min(put_prices), min(call_prices), call_poc, put_poc) - 5)
    max_p1 = max(max(put_prices), max(call_prices), call_poc, put_poc) + 5
    if min_p1 == max_p1:
        min_p1, max_p1 = 0, 100

    fig_scalp.update_layout(
        height=640, template="plotly_dark", margin=dict(l=8, r=8, t=26, b=8),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis=dict(fixedrange=True), yaxis=dict(fixedrange=True),
        xaxis2=dict(fixedrange=True), yaxis2=dict(fixedrange=True),
        xaxis3=dict(fixedrange=True), yaxis3=dict(fixedrange=True)
    )
    fig_scalp.update_yaxes(range=[min_p1, max_p1], row=1, col=1, fixedrange=True)
    fig_scalp.update_xaxes(showticklabels=False, row=1, col=1, fixedrange=True)
    fig_scalp.update_xaxes(showticklabels=False, row=2, col=1, fixedrange=True)
    fig_scalp.update_xaxes(showticklabels=True, tickangle=0, nticks=5, row=3, col=1, fixedrange=True)
    return fig_scalp

# -------------------------------------------------------------
# 10. HEADER & DASHBOARD PLACEHOLDERS
# -------------------------------------------------------------
(nifty_spot, fut_price, fut_is_real, atm_strike, expiry_str, call_ltp, put_ltp,
 ce_token, pe_token, ce_symbol, pe_symbol, is_expiry_today) = get_live_market_snapshot(smart_api, scrip_df)
(strikes, pe_solid, pe_crossed, pe_hollow, ce_solid, ce_crossed, ce_hollow,
 live_cp, live_pp, live_pcr, total_ce_oi, total_pe_oi, ce_oi_dict, pe_oi_dict,
 matrix_flow_data, real_max_pain, atm_ce_vol, atm_pe_vol, is_live) = fetch_live_oi_and_power(smart_api, scrip_df, atm_strike, nifty_spot, fut_price)

st.title("⚡ SHK TRADE LABS")
conn_badge = "🟢 Angel One SmartAPI Feed (IST)" if smart_api else f"🟡 Feed Status: {auth_log}"
st.caption(f"Session Status: {conn_badge}")

atm_header_box = st.empty()
data_quality_box = st.empty()
breadth_box = st.empty()
order_flow_matrix_box = st.empty()
checkpoints_box = st.empty()
metrics_box = st.empty()
oi_summary_box = st.empty()
oi_chart_box = st.empty()
chart_box = st.empty()
table_box = st.empty()

base_t = get_current_ist()
if "live_candle_buffer" not in st.session_state:
    st.session_state.live_candle_buffer = {"times": [], "calls": [], "puts": [], "vols": []}
if "matrix_history" not in st.session_state:
    st.session_state.matrix_history = []
if "last_minute_recorded" not in st.session_state:
    st.session_state.last_minute_recorded = get_current_ist().minute
if "last_n50_breadth" not in st.session_state:
    st.session_state.last_n50_breadth = (0, 0, "NEUTRAL", 0, 0, 0, 0, 0, 0)
if "last_breadth_update_ts" not in st.session_state:
    st.session_state.last_breadth_update_ts = 0.0
if "last_oi_update_ts" not in st.session_state:
    st.session_state.last_oi_update_ts = 0.0
if "last_atm_vol_snapshot" not in st.session_state:
    st.session_state.last_atm_vol_snapshot = 0

def get_status_badge_html(status_text):
    if status_text == "BULLISH":
        return '<span class="badge-bullish-tag">BULLISH</span>'
    elif status_text == "BEARISH":
        return '<span class="badge-bearish-tag">BEARISH</span>'
    else:
        return '<span class="badge-neutral-tag">NEUTRAL</span>'

# -------------------------------------------------------------
# 11. INITIAL RENDERING
# -------------------------------------------------------------
live_vix, live_vix_chg = get_live_india_vix(smart_api)

initial_fig_oi = render_oi_chart(strikes, pe_solid, pe_crossed, pe_hollow, ce_solid, ce_crossed, ce_hollow, fut_price)
oi_chart_box.plotly_chart(initial_fig_oi, key="init_oi_chart", config={"displayModeBar": False, "staticPlot": False})

times_dt = st.session_state.live_candle_buffer["times"]
put_prices = st.session_state.live_candle_buffer["puts"]
call_prices = st.session_state.live_candle_buffer["calls"]
volumes = st.session_state.live_candle_buffer["vols"]

initial_fig_scalp = render_scalp_chart(times_dt, put_prices, call_prices, volumes, atm_strike)
chart_box.plotly_chart(initial_fig_scalp, key="init_scalp_chart", config={"displayModeBar": False, "staticPlot": False})

cur_call_power, cur_put_power = live_cp, live_pp
sentiment_tag = "🔴 Put Order Wall Strong" if cur_put_power > cur_call_power else ("🟢 Call Order Wall Strong" if cur_call_power > cur_put_power else "🟡 Imbalance Neutral")
loop_tick = 0

# -------------------------------------------------------------
# 12. STREAMING LOOP
# -------------------------------------------------------------
OI_POLL_SECONDS = 3

while True:
    loop_tick += 1
    current_time_ist = get_current_ist()
    market_active, market_msg = is_market_open()
    current_timestamp = time.time()

    (nifty_spot, fut_price, fut_is_real, atm_strike, expiry_str, new_call, new_put,
     ce_token, pe_token, ce_symbol, pe_symbol, is_expiry_today) = get_live_market_snapshot(smart_api, scrip_df)
    live_vix, live_vix_chg = get_live_india_vix(smart_api)

    if market_active:
        if (current_timestamp - st.session_state.last_oi_update_ts) >= OI_POLL_SECONDS:
            (strikes, pe_solid, pe_crossed, pe_hollow, ce_solid, ce_crossed, ce_hollow,
             live_cp, live_pp, live_pcr, total_ce_oi, total_pe_oi, ce_oi_dict, pe_oi_dict,
             matrix_flow_data, real_max_pain, atm_ce_vol, atm_pe_vol, is_live) = fetch_live_oi_and_power(smart_api, scrip_df, atm_strike, nifty_spot, fut_price)
            st.session_state.last_oi_update_ts = current_timestamp

        cur_call_power, cur_put_power = live_cp, live_pp
        sentiment_tag = "🔴 Put Order Wall Strong" if cur_put_power > cur_call_power else ("🟢 Call Order Wall Strong" if cur_call_power > cur_put_power else "🟡 Imbalance Neutral")

        if (current_timestamp - st.session_state.last_breadth_update_ts) >= 5:
            prev_vals = (st.session_state.last_n50_breadth[0], st.session_state.last_n50_breadth[1],
                         st.session_state.last_n50_breadth[3], st.session_state.last_n50_breadth[4],
                         st.session_state.last_n50_breadth[5], st.session_state.last_n50_breadth[6],
                         st.session_state.last_n50_breadth[7], st.session_state.last_n50_breadth[8])
            st.session_state.last_n50_breadth = fetch_nifty_50_breadth_and_heavyweights(smart_api, nifty50_df, prev_vals)
            st.session_state.last_breadth_update_ts = current_timestamp

        if current_time_ist.minute != st.session_state.last_minute_recorded:
            st.session_state.matrix_history.append({
                "Time": (current_time_ist - timedelta(minutes=1)).strftime("%I:%M %p"),
                "Call Power": cur_call_power, "Put Power": cur_put_power, "Sentiment": sentiment_tag
            })
            if len(st.session_state.matrix_history) > 4:
                st.session_state.matrix_history.pop(0)

            if new_call > 0 and new_put > 0:
                tot_atm_vol = atm_ce_vol + atm_pe_vol
                minute_real_vol = max(1, tot_atm_vol - st.session_state.last_atm_vol_snapshot) if st.session_state.last_atm_vol_snapshot > 0 else max(1, tot_atm_vol)
                st.session_state.last_atm_vol_snapshot = tot_atm_vol

                st.session_state.live_candle_buffer["times"].append(current_time_ist)
                st.session_state.live_candle_buffer["calls"].append(new_call)
                st.session_state.live_candle_buffer["puts"].append(new_put)
                st.session_state.live_candle_buffer["vols"].append(minute_real_vol)

                if len(st.session_state.live_candle_buffer["times"]) > 35:
                    st.session_state.live_candle_buffer["times"].pop(0)
                    st.session_state.live_candle_buffer["calls"].pop(0)
                    st.session_state.live_candle_buffer["puts"].pop(0)
                    st.session_state.live_candle_buffer["vols"].pop(0)

            st.session_state.last_minute_recorded = current_time_ist.minute

            updated_fig_oi = render_oi_chart(strikes, pe_solid, pe_crossed, pe_hollow, ce_solid, ce_crossed, ce_hollow, fut_price)
            if updated_fig_oi:
                oi_chart_box.plotly_chart(updated_fig_oi, key=f"oi_plot_{loop_tick}", config={"displayModeBar": False, "staticPlot": False})

            times_dt = st.session_state.live_candle_buffer["times"]
            put_prices = st.session_state.live_candle_buffer["puts"]
            call_prices = st.session_state.live_candle_buffer["calls"]
            volumes = st.session_state.live_candle_buffer["vols"]

            updated_fig_scalp = render_scalp_chart(times_dt, put_prices, call_prices, volumes, atm_strike)
            if updated_fig_scalp:
                chart_box.plotly_chart(updated_fig_scalp, key=f"scalp_plot_{loop_tick}", config={"displayModeBar": False, "staticPlot": False})
    else:
        cur_call_power, cur_put_power = live_cp, live_pp

    times_dt = st.session_state.live_candle_buffer["times"]
    put_prices = st.session_state.live_candle_buffer["puts"]
    call_prices = st.session_state.live_candle_buffer["calls"]
    volumes = st.session_state.live_candle_buffer["vols"]

    if len(put_prices) > 0 and sum(volumes) > 0:
        put_poc = float(np.round(np.average(put_prices, weights=volumes), 2))
        call_poc = float(np.round(np.average(call_prices, weights=volumes), 2))
        straddle_arr = np.array(put_prices) + np.array(call_prices)
        straddle_cmp = float(np.round(new_call + new_put, 2))
        straddle_vwap = float(np.round(np.cumsum(straddle_arr * np.array(volumes))[-1] / np.sum(volumes), 2))
        straddle_tloc = float(np.round(np.mean(straddle_arr[:12]), 2))
    else:
        put_poc, call_poc = 0.0, 0.0
        straddle_cmp, straddle_vwap, straddle_tloc = 0.0, 0.0, 0.0

    # Checkpoints
    cp1_val = f"CE Net: {format_indian_number(cur_call_power)} | PE Net: {format_indian_number(cur_put_power)}"
    cp1_status = "BULLISH" if cur_call_power > 0 and cur_put_power < 0 else ("BEARISH" if cur_put_power > 0 and cur_call_power < 0 else "NEUTRAL")

    if ce_oi_dict and max(ce_oi_dict.values(), default=0) > 0:
        call_wall = max(ce_oi_dict, key=ce_oi_dict.get)
    else:
        call_wall = atm_strike
    if pe_oi_dict and max(pe_oi_dict.values(), default=0) > 0:
        put_wall = max(pe_oi_dict, key=pe_oi_dict.get)
    else:
        put_wall = atm_strike

    cp2_val = f"Spot: {nifty_spot:.1f} | Wall: {put_wall} - {call_wall}"
    cp2_status = "BULLISH" if nifty_spot >= call_wall and call_wall > 0 else ("BEARISH" if nifty_spot <= put_wall and put_wall > 0 else "NEUTRAL")

    cp3_val = f"CE: ₹{new_call:.1f} (POC: ₹{call_poc:.1f}) | PE: ₹{new_put:.1f} (POC: ₹{put_poc:.1f})"
    cp3_status = "BULLISH" if new_call > call_poc and new_put < put_poc and call_poc > 0 else ("BEARISH" if new_put > put_poc and new_call < call_poc and put_poc > 0 else "NEUTRAL")

    cp4_val = f"Straddle: ₹{straddle_cmp:.1f} | VWAP: ₹{straddle_vwap:.1f} | TLOC: ₹{straddle_tloc:.1f}"
    straddle_expanding = straddle_cmp > straddle_vwap and straddle_cmp > straddle_tloc and straddle_vwap > 0
    call_pull = (new_call - call_poc) if call_poc > 0 else 0.0
    put_pull = (new_put - put_poc) if put_poc > 0 else 0.0
    if straddle_expanding and call_pull > put_pull:
        cp4_status = "BULLISH"
    elif straddle_expanding and put_pull > call_pull:
        cp4_status = "BEARISH"
    else:
        cp4_status = "NEUTRAL"

    cp5_val = f"Order Flow Delta: {format_indian_number(cur_call_power - cur_put_power)} contracts"
    cp5_status = "BULLISH" if (cur_call_power - cur_put_power) > 200000 else ("BEARISH" if (cur_put_power - cur_call_power) > 200000 else "NEUTRAL")

    dist_pain = abs(nifty_spot - real_max_pain)
    cp6_val = f"Max Pain: {real_max_pain} (Dist: {dist_pain:.1f} pts)"
    cp6_status = "NEUTRAL" if (is_expiry_today and current_time_ist.time() >= dtime(13, 0) and dist_pain <= 30) else ("BULLISH" if cp3_status == "BULLISH" else "BEARISH")

    cp7_val = f"India VIX: {live_vix:.2f} ({live_vix_chg:+.2f})"
    cp7_status = "BULLISH" if live_vix >= 11.5 else "NEUTRAL"

    if new_put > put_poc and cur_put_power > cur_call_power and put_poc > 0:
        unwinding_status = "🔥 Put Long Buildup (Heavy Put Buying)"
        multi_trend, multi_class = "BEARISH", "status-bearish"
    elif new_call > call_poc and cur_call_power > cur_put_power and call_poc > 0:
        unwinding_status = "🚀 Call Long Buildup (Heavy Call Buying)"
        multi_trend, multi_class = "BULLISH", "status-bullish"
    else:
        unwinding_status = "Neutral OI Distribution"
        multi_trend, multi_class = "MIXED", "status-wait"

    if new_put > put_poc and new_call < call_poc and put_poc > 0:
        atm_trend, atm_class = "BEARISH", "status-bearish"
    elif new_call > call_poc and new_put < put_poc and call_poc > 0:
        atm_trend, atm_class = "BULLISH", "status-bullish"
    else:
        atm_trend, atm_class = "SIDEWAYS", "status-wait"

    if market_active:
        if atm_trend == multi_trend and atm_trend in ["BULLISH", "BEARISH"]:
            market_status = "ACTIVE MOMENTUM"
            market_class = "status-bullish" if atm_trend == "BULLISH" else "status-bearish"
        else:
            market_status = "WAIT / MIXED"
            market_class = "status-wait"
    else:
        market_status = "MARKET CLOSED"
        market_class = "status-wait"

    # 1. Top Price Section
    fut_label = "FUT" if fut_is_real else "FUT (est.)"
    atm_header_box.markdown(f"""
    <div class="top-price-box">
        <div class="top-price-row">
            <span class="val-badge-neutral">NIFTY {nifty_spot:.2f}</span>
            <span class="val-badge-neutral">{fut_label} {fut_price:.2f}</span>
            <span class="val-badge-neutral">ATM {atm_strike}</span>
        </div>
        <div class="top-price-row">
            <span class="val-badge-call">CALL ₹{new_call:.2f}</span>
            <span class="val-badge-put">PUT ₹{new_put:.2f}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 1b. Data quality banner
    if not smart_api:
        data_quality_box.markdown(f'<div class="metric-grid"><div class="metric-card status-error">⚠️ No API session — {auth_log}</div></div>', unsafe_allow_html=True)
    elif market_active and not is_live:
        data_quality_box.markdown('<div class="metric-grid"><div class="metric-card status-error">⚠️ OI feed returned no live data this cycle</div></div>', unsafe_allow_html=True)
    elif not fut_is_real:
        data_quality_box.markdown('<div class="metric-grid"><div class="metric-card status-error">⚠️ Futures token not resolved — showing spot as fallback</div></div>', unsafe_allow_html=True)
    else:
        data_quality_box.empty()

    # 2. Nifty Breadth
    ab_op, bl_op, op_sent, ab_15, bl_15, h3_a, h3_b, h10_a, h10_b = st.session_state.last_n50_breadth
    buy_class = "touch-left-green-highlight" if ab_op > 34 else "touch-left-green-box"
    sell_class = "touch-right-orange-highlight" if bl_op > 34 else "touch-right-orange-box"

    breadth_html = (
        '<div class="checkpoint-container">'
        '<div class="breadth-flex-row"><span class="breadth-label">Nifty</span>'
        f'<div class="touch-box-group"><span class="{buy_class}">{ab_op}</span><span class="{sell_class}">{bl_op}</span></div>'
        f'<div style="margin-left: auto;">{get_status_badge_html(op_sent)}</div></div>'
        '<div class="breadth-flex-row"><span class="breadth-label">15 min</span>'
        f'<div class="touch-box-group"><span class="touch-left-green-box">{ab_15}</span><span class="touch-right-orange-box">{bl_15}</span></div></div>'
        '<div class="breadth-flex-row"><span class="breadth-label">3 weightage</span>'
        f'<div class="touch-box-group"><span class="touch-left-green-box">{h3_a}</span><span class="touch-right-orange-box">{h3_b}</span></div></div>'
        '<div class="breadth-flex-row"><span class="breadth-label">10 weightage</span>'
        f'<div class="touch-box-group"><span class="touch-left-green-box">{h10_a}</span><span class="touch-right-orange-box">{h10_b}</span></div></div>'
        '<div class="power-live-row">'
        f'<span>Call Net Order Power: <span class="call-buyer-badge">{format_indian_number(cur_call_power)}</span></span>'
        f'<span>Put Net Order Power: <span class="put-buyer-badge">{format_indian_number(cur_put_power)}</span></span>'
        f'<span style="margin-left: auto;">{sentiment_tag}</span></div>'
        '</div>'
    )
    breadth_box.markdown(breadth_html, unsafe_allow_html=True)

    # 2b. Option Order Flow Pressure & Aggression Matrix (Dynamic Highlight & Row Borders)
    rows_parts = []
    alert_msgs = []
    
    num_rows = len(matrix_flow_data) if matrix_flow_data else 6
    tot_ce_pct = sum(v["CE_PRESSURE"] for v in matrix_flow_data.values())
    tot_pe_pct = sum(v["PE_PRESSURE"] for v in matrix_flow_data.values())
    tot_ce_sc = sum(v["CE_SCORE"] for v in matrix_flow_data.values())
    tot_pe_sc = sum(v["PE_SCORE"] for v in matrix_flow_data.values())

    avg_ce_pct = int(round(tot_ce_pct / max(1, num_rows)))
    avg_pe_pct = int(round(tot_pe_pct / max(1, num_rows)))
    avg_ce_sc = int(round(tot_ce_sc / max(1, num_rows)))
    avg_pe_sc = int(round(tot_pe_sc / max(1, num_rows)))

    # Header section border conditions
    ce_pct_win = avg_ce_pct > avg_pe_pct
    pe_pct_win = avg_pe_pct > avg_ce_pct
    ce_sc_win = avg_ce_sc > avg_pe_sc
    pe_sc_win = avg_pe_sc > avg_ce_sc
    ce_both_win = ce_pct_win and ce_sc_win
    pe_both_win = pe_pct_win and pe_sc_win

    ce_hdr_class = "hdr-green-border" if ce_both_win else ""
    pe_hdr_class = "hdr-orange-border" if pe_both_win else ""
    ce_pct_hdr_class = "hdr-green-border" if ce_pct_win else ""
    pe_pct_hdr_class = "hdr-orange-border" if pe_pct_win else ""
    ce_sc_hdr_class = "hdr-green-border" if ce_sc_win else ""
    pe_sc_hdr_class = "hdr-orange-border" if pe_sc_win else ""

    for s in sorted(matrix_flow_data.keys()):
        item = matrix_flow_data[s]
        ce_sc, pe_sc = item["CE_SCORE"], item["PE_SCORE"]
        ce_pct, pe_pct = item["CE_PRESSURE"], item["PE_PRESSURE"]
        
        ce_cls = "score-badge-high" if ce_sc >= 65 else ("score-badge-low" if ce_sc <= 35 else "score-badge-mid")
        pe_cls = "score-badge-high" if pe_sc >= 65 else ("score-badge-low" if pe_sc <= 35 else "score-badge-mid")

        if ce_pct >= 70 and "Buildup" in item["CE_REGIME"]:
            alert_msgs.append(f"🔥 Aggressive CE Buying at <b>{s} CE</b> ({ce_pct}% Pressure)")
        if pe_pct >= 70 and "Buildup" in item["PE_REGIME"]:
            alert_msgs.append(f"🚨 Aggressive PE Buying at <b>{s} PE</b> ({pe_pct}% Pressure)")

        # Row comparison border conditions
        row_ce_pct_win = ce_pct > pe_pct
        row_pe_pct_win = pe_pct > ce_pct
        row_ce_sc_win = ce_sc > pe_sc
        row_pe_sc_win = pe_sc > ce_sc

        ce_pct_cell_html = f"<span class='cell-green-border'>{ce_pct}%</span>" if row_ce_pct_win else f"<span>{ce_pct}%</span>"
        pe_pct_cell_html = f"<span class='cell-orange-border'>{pe_pct}%</span>" if row_pe_pct_win else f"<span>{pe_pct}%</span>"
        
        ce_sc_cell_html = f"<span class='cell-green-border'><span class='{ce_cls}'>{ce_sc}</span></span>" if row_ce_sc_win else f"<span class='{ce_cls}'>{ce_sc}</span>"
        pe_sc_cell_html = f"<span class='cell-orange-border'><span class='{pe_cls}'>{pe_sc}</span></span>" if row_pe_sc_win else f"<span class='{pe_cls}'>{pe_sc}</span>"

        is_atm = (s == atm_strike)
        row_class = "atm-matrix-row" if is_atm else ""
        atm_badge = "<span style='font-size:10px; color:#38bdf8; font-weight:900;'>[ATM]</span>" if is_atm else f"<span style='font-size:10px; color:#64748b;'>({item['TYPE']})</span>"

        rows_parts.append(
            f"<tr class='{row_class}'>"
            f"<td style='color:#00ff7f;'>{ce_pct_cell_html}</td>"
            f"<td>{ce_sc_cell_html}</td>"
            f"<td style='font-size:11px; color:#94a3b8;'>{item['CE_REGIME']}</td>"
            f"<td style='color:#e2e8f0; font-weight:900;'>{s} {atm_badge}</td>"
            f"<td style='font-size:11px; color:#94a3b8;'>{item['PE_REGIME']}</td>"
            f"<td>{pe_sc_cell_html}</td>"
            f"<td style='color:#ff9800;'>{pe_pct_cell_html}</td>"
            f"</tr>"
        )

    alert_banner_html = f"<div class='alert-banner'>{' | '.join(alert_msgs)}</div>" if alert_msgs else ""
    table_rows_str = "".join(rows_parts)

    flow_table_html = (
        f"<div class='checkpoint-container'>"
        f"{alert_banner_html}"
        f"<table class='flow-table'>"
        f"<thead>"
        f"<tr>"
        f"<th colspan='3' style='text-align:left; padding-left:8px;'>"
        f"<span class='{ce_hdr_class}' style='color:#00ff7f; font-size:13px; font-weight:900; margin-right:12px;'>CALL AGGRESSION</span>"
        f"<span class='{ce_pct_hdr_class}' style='color:#00ff7f; font-weight:900; font-size:12px; margin-right:8px;'>{avg_ce_pct}%</span>"
        f"<span class='{ce_sc_hdr_class}' style='color:#ffffff; font-weight:900; font-size:12px;'>{avg_ce_sc}</span>"
        f"</th>"
        f"<th rowspan='2' style='font-size:13px;'>STRIKE</th>"
        f"<th colspan='3' style='text-align:right; padding-right:8px;'>"
        f"<span class='{pe_sc_hdr_class}' style='color:#ff9800; font-weight:900; font-size:12px; margin-right:8px;'>{avg_pe_sc}</span>"
        f"<span class='{pe_pct_hdr_class}' style='color:#ff9800; font-weight:900; font-size:12px; margin-right:12px;'>{avg_pe_pct}%</span>"
        f"<span class='{pe_hdr_class}' style='color:#ff9800; font-size:13px; font-weight:900;'>PUT AGGRESSION</span>"
        f"</th>"
        f"</tr>"
        f"<tr>"
        f"<th>BUY %</th><th>SCORE</th><th>REGIME</th>"
        f"<th>REGIME</th><th>SCORE</th><th>BUY %</th>"
        f"</tr>"
        f"</thead>"
        f"<tbody>{table_rows_str}</tbody>"
        f"</table>"
        f"</div>"
    )
    order_flow_matrix_box.markdown(flow_table_html, unsafe_allow_html=True)

    # 3. 7 Quant Institutional Edge Checkpoints
    checkpoints_html = (
        f"<div class='checkpoint-container'>"
        f"<div style='font-size:15px; font-weight:800; color:#58a6ff; margin-bottom:8px;'>🎯 7 Institutional Edge Checkpoints</div>"
        f"<div class='checkpoint-row'><div>1. Multi-Strike Unwinding Filter</div><div style='display:flex; align-items:center;'><span class='cp-val-text'>{cp1_val}</span> {get_status_badge_html(cp1_status)}</div></div>"
        f"<div class='checkpoint-row'><div>2. Gamma Regime Filter (OI Walls)</div><div style='display:flex; align-items:center;'><span class='cp-val-text'>{cp2_val}</span> {get_status_badge_html(cp2_status)}</div></div>"
        f"<div class='checkpoint-row'><div>3. ATM Micro-Price vs Real Volume POC</div><div style='display:flex; align-items:center;'><span class='cp-val-text'>{cp3_val}</span> {get_status_badge_html(cp3_status)}</div></div>"
        f"<div class='checkpoint-row'><div>4. Straddle Value vs VWAP & TLOC</div><div style='display:flex; align-items:center;'><span class='cp-val-text'>{cp4_val}</span> {get_status_badge_html(cp4_status)}</div></div>"
        f"<div class='checkpoint-row'><div>5. Order Book Imbalance (Net Power)</div><div style='display:flex; align-items:center;'><span class='cp-val-text'>{cp5_val}</span> {get_status_badge_html(cp5_status)}</div></div>"
        f"<div class='checkpoint-row'><div>6. Expiry Day Full-Chain Max Pain Guard</div><div style='display:flex; align-items:center;'><span class='cp-val-text'>{cp6_val}</span> {get_status_badge_html(cp6_status)}</div></div>"
        f"<div class='checkpoint-row'><div>7. IV Skew & Volatility Alignment</div><div style='display:flex; align-items:center;'><span class='cp-val-text'>{cp7_val}</span> {get_status_badge_html(cp7_status)}</div></div>"
        f"</div>"
    )
    checkpoints_box.markdown(checkpoints_html, unsafe_allow_html=True)

    # 4. Metrics Grid
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

    # 5. Institutional OI Metric Bar
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

    # 6. Live Power Matrix Table
    live_time_label = f"🔴 LIVE ({current_time_ist.strftime('%I:%M:%S %p')})" if market_active else f"⏸️ CLOSED ({current_time_ist.strftime('%I:%M:%S %p')})"
    table_rows = [{
        "Time (IST)": live_time_label,
        "Call Power (CE Contracts)": format_indian_number(cur_call_power),
        "Put Power (PE Contracts)": format_indian_number(cur_put_power),
        "Market Sentiment": sentiment_tag
    }]
    for hist in reversed(st.session_state.matrix_history):
        table_rows.append({
            "Time (IST)": hist["Time"],
            "Call Power (CE Contracts)": format_indian_number(hist["Call Power"]),
            "Put Power (PE Contracts)": format_indian_number(hist["Put Power"]),
            "Market Sentiment": hist["Sentiment"]
        })
    table_box.table(pd.DataFrame(table_rows))

    if not market_active:
        st.stop()

    time.sleep(1)
