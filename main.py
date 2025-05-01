from fastapi import FastAPI, HTTPException, Query, Path, Depends
import requests
import os
import uvicorn
from typing import Optional, List, Dict
import time

app = FastAPI(
    title="Moralis API for Solana",
    description="API برای دریافت اطلاعات توکن، موجودی کیف پول، نقدینگی، تاریخچه سواپ و موارد دیگر از Moralis برای شبکه Solana.",
    version="2.0.0"
)

# تنظیم API Key مستقیماً در کد
MORALIS_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJub25jZSI6ImM0NjMwNzI5LTRkM2UtNGQyNS1iZWMxLWE1OGUwMmMzODIyOSIsIm9yZ0lkIjoiNDMzOTQ4IiwidXNlcklkIjoiNDQ2MzkyIiwidHlwZUlkIjoiMWVhMDE1ZWQtMmI0Yy00ZTcxLWIzZjQtM2RlYTY4N2I3OGU1IiwidHlwZSI6IlBST0pFQ1QiLCJpYXQiOjE3NDA2ODUwMDYsImV4cCI6NDg5NjQ0NTAwNn0.0x3bp10ju5iV2cO4jhYEtV1JadQwfnZtX24ZBHn-IPw"

if not MORALIS_API_KEY:
    print("⚠️ WARNING: MORALIS_API_KEY is not set! API will not function correctly.")

BASE_URL = "https://solana-gateway.moralis.io"
DEFI_BASE_URL = "https://deep-index.moralis.io/api/v2.2"
HEADERS = {
    "Accept": "application/json",
    "X-API-Key": MORALIS_API_KEY,
    "User-Agent": "Moralis-API-Bot"
}

@app.get("/")
def home():
    return {"message": "✅ API Moralis روی سرور اجرا شده است!", "version": "2.0.0"}

# تابع کمکی برای ارسال درخواست به Moralis با لاگ بیشتر
def fetch_from_moralis(endpoint: str, params: Optional[dict] = None, method: str = "GET", data: Optional[dict] = None, base_url: str = BASE_URL):
    url = f"{base_url}{endpoint}"
    
    # لاگ برای دیباگ
    print(f"🔍 Sending request to: {url}")
    print(f"🔍 With params: {params}")
    if data:
        print(f"🔍 With data: {data}")

    try:
        if method == "GET":
            response = requests.get(url, headers=HEADERS, params=params)
        elif method == "POST":
            headers_with_content = HEADERS.copy()
            headers_with_content["Content-Type"] = "application/json"
            response = requests.post(url, headers=headers_with_content, json=data)
        
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

# تمیز کردن آدرس‌های توکن (آدرس بدون تغییر برمی‌گردد)
def clean_token_address(address: str) -> str:
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
def get_wallet_portfolio(
    network: str, 
    address: str,
    nft_metadata: bool = Query(False, description="Include NFT metadata")
):
    network = validate_network(network)
    params = {"nft_metadata": nft_metadata}
    return fetch_from_moralis(f"/account/{network}/{address}/portfolio", params)

