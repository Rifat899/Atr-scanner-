import requests
from collections import Counter

CMC_URL = "https://pro-api.coinmarketcap.com/public-api/v3/cryptocurrency/listings/latest"
BINANCE_URL = "https://data-api.binance.vision/api/v3/exchangeInfo"

params = {
    "start": 1,
    "limit": 100,
    "convert": "USD"
}

cmc_response = requests.get(CMC_URL, params=params, timeout=20)
cmc_response.raise_for_status()
coins = cmc_response.json()["data"]

binance_response = requests.get(BINANCE_URL, timeout=30)
binance_response.raise_for_status()
exchange_info = binance_response.json()

cmc_counts = Counter(coin["symbol"] for coin in coins)

binance_pairs = {
    item["baseAsset"]
    for item in exchange_info["symbols"]
    if item["status"] == "TRADING"
    and item["quoteAsset"] == "USDT"
    and item.get("isSpotTradingAllowed", False)
}

matched = []
unmatched = []
ambiguous = []

for coin in coins:
    symbol = coin["symbol"]

    if cmc_counts[symbol] > 1:
        ambiguous.append(coin)
    elif symbol in binance_pairs:
        matched.append(coin)
    else:
        unmatched.append(coin)

print("CMC TO BINANCE MAPPING TEST")
print("CMC coins:", len(coins))
print("Matched:", len(matched))
print("Not matched:", len(unmatched))
print("Ambiguous:", len(ambiguous))

print("\nMATCHED COINS")
for coin in matched:
    print(coin["symbol"] + "USDT", "-", coin["name"])

print("\nNOT MATCHED")
for coin in unmatched:
    print(coin["symbol"], "-", coin["name"])

print("\nAMBIGUOUS")
for coin in ambiguous:
    print(coin["symbol"], "-", coin["name"])
