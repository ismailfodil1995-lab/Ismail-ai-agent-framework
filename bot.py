import csv
import os
from datetime import datetime

def log_trade():
    print("--- 📊 نظام تسجيل أوامر التداول ---")
    
    direction = input("اتجاه الصفقة (BUY / SELL): ").strip().upper()
    instrument = input("الأداة المالية (مثل EURUSD): ").strip().upper()
    entry_price = input("سعر الدخول (Entry Price): ").strip()
    size = input("حجم الصفقة (Position Size): ").strip()
    sl = input("وقف الخسارة (Stop Loss): ").strip()
    tp = input("هدف الربح (Take Profit): ").strip()

    file_name = "orders_log.csv"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    trade_data = [timestamp, direction, instrument, entry_price, size, sl, tp]
    file_exists = os.path.exists(file_name)
    
    try:
        with open(file_name, mode='a', newline='') as file:
            writer = csv.writer(file)
            # إذا كان الملف جديداً، أضف رؤوس الأعمدة أولاً
            if not file_exists or os.path.getsize(file_name) == 0:
                writer.writerow(["Timestamp", "Direction", "Instrument", "Entry Price", "Size", "Stop Loss", "Take Profit"])
            
            writer.writerow(trade_data)
            
        print(f"\n[SUCCESS] تم تسجيل الصفقة بنجاح وحفظها في {file_name}!\n")
    except Exception as e:
        print(f"\n[ERROR] حدث خطأ أثناء الحفظ: {e}\n")

if __name__ == "__main__":
    log_trade()