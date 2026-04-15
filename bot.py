import os
import json
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, CallbackContext

from pro_engine import get_pro_signal

TOKEN=os.getenv("BOT_TOKEN")

ADMIN_ID=123456789

CRYPTO_ADDRESS="0xA7123932DF237A24ad8c251502C169d744dd6D41"

user_settings={}

# ================= USERS =================
def load_users():
    with open("users.json") as f:
        return json.load(f)

def save_users(data):
    with open("users.json","w") as f:
        json.dump(data,f)

def add_vip(user_id):
    data=load_users()
    if user_id not in data["vip_users"]:
        data["vip_users"].append(user_id)
        save_users(data)

def is_vip(user_id):
    if user_id==ADMIN_ID:
        return True
    data=load_users()
    return user_id in data["vip_users"]


# ================= PAYMENTS =================
def load_payments():
    with open("payments.json") as f:
        return json.load(f)

def save_payments(data):
    with open("payments.json","w") as f:
        json.dump(data,f)


# ================= START =================
def start(update:Update,context:CallbackContext):

    kb=[
        [InlineKeyboardButton("📊 Get Signal",callback_data="signal_menu")],
        [InlineKeyboardButton("💳 Buy VIP",callback_data="buy_vip")]
    ]

    update.message.reply_text(
        "🤖 AI SIGNAL BOT",
        reply_markup=InlineKeyboardMarkup(kb)
    )


# ================= BUY VIP =================
def buy_vip(query):

    keyboard=[
        [InlineKeyboardButton("📋 Copy Payment Address",url=f"https://bscscan.com/address/{CRYPTO_ADDRESS}")],
        [InlineKeyboardButton("✅ I PAID",callback_data="upload_proof")]
    ]

    query.edit_message_text(
f"""
💎 VIP PRICE: 15 USDT (BEP20)

Send payment to:

{CRYPTO_ADDRESS}

After payment click I PAID
""",
reply_markup=InlineKeyboardMarkup(keyboard)
)


# ================= BUTTON =================
def button(update:Update,context:CallbackContext):

    query=update.callback_query
    query.answer()

    user_id=query.from_user.id
    data=query.data

    if data=="buy_vip":
        buy_vip(query)

    elif data=="upload_proof":
        context.user_data["awaiting_proof"]=True
        query.message.reply_text("📤 Upload payment screenshot")

    elif data=="signal_menu":

        keyboard=[
            [InlineKeyboardButton("EURUSD",callback_data="pair_EURUSD")],
            [InlineKeyboardButton("USDJPY",callback_data="pair_USDJPY")],
            [InlineKeyboardButton("EURGBP",callback_data="pair_EURGBP")]
        ]

        query.edit_message_text(
            "Select Pair",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif data.startswith("pair_"):

        pair=data.split("_")[1]
        user_settings[user_id]={"pair":pair}

        kb=[
            [InlineKeyboardButton("1 MIN",callback_data="time_1")],
            [InlineKeyboardButton("5 MIN",callback_data="time_5")]
        ]

        query.edit_message_text("Select Timeframe",
        reply_markup=InlineKeyboardMarkup(kb))

    elif data.startswith("time_"):

        timeframe=data.split("_")[1]
        user_settings[user_id]["time"]=timeframe

        kb=[[InlineKeyboardButton("🔥 GET SIGNAL",callback_data="signal")]]

        query.edit_message_text(
            "Click GET SIGNAL",
            reply_markup=InlineKeyboardMarkup(kb)
        )

    elif data=="signal":

        if not is_vip(user_id):
            query.edit_message_text("❌ VIP ONLY\nBuy VIP First")
            return

        pair=user_settings[user_id]["pair"]
        timeframe=user_settings[user_id]["time"]

        signal,rsi,entry,confidence=get_pro_signal(pair,timeframe)

        query.edit_message_text(
f"""
🔥 QUOTEX PRO SIGNAL

PAIR: {pair}
ENTRY: {entry}
TIMEFRAME: {timeframe}

SIGNAL: {signal}
CONFIDENCE: {confidence}
"""
        )

    # ===== ADMIN APPROVE =====
    elif data.startswith("approve_"):

        uid=int(data.split("_")[1])
        add_vip(uid)

        context.bot.send_message(uid,"✅ Payment Approved. VIP Activated")

        query.edit_message_text("User Approved ✅")

    elif data.startswith("reject_"):

        uid=int(data.split("_")[1])

        context.bot.send_message(uid,"❌ Payment Rejected")

        query.edit_message_text("User Rejected ❌")


# ================= PAYMENT PROOF =================
def handle_photo(update:Update,context:CallbackContext):

    if not context.user_data.get("awaiting_proof"):
        return

    user=update.message.from_user

    keyboard=[
        [
            InlineKeyboardButton("✅ APPROVE",
            callback_data=f"approve_{user.id}"),
            InlineKeyboardButton("❌ REJECT",
            callback_data=f"reject_{user.id}")
        ]
    ]

    context.bot.send_photo(
        ADMIN_ID,
        photo=update.message.photo[-1].file_id,
        caption=f"Payment Proof from @{user.username}\nID:{user.id}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    update.message.reply_text("✅ Proof sent to Admin")

    context.user_data["awaiting_proof"]=False


# ================= MAIN =================
def main():

    updater=Updater(TOKEN,use_context=True)

    dp=updater.dispatcher

    dp.add_handler(CommandHandler("start",start))
    dp.add_handler(CallbackQueryHandler(button))
    dp.add_handler(MessageHandler(Filters.photo,handle_photo))

    updater.start_polling()
    updater.idle()

if __name__=="__main__":
    main()
