import os
import requests
import json

from scanner import get_candles, calculate_atr, get_price, format_price

DISCORD_WEBHOOK = os.environ["DISCORD_WEBHOOK_URL"]


def send_report(message):
    response = requests.post(
        DISCORD_WEBHOOK,
        json={"content": message},
        timeout=30
    )

    response.raise_for_status()


def main():
    with open("watchlist.json", "r") as file:
        watchlist = json.load(file)

    with open("settings.json", "r") as file:
        settings = json.load(file)

    length = settings["atr_length"]

    tokens = [
        token["symbol"]
        for token in watchlist["tokens"]
        if token["enabled"]
    ]

    header = (
        f"{'TOKEN':<5} | "
        f"{'PRICE':>12}    "
        f"{'4H':>6}    "
        f"{'1D':>6}    "
        f"{'1W':>6}"
    )

    separator = "-" * len(header)

    rows = []

    print("ATR DISCORD REPORT")

    for symbol in tokens:
        try:
            price = format_price(get_price(symbol)).replace("$", "")
        except Exception as error:
            print(f"{symbol} PRICE ERROR: {error}")
            price = "ERROR"

        values = {}

        for label, interval in {
            "4H": "4h",
            "1D": "1d",
            "1W": "1w"
        }.items():
            try:
                current, previous = calculate_atr(
                    get_candles(symbol, interval),
                    length
                )
                values[label] = f"{current:.2f}"

            except Exception as error:
                print(f"{symbol} {label} ERROR: {error}")
                values[label] = "N/A"

        token_name = (
            symbol[:-4]
            if symbol.endswith("USDT")
            else symbol
        )

        row = (
            f"{token_name:<5} | "
            f"{price:>12}    "
            f"{values['4H']:>6}    "
            f"{values['1D']:>6}    "
            f"{values['1W']:>6}"
        )

        rows.append(row)
        print(row)

    chunks = []
    current_rows = []

    for row in rows:
        content = "\n".join(
            [header, separator] + current_rows + [row]
        )
        test_message = f"```\n{content}\n```"

        if len(test_message) > 1900 and current_rows:
            content = "\n".join(
                [header, separator] + current_rows
            )
            chunks.append(f"```\n{content}\n```")
            current_rows = [row]
        else:
            current_rows.append(row)

    if current_rows:
        content = "\n".join(
            [header, separator] + current_rows
        )
        chunks.append(f"```\n{content}\n```")

    for chunk in chunks:
        send_report(chunk)

    print("\nDiscord report sent successfully.")
    print("Tokens scanned:", len(tokens))


if __name__ == "__main__":
    main()
