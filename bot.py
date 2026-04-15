import os
import requests
import pandas as pd
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# ========================
# START COMMAND
# ========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Trader AI Bot Online!")

# ========================
# GET MARKET DATA
# ========================
def get_price():
    url = "https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1m&limit=50"
    data = requests.get(url).json()
    closes = [float(candle[4]) for candle in data]
    return closes

# ========================
# RSI CALCULATION
# ========================
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

# ========================
# SEND SIGNAL
# ========================
async def send_signal(context: ContextTypes.DEFAULT_TYPE):

    prices = get_price()
    rsi = calculate_rsi(prices)

    if rsi < 30:
        signal = "BUY 📈"
    elif rsi > 70:
        signal = "SELL 📉"
    else:
        signal = "WAIT ⏳"

    message = f"""
🔥 QUOTEX SIGNAL

PAIR: BTCUSD
TIMEFRAME: 1 MIN
RSI: {round(rsi,2)}

SIGNAL: {signal}
"""

    await context.bot.send_message(chat_id=CHAT_ID, text=message)

# ========================
# MAIN BOT
# ========================
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))

app.job_queue.run_repeating(send_signal, interval=60, first=10)

app.run_polling()
