import json
import requests
from collections import Counter

CMC_URL = "https://pro-api.coinmarketcap.com/public-api/v3/cryptocurrency/listings/latest"
BINANCE_URL = "https://data-api.binance.vision/api/v3/exchangeInfo"

# Get CMC top 100
params = {
    "start": 1,
    "limit": 100,
    "convert": "USD"
}

cmc_response = requests.get(CMC_URL, params=params, timeout=20)
cmc_response.raise_for_status()
coins = cmc_response.json()["data"]

# Get Binance spot trading pairs
binance_response = requests.get(BINANCE_URL, timeout=30)
binance_response.raise_for_status()
exchange_info = binance_response.json()

binance_pairs = {
    item["baseAsset"]
    for item in exchange_info["symbols"]
    if item["status"] == "TRADING"
    and item["quoteAsset"] == "USDT"
    and item.get("isSpotTradingAllowed", False)
}

# Read existing watchlist
with open("watchlist.json", "r") as file:
    watchlist = json.load(file)

tokens = watchlist["tokens"]

existing_symbols = {
    token["symbol"] for token in tokens
}

# Identify duplicate CMC symbols
symbol_counts = Counter(coin["symbol"] for coin in coins)

added = []
skipped = []

# Add new matching tokens
for coin in coins:
    symbol = coin["symbol"]

    if symbol_counts[symbol] > 1:
        skipped.append(symbol + " (ambiguous)")
        continue

    if symbol not in binance_pairs:
        continue

    if symbol in existing_symbols:
        continue

    tokens.append({
        "symbol": symbol,
        "enabled": True,
        "name": coin["name"],
        "cmc_rank": coin["cmc_rank"]
    })

    existing_symbols.add(symbol)
    added.append(symbol)

# Save watchlist
with open("watchlist.json", "w") as file:
    json.dump(watchlist, file, indent=2)

print("WATCHLIST UPDATE COMPLETE")
print("New tokens added:", len(added))
print("Total tokens:", len(tokens))
print("Existing tokens preserved")

print("\nNEW TOKENS")
for symbol in added:
    print(symbol)

print("\nSKIPPED AMBIGUOUS TOKENS")
for symbol in skipped:
    print(symbol)
