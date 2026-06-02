import time
from binance_client import BinanceClient

client = BinanceClient()


def strategy(price):
    print(f"📊 PRICE: {price}")

    # TODO: tu dáme tvoju reálnu stratégiu
    if price > 70000:
        print("📈 BUY SIGNAL")
    elif price < 60000:
        print("📉 SELL SIGNAL")


def run():
    while True:
        try:
            price = client.get_price("BTCUSDT")

            if price:
                strategy(price)

            time.sleep(2)

        except Exception as e:
            print("❌ ERROR:", e)
            time.sleep(5)


if __name__ == "__main__":
    run()
