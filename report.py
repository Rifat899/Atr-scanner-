import requests
import json
from datetime import datetime, timezone
from html import escape

from scanner import get_candles, calculate_atr, get_price, format_price

BOT_TOKEN = __import__("os").environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = __import__("os").environ["TELEGRAM_CHAT_ID"]

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

    print("ATR MARKET DASHBOARD")

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

        rows.append(
            f"{token_name:<6} "
            f"{price:<12}"
            f"{values['4H']:>6}"
            f"{values['1D']:>7}"
            f"{values['1W']:>7}"
        )

    header = (
        f"{'TOKEN':<6} "
        f"{'PRICE':<12}"
        f"{'4H':>6}"
        f"{'1D':>7}"
        f"{'1W':>7}"
    )

    title = (
        "📊 ATR MARKET DASHBOARD\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        + datetime.now(timezone.utc).strftime("%d %b %Y %H:%M UTC")
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

    print("\nDashboard sent successfully.")
    print("Tokens scanned:", len(tokens))


if __name__ == "__main__":
    main()
