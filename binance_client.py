from binance.client import Client

class BinanceClient:
    def __init__(self):
        self.client = Client()  # public data, netreba API key

    def get_price(self, symbol="BTCUSDT"):
        ticker = self.client.get_symbol_ticker(symbol=symbol)
        return float(ticker["price"])
