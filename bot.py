import telebot
import json
import os
from telebot.types import InlineKeyboardMarkup,InlineKeyboardButton
from pro_engine import generate_signal,PAIRS

TOKEN=os.getenv("BOT_TOKEN")
ADMIN_ID=8448217655

bot=telebot.TeleBot(TOKEN)

PAYMENT_ADDRESS="0xA7123932DF237A24ad8c251502C169d744dd6D41"

waiting_broadcast={}
waiting_payment={}

# ================= DATABASE =================

def load_users():
    try:
        return json.load(open("users.json"))
    except:
        return {}

def save_users(data):
    json.dump(data,open("users.json","w"))

users=load_users()

# ================= MAIN MENU =================

def main_menu(chat_id):

    kb=InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("📊 Get Signal",callback_data="signal"))
    kb.add(InlineKeyboardButton("💳 Payment",callback_data="payment"))

    if chat_id==ADMIN_ID:
        kb.add(InlineKeyboardButton("⚙ ADMIN PANEL",callback_data="admin"))

    bot.send_message(chat_id,"Main Menu",reply_markup=kb)

# ================= START =================

@bot.message_handler(commands=["start"])
def start(msg):

    uid=str(msg.chat.id)

    if uid not in users:
        users[uid]={"approved":False}
        save_users(users)

    main_menu(msg.chat.id)

# ================= CALLBACK =================

@bot.callback_query_handler(func=lambda call:True)
def callback(call):

    uid=str(call.message.chat.id)

# BACK
    if call.data=="back":
        main_menu(call.message.chat.id)

# PAYMENT
    elif call.data=="payment":

        kb=InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("📋 Copy Address",callback_data="copy"))
        kb.add(InlineKeyboardButton("📤 Upload Payment Proof",callback_data="upload"))
        kb.add(InlineKeyboardButton("⬅ Back",callback_data="back"))

        bot.edit_message_text(
            f"Send USDT BEP20 Payment:\n\n{PAYMENT_ADDRESS}",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=kb)

    elif call.data=="copy":
        bot.answer_callback_query(call.id,"Address Copied ✅",show_alert=True)
        bot.send_message(call.message.chat.id,PAYMENT_ADDRESS)

    elif call.data=="upload":
        waiting_payment[call.message.chat.id]=True
        bot.send_message(call.message.chat.id,"Send payment screenshot.")

# SIGNAL LOCK
    elif call.data=="signal":

        if not users[uid]["approved"]:
            bot.answer_callback_query(call.id,"🔒 Access Locked")
            return

        kb=InlineKeyboardMarkup()
        kb.add(
            InlineKeyboardButton("M1",callback_data="tf_M1"),
            InlineKeyboardButton("M5",callback_data="tf_M5"))
        kb.add(
            InlineKeyboardButton("M15",callback_data="tf_M15"))
        kb.add(InlineKeyboardButton("⬅ Back",callback_data="back"))

        bot.edit_message_text(
            "Select Timeframe",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=kb)

# TIMEFRAME
    elif call.data.startswith("tf_"):

        timeframe=call.data.split("_")[1]
        pair=PAIRS[0]

        signal=generate_signal(pair,timeframe)

        bot.send_message(call.message.chat.id,signal)

# ADMIN PANEL
    elif call.data=="admin" and call.message.chat.id==ADMIN_ID:

        kb=InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("📩 Broadcast",callback_data="broadcast"))
        kb.add(InlineKeyboardButton("👥 Pending Users",callback_data="pending"))
        kb.add(InlineKeyboardButton("⬅ Back",callback_data="back"))

        bot.edit_message_text(
            "ADMIN PANEL",
            call.message.chat.id,
            call.message.message_id,
            reply_markup=kb)

# BROADCAST
    elif call.data=="broadcast":
        waiting_broadcast[call.message.chat.id]=True
        bot.send_message(call.message.chat.id,"Send message/photo to broadcast.")

# PENDING USERS
    elif call.data=="pending":

        for user,data in users.items():
            if not data["approved"]:
                kb=InlineKeyboardMarkup()
                kb.add(
                    InlineKeyboardButton("✅ Approve",callback_data=f"approve_{user}"),
                    InlineKeyboardButton("❌ Reject",callback_data=f"reject_{user}")
                )

                bot.send_message(call.message.chat.id,f"User waiting: {user}",reply_markup=kb)

# APPROVE
    elif call.data.startswith("approve_"):

        user=call.data.split("_")[1]
        users[user]["approved"]=True
        save_users(users)

        bot.send_message(user,"✅ Payment Approved. Access Granted.")
        bot.answer_callback_query(call.id,"Approved")

# REJECT
    elif call.data.startswith("reject_"):

        user=call.data.split("_")[1]
        bot.send_message(user,"❌ Payment Rejected")
        bot.answer_callback_query(call.id,"Rejected")

# ================= MESSAGE HANDLER =================

@bot.message_handler(content_types=["text","photo"])
def messages(msg):

    uid=msg.chat.id

# PAYMENT PROOF
    if uid in waiting_payment:

        bot.forward_message(ADMIN_ID,uid,msg.message_id)
        bot.send_message(uid,"✅ Proof sent to admin")

        waiting_payment.pop(uid)
        return

# BROADCAST
    if uid in waiting_broadcast:

        sent=0

        for user in users:
            try:
                if msg.content_type=="text":
                    bot.send_message(user,msg.text)
                else:
                    bot.send_photo(user,msg.photo[-1].file_id,caption=msg.caption)
                sent+=1
            except:
                pass

        bot.send_message(uid,f"✅ Broadcast sent to {sent} users")

        waiting_broadcast.pop(uid)
        return

bot.infinity_polling()
