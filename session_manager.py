import time
import threading
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from pro_engine import generate_signal, PAIRS, get_prices

TZ = ZoneInfo("Africa/Kigali")

SESSION_TIMES = ["17:05", "19:00", "21:00"]

SIGNALS_PER_SESSION = 5
SIGNAL_INTERVAL = 10   # minutes hagati ya signals


# ================= SEND ALL =================
def send_all(bot, users, message):

    for uid, data in users.items():
        if data.get("approved"):
            try:
                bot.send_message(int(uid), message)
            except:
                pass


# ================= FIND BEST PAIR =================
def find_best_pair():

    best_pair = None
    best_signal = None
    best_conf = -1

    for pair in PAIRS:

        signal = generate_signal(pair, "M1")

        if signal.get("status") != "success":
            continue

        conf = signal.get("confidence", 50)

        if conf > best_conf:
            best_conf = conf
            best_pair = pair
            best_signal = signal

    return best_pair, best_signal


# ================= SINGLE SIGNAL FLOW =================
def run_signal(bot, users, number):

    send_all(bot, users,
f"🧠 Analysis #{number}\nScanning Market...")

    pair, signal = find_best_pair()

    if not pair:
        send_all(bot, users, "❌ No opportunity found.")
        return

    # prepare
    now = datetime.now(TZ)
    entry_time = now + timedelta(minutes=1)

    send_all(bot, users,
f"""
📊 SIGNAL #{number}

Pair: {pair}
Confidence: {signal['confidence']}%

⏳ Prepare...
Entry At: {entry_time.strftime('%H:%M')}
""")

    # wait entry
    while datetime.now(TZ) < entry_time:
        time.sleep(1)

    send_all(bot, users,
f"🔥 ENTRY NOW → {signal['signal']}")

    prices = get_prices(pair, "M1")
    if not prices:
        return

    entry_price = prices[-1]

    # expiry
    expiry = datetime.now(TZ) + timedelta(minutes=1)

    while datetime.now(TZ) < expiry:
        time.sleep(1)

    prices2 = get_prices(pair, "M1")
    if not prices2:
        return

    close_price = prices2[-1]

    if "CALL" in signal["signal"]:
        result = "WIN ✅" if close_price > entry_price else "LOSS ❌"
    else:
        result = "WIN ✅" if close_price < entry_price else "LOSS ❌"

    send_all(bot, users,
f"""
📊 RESULT #{number}

Pair: {pair}
Entry: {entry_price}
Close: {close_price}

RESULT: {result}
""")


# ================= SESSION =================
def run_session(bot, users, session_time):

    send_all(bot, users,
"🚀 SESSION STARTED")

    base_time = session_time

    for i in range(SIGNALS_PER_SESSION):

        signal_time = base_time + timedelta(minutes=i * SIGNAL_INTERVAL)

        # wait signal time
        while datetime.now(TZ) < signal_time:
            time.sleep(1)

        run_signal(bot, users, i + 1)

    send_all(bot, users, "✅ SESSION FINISHED")


# ================= SESSION MANAGER =================
def session_manager(bot, users):

    started_today = set()
    ready_alert = set()

    while True:

        now = datetime.now(TZ)

        for session in SESSION_TIMES:

            session_time = datetime.strptime(
                session, "%H:%M"
            ).replace(
                year=now.year,
                month=now.month,
                day=now.day,
                tzinfo=TZ
            )

            ready_time = session_time - timedelta(minutes=1)

            # READY ALERT
            if now >= ready_time and session not in ready_alert:

                send_all(bot, users,
"⏰ SESSION STARTING SOON\nBe Ready Traders...")

                ready_alert.add(session)

            # START SESSION
            if now >= session_time and session not in started_today:

                threading.Thread(
                    target=run_session,
                    args=(bot, users, session_time),
                    daemon=True
                ).start()

                started_today.add(session)

        # RESET DAILY
        if now.strftime("%H:%M") == "00:01":
            started_today.clear()
            ready_alert.clear()

        time.sleep(5)
