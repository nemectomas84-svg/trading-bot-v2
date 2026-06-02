import time
from binance_client import BinanceClient

client = BinanceClient()

prices = []


def strategy(price):
    prices.append(price)

    if len(prices) < 20:
        return

    sma = sum(prices[-20:]) / 20

    print(f"PRICE: {price} | SMA: {sma}")

    if price > sma:
        print("📈 BUY SIGNAL")

    elif price < sma:
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
