import json

CANDIDATES_FILE = "binance_top100_candidates.json"
WATCHLIST_FILE = "watchlist.json"


def main():
    with open(CANDIDATES_FILE, "r") as file:
        candidates = json.load(file)

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

    print("ATR SCANNER WATCHLIST UPDATED")
    print("--------------------------------")
    print("New tokens added:", len(added))
    print("Total watchlist tokens:", len(tokens))

    print("\nADDED TOKENS")
    for symbol in added:
        print(symbol)

    print("\nExisting tokens preserved.")
    print("All new tokens enabled.")


if __name__ == "__main__":
    main()