# 5️⃣ دریافت تاریخچه سواپ‌ها بر اساس توکن
@app.get("/token-swaps/{network}/{address}")
def get_token_swaps(
    network: str, 
    address: str, 
    limit: int = Query(50, ge=1, le=100),
    cursor: Optional[str] = None,
    order: str = Query("DESC", description="Order by time: ASC or DESC"),
    hours_ago: Optional[int] = Query(None, ge=1, le=720, description="فیلتر زمانی - تعداد ساعت گذشته"),
    min_volume_usd: Optional[float] = Query(None, ge=0, description="حداقل حجم معاملات به دلار"),
    max_volume_usd: Optional[float] = Query(None, ge=0, description="حداکثر حجم معاملات به دلار"),
    swap_type: Optional[str] = Query(None, description="نوع سواپ: buy, sell یا خالی برای همه")
):
    network = validate_network(network)
    
    # تمیز کردن آدرس توکن
    clean_address = clean_token_address(address)
    
    params = {"limit": limit, "order": order}
    if cursor:
        params["cursor"] = cursor
    
    # محاسبه تاریخ شروع بر اساس ساعت‌های گذشته
    if hours_ago:
        from_date = int((time.time() - (hours_ago * 3600)) * 1000)
        params["fromDate"] = from_date
    
    try:
        result = fetch_from_moralis(f"/token/{network}/{clean_address}/swaps", params)
        
        # فیلتر کردن نتایج
        if isinstance(result, dict) and "result" in result:
            filtered_swaps = []
            for swap in result["result"]:
                # فیلتر حجم
                if min_volume_usd and "volumeUsd" in swap and float(swap["volumeUsd"]) < min_volume_usd:
                    continue
                if max_volume_usd and "volumeUsd" in swap and float(swap["volumeUsd"]) > max_volume_usd:
                    continue
                
                # فیلتر نوع سواپ
                if swap_type and "type" in swap and swap["type"].lower() != swap_type.lower():
                    continue
                
                filtered_swaps.append(swap)
            
            result["result"] = filtered_swaps
            result["total"] = len(filtered_swaps)
        
        return result
    except Exception as e:
        print(f"Error in token swaps: {str(e)}")
        raise

# 6️⃣ دریافت تاریخچه سواپ‌ها بر اساس کیف پول
@app.get("/wallet-swaps/{network}/{address}")
def get_wallet_swaps(
    network: str, 
    address: str, 
    limit: int = Query(50, ge=1, le=100),
    cursor: Optional[str] = None,
    order: str = Query("DESC", description="Order by time: ASC or DESC"),
    hours_ago: Optional[int] = Query(None, ge=1, le=720, description="فیلتر زمانی - تعداد ساعت گذشته"),
    min_volume_usd: Optional[float] = Query(None, ge=0, description="حداقل حجم معاملات به دلار"),
    max_volume_usd: Optional[float] = Query(None, ge=0, description="حداکثر حجم معاملات به دلار"),
    token_address: Optional[str] = Query(None, description="فیلتر بر اساس آدرس توکن خاص")
):
    network = validate_network(network)
    
    params = {"limit": limit, "order": order}
    if cursor:
        params["cursor"] = cursor
    
    # محاسبه تاریخ شروع بر اساس ساعت‌های گذشته
    if hours_ago:
        from_date = int((time.time() - (hours_ago * 3600)) * 1000)
        params["fromDate"] = from_date
    
    try:
        result = fetch_from_moralis(f"/account/{network}/{address}/swaps", params)
        
        # فیلتر کردن نتایج
        if isinstance(result, dict) and "result" in result:
            filtered_swaps = []
            for swap in result["result"]:
                # فیلتر حجم
                if min_volume_usd and "volumeUsd" in swap and float(swap["volumeUsd"]) < min_volume_usd:
                    continue
                if max_volume_usd and "volumeUsd" in swap and float(swap["volumeUsd"]) > max_volume_usd:
                    continue
                
                # فیلتر بر اساس توکن
                if token_address:
                    if "tokenAddress" in swap and swap["tokenAddress"].lower() != token_address.lower():
                        continue
                
                filtered_swaps.append(swap)
            
            result["result"] = filtered_swaps
            result["total"] = len(filtered_swaps)
        
        return result
    except Exception as e:
        print(f"Error in wallet swaps: {str(e)}")
        raise

