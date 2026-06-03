import time
from binance_client import get_price

prices = []
last_signal = None

def ema(period, prices):
    if len(prices) < period:
        return None

    k = 2 / (period + 1)
    ema_value = prices[0]

    for price in prices[1:]:
        ema_value = price * k + ema_value * (1 - k)

    return ema_value

def strategy(price):
    global last_signal

    prices.append(price)

    if len(prices) < 50:
        return

    ema20 = ema(20, prices[-50:])
    ema50 = ema(50, prices[-50:])

    if ema20 is None or ema50 is None:
        return

    print(f"PRICE: {price:.2f} | EMA20: {ema20:.2f} | EMA50: {ema50:.2f}")

    # určenie trendu
    if ema20 > ema50:
        current_signal = "BUY"
    else:
        current_signal = "SELL"

    # 🔥 LEN PRI ZMENE
    if current_signal != last_signal:
        print(f"🚨 NEW SIGNAL: {current_signal}")

        last_signal = current_signal

def run():
    while True:
        try:
            price = float(get_price())
            strategy(price)
            time.sleep(2)

        except Exception as e:
            print("ERROR:", e)
            time.sleep(5)


if __name__ == "__main__":
    run()
