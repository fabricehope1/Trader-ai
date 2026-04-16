import requests
import statistics
import json
import os
import threading
import time
from datetime import datetime
from zoneinfo import ZoneInfo

# ================= SETTINGS =================

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

RESULT_FILE="results.json"

# ================= RESULT STORAGE =================

def load_results():
    if not os.path.exists(RESULT_FILE):
        return {"win":0,"loss":0}
    return json.load(open(RESULT_FILE))

def save_results(data):
    json.dump(data,open(RESULT_FILE,"w"))

def accuracy():
    r=load_results()
    total=r["win"]+r["loss"]
    if total==0:
        return "0%"
    return f"{round((r['win']/total)*100,1)}%"

# ================= MARKET DATA =================

def get_prices(pair,timeframe):

    tf=TIMEFRAME_MAP[timeframe]

    url=f"https://api.twelvedata.com/time_series?symbol={pair}&interval={tf}&outputsize=60&apikey={API_KEY}"

    r=requests.get(url).json()

    if "values" not in r:
        print("API ERROR:",r)
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

# ================= AUTO WIN TRACKER =================

def record_result(pair,timeframe,signal,entry_price):

    def check():

        time.sleep(65)  # wait next candle

        prices=get_prices(pair,timeframe)
        if not prices:
            return

        new_price=prices[-1]

        result=load_results()

        win=False

        if signal=="CALL 📈" and new_price>entry_price:
            win=True
        elif signal=="PUT 📉" and new_price<entry_price:
            win=True

        if win:
            result["win"]+=1
        else:
            result["loss"]+=1

        save_results(result)

        print("RESULT UPDATED:",result)

    threading.Thread(target=check).start()

# ================= SIGNAL ENGINE =================

def generate_signal(pair,timeframe):

    try:

        prices=get_prices(pair,timeframe)

        if not prices:
            return {"status":"error"}

        price=round(prices[-1],5)

        rsi=calculate_rsi(prices)
        trend=get_trend(prices)

        # ===== SMART MARKET ANALYSIS =====

        if rsi<35:
            signal="CALL 📈"
        elif rsi>65:
            signal="PUT 📉"
        else:
            return {
                "status":"wait",
                "message":"⏳ Market analysing... wait next setup"
            }

        # ===== ENTRY TIME WITH SECONDS =====

        now=datetime.now(ZoneInfo("Africa/Kigali"))
        entry_time=now.strftime("%H:%M:%S")

        # START AUTO TRACKER
        record_result(pair,timeframe,signal,price)

        return {
            "status":"success",
            "pair":pair,
            "signal":f"""
📊 PAIR: {pair}
💰 Price: {price}
📉 RSI: {rsi}
📈 Trend: {trend}

⏱ Entry Time: {entry_time}

🔥 SIGNAL: {signal}
""",
            "timeframe":timeframe,
            "entry_time":entry_time,
            "accuracy":accuracy()
        }

    except Exception as e:
        print("ENGINE ERROR:",e)
        return {"status":"error"}
