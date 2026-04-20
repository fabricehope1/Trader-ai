import telebot
import json
import os
import time
from threading import Thread
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from telebot.types import ReplyKeyboardMarkup

from pro_engine import generate_signal, PAIRS, get_prices

TOKEN=os.getenv("BOT_TOKEN")

ADMIN_ID=8448217655

bot=telebot.TeleBot(TOKEN)

PAYMENT_ADDRESS="0xA7123932DF237A24ad8c251502C169d744dd6D41"

waiting_broadcast={}
waiting_payment={}
user_pair={}
skip_tracker={}

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

    tz=ZoneInfo("Africa/Kigali")

    while True:
        if skip_tracker.get(chat_id):
            skip_tracker.pop(chat_id)
            return

        now=datetime.now(tz).strftime("%H:%M:%S")
        if now>=entry_time:
            break
        time.sleep(1)

    prices=get_prices(pair,timeframe)
    if not prices:
        return

    entry_price=prices[-1]

    tf_seconds={"M1":60,"M5":300,"M15":900}

    for _ in range(tf_seconds.get(timeframe,60)):
        if skip_tracker.get(chat_id):
            skip_tracker.pop(chat_id)
            return
        time.sleep(1)

    prices_after=get_prices(pair,timeframe)
    if not prices_after:
        return

    close_price=prices_after[-1]

    result="WIN" if (
        ("CALL" in signal and close_price>entry_price)
        or ("PUT" in signal and close_price<entry_price)
    ) else "LOSS"

    uid=str(chat_id)

    if uid not in stats["users"]:
        stats["users"][uid]={"win":0,"loss":0}

    if result=="WIN":
        stats["users"][uid]["win"]+=1
        if chat_id==ADMIN_ID:
            stats["admin"]["win"]+=1
    else:
        stats["users"][uid]["loss"]+=1
        if chat_id==ADMIN_ID:
            stats["admin"]["loss"]+=1

    save_stats(stats)

    bot.send_message(chat_id,f"""
📊 SIGNAL RESULT

Pair: {pair}
Entry: {entry_price}
Close: {close_price}

RESULT: {result}
""")

# ================= SNIPER SESSION ENGINE =================

def sniper_sessions():

    tz=ZoneInfo("Africa/Kigali")

    sessions=["08:00","15:00"]

    while True:

        now=datetime.now(tz).strftime("%H:%M")

        if now in sessions:

            pair=PAIRS[int(time.time()) % len(PAIRS)]

            for uid,data in users.items():

                if not data.get("approved"):
                    continue

                bot.send_message(uid,f"""
🎯 SNIPER SESSION STARTED

Selected Pair: {pair}
Analysis running...
""")

            time.sleep(180)

            result=generate_signal(pair,"M1")

            if result.get("status")!="success":
                continue

            for uid,data in users.items():

                if not data.get("approved"):
                    continue

                bot.send_message(uid,f"""
📊 MARKET ANALYSIS

Pair: {pair}
Trend confirmed
Momentum verified
Liquidity detected

Direction: {result['signal']}
Reason: Smart Money + Trend Alignment
Entry Time: {result['entry_time']}
""")

            time.sleep(60)

            for uid,data in users.items():

                if not data.get("approved"):
                    continue

                bot.send_message(uid,f"""
🚀 SNIPER SIGNAL

Pair: {pair}
Signal: {result['signal']}
Entry: {result['entry_time']}
Timeframe: M1
""")

            for i in range(4):

                time.sleep(600)

                result=generate_signal(pair,"M1")

                for uid,data in users.items():
                    if not data.get("approved"):
                        continue

                    bot.send_message(uid,f"""
⚡ SNIPER SIGNAL {i+2}/5

Pair: {pair}
Signal: {result['signal']}
Entry: {result['entry_time']}
Timeframe: M1
""")

            time.sleep(60)

        time.sleep(20)

Thread(target=sniper_sessions,daemon=True).start()

# ================= MESSAGE HANDLER =================

