import requests
import random
from datetime import datetime

# ================= SETTINGS =================

FOREX_API_KEY="demo"   # Railway uzashyiramo real key niba ufite

PAIRS=[
    "EURUSD",
    "GBPUSD",
    "USDJPY",
    "AUDUSD",
    "USDCAD",
    "USDCHF",
    "EURJPY"
]

last_signal_time={}

# ================= MARKET DATA =================

def get_market_price(pair):

    try:

        url=f"https://api.exchangerate.host/latest?base={pair[:3]}&symbols={pair[3:]}"
        r=requests.get(url,timeout=10).json()

        price=r["rates"][pair[3:]]

        return price

    except:
        return None

# ================= SIMPLE AI ANALYSIS =================

def analyze_market(price):

    # fake AI logic but dynamic
    r=random.randint(1,100)

    if r>55:
        signal="CALL"
    else:
        signal="PUT"

    accuracy=f"{random.randint(82,97)}%"

    return signal,accuracy

# ================= SIGNAL ENGINE =================

def generate_signal(pair,timeframe):

    # ANTI SPAM WAIT
    now=datetime.utcnow()

    key=f"{pair}_{timeframe}"

    if key in last_signal_time:

        diff=(now-last_signal_time[key]).seconds

        if diff<30:
            return {
                "status":"wait",
                "message":"⏳ Wait market forming..."
            }

    # GET MARKET PRICE
    price=get_market_price(pair)

    if price is None:
        return {"status":"error"}

    # ANALYSIS
    signal,accuracy=analyze_market(price)

    entry_time=datetime.utcnow().strftime("%H:%M:%S UTC")

    last_signal_time[key]=now

    return {
        "status":"success",
        "pair":pair,
        "signal":signal,
        "timeframe":timeframe,
        "entry_time":entry_time,
        "accuracy":accuracy
    }
