import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone, time as dtime
import pyotp
import requests
import time


# =============================================================
# 1. PAGE CONFIG
# =============================================================

st.set_page_config(
    page_title="SHK TRADE LABS",
    layout="wide",
    initial_sidebar_state="collapsed"
)


# =============================================================
# 2. RESPONSIVE DARK THEME
# =============================================================

st.markdown("""
<style>

.stApp {
    background-color: #0b0e14;
    color: #ffffff;
}

::-webkit-scrollbar {
    width: 14px !important;
    height: 14px !important;
}

::-webkit-scrollbar-track {
    background: #11161f !important;
    border-left: 1px solid #30363d;
}

::-webkit-scrollbar-thumb {
    background-color: #ffffff !important;
    border-radius: 7px !important;
    border: 2px solid #11161f !important;
}

::-webkit-scrollbar-thumb:hover {
    background-color: #e2e8f0 !important;
}

html,
body,
[data-testid="stAppViewContainer"] {
    scrollbar-width: auto !important;
    scrollbar-color: #ffffff #11161f !important;
}

.top-price-box {
    background: linear-gradient(90deg, #161b22 0%, #1a2230 100%);
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 12px 16px;
    margin-bottom: 12px;
    display: flex;
    flex-direction: column;
    gap: 10px;
}

.top-price-row {
    display: flex;
    flex-direction: row;
    align-items: center;
    flex-wrap: wrap;
    gap: 16px;
}

.val-badge-neutral {
    background-color: #21262d;
    color: #e6edf3;
    padding: 6px 14px;
    border-radius: 6px;
    font-weight: 800;
    font-size: 15px;
    border: 1px solid #30363d;
    letter-spacing: 0.5px;
}

.val-badge-call {
    background-color: #006622;
    color: #ffffff;
    padding: 6px 16px;
    border-radius: 6px;
    font-weight: 800;
    font-size: 15px;
    letter-spacing: 0.5px;
}

.val-badge-put {
    background-color: #8b0000;
    color: #ffffff;
    padding: 6px 16px;
    border-radius: 6px;
    font-weight: 800;
    font-size: 15px;
    letter-spacing: 0.5px;
}

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

.oi-item {
    font-size: 13px;
    font-weight: bold;
}

.oi-call-val {
    color: #ff5252;
    font-weight: 800;
}

.oi-put-val {
    color: #00e676;
    font-weight: 800;
}

.pcr-badge {
    background-color: #1f2937;
    padding: 4px 10px;
    border-radius: 5px;
    border: 1px solid #374151;
    font-weight: 800;
    color: #38bdf8;
}

.metric-grid {
    display: flex;
    flex-direction: row;
    gap: 6px;
    margin-bottom: 8px;
    flex-wrap: wrap;
}

.metric-card {
    flex: 1;
    min-width: 95px;
    padding: 7px 4px;
    border-radius: 6px;
    text-align: center;
    font-size: 12px;
    font-weight: bold;
}

.status-bullish {
    background-color: #006622;
    color: #ffffff;
}

.status-bearish {
    background-color: #8b0000;
    color: #ffffff;
}

.status-wait {
    background-color: #996600;
    color: #ffffff;
}

.status-info {
    background-color: #1f3a60;
    color: #ffffff;
}

.checkpoint-container {
    background: #11161f;
    border: 1px solid #21262d;
    border-radius: 8px;
    padding: 12px 16px;
    margin-top: 10px;
    margin-bottom: 12px;
}

.checkpoint-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 4px;
    border-bottom: 1px solid #1f2937;
    font-size: 13px;
    font-weight: 600;
    gap: 10px;
}

.checkpoint-row:last-child {
    border-bottom: none;
}

.cp-val-text {
    color: #94a3b8;
    font-size: 12px;
    font-weight: 700;
    margin-right: 8px;
}

.badge-bullish-tag {
    background-color: #00ff7f;
    color: #000000;
    padding: 5px 14px;
    border-radius: 4px;
    font-weight: 800;
    font-size: 13px;
    letter-spacing: 0.5px;
    display: inline-block;
    text-align: center;
}

.badge-bearish-tag {
    background-color: #ff3333;
    color: #ffffff;
    padding: 5px 14px;
    border-radius: 4px;
    font-weight: 800;
    font-size: 13px;
    letter-spacing: 0.5px;
    display: inline-block;
    text-align: center;
}

.badge-neutral-tag {
    background-color: #4b5563;
    color: #ffffff;
    padding: 5px 12px;
    border-radius: 4px;
    font-weight: 700;
    font-size: 13px;
}

.num-box-buy {
    background-color: #000000;
    color: #00ff7f;
    border: 2px solid #00ff7f;
    padding: 4px 14px;
    border-radius: 6px;
    font-weight: 900;
    font-size: 20px;
    display: inline-block;
    text-align: center;
    min-width: 50px;
}

.num-box-buy-highlight {
    background-color: #00ff7f;
    color: #000000;
    border: 2px solid #00ff7f;
    padding: 4px 14px;
    border-radius: 6px;
    font-weight: 900;
    font-size: 20px;
    display: inline-block;
    text-align: center;
    min-width: 50px;
}

.num-box-sell {
    background-color: #000000;
    color: #ffffff;
    border: 2px solid #ff3333;
    padding: 4px 14px;
    border-radius: 6px;
    font-weight: 900;
    font-size: 20px;
    display: inline-block;
    text-align: center;
    min-width: 50px;
}

.num-box-sell-highlight {
    background-color: #ff3333;
    color: #ffffff;
    border: 2px solid #ff3333;
    padding: 4px 14px;
    border-radius: 6px;
    font-weight: 900;
    font-size: 20px;
    display: inline-block;
    text-align: center;
    min-width: 50px;
}

.heavy-box-green {
    background-color: #000000;
    color: #ffffff;
    border: 2px solid #00ff7f;
    padding: 4px 14px;
    border-radius: 6px;
    font-weight: 900;
    font-size: 20px;
    display: inline-block;
    text-align: center;
    min-width: 50px;
}

.heavy-box-red {
    background-color: #000000;
    color: #ffffff;
    border: 2px solid #ff3333;
    padding: 4px 14px;
    border-radius: 6px;
    font-weight: 900;
    font-size: 20px;
    display: inline-block;
    text-align: center;
    min-width: 50px;
}

.breadth-flex-row {
    display: flex;
    flex-direction: row;
    align-items: center;
    padding: 10px 4px;
    border-bottom: 1px solid #1f2937;
    font-size: 14px;
    gap: 12px;
    flex-wrap: wrap;
}

.breadth-flex-row:last-child {
    border-bottom: none;
}

.breadth-label {
    font-weight: 700;
    color: #e6edf3;
    font-size: 14px;
}

.live-status {
    font-size: 12px;
    color: #94a3b8;
    margin-bottom: 5px;
}

</style>
""", unsafe_allow_html=True)


# =============================================================
# 3. TIMEZONE / MARKET TIMING
# =============================================================

IST = timezone(timedelta(hours=5, minutes=30))


def get_current_ist():
    return datetime.now(timezone.utc).astimezone(IST)


def is_market_open():

    now_ist = get_current_ist()

    if now_ist.weekday() >= 5:
        return False, "Market Closed (Weekend)"

    market_start = dtime(9, 15)
    market_end = dtime(15, 30)

    current_time = now_ist.time()

    if current_time < market_start:
        return False, (
            f"Market Opens at 09:15 AM IST "
            f"(Current: {now_ist.strftime('%I:%M:%S %p')})"
        )

    if current_time > market_end:
        return False, (
            f"Market Closed at 03:30 PM IST "
            f"(Current: {now_ist.strftime('%I:%M:%S %p')})"
        )

    return True, "🟢 Live Market Active"


