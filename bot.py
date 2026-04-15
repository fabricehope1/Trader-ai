import requests
import time
from telegram import Bot
import pandas as pd

TOKEN = "8236042238:AAEAqBYZKNodL6_Z5zopRRJQ3BWZqRRyOno"
CHAT_ID = "8448217655"

bot = Bot(token=TOKEN)

def get_price():
    url = "https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1m&limit=50"
    data = requests.get(url).json()

    closes = [float(candle[4]) for candle in data]
    return closes

def rsi(prices, period=14):
    series = pd.Series(prices)
    delta = series.diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    return rsi.iloc[-1]

while True:
    prices = get_price()
    rsi_value = rsi(prices)

    if rsi_value < 30:
        signal = "BUY 📈"
    elif rsi_value > 70:
        signal = "SELL 📉"
    else:
        signal = "WAIT ⏳"

    message = f"""
QUOTEX SIGNAL 🔥

PAIR: BTCUSD
TIMEFRAME: 1 MIN
RSI: {round(rsi_value,2)}

SIGNAL: {signal}
"""

    bot.send_message(chat_id=CHAT_ID, text=message)

    time.sleep(60)
