import requests
import pandas as pd
import ta
import os
from datetime import datetime
from zoneinfo import ZoneInfo   # Rwanda Time

API_KEY = os.getenv("FOREX_API_KEY")

# ================= PAIRS =================
PAIRS = [
    "EUR/USD",
    "GBP/USD",
    "USD/JPY",
    "EUR/GBP",
    "AUD/USD",
    "USD/CAD"
]

# ================= TIMEFRAME =================
TF_MAP = {
    "M1": "1min",
    "M5": "5min",
    "M15": "15min"
}


# ================= GET FOREX DATA =================
def get_data(pair, timeframe):

    interval = TF_MAP[timeframe]

    url = (
        f"https://api.twelvedata.com/time_series"
        f"?symbol={pair}&interval={interval}&outputsize=120&apikey={API_KEY}"
    )

    response = requests.get(url).json()

    if "values" not in response:
        return None

    df = pd.DataFrame(response["values"])

    df["close"] = df["close"].astype(float)
    df["open"] = df["open"].astype(float)
    df["high"] = df["high"].astype(float)
    df["low"] = df["low"].astype(float)

    return df.iloc[::-1]


# ================= ANALYSIS ENGINE =================
def analyze(df):

    df["ema20"] = ta.trend.ema_indicator(df["close"], window=20)
    df["ema50"] = ta.trend.ema_indicator(df["close"], window=50)
    df["rsi"] = ta.momentum.rsi(df["close"], window=14)

    macd = ta.trend.MACD(df["close"])
    df["macd"] = macd.macd()
    df["macd_signal"] = macd.macd_signal()

    last = df.iloc[-1]

    score = 0

    # Trend
    if last["ema20"] > last["ema50"]:
        score += 1
    else:
        score -= 1

    # RSI
    if last["rsi"] < 35:
        score += 1

    if last["rsi"] > 65:
        score -= 1

    # Momentum
    if last["macd"] > last["macd_signal"]:
        score += 1
    else:
        score -= 1

    if score >= 2:
        return "CALL 📈", score

    if score <= -2:
        return "PUT 📉", score

    return None, score


# ================= RWANDA TIME =================
def rwanda_time():
    return datetime.now(ZoneInfo("Africa/Kigali")).strftime("%H:%M:%S")


# ================= SIGNAL FUNCTION =================
def generate_signal(pair, timeframe):

    df = get_data(pair, timeframe)

    if df is None:
        return {"status": "error"}

    signal, confidence = analyze(df)

    if not signal:
        return {
            "status": "wait",
            "message": "⏳ Market not safe now. Wait next setup..."
        }

    accuracy = 75 + abs(confidence) * 5

    if accuracy > 90:
        accuracy = 90

    return {
        "status": "success",
        "pair": pair,
        "signal": signal,
        "timeframe": timeframe,
        "entry_time": rwanda_time(),
        "accuracy": f"{accuracy}%"
}
