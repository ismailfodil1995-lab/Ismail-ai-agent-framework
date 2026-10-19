import os
from pypdf import PdfReader


def read_pdf_content(file_path: str, max_pages: int = 10) -> str:
  """قراءة واستخراج النصوص من ملفات PDF."""
  if not os.path.exists(file_path):
    return f"Error: File '{file_path}' not found."

  try:
    reader = PdfReader(file_path)
    total_pages = len(reader.pages)
    text = f"--- PDF Document: {os.path.basename(file_path)} (Total Pages: {total_pages}) ---\n\n"

    pages_to_read = min(total_pages, max_pages)
    for i in range(pages_to_read):
      extracted = reader.pages[i].extract_text()
      if extracted:
        text += f"[Page {i+1}]\n{extracted}\n\n"

    if len(text.strip()) < 50:
      return "Warning: The PDF seems to contain images or unreadable text."

    # تحديد النص المرجّع حتى لا يغرق الذاكرة
    return text[:3000] + (
        "\n\n[...Truncated for brevity...]" if len(text) > 3000 else ""
    )

  except Exception as e:
    return f"Error reading PDF file: {str(e)}"