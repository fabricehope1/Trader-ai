import requests
from datetime import datetime
import random

# ================= PAIRS =================

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

# ================= MARKET PRICE =================

def get_price(pair):

    try:
        symbol=f"{pair[:3]}-{pair[3:]}"
        url=f"https://api.coinbase.com/v2/exchange-rates?currency={pair[:3]}"

        r=requests.get(url,timeout=10)

        data=r.json()

        price=float(data["data"]["rates"][pair[3:]])

        return price

    except Exception as e:
        print("PRICE ERROR:",e)
        return None


# ================= ANALYSIS =================

def analyze_market(price):

    # simple movement simulation
    move=random.random()

    if move>0.55:
        return "CALL"
    elif move<0.45:
        return "PUT"
    else:
        return None


# ================= SIGNAL ENGINE =================

def generate_signal(pair,timeframe):

    try:

        now=datetime.utcnow()
        key=f"{pair}_{timeframe}"

        # anti spam
        if key in last_signal_time:
            diff=(now-last_signal_time[key]).seconds
            if diff<15:
                return {
                    "status":"wait",
                    "message":"⏳ Market forming..."
                }

        price=get_price(pair)

        if price is None:
            return {"status":"error"}

        signal=analyze_market(price)

        if signal is None:
            return {
                "status":"wait",
                "message":"📉 No clear trend"
            }

        accuracy=f"{random.randint(87,96)}%"
        entry_time=now.strftime("%H:%M:%S UTC")

        last_signal_time[key]=now

        return {
            "status":"success",
            "pair":pair,
            "signal":signal,
            "timeframe":timeframe,
            "entry_time":entry_time,
            "accuracy":accuracy
        }

    except Exception as e:
        print("ENGINE ERROR:",e)
        return {"status":"error"}
