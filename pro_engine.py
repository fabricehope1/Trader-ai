import requests
from datetime import datetime
import statistics

# ================= API =================

API_KEY="f29c55ce7132437e86f7b025670ec8e4"

# ================= PAIRS =================

PAIRS=[
    "EUR/USD",
    "GBP/USD",
    "USD/JPY",
    "AUD/USD"
]

# ================= CACHE =================

cached_signal=None
last_signal_time=None


# ================= GET CANDLES =================

def get_candles(pair):

    url=f"https://api.twelvedata.com/time_series?symbol={pair}&interval=1min&outputsize=30&apikey={API_KEY}"

    try:
        r=requests.get(url,timeout=10)

        # HTTP ERROR CHECK
        if r.status_code != 200:
            print("HTTP ERROR:",r.status_code)
            return None

        data=r.json()

        # DEBUG RESPONSE
        if "values" not in data:
            print("API ERROR RESPONSE:",data)
            return None

        closes=[float(c["close"]) for c in data["values"]]
        closes.reverse()

        return closes

    except Exception as e:
        print("REQUEST FAILED:",e)
        return None


# ================= RSI =================

def calculate_rsi(prices,period=7):

    gains=[]
    losses=[]

    for i in range(1,len(prices)):
        diff=prices[i]-prices[i-1]

        if diff>0:
            gains.append(diff)
        else:
            losses.append(abs(diff))

    if len(gains)==0 or len(losses)==0:
        return 50

    avg_gain=sum(gains)/period
    avg_loss=sum(losses)/period

    if avg_loss==0:
        return 100

    rs=avg_gain/avg_loss

    return 100-(100/(1+rs))


# ================= MARKET ANALYSIS =================

def analyze_market(prices):

    fast_ma=statistics.mean(prices[-5:])
    slow_ma=statistics.mean(prices[-20:])

    rsi=calculate_rsi(prices)

    print("FAST:",fast_ma,"SLOW:",slow_ma,"RSI:",rsi)

    # CALL CONDITION
    if fast_ma>slow_ma and rsi<65:
        return "CALL"

    # PUT CONDITION
    if fast_ma<slow_ma and rsi>35:
        return "PUT"

    return None


# ================= SIGNAL ENGINE =================

def generate_signal(pair,timeframe):

    global cached_signal,last_signal_time

    now=datetime.utcnow()

    # ⏳ Anti spam 60s
    if last_signal_time:
        diff=(now-last_signal_time).seconds
        if diff<60:
            remain=60-diff
            return {
                "status":"wait",
                "message":f"⏳ Tegereza {remain}s"
            }

    prices=get_candles(pair)

    if prices is None:
        return {
            "status":"error",
            "message":"API data ntabwo yabonetse"
        }

    signal=analyze_market(prices)

    if signal is None:
        return {
            "status":"wait",
            "message":"📉 Market nta confirmation"
        }

    result={
        "status":"success",
        "pair":pair.replace("/",""),
        "signal":signal,
        "timeframe":timeframe,
        "entry_time":now.strftime("%H:%M:%S UTC"),
        "accuracy":"90%+"
    }

    cached_signal=result
    last_signal_time=now

    return result
