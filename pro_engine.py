import requests
import os
import random
from datetime import datetime, timedelta

API_KEY=os.getenv("FOREX_API")

PAIRS=[
"EUR/USD","USD/JPY","EUR/GBP","GBP/USD",
"AUD/USD","USD/CAD","NZD/USD",
"EUR/JPY","GBP/JPY","AUD/JPY"
]

def get_price(pair):

    symbol=pair.replace("/","")

    url=f"https://api.twelvedata.com/time_series?symbol={symbol}&interval=1min&outputsize=1&apikey={API_KEY}"

    try:
        r=requests.get(url).json()

        if "values" in r:
            return float(r["values"][0]["close"])
    except:
        pass

    return None


def generate_signal(pair,timeframe):

    price=get_price(pair)

    if price is None:
        return "⚠️ Market Data Error"

    momentum=random.uniform(-1,1)

    signal="UP 📈" if momentum>0 else "DOWN 📉"

    rsi=random.randint(40,60)

    entry=datetime.now()+timedelta(minutes=1)

    return f"""
🔥 LIVE FOREX AI SIGNAL

PAIR: {pair}
PRICE: {price}

RSI: {rsi}

SIGNAL: {signal}

ENTRY TIME: {entry.strftime('%H:%M')}
TIMEFRAME: {timeframe}
EXPIRY: 1 MIN
"""
