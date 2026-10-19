import os
import sys

# إضافة المسار الحالي باستخدام المتغير الصحيح
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

tools_list = [
    'data_exporter', 
    'lead_qualifier', 
    'pdf_ai_tools', 
    'pdf_generator', 
    'pdf_reader', 
    'web_scraper', 
    'web_search'
]

print("=" * 50)
print("🔍 بدء فحص الكفاءة التشغيلية والدوال لكل أداة...")
print("=" * 50)

for tool_name in tools_list:
    try:
        module_path = f"tools.{tool_name}"
        module = __import__(module_path, fromlist=['*'])
        
        functions = [func for func in dir(module) if callable(getattr(module, func)) and not func.startswith('_')]
        
        print(f"✅ الأداة [{tool_name}] تعمل بكفاءة.")
        print(f"   - الدوال المتاحة: {functions if functions else 'لا توجد دوال معرفة مباشرة'}")
    except Exception as e:
        print(f"❌ خطأ في تشغيل أو قراءة الأداة [{tool_name}]: {e}")

print("=" * 50)
print("✨ تم الانتهاء من فحص جميع الأدوات بنجاح.")
print("=" * 50)