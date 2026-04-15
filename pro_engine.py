import os
import requests
import pandas as pd
import time

API_KEY = os.getenv("FOREX_API")

PAIRS = [
    "EUR/USD",
    "GBP/USD",
    "USD/JPY",
    "AUD/USD",
    "USD/CAD"
]

# =========================
# GET MARKET DATA
# =========================
def get_market_data(symbol):

    url = f"https://api.twelvedata.com/time_series?symbol={symbol}&interval=1min&outputsize=100&apikey={API_KEY}"

    r = requests.get(url)
    data = r.json()

    if "values" not in data:
        return None

    df = pd.DataFrame(data["values"])
    df = df.astype(float)
    df = df.iloc[::-1]

    return df


# =========================
# RSI
# =========================
def calculate_rsi(df, period=14):

    delta = df["close"].diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    return rsi.iloc[-1]


# =========================
# EMA
# =========================
def calculate_ema(df, period):

    return df["close"].ewm(span=period).mean().iloc[-1]


# =========================
# MACD
# =========================
def calculate_macd(df):

    ema12 = df["close"].ewm(span=12).mean()
    ema26 = df["close"].ewm(span=26).mean()

    macd = ema12 - ema26
    signal = macd.ewm(span=9).mean()

    return macd.iloc[-1], signal.iloc[-1]


# =========================
# SUPPORT / RESISTANCE
# =========================
def support_resistance(df):

    support = df["low"].tail(20).min()
    resistance = df["high"].tail(20).max()

    return support, resistance


# =========================
# SIGNAL ENGINE
# =========================
def generate_signal():

    results = []

    for pair in PAIRS:

        df = get_market_data(pair)

        if df is None:
            continue

        # ⏳ Analysis time
        time.sleep(2)

        price = df["close"].iloc[-1]

        rsi = calculate_rsi(df)
        ema20 = calculate_ema(df, 20)
        ema50 = calculate_ema(df, 50)

        macd, macd_signal = calculate_macd(df)

        support, resistance = support_resistance(df)

        signal = "WAIT"

        # ======================
        # BUY CONDITIONS
        # ======================
        if (
            rsi < 35 and
            price > ema20 > ema50 and
            macd > macd_signal and
            price > support
        ):
            signal = "BUY 🟢"

        # ======================
        # SELL CONDITIONS
        # ======================
        elif (
            rsi > 65 and
            price < ema20 < ema50 and
            macd < macd_signal and
            price < resistance
        ):
            signal = "SELL 🔴"

        results.append({
            "pair": pair,
            "signal": signal,
            "price": price,
            "rsi": round(rsi,2)
        })

    return results
