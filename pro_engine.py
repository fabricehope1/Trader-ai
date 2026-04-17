# ================= PRO ENGINE V6 AI =================

import requests
import statistics
import json
import os
from datetime import datetime
from zoneinfo import ZoneInfo

API_KEY="f29c55ce7132437e86f7b025670ec8e4"

PAIRS=[
    "EUR/USD",
    "GBP/USD",
    "USD/JPY",
    "AUD/USD"
]

TIMEFRAME="1min"

AI_FILE="ai_memory.json"


# ================= AI MEMORY =================

def load_ai():
    if not os.path.exists(AI_FILE):
        return {"buy":1,"sell":1}
    return json.load(open(AI_FILE))


def save_ai(data):
    json.dump(data,open(AI_FILE,"w"))


def ai_bias():
    ai=load_ai()
    total=ai["buy"]+ai["sell"]

    buy_ratio=ai["buy"]/total
    sell_ratio=ai["sell"]/total

    return buy_ratio - sell_ratio


def ai_learn(signal,result):

    ai=load_ai()

    if result=="WIN":
        if signal=="BUY":
            ai["buy"]+=1
        else:
            ai["sell"]+=1

    else:
        if signal=="BUY":
            ai["sell"]+=1
        else:
            ai["buy"]+=1

    save_ai(ai)


# ================= GET CANDLES =================

def get_candles(pair):

    symbol=pair.replace("/","")

    url=f"https://api.twelvedata.com/time_series?symbol={symbol}&interval={TIMEFRAME}&outputsize=50&apikey={API_KEY}"

    r=requests.get(url).json()

    if "values" not in r:
        return None

    closes=[float(c["close"]) for c in r["values"]]

    return closes[::-1]


# ================= ANALYSIS =================

def analyze(closes):

    sma_fast=statistics.mean(closes[-5:])
    sma_slow=statistics.mean(closes[-15:])

    momentum=closes[-1]-closes[-5]

    rsi_like=(closes[-1]-min(closes[-14:]))/(max(closes[-14:])-min(closes[-14:]))

    score=0

    if sma_fast>sma_slow:
        score+=1
    else:
        score-=1

    if momentum>0:
        score+=1
    else:
        score-=1

    if rsi_like>0.55:
        score+=1
    elif rsi_like<0.45:
        score-=1

    # ===== AI Bias =====
    score+=ai_bias()

    if score>1:
        signal="BUY"
    elif score<-1:
        signal="SELL"
    else:
        signal="BUY" if score>=0 else "SELL"

    strength="WEAK"

    if abs(score)>=2:
        strength="STRONG"
    elif abs(score)>=1:
        strength="MEDIUM"

    return signal,strength,round(score,2)


# ================= MAIN SIGNAL =================

def generate_signal(pair):

    closes=get_candles(pair)

    if not closes:
        return None

    signal,strength,score=analyze(closes)

    now=datetime.now(ZoneInfo("Africa/Kigali")).strftime("%H:%M:%S")

    return {
        "pair":pair,
        "signal":signal,
        "strength":strength,
        "score":score,
        "time":now
    }
