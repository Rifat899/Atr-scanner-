import os
import requests
import json

from scanner import get_candles, calculate_atr, get_price, format_price

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"


def send_report(message):
    response = requests.post(
        TELEGRAM_API,
        data={
            "chat_id": CHAT_ID,
            "text": message
        },
        timeout=30
    )

    response.raise_for_status()

    if not response.json().get("ok"):
        raise RuntimeError("Telegram report was not accepted")


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

    header = "TOKEN  PRICE       4H     1D     1W"

    rows = []

    print("ATR MARKET REPORT")

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
            f"{token_name:<5} "
            f"{price:<11} "
            f"{values['4H']:>5} "
            f"{values['1D']:>5} "
            f"{values['1W']:>5}"
        )

        rows.append(row)
        print(row)

    chunks = []
    current_rows = [header]

    for row in rows:
        test_message = "\n".join(current_rows + [row])

        if len(test_message) > 3500:
            chunks.append("\n".join(current_rows))
            current_rows = [header, row]
        else:
            current_rows.append(row)

    if current_rows:
        chunks.append("\n".join(current_rows))

    for chunk in chunks:
        send_report(chunk)

    print("\nReport sent successfully.")
    print("Tokens scanned:", len(tokens))


if __name__ == "__main__":
    main()
