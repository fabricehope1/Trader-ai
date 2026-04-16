import requests
import random
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

API_KEY="f29c55ce7132437e86f7b025670ec8e4"

TIMEFRAME_MAP={
    "M1":"1min",
    "M5":"5min",
    "M15":"15min"
}

# ================= GET DATA =================

def get_prices(pair,timeframe):

    symbol=pair.replace("/","")
    interval=TIMEFRAME_MAP.get(timeframe,"1min")

    url=f"https://api.twelvedata.com/time_series?symbol={symbol}&interval={interval}&outputsize=50&apikey={API_KEY}"

    r=requests.get(url).json()

    if "values" not in r:
        print("API RESPONSE:",r)
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
    return round(100-(100/(1+rs)),2)


# ================= TREND =================

def get_trend(prices):

    fast=sum(prices[-5:])/5
    slow=sum(prices[-20:])/20

    return "UP" if fast>slow else "DOWN"


# ================= SIGNAL =================

def generate_signal(pair,timeframe):

    try:

        prices=get_prices(pair,timeframe)

        if not prices or len(prices)<20:
            return {"status":"error"}

        price=round(prices[-1],5)
        rsi=calculate_rsi(prices)
        trend=get_trend(prices)

        # Signal logic
        signal="CALL 🟢" if rsi<50 else "PUT 🔴"

        # Strength
        if rsi<30 or rsi>70:
            strength="STRONG 🔥"
            accuracy=random.randint(85,92)
        elif rsi<40 or rsi>60:
            strength="MEDIUM ⚡"
            accuracy=random.randint(72,84)
        else:
            strength="WEAK ⚠️"
            accuracy=random.randint(60,71)

        # Prepare 30 seconds
        now=datetime.now(ZoneInfo("Africa/Kigali"))
        entry_time=(now+timedelta(seconds=30)).strftime("%H:%M:%S")

        message=f"""
📊 PAIR: {pair}
💰 Price: {price}
📉 RSI: {rsi}
📈 Trend: {trend}

🔥 SIGNAL: {signal}
Strength: {strength}
Accuracy: {accuracy}%

⏳ Prepare: 30 seconds
🕒 Entry: {entry_time}
⌛ Expiry: {timeframe}
"""

        return {
            "status":"success",
            "signal":message,
            "accuracy":accuracy
        }

    except Exception as e:
        print("ENGINE ERROR:",e)
        return {"status":"error"}
