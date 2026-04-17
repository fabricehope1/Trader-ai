import threading
import time
import json
from pro_engine import get_prices, update_ai

# ================= LOAD / SAVE =================

def load_json(file,default):
    try:
        return json.load(open(file))
    except:
        return default

def save_json(file,data):
    json.dump(data,open(file,"w"))

stats=load_json("stats.json",{"win":0,"loss":0})

# ================= TIMEFRAME SECONDS =================

def tf_seconds(tf):
    if tf=="M1":
        return 60
    elif tf=="M5":
        return 300
    else:
        return 900


# ================= MAIN TRACKER =================

def start_tracker(
        bot,
        ADMIN_ID,
        active_signals,
        chat_id,
        pair,
        signal,
        entry_price,
        timeframe,
        prepare):

    threading.Thread(
        target=track_signal,
        args=(
            bot,
            ADMIN_ID,
            active_signals,
            chat_id,
            pair,
            signal,
            entry_price,
            timeframe,
            prepare),
        daemon=True
    ).start()


# ================= TRACK SIGNAL =================

def track_signal(
        bot,
        ADMIN_ID,
        active_signals,
        chat_id,
        pair,
        signal,
        entry_price,
        timeframe,
        prepare):

    try:

        # WAIT PREPARE + CANDLE CLOSE + BUFFER
        wait_time = prepare + tf_seconds(timeframe) + 5
        time.sleep(wait_time)

        # USER SKIPPED SIGNAL
        if chat_id not in active_signals:
            return

        prices=get_prices(pair,timeframe)

        if not prices:
            return

        # ===== CLOSE CANDLE PRICE =====
        close_price=prices[-1]

        result="LOSS"

        if "CALL" in signal and close_price>entry_price:
            result="WIN"

        if "PUT" in signal and close_price<entry_price:
            result="WIN"

        # ================= SAVE STATS =================

        if result=="WIN":
            stats["win"]+=1
        else:
            stats["loss"]+=1

        save_json("stats.json",stats)

        # ================= AI LEARNING =================

        trend="UP" if "Trend: UP" in signal else "DOWN"

        if "STRONG" in signal:
            strength="STRONG 🔥"
        elif "MEDIUM" in signal:
            strength="MEDIUM ✅"
        else:
            strength="WEAK ⚠️"

        update_ai(pair,trend,strength,result)

        # REMOVE ACTIVE SIGNAL
        active_signals.pop(chat_id,None)

        # ================= USER RESULT =================

        bot.send_message(
            chat_id,
f"""
📊 RESULT CLOSED

Pair: {pair}
Entry: {entry_price}
Close: {close_price}

✅ RESULT: {result}
""")

        # ================= ADMIN REPORT =================

        bot.send_message(
            ADMIN_ID,
f"""
📈 AUTO TRACKER REPORT

User: {chat_id}
Pair: {pair}
Result: {result}

TOTAL WIN: {stats['win']}
TOTAL LOSS: {stats['loss']}
""")

    except Exception as e:
        print("TRACKER ERROR:",e)
