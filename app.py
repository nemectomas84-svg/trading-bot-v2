import time
from binance_client import get_price

prices = []

# 🔥 GLOBAL STATE
last_signal = None
last_trade_time = 0

# 🔧 SETTINGS
COOLDOWN = 300  # 5 minút
MIN_DIFF = 5    # minimálny rozdiel EMA
CONFIRMATION_COUNT = 3

signal_buffer = []


# 📊 EMA funkcia
def ema(period, prices):
    if len(prices) < period:
        return None

    k = 2 / (period + 1)
    ema_value = prices[0]

    for price in prices[1:]:
        ema_value = price * k + ema_value * (1 - k)

    return ema_value


# 🧠 STRATÉGIA
def strategy(price):
    global last_signal, last_trade_time, signal_buffer

    prices.append(price)

    if len(prices) < 50:
        return

    ema20 = ema(20, prices[-50:])
    ema50 = ema(50, prices[-50:])

    if ema20 is None or ema50 is None:
        return

    print(f"PRICE: {price:.2f} | EMA20: {ema20:.2f} | EMA50: {ema50:.2f}")

    # 🔥 FILTER SLABÉHO TRENDU
    diff = abs(ema20 - ema50)
    if diff < MIN_DIFF:
        return

    # určenie trendu
    if ema20 > ema50:
        current_signal = "BUY"
    else:
        current_signal = "SELL"

    # 🔁 CONFIRMATION BUFFER
    signal_buffer.append(current_signal)

    if len(signal_buffer) > CONFIRMATION_COUNT:
        signal_buffer.pop(0)

    now = time.time()

    # ✅ MUSÍ BYŤ POTVRDENÝ SIGNÁL
    if signal_buffer.count(current_signal) == CONFIRMATION_COUNT:

        if current_signal != last_signal and (now - last_trade_time > COOLDOWN):

            print(f"🚨 TRADE SIGNAL: {current_signal}")

            last_signal = current_signal
            last_trade_time = now


# 🔁 LOOP
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
