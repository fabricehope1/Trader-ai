import os
import requests
import pandas as pd
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.ext import (
    Updater,
    CommandHandler,
    CallbackQueryHandler,
    CallbackContext,
)

TOKEN = os.getenv("BOT_TOKEN")

user_settings = {}

# ===============================
# MARKET DATA
# ===============================
def get_prices(pair):
    symbol = pair.replace("/", "") + "T"
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval=1m&limit=50"
    data = requests.get(url).json()
    closes = [float(candle[4]) for candle in data]
    return closes


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


def get_signal(pair):
    prices = get_prices(pair)
    rsi = calculate_rsi(prices)

    if rsi < 30:
        signal = "BUY 📈"
    elif rsi > 70:
        signal = "SELL 📉"
    else:
        signal = "WAIT ⏳"

    return signal, rsi


# ===============================
# START COMMAND
# ===============================
def start(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("EUR/USD", callback_data="pair_EUR/USDT")],
        [InlineKeyboardButton("BTC/USD", callback_data="pair_BTC/USDT")],
        [InlineKeyboardButton("ETH/USD", callback_data="pair_ETH/USDT")],
    ]

    update.message.reply_text(
        "🔥 Select Pair:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# ===============================
# BUTTON HANDLER
# ===============================
def button(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()

    user_id = query.from_user.id

    data = query.data

    if data.startswith("pair_"):
        pair = data.split("_")[1]
        user_settings[user_id] = {"pair": pair}

        keyboard = [
            [InlineKeyboardButton("1 Minute", callback_data="time_1")],
            [InlineKeyboardButton("5 Minutes", callback_data="time_5")],
        ]

        query.edit_message_text(
            f"✅ Pair Selected: {pair}\n\nSelect Time:",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    elif data.startswith("time_"):
        timeframe = data.split("_")[1]
        user_settings[user_id]["time"] = timeframe

        keyboard = [
            [InlineKeyboardButton("GET SIGNAL 🔥", callback_data="signal")]
        ]

        query.edit_message_text(
            "⏱ Time Selected\n\nClick GET SIGNAL",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    elif data == "signal":
        settings = user_settings[user_id]
        pair = settings["pair"]

        signal, rsi = get_signal(pair)

        query.edit_message_text(
            f"""
🔥 QUOTEX SIGNAL

PAIR: {pair}
TIMEFRAME: 1 MIN

RSI: {round(rsi,2)}
SIGNAL: {signal}
"""
        )


# ===============================
# AUTO SIGNAL EVERY MINUTE
# ===============================
def auto_signal(context: CallbackContext):
    for user_id, settings in user_settings.items():
        pair = settings["pair"]
        signal, rsi = get_signal(pair)

        context.bot.send_message(
            chat_id=user_id,
            text=f"""
⚡ AUTO SIGNAL

PAIR: {pair}
RSI: {round(rsi,2)}
SIGNAL: {signal}
"""
        )


# ===============================
# MAIN
# ===============================
def main():
    updater = Updater(TOKEN, use_context=True)

    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(button))

    updater.job_queue.run_repeating(auto_signal, interval=60, first=10)

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
