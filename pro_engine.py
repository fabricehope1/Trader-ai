import requests
import pandas as pd
from datetime import datetime, timedelta

# ===== REAL FOREX DATA =====
def get_prices(pair):

    symbol_map = {
        "EUR/USDT":"EURUSD",
        "USD/USDT":"USDJPY",
        "ETH/USDT":"EURGBP"
    }

    symbol = symbol_map.get(pair,"EURUSD")

    url=f"https://api.twelvedata.com/time_series?symbol={symbol}&interval=1min&outputsize=60&apikey=demo"

    data=requests.get(url).json()

    closes=[float(x["close"]) for x in data["values"]]

    closes.reverse()

    return closes


# ===== INDICATORS =====
def calculate_rsi(prices,period=14):
    series=pd.Series(prices)
    delta=series.diff()

    gain=delta.clip(lower=0)
    loss=-delta.clip(upper=0)

    avg_gain=gain.rolling(period).mean()
    avg_loss=loss.rolling(period).mean()

    rs=avg_gain/avg_loss
    rsi=100-(100/(1+rs))

    return rsi.iloc[-1]


def ema(prices,period):
    return pd.Series(prices).ewm(span=period).mean().iloc[-1]


# ===== PRO SIGNAL =====
def get_pro_signal(pair,timeframe):

    prices=get_prices(pair)

    rsi=calculate_rsi(prices)

    ema_fast=ema(prices,9)
    ema_slow=ema(prices,21)

    last=prices[-1]

    # ===== DECISION ENGINE =====
    if rsi<40 and ema_fast>ema_slow and last>ema_fast:
        signal="UP 📈"

    elif rsi>60 and ema_fast<ema_slow and last<ema_fast:
        signal="DOWN 📉"

    else:
        signal="UP 📈" if ema_fast>ema_slow else "DOWN 📉"

    now=datetime.now()

    entry=now+timedelta(minutes=int(timeframe))

    confidence=round(abs(ema_fast-ema_slow)*10000,2)

    return signal,rsi,entry.strftime("%H:%M"),confidence
