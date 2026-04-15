
import os
import requests
import time
import pandas as pd
from telegram import Bot

# ===============================
# GET SECRET VARIABLES
# ===============================
TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

bot = Bot(token=TOKEN)

# ===============================
# GET REAL MARKET DATA
# ===============================
def get_price():
    url = "https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1m&limit=50"
    data = requests.get(url).json()

    closes = [float(candle[4]) for candle in data]
    return closes

# ===============================
# RSI CALCULATION
# ===============================
def calculate_rsi(prices, period=14):
    series = pd.Series(prices)
    delta = series.diff()

    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(period).mean()
    avg_loss = loss.rolling(period).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))

    return rsi.iloc[-1]

# ===============================
# SIGNAL LOGIC
# ===============================
def get_signal():
    prices = get_price()
    rsi = calculate_rsi(prices)

    if rsi < 30:
        return "BUY 📈", rsi
    elif rsi > 70:
        return "SELL 📉", rsi
    else:
        return "WAIT ⏳", rsi

# ===============================
# MAIN LOOP
# ===============================
while True:
    try:
        signal, rsi_value = get_signal()

        message = f"""
🔥 QUOTEX SIGNAL

PAIR: BTCUSD
TIMEFRAME: 1 MIN

RSI: {round(rsi_value,2)}
SIGNAL: {signal}
"""

        bot.send_message(chat_id=CHAT_ID, text=message)

        time.sleep(60)

    except Exception as e:
        print("Error:", e)
        time.sleep(10)
