import time
import threading
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from pro_engine import generate_signal, PAIRS, get_prices

TZ = ZoneInfo("Africa/Kigali")

# ===== SETTINGS =====
SIGNALS_PER_SESSION = 5
SIGNAL_INTERVAL = 180   # 3 min hagati ya signals


# ================= BROADCAST =================
def send_all(bot, users, message):

    for uid, data in users.items():
        if data.get("approved"):
            try:
                bot.send_message(int(uid), message)
            except:
                pass


# ================= ONE SESSION =================
def run_signal_cycle(bot, users):

    pair = PAIRS[0]   # ntabwo ari random

    # READY
    send_all(bot, users,
f"""
⏰ SESSION READY

Prepare Traders...
"""
    )

    time.sleep(60)

    # PAIR SELECTED
    send_all(bot, users,
f"""
🚀 SESSION STARTED

📊 Pair: {pair}
🧠 AI Market Analysis Running...
"""
    )

    time.sleep(180)

    # ===== SIGNAL LOOP =====
    for i in range(SIGNALS_PER_SESSION):

        signal = generate_signal(pair, "M1")

        if signal.get("status") != "success":
            continue

        signal_text = signal["signal"]

        # SEND SIGNAL
        send_all(bot, users, signal_text)

        prices = get_prices(pair, "M1")
        if not prices:
            continue

        entry = prices[-1]

        # ENTRY TIME (1 minute)
        time.sleep(60)

        prices2 = get_prices(pair, "M1")
        if not prices2:
            continue

        close = prices2[-1]

        # RESULT CHECK
        if "CALL" in signal_text:
            result = "WIN ✅" if close > entry else "LOSS ❌"
        else:
            result = "WIN ✅" if close < entry else "LOSS ❌"

        send_all(bot, users,
f"""
📊 RESULT

Entry: {entry}
Close: {close}

🏁 RESULT: {result}
"""
        )

        # WAIT NEXT SIGNAL
        if i < SIGNALS_PER_SESSION - 1:
            time.sleep(SIGNAL_INTERVAL)


# ================= SESSION MANAGER =================
def run_session(bot, users):

    SESSION_TIMES = ["16:40", "18:00", "21:00"]

    done_today = set()

    while True:

        now = datetime.now(TZ).strftime("%H:%M")

        for session in SESSION_TIMES:

            if now == session and session not in done_today:

                threading.Thread(
                    target=run_signal_cycle,
                    args=(bot, users),
                    daemon=True
                ).start()

                done_today.add(session)

        # reset everyday
        if now == "00:01":
            done_today.clear()

        time.sleep(10)
