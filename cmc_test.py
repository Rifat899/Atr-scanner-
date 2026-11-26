import requests

URL = "https://pro-api.coinmarketcap.com/public-api/v3/cryptocurrency/listings/latest"

params = {
    "start": 1,
    "limit": 100,
    "convert": "USD"
}

response = requests.get(URL, params=params, timeout=20)
response.raise_for_status()

data = response.json()["data"]

print("COINMARKETCAP TOP 100 TEST")
print("Coins received:", len(data))

for coin in data:
    print(
        coin["cmc_rank"],
        coin["name"],
        coin["symbol"]
    )