# 7️⃣ دریافت تاریخچه سواپ‌ها بر اساس جفت معاملاتی
@app.get("/pair-swaps/{network}/{pair_address}")
def get_pair_swaps(
    network: str, 
    pair_address: str, 
    limit: int = Query(50, ge=1, le=100),
    cursor: Optional[str] = None,
    order: str = Query("DESC", description="Order by time: ASC or DESC")
):
    network = validate_network(network)
    
    # تمیز کردن آدرس جفت معاملاتی
    clean_address = clean_token_address(pair_address)
    
    params = {"limit": limit, "order": order}
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
    days_ago: int = Query(7, ge=1, le=30, description="تعداد روزهای گذشته برای دریافت داده", deprecated=True),
    from_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    to_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    currency: str = Query("usd", description="Currency for price data"),
    limit: int = Query(100, ge=1, le=1000, description="Number of data points to return")
):
    if timeframe not in ["1m", "5m", "15m", "1h", "4h", "1d"]:
        raise HTTPException(status_code=400, detail="❌ Invalid timeframe. Use one of: 1m, 5m, 15m, 1h, 4h, 1d")
    
    network = validate_network(network)
    
    # تمیز کردن آدرس جفت معاملاتی
    clean_address = clean_token_address(pair_address)
    
    params = {
        "timeframe": timeframe,
        "currency": currency,
        "limit": limit
    }
    
    if from_date:
        params["fromDate"] = from_date
    elif days_ago:  # برای سازگاری با نسخه قبلی
        to_date_timestamp = int(time.time() * 1000)
        from_date_timestamp = to_date_timestamp - (days_ago * 24 * 60 * 60 * 1000)
        params["fromDate"] = from_date_timestamp
        params["toDate"] = to_date_timestamp
    
    if to_date:
        params["toDate"] = to_date
    
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

# 1️⃣2️⃣ دریافت توکن‌های جدید PumpFun
@app.get("/pumpfun-new-tokens/{network}")
def get_pumpfun_new_tokens(
    network: str,
    limit: int = Query(20, ge=1, le=100, description="Number of tokens to return"),
    min_liquidity: Optional[float] = Query(None, ge=0, description="حداقل نقدینگی به دلار"),
    max_liquidity: Optional[float] = Query(None, ge=0, description="حداکثر نقدینگی به دلار"),
    hours_old: Optional[int] = Query(None, ge=1, le=168, description="حداکثر قدمت توکن به ساعت"),
    sort_by: str = Query("created", description="مرتب‌سازی بر اساس: created, liquidity, volume")
):
    network = validate_network(network)
    try:
        result = fetch_from_moralis(f"/token/{network}/exchange/pumpfun/new", {"limit": 100})
        
        # فیلتر کردن و مرتب‌سازی
        if isinstance(result, dict) and "result" in result:
            filtered_tokens = []
            current_time = int(time.time() * 1000)
            
            for token in result["result"]:
                # فیلتر نقدینگی
                if min_liquidity and "liquidity" in token and float(token["liquidity"]) < min_liquidity:
                    continue
                if max_liquidity and "liquidity" in token and float(token["liquidity"]) > max_liquidity:
                    continue
                
                # فیلتر قدمت
                if hours_old and "createdAt" in token:
                    token_age_hours = (current_time - int(token["createdAt"])) / (1000 * 3600)
                    if token_age_hours > hours_old:
                        continue
                
                filtered_tokens.append(token)
            
            # مرتب‌سازی
            if sort_by == "liquidity" and filtered_tokens:
                filtered_tokens.sort(key=lambda x: float(x.get("liquidity", 0)), reverse=True)
            elif sort_by == "volume" and filtered_tokens:
                filtered_tokens.sort(key=lambda x: float(x.get("volume24h", 0)), reverse=True)
            
            # محدود کردن تعداد
            result["result"] = filtered_tokens[:limit]
            result["total"] = len(result["result"])
        
        return result
    except Exception as e:
        # در صورت خطای سرور، لیست خالی برمی‌گردانیم
        print(f"Error in PumpFun new tokens: {str(e)}")
        return {"result": [], "total": 0, "error": "Service temporarily unavailable"}

