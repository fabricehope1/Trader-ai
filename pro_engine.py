import requests
from datetime import datetime,timedelta
import statistics

API_KEY="f29c55ce7132437e86f7b025670ec8e4"

PAIRS=[
"EURUSD","GBPUSD","USDJPY",
"AUDUSD","USDCAD","USDCHF","EURJPY"
]

last_analysis={}

# ================= RWANDA TIME =================

def rwanda_time():
    return (datetime.utcnow()+timedelta(hours=2)).strftime("%H:%M:%S")

# ================= GET DATA =================

def get_candles(pair):

    try:
        url=f"https://api.twelvedata.com/time_series?symbol={pair}&interval=1min&outputsize=60&apikey={API_KEY}"
        data=requests.get(url,timeout=10).json()

        closes=[float(x["close"]) for x in data["values"]]
        closes.reverse()

        return closes

    except:
        return None

# ================= RSI =================

def rsi_calc(closes,period=14):

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

    avg_gain=statistics.mean(gains[-period:])
    avg_loss=statistics.mean(losses[-period:])

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

# ================= ANALYSIS ENGINE =================

def generate_signal(pair,timeframe):

    now=datetime.utcnow()
    key=f"{pair}_{timeframe}"

    # ===== Anti Spam 1 minute =====
    if key in last_analysis:
        if (now-last_analysis[key]).seconds<60:
            return {
                "status":"wait",
                "message":"⏳ Market iracyategurwa..."
            }

    closes=get_candles(pair)

    if not closes:
        return {"status":"error"}

    price=closes[-1]
    rsi=rsi_calc(closes)
    tr=trend(closes)

    if rsi is None:
        return {"status":"wait","message":"Loading market..."}

    signal=None
    strength="WEAK"

    # ===== SMART ENTRY LOGIC =====
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
        return {"status":"wait","message":"No clean setup"}

    last_analysis[key]=now

    # ===== PREPARATION TIME =====
    entry_time=(datetime.utcnow()+timedelta(seconds=30))

    return {
        "status":"prepare",
        "pair":pair,
        "direction":signal,
        "strength":strength,
        "price":price,
        "rsi":rsi,
        "analysis_time":rwanda_time(),
        "entry_at":(entry_time+timedelta(hours=2)).strftime("%H:%M:%S"),
        "message":"⚡ Market Ready — Tegereza entry time"
    }
