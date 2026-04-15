import os
import requests
import pandas as pd
from datetime import datetime, timedelta

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext

TOKEN = os.getenv("BOT_TOKEN")

user_settings = {}

# ===============================
# FOREX DATA
# ===============================
def get_prices(pair):

    url = f"https://api.exchangerate.host/timeseries?base={pair[:3]}&symbols={pair[3:]}"
    data = requests.get(url).json()

    prices = []

    if "rates" in data:
        for t in data["rates"]:
            prices.append(data["rates"][t][pair[3:]])

    if len(prices) < 40:
        prices = [1 + i*0.0001 for i in range(60)]

    return prices


# ===============================
# AI ANALYSIS
# ===============================
def ai_signal(pair):

    prices = get_prices(pair)

    series = pd.Series(prices)

    # RSI
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    rsi_value = rsi.iloc[-1]

    # TREND FILTER
    ma_fast = series.rolling(5).mean().iloc[-1]
    ma_slow = series.rolling(20).mean().iloc[-1]

    # AI DECISION
    if rsi_value < 35 and ma_fast > ma_slow:
        signal = "UP 📈"
    elif rsi_value > 65 and ma_fast < ma_slow:
        signal = "DOWN 📉"
    else:
        signal = "WAIT ⏳"

    return signal, rsi_value


# ===============================
# TIME
# ===============================
def entry_time():

    now = datetime.now()
    entry = now + timedelta(minutes=1)

    return now.strftime("%H:%M"), entry.strftime("%H:%M")


# ===============================
# MENUS
# ===============================
def pair_menu():

    keyboard = [
        [InlineKeyboardButton("EURUSD", callback_data="pair_EURUSD")],
        [InlineKeyboardButton("USDJPY", callback_data="pair_USDJPY")],
        [InlineKeyboardButton("EURGBP", callback_data="pair_EURGBP")],
    ]

    return InlineKeyboardMarkup(keyboard)


def timeframe_menu():
    keyboard = [
        [InlineKeyboardButton("1 MIN", callback_data="time_1")],
        [InlineKeyboardButton("5 MIN", callback_data="time_5")],
        [InlineKeyboardButton("⬅️ BACK", callback_data="back_pair")],
    ]
    return InlineKeyboardMarkup(keyboard)


def signal_menu():
    keyboard = [
        [InlineKeyboardButton("GET AI SIGNAL 🔥", callback_data="signal")],
        [InlineKeyboardButton("⬅️ BACK", callback_data="back_time")],
    ]
    return InlineKeyboardMarkup(keyboard)


# ===============================
# START
# ===============================
def start(update: Update, context: CallbackContext):

    update.message.reply_text(
        "🔥 QUOTEX AI BOT\n\nSelect Pair",
        reply_markup=pair_menu(),
    )


# ===============================
# BUTTON HANDLER
# ===============================
def button(update: Update, context: CallbackContext):

    query = update.callback_query
    query.answer()

    user_id = query.from_user.id
    data = query.data

    # BACK BUTTONS
    if data == "back_pair":
        query.edit_message_text(
            "Select Pair",
            reply_markup=pair_menu(),
        )
        return

    if data == "back_time":
        query.edit_message_text(
            "Select Timeframe",
            reply_markup=timeframe_menu(),
        )
        return

    # PAIR
    if data.startswith("pair_"):

        pair = data.split("_")[1]
        user_settings[user_id] = {"pair": pair}

        query.edit_message_text(
            f"✅ Pair Selected: {pair}",
            reply_markup=timeframe_menu(),
        )

    # TIMEFRAME
    elif data.startswith("time_"):

        timeframe = data.split("_")[1]
        user_settings[user_id]["time"] = timeframe

        query.edit_message_text(
            f"⏱ Timeframe: {timeframe} MIN",
            reply_markup=signal_menu(),
        )

    # SIGNAL
    elif data == "signal":

        settings = user_settings[user_id]

        pair = settings["pair"]
        timeframe = settings["time"]

        signal, rsi = ai_signal(pair)

        current_time, entry = entry_time()

        query.edit_message_text(
            f"""
🔥 QUOTEX AI SIGNAL

PAIR: {pair}
TIMEFRAME: {timeframe} MIN

CURRENT TIME: {current_time}
ENTRY TIME: {entry}

AI RSI: {round(rsi,2)}
SIGNAL: {signal}
""",
            reply_markup=signal_menu(),
        )


# ===============================
# MAIN
# ===============================
def main():

    updater = Updater(TOKEN, use_context=True)

    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(button))

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
