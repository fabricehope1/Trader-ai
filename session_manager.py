import time
import threading
from datetime import datetime
from zoneinfo import ZoneInfo

from pro_engine import generate_signal, PAIRS, get_prices

TZ = ZoneInfo("Africa/Kigali")

SIGNALS_PER_SESSION = 5


# ================= SEND =================
def send_all(bot, users, message):

    for uid,data in users.items():
        if data.get("approved"):
            try:
                bot.send_message(int(uid), message)
            except:
                pass


# ================= AI MARKET SCANNER =================
def ai_find_trade():

    best_pair=None
    best_signal=None
    best_score=0

    for pair in PAIRS:

        signal=generate_signal(pair,"M1")

        if signal.get("status")!="success":
            continue

        confidence=signal.get("confidence",0)

        # PRO FILTERS
        if confidence < 70:
            continue

        prices=get_prices(pair,"M1")
        if not prices:
            continue

        volatility=max(prices[-5:])-min(prices[-5:])

        score=confidence+(volatility*10000)

        if score>best_score:
            best_score=score
            best_pair=pair
            best_signal=signal

    return best_pair,best_signal


# ================= PRO SESSION =================
def run_session(bot,users):

    send_all(bot,users,"🚀 PRO AI SESSION STARTED")

    signals_sent=0

    while signals_sent < SIGNALS_PER_SESSION:

        send_all(bot,users,
        f"🧠 Analysis #{signals_sent+1}\nAI scanning market...")

        pair,signal=ai_find_trade()

        # if market bad → wait and retry
        if not pair:
            send_all(bot,users,"⚠️ Market weak... waiting better setup")
            time.sleep(60)
            continue

        direction="CALL 📈" if "CALL" in signal["signal"] else "PUT 📉"

        send_all(bot,users,
f"""
🔥 PRO SIGNAL #{signals_sent+1}

Pair: {pair}
Direction: {direction}
Confidence: {signal.get("confidence","--")}%

⏳ Prepare...
Entry Next Minute
"""
)

        # ENTRY WAIT
        time.sleep(60)

        send_all(bot,users,f"🚨 ENTER NOW\n{pair}\n{direction}")

        prices=get_prices(pair,"M1")
        if not prices:
            continue

        entry=prices[-1]

        # RESULT WAIT
        time.sleep(60)

        prices2=get_prices(pair,"M1")
        if not prices2:
            continue

        close=prices2[-1]

        if "CALL" in direction:
            result="WIN ✅" if close>entry else "LOSS ❌"
        else:
            result="WIN ✅" if close<entry else "LOSS ❌"

        send_all(bot,users,
f"""
📊 RESULT #{signals_sent+1}

Pair: {pair}
Entry: {entry}
Close: {close}

RESULT: {result}
"""
)

        signals_sent+=1

        # AI cooldown (avoid overtrading)
        time.sleep(60)

    send_all(bot,users,"✅ PRO SESSION FINISHED")


# ================= SESSION MANAGER =================
def session_manager(bot,users):

    SESSION_TIMES=["15:00","18:00","21:00"]

    started_today=set()

    while True:

        now=datetime.now(TZ).strftime("%H:%M")

        for session in SESSION_TIMES:

            if now==session and session not in started_today:

                threading.Thread(
                    target=run_session,
                    args=(bot,users),
                    daemon=True
                ).start()

                started_today.add(session)

        if now=="00:01":
            started_today.clear()

        time.sleep(20)
