import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# ENGINE
from pro_engine import generate_signal, PAIRS


# ==============================
# FIND BEST PAIR (REAL ANALYSIS)
# ==============================
def find_best_pair():

    best_pair = None
    best_score = 0
    best_signal = None

    for pair in PAIRS:

        try:
            result = generate_signal(pair, "M1")

            if result["status"] != "success":
                continue

            score = result.get("score", 50)

            if score > best_score:
                best_score = score
                best_pair = pair
                best_signal = result

        except Exception as e:
            print("Scan error:", e)

    return best_pair, best_signal


# ==============================
# SESSION MANAGER
# ==============================
def session_manager(bot, ADMIN_ID):

    # igihe session itangira
    SESSION_TIME = "15:00"

    ready_sent = False
    started = False

    while True:

        now = datetime.now(ZoneInfo("Africa/Kigali"))
        current_time = now.strftime("%H:%M")

        # ================= READY MESSAGE =================
        ready_time = (
            datetime.strptime(SESSION_TIME, "%H:%M")
            - timedelta(minutes=1)
        ).strftime("%H:%M")

        if current_time == ready_time and not ready_sent:

            bot.send_message(
                ADMIN_ID,
                f"""
⏰ SESSION READY

Session iratangira saa {SESSION_TIME}
Bot iri gukora Market Scan...
"""
            )

            ready_sent = True

        # ================= SESSION START =================
        if current_time == SESSION_TIME and not started:

            bot.send_message(
                ADMIN_ID,
                "🧠 Gutoranya pair nziza ku isoko..."
            )

            pair, signal = find_best_pair()

            if not pair or not signal:
                bot.send_message(
                    ADMIN_ID,
                    "❌ Ntago habonetse signal nziza."
                )
                started = True
                continue

            bot.send_message(
                ADMIN_ID,
                f"""
🚀 SESSION STARTED

📊 Pair Selected: {pair}
📈 Direction: {signal['direction']}
⏱ Timeframe: M1

📊 Reason:
RSI + Trend + Momentum Confirmed
"""
            )

            # ===== ENTRY TIME (3 min nyuma)
            entry_time = (
                now + timedelta(minutes=3)
            ).strftime("%H:%M")

            bot.send_message(
                ADMIN_ID,
                f"""
⌛ ENTRY TIME

Kanda trade saa {entry_time}
"""
            )

            # ===== SIGNAL EVERY 10 MINUTES =====
            for i in range(3):

                time.sleep(600)  # 10 minutes

                pair, signal = find_best_pair()

                if pair and signal:

                    bot.send_message(
                        ADMIN_ID,
                        f"""
🔥 NEW SIGNAL

Pair: {pair}
Direction: {signal['direction']}
Timeframe: M1
"""
                    )

            started = True

        # ===== RESET EVERYDAY =====
        if current_time == "00:01":
            ready_sent = False
            started = False

        time.sleep(10)
