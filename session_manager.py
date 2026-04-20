import time
import threading
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from pro_engine import generate_signal, PAIRS, get_prices

# ================= SETTINGS =================

TZ = ZoneInfo("Africa/Kigali")

SESSION_TIMES = ["15:55", "18:00", "21:00"]


# ================= BROADCAST =================
def send_all(bot, users, message):

    for uid, data in users.items():
        if data.get("approved"):
            try:
                bot.send_message(int(uid), message)
            except:
                pass


# ================= SMART PAIR FINDER =================
def find_best_pair():

    best_pair = None
    best_conf = -1

    for pair in PAIRS:

        signal = generate_signal(pair, "M1")

        if signal.get("status") != "success":
            continue

        conf = signal.get("confidence", 50)

        if conf > best_conf:
            best_conf = conf
            best_pair = pair

    # fallback → ntizongera kuvuga no opportunity
    if not best_pair:
        best_pair = PAIRS[0]

    return best_pair


# ================= SESSION FLOW =================
def run_session(bot, users, session_time):

    # READY (1 minute before)
    send_all(bot, users,
    "⏰ SESSION READY\nPrepare Traders...")

    time.sleep(60)

    # PAIR SELECTED
    pair = find_best_pair()

    send_all(bot, users,
f"""
📊 Pair Selected: {pair}
🧠 Market Analysis Running...
""")

    # wait until signal time (3 min)
    time.sleep(180)

    # SIGNAL
    signal = generate_signal(pair, "M1")

    if signal.get("status") != "success":
        return

    send_all(bot, users, signal["signal"])

    prices = get_prices(pair, "M1")
    if not prices:
        return

    entry = prices[-1]

    # expiry 1 minute
    time.sleep(60)

    prices2 = get_prices(pair, "M1")
    if not prices2:
        return

    close = prices2[-1]

    if "CALL" in signal["signal"]:
        result = "WIN ✅" if close > entry else "LOSS ❌"
    else:
        result = "WIN ✅" if close < entry else "LOSS ❌"

    send_all(bot, users,
f"""
📊 RESULT

Pair: {pair}
Entry: {entry}
Close: {close}

RESULT: {result}
""")


# ================= SESSION MANAGER =================
def session_manager(bot, users):

    started_today = set()

    while True:

        now = datetime.now(TZ)

        for session in SESSION_TIMES:

            session_dt = datetime.strptime(
                session, "%H:%M"
            ).replace(
                year=now.year,
                month=now.month,
                day=now.day,
                tzinfo=TZ
            )

            ready_dt = session_dt - timedelta(minutes=1)

            # READY ALERT
            if now >= ready_dt and session not in started_today:

                threading.Thread(
                    target=run_session,
                    args=(bot, users, session),
                    daemon=True
                ).start()

                started_today.add(session)

        # reset everyday
        if now.strftime("%H:%M") == "00:01":
            started_today.clear()

        time.sleep(5)
