import time
import threading
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from pro_engine import generate_signal, PAIRS, get_prices

# ================= SETTINGS =================

TZ = ZoneInfo("Africa/Kigali")

# igihe session zitangirira
SESSION_TIMES = ["17:10", "19:00", "21:00"]

SIGNALS_PER_SESSION = 5      # signals 5 muri session
SIGNAL_INTERVAL = 600        # 10 minutes hagati ya signals
EXPIRY_SECONDS = 60          # M1 expiry


# ================= SEND TO ALL USERS =================
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
    best_confidence = -1

    for pair in PAIRS:

        signal = generate_signal(pair, "M1")

        if signal.get("status") != "success":
            continue

        confidence = signal.get("confidence", 50)

        if confidence > best_confidence:
            best_confidence = confidence
            best_pair = pair

    if not best_pair:
        best_pair = PAIRS[0]

    return best_pair


# ================= RUN FULL SESSION =================
def run_session(bot, users):

    # READY MESSAGE
    send_all(bot, users,
"""
⏰ SESSION STARTED
🧠 Scanning Market...
Finding Best Pair...
""")

    pair = find_best_pair()

    send_all(bot, users,
f"""
🔥 BEST PAIR SELECTED
PAIR: {pair}

Market Analysis Running...
""")

    # wait analysis (3 minutes)
    time.sleep(180)

    # ===== SIGNAL LOOP =====
    for i in range(SIGNALS_PER_SESSION):

        signal = generate_signal(pair, "M1")

        if signal.get("status") != "success":
            continue

        signal_text = signal["signal"]

        send_all(bot, users, signal_text)

        prices = get_prices(pair, "M1")
        if not prices:
            continue

        entry_price = prices[-1]

        # WAIT EXPIRY
        time.sleep(EXPIRY_SECONDS)

        prices_after = get_prices(pair, "M1")
        if not prices_after:
            continue

        close_price = prices_after[-1]

        # RESULT LOGIC
        if "CALL" in signal_text:
            result = "WIN ✅" if close_price > entry_price else "LOSS ❌"
        else:
            result = "WIN ✅" if close_price < entry_price else "LOSS ❌"

        send_all(bot, users,
f"""
📊 SIGNAL RESULT

Pair: {pair}
Entry: {entry_price}
Close: {close_price}

RESULT: {result}
"""
        )

        # WAIT NEXT SIGNAL
        if i < SIGNALS_PER_SESSION - 1:
            time.sleep(SIGNAL_INTERVAL)

    send_all(bot, users, "✅ SESSION FINISHED")


# ================= SESSION MANAGER =================
def session_manager(bot, users):

    started_today = set()
    ready_alert = set()

    print("✅ SESSION MANAGER STARTED")

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
"""
⏰ SESSION STARTING SOON
Be Ready Traders...
""")
                ready_alert.add(session)

            # START SESSION
            if now >= session_time and session not in started_today:

                threading.Thread(
                    target=run_session,
                    args=(bot, users),
                    daemon=True
                ).start()

                started_today.add(session)

        # RESET DAILY
        if now.strftime("%H:%M") == "00:01":
            started_today.clear()
            ready_alert.clear()

        time.sleep(5)
