import requests
from datetime import datetime
import pytz

API_KEY="f29c55ce7132437e86f7b025670ec8e4"

# ================= PAIRS =================

PAIRS=[
    "EUR/USD",
    "GBP/USD",
    "USD/JPY",
    "AUD/USD",
    "USD/CAD",
    "USD/CHF",
    "EUR/JPY"
]

last_signal_time={}

# ================= GET MARKET DATA =================

def get_market_data(pair):

    url=f"https://api.twelvedata.com/time_series?symbol={pair}&interval=1min&outputsize=60&apikey={API_KEY}"

    r=requests.get(url,timeout=10)
    data=r.json()

    if "values" not in data:
        return None

    closes=[float(c["close"]) for c in data["values"]]

    return closes


# ================= RSI =================

def calculate_rsi(closes,period=14):

    gains=[]
    losses=[]

    for i in range(1,period+1):
        diff=closes[i]-closes[i-1]

        if diff>0:
            gains.append(diff)
        else:
            losses.append(abs(diff))

    avg_gain=sum(gains)/period if gains else 0.0001
    avg_loss=sum(losses)/period if losses else 0.0001

    rs=avg_gain/avg_loss
    rsi=100-(100/(1+rs))

    return rsi


# ================= SIGNAL =================

def generate_signal(pair,timeframe="1m"):

    now=datetime.now(pytz.timezone("Africa/Kigali"))
    key=f"{pair}_{timeframe}"

    # 1 signal per minute
    if key in last_signal_time:
        diff=(now-last_signal_time[key]).seconds
        if diff<60:
            return {
                "status":"wait",
                "message":"⏳ Tegereza next candle..."
            }

    closes=get_market_data(pair)

    if closes is None:
        return {"status":"error","message":"API error"}

    rsi=calculate_rsi(closes)

    price=closes[0]

    # ===== SIGNAL LOGIC =====

    if rsi<30:
        signal="CALL"
        strength="🔥 STRONG BUY"

    elif rsi>70:
        signal="PUT"
        strength="🔥 STRONG SELL"

    elif 45<rsi<55:
        return {
            "status":"wait",
            "message":"📊 Market iracyari hagati"
        }
    else:
        signal="CALL" if rsi<50 else "PUT"
        strength="⚡ NORMAL"

    last_signal_time[key]=now

    return {
        "status":"success",
        "pair":pair,
        "signal":signal,
        "strength":strength,
        "rsi":round(rsi,2),
        "price":price,
        "time":now.strftime("%H:%M:%S")
    }
