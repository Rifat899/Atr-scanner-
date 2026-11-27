import json
import time
import requests
from collections import Counter

COINGECKO_API = "https://api.coingecko.com/api/v3/coins/markets"
BINANCE_API = "https://data-api.binance.vision/api/v3/exchangeInfo"

CANDIDATES_FILE = "binance_top100_candidates.json"
WATCHLIST_FILE = "watchlist.json"

EXCLUDED_SYMBOLS = {
    "USDC", "USDS", "USDE", "USD1",
    "RLUSD", "TUSD", "BFUSD", "U",
    "XAUT", "PAXG", "GRAM"
}


def get_coingecko_top100():
    params = {
        "vs_currency": "usd",
        "order": "market_cap_desc",
        "per_page": 100,
        "page": 1,
        "sparkline": "false"
    }

    headers = {"User-Agent": "ATR-Scanner/1.0"}

    for attempt in range(3):
        response = requests.get(
            COINGECKO_API,
            params=params,
            headers=headers,
            timeout=30
        )

        if response.status_code == 429:
            print("CoinGecko rate limit. Retrying...")
            time.sleep(15)
            continue

        response.raise_for_status()
        return response.json()

    raise RuntimeError("CoinGecko rate limit. Please try again later.")


def get_binance_spot_pairs():
    response = requests.get(BINANCE_API, timeout=30)
    response.raise_for_status()

    pairs = set()

    for item in response.json()["symbols"]:
        if (
            item.get("status") == "TRADING"
            and item.get("isSpotTradingAllowed") is True
            and item.get("quoteAsset") == "USDT"
        ):
            pairs.add(item["symbol"])

    return pairs


def main():
    print("Fetching fresh CoinGecko top 100...")
    coins = get_coingecko_top100()

    print("Checking Binance USDT spot pairs...")
    binance_pairs = get_binance_spot_pairs()

    symbol_counts = Counter(
        coin["symbol"].upper() for coin in coins
    )

    candidates = []
    skipped = []

    for coin in coins:
        symbol = coin["symbol"].upper()
        name = coin["name"]

        if symbol in EXCLUDED_SYMBOLS:
            skipped.append(name + ": excluded")
            continue

        if symbol_counts[symbol] > 1:
            skipped.append(name + ": duplicate symbol")
            continue

        binance_symbol = symbol + "USDT"

        if binance_symbol not in binance_pairs:
            skipped.append(name + ": no active Binance USDT pair")
            continue

        candidates.append({
            "rank": coin.get("market_cap_rank"),
            "name": name,
            "symbol": symbol,
            "binance_symbol": binance_symbol,
            "market_cap": coin.get("market_cap")
        })

    candidates.sort(
        key=lambda item: item["rank"] or 9999
    )

    with open(CANDIDATES_FILE, "w") as file:
        json.dump(candidates, file, indent=2)

    with open(WATCHLIST_FILE, "r") as file:
        watchlist = json.load(file)

    tokens = watchlist["tokens"]

    existing_symbols = {
        token["symbol"] for token in tokens
    }

    added = []

    for coin in candidates:
        symbol = coin["binance_symbol"]

        if symbol in existing_symbols:
            continue

        tokens.append({
            "symbol": symbol,
            "enabled": True
        })

        existing_symbols.add(symbol)
        added.append(symbol)

    with open(WATCHLIST_FILE, "w") as file:
        json.dump(watchlist, file, indent=2)

    print("\nUPDATE COMPLETE")
    print("----------------------------")
    print("Fresh candidates:", len(candidates))
    print("New tokens added:", len(added))
    print("Skipped:", len(skipped))
    print("Total watchlist:", len(tokens))
    print("----------------------------")

    print("\nNew tokens:")
    for symbol in added:
        print(symbol)

    print("\nExisting watchlist tokens preserved.")


if __name__ == "__main__":
    main()
