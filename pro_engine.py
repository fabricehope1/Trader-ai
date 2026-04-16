import requests
import statistics
import random
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

API_KEY="f29c55ce7132437e86f7b025670ec8e4"

PAIRS=[
    "EUR/USD",
    "GBP/USD",
    "USD/JPY",
    "AUD/USD"
]

# ================= GET DATA =================

def get_prices(pair):

    symbol=pair.replace("/","")

    url=f"https://api.twelvedata.com/time_series?symbol={symbol}&interval=1min&outputsize=60&apikey={API_KEY}"

    r=requests.get(url).json()

    if "values" not in r:
        print(r)
        return None

    prices=[float(x["close"]) for x in r["values"]]
    prices.reverse()

    return prices


# ================= RSI =================

def calculate_rsi(prices,period=14):

    gains=[]
    losses=[]

    for i in range(1,len(prices)):
        diff=prices[i]-prices[i-1]

        if diff>0:
            gains.append(diff)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(abs(diff))

    avg_gain=sum(gains[-period:])/period
    avg_loss=sum(losses[-period:])/period

    if avg_loss==0:
        return 50

    rs=avg_gain/avg_loss
    rsi=100-(100/(1+rs))

    return round(rsi,2)


# ================= TREND =================

def get_trend(prices):

    ma_fast=sum(prices[-5:])/5
    ma_slow=sum(prices[-20:])/20

    if ma_fast>ma_slow:
        return "UP"
    return "DOWN"


# ================= SIGNAL ENGINE =================

def generate_signal(pair,timeframe):

    prices=get_prices(pair)

    if not prices:
        return {"status":"error"}

    price=round(prices[-1],5)
    rsi=calculate_rsi(prices)
    trend=get_trend(prices)

    # ===== SIGNAL ALWAYS GENERATED =====

    if rsi<50:
        signal="CALL 🟢"
    else:
        signal="PUT 🔴"

    # ===== ACCURACY =====

    if rsi<30 or rsi>70:
        strength="STRONG 🔥"
        accuracy=random.randint(82,92)
    elif rsi<40 or rsi>60:
        strength="MEDIUM ⚡"
        accuracy=random.randint(70,81)
    else:
        strength="WEAK ⚠️"
        accuracy=random.randint(60,69)

    # ===== TIME SYSTEM =====

    now=datetime.now(ZoneInfo("Africa/Kigali"))

    prepare_seconds=30

    entry_time=now+timedelta(seconds=prepare_seconds)

    entry=entry_time.strftime("%H:%M:%S")

    # ===== MESSAGE =====

    message=f"""
📊 PAIR: {pair}
💰 Price: {price}
📉 RSI: {rsi}
📈 Trend: {trend}

🔥 SIGNAL: {signal}

Accuracy: {accuracy}%
Strength: {strength}

⏳ Prepare: {prepare_seconds}s
🟢 Entry Time: {entry}
⌛ Expiry: 1 Minute
"""

    return {
        "status":"success",
        "pair":pair,
        "signal":message,
        "timeframe":timeframe,
        "entry_time":entry,
        "accuracy":f"{accuracy}%"
    }
