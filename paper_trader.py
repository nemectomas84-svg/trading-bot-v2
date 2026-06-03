import csv
import os
from datetime import datetime


class PaperTrader:
    def __init__(
        self,
        initial_balance=1000.0,
        position_fraction=1.0,
        fee_rate=0.001,
        slippage_rate=0.0002,
    ):
        self.balance = initial_balance
        self.initial_balance = initial_balance

        self.position = None
        self.entry_price = 0.0
        self.entry_time = None
        self.position_size_usdt = 0.0
        self.qty = 0.0

        self.position_fraction = position_fraction
        self.fee_rate = fee_rate
        self.slippage_rate = slippage_rate

        self.SL_PERCENT = 0.35
        self.TP_PERCENT = 0.70
        self.TRAIL_PERCENT = 0.25
        self.MAX_TRADE_SECONDS = 20 * 60

        self.trailing_price = None

        self.init_log()

    def init_log(self):
        file_exists = os.path.exists("trades_log.csv")

        if not file_exists:
            with open("trades_log.csv", "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "time",
                    "action",
                    "price",
                    "reason",
                    "pnl",
                    "pnl_pct",
                    "fees",
                    "balance"
                ])

    def log_trade(self, action, price, reason, pnl=0.0, pnl_pct=0.0, fees=0.0):
        with open("trades_log.csv", "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                action,
                round(price, 2),
                reason,
                round(pnl, 4),
                round(pnl_pct, 4),
                round(fees, 4),
                round(self.balance, 2)
            ])

    def open_position(self, side, price):
        if side != "BUY":
            return

        if self.position is not None:
            return

        execution_price = price * (1 + self.slippage_rate)

        self.position = "BUY"
        self.entry_price = execution_price
        self.entry_time = datetime.now()
        self.trailing_price = execution_price

        self.position_size_usdt = self.balance * self.position_fraction
        self.qty = self.position_size_usdt / execution_price

        entry_fee = self.position_size_usdt * self.fee_rate
        self.balance -= entry_fee

        print(f"📈 OPEN BUY at {execution_price:.2f} | fee: {entry_fee:.2f}")
        self.log_trade("OPEN_BUY", execution_price, "signal", 0.0, 0.0, entry_fee)

    def close_position(self, price, reason):
        if self.position != "BUY":
            return

        execution_price = price * (1 - self.slippage_rate)

        gross_pnl = (execution_price - self.entry_price) * self.qty
        exit_value = self.qty * execution_price
        exit_fee = exit_value * self.fee_rate

        net_pnl = gross_pnl - exit_fee
        pnl_pct = net_pnl / self.position_size_usdt * 100

        self.balance += net_pnl

        print(
            f"❌ CLOSE BUY at {execution_price:.2f} | {reason} | "
            f"PNL: {net_pnl:.2f} ({pnl_pct:.2f}%) | BALANCE: {self.balance:.2f}"
        )

        self.log_trade("CLOSE_BUY", execution_price, reason, net_pnl, pnl_pct, exit_fee)

        self.position = None
        self.entry_price = 0.0
        self.entry_time = None
        self.trailing_price = None
        self.position_size_usdt = 0.0
        self.qty = 0.0

    def update(self, price):
        if self.position != "BUY":
            return

        pnl_pct_raw = (price - self.entry_price) / self.entry_price * 100

        if price <= self.entry_price * (1 - self.SL_PERCENT / 100):
            self.close_position(price, "SL")
            return

        if price >= self.entry_price * (1 + self.TP_PERCENT / 100):
            self.close_position(price, "TP")
            return

        if price > self.trailing_price:
            self.trailing_price = price

        if price <= self.trailing_price * (1 - self.TRAIL_PERCENT / 100):
            self.close_position(price, "TRAIL")
            return

        trade_age = (datetime.now() - self.entry_time).total_seconds()

        if trade_age >= self.MAX_TRADE_SECONDS and pnl_pct_raw < 0.20:
            self.close_position(price, "TIME_STOP")
            return

    def force_close_on_opposite_signal(self, price):
        if self.position == "BUY":
            self.close_position(price, "OPPOSITE_SIGNAL")
