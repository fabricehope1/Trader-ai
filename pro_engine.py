import requests
from datetime import datetime,timedelta
import statistics

API_KEY="f29c55ce7132437e86f7b025670ec8e4"

PAIRS=[
"EURUSD","GBPUSD","USDJPY",
"AUDUSD","USDCAD","USDCHF","EURJPY"
]

last_signal={}

# ================= RWANDA TIME =================

def rwanda_time():
    return (datetime.utcnow()+timedelta(hours=2)).strftime("%H:%M:%S")

# ================= SAFE API REQUEST =================

def get_candles(pair):

    try:

        url=f"https://api.twelvedata.com/time_series"

        params={
            "symbol":pair,
            "interval":"1min",
            "outputsize":50,
            "apikey":API_KEY
        }

        r=requests.get(url,params=params,timeout=10)
        data=r.json()

        # ===== API ERROR CHECK =====
        if "values" not in data:
            print("API RESPONSE:",data)
            return None

        closes=[float(c["close"]) for c in data["values"]]
        closes.reverse()

        return closes

    except Exception as e:
        print("DATA ERROR:",e)
        return None

# ================= RSI =================

def calc_rsi(closes,period=14):

    gains=[]
    losses=[]

    for i in range(1,len(closes)):
        diff=closes[i]-closes[i-1]

        if diff>0:
            gains.append(diff)
        else:
            losses.append(abs(diff))

    if len(gains)<period:
        return None

    avg_gain=sum(gains[-period:])/period
    avg_loss=sum(losses[-period:])/period

    if avg_loss==0:
        return 100

    rs=avg_gain/avg_loss
    return round(100-(100/(1+rs)),2)

# ================= TREND =================

def trend(closes):

    fast=sum(closes[-5:])/5
    slow=sum(closes[-20:])/20

    if fast>slow:
        return "UP"
    elif fast<slow:
        return "DOWN"
    return "SIDE"

# ================= SIGNAL ENGINE =================

def generate_signal(pair,timeframe):

    try:

        now=datetime.utcnow()
        key=f"{pair}_{timeframe}"

        # ===== ONE SIGNAL PER MINUTE =====
        if key in last_signal:
            diff=(now-last_signal[key]).seconds
            if diff<60:
                return {
                    "status":"wait",
                    "message":"⏳ Tegereza minute 1"
                }

        closes=get_candles(pair)

        if closes is None:
            return {
                "status":"error",
                "message":"Market data unavailable"
            }

        price=closes[-1]
        rsi=calc_rsi(closes)
        tr=trend(closes)

        if rsi is None:
            return {
                "status":"wait",
                "message":"Market loading..."
            }

        signal=None
        strength="WEAK"

        # ===== REAL LOGIC =====
        if rsi<30 and tr=="UP":
            signal="CALL"
            strength="🔥 STRONG"

        elif rsi>70 and tr=="DOWN":
            signal="PUT"
            strength="🔥 STRONG"

        elif rsi<40:
            signal="CALL"

        elif rsi>60:
            signal="PUT"

        if signal is None:
            return {
                "status":"wait",
                "message":"No clean setup"
            }

        last_signal[key]=now

        entry=(datetime.utcnow()+timedelta(seconds=30)+timedelta(hours=2)).strftime("%H:%M:%S")

        return {
            "status":"prepare",
            "pair":pair,
            "direction":signal,
            "strength":strength,
            "rsi":rsi,
            "price":price,
            "entry_time":entry,
            "time":rwanda_time()
        }

    except Exception as e:
        print("ENGINE ERROR:",e)
        return {
            "status":"error",
            "message":"Engine crashed"
        }
