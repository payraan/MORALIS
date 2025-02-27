from fastapi import FastAPI
import requests
import os
import uvicorn

app = FastAPI()

# دریافت API Key از متغیر محیطی
MORALIS_API_KEY = os.getenv("MORALIS_API_KEY")
BASE_URL = "https://solana-gateway.moralis.io"
HEADERS = {
    "Accept": "application/json",
    "X-API-Key": MORALIS_API_KEY
}

@app.get("/")
def home():
    return {"message": "✅ API Moralis روی سرور اجرا شده است!"}

# 1. دریافت اطلاعات توکن
@app.get("/token-info/{network}/{address}")
def get_token_info(network: str, address: str):
    url = f"{BASE_URL}/token/{network}/{address}/metadata"
    return requests.get(url, headers=HEADERS).json()

# 2. دریافت لیست توکن‌های کیف پول
@app.get("/wallet-spl-tokens/{network}/{address}")
def get_wallet_tokens(network: str, address: str):
    url = f"{BASE_URL}/account/{network}/{address}/tokens"
    return requests.get(url, headers=HEADERS).json()

# 3. دریافت موجودی SOL در کیف پول
@app.get("/wallet-sol-balance/{network}/{address}")
def get_wallet_sol_balance(network: str, address: str):
    url = f"{BASE_URL}/account/{network}/{address}/balance"
    return requests.get(url, headers=HEADERS).json()

# 4. دریافت پرتفوی کیف پول
@app.get("/wallet-portfolio/{network}/{address}")
def get_wallet_portfolio(network: str, address: str):
    url = f"{BASE_URL}/account/{network}/{address}/portfolio"
    return requests.get(url, headers=HEADERS).json()

# 5. دریافت تاریخچه سواپ‌ها بر اساس توکن
@app.get("/token-swaps/{network}/{address}")
def get_token_swaps(network: str, address: str):
    url = f"{BASE_URL}/token/{network}/{address}/swaps"
    return requests.get(url, headers=HEADERS).json()

# 6. دریافت تاریخچه سواپ‌ها بر اساس کیف پول
@app.get("/wallet-swaps/{network}/{address}")
def get_wallet_swaps(network: str, address: str):
    url = f"{BASE_URL}/account/{network}/{address}/swaps"
    return requests.get(url, headers=HEADERS).json()

# 7. دریافت تاریخچه سواپ‌ها بر اساس جفت معاملاتی
@app.get("/pair-swaps/{network}/{pair_address}")
def get_pair_swaps(network: str, pair_address: str):
    url = f"{BASE_URL}/token/{network}/pairs/{pair_address}/swaps"
    return requests.get(url, headers=HEADERS).json()

# 8. دریافت اطلاعات نقدینگی جفت معاملاتی و قیمت توکن
@app.get("/token-price/{network}/{address}")
def get_token_price(network: str, address: str):
    url = f"{BASE_URL}/token/{network}/{address}/price"
    return requests.get(url, headers=HEADERS).json()

# 9. دریافت اطلاعات جفت معاملاتی
@app.get("/token-pairs/{network}/{address}")
def get_token_pairs(network: str, address: str):
    url = f"{BASE_URL}/token/{network}/{address}/pairs"
    return requests.get(url, headers=HEADERS).json()

# 10. دریافت اطلاعات OHLCV (کندل‌ها)
@app.get("/pair-ohlcv/{network}/{pair_address}")
def get_pair_ohlcv(network: str, pair_address: str, timeframe: str = "1h"):
    url = f"{BASE_URL}/token/{network}/pairs/{pair_address}/ohlcv?timeframe={timeframe}"
    return requests.get(url, headers=HEADERS).json()

# 11. دریافت اطلاعات Snipers
@app.get("/pair-snipers/{network}/{pair_address}")
def get_pair_snipers(network: str, pair_address: str, blocks_after_creation: int = 1000):
    url = f"{BASE_URL}/token/{network}/pairs/{pair_address}/snipers?blocksAfterCreation={blocks_after_creation}"
    return requests.get(url, headers=HEADERS).json()

# اجرای سرور با دریافت پورت از متغیر محیطی
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5110))  # مقدار پیش‌فرض 5110 برای اجرا در لوکال
    uvicorn.run(app, host="0.0.0.0", port=port)