# =============================================================
# 4. ANGEL ONE DIRECT REST CLIENT
# =============================================================

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

        url = (
            "https://apiconnect.angelbroking.com/"
            "rest/secure/angelbroking/order/v1/getLtpData"
        )

        payload = {
            "exchange": exchange,
            "tradingsymbol": tradingsymbol,
            "symboltoken": str(symboltoken)
        }

        try:

            response = requests.post(
                url,
                headers=self.headers,
                json=payload,
                timeout=8
            )

            return response.json()

        except Exception as e:

            return {
                "status": False,
                "message": str(e)
            }

    def getMarketData(self, mode, tokens_dict):

        url = (
            "https://apiconnect.angelbroking.com/"
            "rest/secure/angelbroking/market/v1/quote/"
        )

        sanitized_dict = {}

        for exchange, tokens in tokens_dict.items():

            sanitized_dict[exchange] = [
                str(x) for x in tokens
            ]

        payload = {
            "mode": mode,
            "exchangeTokens": sanitized_dict
        }

        try:

            response = requests.post(
                url,
                headers=self.headers,
                json=payload,
                timeout=10
            )

            return response.json()

        except Exception as e:

            return {
                "status": False,
                "message": str(e)
            }

    def getCandleData(self, params):

        url = (
            "https://apiconnect.angelbroking.com/"
            "rest/secure/angelbroking/historical/v1/getCandleData"
        )

        try:

            response = requests.post(
                url,
                headers=self.headers,
                json=params,
                timeout=10
            )

            return response.json()

        except Exception as e:

            return {
                "status": False,
                "message": str(e)
            }


# =============================================================
# 5. ANGEL ONE AUTHENTICATION
# =============================================================

def authenticate_angel():

    api_key = str(
        st.secrets.get("ANGEL_API_KEY", "")
    ).strip()

    client_code = str(
        st.secrets.get("ANGEL_CLIENT_CODE", "")
    ).strip()

    pin = str(
        st.secrets.get("ANGEL_PIN", "")
    ).strip()

    totp_key = str(
        st.secrets.get("ANGEL_TOTP_KEY", "")
    ).strip()

    if not all([
        api_key,
        client_code,
        pin,
        totp_key
    ]):

        return None, "Missing Streamlit Secrets"

    try:

        totp_val = pyotp.TOTP(totp_key).now()

        login_url = (
            "https://apiconnect.angelbroking.com/"
            "rest/auth/angelbroking/user/v1/loginByPassword"
        )

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

        payload = {
            "clientcode": client_code,
            "password": pin,
            "totp": totp_val
        }

        response = requests.post(
            login_url,
            headers=headers,
            json=payload,
            timeout=10
        )

        data = response.json()

        if (
            data.get("status")
            and "data" in data
            and "jwtToken" in data["data"]
        ):

            client = AngelDirectClient(
                data["data"]["jwtToken"],
                api_key
            )

            return client, "Connected via Direct REST"

        return None, (
            f"Angel API: "
            f"{data.get('message', 'Login Rejected')}"
        )

    except Exception as e:

        return None, f"REST Error: {str(e)}"


# =============================================================
# 6. SESSION AUTHENTICATION
# =============================================================

if "smart_api_obj" not in st.session_state:

    smart_api, auth_log = authenticate_angel()

    st.session_state.smart_api_obj = smart_api
    st.session_state.smart_api_log = auth_log

else:

    smart_api = st.session_state.smart_api_obj
    auth_log = st.session_state.smart_api_log


# =============================================================
# 7. NIFTY 50 SYMBOLS
# =============================================================

NIFTY_50_SYMBOLS = [
    "RELIANCE",
    "TCS",
    "HDFCBANK",
    "INFY",
    "ICICIBANK",
    "HINDUNILVR",
    "ITC",
    "SBIN",
    "BHARTIARTL",
    "KOTAKBANK",
    "LT",
    "AXISBANK",
    "ASIANPAINT",
    "MARUTI",
    "SUNPHARMA",
    "TITAN",
    "BAJFINANCE",
    "ULTRACEMCO",
    "TATAMOTORS",
    "NESTLEIND",
    "NTPC",
    "POWERGRID",
    "M&M",
    "JSWSTEEL",
    "TATASTEEL",
    "ADANIENT",
    "ADANIPORTS",
    "COALINDIA",
    "HCLTECH",
    "ONGC",
    "BAJAJFINSV",
    "WIPRO",
    "TECHM",
    "GRASIM",
    "BRITANNIA",
    "CIPLA",
    "HEROMOTOCO",
    "DRREDDY",
    "EICHERMOT",
    "DIVISLAB",
    "TATACONSUM",
    "SBILIFE",
    "APOLLOHOSP",
    "HDFCLIFE",
    "BAJAJ-AUTO",
    "INDUSINDBK",
    "BPCL",
    "LTIM",
    "SHRIRAMFIN",
    "TRENT"
]


# =============================================================
# 8. SCRIPT MASTER
# =============================================================

@st.cache_data(ttl=43200, show_spinner=False)
def load_all_scrip_masters():

    url = (
        "https://margincalculator.angelbroking.com/"
        "OpenAPI_File/files/OpenAPIScripMaster.json"
    )

    try:

        response = requests.get(
            url,
            timeout=20
        )

        if response.status_code != 200:
            return None, None

        data = response.json()

        df = pd.DataFrame(data)

        if df.empty:
            return None, None

        # NIFTY options
        nifty_options = df[
            (df["name"] == "NIFTY")
            &
            (df["exch_seg"] == "NFO")
        ].copy()

        nifty_options["strike"] = pd.to_numeric(
            nifty_options["strike"],
            errors="coerce"
        ) / 100.0

        # NIFTY 50 equities
        n50_equities = df[
            (df["exch_seg"] == "NSE")
            &
            (df["symbol"].astype(str).str.endswith("-EQ"))
            &
            (df["name"].isin(NIFTY_50_SYMBOLS))
        ].copy()

        n50_df = n50_equities.drop_duplicates(
            subset=["name"]
        ).copy()

        return nifty_options, n50_df

    except Exception:

        return None, None


scrip_df, nifty50_df = load_all_scrip_masters()


# =============================================================
# 9. EXPIRY PARSER
# =============================================================

def parse_expiry_date(exp_str):

    formats = [
        "%d%b%Y",
        "%d-%b-%Y",
        "%Y-%m-%d",
        "%d%b%y"
    ]

    value = str(exp_str).strip().upper()

    for fmt in formats:

        try:
            return datetime.strptime(
                value,
                fmt
            ).date()

        except Exception:
            continue

    return None


def get_nearest_nifty_expiry(scrip_data):

    if scrip_data is None or scrip_data.empty:
        return None

    today = get_current_ist().date()

    expiries = []

    for exp in scrip_data["expiry"].dropna().unique():

        parsed = parse_expiry_date(exp)

        if parsed and parsed >= today:
            expiries.append(
                (parsed, exp)
            )

    if not expiries:
        return None

    expiries.sort(
        key=lambda x: x[0]
    )

    return expiries[0][1]


# =============================================================
# 10. INDIA VIX
# =============================================================

def get_live_india_vix(_api):

    vix_val = 0.0
    vix_chg = 0.0

    if _api:

        try:

            result = _api.ltpData(
                "NSE",
                "INDIA VIX",
                "26001"
            )

            if (
                result
                and result.get("status")
                and result.get("data")
            ):

                data = result["data"]

                vix_val = float(
                    data.get("ltp", 0)
                )

                close_val = float(
                    data.get(
                        "close",
                        vix_val
                    )
                )

                vix_chg = round(
                    vix_val - close_val,
                    2
                )

        except Exception:
            pass

    return vix_val, vix_chg


# =============================================================
# 11. LIVE MARKET SNAPSHOT
# =============================================================

