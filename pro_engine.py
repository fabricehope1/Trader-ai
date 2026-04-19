import requests
import statistics
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# ================= SETTINGS =================

API_KEY="f29c55ce7132437e86f7b025670ec8e4"

PAIRS=[
    "EUR/USD",
    "GBP/USD",
    "USD/JPY",
    "AUD/CAD",
    "CAD/JPY",
    "GBP/JPY",
    "AUD/USD"
]

TIMEFRAME_MAP={
    "M1":"1min",
    "M5":"5min",
    "M15":"15min"
}

# ================= GET MARKET DATA =================

def get_prices(pair,timeframe):

    tf=TIMEFRAME_MAP[timeframe]

    url=f"https://api.twelvedata.com/time_series?symbol={pair}&interval={tf}&outputsize=120&apikey={API_KEY}"

    r=requests.get(url).json()

    if "values" not in r:
        print("API ERROR:", r)
        return None

    closes=[float(c["close"]) for c in r["values"]]
    closes.reverse()

    return closes

# ================= RSI =================

def calculate_rsi(prices,period=14):

    gains=[]
    losses=[]

    for i in range(1,len(prices)):
        diff=prices[i]-prices[i-1]
        gains.append(max(diff,0))
        losses.append(abs(min(diff,0)))

    avg_gain=sum(gains[-period:])/period
    avg_loss=sum(losses[-period:])/period

    if avg_loss==0:
        return 100

    rs=avg_gain/avg_loss
    return round(100-(100/(1+rs)),2)

# ================= TREND =================

def get_trend(prices):

    fast=statistics.mean(prices[-10:])
    slow=statistics.mean(prices[-30:])

    if fast>slow:
        return "UP 📈"
    else:
        return "DOWN 📉"

# ================= MARKET STRENGTH =================

def market_strength(prices):

    moves=[abs(prices[i]-prices[i-1]) for i in range(-10,-1)]

    avg=sum(moves)/len(moves)
    last=abs(prices[-1]-prices[-2])

    if last > avg*1.8:
        return "STRONG 🔥"

    elif last > avg*1.2:
        return "MEDIUM ✅"

    else:
        return "WEAK ⚠️"

# ================= MOMENTUM =================

def momentum(prices):

    up=sum(1 for i in range(-6,-1) if prices[i]>prices[i-1])
    down=sum(1 for i in range(-6,-1) if prices[i]<prices[i-1])

    if up>=4:
        return "BUY 🔥"

    if down>=4:
        return "SELL 🔥"

    return "SIDEWAYS ⚠️"

# ================= ENTRY TIME =================

def get_entry_time(timeframe):

    now=datetime.now(ZoneInfo("Africa/Kigali"))

    if timeframe=="M1":
        nxt=now.replace(second=0,microsecond=0)+timedelta(minutes=1)

    elif timeframe=="M5":
        minute=(now.minute//5+1)*5
        nxt=now.replace(minute=0,second=0,microsecond=0)+timedelta(minutes=minute)

    else:
        minute=(now.minute//15+1)*15
        nxt=now.replace(minute=0,second=0,microsecond=0)+timedelta(minutes=minute)

    prepare=int((nxt-now).total_seconds())

    return nxt.strftime("%H:%M:%S"), prepare

# ================= MAIN ENGINE =================

def generate_signal(pair,timeframe):

    try:

        prices=get_prices(pair,timeframe)

        if not prices:
            return {"status":"error"}

        price=round(prices[-1],5)

        rsi=calculate_rsi(prices)
        trend=get_trend(prices)
        strength=market_strength(prices)
        mom=momentum(prices)

        # ================= DIRECTION (USER DECISION) =================

        if rsi < 50:
            direction="CALL 📈"
        else:
            direction="PUT 📉"

        # ================= CONFIDENCE =================

        confidence=round(50 + abs(50-rsi)/1.5)

        # ================= ENTRY =================

        entry_time, prepare = get_entry_time(timeframe)

        # ================= FINAL MESSAGE =================

        message=f"""
📊 AI MARKET ANALYSIS

Pair: {pair}
Price: {price}

📉 RSI: {rsi}
📈 Trend: {trend}
⚡ Momentum: {mom}
🔥 Strength: {strength}

🎯 Confidence: {confidence}%

⏳ Prepare: {prepare}s
⏱ Entry: {entry_time}

📌 Direction: {direction}

⚠️ Final Decision: YOU
"""

        return {
            "status":"success",
            "pair":pair,
            "signal":message,
            "timeframe":timeframe,
            "entry_time":entry_time,
            "accuracy":f"{confidence}%"
        }

    except Exception as e:
        print("ENGINE ERROR:", e)
        return {"status":"error"}
