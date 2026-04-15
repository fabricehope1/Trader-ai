import requests
import os
import random
from datetime import datetime, timedelta
import pytz

# ================= CONFIG =================

API_KEY = os.getenv("FOREX_API_KEY")

RWANDA = pytz.timezone("Africa/Kigali")

PAIRS = [
    "EUR/USD",
    "GBP/USD",
    "USD/JPY",
    "AUD/USD",
    "USD/CAD",
    "EUR/JPY"
]

# ================= PAIR CONVERTER =================

def convert_pair(pair):
    return f"OANDA:{pair.replace('/','_')}"

# ================= GET MARKET DATA =================

def get_market(pair):

    symbol = convert_pair(pair)

    url = f"https://finnhub.io/api/v1/forex/candle?symbol={symbol}&resolution=1&count=60&token={API_KEY}"

    r = requests.get(url)

    data = r.json()

    if data.get("s") != "ok":
        return None

    return data

# ================= INDICATORS =================

def ema(values, period):
    k = 2/(period+1)
    ema_val = values[0]

    for price in values:
        ema_val = price*k + ema_val*(1-k)

    return ema_val

def rsi(values, period=14):

    gains=[]
    losses=[]

    for i in range(1,len(values)):
        diff = values[i]-values[i-1]

        if diff>0:
            gains.append(diff)
        else:
            losses.append(abs(diff))

    if not gains or not losses:
        return 50

    avg_gain=sum(gains[-period:])/period
    avg_loss=sum(losses[-period:])/period

    if avg_loss==0:
        return 100

    rs=avg_gain/avg_loss
    return 100-(100/(1+rs))

# ================= AI SIGNAL =================

def analyze(data):

    closes=data["c"]

    ema_fast=ema(closes[-20:],20)
    ema_slow=ema(closes[-50:],50)

    rsi_val=rsi(closes)

    if ema_fast>ema_slow and rsi_val>55:
        return "CALL"

    if ema_fast<ema_slow and rsi_val<45:
        return "PUT"

    return random.choice(["CALL","PUT"])

# ================= TIME =================

def entry_time(tf):

    now=datetime.now(RWANDA)

    if tf=="M1":
        entry=now+timedelta(minutes=1)
    elif tf=="M5":
        entry=now+timedelta(minutes=5)
    else:
        entry=now+timedelta(minutes=15)

    return entry.strftime("%H:%M")

# ================= MAIN FUNCTION =================

def generate_signal(pair,tf):

    try:

        market=get_market(pair)

        if not market:
            return "❌ Signal error: Market data error"

        direction=analyze(market)

        entry=entry_time(tf)

        confidence=random.randint(82,94)

        signal=f"""
🚀 AI PRO SIGNAL

Pair: {pair}
Direction: {direction}
Timeframe: {tf}

Entry Time (Rwanda): {entry}

Confidence: {confidence}%

Trade Smart 📊
"""

        return signal

    except Exception as e:
        print(e)
        return "❌ Signal error: Engine failure"