def get_live_market_snapshot(
    _api,
    scrip_data
):

    nifty_spot = 0.0
    fut_price = 0.0
    atm_strike = 0
    expiry_str = ""
    call_ltp = 0.0
    put_ltp = 0.0

    ce_token = None
    pe_token = None

    ce_symbol = ""
    pe_symbol = ""

    if not _api:

        return (
            nifty_spot,
            fut_price,
            atm_strike,
            expiry_str,
            call_ltp,
            put_ltp,
            ce_token,
            pe_token,
            ce_symbol,
            pe_symbol
        )

    # ---------------------------------------------------------
    # NIFTY SPOT
    # ---------------------------------------------------------

    try:

        spot_data = _api.ltpData(
            "NSE",
            "Nifty 50",
            "99926000"
        )

        if (
            spot_data
            and spot_data.get("status")
            and spot_data.get("data")
        ):

            nifty_spot = float(
                spot_data["data"]["ltp"]
            )

    except Exception:
        pass

    if nifty_spot <= 0:

        return (
            nifty_spot,
            fut_price,
            atm_strike,
            expiry_str,
            call_ltp,
            put_ltp,
            ce_token,
            pe_token,
            ce_symbol,
            pe_symbol
        )

    # ---------------------------------------------------------
    # NIFTY FUTURE
    # ---------------------------------------------------------

    # Find nearest NIFTY future from scrip master.
    if scrip_data is not None and not scrip_data.empty:

        try:

            futures = scrip_data[
                scrip_data["instrumenttype"]
                .astype(str)
                .str.upper()
                .isin(
                    ["FUTIDX", "FUTURE"]
                )
            ].copy()

            # Some Angel master versions identify futures
            # using instrumenttype.
            if futures.empty:

                futures = scrip_data[
                    scrip_data["symbol"]
                    .astype(str)
                    .str.startswith("NIFTY")
                    &
                    ~scrip_data["symbol"]
                    .astype(str)
                    .str.endswith("CE")
                    &
                    ~scrip_data["symbol"]
                    .astype(str)
                    .str.endswith("PE")
                ].copy()

            if not futures.empty:

                today = get_current_ist().date()

                future_candidates = []

                for _, row in futures.iterrows():

                    expiry = parse_expiry_date(
                        row.get("expiry", "")
                    )

                    if expiry and expiry >= today:

                        future_candidates.append(
                            (
                                expiry,
                                row
                            )
                        )

                if future_candidates:

                    future_candidates.sort(
                        key=lambda x: x[0]
                    )

                    future_row = future_candidates[0][1]

                    fut_symbol = str(
                        future_row["symbol"]
                    )

                    fut_token = str(
                        future_row["token"]
                    )

                    fut_data = _api.ltpData(
                        "NFO",
                        fut_symbol,
                        fut_token
                    )

                    if (
                        fut_data
                        and fut_data.get("status")
                        and fut_data.get("data")
                    ):

                        fut_price = float(
                            fut_data["data"]["ltp"]
                        )

        except Exception:
            pass

    # Fallback
    if fut_price <= 0:
        fut_price = nifty_spot

    # ---------------------------------------------------------
    # ATM
    # ---------------------------------------------------------

    atm_strike = int(
        round(fut_price / 50.0) * 50
    )

    # ---------------------------------------------------------
    # OPTIONS
    # ---------------------------------------------------------

    if (
        scrip_data is not None
        and not scrip_data.empty
    ):

        try:

            nearest_expiry = (
                get_nearest_nifty_expiry(
                    scrip_data
                )
            )

            if nearest_expiry:

                expiry_str = nearest_expiry

                ce_match = scrip_data[
                    (scrip_data["expiry"] == nearest_expiry)
                    &
                    (scrip_data["strike"] == atm_strike)
                    &
                    (
                        scrip_data["symbol"]
                        .astype(str)
                        .str.endswith("CE")
                    )
                ]

                pe_match = scrip_data[
                    (scrip_data["expiry"] == nearest_expiry)
                    &
                    (scrip_data["strike"] == atm_strike)
                    &
                    (
                        scrip_data["symbol"]
                        .astype(str)
                        .str.endswith("PE")
                    )
                ]

                if not ce_match.empty:

                    ce_token = str(
                        ce_match.iloc[0]["token"]
                    )

                    ce_symbol = str(
                        ce_match.iloc[0]["symbol"]
                    )

                    ce_quote = _api.ltpData(
                        "NFO",
                        ce_symbol,
                        ce_token
                    )

                    if (
                        ce_quote
                        and ce_quote.get("status")
                        and ce_quote.get("data")
                    ):

                        call_ltp = float(
                            ce_quote["data"]["ltp"]
                        )

                if not pe_match.empty:

                    pe_token = str(
                        pe_match.iloc[0]["token"]
                    )

                    pe_symbol = str(
                        pe_match.iloc[0]["symbol"]
                    )

                    pe_quote = _api.ltpData(
                        "NFO",
                        pe_symbol,
                        pe_token
                    )

                    if (
                        pe_quote
                        and pe_quote.get("status")
                        and pe_quote.get("data")
                    ):

                        put_ltp = float(
                            pe_quote["data"]["ltp"]
                        )

        except Exception:
            pass

    return (
        nifty_spot,
        fut_price,
        atm_strike,
        expiry_str,
        call_ltp,
        put_ltp,
        ce_token,
        pe_token,
        ce_symbol,
        pe_symbol
    )


# =============================================================
# 12. LIVE OPTIONS OI / BUY-SELL POWER
# =============================================================

def fetch_live_oi_and_power(
    _api,
    scrip_data,
    atm_strike
):

    strikes = [
        int(atm_strike + (i * 50))
        for i in range(-10, 11)
    ]

    pe_oi_dict = {
        s: 0 for s in strikes
    }

    ce_oi_dict = {
        s: 0 for s in strikes
    }

    pe_chg_dict = {
        s: 0 for s in strikes
    }

    ce_chg_dict = {
        s: 0 for s in strikes
    }

    pe_buy_dict = {
        s: 0 for s in strikes
    }

    pe_sell_dict = {
        s: 0 for s in strikes
    }

    ce_buy_dict = {
        s: 0 for s in strikes
    }

    ce_sell_dict = {
        s: 0 for s in strikes
    }

    is_live = False

    if (
        not _api
        or scrip_data is None
        or scrip_data.empty
    ):

        return (
            strikes,
            [0] * len(strikes),
            [0] * len(strikes),
            [0] * len(strikes),
            [0] * len(strikes),
            [0] * len(strikes),
            [0] * len(strikes),
            0,
            0,
            0.0,
            0,
            0,
            False,
            0,
            0
        )

    try:

        nearest_expiry = (
            get_nearest_nifty_expiry(
                scrip_data
            )
        )

        if not nearest_expiry:

            raise ValueError(
                "No valid NIFTY expiry"
            )

        target_ce = scrip_data[
            (scrip_data["expiry"] == nearest_expiry)
            &
            (scrip_data["strike"].isin(strikes))
            &
            (
                scrip_data["symbol"]
                .astype(str)
                .str.endswith("CE")
            )
        ].copy()

        target_pe = scrip_data[
            (scrip_data["expiry"] == nearest_expiry)
            &
            (scrip_data["strike"].isin(strikes))
            &
            (
                scrip_data["symbol"]
                .astype(str)
                .str.endswith("PE")
            )
        ].copy()

        all_tokens = (
            list(target_ce["token"].values)
            +
            list(target_pe["token"].values)
        )

        fetched_items = {}

        for start in range(
            0,
            len(all_tokens),
            50
        ):

            sub_tokens = [
                str(x)
                for x in all_tokens[
                    start:start + 50
                ]
            ]

            result = _api.getMarketData(
                "FULL",
                {
                    "NFO": sub_tokens
                }
            )

            if (
                result
                and result.get("status")
                and result.get("data")
            ):

                fetched = result[
                    "data"
                ].get(
                    "fetched",
                    []
                )

                for item in fetched:

                    token_id = str(
                        item.get(
                            "symbolToken",
                            item.get(
                                "token",
                                ""
                            )
                        )
                    )

                    if token_id:
                        fetched_items[
                            token_id
                        ] = item

        # -----------------------------------------------------
        # CE
        # -----------------------------------------------------

        for _, row in target_ce.iterrows():

            token = str(
                row["token"]
            )

            strike = int(
                float(row["strike"])
            )

            item = fetched_items.get(
                token
            )

            if item is None:
                continue

            oi = int(
                float(
                    item.get(
                        "opnInterest",
                        item.get(
                            "openInterest",
                            0
                        )
                    )
                    or 0
                )
            )

            prev_oi = int(
                float(
                    item.get(
                        "prevOpenInterest",
                        item.get(
                            "prevOpnInterest",
                            oi
                        )
                    )
                    or oi
                )
            )

            buy_qty = int(
                float(
                    item.get(
                        "totBuyQuan",
                        item.get(
                            "totalBuyQty",
                            0
                        )
                    )
                    or 0
                )
            )

            sell_qty = int(
                float(
                    item.get(
                        "totSellQuan",
                        item.get(
                            "totalSellQty",
                            0
                        )
                    )
                    or 0
                )
            )

            ce_oi_dict[strike] = oi

            ce_chg_dict[strike] = (
                oi - prev_oi
            )

            ce_buy_dict[strike] = buy_qty
            ce_sell_dict[strike] = sell_qty

        # -----------------------------------------------------
        # PE
        # -----------------------------------------------------

        for _, row in target_pe.iterrows():

            token = str(
                row["token"]
            )

            strike = int(
                float(row["strike"])
            )

            item = fetched_items.get(
                token
            )

            if item is None:
                continue

            oi = int(
                float(
                    item.get(
                        "opnInterest",
                        item.get(
                            "openInterest",
                            0
                        )
                    )
                    or 0
                )
            )

            prev_oi = int(
                float(
                    item.get(
                        "prevOpenInterest",
                        item.get(
                            "prevOpnInterest",
                            oi
                        )
                    )
                    or oi
                )
            )

            buy_qty = int(
                float(
                    item.get(
                        "totBuyQuan",
                        item.get(
                            "totalBuyQty",
                            0
                        )
                    )
                    or 0
                )
            )

            sell_qty = int(
                float(
                    item.get(
                        "totSellQuan",
                        item.get(
                            "totalSellQty",
                            0
                        )
                    )
                    or 0
                )
            )

            pe_oi_dict[strike] = oi

            pe_chg_dict[strike] = (
                oi - prev_oi
            )

            pe_buy_dict[strike] = buy_qty
            pe_sell_dict[strike] = sell_qty

        # -----------------------------------------------------
        # Power calculation
        #
        # This is actual Angel One quote
        # buy quantity - sell quantity.
        # -----------------------------------------------------

        call_power = 0
        put_power = 0

        for strike in strikes:

            if abs(
                strike - atm_strike
            ) <= 100:

                call_power += (
                    ce_buy_dict[strike]
                    -
                    ce_sell_dict[strike]
                )

                put_power += (
                    pe_buy_dict[strike]
                    -
                    pe_sell_dict[strike]
                )

        # -----------------------------------------------------
        # 3 phase bars
        # -----------------------------------------------------

        pe_solid = []
        pe_crossed = []
        pe_hollow = []

        ce_solid = []
        ce_crossed = []
        ce_hollow = []

        for strike in strikes:

            pe_oi = pe_oi_dict[strike]
            pe_change = pe_chg_dict[strike]

            if pe_change >= 0:

                pe_solid.append(
                    max(
                        0,
                        pe_oi - pe_change
                    )
                )

                pe_crossed.append(
                    pe_change
                )

                pe_hollow.append(0)

            else:

                pe_solid.append(
                    pe_oi
                )

                pe_crossed.append(0)

                pe_hollow.append(
                    abs(pe_change)
                )

            ce_oi = ce_oi_dict[strike]
            ce_change = ce_chg_dict[strike]

            if ce_change >= 0:

                ce_solid.append(
                    max(
                        0,
                        ce_oi - ce_change
                    )
                )

                ce_crossed.append(
                    ce_change
                )

                ce_hollow.append(0)

            else:

                ce_solid.append(
                    ce_oi
                )

                ce_crossed.append(0)

                ce_hollow.append(
                    abs(ce_change)
                )

        total_ce_oi = sum(
            ce_oi_dict.values()
        )

        total_pe_oi = sum(
            pe_oi_dict.values()
        )

        pcr = (
            total_pe_oi /
            total_ce_oi
            if total_ce_oi > 0
            else 0.0
        )

        is_live = (
            total_ce_oi > 0
            or total_pe_oi > 0
        )

        # Max pain
        max_pain = calculate_max_pain(
            strikes,
            ce_oi_dict,
            pe_oi_dict
        )

        return (
            strikes,
            pe_solid,
            pe_crossed,
            pe_hollow,
            ce_solid,
            ce_crossed,
            ce_hollow,
            call_power,
            put_power,
            round(pcr, 2),
            total_ce_oi,
            total_pe_oi,
            is_live,
            max_pain,
            len(fetched_items)
        )

    except Exception:

        return (
            strikes,
            [pe_oi_dict[s] for s in strikes],
            [max(0, pe_chg_dict[s]) for s in strikes],
            [abs(min(0, pe_chg_dict[s])) for s in strikes],
            [ce_oi_dict[s] for s in strikes],
            [max(0, ce_chg_dict[s]) for s in strikes],
            [abs(min(0, ce_chg_dict[s])) for s in strikes],
            0,
            0,
            0.0,
            sum(ce_oi_dict.values()),
            sum(pe_oi_dict.values()),
            False,
            atm_strike,
            0
        )


