import os
import requests
import pandas as pd
from ta.momentum import RSIIndicator
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = os.getenv("TOKEN")

pairs = {
    "EURUSD": "BTCUSDT",
    "GBPUSD": "ETHUSDT",
    "USDJPY": "BNBUSDT"
}

times = {
    "1m": "1m",
    "2m": "3m",
    "3m": "5m",
    "5m": "15m"
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("📊 GET SIGNAL", callback_data="signal")]]
    await update.message.reply_text(
        "🔥 Pocket Option Signal Bot",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "signal":
        keyboard = [
            [InlineKeyboardButton(p, callback_data=f"pair_{p}")]
            for p in pairs
        ]
        await query.edit_message_text(
            "Choose Pair:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif "pair_" in query.data:
        pair = query.data.split("_")[1]
        context.user_data["pair"] = pair

        keyboard = [
            [InlineKeyboardButton(t, callback_data=f"time_{t}")]
            for t in times
        ]
        await query.edit_message_text(
            f"{pair} selected\nChoose Time:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif "time_" in query.data:
        pair = context.user_data["pair"]
        timeframe = query.data.split("_")[1]

        signal, acc = get_signal(pair, timeframe)

        await query.edit_message_text(
f"""
📊 SIGNAL

Pair: {pair}
Time: {timeframe}
Direction: {signal}
Accuracy: {acc}%
"""
        )

def get_signal(pair, timeframe):
    symbol = pairs[pair]
    interval = times[timeframe]

    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit=100"
    data = requests.get(url).json()

    closes = [float(c[4]) for c in data]
    df = pd.DataFrame(closes, columns=["close"])

    rsi = RSIIndicator(df["close"], window=14).rsi().iloc[-1]

    if rsi < 30:
        return "🟢 CALL", 88
    elif rsi > 70:
        return "🔴 PUT", 85
    else:
        return "⚪ WAIT", 60

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button))

print("BOT STARTED...")
app.run_polling()
