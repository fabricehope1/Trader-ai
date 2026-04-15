import telebot
import json
import os
from pro_engine import get_price

TOKEN = os.getenv("BOT_TOKEN")

ADMIN_ID = 8590363710   # chat id yawe

bot = telebot.TeleBot(TOKEN)

PAIRS = ["EUR/USD","USD/JPY","GBP/USD","USD/CHF"]
TIMEFRAMES = ["1min","5min","15min"]

# ---------- DATABASE ----------

def load_users():
    try:
        return json.load(open("users.json"))
    except:
        return {}

def save_users(data):
    json.dump(data,open("users.json","w"))

users = load_users()

# ---------- MENUS ----------

def main_menu(uid):
    kb = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("📊 Get Signal")
    kb.add("💳 Payment")
    if uid == ADMIN_ID:
        kb.add("⚙ ADMIN PANEL")
    return kb

# ---------- START ----------

@bot.message_handler(commands=["start"])
def start(m):
    uid=str(m.chat.id)

    if uid not in users:
        users[uid]={"approved":False}
        save_users(users)

    bot.send_message(m.chat.id,"Main Menu",reply_markup=main_menu(m.chat.id))

# ---------- PAYMENT ----------

@bot.message_handler(func=lambda m:m.text=="💳 Payment")
def payment(m):

    address="USDT_ADDRESS_HERE"

    kb=telebot.types.InlineKeyboardMarkup()
    kb.add(telebot.types.InlineKeyboardButton(
        "Copy Address",
        callback_data="copy"))

    bot.send_message(
        m.chat.id,
        f"Send payment to:\n`{address}`",
        parse_mode="Markdown",
        reply_markup=kb
    )

# ---------- COPY ----------

@bot.callback_query_handler(func=lambda c:c.data=="copy")
def copy(c):
    bot.answer_callback_query(c.id,"Address copied!")

# ---------- SELECT PAIR ----------

@bot.message_handler(func=lambda m:m.text=="📊 Get Signal")
def select_pair(m):

    uid=str(m.chat.id)

    if not users[uid]["approved"]:
        bot.send_message(m.chat.id,"🔒 Access Locked")
        return

    kb=telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    for p in PAIRS:
        kb.add(p)
    kb.add("⬅ Back")

    bot.send_message(m.chat.id,"Select Pair",reply_markup=kb)

# ---------- PAIR ----------

@bot.message_handler(func=lambda m:m.text in PAIRS)
def select_tf(m):

    users[str(m.chat.id)]["pair"]=m.text
    save_users(users)

    kb=telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    for t in TIMEFRAMES:
        kb.add(t)
    kb.add("⬅ Back")

    bot.send_message(m.chat.id,"Select Timeframe",reply_markup=kb)

# ---------- TIMEFRAME ----------

@bot.message_handler(func=lambda m:m.text in TIMEFRAMES)
def send_signal(m):

    uid=str(m.chat.id)

    pair=users[uid]["pair"]
    tf=m.text

    data=get_price(pair,tf)

    if not data:
        bot.send_message(m.chat.id,"Market Error ❌")
        return

    msg=f"""
🔥 LIVE AI SIGNAL

PAIR: {pair}
DIRECTION: {data['direction']}
ENTRY: NOW
EXPIRY: {tf}
"""

    bot.send_message(m.chat.id,msg,reply_markup=main_menu(m.chat.id))

# ---------- BACK ----------

@bot.message_handler(func=lambda m:m.text=="⬅ Back")
def back(m):
    bot.send_message(m.chat.id,"Main Menu",reply_markup=main_menu(m.chat.id))

# ---------- ADMIN PANEL ----------

@bot.message_handler(func=lambda m:m.text=="⚙ ADMIN PANEL")
def admin(m):

    if m.chat.id!=ADMIN_ID:
        return

    kb=telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("✅ Approve User")
    kb.add("📢 Broadcast")
    kb.add("⬅ Back")

    bot.send_message(m.chat.id,"ADMIN PANEL",reply_markup=kb)

# ---------- APPROVE ----------

@bot.message_handler(func=lambda m:m.text=="✅ Approve User")
def ask_id(m):
    bot.send_message(m.chat.id,"Send User ID")

    bot.register_next_step_handler(m,approve)

def approve(m):
    uid=m.text
    users[uid]["approved"]=True
    save_users(users)

    bot.send_message(m.chat.id,"User Approved ✅")

# ---------- BROADCAST ----------

@bot.message_handler(func=lambda m:m.text=="📢 Broadcast")
def ask_bc(m):
    bot.send_message(m.chat.id,"Send broadcast message")
    bot.register_next_step_handler(m,send_bc)

def send_bc(m):
    for uid in users:
        try:
            bot.send_message(uid,m.text)
        except:
            pass

    bot.send_message(m.chat.id,"Broadcast Sent ✅")

bot.infinity_polling()