@bot.message_handler(content_types=["text","photo","video","document"])
def messages(msg):

    uid=str(msg.chat.id)
    text=msg.text if msg.content_type=="text" else ""

    if text=="⬅ Back":
        main_menu(msg.chat.id)
        return

    if text=="⏭ Skip Signal":
        skip_tracker[msg.chat.id]=True
        bot.send_message(msg.chat.id,"Signal skipped ✅")
        return

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

    if text in PAIRS:

        user_pair[msg.chat.id]=text

        kb=ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add("M1","M5","M15")
        kb.add("⬅ Back")

        bot.send_message(msg.chat.id,
            f"Pair Selected: {text}\nSelect Timeframe",
            reply_markup=kb)
        return

    if text in ["M1","M5","M15"]:

        pair=user_pair.get(msg.chat.id)

        if not pair:
            bot.send_message(msg.chat.id,"Select pair first")
            return

        result=generate_signal(pair,text)

        if result.get("status")!="success":
            bot.send_message(msg.chat.id,"Signal error")
            return

        kb=ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add("⏭ Skip Signal")
        kb.add("⬅ Back")

        message=f"""
📊 AI SIGNAL

Pair: {result['pair']}
Signal: {result['signal']}
Timeframe: {result['timeframe']}
Entry Time: {result['entry_time']}
Accuracy: {result['accuracy']}
"""

        bot.send_message(msg.chat.id,message,reply_markup=kb)

        Thread(
            target=auto_tracker,
            args=(
                msg.chat.id,
                result['pair'],
                result['signal'],
                result['timeframe'],
                result['entry_time']
            )
        ).start()

        return

    # ===== ADMIN PANEL (UNCHANGED) =====
    if text=="⚙ ADMIN PANEL" and msg.chat.id==ADMIN_ID:

        kb=ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add("📊 BOT STATISTICS")
        kb.add("📩 Broadcast")
        kb.add("👥 Pending Users")
        kb.add("👤 All Users")
        kb.add("⬅ Back")

        bot.send_message(msg.chat.id,"ADMIN PANEL",reply_markup=kb)
        return

    if text=="📊 BOT STATISTICS" and msg.chat.id==ADMIN_ID:

        total_win=sum(u["win"] for u in stats["users"].values())
        total_loss=sum(u["loss"] for u in stats["users"].values())

        admin_win=stats["admin"]["win"]
        admin_loss=stats["admin"]["loss"]

        bot.send_message(msg.chat.id,f"""
📊 GLOBAL BOT STATS

USERS TOTAL
WIN: {total_win}
LOSS: {total_loss}

👑 ADMIN STATS
WIN: {admin_win}
LOSS: {admin_loss}
""")
        return

    if text=="📩 Broadcast" and msg.chat.id==ADMIN_ID:
        waiting_broadcast[msg.chat.id]=True
        back_menu(msg.chat.id,"Send broadcast message")
        return

    if msg.chat.id in waiting_broadcast:

        sent=0

        for user in users:
            try:
                bot.copy_message(
                    chat_id=user,
                    from_chat_id=msg.chat.id,
                    message_id=msg.message_id
                )
                sent+=1
            except:
                pass

        bot.send_message(msg.chat.id,f"Broadcast sent to {sent} users")

        waiting_broadcast.pop(msg.chat.id)
        main_menu(msg.chat.id)
        return

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

    if text.startswith("✅ Approve") and msg.chat.id==ADMIN_ID:

        user=text.split(" ")[2]

        users[user]["approved"]=True
        save_users(users)

        bot.send_message(user,"✅ Payment Approved")
        bot.send_message(msg.chat.id,f"Approved {user}")
        return

    if text.startswith("❌ Reject") and msg.chat.id==ADMIN_ID:

        user=text.split(" ")[2]

        bot.send_message(user,"❌ Payment Rejected")
        bot.send_message(msg.chat.id,f"Rejected {user}")
        return

    if uid in waiting_payment:

        bot.forward_message(
            ADMIN_ID,
            msg.chat.id,
            msg.message_id
        )

        bot.send_message(msg.chat.id,"Proof sent to admin")

        waiting_payment.pop(uid)
        return

    if text=="👤 All Users" and msg.chat.id==ADMIN_ID:

        vip=[]
        nonvip=[]

        for uid,data in users.items():
            if data.get("approved"):
                vip.append(uid)
            else:
                nonvip.append(uid)

        message=f"""
👥 USERS LIST

✅ VIP USERS: {len(vip)}
❌ NON VIP USERS: {len(nonvip)}

------ VIP ------
{" ".join(vip) if vip else "None"}

------ NON VIP ------
{" ".join(nonvip) if nonvip else "None"}
"""

        bot.send_message(msg.chat.id,message)
        return

# ================= START BOT =================

bot.infinity_polling(
    timeout=60,
    long_polling_timeout=60,
    skip_pending=True
    )
