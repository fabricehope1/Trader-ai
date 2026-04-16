import requests
import time
from datetime import datetime
import pytz

# ================= API =================

API_KEY="f29c55ce7132437e86f7b025670ec8e4"

PAIRS=[
    "EUR/USD",
    "GBP/USD",
    "USD/JPY",
    "AUD/USD",
    "GBP/CAD"
]

LAST_SIGNAL_TIME=0


# ================= MARKET DATA =================

def get_market(pair):

    url=f"https://api.twelvedata.com/time_series?symbol={pair}&interval=1min&outputsize=50&apikey={API_KEY}"

    r=requests.get(url).json()

    if r.get("status")!="ok":
        print("API ERROR:",r)
        return None

    closes=[float(x["close"]) for x in r["values"]]

    return closes


# ================= RSI =================

def calculate_rsi(prices,period=14):

    gains=[]
    losses=[]

    for i in range(1,len(prices)):
        diff=prices[i-1]-prices[i]

        if diff>0:
            gains.append(diff)
        else:
            losses.append(abs(diff))

    avg_gain=sum(gains[-period:])/period
    avg_loss=sum(losses[-period:])/period

    if avg_loss==0:
        return 100

    rs=avg_gain/avg_loss
    rsi=100-(100/(1+rs))

    return round(rsi,2)


# ================= SIGNAL ANALYSIS =================

def analyze(pair):

    prices=get_market(pair)

    if prices is None:
        return "❌ Market Error"

    price_now=prices[0]
    price_prev=prices[1]

    rsi=calculate_rsi(prices)

    # direction
    if rsi<30 and price_now>price_prev:
        direction="CALL 📈"
        strength="🔥 STRONG"
    elif rsi>70 and price_now<price_prev:
        direction="PUT 📉"
        strength="🔥 STRONG"
    elif price_now>price_prev:
        direction="CALL 📈"
        strength="⚠️ WEAK"
    else:
        direction="PUT 📉"
        strength="⚠️ WEAK"

    # Rwanda Time
    rw_tz=pytz.timezone("Africa/Kigali")
    now=datetime.now(rw_tz).strftime("%H:%M:%S")

    signal=f"""
🚨 ULTRA VIP SIGNAL

PAIR: {pair}
PRICE: {price_now}
RSI: {rsi}

DIRECTION: {direction}
POWER: {strength}

TIME RWANDA: {now}
EXPIRY: 1 MIN
"""

    return signal


# ================= AUTO ENGINE =================

def generate_signal():

    global LAST_SIGNAL_TIME

    current=time.time()

    # signal rimwe mumunota
    if current-LAST_SIGNAL_TIME<60:
        wait=int(60-(current-LAST_SIGNAL_TIME))
        return f"⏳ Tegereza {wait}s mbere ya signal ikurikira"

    pair=PAIRS[int(current)%len(PAIRS)]

    signal=analyze(pair)

    LAST_SIGNAL_TIME=current

    return signal


# ================= TEST RUN =================

if __name__=="__main__":

    while True:

        print(generate_signal())

        time.sleep(10)
