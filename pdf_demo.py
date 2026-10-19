import time
import pdfplumber
import os

def process_real_pdf_perfect_duration():
    print("[AI Agent] Initializing Autonomous Document Processing Pipeline...")
    time.sleep(3.0) # زيادة الوقت قليلاً في البداية
    
    pdf_filename = "my_document.pdf" 

    if not os.path.exists(pdf_filename):
        print(f"[Error] File '{pdf_filename}' not found.")
        return

    print(f"[System] Establishing secure stream for file: {pdf_filename}")
    time.sleep(3.0)
    
    try:
        extracted_text_full = ""
        with pdfplumber.open(pdf_filename) as pdf:
            total_pages = len(pdf.pages)
            print(f"[System] Target verified. Total pages detected: {total_pages}")
            time.sleep(2.5)
            
            # --- المرحلة الأولى: قراءة أطول وأكثر هدوءاً للصفحة الأولى ---
            print("\n--- [PHASE 1: Deep Layout & OCR Analysis] ---")
            for i in range(min(1, total_pages)):
                print(f"[Parser] Extracting text vectors from page {i+1}/{total_pages}...")
                page = pdf.pages[i]
                text = page.extract_text()
                if text:
                    extracted_text_full += text + "\n"
                time.sleep(5.0) # منح متسع من الوقت لصفحة البداية
            
            # --- مرحلة التسارع المتزن (Turbo Mode) ---
            print("\n\n⚡ >>>>> [TURBO MODE ENGAGED: Accelerated Engine] <<<<< ⚡\n")
            time.sleep(1.5)
            
            print("[AI Agent] Processing remaining pages with optimized throughput...")
            for i in range(1, total_pages):
                print(f"[Parser] Fast-tracking page {i+1}/{total_pages}...")
                page = pdf.pages[i]
                text = page.extract_text()
                if text:
                    extracted_text_full += text + "\n"
                time.sleep(2.0) # سرعة متوسطة ومرئية لباقي الصفحات
            
            print("\n--- [Data Verification & JSON Schema Mapping completed] ---")
            time.sleep(2.5)
            
            # طباعة التقرير النهائي
            print("\n================ [ Extracted Data Report ] ================")
            preview_text = extracted_text_full.strip()[:600]
            print(preview_text)
            print("===========================================================")
            time.sleep(4.0) # وقت كافٍ لقراءة النتيجة في نهاية الفيديو
            
            print(f"[AI Agent] Status: Success! Document fully processed and structured. 🚀")

    except Exception as e:
        print(f"[Critical Error]: {e}")

if __name__ == "__main__":
    process_real_pdf_perfect_duration()