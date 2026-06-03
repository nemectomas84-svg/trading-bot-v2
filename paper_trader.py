import csv
from datetime import datetime

balance = 1000
position = None
entry_price = 0

SL_PERCENT = 0.5
TP_PERCENT = 1.0
TRAIL_PERCENT = 0.3

trailing_price = None

# vytvor log file ak neexistuje
def init_log():
    with open("trades_log.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["time","action","price","reason","pnl","balance"])
        
def log_trade(action, price, reason, pnl):
    global balance
    with open("trades_log.csv", "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            action,
            price,
            reason,
            round(pnl, 2),
            round(balance, 2)
        ])

def open_buy(price):
    global position, entry_price, trailing_price

    position = "BUY"
    entry_price = price
    trailing_price = price

    print(f"📈 OPEN BUY at {price}")
    log_trade("OPEN_BUY", price, "signal", 0)

def close_buy(price, reason):
    global position, balance

    pnl = (price - entry_price)

    balance += pnl
    print(f"❌ CLOSE BUY at {price} | {reason} | PNL: {pnl:.2f} | BALANCE: {balance:.2f}")

    log_trade("CLOSE_BUY", price, reason, pnl)

    position = None

def check_trade(price):
    global trailing_price

    if position != "BUY":
        return

    # STOP LOSS
    if price <= entry_price * (1 - SL_PERCENT / 100):
        close_buy(price, "SL")
        return

    # TAKE PROFIT
    if price >= entry_price * (1 + TP_PERCENT / 100):
        close_buy(price, "TP")
        return

    # TRAILING STOP
    if price > trailing_price:
        trailing_price = price

    if price <= trailing_price * (1 - TRAIL_PERCENT / 100):
        close_buy(price, "TRAIL")
        return

def strategy(price, ema20, ema50):
    print(f"PRICE: {price} | EMA20: {ema20} | EMA50: {ema50}")

    # najprv kontroluj otvorený trade
    check_trade(price)

    global position

    # BUY SIGNAL
    if ema20 > ema50 and position is None:
        print("🚨 BUY SIGNAL")
        open_buy(price)

    # SELL SIGNAL (zatvor BUY ak ešte žije)
    elif ema20 < ema50 and position == "BUY":
        print("🚨 SELL SIGNAL")
        close_buy(price, "signal")
