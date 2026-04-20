import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from pro_engine import generate_signal, PAIRS, get_prices

TZ = ZoneInfo("Africa/Kigali")

SIGNALS_PER_SESSION = 5


# ================= SEND MESSAGE =================
def send_all(bot, message):

    from bot import users

    for uid, data in users.items():
        if data.get("approved"):
            try:
                bot.send_message(int(uid), message)
            except:
                pass


# ================= RESULT CHECK =================
def check_result(pair, entry_price, direction):

    prices = get_prices(pair, "M1")

    if not prices:
        return "UNKNOWN", entry_price

    close_price = prices[-1]

    if direction == "CALL":
        result = "WIN ✅" if close_price > entry_price else "LOSS ❌"
    else:
        result = "WIN ✅" if close_price < entry_price else "LOSS ❌"

    return result, close_price


# ================= SCAN ALL PAIRS =================
def get_best_signal():

    best_signal = None
    best_confidence = 0

    for pair in PAIRS:

        result = generate_signal(pair, "M1")

        if result["status"] != "success":
            continue

        confidence = result.get("confidence", 50)

        if confidence > best_confidence:
            best_confidence = confidence
            best_signal = result

    return best_signal


# ================= ONE SIGNAL =================
def run_single_signal(bot, number, used_pairs):

    send_all(
        bot,
        f"🧠 Analysis #{number}\nScanning ALL pairs..."
    )

    signal = None

    # wait strong setup
    while signal is None:

        best = get_best_signal()

        if best and best["pair"] not in used_pairs:
            signal = best
            used_pairs.append(best["pair"])
        else:
            send_all(bot, "⚠️ No strong setup... waiting better market")
            time.sleep(20)

    # ===== SEND SIGNAL =====
    send_all(bot, signal["signal"])

    pair = signal["pair"]
    direction = signal["direction"]

    prices = get_prices(pair, "M1")
    if not prices:
        return

    entry_price = prices[-1]

    # wait expiry candle
    time.sleep(60)

    result, close_price = check_result(pair, entry_price, direction)

    send_all(
        bot,
f"""
📊 RESULT

Pair: {pair}

Entry: {entry_price}
Close: {close_price}

Result: {result}
"""
    )


# ================= SESSION ENGINE =================
def run_signal_cycle(bot):

    used_pairs = []

    send_all(bot, "🚀 AI SESSION STARTED")

    for i in range(1, SIGNALS_PER_SESSION + 1):

        run_single_signal(bot, i, used_pairs)

        if i < SIGNALS_PER_SESSION:
            time.sleep(60)


# ================= SESSION MANAGER =================
def session_manager(bot):

    SESSION_TIMES = ["19:05", "20:00", "21:00"]

    done = set()

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

            warning_time = (session_time - timedelta(minutes=5)).strftime("%H:%M")

            # WARNING MESSAGE
            if current == warning_time and session not in done:
                send_all(
                    bot,
"""
⚠️ SESSION STARTING IN 5 MINUTES
Prepare your account...
"""
                )

            # START SESSION
            if current == session and session not in done:

                run_signal_cycle(bot)

                done.add(session)

        # reset everyday
        if current == "00:01":
            done.clear()

        time.sleep(10)
