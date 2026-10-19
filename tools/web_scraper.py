import requests
from bs4 import BeautifulSoup
from tools import register_tool

@register_tool(name="scrape_web_page", description="سحب النصوص الأساسية من أي رابط موقع.")
def scrape_web_page(url: str = "https://example.com") -> str:
    try:
        # إضافة هيدر لتجنب حظر المكتبة من قبل بعض المواقع
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
        }
        
        # إضافة http:// للرابط إذا نسيه المستخدم
        if not url.startswith("http://") and not url.startswith("https://"):
            url = "https://" + url

        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        # حذف أكواد الـ JavaScript والـ CSS للحصول على نص نظيف فقط
        for element in soup(["script", "style", "nav", "footer"]):
            element.extract()

        # استخراج النص وتنظيف المساحات الفارغة
        clean_text = ' '.join(soup.get_text().split())
        
        return clean_text[:2000] if clean_text else "لم يتم العثور على نص واضح في الصفحة."

    except Exception as e:
        return f"Error scraping web page: {str(e)}"