import requests
import random
import os
from datetime import datetime, timedelta

# =============================
# LOAD API FROM ENV VARIABLE
# =============================

API_KEY = os.getenv("FOREX_API")

# =============================
# FOREX PAIRS
# =============================

PAIRS = {
    "EURUSD": "EUR/USD",
    "USDJPY": "USD/JPY",
    "EURGBP": "EUR/GBP",
    "GBPUSD": "GBP/USD",
    "AUDUSD": "AUD/USD",
    "USDCAD": "USD/CAD",
    "NZDUSD": "NZD/USD",
    "EURJPY": "EUR/JPY",
    "GBPJPY": "GBP/JPY",
    "AUDJPY": "AUD/JPY"
}

# =============================
# GET LIVE PRICE
# =============================

def get_price(pair):

    url = f"https://api.twelvedata.com/price?symbol={pair}&apikey={API_KEY}"

    try:
        r = requests.get(url).json()
        return float(r["price"])
    except:
        return None


# =============================
# RSI SIMULATION
# =============================

def calculate_rsi():
    return random.randint(30, 70)


# =============================
# MARKET ANALYSIS
# =============================

def analyze_market(price, rsi):

    if price is None:
        return "WAIT ⏳"

    if rsi < 45:
        return "UP 📈"

    elif rsi > 55:
        return "DOWN 📉"

    return "WAIT ⏳"


# =============================
# ENTRY TIME
# =============================

def entry_time():
    now = datetime.now()
    entry = now + timedelta(minutes=1)
    return entry.strftime("%H:%M")


# =============================
# SIGNAL ENGINE
# =============================

def generate_signal(pair):

    if pair not in PAIRS:
        return "Pair not supported"

    price = get_price(pair)
    rsi = calculate_rsi()
    direction = analyze_market(price, rsi)
    entry = entry_time()

    return f"""
🔥 PRO AI FOREX SIGNAL

PAIR: {PAIRS[pair]}
PRICE: {price}

RSI: {rsi}

SIGNAL: {direction}

ENTRY TIME: {entry}
TIMEFRAME: M1
"""
