import json
from tools import register_tool

@register_tool(
    name="qualify_lead", 
    description="تأهيل وتقييم العملاء المحتملين بناءً على الميزانية والحاجة والجاهزية."
)
def qualify_lead(
    client_info: str = "عميل مهتم بإنشاء نظام ذكاء اصطناعي، الميزانية متوسطة، والبدء فوري",
    **kwargs  # التقاط أي متغير إضافي يرسله النموذج أياً كان اسمه (مثل client_name أو client_names)
) -> str:
    """
    أداة لتأهيل العملاء مع حماية شاملة ضد أي اسم وسيط يرسله الذكاء الاصطناعي
    """
    try:
        # البحث في الـ kwargs إذا تم إرسال الاسم بأي صيغة أخرى
        for key in ["client_name", "client_names", "name", "info", "query"]:
            if key in kwargs and isinstance(kwargs[key], str):
                client_info = kwargs[key]
                break

        info_lower = str(client_info).lower()
        score = 50
        notes = []

        if any(w in info_lower for w in ["عالية", "كبيرة", "ممتازة", "high", "good", "4000", "5000", "6000", "دولار"]):
            score += 25
            notes.append("ميزانية/إمكانيات ممتازة")
        if any(w in info_lower for w in ["فوري", "عاجل", "الآن", "urgent", "now", "اليوم"]):
            score += 25
            notes.append("جاهزية عالية للبدء")

        # التقييم النهائي
        if score >= 75:
            category = "🔥 عميل عالي الأهمية (High Quality Lead)"
            action = "تواصل معه فوراً وارسِل له عرض السعر (Proposal)."
        elif score >= 50:
            category = "⚠️ عميل متوسط (Medium Lead)"
            action = "يحتاج استفسارات أكثر عن الميزانية والمشروع."
        else:
            category = "❄️ عميل غير جاهز (Low Lead)"
            action = "أرسل له معلومات عامة ولا تضيع وقتاً كبيراً معه."

        report = f"""
🎯 نتيجة تأهيل العميل:
- البيانات المُحللة: {client_info}
- التقييم: {score}/100
- التصنيف: {category}
- الملاحظات: {', '.join(notes) if notes else 'بيانات قياسية'}
- الخطوة الموصى بها: {action}
        """
        return report.strip()

    except Exception as e:
        return f"Error qualifying lead: {str(e)}"