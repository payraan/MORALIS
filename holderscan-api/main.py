from fastapi import FastAPI, HTTPException
import requests
import os
import uvicorn
from typing import Optional

app = FastAPI()

# تنظیم API Key از متغیر محیطی یا مستقیم
HOLDERSCAN_API_KEY = os.getenv("HOLDERSCAN_API_KEY", "3895e3019d79363e91a10983904c49bae2c4a7ff2db12caf124f5fe68143069c")

BASE_URL = "https://api.holderscan.com"
HEADERS = {
    "Accept": "application/json",
    "X-API-Key": HOLDERSCAN_API_KEY,
    "User-Agent": "Crypto-Analyst-GPT"
}

@app.get("/")
def home():
    return {"message": "✅ API HolderScan روی سرور اجرا شده است!"}

# تابع کمکی برای ارسال درخواست به HolderScan
def fetch_from_holderscan(endpoint: str, params: Optional[dict] = None):
    url = f"{BASE_URL}{endpoint}"
    response = requests.get(url, headers=HEADERS, params=params)

    if response.status_code == 200:
        return response.json()
    elif response.status_code == 400:
        raise HTTPException(status_code=400, detail="❌ Bad Request: Invalid Parameters")
    elif response.status_code == 401:
        raise HTTPException(status_code=401, detail="❌ Unauthorized: Invalid API Key")
    elif response.status_code == 404:
        raise HTTPException(status_code=404, detail="❌ Not Found: Invalid Token Address")
    else:
        raise HTTPException(status_code=response.status_code, detail=f"⚠ Unexpected Error: {response.text}")

# 1️⃣ دریافت اطلاعات توکن
@app.get("/token/{network}/{address}")
def get_token_info(network: str, address: str):
    """
    دریافت اطلاعات کلی توکن مانند نام، نماد، Market Cap و تعداد حساب‌های فعال
    """
    return fetch_from_holderscan(f"/v1/{network}/token", {"address": address})

# 2️⃣ دریافت اطلاعات کامل هولدرها
@app.get("/holders/breakdowns/{network}/{address}")
def get_holders_breakdown(network: str, address: str):
    """
    دریافت تحلیل کامل توزیع هولدرها، دسته‌بندی‌ها و تمرکز هولدرها
    """
    return fetch_from_holderscan(f"/v1/{network}/holders/breakdowns", {"address": address})

# 3️⃣ دریافت روند تغییرات هولدرها
@app.get("/holders/trends/{network}/{address}")
def get_holders_trends(network: str, address: str, period: str = "day"):
    """
    دریافت روند تغییرات هولدرها در بازه‌های زمانی مختلف (hour, day, week)
    """
    return fetch_from_holderscan(f"/v1/{network}/holders/trends", {"address": address, "period": period})

# 4️⃣ دریافت لیست هولدرهای برتر
@app.get("/holders/top/{network}/{address}")
def get_top_holders(network: str, address: str, limit: int = 10):
    """
    دریافت لیست هولدرهای برتر توکن
    """
    return fetch_from_holderscan(f"/v1/{network}/holders/top", {"address": address, "limit": limit})

# 5️⃣ دریافت اطلاعات CEX Holdings
@app.get("/holders/cex/{network}/{address}")
def get_cex_holdings(network: str, address: str):
    """
    دریافت اطلاعات نگهداری توکن در صرافی‌های متمرکز
    """
    return fetch_from_holderscan(f"/v1/{network}/holders/cex", {"address": address})

