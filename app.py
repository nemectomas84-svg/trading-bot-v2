import time
from binance_client import get_price
from telegram_bot import send_message
from paper_trader import PaperTrader

trader = PaperTrader()

prices = []

last_signal = None
last_entry_time = 0

COOLDOWN = 300

EMA_FAST = 20
EMA_SLOW = 50

MIN_DIFF_PCT = 0.030
MIN_MOVE_PCT = 0.080
MAX_PRICE_ABOVE_EMA20_PCT = 0.060

CONFIRMATION_COUNT = 3

signal_buffer = []


def ema(period, values):
    if len(values) < period:
        return None

    k = 2 / (period + 1)
    ema_value = values[0]

    for value in values[1:]:
        ema_value = value * k + ema_value * (1 - k)

    return ema_value


def pct_diff(a, b):
    return abs(a - b) / b * 100


def strategy(price):
    global last_signal, last_entry_time, signal_buffer

    prices.append(price)

    if len(prices) > 1000:
        prices.pop(0)

    trader.update(price)

    if len(prices) < EMA_SLOW:
        return

    ema20 = ema(EMA_FAST, prices[-EMA_SLOW:])
    ema50 = ema(EMA_SLOW, prices[-EMA_SLOW:])

    if ema20 is None or ema50 is None:
        return

    diff_pct = pct_diff(ema20, ema50)

    recent_prices = prices[-30:]
    move_pct = (max(recent_prices) - min(recent_prices)) / price * 100

    trend_up = ema20 > ema50
    trend_down = ema20 < ema50
    price_above_ema20 = price > ema20
    strong_trend = diff_pct >= MIN_DIFF_PCT
    enough_movement = move_pct >= MIN_MOVE_PCT

    price_distance_ema20_pct = (price - ema20) / ema20 * 100
    not_overextended = price_distance_ema20_pct <= MAX_PRICE_ABOVE_EMA20_PCT

    print(
        f"PRICE: {price:.2f} | EMA20: {ema20:.2f} | EMA50: {ema50:.2f} | "
        f"DIFF: {diff_pct:.3f}% | MOVE: {move_pct:.3f}% | "
        f"DIST_EMA20: {price_distance_ema20_pct:.3f}%"
    )

    print(
        f"FILTERS | trend_up={trend_up} | trend_down={trend_down} | "
        f"price_above_ema20={price_above_ema20} | strong_trend={strong_trend} | "
        f"enough_movement={enough_movement} | not_overextended={not_overextended}"
    )

    buy_condition = (
        trend_up
        and price_above_ema20
        and strong_trend
        and enough_movement
        and not_overextended
    )

    if buy_condition:
        current_signal = "BUY"
    elif trend_down and strong_trend:
        current_signal = "SELL"
    else:
        current_signal = "HOLD"

    if current_signal != "BUY":
        if not trend_up:
            print("NO BUY: market is not in uptrend")
        elif not price_above_ema20:
            print("NO BUY: price below EMA20")
        elif not strong_trend:
            print("NO BUY: trend too weak")
        elif not enough_movement:
            print("NO BUY: movement too weak")
        elif not not_overextended:
            print("NO BUY: price too far above EMA20")

    signal_buffer.append(current_signal)

    if len(signal_buffer) > CONFIRMATION_COUNT:
        signal_buffer.pop(0)

    if signal_buffer.count(current_signal) < CONFIRMATION_COUNT:
        return

    now = time.time()

    if current_signal == "SELL":
        if trader.position == "BUY":
            send_message(f"⚠️ FORCE CLOSE BUY\nPRICE: {price:.2f}")
            trader.force_close_on_opposite_signal(price)

        last_signal = "SELL"
        return

    if current_signal == "HOLD":
        return

    if current_signal == "BUY":
        if trader.position is not None:
            return

        if now - last_entry_time < COOLDOWN:
            return

        message = f"🚨 BUY SIGNAL\nPRICE: {price:.2f}"

        print(message)
        send_message(message)

        trader.open_position("BUY", price)

        last_signal = "BUY"
        last_entry_time = now


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
