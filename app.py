import time
import json
import os

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

MIN_DIFF_PCT = 0.100
MIN_MOVE_PCT = 0.200
MAX_PRICE_ABOVE_EMA20_PCT = 0.040

CONFIRMATION_COUNT = 5

signal_buffer = []

TRADER_STATE_FILE = "data/trader_state.json"


def update_dashboard_state(
    signal="WAITING",
    reason="Starting bot",
    trend="UNKNOWN",
    price=None,
    ema20=None,
    ema50=None,
    diff_pct=None,
    move_pct=None,
    price_distance_ema20_pct=None,
):
    try:
        state = {}

        if os.path.exists(TRADER_STATE_FILE):
            with open(TRADER_STATE_FILE, "r") as f:
                state = json.load(f)

        state["market"] = {
            "signal": signal,
            "reason": reason,
            "trend": trend,
            "price": round(price, 2) if price is not None else None,
            "ema20": round(ema20, 2) if ema20 is not None else None,
            "ema50": round(ema50, 2) if ema50 is not None else None,
            "diff_pct": round(diff_pct, 4) if diff_pct is not None else None,
            "move_pct": round(move_pct, 4) if move_pct is not None else None,
            "price_distance_ema20_pct": round(price_distance_ema20_pct, 4)
            if price_distance_ema20_pct is not None
            else None,
            "updated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        }

        with open(TRADER_STATE_FILE, "w") as f:
            json.dump(state, f, indent=2)

    except Exception as e:
        print("DASHBOARD STATE ERROR:", e)


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

    if trader.position == "BUY":
        update_dashboard_state(
            signal="IN_TRADE",
            reason="Bot is managing open BUY position",
            trend="ACTIVE_TRADE",
            price=price,
        )

    if len(prices) < EMA_SLOW:
        update_dashboard_state(
            signal="WAITING",
            reason=f"Collecting data: {len(prices)}/{EMA_SLOW}",
            trend="UNKNOWN",
            price=price,
        )
        return

    ema20 = ema(EMA_FAST, prices[-EMA_SLOW:])
    ema50 = ema(EMA_SLOW, prices[-EMA_SLOW:])

    if ema20 is None or ema50 is None:
        update_dashboard_state(
            signal="WAITING",
            reason="EMA not ready yet",
            trend="UNKNOWN",
            price=price,
        )
        return

    diff_pct = pct_diff(ema20, ema50)

    recent_prices = prices[-30:]
    move_pct = (max(recent_prices) - min(recent_prices)) / price * 100

    trend_up = ema20 > ema50
    trend_down = ema20 < ema50

    price_above_ema20 = price > ema20

    price_distance_ema20_pct = (price - ema20) / ema20 * 100

    strong_trend = diff_pct >= MIN_DIFF_PCT
    enough_movement = move_pct >= MIN_MOVE_PCT

    not_overextended = (
        price_distance_ema20_pct >= 0
        and price_distance_ema20_pct <= MAX_PRICE_ABOVE_EMA20_PCT
    )

    if trend_up:
        trend_label = "UPTREND"
    elif trend_down:
        trend_label = "DOWNTREND"
    else:
        trend_label = "FLAT"

    print(
        f"PRICE: {price:.2f} | EMA20: {ema20:.2f} | EMA50: {ema50:.2f} | "
        f"DIFF: {diff_pct:.3f}% | MOVE: {move_pct:.3f}% | "
        f"DIST_EMA20: {price_distance_ema20_pct:.3f}%"
    )

    print(
        f"FILTERS | trend_up={trend_up} | trend_down={trend_down} | "
        f"price_above_ema20={price_above_ema20} | "
        f"strong_trend={strong_trend} | enough_movement={enough_movement} | "
        f"not_overextended={not_overextended}"
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
        reason = "BUY conditions passed"
        dashboard_signal = "BUY_READY"
    elif trend_down and strong_trend:
        current_signal = "SELL"
        reason = "Downtrend detected. Used only to close BUY position."
        dashboard_signal = "SELL_WATCH"
    else:
        current_signal = "HOLD"
        dashboard_signal = "WAITING"

        if not trend_up:
            reason = "Market is not in uptrend"
            print("NO BUY: market is not in uptrend")
        elif not price_above_ema20:
            reason = "Price below EMA20"
            print("NO BUY: price below EMA20")
        elif not strong_trend:
            reason = "Trend too weak"
            print("NO BUY: trend too weak")
        elif not enough_movement:
            reason = "Movement too weak"
            print("NO BUY: movement too weak")
        elif not not_overextended:
            reason = "Price too far above EMA20"
            print("NO BUY: price too far above EMA20")
        else:
            reason = "Waiting for setup"

    update_dashboard_state(
        signal=dashboard_signal,
        reason=reason,
        trend=trend_label,
        price=price,
        ema20=ema20,
        ema50=ema50,
        diff_pct=diff_pct,
        move_pct=move_pct,
        price_distance_ema20_pct=price_distance_ema20_pct,
    )

    signal_buffer.append(current_signal)

    if len(signal_buffer) > CONFIRMATION_COUNT:
        signal_buffer.pop(0)

    if signal_buffer.count(current_signal) < CONFIRMATION_COUNT:
        update_dashboard_state(
            signal="CONFIRMING",
            reason=f"Confirming signal {current_signal}: {signal_buffer.count(current_signal)}/{CONFIRMATION_COUNT}",
            trend=trend_label,
            price=price,
            ema20=ema20,
            ema50=ema50,
            diff_pct=diff_pct,
            move_pct=move_pct,
            price_distance_ema20_pct=price_distance_ema20_pct,
        )
        return

    now = time.time()

    if current_signal == "SELL":
        if trader.position == "BUY":
            send_message(f"⚠️ FORCE CLOSE BUY\nPRICE: {price:.2f}")
            trader.force_close_on_opposite_signal(price)

            update_dashboard_state(
                signal="EXITED",
                reason="BUY position closed because opposite SELL signal appeared",
                trend=trend_label,
                price=price,
                ema20=ema20,
                ema50=ema50,
                diff_pct=diff_pct,
                move_pct=move_pct,
                price_distance_ema20_pct=price_distance_ema20_pct,
            )
        else:
            update_dashboard_state(
                signal="WAITING",
                reason="SELL detected, but SHORT trading is not enabled yet",
                trend=trend_label,
                price=price,
                ema20=ema20,
                ema50=ema50,
                diff_pct=diff_pct,
                move_pct=move_pct,
                price_distance_ema20_pct=price_distance_ema20_pct,
            )

        last_signal = "SELL"
        return

    if current_signal == "HOLD":
        return

    if current_signal == "BUY":
        if trader.position is not None:
            update_dashboard_state(
                signal="IN_TRADE",
                reason="BUY signal detected, but position is already open",
                trend=trend_label,
                price=price,
                ema20=ema20,
                ema50=ema50,
                diff_pct=diff_pct,
                move_pct=move_pct,
                price_distance_ema20_pct=price_distance_ema20_pct,
            )
            return

        if now - last_entry_time < COOLDOWN:
            update_dashboard_state(
                signal="COOLDOWN",
                reason="Waiting for cooldown before next entry",
                trend=trend_label,
                price=price,
                ema20=ema20,
                ema50=ema50,
                diff_pct=diff_pct,
                move_pct=move_pct,
                price_distance_ema20_pct=price_distance_ema20_pct,
            )
            return

        message = f"🚨 BUY SIGNAL\nPRICE: {price:.2f}"

        print(message)
        send_message(message)

        trader.open_position("BUY", price)

        update_dashboard_state(
            signal="BUY_OPENED",
            reason="BUY position opened",
            trend=trend_label,
            price=price,
            ema20=ema20,
            ema50=ema50,
            diff_pct=diff_pct,
            move_pct=move_pct,
            price_distance_ema20_pct=price_distance_ema20_pct,
        )

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
            update_dashboard_state(
                signal="ERROR",
                reason=str(e),
                trend="UNKNOWN",
            )
            time.sleep(5)


if __name__ == "__main__":
    run()