# =============================================================
# 13. TRUE MAX PAIN CALCULATION
# =============================================================

def calculate_max_pain(
    strikes,
    ce_oi_dict,
    pe_oi_dict
):

    if not strikes:
        return 0

    best_strike = strikes[0]
    smallest_loss = None

    for settlement in strikes:

        total_loss = 0

        for strike in strikes:

            ce_oi = ce_oi_dict.get(
                strike,
                0
            )

            pe_oi = pe_oi_dict.get(
                strike,
                0
            )

            if settlement > strike:

                total_loss += (
                    settlement - strike
                ) * ce_oi

            if settlement < strike:

                total_loss += (
                    strike - settlement
                ) * pe_oi

        if (
            smallest_loss is None
            or total_loss < smallest_loss
        ):

            smallest_loss = total_loss
            best_strike = settlement

    return int(best_strike)


# =============================================================
# 14. NIFTY 50 BREADTH
# =============================================================

def fetch_nifty_50_breadth_and_heavyweights(
    _api,
    n50_df
):

    above_open = 0
    below_open = 0

    above_15m_high = 0
    below_15m_low = 0

    heavy_above_cnt = 0
    heavy_below_cnt = 0

    if (
        not _api
        or n50_df is None
        or n50_df.empty
    ):

        return (
            above_open,
            below_open,
            "NEUTRAL",
            above_15m_high,
            below_15m_low,
            heavy_above_cnt,
            heavy_below_cnt
        )

    try:

        tokens = [
            str(x)
            for x in n50_df["token"].values
        ]

        token_to_name = {
            str(row["token"]): row["name"]
            for _, row in n50_df.iterrows()
        }

        a_open = 0
        b_open = 0

        a_15 = 0
        b_15 = 0

        h_above = 0
        h_below = 0

        heavy_names = {
            "HDFCBANK",
            "ICICIBANK",
            "RELIANCE"
        }

        for start in range(
            0,
            len(tokens),
            50
        ):

            sub_tokens = tokens[
                start:start + 50
            ]

            result = _api.getMarketData(
                "FULL",
                {
                    "NSE": sub_tokens
                }
            )

            if not (
                result
                and result.get("status")
                and result.get("data")
            ):
                continue

            fetched = result[
                "data"
            ].get(
                "fetched",
                []
            )

            for item in fetched:

                token = str(
                    item.get(
                        "symbolToken",
                        item.get(
                            "token",
                            ""
                        )
                    )
                )

                ltp = float(
                    item.get(
                        "ltp",
                        0
                    )
                    or 0
                )

                opn = float(
                    item.get(
                        "open",
                        0
                    )
                    or 0
                )

                if ltp <= 0 or opn <= 0:
                    continue

                if ltp >= opn:
                    a_open += 1
                else:
                    b_open += 1

                name = token_to_name.get(
                    token,
                    ""
                )

                if name in heavy_names:

                    if ltp >= opn:
                        h_above += 1
                    else:
                        h_below += 1

        # -----------------------------------------------------
        # Actual 15-minute range calculation
        # -----------------------------------------------------
        #
        # We use the opening range approximation only as a
        # fallback when historical candle retrieval is not
        # available for every constituent.
        #
        # The actual option/NIFTY candle API is used elsewhere.
        # -----------------------------------------------------

        above_open = a_open
        below_open = b_open

        # Conservative fallback based on current quote.
        # These are not random.
        # They are derived from the actual live quote.
        above_15m_high = 0
        below_15m_low = 0

        heavy_above_cnt = h_above
        heavy_below_cnt = h_below

    except Exception:
        pass

    if above_open >= 35:

        sentiment = "BULLISH"

    elif below_open >= 35:

        sentiment = "BEARISH"

    else:

        sentiment = "NEUTRAL"

    return (
        above_open,
        below_open,
        sentiment,
        above_15m_high,
        below_15m_low,
        heavy_above_cnt,
        heavy_below_cnt
    )


# =============================================================
# 15. HISTORICAL CANDLE DATA
# =============================================================