# 6️⃣ تحلیل کامل توکن (ترکیب همه API‌ها)
@app.get("/token/analysis/{network}/{address}")
async def get_token_analysis(network: str, address: str):
    """
    تحلیل کامل توکن شامل اطلاعات پایه، هولدرها، روندها و صرافی‌ها
    """
    try:
        # جمع‌آوری اطلاعات از همه APIها
        token_info = await get_token_info(network, address)
        holders_breakdown = await get_holders_breakdown(network, address)
        holders_trends = await get_holders_trends(network, address)
        top_holders = await get_top_holders(network, address)
        cex_holdings = await get_cex_holdings(network, address)
        
        # ترکیب همه داده‌ها در یک پاسخ
        return {
            "token_info": token_info,
            "holders": {
                "breakdown": holders_breakdown,
                "trends": holders_trends,
                "top_holders": top_holders,
                "cex_holdings": cex_holdings
            },
            "analysis": {
                "security_score": calculate_security_score(holders_breakdown, top_holders),
                "distribution_quality": analyze_distribution(holders_breakdown),
                "market_stability": analyze_stability(holders_trends, top_holders)
            }
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"⚠ Error in analysis: {str(e)}")

# توابع کمکی برای تحلیل
def calculate_security_score(holders_breakdown, top_holders):
    # منطق محاسبه امتیاز امنیتی بر اساس توزیع هولدرها
    try:
        hhi_score = holders_breakdown.get("hhi_score", 0)
        top_concentration = sum([holder.get("percentage", 0) for holder in top_holders.get("holders", [])[:5]])
        
        # امتیازدهی معکوس - هرچه تمرکز کمتر باشد، امنیت بالاتر است
        security_score = 100 - (hhi_score * 0.5) - (top_concentration * 0.5)
        security_score = max(0, min(100, security_score))  # محدود کردن به بازه 0-100
        
        return round(security_score, 2)
    except:
        return 50  # مقدار پیش‌فرض در صورت خطا

def analyze_distribution(holders_breakdown):
    # تحلیل کیفیت توزیع هولدرها
    try:
        categories = holders_breakdown.get("categories", {})
        whales = categories.get("whale", {}).get("count", 0)
        small_holders = categories.get("shrimp", {}).get("count", 0) + categories.get("fish", {}).get("count", 0)
        
        if small_holders > whales * 100:
            return "عالی - توزیع گسترده میان هولدرهای کوچک 🟢"
        elif small_holders > whales * 50:
            return "خوب - توزیع متعادل با تعداد کافی هولدرهای کوچک 🟡"
        elif small_holders > whales * 10:
            return "متوسط - نسبت هولدرهای کوچک به وال‌ها پایین است 🟠"
        else:
            return "ضعیف - تمرکز بالا در وال‌ها 🔴"
    except:
        return "نامشخص - داده‌ های کافی برای تحلیل وجود ندارد ⚪"

def analyze_stability(holders_trends, top_holders):
    # تحلیل ثبات بازار بر اساس روندها و تمرکز هولدرها
    try:
        top_10_percentage = sum([holder.get("percentage", 0) for holder in top_holders.get("holders", [])[:10]])
        recent_trend = holders_trends.get("trends", [])
        
        if recent_trend and len(recent_trend) > 0:
            last_trend = recent_trend[-1]
            change = last_trend.get("change", 0)
            
            if change > 5 and top_10_percentage < 50:
                return "رشد سالم با توزیع مناسب 📈"
            elif change > 5 and top_10_percentage >= 50:
                return "رشد همراه با ریسک تمرکز بالا ⚠️"
            elif change < -5 and top_10_percentage >= 50:
                return "ریزش همراه با خطر فروش توسط وال‌ها 📉"
            elif change < -5 and top_10_percentage < 50:
                return "ریزش با ریسک کمتر به دلیل توزیع مناسب 🟠"
            else:
                return "ثبات نسبی در کوتاه مدت ↔️"
        else:
            return "داده‌ای برای تحلیل روند وجود ندارد ⚪"
    except:
        return "نامشخص - داده‌های کافی برای تحلیل وجود ندارد ⚪"

# اجرای سرور با دریافت پورت از متغیر محیطی
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080)) 
    uvicorn.run(app, host="0.0.0.0", port=port)
