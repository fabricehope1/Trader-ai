# ================= AUTO TRACKER V6 =================

import time
import requests
from pro_engine import ai_learn

API_KEY="f29c55ce7132437e86f7b025670ec8e4"


def get_last_close(pair):

    symbol=pair.replace("/","")

    url=f"https://api.twelvedata.com/time_series?symbol={symbol}&interval=1min&outputsize=2&apikey={API_KEY}"

    r=requests.get(url).json()

    if "values" not in r:
        return None

    closes=[float(c["close"]) for c in r["values"]]

    closes.reverse()

    return closes[-1]


# ================= TRACKER =================

def start_tracker(
    bot,
    ADMIN_ID,
    active_signals,
    chat_id,
    pair,
    signal,
    entry_price,
    text,
    prepare
):

    active_signals[chat_id]=True

    entry_close=get_last_close(pair)

    if not entry_close:
        return

    # wait candle close (1min)
    time.sleep(60)

    result_close=get_last_close(pair)

    if not result_close:
        return

    win=False

    if signal=="BUY" and result_close>entry_close:
        win=True

    if signal=="SELL" and result_close<entry_close:
        win=True

    result="WIN" if win else "LOSS"

    # ===== AI LEARNING =====
    ai_learn(signal,result)

    msg=f"""
📊 RESULT

Pair: {pair}
Signal: {signal}

Entry Candle Close: {entry_close}
Result Candle Close: {result_close}

✅ {result}
"""

    bot.send_message(chat_id,msg)

    active_signals.pop(chat_id,None)
