import csv
import os
import json
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

        self.SL_PERCENT = 0.12
        self.TP_PERCENT = 0.60
        self.TRAIL_PERCENT = 0.08
        self.TRAILING_ACTIVATION_PERCENT = 0.08
        self.MAX_TRADE_SECONDS = 15 * 60

        self.trailing_price = None

        self.max_profit_seen = 0.0
        self.max_drawdown_seen = 0.0

        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.total_pnl = 0.0

        self.last_trade = None
        self.trade_history = []

        self.current_price = 0.0
        self.current_pnl = 0.0
        self.current_pnl_pct = 0.0
        self.current_trade_duration_sec = 0.0

        self.STATE_FILE = "trader_state.json"
        self.ENABLE_FILE_LOGGING = False

        self.init_log()
        self.save_state()

    def init_log(self):
        if not self.ENABLE_FILE_LOGGING:
            return

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
                    "balance",
                    "trade_duration_sec",
                    "max_profit_seen_pct",
                    "max_drawdown_seen_pct"
                ])

    def _read_existing_market_state(self):
        if not os.path.exists(self.STATE_FILE):
            return None

        try:
            with open(self.STATE_FILE, "r") as f:
                state = json.load(f)
                return state.get("market")
        except:
            return None

    def save_state(self):
        win_rate = 0.0
        if self.total_trades > 0:
            win_rate = self.winning_trades / self.total_trades * 100

        total_pnl_pct = ((self.balance - self.initial_balance) / self.initial_balance) * 100

        market_state = self._read_existing_market_state()

        state = {
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "initial_balance": round(self.initial_balance, 2),
            "balance": round(self.balance, 2),

            "position": self.position,
            "entry_price": round(self.entry_price, 2),
            "current_price": round(self.current_price, 2) if self.current_price else 0.0,
            "position_size_usdt": round(self.position_size_usdt, 2),
            "qty": round(self.qty, 8),
            "trailing_price": round(self.trailing_price, 2) if self.trailing_price else None,

            "current_pnl": round(self.current_pnl, 4),
            "current_pnl_pct": round(self.current_pnl_pct, 4),
            "current_trade_duration_sec": round(self.current_trade_duration_sec, 2),

            "max_profit_seen": round(self.max_profit_seen, 4),
            "max_drawdown_seen": round(self.max_drawdown_seen, 4),

            "total_trades": self.total_trades,
            "winning_trades": self.winning_trades,
            "losing_trades": self.losing_trades,
            "win_rate": round(win_rate, 2),
            "total_pnl": round(self.total_pnl, 4),
            "total_pnl_pct": round(total_pnl_pct, 4),

            "last_trade": self.last_trade,
            "trade_history": self.trade_history[-10:],

            "settings": {
                "SL_PERCENT": self.SL_PERCENT,
                "TP_PERCENT": self.TP_PERCENT,
                "TRAIL_PERCENT": self.TRAIL_PERCENT,
                "TRAILING_ACTIVATION_PERCENT": self.TRAILING_ACTIVATION_PERCENT,
                "MAX_TRADE_SECONDS": self.MAX_TRADE_SECONDS,
            }
        }

        if market_state is not None:
            state["market"] = market_state

        with open(self.STATE_FILE, "w") as f:
            json.dump(state, f, indent=2)

    def log_trade(
        self,
        action,
        price,
        reason,
        pnl=0.0,
        pnl_pct=0.0,
        fees=0.0,
        trade_duration_sec=0,
        max_profit_seen_pct=0.0,
        max_drawdown_seen_pct=0.0,
    ):
        if not self.ENABLE_FILE_LOGGING:
            return

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
                round(self.balance, 2),
                round(trade_duration_sec, 2),
                round(max_profit_seen_pct, 4),
                round(max_drawdown_seen_pct, 4),
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

        self.current_price = price
        self.current_pnl = 0.0
        self.current_pnl_pct = 0.0
        self.current_trade_duration_sec = 0.0

        self.max_profit_seen = 0.0
        self.max_drawdown_seen = 0.0

        entry_fee = self.position_size_usdt * self.fee_rate
        self.balance -= entry_fee

        print(f"📈 OPEN BUY at {execution_price:.2f} | fee: {entry_fee:.2f}")

        self.log_trade(
            "OPEN_BUY",
            execution_price,
            "signal",
            0.0,
            0.0,
            entry_fee,
            0,
            0.0,
            0.0,
        )

        self.save_state()

    def close_position(self, price, reason):
        if self.position != "BUY":
            return

        execution_price = price * (1 - self.slippage_rate)

        gross_pnl = (execution_price - self.entry_price) * self.qty
        exit_value = self.qty * execution_price
        exit_fee = exit_value * self.fee_rate

        net_pnl = gross_pnl - exit_fee
        pnl_pct = net_pnl / self.position_size_usdt * 100

        trade_duration_sec = 0
        if self.entry_time is not None:
            trade_duration_sec = (datetime.now() - self.entry_time).total_seconds()

        self.balance += net_pnl

        self.total_trades += 1
        self.total_pnl += net_pnl

        if net_pnl > 0:
            self.winning_trades += 1
            result = "WIN"
        else:
            self.losing_trades += 1
            result = "LOSS"

        closed_trade = {
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "side": "BUY",
            "entry_price": round(self.entry_price, 2),
            "exit_price": round(execution_price, 2),
            "reason": reason,
            "pnl": round(net_pnl, 4),
            "pnl_pct": round(pnl_pct, 4),
            "fees": round(exit_fee, 4),
            "duration_sec": round(trade_duration_sec, 2),
            "max_profit_seen_pct": round(self.max_profit_seen, 4),
            "max_drawdown_seen_pct": round(self.max_drawdown_seen, 4),
            "result": result,
            "balance_after": round(self.balance, 2),
        }

        self.last_trade = closed_trade
        self.trade_history.insert(0, closed_trade)
        self.trade_history = self.trade_history[:50]

        print(
            f"❌ CLOSE BUY at {execution_price:.2f} | {reason} | "
            f"PNL: {net_pnl:.2f} ({pnl_pct:.2f}%) | "
            f"MAX PROFIT: {self.max_profit_seen:.2f}% | "
            f"MAX DD: {self.max_drawdown_seen:.2f}% | "
            f"DURATION: {trade_duration_sec:.0f}s | "
            f"BALANCE: {self.balance:.2f}"
        )

        self.log_trade(
            "CLOSE_BUY",
            execution_price,
            reason,
            net_pnl,
            pnl_pct,
            exit_fee,
            trade_duration_sec,
            self.max_profit_seen,
            self.max_drawdown_seen,
        )

        self.position = None
        self.entry_price = 0.0
        self.entry_time = None
        self.trailing_price = None
        self.position_size_usdt = 0.0
        self.qty = 0.0

        self.current_price = 0.0
        self.current_pnl = 0.0
        self.current_pnl_pct = 0.0
        self.current_trade_duration_sec = 0.0

        self.max_profit_seen = 0.0
        self.max_drawdown_seen = 0.0

        self.save_state()

    def update(self, price):
        self.current_price = price

        if self.position != "BUY":
            self.current_pnl = 0.0
            self.current_pnl_pct = 0.0
            self.current_trade_duration_sec = 0.0
            self.save_state()
            return

        gross_pnl = (price - self.entry_price) * self.qty
        current_value = self.qty * price
        estimated_exit_fee = current_value * self.fee_rate

        self.current_pnl = gross_pnl - estimated_exit_fee
        self.current_pnl_pct = self.current_pnl / self.position_size_usdt * 100

        pnl_pct_raw = (price - self.entry_price) / self.entry_price * 100

        if self.entry_time is not None:
            self.current_trade_duration_sec = (
                datetime.now() - self.entry_time
            ).total_seconds()

        print(
            f"POSITION=BUY | ENTRY={self.entry_price:.2f} | "
            f"CURRENT={price:.2f} | PNL_RAW={pnl_pct_raw:.3f}% | "
            f"PNL_NET={self.current_pnl:.2f} ({self.current_pnl_pct:.3f}%) | "
            f"TRAILING_PRICE={self.trailing_price:.2f}"
        )

        if pnl_pct_raw > self.max_profit_seen:
            self.max_profit_seen = pnl_pct_raw

        if pnl_pct_raw < self.max_drawdown_seen:
            self.max_drawdown_seen = pnl_pct_raw

        self.save_state()

        if price <= self.entry_price * (1 - self.SL_PERCENT / 100):
            self.close_position(price, "SL")
            return

        if price >= self.entry_price * (1 + self.TP_PERCENT / 100):
            self.close_position(price, "TP")
            return

        if pnl_pct_raw >= self.TRAILING_ACTIVATION_PERCENT:
            if price > self.trailing_price:
                self.trailing_price = price

            if price <= self.trailing_price * (1 - self.TRAIL_PERCENT / 100):
                self.close_position(price, "TRAIL")
                return

        trade_age = (datetime.now() - self.entry_time).total_seconds()

        if trade_age >= self.MAX_TRADE_SECONDS and pnl_pct_raw < 0.15:
            self.close_position(price, "TIME_STOP")
            return

    def force_close_on_opposite_signal(self, price):
        if self.position == "BUY":
            self.close_position(price, "OPPOSITE_SIGNAL")
