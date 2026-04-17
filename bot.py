import telebot
import json
import os
import threading
import time
import requests
from telebot.types import ReplyKeyboardMarkup
from pro_engine import generate_signal, PAIRS

TOKEN=os.getenv("BOT_TOKEN")
ADMIN_ID=8448217655

bot=telebot.TeleBot(TOKEN)

PAYMENT_ADDRESS="0xA7123932DF237A24ad8c251502C169d744dd6D41"

waiting_broadcast={}
waiting_payment={}
user_pair={}

# ================= USERS =================

def load_users():
    try:
        return json.load(open("users.json"))
    except:
        return {}

def save_users(d):
    json.dump(d,open("users.json","w"))

users=load_users()

# ================= TRACKER =================

def load_tracker():
    try:
        return json.load(open("tracker.json"))
    except:
        return {"total":0,"win":0,"loss":0}

def save_tracker(d):
    json.dump(d,open("tracker.json","w"))

tracker=load_tracker()

# ================= AUTO WIN TRACK =================

def check_trade(pair,timeframe,direction,entry_price):

    def run():

        tf={"M1":60,"M5":300,"M15":900}

        time.sleep(tf[timeframe]+5)

        r=requests.get(
            f"https://api.twelvedata.com/price?symbol={pair}&apikey=f29c55ce7132437e86f7b025670ec8e4"
        ).json()

        if "price" not in r:
            return

        exit_price=float(r["price"])

        win=False

        if direction=="CALL 📈" and exit_price>entry_price:
            win=True
        if direction=="PUT 📉" and exit_price<entry_price:
            win=True

        tracker["total"]+=1

        if win:
            tracker["win"]+=1
            bot.send_message(ADMIN_ID,f"✅ WIN {pair}")
        else:
            tracker["loss"]+=1
            bot.send_message(ADMIN_ID,f"❌ LOSS {pair}")

        save_tracker(tracker)

    threading.Thread(target=run).start()

# ================= MENU =================

def main_menu(cid):
    kb=ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("📊 Get Signal")
    kb.add("💳 Payment")
    if cid==ADMIN_ID:
        kb.add("⚙ ADMIN PANEL")
    bot.send_message(cid,"Main Menu",reply_markup=kb)

# ================= START =================

@bot.message_handler(commands=["start"])
def start(msg):

    uid=str(msg.chat.id)

    if uid not in users:
        users[uid]={"approved":False}

    if msg.chat.id==ADMIN_ID:
        users[uid]["approved"]=True

    save_users(users)
    main_menu(msg.chat.id)

# ================= HANDLER =================

@bot.message_handler(content_types=["text","photo"])
def messages(msg):

    uid=str(msg.chat.id)
    text=msg.text if msg.content_type=="text" else ""

# PAYMENT
    if text=="💳 Payment":
        waiting_payment[msg.chat.id]=True
        bot.send_message(msg.chat.id,PAYMENT_ADDRESS)
        return

# SIGNAL
    if text=="📊 Get Signal":

        if not users[uid]["approved"]:
            bot.send_message(msg.chat.id,"🔒 Access Locked")
            return

        kb=ReplyKeyboardMarkup(resize_keyboard=True)
        for p in PAIRS:
            kb.add(p)
        bot.send_message(msg.chat.id,"Select Pair",reply_markup=kb)
        return

    if text in PAIRS:
        user_pair[msg.chat.id]=text
        kb=ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add("M1","M5","M15")
        bot.send_message(msg.chat.id,"Select Timeframe",reply_markup=kb)
        return

    if text in ["M1","M5","M15"]:

        pair=user_pair.get(msg.chat.id)
        result=generate_signal(pair,text)

        if result["status"]!="success":
            bot.send_message(msg.chat.id,"Signal error")
            return

        message=f"""
📊 AI SIGNAL

Pair: {result['pair']}
{result['signal']}
Timeframe: {result['timeframe']}
Entry Time: {result['entry_time']}
Accuracy: {result['accuracy']}
"""

        bot.send_message(msg.chat.id,message)

        # AUTO TRACK
        signal_text=result["signal"]
        direction="CALL 📈" if "CALL" in signal_text else "PUT 📉"
        price_line=[l for l in signal_text.split("\n") if "Price" in l][0]
        entry_price=float(price_line.split(":")[1])

        check_trade(pair,text,direction,entry_price)
        return

# ================= ADMIN =================

    if text=="⚙ ADMIN PANEL" and msg.chat.id==ADMIN_ID:

        kb=ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add("📩 Broadcast")
        kb.add("👥 Pending Users")
        kb.add("👤 Total Users")
        kb.add("📈 Win Tracker")

        bot.send_message(msg.chat.id,"ADMIN PANEL",reply_markup=kb)
        return

# BROADCAST
    if text=="📩 Broadcast" and msg.chat.id==ADMIN_ID:
        waiting_broadcast[msg.chat.id]=True
        bot.send_message(msg.chat.id,"Send broadcast")
        return

    if msg.chat.id in waiting_broadcast:

        sent=0
        for u in users:
            try:
                if msg.content_type=="text":
                    bot.send_message(u,msg.text)
                else:
                    bot.send_photo(u,msg.photo[-1].file_id)
                sent+=1
            except:
                pass

        bot.send_message(msg.chat.id,f"Broadcast sent {sent}")
        waiting_broadcast.pop(msg.chat.id)
        return

# TOTAL USERS
    if text=="👤 Total Users" and msg.chat.id==ADMIN_ID:

        vip=sum(1 for u in users.values() if u["approved"])
        locked=len(users)-vip

        bot.send_message(
            msg.chat.id,
            f"""
👥 USERS

VIP: {vip}
Locked: {locked}
Total: {len(users)}
"""
        )
        return

# WIN TRACKER
    if text=="📈 Win Tracker" and msg.chat.id==ADMIN_ID:

        winrate=0
        if tracker["total"]>0:
            winrate=round(tracker["win"]/tracker["total"]*100,2)

        bot.send_message(
            msg.chat.id,
            f"""
📊 PERFORMANCE

Total: {tracker['total']}
Wins: {tracker['win']}
Loss: {tracker['loss']}
Winrate: {winrate}%
"""
        )
        return

# PAYMENT PROOF
    if msg.chat.id in waiting_payment:
        bot.forward_message(ADMIN_ID,msg.chat.id,msg.message_id)
        bot.send_message(msg.chat.id,"Proof sent")
        waiting_payment.pop(msg.chat.id)

bot.infinity_polling(skip_pending=True)
