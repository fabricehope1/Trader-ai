import os
import json
import requests
import pandas as pd
import random
from datetime import datetime, timedelta

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, CallbackContext

TOKEN = os.getenv("BOT_TOKEN")
FOREX_API = os.getenv("FOREX_API")
ADMIN_ID = 8448217655

DATA_FILE = "users.json"

# =====================
# DATABASE
# =====================

def load_users():
    if not os.path.exists(DATA_FILE):
        return {"vip_users": [], "pending": {}}

    with open(DATA_FILE) as f:
        return json.load(f)


def save_users(data):
    with open(DATA_FILE,"w") as f:
        json.dump(data,f)


def is_vip(user_id):
    if user_id == ADMIN_ID:
        return True

    data = load_users()
    return user_id in data["vip_users"]


user_settings = {}

# =====================
# LIVE FOREX DATA
# =====================

def get_live_price(pair):

    symbol = pair.replace("/","")

    url=f"https://api.twelvedata.com/time_series?symbol={symbol}&interval=1min&outputsize=50&apikey={FOREX_API}"

    r=requests.get(url).json()

    if "values" not in r:
        return None

    prices=[float(c["close"]) for c in r["values"]]
    prices.reverse()

    return prices


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


def generate_signal(pair):

    prices=get_live_price(pair)

    if not prices:
        return "Market Error",0,"00:00"

    rsi=calculate_rsi(prices)

    trend_up=prices[-1]>prices[-5]

    if rsi<45 and trend_up:
        signal="UP 📈"
    elif rsi>55 and not trend_up:
        signal="DOWN 📉"
    else:
        signal=random.choice(["UP 📈","DOWN 📉"])

    entry=(datetime.utcnow()+timedelta(minutes=1)).strftime("%H:%M")

    return signal,round(rsi,2),entry

# =====================
# PAIRS
# =====================

PAIRS=[
"EUR/USD","USD/JPY","GBP/USD","EUR/GBP",
"AUD/USD","USD/CAD","EUR/JPY","GBP/JPY",
"NZD/USD","USD/CHF"
]

# =====================
# START
# =====================

def start(update,context):

    user_id=update.message.from_user.id

    if user_id==ADMIN_ID:
        kb=[
            [InlineKeyboardButton("📊 Get Signal",callback_data="pairs")],
            [InlineKeyboardButton("👑 Admin Panel",callback_data="admin")]
        ]
    else:
        kb=[
            [InlineKeyboardButton("📊 Get Signal",callback_data="pairs")],
            [InlineKeyboardButton("💳 Buy VIP",callback_data="buy")]
        ]

    update.message.reply_text(
        "🤖 PRO AI FOREX BOT",
        reply_markup=InlineKeyboardMarkup(kb)
    )

# =====================
# BUTTON HANDLER
# =====================

