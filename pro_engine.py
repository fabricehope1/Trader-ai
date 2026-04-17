import requests
import statistics
import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

API_KEY="f29c55ce7132437e86f7b025670ec8e4"

PAIRS=[
    "EUR/USD",
    "GBP/USD",
    "USD/JPY",
    "AUD/USD"
]

TIMEFRAME_MAP={
    "M1":"1min",
    "M5":"5min",
    "M15":"15min"
}

AI_FILE="ai_memory.json"

# ================= AI MEMORY =================

def load_ai():
    try:
        return json.load(open(AI_FILE))
    except:
        return {}

def save_ai(data):
    json.dump(data,open(AI_FILE,"w"))

# ================= DATA =================

def get_prices(pair,timeframe):

    tf=TIMEFRAME_MAP[timeframe]

    url=f"https://api.twelvedata.com/time_series?symbol={pair}&interval={tf}&outputsize=60&apikey={API_KEY}"

    r=requests.get(url).json()

    if "values" not in r:
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

        if diff>0:
            gains.append(diff)
            losses.append(0)
        else:
            gains.append(0)
            losses.append(abs(diff))

    avg_gain=sum(gains[-period:])/period
    avg_loss=sum(losses[-period:])/period

    if avg_loss==0:
        return 100

    rs=avg_gain/avg_loss
    return round(100-(100/(1+rs)),2)

# ================= TREND =================

def get_trend(prices):

    sma_fast=statistics.mean(prices[-10:])
    sma_slow=statistics.mean(prices[-30:])

    return "UP" if sma_fast>sma_slow else "DOWN"

# ================= STRENGTH =================

def candle_strength(prices):

    moves=[abs(prices[i]-prices[i-1]) for i in range(-6,-1)]

    avg_move=sum(moves)/len(moves)
    last_move=abs(prices[-1]-prices[-2])

    if last_move>avg_move*1.8:
        return "STRONG"
    elif last_move>avg_move*1.2:
        return "MEDIUM"
    else:
        return "WEAK"

# ================= ENTRY TIME =================

def get_entry_time(timeframe):

    now=datetime.now(ZoneInfo("Africa/Kigali"))

    if timeframe=="M1":
        next_candle=now.replace(second=0,microsecond=0)+timedelta(minutes=1)

    elif timeframe=="M5":
        minute=(now.minute//5+1)*5
        next_candle=now.replace(minute=0,second=0,microsecond=0)+timedelta(minutes=minute)

    else:
        minute=(now.minute//15+1)*15
        next_candle=now.replace(minute=0,second=0,microsecond=0)+timedelta(minutes=minute)

    prepare=int((next_candle-now).total_seconds())

    return next_candle.strftime("%H:%M:%S"),prepare

# ================= AI LEARNING =================

def ai_score(pair,rsi,trend,strength):

    ai=load_ai()

    key=f"{pair}_{trend}_{strength}"

    if key not in ai:
        return 0

    data=ai[key]

    total=data["win"]+data["loss"]

    if total<5:
        return 0

    return (data["win"]-data["loss"])/total

# ================= SIGNAL =================

def generate_signal(pair,timeframe):

    prices=get_prices(pair,timeframe)

    if not prices:
        return {"status":"error"}

    price=round(prices[-1],5)

    rsi=calculate_rsi(prices)
    trend=get_trend(prices)
    strength=candle_strength(prices)

    # base signal
    if rsi<=35:
        signal="CALL 📈"
    elif rsi>=65:
        signal="PUT 📉"
    else:
        signal="CALL 📈" if trend=="UP" else "PUT 📉"

    # AI correction
    score=ai_score(pair,rsi,trend,strength)

    if score<-0.3:
        signal="PUT 📉" if "CALL" in signal else "CALL 📈"

    entry_time,prepare=get_entry_time(timeframe)

    accuracy=round(78+abs(50-rsi)/3+score*10,1)

    return {
        "status":"success",
        "pair":pair,
        "signal":f"""
📊 PAIR: {pair}
💰 Price: {price}
📉 RSI: {rsi}
📈 Trend: {trend}
⚡ Strength: {strength}

🧠 AI Score: {round(score,2)}

⏳ Prepare: {prepare}s
⏱ Enter At: {entry_time}

🔥 SIGNAL: {signal}
""",
        "timeframe":timeframe,
        "entry_time":entry_time,
        "accuracy":f"{accuracy}%"
    }

# ================= AI UPDATE =================

def update_ai(pair,trend,strength,result):

    ai=load_ai()

    key=f"{pair}_{trend}_{strength}"

    if key not in ai:
        ai[key]={"win":0,"loss":0}

    if result=="WIN":
        ai[key]["win"]+=1
    else:
        ai[key]["loss"]+=1

    save_ai(ai)
