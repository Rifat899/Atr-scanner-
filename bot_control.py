import os
import json
import requests

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
GH_TOKEN = os.environ.get("GH_ACTIONS_TOKEN", "")

MY_CHAT_ID = 1221378175

API = f"https://api.telegram.org/bot{BOT_TOKEN}"

GITHUB_API = (
    "https://api.github.com/repos/"
    "Rifat899/Atr-scanner-/"
    "actions/workflows/scanner-test.yml/dispatches"
)

SETTINGS_FILE = "settings.json"
OFFSET_FILE = "bot_update_offset.json"


def send_message(text):
    response = requests.post(
        f"{API}/sendMessage",
        data={
            "chat_id": MY_CHAT_ID,
            "text": text
        },
        timeout=20
    )

    response.raise_for_status()

    if not response.json().get("ok"):
        raise RuntimeError("Telegram message failed")


def trigger_scan():
    if not GH_TOKEN:
        return "Scan failed: GitHub token is missing."

    try:
        response = requests.post(
            GITHUB_API,
            headers={
                "Authorization": f"Bearer {GH_TOKEN}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28"
            },
            json={"ref": "main"},
            timeout=20
        )

        if response.status_code == 204:
            return (
                "SCAN REQUESTED\n\n"
                "GitHub Actions will start the ATR scanner."
            )

        return (
            f"Scan request failed: HTTP {response.status_code}\n"
            f"{response.text[:300]}"
        )

    except requests.RequestException as error:
        return f"Scan request failed: {error}"


def load_settings():
    with open(SETTINGS_FILE, "r") as file:
        return json.load(file)


def save_settings(settings):
    with open(SETTINGS_FILE, "w") as file:
        json.dump(settings, file, indent=2)


def load_offset():
    if not os.path.exists(OFFSET_FILE):
        return 0

    with open(OFFSET_FILE, "r") as file:
        return json.load(file)["offset"]


def save_offset(offset):
    with open(OFFSET_FILE, "w") as file:
        json.dump({"offset": offset}, file, indent=2)


def show_settings(settings):
    lines = ["ATR SCANNER SETTINGS", ""]

    for timeframe in ["4H", "1D", "1W"]:
        lines.append(timeframe)

        for condition in ["C1", "C2", "C3", "C4"]:
            config = settings["conditions"][timeframe][condition]
            status = "ON" if config["enabled"] else "OFF"

            lines.append(
                f"{condition}: {status} | Threshold: {config['threshold']}"
            )

        lines.append("")

    return "\n".join(lines)


def show_help():
    return (
        "ATR SCANNER COMMANDS\n\n"
        "/scan - Run ATR scanner now\n"
        "/settings - Show all settings\n"
        "/help - Show commands\n\n"
        "ENABLE WITH THRESHOLD:\n"
        "/c1 4H on 0.5\n"
        "/c2 1D on 5\n\n"
        "DISABLE:\n"
        "/c1 4H off\n\n"
        "Conditions: C1, C2, C3, C4\n"
        "Timeframes: 4H, 1D, 1W"
    )


def process_command(text, settings):
    parts = text.strip().split()

    if not parts:
        return None

    command = parts[0].split("@")[0].lower()

    if command == "/start":
        return "ATR Scanner Bot connected. Send /help to see commands."

    if command == "/help":
        return show_help()

    if command == "/settings":
        return show_settings(settings)

    if command == "/scan":
        return trigger_scan()
    if command == "/price":
    if len(parts) != 2:
        return "Usage: /price BTC"

    return get_price(parts[1])
def get_price(symbol):
    symbol = symbol.upper()

    if not symbol.endswith("USDT"):
        symbol += "USDT"

    url = "https://data-api.binance.vision/api/v3/ticker/price"

    response = requests.get(
        url,
        params={"symbol": symbol},
        timeout=15
    )

    if response.status_code != 200:
        return f"Price unavailable for {symbol}"

    data = response.json()

    return f"{symbol}: ${float(data['price']):,.8f}"

    if command not in ["/c1", "/c2", "/c3", "/c4"]:
        return "Unknown command. Send /help."

    if len(parts) not in [3, 4]:
        return "Invalid format. Example: /c1 4H on 0.5"

    condition = command.upper()[1:]
    timeframe = parts[1].upper()
    action = parts[2].lower()

    if timeframe not in ["4H", "1D", "1W"]:
        return "Invalid timeframe. Use 4H, 1D or 1W."

    if action not in ["on", "off"]:
        return "Use ON or OFF."

    config = settings["conditions"][timeframe][condition]

    if action == "on" and len(parts) != 4:
        return "Please provide a threshold. Example: /c1 4H on 0.5"

    if len(parts) == 4:
        try:
            threshold = float(parts[3])

            if threshold < 0 or threshold > 100000:
                return "Threshold must be between 0 and 100000."

        except ValueError:
            return "Invalid threshold. Please enter a number."

        config["threshold"] = threshold

    config["enabled"] = action == "on"

    save_settings(settings)

    status = "ENABLED" if config["enabled"] else "DISABLED"

    return (
        f"{condition} {timeframe} {status}\n"
        f"Threshold: {config['threshold']}"
    )


def main():
    settings = load_settings()
    offset = load_offset()

    response = requests.get(
        f"{API}/getUpdates",
        params={
            "offset": offset,
            "timeout": 0,
            "limit": 100
        },
        timeout=20
    )

    response.raise_for_status()
    data = response.json()

    if not data.get("ok"):
        raise RuntimeError("Could not retrieve Telegram updates")

    updates = data["result"]

    for update in updates:
        update_id = update["update_id"]

        message = update.get("message", {})
        chat = message.get("chat", {})

        # Only accept commands from your private chat
        if (
            str(chat.get("id")) == str(MY_CHAT_ID)
            and chat.get("type") == "private"
        ):
            text = message.get("text", "")

            if text.startswith("/"):
                reply = process_command(text, settings)

                if reply:
                    send_message(reply)

        offset = update_id + 1

    save_offset(offset)

    if updates:
        print("Processed updates:", len(updates))
    else:
        print("No new commands")


if __name__ == "__main__":
    main()
