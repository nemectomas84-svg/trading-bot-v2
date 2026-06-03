import csv
from datetime import datetime


class PaperTrader:
    def __init__(self):
        self.balance = 1000
        self.position = None
        self.entry_price = 0

        self.SL_PERCENT = 0.5
        self.TP_PERCENT = 1.0
        self.TRAIL_PERCENT = 0.3

        self.trailing_price = None

        self.init_log()

    # 🔥 reset logu pri štarte
    def init_log(self):
        with open("trades_log.csv", "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["time","action","price","reason","pnl","balance"])

    def log_trade(self, action, price, reason, pnl):
        with open("trades_log.csv", "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                action,
                price,
                reason,
                round(pnl, 2),
                round(self.balance, 2)
            ])

    def open_position(self, side, price):
        if side == "BUY":
            self.position = "BUY"
            self.entry_price = price
            self.trailing_price = price

            print(f"📈 OPEN BUY at {price}")
            self.log_trade("OPEN_BUY", price, "signal", 0)

    def close_position(self, price, reason):
        if self.position != "BUY":
            return

        pnl = (price - self.entry_price)
        self.balance += pnl

        print(f"❌ CLOSE BUY at {price} | {reason} | PNL: {pnl:.2f} | BALANCE: {self.balance:.2f}")

        self.log_trade("CLOSE_BUY", price, reason, pnl)

        self.position = None

    def update(self, price):
        if self.position != "BUY":
            return

        # STOP LOSS
        if price <= self.entry_price * (1 - self.SL_PERCENT / 100):
            self.close_position(price, "SL")
            return

        # TAKE PROFIT
        if price >= self.entry_price * (1 + self.TP_PERCENT / 100):
            self.close_position(price, "TP")
            return

        # TRAILING STOP
        if price > self.trailing_price:
            self.trailing_price = price

        if price <= self.trailing_price * (1 - self.TRAIL_PERCENT / 100):
            self.close_position(price, "TRAIL")
