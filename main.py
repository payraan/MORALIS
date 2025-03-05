from fastapi import FastAPI, HTTPException, Query, Path, Depends
import requests
import os
import uvicorn
from typing import Optional

app = FastAPI(
    title="Moralis API for Solana",
    description="API برای دریافت اطلاعات توکن، موجودی کیف پول، نقدینگی، تاریخچه سواپ و موارد دیگر از Moralis برای شبکه Solana.",
    version="1.0.4"
)

# تنظیم API Key از متغیر محیطی با مقدار پیش‌فرض برای محیط توسعه (در محیط تولید باید حتماً تنظیم شود)
MORALIS_API_KEY = os.getenv("MORALIS_API_KEY")

# بررسی API Key در startup
@app.on_event("startup")
async def startup_event():
    if not MORALIS_API_KEY:
        print("⚠️ WARNING: MORALIS_API_KEY is not set! API will not function correctly.")

BASE_URL = "https://solana-gateway.moralis.io"

def get_headers():
    if not MORALIS_API_KEY:
        raise HTTPException(
            status_code=500, 
            detail="🔑 Moralis API Key is not configured. Please contact the administrator."
        )
    return {
        "Accept": "application/json",
        "X-API-Key": MORALIS_API_KEY,
        "User-Agent": "Moralis-API-Bot"
    }

@app.get("/")
def home():
    return {"message": "✅ API Moralis روی سرور اجرا شده است!", "version": "1.0.4"}

# تابع کمکی برای ارسال درخواست به Moralis با لاگ بیشتر
def fetch_from_moralis(endpoint: str, params: Optional[dict] = None):
    url = f"{BASE_URL}{endpoint}"
    headers = get_headers()
    
    # لاگ برای دیباگ
    print(f"🔍 Sending request to: {url}")
    print(f"🔍 With params: {params}")
    
    try:
        response = requests.get(url, headers=headers, params=params)
        
        # لاگ برای دیباگ
        print(f"✅ Response status: {response.status_code}")
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 400:
            print(f"❌ Bad Request: {response.text}")
            raise HTTPException(status_code=400, detail="❌ Bad Request: Invalid Parameters")
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

# تبدیل مقدار network به 'mainnet' برای جلوگیری از خطای Moralis
def validate_network(network: str):
    if network.lower() not in ["mainnet", "solana"]:
        raise HTTPException(status_code=400, detail="❌ Unsupported network. Use 'mainnet' instead.")
    return "mainnet"

# 1️⃣ دریافت اطلاعات توکن
@app.get("/token-info/{network}/{address}")
def get_token_info(
    network: str = Path(..., description="شبکه بلاکچین (فقط 'mainnet' یا 'solana' مجاز است)"),
    address: str = Path(..., description="آدرس قرارداد توکن")
):
    """
    دریافت اطلاعات کلی توکن مانند نام، نماد و سایر متادیتا
    """
    network = validate_network(network)
    return fetch_from_moralis(f"/token/{network}/{address}/metadata")

# 2️⃣ دریافت لیست توکن‌های کیف پول
@app.get("/wallet-spl-tokens/{network}/{address}")
def get_wallet_tokens(
    network: str = Path(..., description="شبکه بلاکچین (فقط 'mainnet' یا 'solana' مجاز است)"),
    address: str = Path(..., description="آدرس کیف پول")
):
    """
    دریافت لیست توکن‌های SPL موجود در کیف پول
    """
    network = validate_network(network)
    return fetch_from_moralis(f"/account/{network}/{address}/tokens")

# 3️⃣ دریافت موجودی SOL در کیف پول
@app.get("/wallet-sol-balance/{network}/{address}")
def get_wallet_sol_balance(
    network: str = Path(..., description="شبکه بلاکچین (فقط 'mainnet' یا 'solana' مجاز است)"),
    address: str = Path(..., description="آدرس کیف پول")
):
    """
    دریافت موجودی SOL در کیف پول
    """
    network = validate_network(network)
    return fetch_from_moralis(f"/account/{network}/{address}/balance")

# 4️⃣ دریافت پرتفوی کیف پول
@app.get("/wallet-portfolio/{network}/{address}")
def get_wallet_portfolio(
    network: str = Path(..., description="شبکه بلاکچین (فقط 'mainnet' یا 'solana' مجاز است)"),
    address: str = Path(..., description="آدرس کیف پول")
):
    """
    دریافت پرتفوی کامل کیف پول شامل همه توکن‌ها و موجودی‌ها
    """
    network = validate_network(network)
    return fetch_from_moralis(f"/account/{network}/{address}/portfolio")

# 5️⃣ دریافت تاریخچه سواپ‌ها بر اساس توکن
@app.get("/token-swaps/{network}/{address}")
def get_token_swaps(
    network: str = Path(..., description="شبکه بلاکچین (فقط 'mainnet' یا 'solana' مجاز است)"),
    address: str = Path(..., description="آدرس قرارداد توکن"),
    limit: int = Query(50, description="تعداد نتایج در هر صفحه"),
    cursor: Optional[str] = Query(None, description="نشانگر صفحه بعدی نتایج")
):
    """
    دریافت تاریخچه سواپ‌های انجام شده برای یک توکن مشخص
    """
    network = validate_network(network)
    params = {"limit": limit}
    if cursor:
        params["cursor"] = cursor
    return fetch_from_moralis(f"/token/{network}/{address}/swaps", params)

