from binance.client import Client

# API keys (môžu byť None – funguje aj bez nich)
client = Client()


def get_price(symbol="BTCUSDT"):
    ticker = client.get_symbol_ticker(symbol=symbol)
    return ticker["price"]
