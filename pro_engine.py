import requests
import os
from datetime import datetime,timedelta

API_KEY=os.getenv("FOREX_API")

PAIRS=[
"EUR/USD","USD/JPY","EUR/GBP","GBP/USD",
"AUD/USD","USD/CAD","NZD/USD",
"EUR/JPY","GBP/JPY","AUD/JPY"
]

# ================= REAL MARKET PRICE =================

def get_price(pair):

    try:

        url=f"https://api.twelvedata.com/time_series?symbol={pair}&interval=1min&outputsize=2&apikey={API_KEY}"

        r=requests.get(url).json()

        if "values" not in r:
            print(r)
            return None

        current=float(r["values"][0]["close"])
        previous=float(r["values"][1]["close"])

        return current,previous

    except Exception as e:
        print(e)
        return None


# ================= SIGNAL ENGINE =================

def generate_signal(pair,timeframe):

    data=get_price(pair)

    if data is None:
        return "⚠️ Market Data Error"

    current,previous=data

    # REAL TREND ANALYSIS
    if current>previous:
        signal="UP 📈"
    else:
        signal="DOWN 📉"

    # REAL ENTRY TIME
    entry=datetime.utcnow()+timedelta(minutes=1)

    return f"""
🔥 LIVE AI SIGNAL

PAIR: {pair}

PRICE: {current}

SIGNAL: {signal}

ENTRY TIME: {entry.strftime('%H:%M')} UTC
TIMEFRAME: {timeframe}

EXPIRY: 1 MIN
"""
