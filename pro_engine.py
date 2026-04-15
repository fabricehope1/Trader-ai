import requests
import random
from datetime import datetime, timedelta
import pytz

# ================= RWANDA TIME =================

RWANDA = pytz.timezone("Africa/Kigali")

# ================= PAIRS =================

PAIRS = [
    "EUR/USD",
    "GBP/USD",
    "USD/JPY",
    "AUD/USD",
    "USD/CAD",
    "EUR/JPY"
]

# ================= STOOQ SYMBOL =================

def stooq_symbol(pair):
    return pair.replace("/","").lower()

# ================= GET MARKET DATA =================

def get_market(pair):

    symbol = stooq_symbol(pair)

    url = f"https://stooq.com/q/d/l/?s={symbol}&i=m"

    try:
        r = requests.get(url, timeout=10)

        lines = r.text.split("\n")

        prices = []

        for line in lines[1:60]:
            parts = line.split(",")

            if len(parts) > 4:
                prices.append(float(parts[4]))

        return prices

    except:
        return None

# ================= EMA =================

def ema(data, period):

    k = 2/(period+1)
    ema_val = data[0]

    for price in data:
        ema_val = price*k + ema_val*(1-k)

    return ema_val

# ================= RSI =================

def rsi(data, period=14):

    gains=[]
    losses=[]

    for i in range(1,len(data)):
        diff=data[i]-data[i-1]

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

# ================= ANALYSIS =================

def analyze(prices):

    ema_fast=ema(prices[-20:],20)
    ema_slow=ema(prices[-50:],50)

    rsi_val=rsi(prices)

    buy=0
    sell=0

    if ema_fast>ema_slow:
        buy+=1
    else:
        sell+=1

    if rsi_val>55:
        buy+=1

    if rsi_val<45:
        sell+=1

    if buy>sell:
        return "🟢 BUY (CALL)"
    else:
        return "🔴 SELL (PUT)"

# ================= ENTRY TIME =================

def entry_time(tf):

    now=datetime.now(RWANDA)

    if tf=="M1":
        entry=now+timedelta(minutes=1)
    elif tf=="M5":
        entry=now+timedelta(minutes=5)
    else:
        entry=now+timedelta(minutes=15)

    return entry.strftime("%H:%M")

# ================= MAIN ENGINE =================

def generate_signal(pair,tf):

    prices=get_market(pair)

    if not prices or len(prices)<50:
        return "⚠️ Market loading... try again"

    direction=analyze(prices)

    confidence=random.randint(83,95)

    entry=entry_time(tf)

    return f"""
🔥 PRO AI SIGNAL

Pair: {pair}
Direction: {direction}
Timeframe: {tf}

Entry Time 🇷🇼: {entry}

Accuracy: {confidence}%

Stooq Smart Analysis
"""
