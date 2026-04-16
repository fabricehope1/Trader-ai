import requests
import statistics
from datetime import datetime
from zoneinfo import ZoneInfo

API_KEY="f29c55ce7132437e86f7b025670ec8e4"

# ===== CORRECT PAIRS =====
PAIRS=[
    "EURUSD",
    "GBPUSD",
    "USDJPY",
    "AUDUSD"
]

# ================= GET MARKET DATA =================

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


# ================= MARKET ANALYSIS =================

def analyze_market(prices):

    rsi=calculate_rsi(prices)

    fast_ma=statistics.mean(prices[-5:])
    slow_ma=statistics.mean(prices[-20:])

    momentum=prices[-1]-prices[-3]

    score=0

    # TREND
    if fast_ma>slow_ma:
        score+=1
    else:
        score-=1

    # MOMENTUM
    if momentum>0:
        score+=1
    else:
        score-=1

    # RSI CONFIRMATION
    if rsi<35:
        score+=1
    elif rsi>65:
        score-=1

    # ===== FINAL DECISION =====
    direction="CALL" if score>=0 else "PUT"

    confidence=70+abs(score)*10

    return direction,confidence,rsi


# ================= SIGNAL GENERATOR =================

def generate_signal(pair):

    prices,current_price=get_prices(pair)

    # NEVER SILENT
    if prices is None:
        return {
            "pair":pair,
            "direction":"WAIT",
            "confidence":0,
            "expiry":"--",
            "time":"NO DATA",
            "rsi":0,
            "price":0
        }

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

# ================= TEST RUN =================

if __name__=="__main__":

    print("=== SIGNAL ENGINE STARTED ===")

    for pair in PAIRS:

        signal=generate_signal(pair)

        print(signal)
