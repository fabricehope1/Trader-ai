import requests
import statistics
from datetime import datetime
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

    url=f"https://api.twelvedata.com/time_series?symbol={pair}&interval=1min&outputsize=30&apikey={API_KEY}"

    r=requests.get(url).json()

    if "values" not in r:
        print("API ERROR:",r)
        return None,None

    prices=[float(c["close"]) for c in reversed(r["values"])]
    current_price=prices[-1]

    return prices,current_price


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

    avg_gain=statistics.mean(gains[-period:])
    avg_loss=statistics.mean(losses[-period:])

    if avg_loss==0:
        return 100

    rs=avg_gain/avg_loss
    rsi=100-(100/(1+rs))

    return round(rsi,2)


# ================= SIMPLE MARKET ANALYSIS =================

def analyze_market(prices):

    rsi=calculate_rsi(prices)

    fast_ma=statistics.mean(prices[-5:])
    slow_ma=statistics.mean(prices[-15:])

    last_move=prices[-1]-prices[-2]

    score=0

    # TREND
    if fast_ma>slow_ma:
        score+=1
    else:
        score-=1

    # MOMENTUM
    if last_move>0:
        score+=1
    else:
        score-=1

    # RSI FILTER
    if rsi<30:
        score+=1
    elif rsi>70:
        score-=1

    # DECISION (ntijya iceceka)
    if score>=0:
        direction="CALL"
        confidence=80
    else:
        direction="PUT"
        confidence=80

    return direction,confidence,rsi


# ================= SIGNAL =================

def generate_signal(pair):

    prices,current_price=get_prices(pair)

    if not prices:
        return None

    direction,confidence,rsi=analyze_market(prices)

    rwanda_time=datetime.now(
        ZoneInfo("Africa/Kigali")
    ).strftime("%H:%M:%S")

    return {
        "pair":pair,
        "direction":direction,
        "confidence":confidence,
        "expiry":"1 MIN",
        "time":rwanda_time,
        "rsi":rsi,
        "price":round(current_price,5)
    }
