import os
import time
from xtb_client import XTBClient

# ENV VARIABLES (Render)
XTB_LOGIN = os.getenv("XTB_LOGIN")
XTB_PASSWORD = os.getenv("XTB_PASSWORD")

# INIT CLIENT
client = XTBClient(XTB_LOGIN, XTB_PASSWORD)


def strategy(price_data):
    """
    TU DÁME TVOJU STRATÉGIU (V2)
    zatiaľ len debug
    """

    bid = price_data.get("bid")
    ask = price_data.get("ask")

    print(f"📊 BID: {bid} | ASK: {ask}")

    # placeholder logic
    if bid and bid > 20000:
        print("📈 SIGNAL: BUY (placeholder)")
    elif bid and bid < 19000:
        print("📉 SIGNAL: SELL (placeholder)")


def run():
    client.connect()

    while True:
        try:
            price = client.get_price("US100")

            if price:
                strategy(price)

            time.sleep(5)

        except Exception as e:
            print("❌ LOOP ERROR:", e)
            client.reconnect()


if __name__ == "__main__":
    run()
