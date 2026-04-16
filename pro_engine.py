import requests
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# ================= API =================

API_KEY="f29c55ce7132437e86f7b025670ec8e4"

# ================= PAIRS =================

PAIRS=[
    "EUR/USD",
    "GBP/USD",
    "USD/JPY",
    "AUD/USD"
]

# ================= TIME =================

def rwanda_time():
    return datetime.now(ZoneInfo("Africa/Kigali"))

# ================= GET PRICE =================

def get_price(pair):

    symbol=pair.replace("/","")

    url=f"https://api.twelvedata.com/price?symbol={symbol}&apikey={API_KEY}"

    try:
        r=requests.get(url).json()

        if "price" in r:
            return float(r["price"])

    except:
        pass

    return None

# ================= GET CANDLES =================

def get_candles(pair,interval="1min"):

    symbol=pair.replace("/","")

    url=f"https://api.twelvedata.com/time_series?symbol={symbol}&interval={interval}&outputsize=50&apikey={API_KEY}"

    try:
        data=requests.get(url).json()

        if "values" not in data:
            return []

        closes=[float(c["close"]) for c in data["values"]]

        closes.reverse()

        return closes

    except:
        return []

# ================= RSI =================

def calculate_rsi(closes,period=14):

    if len(closes)<period+1:
        return 50

    gains=[]
    losses=[]

    for i in range(1,len(closes)):
        diff=closes[i]-closes[i-1]

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

def trend(closes):

    if len(closes)<20:
        return "WAIT"

    sma_fast=sum(closes[-5:])/5
    sma_slow=sum(closes[-20:])/20

    if sma_fast>sma_slow:
        return "UP"

    if sma_fast<sma_slow:
        return "DOWN"

    return "SIDE"

# ================= NEXT ENTRY TIME =================

def next_entry(tf_minutes):

    now=rwanda_time()

    minute=(now.minute//tf_minutes+1)*tf_minutes

    if minute>=60:
        entry=now.replace(minute=0,second=0,microsecond=0)+timedelta(hours=1)
    else:
        entry=now.replace(minute=minute,second=0,microsecond=0)

    return entry.strftime("%H:%M")

# ================= SIGNAL ENGINE =================

def generate_signal(pair):

    closes=get_candles(pair,"1min")

    if not closes:
        return None

    price=get_price(pair)

    rsi=calculate_rsi(closes)

    market_trend=trend(closes)

    signal=None

    if rsi<30 and market_trend=="UP":
        signal="CALL 📈"

    elif rsi>70 and market_trend=="DOWN":
        signal="PUT 📉"

    else:
        signal="WAIT ⏳"

    entry_time=next_entry(1)

    analysis=f"""
📊 PAIR: {pair}

💰 Price: {price}

📉 RSI: {rsi}
📈 Trend: {market_trend}

⏱ Next Entry: {entry_time}

🔥 Signal: {signal}
"""

    return analysis
