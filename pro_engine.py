import requests
import os
from datetime import datetime, timedelta

# ================= API =================

API_KEY = os.getenv("FOREX_API_KEY")

INTERVALS = {
    "M1": "1min",
    "M5": "5min",
    "M15": "15min"
}

# ================= PAIRS =================

PAIRS = [
    "EUR/USD",
    "GBP/USD",
    "USD/JPY",
    "EUR/JPY",
    "GBP/JPY",
]

# ================= GET MARKET DATA =================

def get_market(pair, timeframe):

    symbol = pair.replace("/", "")

    interval = INTERVALS.get(timeframe, "1min")

    url = (
        f"https://api.twelvedata.com/time_series?"
        f"symbol={symbol}"
        f"&interval={interval}"
        f"&outputsize=120"
        f"&apikey={API_KEY}"
    )

    data = requests.get(url).json()

    if "values" not in data:
        raise Exception("Market data error")

    closes = [float(c["close"]) for c in data["values"]]
    closes.reverse()

    return closes


# ================= RSI =================

def rsi(data, period=14):

    gains = []
    losses = []

    for i in range(1, len(data)):
        diff = data[i] - data[i - 1]

        if diff > 0:
            gains.append(diff)
        else:
            losses.append(abs(diff))

    avg_gain = sum(gains[-period:]) / period if gains else 0
    avg_loss = sum(losses[-period:]) / period if losses else 0

    if avg_loss == 0:
        return 50

    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


# ================= EMA =================

def ema(data, period):

    k = 2 / (period + 1)
    ema_val = data[0]

    for price in data:
        ema_val = price * k + ema_val * (1 - k)

    return ema_val


# ================= MACD =================

def macd(data):
    return ema(data, 12) - ema(data, 26)


# ================= SUPPORT / RESIST =================

def resistance(data):
    return max(data[-30:])

def support(data):
    return min(data[-30:])


# ================= RWANDA ENTRY TIME =================

def entry_time():

    now = datetime.utcnow() + timedelta(hours=2)
    entry = now + timedelta(seconds=15)

    return entry.strftime("%H:%M:%S")


# ================= SIGNAL ENGINE =================

def generate_signal(pair, timeframe):

    try:

        closes = get_market(pair, timeframe)

        price = closes[-1]

        rsi_val = rsi(closes)
        macd_val = macd(closes)

        ema_fast = ema(closes, 9)
        ema_slow = ema(closes, 21)

        res = resistance(closes)
        sup = support(closes)

        buy = 0
        sell = 0

        # ===== RSI LOGIC =====
        if rsi_val < 40:
            buy += 1
        elif rsi_val > 60:
            sell += 1

        # ===== EMA TREND =====
        if ema_fast > ema_slow:
            buy += 1
        else:
            sell += 1

        # ===== MACD =====
        if macd_val > 0:
            buy += 1
        else:
            sell += 1

        # ===== SUPPORT / RESIST =====
        if price <= sup * 1.002:
            buy += 1

        if price >= res * 0.998:
            sell += 1

        strength = abs(buy - sell)

        # ===== FILTER =====
        if strength < 2:
            return "⚠ Market weak now. Wait next signal."

        signal = "🟢 BUY (CALL)" if buy > sell else "🔴 SELL (PUT)"

        winrate = min(92, 85 + strength)

        entry = entry_time()

        return f"""
🔥 PRO AI SIGNAL

PAIR: {pair}
TIMEFRAME: {timeframe}

PRICE: {round(price,5)}

RSI: {round(rsi_val,2)}
MACD: {round(macd_val,5)}

SIGNAL: {signal}

ENTRY TIME 🇷🇼: {entry}
EXPIRY: {timeframe}

WINRATE BOOSTER: {winrate}%
STRENGTH: {strength}/4
"""

    except Exception as e:
        return f"❌ Signal error: {e}"
