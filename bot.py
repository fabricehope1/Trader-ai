import telebot
import json
import os
import time
import threading
from threading import Thread
from session_manager import session_manager
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from telebot.types import ReplyKeyboardMarkup

# ENGINE
from pro_engine import generate_signal, PAIRS, get_prices, find_best_pair

TOKEN=os.getenv("BOT_TOKEN")

ADMIN_ID=8448217655

bot=telebot.TeleBot(TOKEN)

PAYMENT_ADDRESS="0xA7123932DF237A24ad8c251502C169d744dd6D41"

waiting_broadcast={}
waiting_payment={}
user_pair={}
skip_tracker={}

TZ=ZoneInfo("Africa/Kigali")

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
        return {"users":{}, "admin":{"win":0,"loss":0}}

def save_stats(data):
    json.dump(data,open("stats.json","w"))

users=load_users()
stats=load_stats()

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

# ================= AUTO TRACKER =================

def auto_tracker(chat_id,pair,signal,timeframe,entry_time):

    while True:
        if skip_tracker.get(chat_id):
            skip_tracker.pop(chat_id)
            return

        now=datetime.now(TZ).strftime("%H:%M:%S")
        if now>=entry_time:
            break
        time.sleep(1)

    prices=get_prices(pair,timeframe)
    if not prices:
        return

    entry_price=prices[-1]

    tf_seconds={"M1":60,"M5":300,"M15":900}

    time.sleep(tf_seconds.get(timeframe,60))

    prices_after=get_prices(pair,timeframe)
    if not prices_after:
        return

    close_price=prices_after[-1]

    result="WIN" if ("CALL" in signal and close_price>entry_price) or ("PUT" in signal and close_price<entry_price) else "LOSS"

    uid=str(chat_id)

    if uid not in stats["users"]:
        stats["users"][uid]={"win":0,"loss":0}

    stats["users"][uid]["win" if result=="WIN" else "loss"]+=1

    if chat_id==ADMIN_ID:
        stats["admin"]["win" if result=="WIN" else "loss"]+=1

    save_stats(stats)

    bot.send_message(chat_id,f"""
📊 SIGNAL RESULT

Pair: {pair}
Entry: {entry_price}
Close: {close_price}

RESULT: {result}
""")

# ================= MESSAGE HANDLER =================

@bot.message_handler(content_types=["text","photo","video","document"])
def messages(msg):

    uid=str(msg.chat.id)
    text=msg.text if msg.content_type=="text" else ""

    if text=="⬅ Back":
        main_menu(msg.chat.id)
        return

# SKIP
    if text=="⏭ Skip Signal":
        skip_tracker[msg.chat.id]=True
        bot.send_message(msg.chat.id,"Signal skipped ✅")
        return

# PAYMENT
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

# SIGNAL
    if text=="📊 Get Signal":

        if not users.get(uid,{}).get("approved"):
            bot.send_message(msg.chat.id,"🔒 Access Locked")
            return

        kb=ReplyKeyboardMarkup(resize_keyboard=True)
        for p in PAIRS:
            kb.add(p)
        kb.add("⬅ Back")

        bot.send_message(msg.chat.id,"Select Pair",reply_markup=kb)
        return

# PAIR
    if text in PAIRS:
        user_pair[msg.chat.id]=text

        kb=ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add("M1","M5","M15")
        kb.add("⬅ Back")

        bot.send_message(msg.chat.id,f"Pair Selected: {text}",reply_markup=kb)
        return

# TIMEFRAME
    if text in ["M1","M5","M15"]:

        pair=user_pair.get(msg.chat.id)

        result=generate_signal(pair,text)

        if result.get("status")!="success":
            bot.send_message(msg.chat.id,"Signal error")
            return

        kb=ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add("⏭ Skip Signal")
        kb.add("⬅ Back")

        bot.send_message(msg.chat.id,result["signal"],reply_markup=kb)

        Thread(
            target=auto_tracker,
            args=(msg.chat.id,result['pair'],result['signal'],result['timeframe'],result['entry_time'])
        ).start()

        return

# ================= ADMIN PANEL =================

    if text=="⚙ ADMIN PANEL" and msg.chat.id==ADMIN_ID:

        kb=ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add("📊 BOT STATISTICS")
        kb.add("📩 Broadcast")
        kb.add("👥 Pending Users")
        kb.add("👤 All Users")
        kb.add("⬅ Back")

        bot.send_message(msg.chat.id,"ADMIN PANEL",reply_markup=kb)
        return

# STATS
    if text=="📊 BOT STATISTICS" and msg.chat.id==ADMIN_ID:

        total_win=sum(u["win"] for u in stats["users"].values())
        total_loss=sum(u["loss"] for u in stats["users"].values())

        bot.send_message(msg.chat.id,f"""
📊 GLOBAL BOT STATS

WIN: {total_win}
LOSS: {total_loss}

👑 ADMIN
WIN: {stats['admin']['win']}
LOSS: {stats['admin']['loss']}
""")
        return

# BROADCAST
    if text=="📩 Broadcast" and msg.chat.id==ADMIN_ID:
        waiting_broadcast[msg.chat.id]=True
        back_menu(msg.chat.id,"Send broadcast message")
        return

    if msg.chat.id in waiting_broadcast:

        for user in users:
            try:
                bot.copy_message(user,msg.chat.id,msg.message_id)
            except:
                pass

        waiting_broadcast.pop(msg.chat.id)
        main_menu(msg.chat.id)
        return

# PENDING USERS
    if text=="👥 Pending Users" and msg.chat.id==ADMIN_ID:

        pending=[u for u,d in users.items() if not d["approved"]]

        if not pending:
            bot.send_message(msg.chat.id,"No pending users")
            return

        kb=ReplyKeyboardMarkup(resize_keyboard=True)

        for u in pending:
            kb.add(f"✅ Approve {u}")
            kb.add(f"❌ Reject {u}")

        kb.add("⬅ Back")

        bot.send_message(msg.chat.id,"Pending Users",reply_markup=kb)
        return

# APPROVE
    if text.startswith("✅ Approve") and msg.chat.id==ADMIN_ID:

        user=text.split(" ")[2]
        users[user]["approved"]=True
        save_users(users)

        bot.send_message(user,"✅ Payment Approved")
        return

# REJECT
    if text.startswith("❌ Reject") and msg.chat.id==ADMIN_ID:

        user=text.split(" ")[2]
        bot.send_message(user,"❌ Payment Rejected")
        return

# PAYMENT PROOF
    if uid in waiting_payment:

        bot.forward_message(ADMIN_ID,msg.chat.id,msg.message_id)
        waiting_payment.pop(uid)
        return

# ALL USERS
    if text=="👤 All Users" and msg.chat.id==ADMIN_ID:

        vip=[u for u,d in users.items() if d.get("approved")]
        nonvip=[u for u,d in users.items() if not d.get("approved")]

        bot.send_message(msg.chat.id,f"""
👥 USERS

VIP: {len(vip)}
NON VIP: {len(nonvip)}
""")
        return

# ================= REAL SESSION SYSTEM =================

def broadcast_all(message):

    for uid,data in users.items():
        if data.get("approved"):
            try:
                bot.send_message(int(uid),message)
            except:
                pass

import threading

threading.Thread(
    target=session_manager,
    args=(bot, ADMIN_ID),
    daemon=True
).start()

# ================= START BOT =================

bot.infinity_polling(skip_pending=True)
