import os
import requests
import json
from datetime import datetime, timezone
from html import escape

from scanner import get_candles, calculate_atr, get_price, format_price

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"


def send_report(message):
    response = requests.post(
        TELEGRAM_API,
        data={
            "chat_id": CHAT_ID,
            "text": message,
            "parse_mode": "HTML"
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

    rows = []

    print("ATR MARKET SNAPSHOT")
    print("Time:", datetime.now(timezone.utc).isoformat())

    for symbol in tokens:
        try:
            price = format_price(get_price(symbol))
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

                values[label] = f"{current:.4f}%"

            except Exception as error:
                print(f"{symbol} {label} ERROR: {error}")
                values[label] = "ERROR"

        token_name = symbol[:-4] if symbol.endswith("USDT") else symbol

        rows.append(
            f"{token_name:<12} "
            f"{price:>16} "
            f"{values['4H']:>10} "
            f"{values['1D']:>10} "
            f"{values['1W']:>10}"
        )

    header = (
        f"{'TOKEN':<12} "
        f"{'PRICE':>16} "
        f"{'4H ATR%':>10} "
        f"{'1D ATR%':>10} "
        f"{'1W ATR%':>10}"
    )

    title = (
        "ATR MARKET SNAPSHOT\n"
        + datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    )

    chunks = []
    current_rows = []

    for row in rows:
        test_message = (
            f"{title}\n\n"
            f"{header}\n"
            + "\n".join(current_rows + [row])
        )

        if len(test_message) > 3500 and current_rows:
            chunks.append(current_rows)
            current_rows = [row]
        else:
            current_rows.append(row)

    if current_rows:
        chunks.append(current_rows)

    for chunk_rows in chunks:
        report = (
            f"{title}\n\n"
            f"<pre>{escape(header)}\n"
            f"{escape(chr(10).join(chunk_rows))}</pre>"
        )

        send_report(report)

    print("\nSnapshot sent successfully.")
    print("Tokens scanned:", len(tokens))


if __name__ == "__main__":
    main()
