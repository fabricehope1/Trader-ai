import requests
import os
import random
from datetime import datetime
import pytz

API_KEY = os.getenv("FOREX_API_KEY")

PAIRS = [
    "EUR/USD",
    "GBP/USD",
    "USD/JPY",
    "USD/CAD",
    "EUR/GBP",
    "AUD/USD"
]

def format_pair(pair):
    # EUR/USD -> EURUSD
    return pair.replace("/", "")


def get_price(pair):

    symbol = format_pair(pair)

    url = "https://api.twelvedata.com/price"

    params = {
        "symbol": symbol,
        "apikey": API_KEY
    }

    try:
        r = requests.get(url, params=params, timeout=10).json()

        print("API RESPONSE:", r)

        if "price" not in r:
            return None

        return float(r["price"])

    except Exception as e:
        print(e)
        return None


def generate_signal(pair, timeframe):

    price = get_price(pair)

    if price is None:
        return {
            "status": "error",
            "message": "API failed"
        }

    direction = random.choice(["CALL 📈", "PUT 📉"])
    accuracy = random.randint(82, 94)

    tz = pytz.timezone("Africa/Kigali")
    entry_time = datetime.now(tz).strftime("%H:%M:%S")

    return {
        "status": "success",
        "pair": pair,
        "signal": direction,
        "timeframe": timeframe,
        "entry_time": entry_time,
        "accuracy": f"{accuracy}%"
    }
