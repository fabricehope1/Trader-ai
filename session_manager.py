import time
import random
import threading
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from pro_engine import generate_signal, PAIRS, get_prices

# ================= SETTINGS =================

TZ = ZoneInfo("Africa/Kigali")

SIGNALS_PER_SESSION = 5
SIGNAL_INTERVAL = 600   # 10 minutes

SESSION_TIMES = ["15:33", "18:00", "21:00"]


# ================= BROADCAST =================
def send_all(bot, users, message):

    for uid, data in users.items():
        if data.get("approved"):
            try:
                bot.send_message(int(uid), message)
            except Exception:
                pass


# ================= SIGNAL CYCLE =================
def run_signal_cycle(bot, users):

    pair = random.choice(PAIRS)

    send_all(
        bot,
        users,
        f"""
🚀 SESSION STARTED

📊 Pair Selected: {pair}
🧠 Real Market Analysis running...
"""
    )

    # analysis time
    time.sleep(180)

    for _ in range(SIGNALS_PER_SESSION):

        signal = generate_signal(pair, "M1")

        if signal.get("status") != "success":
            continue

        send_all(bot, users, signal["signal"])

        prices = get_prices(pair, "M1")
        if not prices:
            continue

        entry = prices[-1]

        # expiry
        time.sleep(60)

        prices2 = get_prices(pair, "M1")
        if not prices2:
            continue

        close = prices2[-1]

        direction = signal["signal"]

        if "CALL" in direction:
            result = "WIN ✅" if close > entry else "LOSS ❌"
        else:
            result = "WIN ✅" if close < entry else "LOSS ❌"

        send_all(
            bot,
            users,
            f"""
📊 RESULT

Entry: {entry}
Close: {close}

RESULT: {result}
"""
        )

        time.sleep(SIGNAL_INTERVAL)


# ================= SESSION MANAGER =================
def session_manager(bot, users):

    done_today = set()
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

            # ===== READY ALERT =====
            if (
                now >= ready_time
                and session not in ready_alert
            ):
                send_all(
                    bot,
                    users,
                    "⏰ SESSION STARTING SOON\nBe Ready Traders..."
                )
                ready_alert.add(session)

            # ===== START SESSION =====
            if (
                now >= session_time
                and session not in done_today
            ):

                threading.Thread(
                    target=run_signal_cycle,
                    args=(bot, users),
                    daemon=True
                ).start()

                done_today.add(session)

        # reset everyday
        if now.strftime("%H:%M") == "00:01":
            done_today.clear()
            ready_alert.clear()

        time.sleep(5)
