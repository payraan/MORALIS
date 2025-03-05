from fastapi import FastAPI, HTTPException, Query, Path, Depends
import requests
import os
import uvicorn
from typing import Optional
import time

app = FastAPI(
    title="Moralis API for Solana",
    description="API برای دریافت اطلاعات توکن، موجودی کیف پول، نقدینگی، تاریخچه سواپ و موارد دیگر از Moralis برای شبکه Solana.",
    version="1.0.5"
)

# تنظیم API Key از متغیر محیطی
MORALIS_API_KEY = os.getenv("MORALIS_API_KEY")
if not MORALIS_API_KEY:
    print("⚠️ WARNING: MORALIS_API_KEY is not set! API will not function correctly.")

BASE_URL = "https://solana-gateway.moralis.io"
HEADERS = {
    "Accept": "application/json",
    "X-API-Key": MORALIS_API_KEY,
    "User-Agent": "Moralis-API-Bot"
}

@app.get("/")
def home():
    return {"message": "✅ API Moralis روی سرور اجرا شده است!", "version": "1.0.5"}

# تابع کمکی برای ارسال درخواست به Moralis با لاگ بیشتر
def fetch_from_moralis(endpoint: str, params: Optional[dict] = None):
    url = f"{BASE_URL}{endpoint}"
    
    # لاگ برای دیباگ
    print(f"🔍 Sending request to: {url}")
    print(f"🔍 With params: {params}")

    try:
        response = requests.get(url, headers=HEADERS, params=params)
        
        # لاگ برای دیباگ
        print(f"✅ Response status: {response.status_code}")
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 400:
            print(f"❌ Bad Request: {response.text}")
            raise HTTPException(status_code=400, detail=f"❌ Bad Request: {response.text}")
        elif response.status_code == 401:
            print(f"❌ Unauthorized: {response.text}")
            raise HTTPException(status_code=401, detail="❌ Unauthorized: Invalid API Key")
        elif response.status_code == 404:
            print(f"❌ Not Found: {response.text}")
            raise HTTPException(status_code=404, detail="❌ Not Found: Invalid Token or Wallet Address")
        else:
            print(f"⚠ Unexpected Error: {response.text}")
            raise HTTPException(status_code=response.status_code, detail=f"⚠ Unexpected Error: {response.text[:200]}")
    except requests.RequestException as e:
        print(f"❌ Request error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"❌ Connection Error: {str(e)}")

# تمیز کردن آدرس‌های توکن (برای حذف پسوندهای اضافی مانند "pump")
def clean_token_address(address: str) -> str:
    # حذف پسوند "pump" که ممکن است به دلیل خطای تایپی اضافه شده باشد
    if address.lower().endswith("pump"):
        return address[:-4]
    return address

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
def get_token_swaps(
    network: str, 
    address: str, 
    limit: int = Query(50, ge=1, le=100),
    cursor: Optional[str] = None
):
    network = validate_network(network)
    
    # تمیز کردن آدرس توکن
    clean_address = clean_token_address(address)
    
    params = {"limit": limit}
    if cursor:
        params["cursor"] = cursor
        
    return fetch_from_moralis(f"/token/{network}/{clean_address}/swaps", params)

# 6️⃣ دریافت تاریخچه سواپ‌ها بر اساس کیف پول
@app.get("/wallet-swaps/{network}/{address}")
def get_wallet_swaps(
    network: str, 
    address: str, 
    limit: int = Query(50, ge=1, le=100),
    cursor: Optional[str] = None
):
    network = validate_network(network)
    
    params = {"limit": limit}
    if cursor:
        params["cursor"] = cursor
        
    return fetch_from_moralis(f"/account/{network}/{address}/swaps", params)

# 7️⃣ دریافت تاریخچه سواپ‌ها بر اساس جفت معاملاتی
@app.get("/pair-swaps/{network}/{pair_address}")
def get_pair_swaps(
    network: str, 
    pair_address: str, 
    limit: int = Query(50, ge=1, le=100),
    cursor: Optional[str] = None
):
    network = validate_network(network)
    
    # تمیز کردن آدرس جفت معاملاتی
    clean_address = clean_token_address(pair_address)
    
    params = {"limit": limit}
    if cursor:
        params["cursor"] = cursor
        
    return fetch_from_moralis(f"/token/{network}/pairs/{clean_address}/swaps", params)

# 8️⃣ دریافت اطلاعات نقدینگی و قیمت توکن
@app.get("/token-price/{network}/{address}")
def get_token_price(network: str, address: str):
    network = validate_network(network)
    
    # تمیز کردن آدرس توکن
    clean_address = clean_token_address(address)
    
    return fetch_from_moralis(f"/token/{network}/{clean_address}/price")

# 9️⃣ دریافت اطلاعات جفت معاملاتی
@app.get("/token-pairs/{network}/{address}")
def get_token_pairs(network: str, address: str):
    network = validate_network(network)
    
    # تمیز کردن آدرس توکن
    clean_address = clean_token_address(address)
    
    return fetch_from_moralis(f"/token/{network}/{clean_address}/pairs")

# 🔟 دریافت اطلاعات OHLCV (کندل‌ها)
@app.get("/pair-ohlcv/{network}/{pair_address}")
def get_pair_ohlcv(
    network: str, 
    pair_address: str, 
    timeframe: str = Query("1h", description="بازه زمانی (1m, 5m, 15m, 1h, 4h, 1d)"),
    days_ago: int = Query(7, ge=1, le=30, description="تعداد روزهای گذشته برای دریافت داده")
):
    if timeframe not in ["1m", "5m", "15m", "1h", "4h", "1d"]:
        raise HTTPException(status_code=400, detail="❌ Invalid timeframe. Use one of: 1m, 5m, 15m, 1h, 4h, 1d")
    
    network = validate_network(network)
    
    # تمیز کردن آدرس جفت معاملاتی
    clean_address = clean_token_address(pair_address)
    
    # محاسبه زمان شروع و پایان (به میلی‌ثانیه)
    to_date = int(time.time() * 1000)  # زمان فعلی به میلی‌ثانیه
    from_date = to_date - (days_ago * 24 * 60 * 60 * 1000)  # تعداد روز قبل
    
    params = {
        "timeframe": timeframe,
        "fromDate": from_date,
        "toDate": to_date
    }
    
    return fetch_from_moralis(f"/token/{network}/pairs/{clean_address}/ohlcv", params)

# 1️⃣1️⃣ دریافت اطلاعات Snipers
@app.get("/pair-snipers/{network}/{pair_address}")
def get_pair_snipers(
    network: str, 
    pair_address: str, 
    blocks_after_creation: int = Query(1000, ge=10, le=10000)
):
    network = validate_network(network)
    
    # تمیز کردن آدرس جفت معاملاتی
    clean_address = clean_token_address(pair_address)
    
    return fetch_from_moralis(f"/token/{network}/pairs/{clean_address}/snipers", {"blocksAfterCreation": blocks_after_creation})

# تست API key و سرویس Moralis
@app.get("/test-api-key")
def test_moralis_api():
    """
    تست API key و اتصال به سرویس Moralis
    """
    try:
        # تست ساده با درخواست اطلاعات توکن معروف (USDC)
        usdc_address = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
        return fetch_from_moralis(f"/token/mainnet/{usdc_address}/metadata")
    except Exception as e:
        return {"status": "error", "message": f"❌ خطای اتصال: {str(e)}"}

# اجرای سرور
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080)) 
    print(f"🚀 Starting Moralis API server on port {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port)