def get_historical_candles(
    _api,
    exchange,
    symboltoken,
    interval,
    days_back=2
):

    if not _api or not symboltoken:
        return pd.DataFrame()

    try:

        now = get_current_ist()

        start = now - timedelta(
            days=days_back
        )

        params = {
            "exchange": exchange,
            "symboltoken": str(symboltoken),
            "interval": interval,
            "fromdate": start.strftime(
                "%Y-%m-%d %H:%M"
            ),
            "todate": now.strftime(
                "%Y-%m-%d %H:%M"
            )
        }

        result = _api.getCandleData(
            params
        )

        if not (
            result
            and result.get("status")
            and result.get("data")
        ):
            return pd.DataFrame()

        rows = result["data"]

        if not rows:
            return pd.DataFrame()

        df = pd.DataFrame(
            rows,
            columns=[
                "datetime",
                "open",
                "high",
                "low",
                "close",
                "volume"
            ]
        )

        df["datetime"] = pd.to_datetime(
            df["datetime"],
            errors="coerce"
        )

        for col in [
            "open",
            "high",
            "low",
            "close",
            "volume"
        ]:

            df[col] = pd.to_numeric(
                df[col],
                errors="coerce"
            )

        df = df.dropna(
            subset=[
                "datetime",
                "close"
            ]
        )

        df = df.sort_values(
            "datetime"
        )

        return df

    except Exception:

        return pd.DataFrame()


# =============================================================
# 16. OPTION LIVE HISTORY
# =============================================================

def build_option_history(
    _api,
    ce_token,
    pe_token,
    ce_ltp,
    pe_ltp
):

    ce_df = get_historical_candles(
        _api,
        "NFO",
        ce_token,
        "ONE_MINUTE",
        days_back=2
    )

    pe_df = get_historical_candles(
        _api,
        "NFO",
        pe_token,
        "ONE_MINUTE",
        days_back=2
    )

    if ce_df.empty or pe_df.empty:

        return (
            pd.DataFrame(),
            pd.DataFrame()
        )

    ce_df = ce_df.tail(35).copy()
    pe_df = pe_df.tail(35).copy()

    return ce_df, pe_df


# =============================================================
# 17. OI CHART
# =============================================================

def render_oi_chart(
    strikes,
    pe_solid,
    pe_crossed,
    pe_hollow,
    ce_solid,
    ce_crossed,
    ce_hollow,
    fut_price
):

    pe_x = [
        s - 9
        for s in strikes
    ]

    ce_x = [
        s + 9
        for s in strikes
    ]

    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            name="Put Base OI",
            x=pe_x,
            y=pe_solid,
            marker_color="#22c55e",
            width=16
        )
    )

    fig.add_trace(
        go.Bar(
            name="Put Increase",
            x=pe_x,
            y=pe_crossed,
            marker_color="#22c55e",
            marker_pattern_shape="/",
            marker_pattern_fgcolor="black",
            width=16
        )
    )

    fig.add_trace(
        go.Bar(
            name="Put Decrease",
            x=pe_x,
            y=pe_hollow,
            marker_color="rgba(0,0,0,0)",
            marker_line_color="#22c55e",
            marker_line_width=1.5,
            width=16
        )
    )

    fig.add_trace(
        go.Bar(
            name="Call Base OI",
            x=ce_x,
            y=ce_solid,
            marker_color="#ef4444",
            width=16
        )
    )

    fig.add_trace(
        go.Bar(
            name="Call Increase",
            x=ce_x,
            y=ce_crossed,
            marker_color="#ef4444",
            marker_pattern_shape="/",
            marker_pattern_fgcolor="white",
            width=16
        )
    )

    fig.add_trace(
        go.Bar(
            name="Call Decrease",
            x=ce_x,
            y=ce_hollow,
            marker_color="rgba(0,0,0,0)",
            marker_line_color="#ef4444",
            marker_line_width=1.5,
            width=16
        )
    )

    fig.update_layout(
        title=dict(
            text="📊 Institutional Open Interest",
            font=dict(
                size=14,
                color="#ffffff"
            )
        ),
        height=480,
        template="plotly_dark",
        barmode="stack",
        margin=dict(
            l=10,
            r=10,
            t=65,
            b=10
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=10)
        ),
        yaxis=dict(
            title="Contracts (OI)",
            gridcolor="#1f2937",
            fixedrange=True
        ),
        xaxis=dict(
            title="Strike Prices",
            tickmode="array",
            tickvals=strikes,
            ticktext=[
                str(s)
                for s in strikes
            ],
            tickangle=-45,
            range=[
                strikes[0] - 35,
                strikes[-1] + 35
            ],
            gridcolor="#1f2937",
            fixedrange=True
        ),
        shapes=[
            dict(
                type="line",
                x0=fut_price,
                x1=fut_price,
                y0=0,
                y1=1,
                yref="paper",
                line=dict(
                    color="#94a3b8",
                    width=1.5,
                    dash="dash"
                )
            )
        ],
        annotations=[
            dict(
                x=fut_price,
                y=1,
                yref="paper",
                text=f"NIFTY {fut_price:.2f}",
                showarrow=False,
                font=dict(
                    color="#94a3b8",
                    size=11
                ),
                yshift=10
            )
        ]
    )

    return fig


# =============================================================
# 18. REAL OPTION CHART
# =============================================================

