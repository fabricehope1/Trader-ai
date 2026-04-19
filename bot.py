import telebot
import json
import os
import time
from threading import Thread
from telebot.types import ReplyKeyboardMarkup
from pro_engine import generate_signal, PAIRS, get_prices

TOKEN=os.getenv("BOT_TOKEN")
ADMIN_ID=8448217655

bot=telebot.TeleBot(TOKEN)

PAYMENT_ADDRESS="0xA7123932DF237A24ad8c251502C169d744dd6D41"

waiting_broadcast={}
waiting_payment={}
user_pair={}

# ================= DATABASE =================

def load_users():
    try:
        return json.load(open("users.json"))
    except:
        return {}

def save_users(data):
    json.dump(data,open("users.json","w"))

def load_stats():
    try:
        return json.load(open("stats.json"))
    except:
        return {}

def save_stats(data):
    json.dump(data,open("stats.json","w"))

users=load_users()
user_stats=load_stats()

# ================= MENUS =================

def main_menu(chat_id):

    kb=ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("📊 Get Signal")
    kb.add("💳 Payment")

    if chat_id==ADMIN_ID:
        kb.add("⚙ ADMIN PANEL")

    bot.send_message(chat_id,"Main Menu",reply_markup=kb)

def back_menu(chat_id,text):
    kb=ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("⬅ Back")
    bot.send_message(chat_id,text,reply_markup=kb)

# ================= REAL AUTO TRACKER =================

def auto_tracker(chat_id,pair,signal,timeframe,prepare_seconds):

    try:

        # wait entry time
        time.sleep(prepare_seconds)

        prices=get_prices(pair,timeframe)
        if not prices:
            return

        entry_price=prices[-1]

        tf_seconds={
            "M1":60,
            "M5":300,
            "M15":900
        }

        # wait candle close
        time.sleep(tf_seconds.get(timeframe,60))

        prices_after=get_prices(pair,timeframe)
        if not prices_after:
            return

        close_price=prices_after[-1]

        if "CALL" in signal:
            result="WIN" if close_price>entry_price else "LOSS"
        else:
            result="WIN" if close_price<entry_price else "LOSS"

        # save stats
        uid=str(chat_id)

        if uid not in user_stats:
            user_stats[uid]={"win":0,"loss":0}

        if result=="WIN":
            user_stats[uid]["win"]+=1
        else:
            user_stats[uid]["loss"]+=1

        save_stats(user_stats)

        # user result
        bot.send_message(chat_id,f"""
📊 SIGNAL RESULT

Pair: {pair}
Entry: {entry_price}
Close: {close_price}

RESULT: {result}
""")

        # admin live result
        bot.send_message(ADMIN_ID,f"""
🔥 USER TRADE RESULT

User: {chat_id}
Pair: {pair}
Signal: {signal}

Entry: {entry_price}
Close: {close_price}

RESULT: {result}
""")

    except Exception as e:
        print("TRACKER ERROR:",e)

# ================= START =================

@bot.message_handler(commands=["start"])
def start(msg):

    uid=str(msg.chat.id)

    if uid not in users:
        users[uid]={"approved":False}

    if msg.chat.id==ADMIN_ID:
        users[uid]["approved"]=True

    save_users(users)

    bot.send_message(msg.chat.id,f"Your ID: {msg.chat.id}")
    main_menu(msg.chat.id)

# ================= MESSAGE HANDLER =================

@bot.message_handler(content_types=["text","photo","video","document"])
def messages(msg):

    uid=str(msg.chat.id)
    text=msg.text if msg.content_type=="text" else ""

    if text=="⬅ Back":
        main_menu(msg.chat.id)
        return

# ================= PAYMENT =================

    if text=="💳 Payment":

        kb=ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add("📋 Copy Address")
        kb.add("📤 Upload Payment Proof")
        kb.add("⬅ Back")

        bot.send_message(
            msg.chat.id,
            f"Send USDT BEP20 Payment:\n\n{PAYMENT_ADDRESS}",
            reply_markup=kb)
        return

    if text=="📋 Copy Address":
        bot.send_message(msg.chat.id,PAYMENT_ADDRESS)
        return

    if text=="📤 Upload Payment Proof":
        waiting_payment[uid]=True
        back_menu(msg.chat.id,"Send payment screenshot.")
        return

# ================= SIGNAL =================

    if text=="📊 Get Signal":

        if uid not in users:
            users[uid]={"approved":False}

        if not users[uid]["approved"]:
            bot.send_message(msg.chat.id,"🔒 Access Locked")
            return

        kb=ReplyKeyboardMarkup(resize_keyboard=True)

        for p in PAIRS:
            kb.add(p)

        kb.add("⬅ Back")

        bot.send_message(msg.chat.id,"Select Pair",reply_markup=kb)
        return

# ================= PAIR =================

    if text in PAIRS:

        user_pair[msg.chat.id]=text

        kb=ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add("M1","M5","M15")
        kb.add("⬅ Back")

        bot.send_message(
            msg.chat.id,
            f"Pair Selected: {text}\nSelect Timeframe",
            reply_markup=kb)
        return

# ================= TIMEFRAME =================

    if text in ["M1","M5","M15"]:

        pair=user_pair.get(msg.chat.id)

        if not pair:
            bot.send_message(msg.chat.id,"⚠️ Select pair first")
            return

        result=generate_signal(pair,text)

        if result.get("status")=="success":

            message=f"""
📊 AI SIGNAL

Pair: {result['pair']}
Signal: {result['signal']}
Timeframe: {result['timeframe']}
Entry Time: {result['entry_time']}
Accuracy: {result['accuracy']}
"""

            bot.send_message(msg.chat.id,message)

            # extract prepare seconds
            prepare=int(result['signal'].split("Prepare:")[1].split("s")[0])

            Thread(
                target=auto_tracker,
                args=(
                    msg.chat.id,
                    result['pair'],
                    result['signal'],
                    result['timeframe'],
                    prepare
                )
            ).start()

        else:
            bot.send_message(msg.chat.id,"⚠️ Signal error")

        return

# ================= ADMIN PANEL =================

    if text=="⚙ ADMIN PANEL" and msg.chat.id==ADMIN_ID:

        kb=ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add("📩 Broadcast")
        kb.add("👥 Pending Users")
        kb.add("📊 Users Results")
        kb.add("⬅ Back")

        bot.send_message(msg.chat.id,"ADMIN PANEL",reply_markup=kb)
        return

# ================= USERS RESULTS =================

    if text=="📊 Users Results" and msg.chat.id==ADMIN_ID:

        report="📊 USERS RESULTS\n\n"

        for u,data in user_stats.items():
            report+=f"""
User: {u}
WIN: {data.get('win',0)}
LOSS: {data.get('loss',0)}
"""

        bot.send_message(msg.chat.id,report)
        return

# ================= PAYMENT PROOF =================

    if uid in waiting_payment:

        bot.forward_message(
            ADMIN_ID,
            msg.chat.id,
            msg.message_id
        )

        bot.send_message(msg.chat.id,"✅ Proof sent to admin")

        waiting_payment.pop(uid)
        return

# ================= START BOT =================

bot.infinity_polling(
    timeout=60,
    long_polling_timeout=60,
    skip_pending=True
    )
