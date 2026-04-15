import os
import requests
import pandas as pd
from datetime import datetime, timedelta

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext

TOKEN = os.getenv("BOT_TOKEN")

user_settings = {}

# ==================================================
# MARKET DATA
# ==================================================
def get_prices(pair):

    url = f"https://api.exchangerate.host/timeseries?base={pair[:3]}&symbols={pair[3:]}"
    data = requests.get(url).json()

    prices = []

    if "rates" in data:
        for t in data["rates"]:
            prices.append(data["rates"][t][pair[3:]])

    # fallback candles
    if len(prices) < 50:
        prices = [1 + i*0.0002 for i in range(60)]

    return prices


# ==================================================
# ULTRA AI ENGINE
# ==================================================
def ai_signal(pair):

    prices = get_prices(pair)

    series = pd.Series(prices)

    # ===== RSI =====
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    rsi_value = rsi.iloc[-1]

    # ===== EMA TREND =====
    ema_fast = series.ewm(span=5).mean().iloc[-1]
    ema_slow = series.ewm(span=20).mean().iloc[-1]

    # ===== MOMENTUM =====
    momentum = series.iloc[-1] - series.iloc[-5]

    score_up = 0
    score_down = 0

    if rsi_value < 50:
        score_up += 1
    else:
        score_down += 1

    if ema_fast > ema_slow:
        score_up += 1
    else:
        score_down += 1

    if momentum > 0:
        score_up += 1
    else:
        score_down += 1

    if score_up >= score_down:
        signal = "UP 📈"
        confidence = 70 + score_up * 10
        trend = "STRONG UP"
    else:
        signal = "DOWN 📉"
        confidence = 70 + score_down * 10
        trend = "STRONG DOWN"

    return signal, rsi_value, confidence, trend


# ==================================================
# ENTRY TIME
# ==================================================
def entry_time():
    now = datetime.now()
    entry = now + timedelta(minutes=1)
    return now.strftime("%H:%M"), entry.strftime("%H:%M")


# ==================================================
# MENUS
# ==================================================
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


# ==================================================
# START
# ==================================================
def start(update: Update, context: CallbackContext):
    update.message.reply_text(
        "🔥 ULTRA QUOTEX AI BOT\n\nSelect Pair",
        reply_markup=pair_menu(),
    )


# ==================================================
# BUTTON HANDLER
# ==================================================
def button(update: Update, context: CallbackContext):

    query = update.callback_query
    query.answer()

    user_id = query.from_user.id
    data = query.data

    # BACK BUTTONS
    if data == "back_pair":
        query.edit_message_text("Select Pair", reply_markup=pair_menu())
        return

    if data == "back_time":
        query.edit_message_text("Select Timeframe", reply_markup=timeframe_menu())
        return

    # SELECT PAIR
    if data.startswith("pair_"):
        pair = data.split("_")[1]
        user_settings[user_id] = {"pair": pair}

        query.edit_message_text(
            f"✅ Pair Selected: {pair}",
            reply_markup=timeframe_menu(),
        )

    # SELECT TIMEFRAME
    elif data.startswith("time_"):
        timeframe = data.split("_")[1]
        user_settings[user_id]["time"] = timeframe

        query.edit_message_text(
            f"⏱ Timeframe: {timeframe} MIN",
            reply_markup=signal_menu(),
        )

    # GET SIGNAL
    elif data == "signal":

        settings = user_settings[user_id]

        pair = settings["pair"]
        timeframe = settings["time"]

        signal, rsi, confidence, trend = ai_signal(pair)

        current_time, entry = entry_time()

        query.edit_message_text(
f"""
🔥 ULTRA AI SIGNAL

PAIR: {pair}
TIMEFRAME: {timeframe} MIN

CURRENT TIME: {current_time}
ENTRY TIME: {entry}

AI RSI: {round(rsi,2)}
TREND: {trend}

SIGNAL: {signal}
CONFIDENCE: {confidence}%
""",
            reply_markup=signal_menu(),
        )


# ==================================================
# MAIN
# ==================================================
def main():

    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(button))

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
