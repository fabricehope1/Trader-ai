import telebot
import json
import os
import threading
import time
from datetime import datetime
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

# ================= AUTO TRACKER =================
trade_history={}

# ================= DATABASE =================

def load_users():
    try:
        return json.load(open("users.json"))
    except:
        return {}

def save_users(data):
    json.dump(data,open("users.json","w"))

users=load_users()

# ================= SAVE RESULTS =================

def save_trade_result(user,pair,result):

    try:
        data=json.load(open("results.json"))
    except:
        data=[]

    data.append({
        "user":user,
        "pair":pair,
        "result":result,
        "time":datetime.now().strftime("%H:%M:%S")
    })

    json.dump(data,open("results.json","w"))

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

# ================= MESSAGE HANDLER =================

@bot.message_handler(content_types=["text","photo","video","document"])
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
        waiting_payment[str(msg.chat.id)]=True
        back_menu(msg.chat.id,"Send payment screenshot.")
        return

# ================= SIGNAL =================

if text=="📊 Get Signal":

    # AUTO ADMIN ACCESS (ADD ONLY)
    if msg.chat.id==ADMIN_ID:
        users[str(msg.chat.id)]={"approved":True}
        save_users(users)

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
{result['signal']}
Timeframe: {result['timeframe']}
Entry Time: {result['entry_time']}
Accuracy: {result['accuracy']}
"""

            # extract prepare seconds automatically
            prepare=int(result["signal"].split("Prepare: ")[1].split("s")[0])

            kb=ReplyKeyboardMarkup(resize_keyboard=True)
            kb.add("✅ Trade Taken","⏭ Skip Signal")
            kb.add("⬅ Back")

            bot.send_message(msg.chat.id,message,reply_markup=kb)

            trade_history[msg.chat.id]={
                "pair":pair,
                "timeframe":text,
                "prepare":prepare
            }

        else:
            bot.send_message(msg.chat.id,"⚠️ Signal error")

        return

# ================= SKIP SIGNAL =================

    if text=="⏭ Skip Signal":

        trade_history.pop(msg.chat.id,None)

        bot.send_message(msg.chat.id,"✅ Signal skipped")
        main_menu(msg.chat.id)
        return

# ================= TRADE TRACKER =================

    if text=="✅ Trade Taken":

        trade=trade_history.get(msg.chat.id)

        if not trade:
            bot.send_message(msg.chat.id,"No active trade")
            return

        bot.send_message(msg.chat.id,"⏳ Waiting entry candle...")

        def track_trade(chat_id,trade):

            prepare=trade["prepare"]

            # wait prepare seconds first
            time.sleep(prepare)

            tf=trade["timeframe"]

            expiry={"M1":60,"M5":300,"M15":900}[tf]

            # wait candle expiry
            time.sleep(expiry+5)

            prices=get_prices(trade["pair"],tf)

            open_price=prices[-2]
            close_price=prices[-1]

            result="WIN ✅" if close_price>open_price else "LOSS ❌"

            bot.send_message(chat_id,f"""
📊 TRADE RESULT

PAIR: {trade['pair']}
RESULT: {result}
""")

            save_trade_result(chat_id,trade["pair"],result)

            trade_history.pop(chat_id,None)

        threading.Thread(
            target=track_trade,
            args=(msg.chat.id,trade)
        ).start()

        return

# ================= ADMIN PANEL =================

    if text=="⚙ ADMIN PANEL" and msg.chat.id==ADMIN_ID:

        kb=ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add("📩 Broadcast")
        kb.add("👥 Pending Users")
        kb.add("📊 Trade Results")
        kb.add("⬅ Back")

        bot.send_message(msg.chat.id,"ADMIN PANEL",reply_markup=kb)
        return

# ================= ADMIN RESULTS =================

    if text=="📊 Trade Results" and msg.chat.id==ADMIN_ID:

        try:
            data=json.load(open("results.json"))
        except:
            bot.send_message(msg.chat.id,"No results yet")
            return

        text="📊 LAST TRADES\n\n"

        for r in data[-10:]:
            text+=f"{r['pair']} | {r['result']} | {r['time']}\n"

        bot.send_message(msg.chat.id,text)
        return

# ================= PAYMENT PROOF =================

    if str(msg.chat.id) in waiting_payment:

        bot.forward_message(
            ADMIN_ID,
            msg.chat.id,
            msg.message_id
        )

        bot.send_message(msg.chat.id,"✅ Proof sent to admin")

        waiting_payment.pop(str(msg.chat.id))
        return

# ================= START BOT =================

bot.infinity_polling(
    timeout=60,
    long_polling_timeout=60,
    skip_pending=True
)
