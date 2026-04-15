hereimport requests
import pandas as pd
import ta
import os
from datetime import datetime
import pytz

# ========================
# API KEY
# ========================
API_KEY = os.getenv("FOREX_API_KEY")

# ========================
# FOREX PAIRS (Binary Options)
# ========================
PAIRS = [
    "EUR/USD",
    "GBP/USD",
    "USD/JPY",
    "USD/CAD",
    "EUR/GBP",
    "AUD/USD"
]

# ========================
# TIMEFRAMES
# ========================
TIMEFRAME_MAP = {
    "M1": "1min",
    "M5": "5min",
    "M15": "15min"
}


# ========================
# GET MARKET DATA
# ========================
def get_market_data(pair, timeframe):

    url = "https://api.twelvedata.com/time_series"

    params = {
        "symbol": pair,
        "interval": timeframe,
        "apikey": API_KEY,
        "outputsize": 120
    }

    try:
        response = requests.get(url, params=params).json()

        if "values" not in response:
            print("API ERROR:", response)
            return None

        df = pd.DataFrame(response["values"])
        df = df.astype(float)
        df = df[::-1]

        return df

    except Exception as e:
        print("DATA ERROR:", e)
        return None


# ========================
# SIGNAL ENGINE
# ========================
def generate_signal(pair, tf):

    if tf not in TIMEFRAME_MAP:
        return "Invalid timeframe"

    timeframe = TIMEFRAME_MAP[tf]

    df = get_market_data(pair, timeframe)

    if df is None or len(df) < 60:
        return None

    close = df["close"]

    # Indicators
    rsi = ta.momentum.RSIIndicator(close).rsi()
    ema_fast = ta.trend.EMAIndicator(close, window=20).ema_indicator()
    ema_slow = ta.trend.EMAIndicator(close, window=50).ema_indicator()

    price = close.iloc[-1]
    rsi_last = rsi.iloc[-1]
    ema20 = ema_fast.iloc[-1]
    ema50 = ema_slow.iloc[-1]

    signal = "WAIT ⏳"

    if price > ema20 > ema50 and rsi_last > 55:
        signal = "CALL 📈"

    elif price < ema20 < ema50 and rsi_last < 45:
        signal = "PUT 📉"

    # Rwanda Time
    tz = pytz.timezone("Africa/Kigali")
    entry_time = datetime.now(tz).strftime("%H:%M:%S")

    message = f"""
📊 BINARY OPTIONS SIGNAL

PAIR: {pair}
TIMEFRAME: {tf}

SIGNAL: {signal}

ENTRY TIME 🇷🇼: {entry_time}
EXPIRY: {tf}
"""

    return message
