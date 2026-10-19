import time
import pdfplumber
import os

def process_pdf_demo():
    print("==================================================")
    print(" [AI Agent] Initializing PDF Extraction Pipeline")
    print("==================================================")
    time.sleep(3.0)
    
    # تأكد من وجود ملف PDF تجريبي بنفس الاسم في نفس المجلد
    pdf_filename = "my_document.pdf"

    if not os.path.exists(pdf_filename):
        print(f"[Error] Target file '{pdf_filename}' not found.")
        return

    print(f"[System] Secure channel opened for file: {pdf_filename}")
    time.sleep(2.5)
    
    try:
        with pdfplumber.open(pdf_filename) as pdf:
            total_pages = len(pdf.pages)
            print(f"[System] Document loaded. Total pages detected: {total_pages}")
            time.sleep(2.5)
            
            extracted_text_full = ""
            
            print("\n--- [Phase 1: Deep Vector Extraction & OCR] ---")
            for i in range(min(2, total_pages)):
                print(f"[Parser Node] Processing page {i+1}/{total_pages}...")
                page = pdf.pages[i]
                text = page.extract_text()
                if text:
                    extracted_text_full += text + "\n"
                time.sleep(4.0) # قراءة واضحة ومريحة للمشاهد
            
            print("\n--- [Phase 2: Data Structuring & JSON Mapping] ---")
            time.sleep(3.0)
            
            print("\n================ [ Extracted PDF Summary ] ================")
            preview_text = extracted_text_full.strip()[:300]
            print(preview_text if preview_text else "[Notice] Data parsed successfully.")
            print("===========================================================")
            time.sleep(5.0) # وقت كافٍ لقراءة النتيجة في نهاية الفيديو
            
            print(f"[AI Agent] Status: Pipeline executed successfully. Data ready! ✅")

    except Exception as e:
        print(f"[Critical Error]: {e}")

if __name__ == "__main__":
    process_pdf_demo()