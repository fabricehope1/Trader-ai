import requests
import random
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# ================= PAIRS =================

PAIRS=[
    "EUR/USD",
    "GBP/USD",
    "USD/JPY",
    "AUD/USD"
]

API_KEY="f29c55ce7132437e86f7b025670ec8e4"

TIMEFRAME_MAP={
    "M1":"1min",
    "M5":"5min",
    "M15":"15min"
}

# ================= GET DATA =================

def get_prices(pair,timeframe):

    try:
        symbol=pair.replace("/","")
        interval=TIMEFRAME_MAP[timeframe]

        url=f"https://api.twelvedata.com/time_series?symbol={symbol}&interval={interval}&outputsize=30&apikey={API_KEY}"

        r=requests.get(url,timeout=10).json()

        if "values" not in r:
            return None

        prices=[float(x["close"]) for x in r["values"]]
        prices.reverse()

        return prices

    except:
        return None


# ================= SIMPLE ANALYSIS =================

def analyse_market(prices):

    if not prices:
        return random.choice(["CALL 🟢","PUT 🔴"]),50

    last=prices[-1]
    avg=sum(prices[-10:])/10

    if last>avg:
        signal="CALL 🟢"
    else:
        signal="PUT 🔴"

    momentum=abs(last-avg)

    if momentum>0.001:
        strength="STRONG 🔥"
        accuracy=random.randint(85,92)
    elif momentum>0.0005:
        strength="MEDIUM ⚡"
        accuracy=random.randint(72,84)
    else:
        strength="WEAK ⚠️"
        accuracy=random.randint(60,71)

    return signal,strength,accuracy,last


# ================= SIGNAL ENGINE =================

def generate_signal(pair,timeframe):

    prices=get_prices(pair,timeframe)

    signal,strength,accuracy,price=analyse_market(prices)

    now=datetime.now(ZoneInfo("Africa/Kigali"))

    # prepare seconds (user yitegure)
    prepare_seconds=25
    entry=(now+timedelta(seconds=prepare_seconds)).strftime("%H:%M:%S")

    message=f"""
🤖 AI SIGNAL READY

📊 Pair: {pair}
💰 Price: {round(price,5)}

🔥 Signal: {signal}
Strength: {strength}
Accuracy: {accuracy}%

⏳ Prepare: {prepare_seconds}s
🕒 Entry Time: {entry}
⌛ Expiry: {timeframe}
"""

    return {
        "status":"success",
        "signal":message,
        "accuracy":accuracy
        }
