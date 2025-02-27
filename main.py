from fastapi import FastAPI, HTTPException
import requests
import os
import uvicorn

app = FastAPI()

# مقدار API Key از متغیر محیطی
MORALIS_API_KEY = os.getenv("MORALIS_API_KEY")
if not MORALIS_API_KEY:
    raise ValueError("🚨 MORALIS_API_KEY is not set!")

BASE_URL = "https://solana-gateway.moralis.io"
HEADERS = {
    "Accept": "application/json",
    "X-API-Key": MORALIS_API_KEY,
    "User-Agent": "Investia-Moralis-API-Bot"
}

@app.get("/")
def home():
    return {"message": "✅ API Moralis روی سرور اجرا شده است!"}

# تابع کمکی برای ارسال درخواست به Moralis
def fetch_from_moralis(endpoint: str):
    url = f"{BASE_URL}{endpoint}"
    response = requests.get(url, headers=HEADERS)

    if response.status_code == 200:
        return response.json()
    elif response.status_code == 400:
        raise HTTPException(status_code=400, detail="❌ Bad Request: Invalid Parameters")
    elif response.status_code == 401:
        raise HTTPException(status_code=401, detail="❌ Unauthorized: Invalid API Key")
    elif response.status_code == 404:
        raise HTTPException(status_code=404, detail="❌ Not Found: Invalid Token or Wallet Address")
    else:
        raise HTTPException(status_code=response.status_code, detail="⚠ Unexpected Error")

# تبدیل مقدار network به 'mainnet' برای جلوگیری از خطای Moralis
def validate_network(network: str):
    if network.lower() not in ["mainnet", "solana"]:
        raise HTTPException(status_code=400, detail="❌ Unsupported network. Use 'mainnet' instead.")
    return "mainnet"

# 1️⃣ دریافت اطلاعات توکن
@app.get("/token-info/{network}/{address}")
def get_token_info(network: str, address: str):
    network = validate_network(network)
    return fetch_from_moralis(f"/token/{network}/{address}/metadata")

# 2️⃣ دریافت لیست توکن‌های کیف پول
@app.get("/wallet-spl-tokens/{network}/{address}")
def get_wallet_tokens(network: str, address: str):
    network = validate_network(network)
    return fetch_from_moralis(f"/account/{network}/{address}/tokens")

# 3️⃣ دریافت موجودی SOL در کیف پول
@app.get("/wallet-sol-balance/{network}/{address}")
def get_wallet_sol_balance(network: str, address: str):
    network = validate_network(network)
    return fetch_from_moralis(f"/account/{network}/{address}/balance")

# 4️⃣ دریافت پرتفوی کیف پول
@app.get("/wallet-portfolio/{network}/{address}")
def get_wallet_portfolio(network: str, address: str):
    network = validate_network(network)
    return fetch_from_moralis(f"/account/{network}/{address}/portfolio")

# 5️⃣ دریافت تاریخچه سواپ‌ها بر اساس توکن
@app.get("/token-swaps/{network}/{address}")
def get_token_swaps(network: str, address: str):
    network = validate_network(network)
    return fetch_from_moralis(f"/token/{network}/{address}/swaps")

# 6️⃣ دریافت تاریخچه سواپ‌ها بر اساس کیف پول
@app.get("/wallet-swaps/{network}/{address}")
def get_wallet_swaps(network: str, address: str):
    network = validate_network(network)
    return fetch_from_moralis(f"/account/{network}/{address}/swaps")

# 7️⃣ دریافت تاریخچه سواپ‌ها بر اساس جفت معاملاتی
@app.get("/pair-swaps/{network}/{pair_address}")
def get_pair_swaps(network: str, pair_address: str):
    network = validate_network(network)
    return fetch_from_moralis(f"/token/{network}/pairs/{pair_address}/swaps")

# 8️⃣ دریافت اطلاعات نقدینگی و قیمت توکن
@app.get("/token-price/{network}/{address}")
def get_token_price(network: str, address: str):
    network = validate_network(network)
    return fetch_from_moralis(f"/token/{network}/{address}/price")

# 9️⃣ دریافت اطلاعات جفت معاملاتی
@app.get("/token-pairs/{network}/{address}")
def get_token_pairs(network: str, address: str):
    network = validate_network(network)
    return fetch_from_moralis(f"/token/{network}/{address}/pairs")

# 🔟 دریافت اطلاعات OHLCV (کندل‌ها)
@app.get("/pair-ohlcv/{network}/{pair_address}")
def get_pair_ohlcv(network: str, pair_address: str, timeframe: str = "1h"):
    network = validate_network(network)
    return fetch_from_moralis(f"/token/{network}/pairs/{pair_address}/ohlcv?timeframe={timeframe}")

# 1️⃣1️⃣ دریافت اطلاعات Snipers
@app.get("/pair-snipers/{network}/{pair_address}")
def get_pair_snipers(network: str, pair_address: str, blocks_after_creation: int = 1000):
    network = validate_network(network)
    return fetch_from_moralis(f"/token/{network}/pairs/{pair_address}/snipers?blocksAfterCreation={blocks_after_creation}")

# اجرای سرور با دریافت پورت از متغیر محیطی
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080)) 
    uvicorn.run(app, host="0.0.0.0", port=port)
