import pandas as pd
from tools import register_tool

@register_tool(name="export_to_csv", description="تصدير البيانات الهيكلية أو القوائم إلى ملف CSV.")
def export_to_csv(data: list = None, filename_prefix: str = "export") -> str:
    try:
        # إذا لم يرسل النموذج أي بيانات، نضع بيانات افتراضية تجنباً للخطأ
        if data is None or not data:
            data = [{"ملاحظة": "تم إنشاء الملف بنجاح بدون بيانات محددة"}]
        
        # إذا كانت البيانات نصاً وليست قائمة، نحولها لقائمة
        elif isinstance(data, str):
            data = [{"البيانات": data}]

        df = pd.DataFrame(data)
        filename = f"{filename_prefix}.csv"
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        
        return f"SUCCESS: Data exported successfully to '{filename}'"
    except Exception as e:
        return f"Error exporting to CSV: {str(e)}"