import requests
import json
from datetime import datetime, timezone

BINANCE_URL = "https://data-api.binance.vision/api/v3/klines"

ATR_LENGTH = 14

TIMEFRAMES = {
    "4H": "4h",
    "1D": "1d",
    "1W": "1w"
}


def get_candles(symbol, interval):
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": 250
    }

    response = requests.get(BINANCE_URL, params=params, timeout=20)
    response.raise_for_status()

    candles = response.json()

    # Exclude the currently forming candle
    return candles[:-1]


def calculate_atr(candles):
    if len(candles) < ATR_LENGTH + 1:
        raise ValueError("Not enough candles")

    true_ranges = []

    for i in range(1, len(candles)):
        high = float(candles[i][2])
        low = float(candles[i][3])
        previous_close = float(candles[i - 1][4])

        true_range = max(
            high - low,
            abs(high - previous_close),
            abs(low - previous_close)
        )

        true_ranges.append(true_range)

    # Initial ATR: average of first 14 true ranges
    atr = sum(true_ranges[:ATR_LENGTH]) / ATR_LENGTH

    # Wilder's RMA
    for tr in true_ranges[ATR_LENGTH:]:
        atr = ((atr * (ATR_LENGTH - 1)) + tr) / ATR_LENGTH

    close = float(candles[-1][4])
    atr_percent = (atr / close) * 100

    return atr, atr_percent, close


def main():
    with open("watchlist.json", "r") as file:
        watchlist = json.load(file)

    symbols = [
        token["symbol"]
        for token in watchlist["tokens"]
        if token["enabled"]
    ]

    print("ATR% SCANNER TEST")
    print("Time:", datetime.now(timezone.utc).isoformat())

    for symbol in symbols:
        print(f"\n{symbol}")

        for label, interval in TIMEFRAMES.items():
            try:
                candles = get_candles(symbol, interval)
                atr, atr_percent, close = calculate_atr(candles)

                print(
                    f"{label}: ATR={atr:.6f} | "
                    f"ATR%={atr_percent:.4f}% | "
                    f"Price=${close:,.4f}"
                )

            except Exception as error:
                print(f"{label}: ERROR - {error}")


if __name__ == "__main__":
    main()