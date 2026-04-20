import time
import threading
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from pro_engine import generate_signal, PAIRS, get_prices


# ================= SETTINGS =================

TZ = ZoneInfo("Africa/Kigali")

SESSION_TIMES = ["18:00", "21:00"]   # hindura uko ushaka
SIGNALS_PER_SESSION = 5


# ================= BROADCAST =================

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
    best_conf = -1

    for pair in PAIRS:

        signal = generate_signal(pair, "M1")

        if signal.get("status") != "success":
            continue

        confidence = signal.get("confidence", 50)

        if confidence > best_conf:
            best_conf = confidence
            best_pair = pair

    # fallback
    if not best_pair:
        best_pair = PAIRS[0]

    return best_pair


# ================= SESSION ENGINE =================

def run_session(bot, users):

    send_all(bot, users, "🚀 SESSION STARTED")

    for i in range(1, SIGNALS_PER_SESSION + 1):

        # -------- ANALYSIS --------
        send_all(
            bot,
            users,
            f"🧠 Analysis #{i}\nScanning Market..."
        )

        pair = find_best_pair()

        signal = generate_signal(pair, "M1")

        if signal.get("status") != "success":
            continue

        direction = "CALL 📈" if "CALL" in signal["signal"] else "PUT 📉"

        # -------- SIGNAL MESSAGE --------
        send_all(
            bot,
            users,
f"""
📊 SIGNAL #{i}

Pair: {pair}
Direction: {direction}

⏳ Prepare...
Entry Time: Next Minute
"""
        )

        # WAIT ENTRY TIME
        time.sleep(60)

        # -------- ENTRY --------
        send_all(
            bot,
            users,
f"""
🔥 ENTER NOW

{pair}
{direction}
"""
        )

        prices = get_prices(pair, "M1")
        if not prices:
            continue

        entry = prices[-1]

        # WAIT EXPIRY
        time.sleep(60)

        prices2 = get_prices(pair, "M1")
        if not prices2:
            continue

        close = prices2[-1]

        if "CALL" in direction:
            result = "WIN ✅" if close > entry else "LOSS ❌"
        else:
            result = "WIN ✅" if close < entry else "LOSS ❌"

        # -------- RESULT --------
        send_all(
            bot,
            users,
f"""
📊 RESULT #{i}

Pair: {pair}
Entry: {entry}
Close: {close}

RESULT: {result}
"""
        )

        # small delay before next analysis
        time.sleep(5)

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

                send_all(
                    bot,
                    users,
                    "⏰ SESSION STARTING SOON\nBe Ready Traders..."
                )

                ready_alert.add(session)

            # START SESSION
            if now >= session_time and session not in started_today:

                threading.Thread(
                    target=run_session,
                    args=(bot, users),
                    daemon=True
                ).start()

                started_today.add(session)

        # DAILY RESET
        if now.strftime("%H:%M") == "00:01":
            started_today.clear()
            ready_alert.clear()

        time.sleep(5)
