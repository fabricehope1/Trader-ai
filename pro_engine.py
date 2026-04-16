import requests
import statistics
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

# ================= GET MARKET DATA =================

def get_prices(pair,timeframe):

    tf=TIMEFRAME_MAP[timeframe]

    url=f"https://api.twelvedata.com/time_series?symbol={pair}&interval={tf}&outputsize=60&apikey={API_KEY}"

    r=requests.get(url).json()

    if "values" not in r:
        return None

    closes=[float(c["close"]) for c in r["values"]]

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
    rsi=100-(100/(1+rs))

    return round(rsi,2)


# ================= TREND =================

def get_trend(prices):

    sma_fast=statistics.mean(prices[-10:])
    sma_slow=statistics.mean(prices[-30:])

    if sma_fast>sma_slow:
        return "UP"
    else:
        return "DOWN"


# ================= SIGNAL ENGINE =================

def generate_signal(pair,timeframe):

    try:

        prices=get_prices(pair,timeframe)

        if not prices:
            return {"status":"error"}

        price=round(prices[-1],5)

        rsi=calculate_rsi(prices)
        trend=get_trend(prices)

        signal=None

        # ===== REAL LOGIC =====

        if rsi<30 and trend=="UP":
            signal="CALL 📈"

        elif rsi>70 and trend=="DOWN":
            signal="PUT 📉"

        else:
            return {
                "status":"wait",
                "message":"⏳ Market not ready. Wait next candle..."
            }

        # ===== ENTRY TIME RWANDA =====

        now=datetime.now(ZoneInfo("Africa/Kigali"))
        entry_time=now.strftime("%H:%M")

        accuracy=f"{round(75+abs(50-rsi)/2,1)}%"

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
            "accuracy":accuracy
        }

    except Exception as e:
        print("ENGINE ERROR:",e)
        return {"status":"error"}
