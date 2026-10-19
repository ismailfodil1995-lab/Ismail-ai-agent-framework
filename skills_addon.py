import time
import schedule
import pandas as pd

# --- المهارة التاسعة: توليد تقارير Excel منسقة ---
def generate_excel_report(data_list):
    """
    تقرأ البيانات المستخرجة وتحولها إلى ملف Excel منظم تلقائياً
    """
    print("📊 [المهارة 9] جاري توليد تقرير Excel منسق للبيانات...")
    df = pd.DataFrame(data_list)
    output_path = "C:\\Users\\HP\\Documents\\AI_Agent\\automation_report.xlsx"
    df.to_excel(output_path, index=False)
    print(f"✅ تم حفظ التقرير بنجاح في: {output_path}")

# --- المهارة الثامنة: جدولة وتشغيل الـ Framework تلقائياً ---
def start_automated_scheduler(main_framework_function, run_time="08:00"):
    """
    تستقبل دالة تشغيل مشروعك الرئيسية لتشغيلها تلقائياً في وقت محدد
    دون العبث بأكوادك القديمة أو تعديلها
    """
    # جدولة المهارات للعمل كل يوم في ساعة محددة
    schedule.every().day.at(run_time).do(main_framework_function)
    
    print(f"⏳ [المهارة 8] مهارة الجدولة نشطة. تم ضبط الـ Framework ليعمل تلقائياً الساعة {run_time} كل يوم.")
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 تم إيقاف المراقبة التلقائية بأمان.")