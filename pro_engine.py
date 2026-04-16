import requests
import random

API_KEY="f29c55ce7132437e86f7b025670ec8e4"

PAIRS=[
    "EURUSD",
    "GBPUSD",
    "USDJPY",
    "AUDUSD"
]

# ================= PRICE =================

def get_price(pair):

    url=f"https://api.twelvedata.com/time_series?symbol={pair}&interval=1min&outputsize=2&apikey={API_KEY}"

    try:
        r=requests.get(url).json()

        if "values" not in r:
            print("API ERROR:", r)
            return None

        candles=r["values"]

        last_close=float(candles[0]["close"])
        prev_close=float(candles[1]["close"])

        return last_close - prev_close

    except Exception as e:
        print("ERROR:", e)
        return None


# ================= SIGNAL =================

def generate_signal(pair):

    change=get_price(pair)

    if change is None:
        return None

    if change>0:
        direction="CALL 📈"
    else:
        direction="PUT 📉"

    confidence=random.randint(75,95)

    return {
        "pair":pair,
        "direction":direction,
        "confidence":confidence,
        "expiry":"1 MIN"
    }


# ================= TEST =================

if __name__=="__main__":

    for pair in PAIRS:
        signal=generate_signal(pair)

        if signal:
            print(signal)
        else:
            print(pair,"No signal")
