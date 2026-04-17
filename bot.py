import telebot
import json
import os
import threading
import time
from telebot.types import ReplyKeyboardMarkup
from pro_engine import generate_signal, PAIRS, get_prices

TOKEN=os.getenv("BOT_TOKEN")
ADMIN_ID=8448217655

bot=telebot.TeleBot(TOKEN)

PAYMENT_ADDRESS="0xA7123932DF237A24ad8c251502C169d744dd6D41"

waiting_broadcast={}
waiting_payment={}
user_pair={}
pending_list={}
active_signals={}

# ================= DATABASE =================

def load_json(file,default):
    try:
        return json.load(open(file))
    except:
        return default

def save_json(file,data):
    json.dump(data,open(file,"w"))

users=load_json("users.json",{})
stats=load_json("stats.json",{"win":0,"loss":0})

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

    save_json("users.json",users)
    main_menu(msg.chat.id)

# ================= TIMEFRAME SECONDS =================

def tf_seconds(tf):
    return 60 if tf=="M1" else 300 if tf=="M5" else 900

# ================= TRUE AUTO TRACKER =================

def auto_track(chat_id,pair,signal,entry_price,timeframe,prepare):

    # WAIT ENTRY TIME
    time.sleep(prepare)

    # IF USER SKIPPED
    if chat_id not in active_signals:
        return

    # WAIT FULL CANDLE CLOSE
    time.sleep(tf_seconds(timeframe)+5)

    if chat_id not in active_signals:
        return

    prices=get_prices(pair,timeframe)
    if not prices:
        return

    close_price=prices[-1]

    result="LOSS"

    if "CALL" in signal and close_price>entry_price:
        result="WIN"

    if "PUT" in signal and close_price<entry_price:
        result="WIN"

    if result=="WIN":
        stats["win"]+=1
    else:
        stats["loss"]+=1

    save_json("stats.json",stats)

    active_signals.pop(chat_id,None)

    bot.send_message(chat_id,f"📊 RESULT: {result}")

    bot.send_message(
        ADMIN_ID,
f"""📈 AUTO TRACKER

User: {chat_id}
Pair: {pair}
Signal: {signal}
Result: {result}

TOTAL WIN: {stats['win']}
TOTAL LOSS: {stats['loss']}
""")

# ================= MESSAGE HANDLER =================

@bot.message_handler(content_types=["text","photo"])
def messages(msg):

    uid=str(msg.chat.id)
    text=msg.text if msg.content_type=="text" else ""

# BACK
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
        waiting_payment[msg.chat.id]=True
        back_menu(msg.chat.id,"Send payment screenshot.")
        return

# ================= SIGNAL =================

    if text=="📊 Get Signal":

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
{result['signal']}
Timeframe: {result['timeframe']}
Entry Time: {result['entry_time']}
Accuracy: {result['accuracy']}
"""

            kb=ReplyKeyboardMarkup(resize_keyboard=True)
            kb.add("⏭ Skip Signal")
            kb.add("⬅ Back")

            bot.send_message(msg.chat.id,message,reply_markup=kb)

            entry_price=float(result["signal"].split("Price: ")[1].split("\n")[0])
            prepare=int(result["signal"].split("Prepare: ")[1].split("s")[0])

            active_signals[msg.chat.id]=True

            threading.Thread(
                target=auto_track,
                args=(msg.chat.id,pair,result["signal"],entry_price,text,prepare)
            ).start()

        else:
            bot.send_message(msg.chat.id,"⚠️ Signal error")

        return

# ================= SKIP =================

    if text=="⏭ Skip Signal":

        active_signals.pop(msg.chat.id,None)
        bot.send_message(msg.chat.id,"Signal skipped ✅")
        return

# ================= ADMIN PANEL =================

    if text=="⚙ ADMIN PANEL" and msg.chat.id==ADMIN_ID:

        kb=ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add("📩 Broadcast")
        kb.add("👥 Pending Users")
        kb.add("📊 Win Tracker")
        kb.add("⬅ Back")

        bot.send_message(msg.chat.id,"ADMIN PANEL",reply_markup=kb)
        return

# ================= WIN TRACKER =================

    if text=="📊 Win Tracker" and msg.chat.id==ADMIN_ID:

        total=len(users)
        vip=sum(1 for u in users if users[u]["approved"])

        bot.send_message(
            msg.chat.id,
f"""
📊 BOT STATS

Total Users: {total}
VIP Users: {vip}

WIN: {stats['win']}
LOSS: {stats['loss']}
""")
        return

# ================= BROADCAST =================

    if text=="📩 Broadcast" and msg.chat.id==ADMIN_ID:
        waiting_broadcast[msg.chat.id]=True
        back_menu(msg.chat.id,"Send message/photo/link to broadcast")
        return

# ================= PENDING USERS =================

    if text=="👥 Pending Users" and msg.chat.id==ADMIN_ID:

        pending=[u for u in users if not users[u]["approved"]]

        if not pending:
            bot.send_message(msg.chat.id,"No pending users")
            return

        kb=ReplyKeyboardMarkup(resize_keyboard=True)

        for u in pending:
            kb.add(f"✅ Approve {u}")
            kb.add(f"❌ Reject {u}")

        kb.add("⬅ Back")

        bot.send_message(msg.chat.id,"Pending Users:",reply_markup=kb)
        return

# ================= APPROVE =================

    if text.startswith("✅ Approve"):

        user=text.split(" ")[2]

        users[user]["approved"]=True
        save_json("users.json",users)

        bot.send_message(user,"✅ Payment Approved")
        bot.send_message(msg.chat.id,"Approved")

        return

# ================= REJECT =================

    if text.startswith("❌ Reject"):

        user=text.split(" ")[2]

        bot.send_message(user,"❌ Payment Rejected")
        bot.send_message(msg.chat.id,"Rejected")

        return

# ================= PAYMENT PROOF =================

    if msg.chat.id in waiting_payment:

        bot.forward_message(ADMIN_ID,msg.chat.id,msg.message_id)
        bot.send_message(msg.chat.id,"✅ Proof sent to admin")

        waiting_payment.pop(msg.chat.id)
        return

# ================= BROADCAST SEND =================

    if msg.chat.id in waiting_broadcast:

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

        bot.send_message(msg.chat.id,f"✅ Broadcast sent to {sent} users")

        waiting_broadcast.pop(msg.chat.id)
        main_menu(msg.chat.id)
        return

# ================= START BOT =================

bot.infinity_polling(timeout=60,long_polling_timeout=60,skip_pending=True)