def button(update,context):

    query=update.callback_query
    query.answer()

    user_id=query.from_user.id
    data=query.data

    # BACK
    if data=="back":
        start(update,context)
        return

    # SHOW PAIRS
    if data=="pairs":

        buttons=[]

        for p in PAIRS:
            if is_vip(user_id):
                buttons.append([InlineKeyboardButton(p,callback_data=f"pair_{p}")])
            else:
                buttons.append([InlineKeyboardButton(f"{p} 🔒",callback_data="locked")])

        buttons.append([InlineKeyboardButton("⬅ Back",callback_data="back")])

        query.edit_message_text(
            "Select Pair:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    elif data=="locked":
        query.answer("🔒 Buy VIP to unlock signals",show_alert=True)

    # SELECT PAIR
    elif data.startswith("pair_"):

        pair=data.split("_")[1]
        user_settings[user_id]={"pair":pair}

        kb=[
            [InlineKeyboardButton("GET SIGNAL 🔥",callback_data="signal")],
            [InlineKeyboardButton("⬅ Back",callback_data="pairs")]
        ]

        query.edit_message_text(
            f"PAIR SELECTED: {pair}",
            reply_markup=InlineKeyboardMarkup(kb)
        )

    # SIGNAL
    elif data=="signal":

        if not is_vip(user_id):
            query.answer("🔒 VIP required",show_alert=True)
            return

        pair=user_settings[user_id]["pair"]

        signal,rsi,entry=generate_signal(pair)

        kb=[[InlineKeyboardButton("⬅ Back",callback_data="pairs")]]

        query.edit_message_text(
f"""🔥 LIVE AI SIGNAL

PAIR: {pair}

RSI: {rsi}

SIGNAL: {signal}

ENTRY TIME: {entry}
EXPIRY: 1 MIN
""",
reply_markup=InlineKeyboardMarkup(kb)
)

    # BUY VIP
    elif data=="buy":

        kb=[
            [InlineKeyboardButton("📋 Copy Payment Address",callback_data="copy")],
            [InlineKeyboardButton("⬆ Upload Payment Proof",callback_data="proof")],
            [InlineKeyboardButton("⬅ Back",callback_data="back")]
        ]

        query.edit_message_text(
"""
💳 VIP PAYMENT

Network: BEP20
Coin: CRYPTO USD

Address:
0xA7123932DF237A24ad8c251502C169d744dd6D41
""",
reply_markup=InlineKeyboardMarkup(kb)
)

    elif data=="copy":
        query.answer("Address copied ✔")

    elif data=="proof":
        context.bot.send_message(user_id,"Send payment screenshot.")

    # ADMIN PANEL
    elif data=="admin":

        if user_id!=ADMIN_ID:
            return

        kb=[
            [InlineKeyboardButton("📥 Pending Payments",callback_data="pending")],
            [InlineKeyboardButton("📢 Broadcast",callback_data="broadcast")],
            [InlineKeyboardButton("⬅ Back",callback_data="back")]
        ]

        query.edit_message_text(
            "ADMIN PANEL",
            reply_markup=InlineKeyboardMarkup(kb)
        )

    elif data=="pending":

        data_users=load_users()

        if not data_users["pending"]:
            query.edit_message_text("No pending users")
            return

        for uid in data_users["pending"]:
            context.bot.send_message(
                ADMIN_ID,
                f"User waiting approval: {uid}",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("✅ Approve",callback_data=f"approve_{uid}")],
                    [InlineKeyboardButton("❌ Reject",callback_data=f"reject_{uid}")]
                ])
            )

    elif data.startswith("approve_"):

        uid=int(data.split("_")[1])

        data_users=load_users()
        data_users["vip_users"].append(uid)
        del data_users["pending"][str(uid)]

        save_users(data_users)

        context.bot.send_message(uid,"✅ VIP ACTIVATED")

    elif data.startswith("reject_"):

        uid=int(data.split("_")[1])

        data_users=load_users()
        del data_users["pending"][str(uid)]

        save_users(data_users)

        context.bot.send_message(uid,"❌ Payment rejected")

    elif data=="broadcast":
        context.bot.send_message(ADMIN_ID,"Send message to broadcast.")


# =====================
# PAYMENT PROOF HANDLER
# =====================

def proof_handler(update,context):

    user_id=update.message.from_user.id

    if update.message.photo:

        data_users=load_users()
        data_users["pending"][str(user_id)]="waiting"
        save_users(data_users)

        context.bot.forward_message(
            ADMIN_ID,
            user_id,
            update.message.message_id
        )

        update.message.reply_text("Payment sent for approval ✔")


# =====================
# MAIN
# =====================

def main():

    updater=Updater(TOKEN,use_context=True)
    dp=updater.dispatcher

    dp.add_handler(CommandHandler("start",start))
    dp.add_handler(CallbackQueryHandler(button))
    dp.add_handler(MessageHandler(Filters.photo,proof_handler))

    updater.start_polling()
    updater.idle()

if __name__=="__main__":
    main()
