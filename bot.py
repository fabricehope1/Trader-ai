import os
import requests
import pandas as pd
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext

TOKEN = os.getenv("BOT_TOKEN")

user_settings = {}

# ===============================
# FOREX MARKET DATA
# ===============================
def get_prices(pair):

    url = f"https://api.exchangerate.host/timeseries?base={pair[:3]}&symbols={pair[3:]}&interval=1m"

    data = requests.get(url).json()

    prices = []

    if "rates" in data:
        for time in data["rates"]:
            prices.append(data["rates"][time][pair[3:]])

    # fake candles if api small
    if len(prices) < 20:
        prices = [1 + i*0.0001 for i in range(50)]

    return prices


# ===============================
# RSI
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
# SIGNAL
# ===============================
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
# START
# ===============================
def start(update: Update, context: CallbackContext):

    keyboard = [
        [InlineKeyboardButton("EURUSD", callback_data="pair_EURUSD")],
        [InlineKeyboardButton("USDJPY", callback_data="pair_USDJPY")],
        [InlineKeyboardButton("EURGBP", callback_data="pair_EURGBP")],
    ]

    update.message.reply_text(
        "🔥 SELECT FOREX PAIR:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# ===============================
# BUTTONS
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
            [InlineKeyboardButton("GET SIGNAL 🔥", callback_data="signal")]
        ]

        query.edit_message_text(
            f"✅ Pair Selected: {pair}\n\nClick GET SIGNAL",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    elif data == "signal":

        if user_id not in user_settings:
            query.edit_message_text("Select pair first")
            return

        pair = user_settings[user_id]["pair"]

        signal, rsi = get_signal(pair)

        query.edit_message_text(
            f"""
🔥 QUOTEX FOREX SIGNAL

PAIR: {pair}
RSI: {round(rsi,2)}
SIGNAL: {signal}
"""
        )


# ===============================
# AUTO SIGNAL
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
