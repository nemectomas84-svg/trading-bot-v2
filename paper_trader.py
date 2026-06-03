class PaperTrader:
    def __init__(self):
        self.position = None
        self.entry_price = 0
        self.stop_loss = 0
        self.trailing_stop = 0
        self.balance = 1000  # štart kapitál
        self.trade_size = 100  # veľkosť jedného trade

    def open_position(self, signal, price):
        if self.position is not None:
            return

        self.position = signal
        self.entry_price = price

        if signal == "BUY":
            self.stop_loss = price * 0.995  # -0.5%
            self.trailing_stop = price * 0.997
        else:
            self.stop_loss = price * 1.005
            self.trailing_stop = price * 1.003

        print(f"📈 OPEN {signal} at {price:.2f}")

    def update(self, price):
        if self.position is None:
            return

        if self.position == "BUY":
            # trailing stop
            new_trailing = price * 0.997
            if new_trailing > self.trailing_stop:
                self.trailing_stop = new_trailing

            # exit
            if price <= self.stop_loss or price <= self.trailing_stop:
                profit = (price - self.entry_price) / self.entry_price
                self.balance += self.trade_size * profit
                print(f"❌ CLOSE BUY at {price:.2f} | PnL: {profit*100:.2f}% | BALANCE: {self.balance:.2f}")
                self.position = None

        if self.position == "SELL":
            new_trailing = price * 1.003
            if new_trailing < self.trailing_stop:
                self.trailing_stop = new_trailing

            if price >= self.stop_loss or price >= self.trailing_stop:
                profit = (self.entry_price - price) / self.entry_price
                self.balance += self.trade_size * profit
                print(f"❌ CLOSE SELL at {price:.2f} | PnL: {profit*100:.2f}% | BALANCE: {self.balance:.2f}")
                self.position = None
