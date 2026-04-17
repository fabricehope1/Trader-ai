import time
import json
from pro_engine import get_prices

# ================= LOAD SAVE =================

def load_json(file,default):
    try:
        return json.load(open(file))
    except:
        return default

def save_json(file,data):
    json.dump(data,open(file,"w"))

stats=load_json("stats.json",{"win":0,"loss":0})


# ================= TIMEFRAME =================

def tf_seconds(tf):

    if tf=="M1":
        return 60
    if tf=="M5":
        return 300
    if tf=="M15":
        return 900

    return 60


# ================= AUTO TRACKER =================

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

    def tracker():

        # 1️⃣ WAIT PREPARE TIME
        time.sleep(prepare)

        # 2️⃣ WAIT FULL CANDLE
        candle_time=tf_seconds(timeframe)

        time.sleep(candle_time)

        # 3️⃣ BUFFER (avoid fake result)
        time.sleep(5)

        # user skipped?
        if chat_id not in active_signals:
            return

        prices=get_prices(pair,timeframe)

        if not prices or len(prices)<3:
            return

        # ✅ CLOSED CANDLE PRICE
        close_price=prices[-2]

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
Result: {result}

WIN: {stats['win']}
LOSS: {stats['loss']}
""")

    import threading
    threading.Thread(target=tracker).start()
