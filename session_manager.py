import time
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# ENGINE YAWE
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
def check_result(pair, entry_price):

    prices = get_prices(pair, "M1")

    if not prices:
        return "UNKNOWN"

    close_price = prices[-1]

    if close_price > entry_price:
        return "WIN ✅", close_price
    else:
        return "LOSS ❌", close_price


# ================= ONE SIGNAL =================
def run_single_signal(bot, number, used_pairs):

    send_all(
        bot,
        f"🧠 Analysis #{number}\nAI scanning ALL pairs..."
    )

    signal = None

    # AI ikomeza gushaka setup nziza
    while signal is None:

        for pair in PAIRS:

            if pair in used_pairs:
                continue

            result = generate_signal(pair, "M1")

            if result["status"] == "success":

                signal = result
                used_pairs.append(pair)
                break

        if signal is None:
            send_all(bot, "⚠️ Market weak... waiting better setup")
            time.sleep(15)

    # ================= SIGNAL =================
    send_all(bot, signal["signal"])

    pair = signal["pair"]

    prices = get_prices(pair, "M1")
    entry_price = prices[-1]

    # wait entry candle
    time.sleep(60)

    result, close_price = check_result(pair, entry_price)

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
            time.sleep(60)  # next analysis after result


# ================= SESSION MANAGER =================
def session_manager(bot):

    SESSION_TIMES = ["18:57", "20:00", "21:00"]

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

            # ⚠️ WARNING
            if current == warning_time and session not in done:
                send_all(bot,
"""
⚠️ SESSION STARTING IN 5 MINUTES
Prepare your account...
""")

            # 🚀 START SESSION
            if current == session and session not in done:

                run_signal_cycle(bot)

                done.add(session)

        # reset daily
        if current == "00:01":
            done.clear()

        time.sleep(10)