# 1️⃣3️⃣ دریافت توکن‌های در حال باندینگ PumpFun
@app.get("/pumpfun-bonding-tokens/{network}")
def get_pumpfun_bonding_tokens(
    network: str,
    limit: int = Query(20, ge=1, le=100, description="Number of tokens to return"),
    min_progress: Optional[float] = Query(None, ge=0, le=100, description="حداقل درصد پیشرفت باندینگ"),
    max_progress: Optional[float] = Query(None, ge=0, le=100, description="حداکثر درصد پیشرفت باندینگ"),
    min_volume: Optional[float] = Query(None, ge=0, description="حداقل حجم معاملات 24 ساعته"),
    sort_by: str = Query("progress", description="مرتب‌سازی بر اساس: progress, volume, holders")
):
    network = validate_network(network)
    try:
        result = fetch_from_moralis(f"/token/{network}/exchange/pumpfun/bonding", {"limit": 100})
        
        # فیلتر کردن و مرتب‌سازی
        if isinstance(result, dict) and "result" in result:
            filtered_tokens = []
            
            for token in result["result"]:
                # فیلتر پیشرفت باندینگ
                if min_progress and "bondingProgress" in token and float(token["bondingProgress"]) < min_progress:
                    continue
                if max_progress and "bondingProgress" in token and float(token["bondingProgress"]) > max_progress:
                    continue
                
                # فیلتر حجم معاملات
                if min_volume and "volume24h" in token and float(token["volume24h"]) < min_volume:
                    continue
                
                filtered_tokens.append(token)
            
            # مرتب‌سازی
            if sort_by == "volume" and filtered_tokens:
                filtered_tokens.sort(key=lambda x: float(x.get("volume24h", 0)), reverse=True)
            elif sort_by == "holders" and filtered_tokens:
                filtered_tokens.sort(key=lambda x: int(x.get("holders", 0)), reverse=True)
            elif sort_by == "progress" and filtered_tokens:
                filtered_tokens.sort(key=lambda x: float(x.get("bondingProgress", 0)), reverse=True)
            
            # محدود کردن تعداد
            result["result"] = filtered_tokens[:limit]
            result["total"] = len(result["result"])
        
        return result
    except Exception as e:
        print(f"Error in PumpFun bonding tokens: {str(e)}")
        return {"result": [], "total": 0, "error": "Service temporarily unavailable"}

# 1️⃣4️⃣ دریافت توکن‌های گرجوئیت شده PumpFun
@app.get("/pumpfun-graduated-tokens/{network}")
def get_pumpfun_graduated_tokens(
    network: str,
    limit: int = Query(20, ge=1, le=100, description="Number of tokens to return"),
    hours_ago: Optional[int] = Query(None, ge=1, le=720, description="محدوده زمانی - تعداد ساعت گذشته"),
    min_market_cap: Optional[float] = Query(None, ge=0, description="حداقل مارکت کپ"),
    min_liquidity: Optional[float] = Query(None, ge=0, description="حداقل نقدینگی"),
    sort_by: str = Query("recent", description="مرتب‌سازی: recent, marketcap, liquidity, volume")
):
    network = validate_network(network)
    try:
        result = fetch_from_moralis(f"/token/{network}/exchange/pumpfun/graduated", {"limit": 100})
        
        # فیلتر کردن و مرتب‌سازی
        if isinstance(result, dict) and "result" in result:
            filtered_tokens = []
            current_time = int(time.time() * 1000)
            
            for token in result["result"]:
                # فیلتر زمانی
                if hours_ago and "graduatedAt" in token:
                    token_age_hours = (current_time - int(token["graduatedAt"])) / (1000 * 3600)
                    if token_age_hours > hours_ago:
                        continue
                
                # فیلتر مارکت کپ
                if min_market_cap and "marketCap" in token and float(token["marketCap"]) < min_market_cap:
                    continue
                
                # فیلتر نقدینگی
                if min_liquidity and "liquidity" in token and float(token["liquidity"]) < min_liquidity:
                    continue
                
                filtered_tokens.append(token)
            
            # مرتب‌سازی
            if sort_by == "marketcap" and filtered_tokens:
                filtered_tokens.sort(key=lambda x: float(x.get("marketCap", 0)), reverse=True)
            elif sort_by == "liquidity" and filtered_tokens:
                filtered_tokens.sort(key=lambda x: float(x.get("liquidity", 0)), reverse=True)
            elif sort_by == "volume" and filtered_tokens:
                filtered_tokens.sort(key=lambda x: float(x.get("volume24h", 0)), reverse=True)
            elif sort_by == "recent" and filtered_tokens:
                filtered_tokens.sort(key=lambda x: int(x.get("graduatedAt", 0)), reverse=True)
            
            # محدود کردن تعداد
            result["result"] = filtered_tokens[:limit]
            result["total"] = len(result["result"])
        
        return result
    except Exception as e:
        print(f"Error in PumpFun graduated tokens: {str(e)}")
        return {"result": [], "total": 0, "error": "Service temporarily unavailable"}

