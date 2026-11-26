import requests
import json
from datetime import datetime, timezone
from conditions import check_conditions
from alert_manager import load_state, save_state, get_new_triggers

BINANCE_URL = "https://data-api.binance.vision/api/v3/klines"

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

    return response.json()[:-1]


def calculate_atr(candles, length):
    if len(candles) < length + 2:
        raise ValueError("Not enough candles")

    true_ranges = []

    for i in range(1, len(candles)):
        high = float(candles[i][2])
        low = float(candles[i][3])
        previous_close = float(candles[i - 1][4])

        tr = max(
            high - low,
            abs(high - previous_close),
            abs(low - previous_close)
        )

        true_ranges.append(tr)

    atr = sum(true_ranges[:length]) / length
    atr_values = [atr]

    for tr in true_ranges[length:]:
        atr = ((atr * (length - 1)) + tr) / length
        atr_values.append(atr)

    current_atr = atr_values[-1]
    previous_atr = atr_values[-2]

    current_close = float(candles[-1][4])
    previous_close = float(candles[-2][4])

    current_percent = current_atr / current_close * 100
    previous_percent = previous_atr / previous_close * 100

    return current_percent, previous_percent, current_close


def main():
    with open("watchlist.json", "r") as file:
        watchlist = json.load(file)

    with open("settings.json", "r") as file:
        settings = json.load(file)

    state = load_state()
    length = settings["atr_length"]

    symbols = [
        token["symbol"]
        for token in watchlist["tokens"]
        if token["enabled"]
    ]

    alert_blocks = []

    print("ATR% SCANNER")
    print("Time:", datetime.now(timezone.utc).isoformat())

    for symbol in symbols:
        results = {}
        new_alerts = {}
        price = None

        print(f"\n{symbol}")

        for label, interval in TIMEFRAMES.items():
            try:
                current, previous, close = calculate_atr(
                    get_candles(symbol, interval),
                    length
                )

                triggered = check_conditions(
                    current,
                    previous,
                    settings["conditions"][label]
                )

                new_triggers = get_new_triggers(
                    symbol,
                    label,
                    triggered,
                    state
                )

                results[label] = current
                new_alerts[label] = new_triggers

                if label == "4H":
                    price = close

                condition_text = ",".join(triggered) if triggered else "-"

                print(
                    f"{label}: {current:.4f}% "
                    f"| Price=${close:,.4f} "
                    f"| Conditions: {condition_text}"
                )

            except Exception as error:
                print(f"{label}: ERROR - {error}")

        if any(new_alerts.get(label) for label in TIMEFRAMES):
            lines = [f"{symbol} | ${price:,.4f}"]

            for label in TIMEFRAMES:
                if label in results:
                    conditions = new_alerts.get(label, [])
                    condition_text = ",".join(conditions) if conditions else "-"

                    lines.append(
                        f"{label}: {results[label]:.2f}% [{condition_text}]"
                    )

            alert_blocks.append("\n".join(lines))

    save_state(state)

    print("\nNEW ALERTS")

    if alert_blocks:
        print("\n\n".join(alert_blocks))
    else:
        print("No new alerts")


if __name__ == "__main__":
    main()
