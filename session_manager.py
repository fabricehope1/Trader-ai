import time
import random
import threading
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from pro_engine import generate_signal, PAIRS, get_prices

TZ = ZoneInfo("Africa/Kigali")

SIGNALS_PER_SESSION = 5
SIGNAL_INTERVAL = 600   # 10 minutes


# ================= BROADCAST =================
def send_all(bot, users, message):

    for uid, data in users.items():
        if data.get("approved"):
            try:
                bot.send_message(int(uid), message)
            except:
                pass


# ================= SIGNAL CYCLE =================
def run_signal_cycle(bot, users):

    pair = random.choice(PAIRS)

    send_all(bot, users,
f"""
🚀 SESSION STARTED

📊 Pair Selected: {pair}
🧠 Real Market Analysis running...
""")

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

        time.sleep(60)

        prices2 = get_prices(pair, "M1")
        if not prices2:
            continue

        close = prices2[-1]

        direction = signal["signal"]

        if "CALL" in direction:
            result = "WIN" if close > entry else "LOSS"
        else:
            result = "WIN" if close < entry else "LOSS"

        send_all(bot, users,
f"""
📊 RESULT

Entry: {entry}
Close: {close}

RESULT: {result}
""")

        time.sleep(SIGNAL_INTERVAL)


# ================= SESSION MANAGER =================
def session_manager(bot, users, ADMIN_ID):

    SESSION_TIMES = ["15:33", "18:00", "21:00"]

    done = set()
    ready_done = set()

    while True:

        now = datetime.now(TZ)
        current = now.strftime("%H:%M")

        for session in SESSION_TIMES:

            session_time = datetime.strptime(session, "%H:%M").replace(
                year=now.year,
                month=now.month,
                day=now.day,
                tzinfo=TZ
            )

            ready_time = (session_time - timedelta(minutes=1)).strftime("%H:%M")

            # READY ALERT
            if current == ready_time and session not in ready_done:

                send_all(bot, users,
"⏰ SESSION STARTING SOON\nBe Ready Traders..."
                )

                ready_done.add(session)

            # SESSION START
            if current == session and session not in done:

                threading.Thread(
                    target=run_signal_cycle,
                    args=(bot, users),
                    daemon=True
                ).start()

                done.add(session)

        if current == "00:01":
            done.clear()
            ready_done.clear()

        time.sleep(10)
