import requests
import statistics
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

API_KEY="f29c55ce7132437e86f7b025670ec8e4"

# ================= PAIRS =================

PAIRS=[
    "EUR/USD",
    "GBP/USD",
    "USD/JPY",
    "AUD/USD"
]

# ================= GET DATA =================

def get_prices(pair):

    url=f"https://api.twelvedata.com/time_series?symbol={pair}&interval=1min&outputsize=50&apikey={API_KEY}"

    try:
        r=requests.get(url,timeout=10).json()

        if "values" not in r:
            print("API ERROR:",r)
            return None,None

        prices=[float(c["close"]) for c in reversed(r["values"])]

        if len(prices)<20:
            return None,None

        return prices,prices[-1]

    except Exception as e:
        print("REQUEST ERROR:",e)
        return None,None


# ================= RSI =================

def calculate_rsi(prices,period=14):

    gains=[]
    losses=[]

    for i in range(1,len(prices)):
        diff=prices[i]-prices[i-1]

        gains.append(max(diff,0))
        losses.append(abs(min(diff,0)))

    avg_gain=statistics.mean(gains[-period:])
    avg_loss=statistics.mean(losses[-period:])

    if avg_loss==0:
        return 100

    rs=avg_gain/avg_loss
    return round(100-(100/(1+rs)),2)


# ================= ANALYSIS =================

def analyze_market(prices):

    rsi=calculate_rsi(prices)

    fast_ma=statistics.mean(prices[-5:])
    slow_ma=statistics.mean(prices[-20:])

    momentum=prices[-1]-prices[-3]

    score=0

    if fast_ma>slow_ma:
        score+=1
    else:
        score-=1

    if momentum>0:
        score+=1
    else:
        score-=1

    if rsi<35:
        score+=1
    elif rsi>65:
        score-=1

    direction="CALL" if score>=0 else "PUT"
    confidence=70+abs(score)*10

    return direction,confidence,rsi


# ================= ENTRY TIME =================

def next_entry(timeframe):

    now=datetime.now(ZoneInfo("Africa/Kigali"))

    if timeframe=="M1":
        entry=now+timedelta(minutes=1)
    elif timeframe=="M5":
        entry=now+timedelta(minutes=5)
    else:
        entry=now+timedelta(minutes=15)

    return entry.strftime("%H:%M:%S")


# ================= SIGNAL =================

def generate_signal(pair,timeframe):

    prices,current_price=get_prices(pair)

    if prices is None:
        return {
            "status":"wait",
            "message":"⏳ Market data loading..."
        }

    direction,confidence,rsi=analyze_market(prices)

    entry_time=next_entry(timeframe)

    # ✅ FULL MESSAGE CREATED INSIDE ENGINE
    message=f"""
📊 AI SIGNAL

Pair: {pair}
Signal: {direction}
Timeframe: {timeframe}

Price: {round(current_price,5)}
Next Entry: {entry_time}

Accuracy: {confidence}%
"""

    return {
        "status":"success",
        "message":message
    }
