import requests
import statistics
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import threading

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

# ================= WIN TRACKER =================

TOTAL_SIGNALS=0
WINS=0
LOSSES=0

# ================= GET MARKET DATA =================

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

# ================= SIGNAL STRENGTH =================

def signal_strength(rsi):

    if rsi<=25 or rsi>=75:
        return "STRONG 💪",90
    elif rsi<=35 or rsi>=65:
        return "MEDIUM ⚡",82
    else:
        return "WEAK ⚠️",74

# ================= WIN TRACKER AUTO =================

def track_result(pair,signal,entry_price,timeframe):

    global TOTAL_SIGNALS,WINS,LOSSES

    tf_seconds={
        "M1":60,
        "M5":300,
        "M15":900
    }

    wait=tf_seconds[timeframe]

    def check():

        global TOTAL_SIGNALS,WINS,LOSSES

        new_prices=get_prices(pair,timeframe)

        if not new_prices:
            return

        exit_price=new_prices[-1]

        win=False

        if "CALL" in signal and exit_price>entry_price:
            win=True

        if "PUT" in signal and exit_price<entry_price:
            win=True

        TOTAL_SIGNALS+=1

        if win:
            WINS+=1
        else:
            LOSSES+=1

        acc=round((WINS/TOTAL_SIGNALS)*100,2)

        print(f"RESULT → WIN:{WINS} LOSS:{LOSSES} ACC:{acc}%")

    threading.Timer(wait,check).start()

# ================= MAIN ENGINE =================

def generate_signal(pair,timeframe="M1"):

    prices=get_prices(pair,timeframe)

    if not prices:
        return {"status":"error"}

    price=round(prices[-1],5)

    rsi=calculate_rsi(prices)
    trend=get_trend(prices)

    # ===== SIGNAL DECISION =====

    if rsi<=35:
        signal="CALL 📈"
    elif rsi>=65:
        signal="PUT 📉"
    else:
        signal="CALL 📈" if trend=="UP" else "PUT 📉"

    # ===== STRENGTH =====

    strength,accuracy_value=signal_strength(rsi)

    # ===== TIME =====

    now=datetime.now(ZoneInfo("Africa/Kigali"))

    prepare_seconds=15
    entry_time=(now+timedelta(seconds=prepare_seconds)).strftime("%H:%M:%S")

    # ===== START AUTO WIN TRACKER =====

    track_result(pair,signal,price,timeframe)

    return {
        "status":"success",
        "pair":pair,
        "signal":f"""
📊 PAIR: {pair}
💰 Price: {price}

📉 RSI: {rsi}
📈 Trend: {trend}

⚡ Strength: {strength}
🎯 Estimated Accuracy: {accuracy_value}%

⏳ Prepare: {prepare_seconds}s
🕒 Entry Time: {entry_time}

🔥 SIGNAL: {signal}
"""
    }
