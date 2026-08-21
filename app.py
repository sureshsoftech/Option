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
# 1. PAGE CONFIG & RESPONSIVE DARK THEME + THICK WHITE SCROLLBAR
# -------------------------------------------------------------

st.set_page_config(
    page_title="SHK TRADE LABS",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    .stApp { background-color: #0b0e14; color: #ffffff; }

    /* --- High-Visibility Thick White Scrollbar --- */
    ::-webkit-scrollbar { width: 14px !important; height: 14px !important; }
    ::-webkit-scrollbar-track { background: #11161f !important; border-left: 1px solid #30363d; }
    ::-webkit-scrollbar-thumb { background-color: #ffffff !important; border-radius: 7px !important; border: 2px solid #11161f !important; }
    ::-webkit-scrollbar-thumb:hover { background-color: #e2e8f0 !important; }
    html, body, [data-testid="stAppViewContainer"] { scrollbar-width: auto !important; scrollbar-color: #ffffff #11161f !important; }

    .top-price-box { background: linear-gradient(90deg, #161b22 0%, #1a2230 100%); border: 1px solid #30363d; border-radius: 8px; padding: 12px 16px; margin-bottom: 12px; display: flex; flex-direction: column; gap: 10px; }
    .top-price-row { display: flex; flex-direction: row; align-items: center; flex-wrap: wrap; gap: 16px; }
    .val-badge-neutral { background-color: #21262d; color: #e6edf3; padding: 6px 14px; border-radius: 6px; font-weight: 800; font-size: 15px; border: 1px solid #30363d; letter-spacing: 0.5px; }
    .val-badge-call { background-color: #006622; color: #ffffff; padding: 6px 16px; border-radius: 6px; font-weight: 800; font-size: 15px; letter-spacing: 0.5px; }
    .val-badge-put { background-color: #8b0000; color: #ffffff; padding: 6px 16px; border-radius: 6px; font-weight: 800; font-size: 15px; letter-spacing: 0.5px; }

    .oi-summary-card { background: #11161f; border: 1px solid #21262d; border-radius: 8px; padding: 10px 14px; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px; }
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

    .checkpoint-container { background: #11161f; border: 1px solid #21262d; border-radius: 8px; padding: 12px 16px; margin-top: 10px; margin-bottom: 12px; }
    .checkpoint-row { display: flex; justify-content: space-between; align-items: center; padding: 8px 4px; border-bottom: 1px solid #1f2937; font-size: 13px; font-weight: 600; gap: 10px; }
    .checkpoint-row:last-child { border-bottom: none; }

    .cp-val-text { color: #94a3b8; font-size: 12px; font-weight: 700; margin-right: 8px; }

    .badge-bullish-tag { background-color: #00ff7f; color: #000000; padding: 5px 14px; border-radius: 4px; font-weight: 800; font-size: 13px; letter-spacing: 0.5px; display: inline-block; text-align: center; }
    .badge-bearish-tag { background-color: #ff3333; color: #ffffff; padding: 5px 14px; border-radius: 4px; font-weight: 800; font-size: 13px; letter-spacing: 0.5px; display: inline-block; text-align: center; }
    .badge-neutral-tag { background-color: #4b5563; color: #ffffff; padding: 5px 12px; border-radius: 4px; font-weight: 700; font-size: 13px; }

    .num-box-buy { background-color: #000000; color: #00ff7f; border: 2px solid #00ff7f; padding: 4px 14px; border-radius: 6px; font-weight: 900; font-size: 20px; display: inline-block; text-align: center; min-width: 50px; }
    .num-box-buy-highlight { background-color: #00ff7f; color: #000000; border: 2px solid #00ff7f; padding: 4px 14px; border-radius: 6px; font-weight: 900; font-size: 20px; display: inline-block; text-align: center; min-width: 50px; }
    .num-box-sell { background-color: #000000; color: #ffffff; border: 2px solid #ff3333; padding: 4px 14px; border-radius: 6px; font-weight: 900; font-size: 20px; display: inline-block; text-align: center; min-width: 50px; }
    .num-box-sell-highlight { background-color: #ff3333; color: #ffffff; border: 2px solid #ff3333; padding: 4px 14px; border-radius: 6px; font-weight: 900; font-size: 20px; display: inline-block; text-align: center; min-width: 50px; }

    .heavy-box-green { background-color: #000000; color: #ffffff; border: 2px solid #00ff7f; padding: 4px 14px; border-radius: 6px; font-weight: 900; font-size: 20px; display: inline-block; text-align: center; min-width: 50px; }
    .heavy-box-red { background-color: #000000; color: #ffffff; border: 2px solid #ff3333; padding: 4px 14px; border-radius: 6px; font-weight: 900; font-size: 20px; display: inline-block; text-align: center; min-width: 50px; }

    .breadth-flex-row { display: flex; flex-direction: row; align-items: center; padding: 10px 4px; border-bottom: 1px solid #1f2937; font-size: 14px; gap: 12px; flex-wrap: wrap; }
    .breadth-flex-row:last-child { border-bottom: none; }
    .breadth-label { font-weight: 700; color: #e6edf3; font-size: 14px; }
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
# 3. DIRECT REST API SESSION ENGINE
# -------------------------------------------------------------

class AngelDirectClient:
    def __init__(self, jwt_token, api_key):
        self.jwt_token = jwt_token
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {jwt_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-UserType": "USER",
            "X-SourceID": "WEB",
            "X-ClientLocalIP": "127.0.0.1",
            "X-ClientPublicIP": "106.193.147.98",
            "X-MACAddress": "fe80::216e:6507:4b90:3719",
            "X-PrivateKey": api_key
        }

    def ltpData(self, exchange, tradingsymbol, symboltoken):
        url = "https://apiconnect.angelbroking.com/rest/secure/angelbroking/order/v1/getLtpData"
        payload = {"exchange": exchange, "tradingsymbol": tradingsymbol, "symboltoken": str(symboltoken)}
        try:
            r = requests.post(url, headers=self.headers, json=payload, timeout=5)
            return r.json()
        except Exception as e:
            return {"status": False, "message": str(e)}

    def getMarketData(self, mode, tokens_dict):
        url = "https://apiconnect.angelbroking.com/rest/secure/angelbroking/market/v1/quote/"
        sanitized_dict = {}
        for exch, t_list in tokens_dict.items():
            sanitized_dict[exch] = [str(x) for x in t_list]
        payload = {"mode": mode, "exchangeTokens": sanitized_dict}
        try:
            r = requests.post(url, headers=self.headers, json=payload, timeout=8)
            return r.json()
        except Exception as e:
            return {"status": False, "message": str(e)}

    def getCandleData(self, params):
        url = "https://apiconnect.angelbroking.com/rest/secure/angelbroking/historical/v1/getCandleData"
        try:
            r = requests.post(url, headers=self.headers, json=params, timeout=8)
            return r.json()
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
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-UserType": "USER",
            "X-SourceID": "WEB",
            "X-ClientLocalIP": "127.0.0.1",
            "X-ClientPublicIP": "106.193.147.98",
            "X-MACAddress": "fe80::216e:6507:4b90:3719",
            "X-PrivateKey": api_key
        }
        payload = {"clientcode": client_code, "password": pin, "totp": totp_val}
        res = requests.post(login_url, headers=headers, json=payload, timeout=8)
        data = res.json()

        if data.get("status") and "data" in data and "jwtToken" in data["data"]:
            client = AngelDirectClient(data["data"]["jwtToken"], api_key)
            return client, "Connected via Direct REST"
        else:
            err_msg = data.get("message", "Login Rejected")
            return None, f"Angel API: {err_msg}"
    except Exception as e:
        return None, f"REST Error: {str(e)}"


if "smart_api_obj" not in st.session_state or st.session_state.smart_api_obj is None:
    smart_api, auth_log = authenticate_angel()
    st.session_state.smart_api_obj = smart_api
    st.session_state.smart_api_log = auth_log
else:
    smart_api = st.session_state.smart_api_obj
    auth_log = st.session_state.smart_api_log

# -------------------------------------------------------------
# 4. SCRIP MASTER & NIFTY 50 EQUITIES LOADER
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


@st.cache_resource(ttl=3600 * 12)
def load_all_scrip_masters():
    url = "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"
    try:
        res = requests.get(url, timeout=12)
        if res.status_code == 200:
            df = pd.DataFrame(res.json())

            nifty_options = df[(df["name"] == "NIFTY") & (df["exch_seg"] == "NFO")].copy()
            nifty_options["strike"] = pd.to_numeric(nifty_options["strike"], errors="coerce") / 100.0

            n50_equities = df[(df["exch_seg"] == "NSE") & (df["symbol"].str.endswith("-EQ")) & (df["name"].isin(NIFTY_50_SYMBOLS))].copy()
            n50_df = n50_equities.drop_duplicates(subset=["name"]).head(50)

            return nifty_options, n50_df
    except Exception:
        pass
    return None, None


scrip_df, nifty50_df = load_all_scrip_masters()

# -------------------------------------------------------------
# 5. DATA RETRIEVAL & MARKET SNAPSHOT
# -------------------------------------------------------------

def get_live_india_vix(_api):
    # Fallback values are ONLY used if the API call fails / is unavailable.
    vix_val, vix_chg = 11.45, 0.06
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


def parse_expiry_date(exp_str):
    for fmt in ("%d%b%Y", "%d-%b-%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(str(exp_str).strip(), fmt).date()
        except Exception:
            continue
    return None


def get_live_market_snapshot(_api, scrip_data):
    # Fallback values are ONLY used before the first successful API response.
    nifty_spot = 24202.20
    fut_price = 24252.75
    expiry_str = "WEEKLY"
    call_ltp = 102.20
    put_ltp = 89.20
    call_vol = 0
    put_vol = 0
    ce_token, pe_token = None, None
    ce_symbol, pe_symbol = "", ""

    if _api:
        try:
            spot_data = _api.ltpData("NSE", "Nifty 50", "99926000")
            if spot_data and spot_data.get("status"):
                nifty_spot = float(spot_data["data"]["ltp"])
                fut_price = nifty_spot + 49.90
        except Exception:
            pass

    atm_strike = int(round(fut_price / 50.0) * 50)

    if _api and scrip_data is not None and not scrip_data.empty:
        try:
            today_date = get_current_ist().date()
            unique_expiries = scrip_data["expiry"].dropna().unique()

            parsed_expiries = []
            for exp in unique_expiries:
                d = parse_expiry_date(exp)
                if d and d >= today_date:
                    parsed_expiries.append((d, exp))

            parsed_expiries.sort(key=lambda x: x[0])

            if parsed_expiries:
                nearest_expiry = parsed_expiries[0][1]
                expiry_str = nearest_expiry

                ce_match = scrip_data[(scrip_data["expiry"] == nearest_expiry) &
                                       (scrip_data["strike"] == atm_strike) &
                                       (scrip_data["symbol"].str.endswith("CE"))]
                pe_match = scrip_data[(scrip_data["expiry"] == nearest_expiry) &
                                       (scrip_data["strike"] == atm_strike) &
                                       (scrip_data["symbol"].str.endswith("PE"))]

                # Use FULL quote mode instead of ltpData so we also get real traded volume.
                if not ce_match.empty:
                    ce_token = str(ce_match.iloc[0]["token"])
                    ce_symbol = ce_match.iloc[0]["symbol"]
                    ce_quote = _api.getMarketData("FULL", {"NFO": [ce_token]})
                    if ce_quote and ce_quote.get("status") and ce_quote.get("data", {}).get("fetched"):
                        itm = ce_quote["data"]["fetched"][0]
                        call_ltp = float(itm.get("ltp", call_ltp))
                        call_vol = int(itm.get("tradeVolume", itm.get("volume", 0)))

                if not pe_match.empty:
                    pe_token = str(pe_match.iloc[0]["token"])
                    pe_symbol = pe_match.iloc[0]["symbol"]
                    pe_quote = _api.getMarketData("FULL", {"NFO": [pe_token]})
                    if pe_quote and pe_quote.get("status") and pe_quote.get("data", {}).get("fetched"):
                        itm = pe_quote["data"]["fetched"][0]
                        put_ltp = float(itm.get("ltp", put_ltp))
                        put_vol = int(itm.get("tradeVolume", itm.get("volume", 0)))
        except Exception:
            pass

    return (nifty_spot, fut_price, atm_strike, expiry_str, call_ltp, put_ltp,
            call_vol, put_vol, ce_token, pe_token, ce_symbol, pe_symbol)


def fetch_recent_minute_candles(_api, symboltoken, minutes=25):
    """Pull real 1-minute historical candles from Angel One instead of seeding
    the chart buffer with a random walk. Returns (times, closes, volumes) or
    (None, None, None) if unavailable."""
    if not _api or not symboltoken:
        return None, None, None
    try:
        now_ist = get_current_ist()
        from_dt = now_ist - timedelta(minutes=minutes + 5)
        params = {
            "exchange": "NFO",
            "symboltoken": str(symboltoken),
            "interval": "ONE_MINUTE",
            "fromdate": from_dt.strftime("%Y-%m-%d %H:%M"),
            "todate": now_ist.strftime("%Y-%m-%d %H:%M"),
        }
        res = _api.getCandleData(params)
        if res and res.get("status") and res.get("data"):
            rows = res["data"][-(minutes + 1):]
            times = [datetime.strptime(r[0][:16].replace("T", " "), "%Y-%m-%d %H:%M").replace(tzinfo=IST) for r in rows]
            closes = [float(r[4]) for r in rows]
            vols = [int(r[5]) if len(r) > 5 else 0 for r in rows]
            return times, closes, vols
    except Exception:
        pass
    return None, None, None


# -------------------------------------------------------------
# 6. LIVE OI & ACCURATE 3-PHASE DELTA ENGINE
# -------------------------------------------------------------

def fetch_live_oi_and_power(_api, scrip_data, atm_strike):
    strikes = [int(atm_strike + (i * 50)) for i in range(-10, 11)]
    pe_oi_dict = {s: 0 for s in strikes}
    ce_oi_dict = {s: 0 for s in strikes}
    pe_chg_dict = {s: 0 for s in strikes}
    ce_chg_dict = {s: 0 for s in strikes}
    live_cp, live_pp = 0, 0
    is_live = False

    if _api and scrip_data is not None and not scrip_data.empty:
        try:
            today_date = get_current_ist().date()
            unique_expiries = scrip_data["expiry"].dropna().unique()
            parsed_expiries = []
            for exp in unique_expiries:
                d = parse_expiry_date(exp)
                if d and d >= today_date:
                    parsed_expiries.append((d, exp))
            parsed_expiries.sort(key=lambda x: x[0])

            if parsed_expiries:
                nearest_expiry = parsed_expiries[0][1]

                target_ce = scrip_data[(scrip_data["expiry"] == nearest_expiry) &
                                        (scrip_data["strike"].isin(strikes)) &
                                        (scrip_data["symbol"].str.endswith("CE"))]
                target_pe = scrip_data[(scrip_data["expiry"] == nearest_expiry) &
                                        (scrip_data["strike"].isin(strikes)) &
                                        (scrip_data["symbol"].str.endswith("PE"))]

                all_tokens = [str(x) for x in list(target_ce["token"].values) + list(target_pe["token"].values)]
                fetched_items = {}

                for chunk_i in range(0, len(all_tokens), 10):
                    sub_toks = all_tokens[chunk_i:chunk_i + 10]
                    res = _api.getMarketData("FULL", {"NFO": sub_toks})
                    if res and res.get("status") and "fetched" in res.get("data", {}):
                        for itm in res["data"]["fetched"]:
                            tok_id = str(itm.get("symbolToken", itm.get("token", "")))
                            if tok_id:
                                fetched_items[tok_id] = itm

                for _, row in target_ce.iterrows():
                    t_str = str(row["token"])
                    s_val = int(row["strike"])
                    if t_str in fetched_items:
                        itm = fetched_items[t_str]
                        oi = int(itm.get("opnInterest", itm.get("openInterest", 0)))
                        ce_oi_dict[s_val] = oi

                        # NOTE: prevOpenInterest is not always returned by the quote
                        # endpoint. When missing we fall back to an estimated prior OI
                        # (flagged fallback, not a substitute for real data).
                        if "prevOpenInterest" in itm or "prevOpnInterest" in itm:
                            prev_oi = int(itm.get("prevOpenInterest", itm.get("prevOpnInterest", oi)))
                        else:
                            prev_oi = int(oi * 0.92)  # fallback estimate only
                        ce_chg_dict[s_val] = oi - prev_oi

                        buy_q = int(itm.get("totBuyQuan", itm.get("totalBuyQty", 0)))
                        sell_q = int(itm.get("totSellQuan", itm.get("totalSellQty", 0)))
                        if abs(s_val - atm_strike) <= 100:
                            live_cp += (buy_q - sell_q)

                for _, row in target_pe.iterrows():
                    t_str = str(row["token"])
                    s_val = int(row["strike"])
                    if t_str in fetched_items:
                        itm = fetched_items[t_str]
                        oi = int(itm.get("opnInterest", itm.get("openInterest", 0)))
                        pe_oi_dict[s_val] = oi

                        if "prevOpenInterest" in itm or "prevOpnInterest" in itm:
                            prev_oi = int(itm.get("prevOpenInterest", itm.get("prevOpnInterest", oi)))
                        else:
                            prev_oi = int(oi * 0.94)  # fallback estimate only
                        pe_chg_dict[s_val] = oi - prev_oi

                        buy_q = int(itm.get("totBuyQuan", itm.get("totalBuyQty", 0)))
                        sell_q = int(itm.get("totSellQuan", itm.get("totalSellQty", 0)))
                        if abs(s_val - atm_strike) <= 100:
                            live_pp += (buy_q - sell_q)

                if sum(ce_oi_dict.values()) > 0 or sum(pe_oi_dict.values()) > 0 or live_cp != 0 or live_pp != 0:
                    is_live = True
        except Exception:
            pass

    pe_solid, pe_crossed, pe_hollow = [], [], []
    ce_solid, ce_crossed, ce_hollow = [], [], []

    for s in strikes:
        cur_pe = pe_oi_dict[s]
        chg_pe = pe_chg_dict[s]
        if chg_pe >= 0:
            pe_solid.append(max(0, cur_pe - chg_pe))
            pe_crossed.append(chg_pe)
            pe_hollow.append(0)
        else:
            pe_solid.append(cur_pe)
            pe_crossed.append(0)
            pe_hollow.append(abs(chg_pe))

        cur_ce = ce_oi_dict[s]
        chg_ce = ce_chg_dict[s]
        if chg_ce >= 0:
            ce_solid.append(max(0, cur_ce - chg_ce))
            ce_crossed.append(chg_ce)
            ce_hollow.append(0)
        else:
            ce_solid.append(cur_ce)
            ce_crossed.append(0)
            ce_hollow.append(abs(chg_ce))

    total_ce_oi = sum(ce_oi_dict.values())
    total_pe_oi = sum(pe_oi_dict.values())
    pcr_val = round(total_pe_oi / max(1, total_ce_oi), 2) if total_ce_oi > 0 else 0.0

    return strikes, pe_solid, pe_crossed, pe_hollow, ce_solid, ce_crossed, ce_hollow, live_cp, live_pp, pcr_val, total_ce_oi, total_pe_oi, is_live


# -------------------------------------------------------------
# 7. NIFTY 50 BREADTH & TOP 3 HEAVYWEIGHTS (2-BOX COUNTS)
# -------------------------------------------------------------

def fetch_nifty_50_breadth_and_heavyweights(_api, n50_df):
    # Fallback values are ONLY used if the API call fails / is unavailable.
    above_open = 18
    below_open = 32
    above_15m_high = 6
    below_15m_low = 18

    heavy_above_cnt = 1
    heavy_below_cnt = 2

    if _api and n50_df is not None and not n50_df.empty:
        try:
            tokens_list = [str(t) for t in list(n50_df["token"].values)[:50]]
            token_to_name = {str(row["token"]): row["name"] for _, row in n50_df.iterrows()}

            a_o, b_o, a_15, b_15 = 0, 0, 0, 0
            h_above, h_below = 0, 0
            target_heavy = ["HDFCBANK", "ICICIBANK", "RELIANCE"]

            for chunk_i in range(0, len(tokens_list), 15):
                sub_toks = tokens_list[chunk_i:chunk_i + 15]
                quote_res = _api.getMarketData("FULL", {"NSE": sub_toks})

                if quote_res and quote_res.get("status") and "fetched" in quote_res.get("data", {}):
                    for item in quote_res["data"]["fetched"]:
                        tok_id = str(item.get("symbolToken", item.get("token", "")))
                        ltp = float(item.get("ltp", 0))
                        opn = float(item.get("open", 0))
                        high = float(item.get("high", 0))
                        low = float(item.get("low", 0))

                        if ltp > 0 and opn > 0:
                            if ltp >= opn:
                                a_o += 1
                            else:
                                b_o += 1

                            range_15m_hi = opn + ((high - opn) * 0.5)
                            range_15m_lo = opn - ((opn - low) * 0.5)
                            if ltp >= range_15m_hi:
                                a_15 += 1
                            elif ltp <= range_15m_lo:
                                b_15 += 1

                            sym_name = token_to_name.get(tok_id, "")
                            if sym_name in target_heavy:
                                if ltp >= opn:
                                    h_above += 1
                                else:
                                    h_below += 1

            if (a_o + b_o) > 0:
                above_open = a_o
                below_open = b_o
                above_15m_high = a_15
                below_15m_low = b_15
                heavy_above_cnt = h_above
                heavy_below_cnt = h_below
        except Exception:
            pass

    open_sentiment = "BULLISH" if above_open >= 35 else ("BEARISH" if below_open >= 35 else "NEUTRAL")
    return above_open, below_open, open_sentiment, above_15m_high, below_15m_low, heavy_above_cnt, heavy_below_cnt


# -------------------------------------------------------------
# 8. LOCKED CHART GENERATION (Fixed Axes)
# -------------------------------------------------------------

def render_oi_chart(strikes, pe_solid, pe_crossed, pe_hollow, ce_solid, ce_crossed, ce_hollow, fut_price):
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
        height=480,
        template="plotly_dark",
        barmode="stack",
        margin=dict(l=10, r=10, t=65, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=10)),
        yaxis=dict(title="Contracts (OI)", tickvals=[0, 2000000, 4000000, 6000000, 8000000, 10000000, 12000000, 14000000, 16000000], ticktext=["0", "20L", "40L", "60L", "80L", "1Cr", "1.2Cr", "1.4Cr", "1.6Cr"], gridcolor="#1f2937", fixedrange=True),
        xaxis=dict(title="Strike Prices", tickmode="array", tickvals=strikes, ticktext=[str(s) for s in strikes], tickangle=-45, range=[strikes[0] - 35, strikes[-1] + 35], gridcolor="#1f2937", fixedrange=True),
        shapes=[dict(type="line", x0=fut_price, x1=fut_price, y0=0, y1=1, yref="paper", line=dict(color="#94a3b8", width=1.5, dash="dash"))],
        annotations=[dict(x=fut_price, y=1, yref="paper", text=f"NIFTY {fut_price:.2f}", showarrow=False, font=dict(color="#94a3b8", size=11), yshift=10)]
    )
    return fig_oi


def render_scalp_chart(times_dt, put_prices, call_prices, volumes, atm_strike, power_history):
    """power_history: list of (call_power - put_power) net-imbalance readings,
    same length as times_dt, used to derive a REAL order-flow force line
    instead of random noise."""
    times_str = [t.strftime("%I:%M %p") for t in times_dt]
    put_poc = float(np.round(np.average(put_prices, weights=volumes) if sum(volumes) > 0 else np.mean(put_prices), 2))
    call_poc = float(np.round(np.average(call_prices, weights=volumes) if sum(volumes) > 0 else np.mean(call_prices), 2))
    straddle_arr = np.array(put_prices) + np.array(call_prices)
    vol_arr = np.array(volumes, dtype=float)
    if vol_arr.sum() > 0:
        straddle_vwap_arr = np.cumsum(straddle_arr * vol_arr) / np.maximum(1, np.cumsum(vol_arr))
    else:
        straddle_vwap_arr = np.cumsum(straddle_arr) / np.arange(1, len(straddle_arr) + 1)
    straddle_tloc = float(np.round(np.mean(straddle_arr[:12]), 2))

    # Real order-flow "force": rate of change of the live call/put buy-sell
    # imbalance (live_cp - live_pp) recorded over time, smoothed with a
    # 3-point moving average. Replaces the previous np.random noise line.
    power_arr = np.array(power_history, dtype=float)
    if len(power_arr) >= 2:
        raw_force = np.diff(power_arr, prepend=power_arr[0]) / 1000.0
    else:
        raw_force = np.zeros(len(times_dt))
    if len(raw_force) >= 3:
        delta_force = np.convolve(raw_force, np.ones(3) / 3, mode='same')
    else:
        delta_force = raw_force
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
        subplot_titles=(f"Dual Option vs POC (ATM {atm_strike})", "Combined Straddle vs VWAP & TLOC", "Order-Flow Force & CVD (from live buy/sell imbalance)")
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
    fig_scalp.add_trace(go.Bar(x=times_str, y=delta_force, marker_color=bar_colors, name="Order-Flow Force"), row=3, col=1)
    fig_scalp.add_trace(go.Scatter(x=times_str, y=cvd_line / 10, name="CVD (cum. imbalance)", line=dict(color="#00e5ff", width=1.5)), row=3, col=1)

    min_p1 = min(min(put_prices), min(call_prices), call_poc, put_poc) - 5
    max_p1 = max(max(put_prices), max(call_prices), call_poc, put_poc) + 5

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


def get_status_badge_html(status_text):
    if status_text == "BULLISH":
        return '<span class="badge-bullish-tag">BULLISH</span>'
    elif status_text == "BEARISH":
        return '<span class="badge-bearish-tag">BEARISH</span>'
    else:
        return '<span class="badge-neutral-tag">NEUTRAL</span>'


# -------------------------------------------------------------
# 9. HEADER, STATE INIT & PLACEHOLDERS (runs ONCE per session)
# -------------------------------------------------------------

st.title("⚡ SHK TRADE LABS")
conn_badge = "🟢 Angel One SmartAPI Feed (IST)" if smart_api else f"🟡 Feed Status: {auth_log}"
st.caption(f"Session Status: {conn_badge}")

atm_header_box = st.empty()
breadth_box = st.empty()
checkpoints_box = st.empty()
metrics_box = st.empty()
oi_summary_box = st.empty()
oi_chart_box = st.empty()
chart_box = st.empty()
table_box = st.empty()
diag_box = st.empty()

# Diagnostic line: makes silent auth / scrip-master failures visible instead
# of just showing zeros with no explanation.
_scrip_status = "✅ Scrip master loaded" if (scrip_df is not None and not scrip_df.empty) else "❌ Scrip master FAILED to load (option chain will stay at 0)"
_auth_status = "✅ Angel One session active" if smart_api else f"❌ Angel One NOT connected — {auth_log}"
diag_box.caption(f"{_auth_status}  |  {_scrip_status}")

if "state_ready" not in st.session_state:
    base_t = get_current_ist()

    nifty_spot0, fut_price0, atm_strike0, expiry0, call_ltp0, put_ltp0, call_vol0, put_vol0, ce_token0, pe_token0, ce_symbol0, pe_symbol0 = get_live_market_snapshot(smart_api, scrip_df)
    strikes0, pe_solid0, pe_crossed0, pe_hollow0, ce_solid0, ce_crossed0, ce_hollow0, live_cp0, live_pp0, pcr0, tce0, tpe0, is_live0 = fetch_live_oi_and_power(smart_api, scrip_df, atm_strike0)

    # Try to seed the chart buffer with REAL historical 1-minute candles.
    ce_times, ce_closes, ce_vols = fetch_recent_minute_candles(smart_api, ce_token0, minutes=25)
    pe_times, pe_closes, pe_vols = fetch_recent_minute_candles(smart_api, pe_token0, minutes=25)

    if ce_times and pe_times:
        n = min(len(ce_times), len(pe_times))
        times_seed = ce_times[-n:]
        calls_seed = ce_closes[-n:]
        puts_seed = pe_closes[-n:]
        vols_seed = [c + p for c, p in zip(ce_vols[-n:], pe_vols[-n:])]
    else:
        # API history unavailable (e.g. before market opens / first load) -
        # flat-seed on the current LTP instead of a random walk, so the
        # buffer is honest (no fake movement) until real ticks arrive.
        n = 26
        times_seed = [base_t - timedelta(minutes=i) for i in range(n - 1, -1, -1)]
        calls_seed = [call_ltp0] * n
        puts_seed = [put_ltp0] * n
        vols_seed = [0] * n

    st.session_state.live_candle_buffer = {
        "times": times_seed,
        "calls": calls_seed,
        "puts": puts_seed,
        "vols": vols_seed,
    }
    st.session_state.power_history_buffer = [live_cp0 - live_pp0] * len(times_seed)

    st.session_state.matrix_history = [
        {"Time": (base_t - timedelta(minutes=4)).strftime("%I:%M %p"), "Call Power": live_cp0, "Put Power": live_pp0,
         "Sentiment": "🔴 Put Buyers Strong" if live_pp0 > live_cp0 else ("🟢 Call Buyers Strong" if live_cp0 > live_pp0 else "🟡 Imbalance Neutral")},
        {"Time": (base_t - timedelta(minutes=3)).strftime("%I:%M %p"), "Call Power": live_cp0, "Put Power": live_pp0,
         "Sentiment": "🔴 Put Buyers Strong" if live_pp0 > live_cp0 else ("🟢 Call Buyers Strong" if live_cp0 > live_pp0 else "🟡 Imbalance Neutral")},
        {"Time": (base_t - timedelta(minutes=2)).strftime("%I:%M %p"), "Call Power": live_cp0, "Put Power": live_pp0,
         "Sentiment": "🔴 Put Buyers Strong" if live_pp0 > live_cp0 else ("🟢 Call Buyers Strong" if live_cp0 > live_pp0 else "🟡 Imbalance Neutral")},
        {"Time": (base_t - timedelta(minutes=1)).strftime("%I:%M %p"), "Call Power": live_cp0, "Put Power": live_pp0,
         "Sentiment": "🔴 Put Buyers Strong" if live_pp0 > live_cp0 else ("🟢 Call Buyers Strong" if live_cp0 > live_pp0 else "🟡 Imbalance Neutral")},
    ]

    st.session_state.last_minute_recorded = base_t.minute
    st.session_state.last_n50_breadth = fetch_nifty_50_breadth_and_heavyweights(smart_api, nifty50_df)
    st.session_state.last_breadth_update_ts = 0.0
    st.session_state.loop_tick = 0
    st.session_state.state_ready = True

# -------------------------------------------------------------
# 10. LIVE FRAGMENT — only THIS block reruns every second, not the page
# -------------------------------------------------------------

@st.fragment(run_every=1)
def live_dashboard():
    try:
        _live_dashboard_body()
    except Exception as e:
        # A single failed tick (API hiccup, rate limit, transient network
        # error) no longer takes the whole app down — it just shows a
        # warning and retries on the next 1s tick.
        st.warning(f"⚠️ Update skipped this tick: {e}")


def _live_dashboard_body():
    st.session_state.loop_tick += 1
    loop_tick = st.session_state.loop_tick
    current_time_ist = get_current_ist()
    market_active, market_msg = is_market_open()
    current_timestamp = time.time()

    (nifty_spot, fut_price, atm_strike, expiry_str, new_call, new_put,
     new_call_vol, new_put_vol, ce_token, pe_token, ce_symbol, pe_symbol) = get_live_market_snapshot(smart_api, scrip_df)
    live_vix, live_vix_chg = get_live_india_vix(smart_api)

    strikes, pe_solid, pe_crossed, pe_hollow, ce_solid, ce_crossed, ce_hollow, live_cp, live_pp, live_pcr, total_ce_oi, total_pe_oi, is_live = fetch_live_oi_and_power(smart_api, scrip_df, atm_strike)
    cur_call_power = live_cp
    cur_put_power = live_pp
    sentiment_tag = "🔴 Put Buyers Strong" if cur_put_power > cur_call_power else ("🟢 Call Buyers Strong" if cur_call_power > cur_put_power else "🟡 Imbalance Neutral")

    if market_active:
        st.session_state.live_candle_buffer["calls"][-1] = new_call
        st.session_state.live_candle_buffer["puts"][-1] = new_put
        st.session_state.power_history_buffer[-1] = cur_call_power - cur_put_power

        if (current_timestamp - st.session_state.last_breadth_update_ts) >= 10:
            st.session_state.last_n50_breadth = fetch_nifty_50_breadth_and_heavyweights(smart_api, nifty50_df)
            st.session_state.last_breadth_update_ts = current_timestamp

        if current_time_ist.minute != st.session_state.last_minute_recorded:
            st.session_state.matrix_history.append({
                "Time": (current_time_ist - timedelta(minutes=1)).strftime("%I:%M %p"),
                "Call Power": cur_call_power,
                "Put Power": cur_put_power,
                "Sentiment": sentiment_tag
            })
            if len(st.session_state.matrix_history) > 4:
                st.session_state.matrix_history.pop(0)

            st.session_state.live_candle_buffer["times"].append(current_time_ist)
            st.session_state.live_candle_buffer["calls"].append(new_call)
            st.session_state.live_candle_buffer["puts"].append(new_put)
            # Real traded volume for this minute (CE + PE), pulled from the
            # live quote instead of a random integer.
            st.session_state.live_candle_buffer["vols"].append(int(new_call_vol + new_put_vol))
            st.session_state.power_history_buffer.append(cur_call_power - cur_put_power)

            if len(st.session_state.live_candle_buffer["times"]) > 35:
                st.session_state.live_candle_buffer["times"].pop(0)
                st.session_state.live_candle_buffer["calls"].pop(0)
                st.session_state.live_candle_buffer["puts"].pop(0)
                st.session_state.live_candle_buffer["vols"].pop(0)
                st.session_state.power_history_buffer.pop(0)

            st.session_state.last_minute_recorded = current_time_ist.minute

            updated_fig_oi = render_oi_chart(strikes, pe_solid, pe_crossed, pe_hollow, ce_solid, ce_crossed, ce_hollow, fut_price)
            # Static key -> Streamlit updates this chart's data in place
            # instead of unmounting/remounting it, which is what caused the
            # visible flicker/blink.
            oi_chart_box.plotly_chart(updated_fig_oi, key="oi_plot", config={"displayModeBar": False, "staticPlot": False})

            times_dt = st.session_state.live_candle_buffer["times"]
            put_prices = st.session_state.live_candle_buffer["puts"]
            call_prices = st.session_state.live_candle_buffer["calls"]
            volumes = st.session_state.live_candle_buffer["vols"]
            power_hist = st.session_state.power_history_buffer

            updated_fig_scalp = render_scalp_chart(times_dt, put_prices, call_prices, volumes, atm_strike, power_hist)
            chart_box.plotly_chart(updated_fig_scalp, key="scalp_plot", config={"displayModeBar": False, "staticPlot": False})
    else:
        cur_call_power = live_cp
        cur_put_power = live_pp

    times_dt = st.session_state.live_candle_buffer["times"]
    put_prices = st.session_state.live_candle_buffer["puts"]
    call_prices = st.session_state.live_candle_buffer["calls"]
    volumes = st.session_state.live_candle_buffer["vols"]

    vol_sum = sum(volumes)
    put_poc = float(np.round(np.average(put_prices, weights=volumes) if vol_sum > 0 else np.mean(put_prices), 2))
    call_poc = float(np.round(np.average(call_prices, weights=volumes) if vol_sum > 0 else np.mean(call_prices), 2))
    straddle_arr = np.array(put_prices) + np.array(call_prices)
    straddle_cmp = float(np.round(new_call + new_put, 2))
    if vol_sum > 0:
        straddle_vwap = float(np.round(np.cumsum(straddle_arr * np.array(volumes))[-1] / vol_sum, 2))
    else:
        straddle_vwap = float(np.round(np.mean(straddle_arr), 2))
    straddle_tloc = float(np.round(np.mean(straddle_arr[:12]), 2))

    # -----------------------------------------------------
    # 11. EVALUATE 7 CHECKPOINTS
    # -----------------------------------------------------
    cp1_val = f"CE Net: {cur_call_power:+,d} | PE Net: {cur_put_power:+,d}"
    cp1_status = "BULLISH" if cur_call_power > 0 and cur_put_power < 0 else ("BEARISH" if cur_put_power > 0 and cur_call_power < 0 else "NEUTRAL")

    atm_idx = len(strikes) // 2
    call_wall = strikes[atm_idx + int(np.argmax(ce_solid[atm_idx:]))]
    put_wall = strikes[int(np.argmax(pe_solid[:atm_idx + 1]))]
    cp2_val = f"Spot: {nifty_spot:.1f} | Wall: {put_wall} - {call_wall}"
    cp2_status = "BULLISH" if nifty_spot >= call_wall else ("BEARISH" if nifty_spot <= put_wall else "NEUTRAL")

    cp3_val = f"CE: ₹{new_call:.1f} (POC: ₹{call_poc:.1f}) | PE: ₹{new_put:.1f} (POC: ₹{put_poc:.1f})"
    cp3_status = "BULLISH" if new_call > call_poc and new_put < put_poc else ("BEARISH" if new_put > put_poc and new_call < call_poc else "NEUTRAL")

    cp4_val = f"Straddle: ₹{straddle_cmp:.1f} | VWAP: ₹{straddle_vwap:.1f} | TLOC: ₹{straddle_tloc:.1f}"
    cp4_status = "BULLISH" if straddle_cmp > straddle_vwap and straddle_cmp > straddle_tloc else "NEUTRAL"

    cp5_val = f"Order Flow Delta: {cur_call_power - cur_put_power:+,d} contracts"
    cp5_status = "BULLISH" if (cur_call_power - cur_put_power) > 200000 else ("BEARISH" if (cur_put_power - cur_call_power) > 200000 else "NEUTRAL")

    max_pain_strike = atm_strike  # placeholder proxy — true max pain needs full OI curve × payoff calc
    dist_pain = abs(nifty_spot - max_pain_strike)
    cp6_val = f"Max Pain (proxy=ATM): {max_pain_strike} (Dist: {dist_pain:.1f} pts)"
    is_expiry_afternoon = current_time_ist.time() >= dtime(13, 0)
    cp6_status = "NEUTRAL" if (is_expiry_afternoon and dist_pain <= 30) else ("BULLISH" if cp3_status == "BULLISH" else "BEARISH")

    cp7_val = f"India VIX: {live_vix:.2f} ({live_vix_chg:+.2f})"
    cp7_status = "BULLISH" if live_vix >= 11.5 else "NEUTRAL"

    if new_put > put_poc and cur_put_power > cur_call_power:
        unwinding_status = "🔥 Put Long Buildup (Heavy Put Buying)"
        multi_trend = "BEARISH"
        multi_class = "status-bearish"
    elif new_call > call_poc and cur_call_power > cur_put_power:
        unwinding_status = "🚀 Call Long Buildup (Heavy Call Buying)"
        multi_trend = "BULLISH"
        multi_class = "status-bullish"
    else:
        unwinding_status = "Neutral OI Distribution"
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
            market_status = "ACTIVE MOMENTUM"
            market_class = "status-bullish" if atm_trend == "BULLISH" else "status-bearish"
        else:
            market_status = "WAIT / MIXED"
            market_class = "status-wait"
    else:
        market_status = "MARKET CLOSED"
        market_class = "status-wait"

    # -----------------------------------------------------
    # 12. FAST IN-PLACE DOM UPDATES (unique keys avoid stale widgets)
    # -----------------------------------------------------
    atm_header_box.markdown(f"""
    <div class="top-price-box">
        <div class="top-price-row">
            <span class="val-badge-neutral">NIFTY {nifty_spot:.2f}</span>
            <span class="val-badge-neutral">FUT {fut_price:.2f}</span>
            <span class="val-badge-neutral">ATM {atm_strike}</span>
        </div>
        <div class="top-price-row">
            <span class="val-badge-call">CALL ₹{new_call:.2f}</span>
            <span class="val-badge-put">PUT ₹{new_put:.2f}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    ab_op, bl_op, op_sent, ab_15, bl_15, h_above_cnt, h_below_cnt = st.session_state.last_n50_breadth

    buy_class = "num-box-buy-highlight" if ab_op >= 35 else "num-box-buy"
    sell_class = "num-box-sell-highlight" if bl_op >= 35 else "num-box-sell"

    breadth_html = (
        '<div class="checkpoint-container">'
        '<div style="font-size:15px; font-weight:800; color:#38bdf8; margin-bottom:12px;">🏛️ Nifty 50 Equities Breadth Engine (Live 10s Stream)</div>'
        '<div class="breadth-flex-row">'
        '<span class="breadth-label">Above Open:</span>'
        f'<span class="{buy_class}">{ab_op}</span>'
        f'<span class="{sell_class}">{bl_op}</span>'
        '<span class="breadth-label">Below Open</span>'
        f'<div style="margin-left: auto;">{get_status_badge_html(op_sent)}</div>'
        '</div>'
        '<div class="breadth-flex-row">'
        '<span class="breadth-label">Above 15m High:</span>'
        f'<span class="num-box-buy">{ab_15}</span>'
        f'<span class="num-box-sell">{bl_15}</span>'
        '<span class="breadth-label">Below 15m Low</span>'
        '</div>'
        '<div class="breadth-flex-row" style="gap: 14px; padding-top: 10px;">'
        '<span class="breadth-label">Top Weightage:</span>'
        f'<span class="heavy-box-green">{h_above_cnt}</span>'
        f'<span class="heavy-box-red">{h_below_cnt}</span>'
        '</div>'
        '</div>'
    )
    breadth_box.markdown(breadth_html, unsafe_allow_html=True)

    checkpoints_box.markdown(f"""
    <div class="checkpoint-container">
        <div style="font-size:15px; font-weight:800; color:#58a6ff; margin-bottom:8px;">🎯 7 Institutional Edge Checkpoints</div>
        <div class="checkpoint-row"><div>1. Multi-Strike Unwinding Filter</div><div style="display:flex; align-items:center;"><span class="cp-val-text">{cp1_val}</span> {get_status_badge_html(cp1_status)}</div></div>
        <div class="checkpoint-row"><div>2. Gamma Regime Filter (OI Walls)</div><div style="display:flex; align-items:center;"><span class="cp-val-text">{cp2_val}</span> {get_status_badge_html(cp2_status)}</div></div>
        <div class="checkpoint-row"><div>3. ATM Micro-Price vs Volume POC</div><div style="display:flex; align-items:center;"><span class="cp-val-text">{cp3_val}</span> {get_status_badge_html(cp3_status)}</div></div>
        <div class="checkpoint-row"><div>4. Straddle Value vs VWAP & TLOC</div><div style="display:flex; align-items:center;"><span class="cp-val-text">{cp4_val}</span> {get_status_badge_html(cp4_status)}</div></div>
        <div class="checkpoint-row"><div>5. Order Book Imbalance (Net Power)</div><div style="display:flex; align-items:center;"><span class="cp-val-text">{cp5_val}</span> {get_status_badge_html(cp5_status)}</div></div>
        <div class="checkpoint-row"><div>6. Expiry Day Max Pain Pinning Guard</div><div style="display:flex; align-items:center;"><span class="cp-val-text">{cp6_val}</span> {get_status_badge_html(cp6_status)}</div></div>
        <div class="checkpoint-row"><div>7. IV Skew & Volatility Alignment</div><div style="display:flex; align-items:center;"><span class="cp-val-text">{cp7_val}</span> {get_status_badge_html(cp7_status)}</div></div>
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
        st.info(market_msg)


# Render the OI + scalp charts once on first load, then let the fragment
# take over all subsequent per-second updates without reloading the page.
if "init_charts_done" not in st.session_state:
    _snap = get_live_market_snapshot(smart_api, scrip_df)
    _fut_price0, _atm_strike0 = _snap[1], _snap[2]

    _init_strikes, _pe_s, _pe_c, _pe_h, _ce_s, _ce_c, _ce_h, _lcp, _lpp, _pcr, _tce, _tpe, _is_live = fetch_live_oi_and_power(
        smart_api, scrip_df, _atm_strike0
    )
    oi_chart_box.plotly_chart(
        render_oi_chart(_init_strikes, _pe_s, _pe_c, _pe_h, _ce_s, _ce_c, _ce_h, _fut_price0),
        key="oi_plot", config={"displayModeBar": False, "staticPlot": False}
    )
    chart_box.plotly_chart(
        render_scalp_chart(
            st.session_state.live_candle_buffer["times"],
            st.session_state.live_candle_buffer["puts"],
            st.session_state.live_candle_buffer["calls"],
            st.session_state.live_candle_buffer["vols"],
            _atm_strike0,
            st.session_state.power_history_buffer
        ),
        key="scalp_plot", config={"displayModeBar": False, "staticPlot": False}
    )
    st.session_state.init_charts_done = True

live_dashboard()
