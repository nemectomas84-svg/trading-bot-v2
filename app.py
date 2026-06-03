import time
from binance_client import get_price
from telegram_bot import send_message
from paper_trader import PaperTrader

trader = PaperTrader()

prices = []

last_signal = None
last_trade_time = 0

COOLDOWN = 300
MIN_DIFF = 5
CONFIRMATION_COUNT = 3
MIN_MOVE = 20

signal_buffer = []


def ema(period, prices):
    if len(prices) < period:
        return None

    k = 2 / (period + 1)
    ema_value = prices[0]

    for price in prices[1:]:
        ema_value = price * k + ema_value * (1 - k)

    return ema_value


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

    # 🔥 vždy update trade
    trader.update(price)

    diff = abs(ema20 - ema50)
    if diff < MIN_DIFF:
        return

    recent_prices = prices[-5:]
    move = max(recent_prices) - min(recent_prices)

    if move < MIN_MOVE:
        return

    current_signal = "BUY" if ema20 > ema50 else "SELL"

    signal_buffer.append(current_signal)

    if len(signal_buffer) > CONFIRMATION_COUNT:
        signal_buffer.pop(0)

    now = time.time()

    if signal_buffer.count(current_signal) == CONFIRMATION_COUNT:

        if current_signal != last_signal and (now - last_trade_time > COOLDOWN):

            message = f"🚨 {current_signal} SIGNAL\nPRICE: {price:.2f}"
            
            print(message)
            send_message(message)

            trader.open_position(current_signal, price)

            last_signal = current_signal
            last_trade_time = now


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
