import requests
import os

API_KEY = os.getenv("TWELVE_API")

def get_price(pair, timeframe):

    pair = pair.replace("/", "")
    
    url = f"https://api.twelvedata.com/time_series?symbol={pair}&interval={timeframe}&outputsize=30&apikey={API_KEY}"

    r = requests.get(url).json()

    if "values" not in r:
        return None

    closes = [float(x["close"]) for x in r["values"]]

    avg = sum(closes)/len(closes)
    last = closes[0]

    if last > avg:
        direction = "UP 🟢"
    else:
        direction = "DOWN 🔴"

    return {
        "pair": pair,
        "direction": direction,
        "price": last
    }
