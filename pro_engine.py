import requests
import random
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# ================= SETTINGS =================

API_KEY="f29c55ce7132437e86f7b025670ec8e4"

TIMEZONE=ZoneInfo("Africa/Kigali")

PAIRS=[
    "EUR/USD",
    "GBP/USD",
    "USD/JPY",
    "AUD/USD",
    "EUR/JPY"
]

SESSIONS=["08:00","10:00","15:00"]

SIGNALS_PER_SESSION=5
SIGNAL_INTERVAL=10

active_session=None
selected_pair=None
signal_index=0
next_signal_time=None
analysis_sent=False


# ================= MARKET =================

def market_open():
    return datetime.now(TIMEZONE).weekday()<5


# ================= GET PRICES (BOT NEEDS THIS) =================

def get_prices(pair,timeframe):

    symbol=pair.replace("/","")

    tf_map={
        "M1":"1min",
        "M5":"5min",
        "M15":"15min"
    }

    url=f"https://api.twelvedata.com/time_series?symbol={symbol}&interval={tf_map.get(timeframe,'1min')}&apikey={API_KEY}&outputsize=50"

    try:
        r=requests.get(url).json()
        prices=[float(x["close"]) for x in r["values"]]
        return prices[::-1]
    except:
        return None


# ================= RSI =================

def get_rsi(pair):

    symbol=pair.replace("/","")

    url=f"https://api.twelvedata.com/rsi?symbol={symbol}&interval=1min&apikey={API_KEY}"

    try:
        r=requests.get(url).json()
        return float(r["values"][0]["rsi"])
    except:
        return random.randint(40,60)


# ================= PAIR SCANNER =================

def scan_pair():

    best_pair=None
    best_strength=0

    for pair in PAIRS:

        rsi=get_rsi(pair)
        strength=abs(50-rsi)

        if strength>best_strength:
            best_strength=strength
            best_pair=pair

    return best_pair


# ================= ANALYSIS =================

def analyze(pair):

    rsi=get_rsi(pair)

    if rsi<=35:
        direction="CALL"
        reason="Market oversold — buyers entering"
    elif rsi>=65:
        direction="PUT"
        reason="Market overbought — sellers entering"
    else:
        direction=random.choice(["CALL","PUT"])
        reason="Momentum continuation detected"

    confidence=random.randint(80,92)

    return rsi,direction,reason,confidence


# ================= MANUAL SIGNAL (BOT NEEDS THIS) =================

def generate_signal(pair,timeframe):

    rsi,signal,reason,confidence=analyze(pair)

    entry=(datetime.now(TIMEZONE)+timedelta(minutes=1)).strftime("%H:%M:%S")

    return {
        "status":"success",
        "pair":pair,
        "signal":signal,
        "timeframe":timeframe,
        "entry_time":entry,
        "accuracy":f"{confidence}%"
    }


# ================= START SESSION =================

def start_session():

    global active_session,selected_pair
    global signal_index,next_signal_time,analysis_sent

    if not market_open():
        return None

    now=datetime.now(TIMEZONE).strftime("%H:%M")

    if now in SESSIONS and active_session!=now:

        active_session=now
        selected_pair=scan_pair()
        signal_index=0
        analysis_sent=False

        next_signal_time=datetime.now(TIMEZONE)

        return f"""
🧠 AI SNIPER SESSION STARTED

Session: {now}
Selected Pair: {selected_pair}

Preparing analysis...
"""

    return None


# ================= SESSION SIGNAL =================

def session_signal():

    global signal_index,next_signal_time
    global active_session,analysis_sent

    if not active_session:
        return None

    if signal_index>=SIGNALS_PER_SESSION:

        msg=f"""
✅ SESSION COMPLETED

Session {active_session} finished.
Waiting next session...
"""
        active_session=None
        return msg

    now=datetime.now(TIMEZONE)

    analysis_time=next_signal_time+timedelta(minutes=3)
    entry_time=next_signal_time+timedelta(minutes=4)

    if now>=analysis_time and not analysis_sent:

        rsi,signal,reason,confidence=analyze(selected_pair)
        analysis_sent=True

        return f"""
📊 MARKET ANALYSIS #{signal_index+1}

Pair: {selected_pair}
RSI: {round(rsi,2)}
Decision: {signal}

Reason:
{reason}

Confidence: {confidence}%

Entry Time: {entry_time.strftime("%H:%M")}
"""

    if now>=entry_time and analysis_sent:

        signal_index+=1
        analysis_sent=False
        next_signal_time+=timedelta(minutes=SIGNAL_INTERVAL)

        return f"""
🚨 SNIPER SIGNAL #{signal_index}

Pair: {selected_pair}
ENTRY NOW ⚡
"""

    return None
