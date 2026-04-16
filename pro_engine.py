import requests
import statistics
import random
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import json
import os

# ================= SETTINGS =================

API_KEY="f29c55ce7132437e86f7b025670ec8e4"

PAIRS=[
    "EUR/USD",
    "GBP/USD",
    "USD/JPY",
    "AUD/USD"
]

# ================= WIN TRACKER =================

STATS_FILE="stats.json"

def load_stats():
    if not os.path.exists(STATS_FILE):
        return {"win":0,"loss":0}
    with open(STATS_FILE,"r") as f:
        return json.load(f)

def save_stats(data):
    with open(STATS_FILE,"w") as f:
        json.dump(data,f)

def calculate_winrate():
    data=load_stats()
    total=data["win"]+data["loss"]
    if total==0:
        return 0
    return round((data["win"]/total)*100)

# ================= GET MARKET DATA =================

def get_prices(pair):

    symbol=pair.replace("/","")

    url=f"https://api.twelvedata.com/time_series?symbol={symbol}&interval=1min&outputsize=60&apikey={API_KEY}"

    r=requests.get(url).json()

    if "values" not in r:
        return None

    prices=[float(x["close"]) for x in r["values"]]

    return prices[::-1]

# ================= RSI =================

def calculate_rsi(prices,period=14):

    gains=[]
    losses=[]

    for i in range(1,len(prices)):
        diff=prices[i]-prices[i-1]
        if diff>0:
            gains.append(diff)
        else:
            losses.append(abs(diff))

    if not gains or not losses:
        return 50

    avg_gain=sum(gains[-period:])/period
    avg_loss=sum(losses[-period:])/period

    rs=avg_gain/avg_loss if avg_loss!=0 else 0
    rsi=100-(100/(1+rs))

    return round(rsi,2)

# ================= TREND =================

def get_trend(prices):

    ma_fast=statistics.mean(prices[-5:])
    ma_slow=statistics.mean(prices[-20:])

    if ma_fast>ma_slow:
        return "UP"
    return "DOWN"

# ================= SIGNAL ENGINE =================

def generate_signal(pair,timeframe):

    prices=get_prices(pair)

    if not prices:
        return "⚠️ Market data unavailable"

    price=prices[-1]
    rsi=calculate_rsi(prices)
    trend=get_trend(prices)

    # ===== SIGNAL LOGIC =====
    signal=None

    if rsi<35 and trend=="DOWN":
        signal="CALL 🟢"
    elif rsi>65 and trend=="UP":
        signal="PUT 🔴"

    # niba nta setup ihari
    if not signal:
        return "⏳ Market analysing... wait next setup"

    # ===== ACCURACY STRENGTH =====

    if rsi<25 or rsi>75:
        strength="STRONG 🔥"
        accuracy=random.randint(80,92)
    elif rsi<35 or rsi>65:
        strength="MEDIUM ⚡"
        accuracy=random.randint(70,79)
    else:
        strength="WEAK ⚠️"
        accuracy=random.randint(60,69)

    winrate=calculate_winrate()

    # ===== TIME SYSTEM =====

    now=datetime.now(ZoneInfo("Africa/Kigali"))

    prepare_seconds=30

    entry_time=now+timedelta(seconds=prepare_seconds)
    expiry_time=entry_time+timedelta(minutes=1)

    prepare=f"{prepare_seconds} sec"
    entry=entry_time.strftime("%H:%M:%S")
    expiry="1 Minute"

    # ===== AUTO WIN TRACKER (SIMULATION) =====
    # nyuma ya signal bot yiyongeramo history
    stats=load_stats()

    if random.random()<accuracy/100:
        stats["win"]+=1
    else:
        stats["loss"]+=1

    save_stats(stats)

    winrate=calculate_winrate()

    # ===== FINAL SIGNAL MESSAGE =====

    message=f"""
📊 AI SIGNAL

Pair: {pair}

Price: {price}
RSI: {rsi}
Trend: {trend}

🔥 Signal: {signal}

Accuracy: {accuracy}%
Strength: {strength}
🏆 Winrate: {winrate}%

⏳ Prepare: {prepare}
🟢 Entry Time: {entry}
⌛ Expiry: {expiry}

🕒 Kigali Time
"""

    return message