# 1️⃣5️⃣ دریافت وضعیت باندینگ توکن
@app.get("/token-bonding-status/{network}/{address}")
def get_token_bonding_status(network: str, address: str):
    network = validate_network(network)
    
    # اضافه کردن پسوند "pump" اگر وجود نداشته باشد
    if not address.lower().endswith("pump"):
        address += "pump"
    
    return fetch_from_moralis(f"/token/{network}/{address}/bonding-status")

# 1️⃣6️⃣ دریافت هولدرهای توکن
@app.get("/token-holders/{network}/{address}")
def get_token_holders(
    network: str,
    address: str,
    limit: int = Query(100, ge=1, le=100),
    cursor: Optional[str] = None
):
    network = validate_network(network)
    params = {"limit": limit}
    if cursor:
        params["cursor"] = cursor
    return fetch_from_moralis(f"/token/{network}/holders/{address}", params)

# 1️⃣7️⃣ دریافت تاریخچه هولدرهای توکن
@app.get("/token-holders-historical/{network}/{address}")
def get_token_holders_historical(
    network: str,
    address: str,
    from_date: str = Query(..., description="Start date (ISO format: YYYY-MM-DDTHH:mm:ss)"),
    to_date: str = Query(..., description="End date (ISO format: YYYY-MM-DDTHH:mm:ss)"),
    time_frame: str = Query("1d", description="Time frame (1m, 5m, 15m, 30m, 1h, 4h, 1d, 1w)"),
    limit: int = Query(100, ge=1, le=100)
):
    network = validate_network(network)
    params = {
        "fromDate": from_date,
        "toDate": to_date,
        "timeFrame": time_frame,
        "limit": limit
    }
    return fetch_from_moralis(f"/token/{network}/holders/{address}/historical", params)

# 1️⃣8️⃣ دریافت آمار جفت معاملاتی
@app.get("/pair-stats/{network}/{pair_address}")
def get_pair_stats(network: str, pair_address: str):
    network = validate_network(network)
    return fetch_from_moralis(f"/token/{network}/pairs/{pair_address}/stats")

# 1️⃣9️⃣ دریافت آمار تمام جفت‌های معاملاتی توکن
@app.get("/token-pairs-stats/{network}/{address}")
def get_token_pairs_stats(network: str, address: str):
    network = validate_network(network)
    return fetch_from_moralis(f"/token/{network}/{address}/pairs/stats")

# 2️⃣0️⃣ دریافت آنالیتیکس توکن
@app.get("/token-analytics/{address}")
def get_token_analytics(address: str):
    return fetch_from_moralis(f"/tokens/{address}/analytics", {"chain": "solana"}, base_url=DEFI_BASE_URL)

# 2️⃣1️⃣ دریافت قیمت چندین توکن
@app.post("/tokens-prices/{network}")
def get_tokens_prices(
    network: str,
    addresses: List[str]
):
    network = validate_network(network)
    data = {"addresses": addresses}
    return fetch_from_moralis(f"/token/{network}/prices", method="POST", data=data)

# اجرای سرور
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080)) 
    print(f"🚀 Starting Moralis API server on port {port}...")
    uvicorn.run(app, host="0.0.0.0", port=port)
