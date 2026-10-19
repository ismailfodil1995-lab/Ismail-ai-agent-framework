import os
import pypdf
from tools import register_tool

@register_tool(name="read_pdf_file", description="استخراج النصوص الخام من أي ملف PDF.")
def read_pdf_file(file_path: str = "", **kwargs) -> str:
    for key in ["file_path", "path", "filename", "pdf_path", "file"]:
        if key in kwargs and kwargs[key]:
            file_path = kwargs[key]
            break

    if not file_path:
        return "Error: No PDF file path provided."

    if not os.path.exists(file_path):
        return f"Error: File '{file_path}' not found."

    try:
        reader = pypdf.PdfReader(file_path)
        text = ""
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
        return text[:4000] if text.strip() else "Warning: PDF is empty or scanned."
    except Exception as e:
        return f"Error reading PDF file: {str(e)}"