import time
import threading
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from pro_engine import generate_signal, PAIRS, get_prices

TZ = ZoneInfo("Africa/Kigali")

SESSION_TIMES = ["18:00","21:00"]
SIGNALS_PER_SESSION = 5
SIGNAL_INTERVAL = 10


# ================= SEND =================
def send_all(bot, users, message):
    for uid,data in users.items():
        if data.get("approved"):
            try:
                bot.send_message(int(uid),message)
            except:
                pass


# ================= SAFE PAIR FINDER =================
def find_best_pair():

    start=time.time()

    while time.time()-start < 10:

        for pair in PAIRS:

            signal=generate_signal(pair,"M1")

            if signal.get("status")=="success":
                return pair,signal

    # fallback (ntigomba guhagarara)
    pair=PAIRS[0]
    signal=generate_signal(pair,"M1")

    return pair,signal


# ================= SINGLE SIGNAL =================
def run_signal(bot,users,number):

    send_all(bot,users,f"🧠 Analysis #{number}\nScanning Market...")

    pair,signal=find_best_pair()

    now=datetime.now(TZ)
    entry_time=now+timedelta(minutes=1)

    send_all(bot,users,
f"""
📊 SIGNAL #{number}

Pair: {pair}

Prepare...
Entry At: {entry_time.strftime('%H:%M')}
""")

    # wait entry
    while datetime.now(TZ)<entry_time:
        time.sleep(1)

    send_all(bot,users,f"🔥 ENTRY → {signal['signal']}")

    prices=get_prices(pair,"M1")
    if not prices:
        return

    entry=prices[-1]

    expiry=datetime.now(TZ)+timedelta(minutes=1)

    while datetime.now(TZ)<expiry:
        time.sleep(1)

    prices2=get_prices(pair,"M1")
    if not prices2:
        return

    close=prices2[-1]

    if "CALL" in signal["signal"]:
        result="WIN ✅" if close>entry else "LOSS ❌"
    else:
        result="WIN ✅" if close<entry else "LOSS ❌"

    send_all(bot,users,
f"""
📊 RESULT #{number}

Pair: {pair}
Entry: {entry}
Close: {close}

RESULT: {result}
""")


# ================= SESSION =================
def run_session(bot,users,session_time):

    send_all(bot,users,"🚀 SESSION STARTED")

    for i in range(SIGNALS_PER_SESSION):

        signal_time=session_time+timedelta(minutes=i*SIGNAL_INTERVAL)

        while datetime.now(TZ)<signal_time:
            time.sleep(1)

        run_signal(bot,users,i+1)

    send_all(bot,users,"✅ SESSION FINISHED")


# ================= MANAGER =================
def session_manager(bot,users):

    started=set()
    ready=set()

    while True:

        now=datetime.now(TZ)

        for session in SESSION_TIMES:

            session_time=datetime.strptime(
                session,"%H:%M"
            ).replace(
                year=now.year,
                month=now.month,
                day=now.day,
                tzinfo=TZ
            )

            ready_time=session_time-timedelta(minutes=1)

            if now>=ready_time and session not in ready:
                send_all(bot,users,
"⏰ SESSION STARTING SOON\nBe Ready Traders...")
                ready.add(session)

            if now>=session_time and session not in started:

                threading.Thread(
                    target=run_session,
                    args=(bot,users,session_time),
                    daemon=True
                ).start()

                started.add(session)

        if now.strftime("%H:%M")=="00:01":
            started.clear()
            ready.clear()

        time.sleep(5)
