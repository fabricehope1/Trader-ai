import telebot
import json
import os
from telebot.types import ReplyKeyboardMarkup
from pro_engine import generate_signal, PAIRS

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 8448217655

bot = telebot.TeleBot(TOKEN)

PAYMENT_ADDRESS = "0xA7123932DF237A24ad8c251502C169d744dd6D41"

waiting_broadcast = {}
waiting_payment = {}
user_pair = {}
pending_list = {}

# ================= DATABASE =================

def load_users():
    try:
        return json.load(open("users.json"))
    except:
        return {}

def save_users(data):
    json.dump(data, open("users.json", "w"))

users = load_users()

# ================= MENUS =================

def main_menu(chat_id):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("📊 Get Signal")
    kb.add("💳 Payment")

    if chat_id == ADMIN_ID:
        kb.add("⚙ ADMIN PANEL")

    bot.send_message(chat_id, "Main Menu", reply_markup=kb)

def back_menu(chat_id, text):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("⬅ Back")
    bot.send_message(chat_id, text, reply_markup=kb)

# ================= START =================

@bot.message_handler(commands=["start"])
def start(msg):

    uid = str(msg.chat.id)

    if uid not in users:
        users[uid] = {"approved": False}

    if msg.chat.id == ADMIN_ID:
        users[uid]["approved"] = True

    save_users(users)
    main_menu(msg.chat.id)

# ================= MESSAGE HANDLER =================

@bot.message_handler(content_types=["text", "photo"])
def messages(msg):

    uid = str(msg.chat.id)
    text = msg.text if msg.content_type == "text" else ""

    # BACK
    if text == "⬅ Back":
        main_menu(msg.chat.id)
        return

# ================= PAYMENT =================

    if text == "💳 Payment":

        kb = ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add("📋 Copy Address")
        kb.add("📤 Upload Payment Proof")
        kb.add("⬅ Back")

        bot.send_message(
            msg.chat.id,
            f"Send USDT BEP20 Payment:\n\n{PAYMENT_ADDRESS}",
            reply_markup=kb)
        return

    if text == "📋 Copy Address":
        bot.send_message(msg.chat.id, PAYMENT_ADDRESS)
        return

    if text == "📤 Upload Payment Proof":
        waiting_payment[msg.chat.id] = True
        back_menu(msg.chat.id, "Send payment screenshot.")
        return

# ================= SIGNAL =================

    if text == "📊 Get Signal":

        if not users[uid]["approved"]:
            bot.send_message(msg.chat.id, "🔒 Access Locked")
            return

        kb = ReplyKeyboardMarkup(resize_keyboard=True)

        for p in PAIRS:
            kb.add(p)

        kb.add("⬅ Back")

        bot.send_message(msg.chat.id, "Select Pair", reply_markup=kb)
        return

# ================= PAIR =================

    if text in PAIRS:

        user_pair[msg.chat.id] = text

        kb = ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add("M1", "M5", "M15")
        kb.add("⬅ Back")

        bot.send_message(
            msg.chat.id,
            f"Pair Selected: {text}\nSelect Timeframe",
            reply_markup=kb)
        return

# ================= TIMEFRAME (FIXED) =================

    if text in ["M1", "M5", "M15"]:

        pair = user_pair.get(msg.chat.id)

        if not pair:
            bot.send_message(msg.chat.id, "⚠️ Select pair first")
            return

        timeframe = text

        result = generate_signal(pair, timeframe)

        if result.get("status") == "success":

            message = f"""
📊 AI SIGNAL

Pair: {result['pair']}
Signal: {result['signal']}
Timeframe: {result['timeframe']}
Entry Time: {result['entry_time']}
Accuracy: {result['accuracy']}
"""

            bot.send_message(msg.chat.id, message)

        elif result.get("status") == "wait":
            bot.send_message(msg.chat.id, result["message"])

        else:
            bot.send_message(msg.chat.id, "⚠️ Signal error")

        return

# ================= ADMIN PANEL =================

    if text == "⚙ ADMIN PANEL" and msg.chat.id == ADMIN_ID:

        kb = ReplyKeyboardMarkup(resize_keyboard=True)
        kb.add("📩 Broadcast")
        kb.add("👥 Pending Users")
        kb.add("⬅ Back")

        bot.send_message(msg.chat.id, "ADMIN PANEL", reply_markup=kb)
        return

# ================= BROADCAST =================

    if text == "📩 Broadcast" and msg.chat.id == ADMIN_ID:
        waiting_broadcast[msg.chat.id] = True
        back_menu(msg.chat.id, "Send message/photo/link to broadcast")
        return

# ================= PENDING USERS =================

    if text == "👥 Pending Users" and msg.chat.id == ADMIN_ID:

        pending = []

        for user, data in users.items():
            if not data["approved"]:
                pending.append(user)

        if not pending:
            bot.send_message(msg.chat.id, "No pending users")
            return

        kb = ReplyKeyboardMarkup(resize_keyboard=True)

        for u in pending:
            kb.add(f"✅ Approve {u}")
            kb.add(f"❌ Reject {u}")

        kb.add("⬅ Back")

        bot.send_message(msg.chat.id, "Pending Users:", reply_markup=kb)
        return

# ================= APPROVE =================

    if text.startswith("✅ Approve") and msg.chat.id == ADMIN_ID:

        user = text.split(" ")[2]

        if user in users:
            users[user]["approved"] = True
            save_users(users)

            bot.send_message(user, "✅ Payment Approved. Access Granted.")
            bot.send_message(msg.chat.id, f"Approved {user}")
        return

# ================= REJECT =================

    if text.startswith("❌ Reject") and msg.chat.id == ADMIN_ID:

        user = text.split(" ")[2]

        if user in users:
            bot.send_message(user, "❌ Payment Rejected")
            bot.send_message(msg.chat.id, f"Rejected {user}")
        return

# ================= PAYMENT PROOF =================

    if msg.chat.id in waiting_payment:

        bot.forward_message(ADMIN_ID, msg.chat.id, msg.message_id)
        bot.send_message(msg.chat.id, "✅ Proof sent to admin")

        waiting_payment.pop(msg.chat.id)
        return

# ================= BROADCAST SEND =================

    if msg.chat.id in waiting_broadcast:

        sent = 0

        for user in users:
            try:
                if msg.content_type == "text":
                    bot.send_message(user, msg.text)
                else:
                    bot.send_photo(user, msg.photo[-1].file_id, caption=msg.caption)
                sent += 1
            except:
                pass

        bot.send_message(msg.chat.id, f"✅ Broadcast sent to {sent} users")

        waiting_broadcast.pop(msg.chat.id)
        main_menu(msg.chat.id)
        return

# ================= RUN BOT =================

bot.infinity_polling(
    timeout=60,
    long_polling_timeout=60,
    skip_pending=True
        )
