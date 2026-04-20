import time
import random
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from pro_engine import generate_signal, PAIRS, get_prices

TZ = ZoneInfo("Africa/Kigali")

SIGNALS_PER_SESSION = 5

def send_all(bot,message):
    from bot import users
    for uid,data in users.items():
        if data.get("approved"):
            try:
                bot.send_message(int(uid),message)
            except:
                pass


def run_signal_cycle(bot):

    pair=random.choice(PAIRS)

    send_all(bot,
    f"""
📊 PAIR SELECTED
{pair}

Market analysis started...
""")

    time.sleep(180)

    for i in range(SIGNALS_PER_SESSION):

        signal=generate_signal(pair,"M1")

        if signal["status"]!="success":
            continue

        send_all(bot,signal["signal"])

        prices=get_prices(pair,"M1")
        entry=prices[-1]

        time.sleep(60)

        prices2=get_prices(pair,"M1")
        close=prices2[-1]

        result="WIN" if close>entry else "LOSS"

        send_all(bot,
f"""
📊 RESULT

Entry: {entry}
Close: {close}

RESULT: {result}
""")

        # next signal after 10 minutes
        time.sleep(600)


def session_manager(bot,ADMIN_ID):

    SESSION_TIMES=["15:25","18:00","21:00"]

    done=set()

    while True:

        now=datetime.now(TZ)
        current=now.strftime("%H:%M")

        for session in SESSION_TIMES:

            session_time=datetime.strptime(session,"%H:%M").replace(
                year=now.year,
                month=now.month,
                day=now.day,
                tzinfo=TZ
            )

            ready_time=(session_time-timedelta(minutes=1)).strftime("%H:%M")

            # READY MESSAGE
            if current==ready_time and session not in done:

                send_all(bot,
"""
⏰ SESSION START
Be Ready Traders...
""")

            # SESSION START
            if current==session and session not in done:

                run_signal_cycle(bot)

                done.add(session)

        # reset daily
        if current=="00:01":
            done.clear()

        time.sleep(10)