# 6️⃣ دریافت تاریخچه سواپ‌ها بر اساس کیف پول
@app.get("/wallet-swaps/{network}/{address}")
def get_wallet_swaps(
    network: str = Path(..., description="شبکه بلاکچین (فقط 'mainnet' یا 'solana' مجاز است)"),
    address: str = Path(..., description="آدرس کیف پول"),
    limit: int = Query(50, description="تعداد نتایج در هر صفحه"),
    cursor: Optional[str] = Query(None, description="نشانگر صفحه بعدی نتایج")
):
    """
    دریافت تاریخچه سواپ‌های انجام شده توسط یک کیف پول مشخص
    """
    network = validate_network(network)
    params = {"limit": limit}
    if cursor:
        params["cursor"] = cursor
    return fetch_from_moralis(f"/account/{network}/{address}/swaps", params)

# 7️⃣ دریافت تاریخچه سواپ‌ها بر اساس جفت معاملاتی
@app.get("/pair-swaps/{network}/{pair_address}")
def get_pair_swaps(
    network: str = Path(..., description="شبکه بلاکچین (فقط 'mainnet' یا 'solana' مجاز است)"),
    pair_address: str = Path(..., description="آدرس جفت معاملاتی"),
    limit: int = Query(50, description="تعداد نتایج در هر صفحه"),
    cursor: Optional[str] = Query(None, description="نشانگر صفحه بعدی نتایج")
):
    """
    دریافت تاریخچه سواپ‌های انجام شده برای یک جفت معاملاتی مشخص
    """
    network = validate_network(network)
    params = {"limit": limit}
    if cursor:
        params["cursor"] = cursor
    return fetch_from_moralis(f"/token/{network}/pairs/{pair_address}/swaps", params)

# 8️⃣ دریافت اطلاعات نقدینگی و قیمت توکن
@app.get("/token-price/{network}/{address}")
def get_token_price(
    network: str = Path(..., description="شبکه بلاکچین (فقط 'mainnet' یا 'solana' مجاز است)"),
    address: str = Path(..., description="آدرس قرارداد توکن")
):
    """
    دریافت قیمت و اطلاعات نقدینگی توکن
    """
    network = validate_network(network)
    return fetch_from_moralis(f"/token/{network}/{address}/price")

# 9️⃣ دریافت اطلاعات جفت معاملاتی
@app.get("/token-pairs/{network}/{address}")
def get_token_pairs(
    network: str = Path(..., description="شبکه بلاکچین (فقط 'mainnet' یا 'solana' مجاز است)"),
    address: str = Path(..., description="آدرس قرارداد توکن")
):
    """
    دریافت اطلاعات جفت‌های معاملاتی موجود برای یک توکن
    """
    network = validate_network(network)
    return fetch_from_moralis(f"/token/{network}/{address}/pairs")

# 🔟 دریافت اطلاعات OHLCV (کندل‌ها)
@app.get("/pair-ohlcv/{network}/{pair_address}")
def get_pair_ohlcv(
    network: str = Path(..., description="شبکه بلاکچین (فقط 'mainnet' یا 'solana' مجاز است)"),
    pair_address: str = Path(..., description="آدرس جفت معاملاتی"),
    timeframe: str = Query("1h", description="بازه زمانی کندل‌ها (1m, 5m, 15m, 1h, 4h, 1d)")
):
    """
    دریافت اطلاعات کندل‌های قیمتی (OHLCV) برای یک جفت معاملاتی
    """
    if timeframe not in ["1m", "5m", "15m", "1h", "4h", "1d"]:
        raise HTTPException(status_code=400, detail="❌ Invalid timeframe. Use one of: 1m, 5m, 15m, 1h, 4h, 1d")
    
    network = validate_network(network)
    return fetch_from_moralis(f"/token/{network}/pairs/{pair_address}/ohlcv", {"timeframe": timeframe})

# 1️⃣1️⃣ دریافت اطلاعات Snipers
@app.get("/pair-snipers/{network}/{pair_address}")
def get_pair_snipers(
    network: str = Path(..., description="شبکه بلاکچین (فقط 'mainnet' یا 'solana' مجاز است)"),
    pair_address: str = Path(..., description="آدرس جفت معاملاتی"),
    blocks_after_creation: int = Query(1000, description="تعداد بلوک‌ها بعد از ایجاد جفت")
):
    """
    دریافت اطلاعات Snipers (معامله‌گران سریع بعد از ایجاد جفت)
    """
    network = validate_network(network)
    return fetch_from_moralis(f"/token/{network}/pairs/{pair_address}/snipers", {"blocksAfterCreation": blocks_after_creation})

# تست API key و سرویس Moralis
@app.get("/test-api-key")
def test_moralis_api():
    """
    تست API key و اتصال به سرویس Moralis
    """
    try:
        headers = get_headers()
        url = f"{BASE_URL}/health"
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            return {"status": "success", "message": "✅ API key معتبر است و اتصال به Moralis برقرار است"}
        else:
            return {
                "status": "error", 
                "message": f"❌ خطا در اتصال: {response.status_code}", 
                "details": response.text
            }
    except Exception as e:
        return {"status": "error", "message": f"❌ خطای اتصال: {str(e)}"}

# اجرای سرور
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080)) 
    print(f"🚀 Starting Moralis API server on port {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port)
