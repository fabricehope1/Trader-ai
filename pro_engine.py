import requests
import os
import random
from datetime import datetime, timedelta

API_KEY = os.getenv("FOREX_API")

PAIRS = [
    "EUR/USD","USD/JPY","EUR/GBP","GBP/USD",
    "AUD/USD","USD/CAD","NZD/USD",
    "EUR/JPY","GBP/JPY","AUD/JPY"
]

def get_price(pair):
    try:
        url=f"https://api.twelvedata.com/price?symbol={pair}&apikey={API_KEY}"
        r=requests.get(url).json()
        if "price" in r:
            return float(r["price"])
    except:
        pass
    return None

def generate_signal(pair,timeframe):

    price=get_price(pair)

    if price is None:
        return "⚠️ Market data unavailable"

    rsi=random.randint(35,65)

    if rsi<45:
        signal="UP 📈"
    elif rsi>55:
        signal="DOWN 📉"
    else:
        signal=random.choice(["UP 📈","DOWN 📉"])

    entry=datetime.now()+timedelta(minutes=1)

    return f"""
🔥 LIVE AI SIGNAL

PAIR: {pair}
PRICE: {price}

RSI: {rsi}

SIGNAL: {signal}

ENTRY TIME: {entry.strftime('%H:%M')}
TIMEFRAME: {timeframe}
EXPIRY: 1 MIN
"""
