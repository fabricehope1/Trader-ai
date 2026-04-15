import os
import json
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, CallbackContext
from pro_engine import get_pro_signal

TOKEN=os.getenv("BOT_TOKEN")

ADMIN_ID=8448217655

CRYPTO_ADDRESS="0xA7123932DF237A24ad8c251502C169d744dd6D41"

user_settings={}

# ================= USERS =================
def load_users():
    with open("users.json") as f:
        return json.load(f)

def save_users(data):
    with open("users.json","w") as f:
        json.dump(data,f)

def add_vip(uid):
    data=load_users()
    if uid not in data["vip_users"]:
        data["vip_users"].append(uid)
        save_users(data)

def is_vip(uid):
    if uid==ADMIN_ID:
        return True
    data=load_users()
    return uid in data["vip_users"]


# ================= START =================
def start(update,context):

    uid=update.message.from_user.id

    if uid==ADMIN_ID:
        kb=[
            [InlineKeyboardButton("📊 Get Signal",callback_data="signal_menu")],
            [InlineKeyboardButton("👑 Admin Panel",callback_data="admin")]
        ]
    else:
        kb=[
            [InlineKeyboardButton("📊 Get Signal",callback_data="signal_menu")],
            [InlineKeyboardButton("💳 Buy VIP",callback_data="buy")]
        ]

    update.message.reply_text(
        "🤖 QUOTEX AI BOT",
        reply_markup=InlineKeyboardMarkup(kb)
    )


# ================= PAIRS =================
def pair_menu(query,uid):

    pairs=[
        "EURUSD","USDJPY","GBPUSD","AUDUSD","USDCAD",
        "EURJPY","GBPJPY","EURGBP","NZDUSD","USDCHF"
    ]

    buttons=[]

    for p in pairs:
        if is_vip(uid):
            buttons.append([InlineKeyboardButton(p,callback_data=f"pair_{p}")])
        else:
            buttons.append([InlineKeyboardButton(f"{p} 🔒",callback_data="locked")])

    buttons.append([InlineKeyboardButton("⬅️ Back",callback_data="back")])

    query.edit_message_text(
        "Select Pair",
        reply_markup=InlineKeyboardMarkup(buttons)
    )


# ================= BUTTON =================
def button(update,context):

    query=update.callback_query
    query.answer()

    uid=query.from_user.id
    data=query.data

    # BACK
    if data=="back":
        start(update,context)
        return

    # BUY VIP
    if data=="buy":

        kb=[
            [InlineKeyboardButton("📋 Copy Address",
             url=f"https://bscscan.com/address/{CRYPTO_ADDRESS}")],
            [InlineKeyboardButton("✅ I PAID",callback_data="proof")],
            [InlineKeyboardButton("⬅️ Back",callback_data="back")]
        ]

        query.edit_message_text(
f"""
💎 VIP PRICE: 15 USDT BEP20

Send payment to:

{CRYPTO_ADDRESS}
""",
reply_markup=InlineKeyboardMarkup(kb)
)

    # USER UPLOAD PROOF
    elif data=="proof":
        context.user_data["await_proof"]=True
        query.message.reply_text("📤 Upload payment screenshot")

    # SIGNAL MENU
    elif data=="signal_menu":
        pair_menu(query,uid)

    # LOCKED
    elif data=="locked":
        query.answer("VIP ONLY 🔒 Buy VIP First",show_alert=True)

    # SELECT PAIR
    elif data.startswith("pair_"):

        pair=data.split("_")[1]

        user_settings[uid]={"pair":pair}

        kb=[
            [InlineKeyboardButton("1 MIN",callback_data="time_1")],
            [InlineKeyboardButton("5 MIN",callback_data="time_5")],
            [InlineKeyboardButton("⬅️ Back",callback_data="signal_menu")]
        ]

        query.edit_message_text(
            f"{pair} Selected\nChoose Timeframe",
            reply_markup=InlineKeyboardMarkup(kb)
        )

    # TIMEFRAME
    elif data.startswith("time_"):

        tf=data.split("_")[1]
        user_settings[uid]["time"]=tf

        kb=[
            [InlineKeyboardButton("🔥 GET SIGNAL",callback_data="signal")],
            [InlineKeyboardButton("⬅️ Back",callback_data="signal_menu")]
        ]

        query.edit_message_text(
            "Click GET SIGNAL",
            reply_markup=InlineKeyboardMarkup(kb)
        )

    # GET SIGNAL
    elif data=="signal":

        if not is_vip(uid):
            query.answer("VIP ONLY 🔒",show_alert=True)
            return

        pair=user_settings[uid]["pair"]
        tf=user_settings[uid]["time"]

        signal,rsi,entry,conf=get_pro_signal(pair,tf)

        query.edit_message_text(
f"""
🔥 QUOTEX PRO SIGNAL

PAIR: {pair}
ENTRY TIME: {entry}
TIMEFRAME: {tf}M

SIGNAL: {signal}
CONFIDENCE: {conf}
"""
)

    # ADMIN PANEL
    elif data=="admin" and uid==ADMIN_ID:

        users=load_users()

        query.edit_message_text(
f"""
👑 ADMIN PANEL

VIP USERS: {len(users['vip_users'])}
"""
)

    # APPROVE USER
    elif data.startswith("approve_"):

        user=int(data.split("_")[1])
        add_vip(user)

        context.bot.send_message(user,"✅ VIP Activated")

        query.edit_message_text("Approved ✅")

    # REJECT USER
    elif data.startswith("reject_"):

        user=int(data.split("_")[1])

        context.bot.send_message(user,"❌ Payment Rejected")

        query.edit_message_text("Rejected ❌")


# ================= PAYMENT PROOF =================
def photo(update,context):

    if not context.user_data.get("await_proof"):
        return

    user=update.message.from_user

    kb=[[
        InlineKeyboardButton("✅ APPROVE",
        callback_data=f"approve_{user.id}"),
        InlineKeyboardButton("❌ REJECT",
        callback_data=f"reject_{user.id}")
    ]]

    context.bot.send_photo(
        ADMIN_ID,
        photo=update.message.photo[-1].file_id,
        caption=f"Payment from @{user.username}\nID:{user.id}",
        reply_markup=InlineKeyboardMarkup(kb)
    )

    update.message.reply_text("✅ Sent to Admin")

    context.user_data["await_proof"]=False


# ================= MAIN =================
def main():

    updater=Updater(TOKEN,use_context=True)

    dp=updater.dispatcher

    dp.add_handler(CommandHandler("start",start))
    dp.add_handler(CallbackQueryHandler(button))
    dp.add_handler(MessageHandler(Filters.photo,photo))

    updater.start_polling()
    updater.idle()

if __name__=="__main__":
    main()
