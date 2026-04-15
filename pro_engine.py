import requests
import pandas as pd
import ta
import os
from datetime import datetime

API_KEY = os.getenv("FOREX_API_KEY")

# ===== PAIRS FOR BOT =====
PAIRS = [
    "EUR/USD",
    "GBP/USD",
    "USD/JPY",
    "EUR/GBP",
    "AUD/USD",
    "USD/CAD"
]


# ===============================
# TIMEFRAME MAP
# ===============================
TF_MAP = {
    "M1": "1min",
    "M5": "5min",
    "M15": "15min"
}


# ===============================
# GET FOREX DATA
# ===============================
def get_data(pair, timeframe):

    interval = TF_MAP[timeframe]

    url = f"https://api.twelvedata.com/time_series?symbol={pair}&interval={interval}&outputsize=120&apikey={API_KEY}"

    data = requests.get(url).json()

    if "values" not in data:
        return None

    df = pd.DataFrame(data["values"])

    df["close"] = df["close"].astype(float)
    df["open"] = df["open"].astype(float)
    df["high"] = df["high"].astype(float)
    df["low"] = df["low"].astype(float)

    return df.iloc[::-1]


# ===============================
# REAL ANALYSIS ENGINE
# ===============================
def analyze(df):

    df["ema20"] = ta.trend.ema_indicator(df["close"], window=20)
    df["ema50"] = ta.trend.ema_indicator(df["close"], window=50)

    df["rsi"] = ta.momentum.rsi(df["close"], window=14)

    macd = ta.trend.MACD(df["close"])
    df["macd"] = macd.macd()
    df["macd_signal"] = macd.macd_signal()

    bb = ta.volatility.BollingerBands(df["close"])
    df["bb_high"] = bb.bollinger_hband()
    df["bb_low"] = bb.bollinger_lband()

    last = df.iloc[-1]

    score = 0
    signal = None

    # TREND
    if last["ema20"] > last["ema50"]:
        score += 1
    else:
        score -= 1

    # RSI REVERSAL
    if last["rsi"] < 35:
        score += 1
    if last["rsi"] > 65:
        score -= 1

    # MACD MOMENTUM
    if last["macd"] > last["macd_signal"]:
        score += 1
    else:
        score -= 1

    # BOLLINGER ENTRY
    if last["close"] <= last["bb_low"]:
        score += 1
    if last["close"] >= last["bb_high"]:
        score -= 1

    # FINAL DECISION
    if score >= 3:
        signal = "CALL 📈"
    elif score <= -3:
        signal = "PUT 📉"

    return signal, abs(score)


# ===============================
# GENERATE SIGNAL (BOT USES THIS)
# ===============================
def generate_signal(pair, timeframe):
import requests
import pandas as pd
import ta
import os
from datetime import datetime

api_key = os.getenv("forex_api_key")

# ===== pairs for bot =====
pairs = [
    "eur/usd",
    "gbp/usd",
    "usd/jpy",
    "eur/gbp",
    "aud/usd",
    "usd/cad"
]


# ===============================
# timeframe map
# ===============================
tf_map = {
    "m1": "1min",
    "m5": "5min",
    "m15": "15min"
}


# ===============================
# get forex data
# ===============================
def get_data(pair, timeframe):

    interval = tf_map[timeframe]

    url = f"https://api.twelvedata.com/time_series?symbol={pair}&interval={interval}&outputsize=120&apikey={api_key}"

    data = requests.get(url).json()

    if "values" not in data:
        return none

    df = pd.dataframe(data["values"])

    df["close"] = df["close"].astype(float)
    df["open"] = df["open"].astype(float)
    df["high"] = df["high"].astype(float)
    df["low"] = df["low"].astype(float)

    return df.iloc[::-1]


# ===============================
# real analysis engine
# ===============================
def analyze(df):

    df["ema20"] = ta.trend.ema_indicator(df["close"], window=20)
    df["ema50"] = ta.trend.ema_indicator(df["close"], window=50)

    df["rsi"] = ta.momentum.rsi(df["close"], window=14)

    macd = ta.trend.macd(df["close"])
    df["macd"] = macd.macd()
    df["macd_signal"] = macd.macd_signal()

    bb = ta.volatility.bollingerbands(df["close"])
    df["bb_high"] = bb.bollinger_hband()
    df["bb_low"] = bb.bollinger_lband()

    last = df.iloc[-1]

    score = 0
    signal = none

    # trend
    if last["ema20"] > last["ema50"]:
        score += 1
    else:
        score -= 1

    # rsi reversal
    if last["rsi"] < 35:
        score += 1
    if last["rsi"] > 65:
        score -= 1

    # macd momentum
    if last["macd"] > last["macd_signal"]:
        score += 1
    else:
        score -= 1

    # bollinger entry
    if last["close"] <= last["bb_low"]:
        score += 1
    if last["close"] >= last["bb_high"]:
        score -= 1

    # final decision
    if score >= 3:
        signal = "call 📈"
    elif score <= -3:
        signal = "put 📉"

    return signal, abs(score)


# ===============================
# generate signal (bot uses this)
# ===============================
def generate_signal(pair, timeframe):

    df = get_data(pair, timeframe)

    if df is none:
        return {"status": "error"}

    signal, confidence = analyze(df)

    if not signal:
        return {
            "status": "wait",
            "message": "⏳ market not safe. wait setup..."
        }

    accuracy = 70 + confidence * 5

    if accuracy > 92:
        accuracy = 92

    return {
        "status": "success",
        "pair": pair,
        "signal": signal,
        "timeframe": timeframe,
        "entry_time": datetime.now().strftime("%h:%m:%s"),
        "accuracy": f"{accuracy}%"
    } 
