# pro_engine.py

from bit import generate_signal as engine_signal, PAIRS
import requests
import json
import os
import threading
import time
from datetime import datetime
from zoneinfo import ZoneInfo

API_KEY="f29c55ce7132437e86f7b025670ec8e4"

STATS_FILE="accuracy.json"


# ================= LOAD/SAVE STATS =================

def load_stats():

    if not os.path.exists(STATS_FILE):
        return {"wins":0,"losses":0}

    with open(STATS_FILE,"r") as f:
        return json.load(f)


def save_stats(stats):

    with open(STATS_FILE,"w") as f:
        json.dump(stats,f)


def record_result(result):

    stats=load_stats()

    if result=="WIN":
        stats["wins"]+=1
    else:
        stats["losses"]+=1

    save_stats(stats)


def get_accuracy():

    stats=load_stats()
    total=stats["wins"]+stats["losses"]

    if total==0:
        return "0%"

    acc=round((stats["wins"]/total)*100,2)
    return f"{acc}%"


# ================= GET CURRENT PRICE =================

def get_current_price(pair):

    symbol=pair.replace("/","")

    url=f"https://api.twelvedata.com/price?symbol={symbol}&apikey={API_KEY}"

    r=requests.get(url).json()

    if "price" not in r:
        return None

    return float(r["price"])


# ================= AUTO RESULT CHECK =================

def auto_check(pair,signal,entry_price):

    # wait 60 sec candle close
    time.sleep(60)

    exit_price=get_current_price(pair)

    if not exit_price:
        return

    if "CALL" in signal:
        result="WIN" if exit_price>entry_price else "LOSS"
    else:
        result="WIN" if exit_price<entry_price else "LOSS"

    record_result(result)

    print(f"AUTO RESULT → {pair} {result}")


# ================= MAIN SIGNAL =================

def generate_signal(pair):

    data=engine_signal(pair)

    if data["status"]!="success":
        return data

    entry_price=float(data["signal"].split("Price: ")[1].split("\n")[0])

    # start background win checker
    threading.Thread(
        target=auto_check,
        args=(pair,data["signal"],entry_price),
        daemon=True
    ).start()

    accuracy=get_accuracy()

    data["signal"]+=f"""

🤖 Auto Result Tracking ON
📊 REAL ACCURACY: {accuracy}
"""

    return data
