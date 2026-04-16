import requests
from datetime import datetime, timedelta

# ================= PAIRS =================

PAIRS = {
    "EURUSD": "EURUSDT",
    "GBPUSD": "GBPUSDT",
    "USDJPY": "JPYUSDT",
    "AUDUSD": "AUDUSDT"
}

# ================= GET REAL CANDLES =================

def get_candles(symbol, interval="1m", limit=100):

    url=f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"

    data=requests.get(url,timeout=10).json()

    closes=[float(candle[4]) for candle in data]

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
    return 100-(100/(1+rs))


# ================= EMA =================

def ema(prices,period):
    k=2/(period+1)
    value=prices[0]

    for price in prices:
        value=price*k+value*(1-k)

    return value


# ================= MACD =================

def macd(prices):
    return ema(prices,12)-ema(prices,26)


# ================= ANALYSIS =================

def analyze_market(prices):

    rsi=calculate_rsi(prices)

    ema_fast=ema(prices,9)
    ema_slow=ema(prices,21)

    macd_val=macd(prices)

    call=0
    put=0

    if rsi<35:
        call+=1
    elif rsi>65:
        put+=1

    if ema_fast>ema_slow:
        call+=1
    else:
        put+=1

    if macd_val>0:
        call+=1
    else:
        put+=1

    signal="CALL" if call>=put else "PUT"

    return signal,rsi


# ================= SIGNAL =================

def generate_signal(pair,timeframe):

    symbol=PAIRS.get(pair)

    if not symbol:
        return {"status":"error"}

    prices=get_candles(symbol,"1m")

    signal,rsi=analyze_market(prices)

    entry_time=(datetime.utcnow()+timedelta(hours=2)).strftime("%H:%M:%S GMT+2")

    accuracy="REAL DATA"

    return {
        "status":"success",
        "pair":pair,
        "signal":signal,
        "timeframe":timeframe,
        "entry_time":entry_time,
        "accuracy":accuracy
    }
