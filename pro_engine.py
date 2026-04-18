from otc_reader import get_otc_price
from datetime import datetime

PAIRS=[
"EURUSD_otc",
"GBPUSD_otc",
"USDJPY_otc"
]

def generate_signal(pair,timeframe):

    try:

        price=get_otc_price()

        signal="BUY" if float(price[-1])%2==0 else "SELL"

        return {
            "status":"success",
            "pair":pair,
            "signal":signal,
            "timeframe":timeframe,
            "entry_time":datetime.now().strftime("%H:%M"),
            "accuracy":"OTC LIVE"
        }

    except Exception as e:

        print(e)

        return {"status":"error"}