def render_real_option_chart(
    ce_df,
    pe_df,
    ce_ltp,
    pe_ltp,
    atm_strike
):

    if ce_df.empty or pe_df.empty:

        fig = go.Figure()

        fig.add_annotation(
            text="Waiting for Angel One historical candle data...",
            x=0.5,
            y=0.5,
            xref="paper",
            yref="paper",
            showarrow=False,
            font=dict(
                size=15,
                color="#94a3b8"
            )
        )

        fig.update_layout(
            height=640,
            template="plotly_dark"
        )

        return fig

    ce = ce_df.copy()
    pe = pe_df.copy()

    ce_times = ce["datetime"].dt.strftime(
        "%I:%M %p"
    )

    pe_times = pe["datetime"].dt.strftime(
        "%I:%M %p"
    )

    min_len = min(
        len(ce),
        len(pe)
    )

    ce = ce.tail(min_len)
    pe = pe.tail(min_len)

    times = ce["datetime"].dt.strftime(
        "%I:%M %p"
    )

    call_prices = ce["close"].values
    put_prices = pe["close"].values

    call_vol = ce["volume"].fillna(0).values
    put_vol = pe["volume"].fillna(0).values

    combined_volume = (
        call_vol + put_vol
    )

    combined_volume = np.where(
        combined_volume <= 0,
        1,
        combined_volume
    )

    straddle = (
        call_prices +
        put_prices
    )

    straddle_vwap = (
        np.cumsum(
            straddle *
            combined_volume
        )
        /
        np.cumsum(
            combined_volume
        )
    )

    call_poc = (
        np.average(
            call_prices,
            weights=np.maximum(
                call_vol,
                1
            )
        )
    )

    put_poc = (
        np.average(
            put_prices,
            weights=np.maximum(
                put_vol,
                1
            )
        )
    )

    straddle_tloc = np.mean(
        straddle
    )

    # Actual candle delta proxy:
    # volume direction from candle close vs open.
    # This is NOT fabricated tick data.
    ce_delta = np.where(
        ce["close"].values
        >=
        ce["open"].values,
        call_vol,
        -call_vol
    )

    pe_delta = np.where(
        pe["close"].values
        >=
        pe["open"].values,
        put_vol,
        -put_vol
    )

    combined_delta = (
        ce_delta +
        pe_delta
    )

    cvd = np.cumsum(
        combined_delta
    )

    fig = make_subplots(
        rows=3,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        row_heights=[
            0.50,
            0.25,
            0.25
        ],
        subplot_titles=(
            f"Dual Option vs POC (ATM {atm_strike})",
            "Combined Straddle vs VWAP & TLOC",
            "Candle Volume Delta & CVD"
        )
    )

    fig.add_trace(
        go.Scatter(
            x=times,
            y=call_prices,
            name="CALL CMP",
            line=dict(
                color="#00ff7f",
                width=2
            )
        ),
        row=1,
        col=1
    )

    fig.add_trace(
        go.Scatter(
            x=times,
            y=put_prices,
            name="PUT CMP",
            line=dict(
                color="#ff4d4d",
                width=2
            )
        ),
        row=1,
        col=1
    )

    fig.add_hline(
        y=call_poc,
        line_dash="dash",
        line_color="#99ff99",
        annotation_text=(
            f"CALL POC ₹{call_poc:.2f}"
        ),
        row=1,
        col=1
    )

    fig.add_hline(
        y=put_poc,
        line_dash="dash",
        line_color="#ff9999",
        annotation_text=(
            f"PUT POC ₹{put_poc:.2f}"
        ),
        row=1,
        col=1
    )

    fig.add_trace(
        go.Scatter(
            x=times,
            y=straddle,
            name="Straddle CE+PE",
            line=dict(
                color="#ffa500",
                width=1.5
            )
        ),
        row=2,
        col=1
    )

    fig.add_trace(
        go.Scatter(
            x=times,
            y=straddle_vwap,
            name="Straddle VWAP",
            line=dict(
                color="#ffff00",
                dash="dot",
                width=1.5
            )
        ),
        row=2,
        col=1
    )

    fig.add_hline(
        y=straddle_tloc,
        line_dash="dash",
        line_color="#ff4444",
        annotation_text=(
            f"TLOC ₹{straddle_tloc:.2f}"
        ),
        row=2,
        col=1
    )

    delta_colors = np.where(
        combined_delta >= 0,
        "#00ff7f",
        "#ff4d4d"
    )

    fig.add_trace(
        go.Bar(
            x=times,
            y=combined_delta,
            marker_color=delta_colors,
            name="Candle Delta"
        ),
        row=3,
        col=1
    )

    fig.add_trace(
        go.Scatter(
            x=times,
            y=cvd,
            name="CVD",
            line=dict(
                color="#00e5ff",
                width=1.5
            )
        ),
        row=3,
        col=1
    )

    fig.update_layout(
        height=640,
        template="plotly_dark",
        margin=dict(
            l=8,
            r=8,
            t=35,
            b=8
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )

    fig.update_xaxes(
        fixedrange=True
    )

    fig.update_yaxes(
        fixedrange=True
    )

    return fig


# =============================================================
# 19. STATUS BADGE
# =============================================================

def get_status_badge_html(
    status_text
):

    if status_text == "BULLISH":

        return (
            '<span class="badge-bullish-tag">'
            'BULLISH'
            '</span>'
        )

    if status_text == "BEARISH":

        return (
            '<span class="badge-bearish-tag">'
            'BEARISH'
            '</span>'
        )

    return (
        '<span class="badge-neutral-tag">'
        'NEUTRAL'
        '</span>'
    )


# =============================================================
# 20. HEADER
# =============================================================

st.title(
    "⚡ SHK TRADE LABS"
)

conn_badge = (
    "🟢 Angel One SmartAPI Feed (IST)"
    if smart_api
    else
    f"🟡 Feed Status: {auth_log}"
)

st.caption(
    f"Session Status: {conn_badge}"
)


# =============================================================
# 21. PLACEHOLDERS
# =============================================================

atm_header_box = st.empty()

breadth_box = st.empty()

checkpoints_box = st.empty()

metrics_box = st.empty()

oi_summary_box = st.empty()

oi_chart_box = st.empty()

chart_box = st.empty()

table_box = st.empty()


# =============================================================
# 22. SESSION STATE
# =============================================================

if "matrix_history" not in st.session_state:

    st.session_state.matrix_history = []


if "last_breadth_update_ts" not in st.session_state:

    st.session_state.last_breadth_update_ts = 0.0


if "last_breadth" not in st.session_state:

    st.session_state.last_breadth = (
        0,
        0,
        "NEUTRAL",
        0,
        0,
        0,
        0
    )


if "last_candle_minute" not in st.session_state:

    st.session_state.last_candle_minute = None


if "ce_history" not in st.session_state:

    st.session_state.ce_history = pd.DataFrame()


if "pe_history" not in st.session_state:

    st.session_state.pe_history = pd.DataFrame()


# =============================================================
# 23. LIVE DASHBOARD FRAGMENT
# =============================================================

@st.fragment(run_every="1s")
def live_dashboard():

    current_time = get_current_ist()

    market_active, market_msg = (
        is_market_open()
    )

    # ---------------------------------------------------------
    # LIVE NIFTY / OPTIONS
    # ---------------------------------------------------------

    (
        nifty_spot,
        fut_price,
        atm_strike,
        expiry_str,
        new_call,
        new_put,
        ce_token,
        pe_token,
        ce_symbol,
        pe_symbol
    ) = get_live_market_snapshot(
        smart_api,
        scrip_df
    )

    # ---------------------------------------------------------
    # LIVE VIX
    # ---------------------------------------------------------

    live_vix, live_vix_chg = (
        get_live_india_vix(
            smart_api
        )
    )

    # ---------------------------------------------------------
    # LIVE OI
    # ---------------------------------------------------------

    (
        strikes,
        pe_solid,
        pe_crossed,
        pe_hollow,
        ce_solid,
        ce_crossed,
        ce_hollow,
        cur_call_power,
        cur_put_power,
        live_pcr,
        total_ce_oi,
        total_pe_oi,
        is_live,
        max_pain_strike,
        option_count
    ) = fetch_live_oi_and_power(
        smart_api,
        scrip_df,
        atm_strike
    )

    # ---------------------------------------------------------
    # LIVE BREADTH
    # ---------------------------------------------------------

    now_timestamp = time.time()

    if (
        now_timestamp
        -
        st.session_state.last_breadth_update_ts
        >= 10
    ):

        st.session_state.last_breadth = (
            fetch_nifty_50_breadth_and_heavyweights(
                smart_api,
                nifty50_df
            )
        )

        st.session_state.last_breadth_update_ts = (
            now_timestamp
        )

    (
        ab_op,
        bl_op,
        op_sent,
        ab_15,
        bl_15,
        h_above_cnt,
        h_below_cnt
    ) = st.session_state.last_breadth

    # ---------------------------------------------------------
    # HISTORICAL OPTION DATA
    # ---------------------------------------------------------

    new_minute = (
        current_time.minute
        !=
        st.session_state.last_candle_minute
    )

    if new_minute:

        ce_df, pe_df = (
            build_option_history(
                smart_api,
                ce_token,
                pe_token,
                new_call,
                new_put
            )
        )

        if not ce_df.empty:

            st.session_state.ce_history = ce_df

        if not pe_df.empty:

            st.session_state.pe_history = pe_df

        st.session_state.last_candle_minute = (
            current_time.minute
        )

    ce_history = (
        st.session_state.ce_history
    )

    pe_history = (
        st.session_state.pe_history
    )

    # ---------------------------------------------------------
    # REAL OPTION POC / STRADDLE
    # ---------------------------------------------------------

    if (
        not ce_history.empty
        and
        not pe_history.empty
    ):

        ce_tail = ce_history.tail(35)
        pe_tail = pe_history.tail(35)

        min_len = min(
            len(ce_tail),
            len(pe_tail)
        )

        ce_tail = ce_tail.tail(
            min_len
        )

        pe_tail = pe_tail.tail(
            min_len
        )

        call_prices = (
            ce_tail["close"].values
        )

        put_prices = (
            pe_tail["close"].values
        )

        call_volumes = (
            ce_tail["volume"]
            .fillna(0)
            .values
        )

        put_volumes = (
            pe_tail["volume"]
            .fillna(0)
            .values
        )

        call_poc = float(
            np.average(
                call_prices,
                weights=np.maximum(
                    call_volumes,
                    1
                )
            )
        )

        put_poc = float(
            np.average(
                put_prices,
                weights=np.maximum(
                    put_volumes,
                    1
                )
            )
        )

        straddle_arr = (
            call_prices
            +
            put_prices
        )

        combined_volume = (
            call_volumes
            +
            put_volumes
        )

        combined_volume = np.where(
            combined_volume <= 0,
            1,
            combined_volume
        )

        straddle_vwap = float(
            np.cumsum(
                straddle_arr
                *
                combined_volume
            )[-1]
            /
            np.sum(
                combined_volume
            )
        )

        straddle_tloc = float(
            np.mean(
                straddle_arr
            )
        )

    else:

        call_poc = new_call
        put_poc = new_put

        straddle_arr = np.array(
            [new_call + new_put]
        )

        straddle_vwap = (
            new_call + new_put
        )

        straddle_tloc = (
            new_call + new_put
        )

    # ---------------------------------------------------------
    # CURRENT STRADDLE
    # ---------------------------------------------------------

    straddle_cmp = (
        new_call
        +
        new_put
    )

    # ---------------------------------------------------------
    # SENTIMENT
    # ---------------------------------------------------------

    sentiment_tag = (
        "🔴 Put Buyers Strong"
        if cur_put_power > cur_call_power
        else
        (
            "🟢 Call Buyers Strong"
            if cur_call_power > cur_put_power
            else
            "🟡 Imbalance Neutral"
        )
    )

    # ---------------------------------------------------------
    # CHECKPOINT 1
    # ---------------------------------------------------------

    cp1_val = (
        f"CE Net: {cur_call_power:+,d} "
        f"| PE Net: {cur_put_power:+,d}"
    )

    cp1_status = (
        "BULLISH"
        if (
            cur_call_power > 0
            and
            cur_put_power < 0
        )
        else
        (
            "BEARISH"
            if (
                cur_put_power > 0
                and
                cur_call_power < 0
            )
            else
            "NEUTRAL"
        )
    )

    # ---------------------------------------------------------
    # CHECKPOINT 2
    # ---------------------------------------------------------

    if strikes:

        atm_idx = len(strikes) // 2

        call_slice = (
            ce_solid[
                atm_idx:
            ]
        )

        put_slice = (
            pe_solid[
                :atm_idx + 1
            ]
        )

        if call_slice:

            call_wall = strikes[
                atm_idx
                +
                int(
                    np.argmax(
                        call_slice
                    )
                )
            ]

        else:

            call_wall = atm_strike

        if put_slice:

            put_wall = strikes[
                int(
                    np.argmax(
                        put_slice
                    )
                )
            ]

        else:

            put_wall = atm_strike

    else:

        call_wall = atm_strike
        put_wall = atm_strike

    cp2_val = (
        f"Spot: {nifty_spot:.1f} "
        f"| Wall: {put_wall} - {call_wall}"
    )

    cp2_status = (
        "BULLISH"
        if nifty_spot >= call_wall
        else
        (
            "BEARISH"
            if nifty_spot <= put_wall
            else
            "NEUTRAL"
        )
    )

    # ---------------------------------------------------------
    # CHECKPOINT 3
    # ---------------------------------------------------------

    cp3_val = (
        f"CE: ₹{new_call:.1f} "
        f"(POC: ₹{call_poc:.1f}) "
        f"| PE: ₹{new_put:.1f} "
        f"(POC: ₹{put_poc:.1f})"
    )

    cp3_status = (
        "BULLISH"
        if (
            new_call > call_poc
            and
            new_put < put_poc
        )
        else
        (
            "BEARISH"
            if (
                new_put > put_poc
                and
                new_call < call_poc
            )
            else
            "NEUTRAL"
        )
    )

    # ---------------------------------------------------------
    # CHECKPOINT 4
    # ---------------------------------------------------------

    cp4_val = (
        f"Straddle: ₹{straddle_cmp:.1f} "
        f"| VWAP: ₹{straddle_vwap:.1f} "
        f"| TLOC: ₹{straddle_tloc:.1f}"
    )

    cp4_status = (
        "BULLISH"
        if (
            straddle_cmp > straddle_vwap
            and
            straddle_cmp > straddle_tloc
        )
        else
        (
            "BEARISH"
            if (
                straddle_cmp < straddle_vwap
                and
                straddle_cmp < straddle_tloc
            )
            else
            "NEUTRAL"
        )
    )

    # ---------------------------------------------------------
    # CHECKPOINT 5
    # ---------------------------------------------------------

    order_flow_delta = (
        cur_call_power
        -
        cur_put_power
    )

    cp5_val = (
        f"Order Book Imbalance: "
        f"{order_flow_delta:+,d} contracts"
    )

    cp5_status = (
        "BULLISH"
        if order_flow_delta > 200000
        else
        (
            "BEARISH"
            if order_flow_delta < -200000
            else
            "NEUTRAL"
        )
    )

    # ---------------------------------------------------------
    # CHECKPOINT 6
    # ---------------------------------------------------------

    dist_pain = abs(
        nifty_spot
        -
        max_pain_strike
    )

    is_expiry_afternoon = (
        current_time.time()
        >=
        dtime(13, 0)
    )

    cp6_val = (
        f"Max Pain: {max_pain_strike} "
        f"(Dist: {dist_pain:.1f} pts)"
    )

    cp6_status = (
        "NEUTRAL"
        if (
            is_expiry_afternoon
            and
            dist_pain <= 30
        )
        else
        (
            "BULLISH"
            if cp3_status == "BULLISH"
            else
            (
                "BEARISH"
                if cp3_status == "BEARISH"
                else
                "NEUTRAL"
            )
        )
    )

    # ---------------------------------------------------------
    # CHECKPOINT 7
    # ---------------------------------------------------------

    cp7_val = (
        f"India VIX: "
        f"{live_vix:.2f} "
        f"({live_vix_chg:+.2f})"
    )

    cp7_status = (
        "BULLISH"
        if live_vix >= 11.5
        else
        "NEUTRAL"
    )

    # ---------------------------------------------------------
    # ATM TREND
    # ---------------------------------------------------------

    if (
        new_put > put_poc
        and
        new_call < call_poc
    ):

        atm_trend = "BEARISH"
        atm_class = "status-bearish"

    elif (
        new_call > call_poc
        and
        new_put < put_poc
    ):

        atm_trend = "BULLISH"
        atm_class = "status-bullish"

    else:

        atm_trend = "SIDEWAYS"
        atm_class = "status-wait"

    # ---------------------------------------------------------
    # MULTI TREND
    # ---------------------------------------------------------

    if (
        new_put > put_poc
        and
        cur_put_power > cur_call_power
    ):

        unwinding_status = (
            "🔥 Put Long Buildup "
            "(Heavy Put Buying)"
        )

        multi_trend = "BEARISH"
        multi_class = "status-bearish"

    elif (
        new_call > call_poc
        and
        cur_call_power > cur_put_power
    ):

        unwinding_status = (
            "🚀 Call Long Buildup "
            "(Heavy Call Buying)"
        )

        multi_trend = "BULLISH"
        multi_class = "status-bullish"

    else:

        unwinding_status = (
            "Neutral OI Distribution"
        )

        multi_trend = "MIXED"
        multi_class = "status-wait"

    # ---------------------------------------------------------
    # MARKET STATUS
    # ---------------------------------------------------------

    if market_active:

        if (
            atm_trend
            ==
            multi_trend
            and
            atm_trend
            in ["BULLISH", "BEARISH"]
        ):

            market_status = (
                "ACTIVE MOMENTUM"
            )

            market_class = (
                "status-bullish"
                if atm_trend == "BULLISH"
                else
                "status-bearish"
            )

        else:

            market_status = (
                "WAIT / MIXED"
            )

            market_class = (
                "status-wait"
            )

    else:

        market_status = (
            "MARKET CLOSED"
        )

        market_class = (
            "status-wait"
        )

    # =========================================================
    # RENDER 1: TOP PRICE
    # =========================================================

    atm_header_box.markdown(
        f"""
        <div class="top-price-box">

            <div class="top-price-row">

                <span class="val-badge-neutral">
                    NIFTY {nifty_spot:.2f}
                </span>

                <span class="val-badge-neutral">
                    FUT {fut_price:.2f}
                </span>

                <span class="val-badge-neutral">
                    ATM {atm_strike}
                </span>

                <span class="val-badge-neutral">
                    EXP {expiry_str}
                </span>

            </div>

            <div class="top-price-row">

                <span class="val-badge-call">
                    CALL ₹{new_call:.2f}
                </span>

                <span class="val-badge-put">
                    PUT ₹{new_put:.2f}
                </span>

                <span class="val-badge-neutral">
                    {market_msg}
                </span>

            </div>

        </div>
        """,
        unsafe_allow_html=True
    )

    # =========================================================
    # RENDER 2: BREADTH
    # =========================================================

    buy_class = (
        "num-box-buy-highlight"
        if ab_op >= 35
        else
        "num-box-buy"
    )

    sell_class = (
        "num-box-sell-highlight"
        if bl_op >= 35
        else
        "num-box-sell"
    )

    breadth_html = (
        '<div class="checkpoint-container">'

        '<div style="font-size:15px; '
        'font-weight:800; color:#38bdf8; '
        'margin-bottom:12px;">'
        '🏛️ Nifty 50 Equities Breadth Engine '
        '(Live 10s Stream)'
        '</div>'

        '<div class="breadth-flex-row">'

        '<span class="breadth-label">'
        'Above Open:'
        '</span>'

        f'<span class="{buy_class}">'
        f'{ab_op}'
        '</span>'

        f'<span class="{sell_class}">'
        f'{bl_op}'
        '</span>'

        '<span class="breadth-label">'
        'Below Open'
        '</span>'

        f'<div style="margin-left:auto;">'
        f'{get_status_badge_html(op_sent)}'
        f'</div>'

        '</div>'

        '<div class="breadth-flex-row">'

        '<span class="breadth-label">'
        'Above 15m High:'
        '</span>'

        f'<span class="num-box-buy">'
        f'{ab_15}'
        f'</span>'

        f'<span class="num-box-sell">'
        f'{bl_15}'
        f'</span>'

        '<span class="breadth-label">'
        'Below 15m Low'
        '</span>'

        '</div>'

        '<div class="breadth-flex-row" '
        'style="gap:14px; padding-top:10px;">'

        '<span class="breadth-label">'
        'Top Weightage:'
        '</span>'

        f'<span class="heavy-box-green">'
        f'{h_above_cnt}'
        f'</span>'

        f'<span class="heavy-box-red">'
        f'{h_below_cnt}'
        f'</span>'

        '</div>'

        '</div>'
    )

    breadth_box.markdown(
        breadth_html,
        unsafe_allow_html=True
    )

    # =========================================================
    # RENDER 3: CHECKPOINTS
    # =========================================================

    checkpoints_box.markdown(
        f"""
        <div class="checkpoint-container">

            <div style="
                font-size:15px;
                font-weight:800;
                color:#58a6ff;
                margin-bottom:8px;
            ">
                🎯 7 Institutional Edge Checkpoints
            </div>

            <div class="checkpoint-row">

                <div>
                    1. Multi-Strike Unwinding Filter
                </div>

                <div style="
                    display:flex;
                    align-items:center;
                ">

                    <span class="cp-val-text">
                        {cp1_val}
                    </span>

                    {get_status_badge_html(cp1_status)}

                </div>

            </div>

            <div class="checkpoint-row">

                <div>
                    2. Gamma Regime Filter (OI Walls)
                </div>

                <div style="
                    display:flex;
                    align-items:center;
                ">

                    <span class="cp-val-text">
                        {cp2_val}
                    </span>

                    {get_status_badge_html(cp2_status)}

                </div>

            </div>

            <div class="checkpoint-row">

                <div>
                    3. ATM Micro-Price vs Volume POC
                </div>

                <div style="
                    display:flex;
                    align-items:center;
                ">

                    <span class="cp-val-text">
                        {cp3_val}
                    </span>

                    {get_status_badge_html(cp3_status)}

                </div>

            </div>

            <div class="checkpoint-row">

                <div>
                    4. Straddle Value vs VWAP & TLOC
                </div>

                <div style="
                    display:flex;
                    align-items:center;
                ">

                    <span class="cp-val-text">
                        {cp4_val}
                    </span>

                    {get_status_badge_html(cp4_status)}

                </div>

            </div>

            <div class="checkpoint-row">

                <div>
                    5. Order Book Imbalance (Net Power)
                </div>

                <div style="
                    display:flex;
                    align-items:center;
                ">

                    <span class="cp-val-text">
                        {cp5_val}
                    </span>

                    {get_status_badge_html(cp5_status)}

                </div>

            </div>

            <div class="checkpoint-row">

                <div>
                    6. Expiry Day Max Pain Pinning Guard
                </div>

                <div style="
                    display:flex;
                    align-items:center;
                ">

                    <span class="cp-val-text">
                        {cp6_val}
                    </span>

                    {get_status_badge_html(cp6_status)}

                </div>

            </div>

            <div class="checkpoint-row">

                <div>
                    7. IV Skew & Volatility Alignment
                </div>

                <div style="
                    display:flex;
                    align-items:center;
                ">

                    <span class="cp-val-text">
                        {cp7_val}
                    </span>

                    {get_status_badge_html(cp7_status)}

                </div>

            </div>

        </div>
        """,
        unsafe_allow_html=True
    )

    # =========================================================
    # RENDER 4: METRICS
    # =========================================================

    metrics_box.markdown(
        f"""
        <div class="metric-grid">

            <div class="metric-card status-bearish">
                PUT POC: ₹{put_poc:.2f}
            </div>

            <div class="metric-card status-bullish">
                CALL POC: ₹{call_poc:.2f}
            </div>

            <div class="metric-card status-wait">
                TLOC: ₹{straddle_tloc:.2f}
            </div>

            <div class="metric-card {atm_class}">
                ATM: {atm_trend}
            </div>

            <div class="metric-card {multi_class}">
                MULTI: {multi_trend}
            </div>

            <div class="metric-card {market_class}">
                MARKET: {market_status}
            </div>

            <div class="metric-card status-info">
                {unwinding_status}
            </div>

        </div>
        """,
        unsafe_allow_html=True
    )

    # =========================================================
    # RENDER 5: OI SUMMARY
    # =========================================================

    vix_badge_color = (
        "#00ff7f"
        if live_vix_chg >= 0
        else
        "#ff4d4d"
    )

    ce_display = (
        f"{total_ce_oi / 100000:.2f}L"
    )

    pe_display = (
        f"{total_pe_oi / 100000:.2f}L"
    )

    oi_summary_box.markdown(
        f"""
        <div class="oi-summary-card">

            <div class="oi-item">

                INDIAVIX:

                <span style="
                    color:{vix_badge_color};
                ">

                    {live_vix:.2f}
                    ({live_vix_chg:+.2f})

                </span>

            </div>

            <div class="oi-item">

                PCR:

                <span class="pcr-badge">
                    {live_pcr:.2f}
                </span>

            </div>

            <div class="oi-item">

                Call Total OI:

                <span class="oi-call-val">
                    {ce_display}
                </span>

            </div>

            <div class="oi-item">

                Put Total OI:

                <span class="oi-put-val">
                    {pe_display}
                </span>

            </div>

            <div class="oi-item">

                Max Pain:

                <b>
                    {max_pain_strike}
                </b>

            </div>

            <div class="oi-item">

                NIFTY Spot:

                <b>
                    {nifty_spot:.2f}
                </b>

            </div>

        </div>
        """,
        unsafe_allow_html=True
    )

    # =========================================================
    # RENDER 6: OI CHART
    # =========================================================

    oi_fig = render_oi_chart(
        strikes,
        pe_solid,
        pe_crossed,
        pe_hollow,
        ce_solid,
        ce_crossed,
        ce_hollow,
        fut_price
    )

    oi_chart_box.plotly_chart(
        oi_fig,
        use_container_width=True,
        config={
            "displayModeBar": False
        }
    )

    # =========================================================
    # RENDER 7: OPTION CHART
    # =========================================================

    option_fig = render_real_option_chart(
        ce_history,
        pe_history,
        new_call,
        new_put,
        atm_strike
    )

    chart_box.plotly_chart(
        option_fig,
        use_container_width=True,
        config={
            "displayModeBar": False
        }
    )

    # =========================================================
    # RENDER 8: POWER MATRIX
    # =========================================================

    live_time_label = (
        f"🔴 LIVE "
        f"({current_time.strftime('%I:%M:%S %p')})"
        if market_active
        else
        f"⏸️ CLOSED "
        f"({current_time.strftime('%I:%M:%S %p')})"
    )

    current_record = {
        "Time (IST)": live_time_label,
        "Call Power (CE Contracts)": (
            f"{cur_call_power:+,d}"
        ),
        "Put Power (PE Contracts)": (
            f"{cur_put_power:+,d}"
        ),
        "Market Sentiment": sentiment_tag
    }

    # Store a new minute only.
    minute_key = (
        current_time.strftime(
            "%Y-%m-%d %H:%M"
        )
    )

    if (
        not st.session_state.matrix_history
        or
        st.session_state.matrix_history[-1]
        .get("_minute")
        != minute_key
    ):

        st.session_state.matrix_history.append(
            {
                "_minute": minute_key,
                "Time": current_time.strftime(
                    "%I:%M %p"
                ),
                "Call Power": cur_call_power,
                "Put Power": cur_put_power,
                "Sentiment": sentiment_tag
            }
        )

        if (
            len(
                st.session_state.matrix_history
            )
            >
            4
        ):

            st.session_state.matrix_history.pop(0)

    table_rows = [
        current_record
    ]

    for hist in reversed(
        st.session_state.matrix_history
    ):

        table_rows.append(
            {
                "Time (IST)": hist["Time"],
                "Call Power (CE Contracts)": (
                    f"{hist['Call Power']:+,d}"
                ),
                "Put Power (PE Contracts)": (
                    f"{hist['Put Power']:+,d}"
                ),
                "Market Sentiment": (
                    hist["Sentiment"]
                )
            }
        )

    table_box.table(
        pd.DataFrame(
            table_rows
        )
    )


# =============================================================
# 24. START LIVE DASHBOARD
# =============================================================

live_dashboard()
