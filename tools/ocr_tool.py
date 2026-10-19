"""
OCR Tool – tools/ocr_tool.py
أداة متقدمة لاستخراج النصوص والجداول من الصور وملفات الـ PDF الممسوحة ضوئياً (Scanned Documents).
تعتمد على pytesseract ومعالجة الصور عبر Pillow مع دعم استخراج الصفحات الممسوحة من ملفات PDF مباشرة.
"""

import io
import os
import shutil
from typing import Any, Dict, List, Optional
from PIL import Image

try:
    import pytesseract
except ImportError:
    pytesseract = None

try:
    import pypdf
except ImportError:
    pypdf = None

from tools import register_tool


def _find_tesseract_binary() -> Optional[str]:
    """البحث الذكي عن مسار محرك Tesseract OCR في النظام"""
    # 1. فحص متغيرات البيئة
    env_path = os.getenv("TESSERACT_PATH") or os.getenv("TESSERACT_CMD")
    if env_path and os.path.exists(env_path):
        return env_path

    # 2. فحص المسارات القياسية في Windows
    windows_paths = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        os.path.expanduser(r"~\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"),
        os.path.expanduser(r"~\AppData\Local\Tesseract-OCR\tesseract.exe")
    ]
    for p in windows_paths:
        if os.path.exists(p):
            return p

    # 3. فحص PATH عبر which/where
    which_path = shutil.which("tesseract")
    if which_path:
        return which_path

    return None


# تهيئة مسار Tesseract إن وُجد
_tesseract_bin = _find_tesseract_binary()
if _tesseract_bin and pytesseract:
    pytesseract.pytesseract.tesseract_cmd = _tesseract_bin


def _extract_images_from_pdf(pdf_path: str) -> List[Image.Image]:
    """استخراج الصور المضمنة في صفحات ملف الـ PDF الممسوح ضوئياً"""
    images: List[Image.Image] = []
    
    # 1. تجربة pdf2image إن كان متاحاً
    try:
        from pdf2image import convert_from_path
        return convert_from_path(pdf_path)
    except Exception:
        pass

    # 2. استخراج الصور عبر pypdf كبديل محلي خفيف الوزن
    if pypdf:
        try:
            reader = pypdf.PdfReader(pdf_path)
            for page in reader.pages:
                for img_obj in page.images:
                    img_data = img_obj.data
                    img = Image.open(io.BytesIO(img_data))
                    images.append(img)
        except Exception:
            pass

    return images


def _load_images(file_path: str) -> List[Image.Image]:
    """تحميل الصور سواء كان الملف صورة عادية أو PDF ممسوح"""
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".pdf":
        return _extract_images_from_pdf(file_path)
    elif ext in [".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif", ".webp"]:
        return [Image.open(file_path)]
    else:
        # تجربة فتح الملف كصورة مباشرة
        return [Image.open(file_path)]


TOOL_PARAMETERS = {
    "extract_text_ocr": {
        "type": "object",
        "properties": {
            "file_path": {"type": "string", "description": "مسار الصورة أو ملف PDF الممسوح ضوئياً"},
            "lang": {"type": "string", "description": "لغة التعرف (افتراضياً: eng أو ara أو eng+ara)"}
        },
        "required": ["file_path"]
    },
    "extract_tables_ocr": {
        "type": "object",
        "properties": {
            "file_path": {"type": "string", "description": "مسار ملف الصورة أو PDF المحتوي على جداول"},
            "lang": {"type": "string", "description": "لغة التعرف البصري (eng أو ara)"}
        },
        "required": ["file_path"]
    }
}


@register_tool(
    name="extract_text_ocr",
    description="استخراج النصوص البصرية من الصور والمستندات والـ PDFs الممسوحة ضوئياً عبر Tesseract OCR."
)
def extract_text_ocr(file_path: str = "", lang: str = "eng", **kwargs) -> str:
    """
    استخراج النصوص الكاملة من الصور وملفات PDF الممسوحة ضوئياً.
    """
    for k in ["path", "filename", "image_path", "pdf_path", "file"]:
        if k in kwargs and kwargs[k]:
            file_path = kwargs[k]
            break

    for k in ["language", "languages"]:
        if k in kwargs and kwargs[k]:
            lang = kwargs[k]
            break

    if not file_path:
        return "Error: No file_path provided for OCR text extraction."

    if not os.path.exists(file_path):
        return f"Error: File '{file_path}' not found."

    # التأكد من توفر pytesseract ومحرك Tesseract
    if not pytesseract:
        return "Error: pytesseract library is not installed."

    tesseract_exec = _find_tesseract_binary()
    if tesseract_exec:
        pytesseract.pytesseract.tesseract_cmd = tesseract_exec
    elif not shutil.which("tesseract") and not getattr(pytesseract.pytesseract, "tesseract_cmd", None):
        # في حال عدم وجود tesseract binary، نحاول القراءة كـ PDF عادي إن كان ملف PDF كـ Fallback
        if file_path.lower().endswith(".pdf") and pypdf:
            try:
                reader = pypdf.PdfReader(file_path)
                text = "\n".join(p.extract_text() or "" for p in reader.pages)
                if text.strip():
                    return f"[PDF Fallback Text Extract]:\n{text[:4000]}"
            except Exception:
                pass
        return (
            "Error: Tesseract OCR binary not found on the system. "
            "Please install Tesseract OCR (https://github.com/UB-Mannheim/tesseract/wiki) "
            "or set the TESSERACT_PATH environment variable."
        )

    try:
        images = _load_images(file_path)
        if not images:
            # محاولة قراءة نص الـ PDF العادي إن لم نجد صوراً مضمنة
            if file_path.lower().endswith(".pdf") and pypdf:
                reader = pypdf.PdfReader(file_path)
                direct_text = "\n".join(p.extract_text() or "" for p in reader.pages)
                if direct_text.strip():
                    return f"[Direct Text Extracted]:\n{direct_text[:4000]}"
            return f"Warning: No images or readable visual content found in '{file_path}'."

        results = []
        for idx, img in enumerate(images, start=1):
            # تحويل نمط الصورة للتأكد من التوافقية
            if img.mode not in ("RGB", "L"):
                img = img.convert("RGB")

            page_text = pytesseract.image_to_string(img, lang=lang)
            if page_text.strip():
                results.append(f"--- Page/Section {idx} ---\n{page_text.strip()}")

        if not results:
            return f"OCR completed on '{file_path}', but no text was recognized."

        return f"SUCCESS: OCR Text extracted from '{file_path}':\n\n" + "\n\n".join(results)

    except Exception as e:
        return f"Error during OCR extraction on '{file_path}': {str(e)}"


@register_tool(
    name="extract_tables_ocr",
    description="استخراج الجداول والبيانات المهيكلة من الصور والـ PDFs الممسوحة ضوئياً وتنسيقها كجدول Markdown."
)
def extract_tables_ocr(file_path: str = "", lang: str = "eng", **kwargs) -> str:
    """
    تحليل الإحداثيات المكانية للكلمات المكتوبة وإعادة بناء الجداول بتنسيق Markdown.
    """
    for k in ["path", "filename", "image_path", "pdf_path", "file"]:
        if k in kwargs and kwargs[k]:
            file_path = kwargs[k]
            break

    for k in ["language", "languages"]:
        if k in kwargs and kwargs[k]:
            lang = kwargs[k]
            break

    if not file_path:
        return "Error: No file_path provided for OCR table extraction."

    if not os.path.exists(file_path):
        return f"Error: File '{file_path}' not found."

    if not pytesseract:
        return "Error: pytesseract library is not installed."

    tesseract_exec = _find_tesseract_binary()
    if tesseract_exec:
        pytesseract.pytesseract.tesseract_cmd = tesseract_exec
    elif not shutil.which("tesseract"):
        return (
            "Error: Tesseract OCR binary not found on the system. "
            "Please install Tesseract OCR or configure TESSERACT_PATH."
        )

    try:
        images = _load_images(file_path)
        if not images:
            return f"Warning: No visual pages/images found in '{file_path}'."

        table_outputs = []

        for page_idx, img in enumerate(images, start=1):
            if img.mode not in ("RGB", "L"):
                img = img.convert("RGB")

            # استخراج بيانات المواضع والكتل والصناديق المحيطة (Bounding Boxes)
            data = pytesseract.image_to_data(img, lang=lang, output_type=pytesseract.Output.DICT)

            # تجميع الكلمات حسب الخطوط والصفوف (group by top coordinate)
            lines_dict: Dict[int, List[Dict[str, Any]]] = {}
            n_boxes = len(data["text"])

            for i in range(n_boxes):
                text = data["text"][i].strip()
                if not text:
                    continue

                top = data["top"][i]
                left = data["left"][i]
                width = data["width"][i]
                height = data["height"][i]

                # تقريب الإحداثي الرأسي لتجميع الكلمات في نفس الصف (Line Binning)
                matched_line_key = None
                for lk in lines_dict.keys():
                    if abs(lk - top) <= 12:  # تسامح رأسي بمقدار 12 بكسل
                        matched_line_key = lk
                        break

                if matched_line_key is None:
                    matched_line_key = top
                    lines_dict[matched_line_key] = []

                lines_dict[matched_line_key].append({
                    "left": left,
                    "text": text,
                    "width": width,
                    "height": height
                })

            if not lines_dict:
                continue

            # ترتيب الصفوف رأسياً
            sorted_lines = sorted(lines_dict.keys())
            reconstructed_rows: List[List[str]] = []

            for lk in sorted_lines:
                words_in_line = sorted(lines_dict[lk], key=lambda w: w["left"])
                
                # تجميع الكلمات المتقاربة جداً في خلية واحدة
                cells: List[str] = []
                current_cell_words = []
                last_right = -1

                for w in words_in_line:
                    if last_right != -1 and (w["left"] - last_right) > 30:
                        # فاصل أعمدة كبير
                        cells.append(" ".join(current_cell_words))
                        current_cell_words = [w["text"]]
                    else:
                        current_cell_words.append(w["text"])
                    last_right = w["left"] + w["width"]

                if current_cell_words:
                    cells.append(" ".join(current_cell_words))

                if cells:
                    reconstructed_rows.append(cells)

            if not reconstructed_rows:
                continue

            # تحديد أقصى عدد أعمدة لبناء جدول Markdown سليم
            max_cols = max(len(row) for row in reconstructed_rows)
            if max_cols < 2:
                # إذا لم يكن هناك عمودين على الأقل، يعرض كنص عادي
                text_lines = [" ".join(r) for r in reconstructed_rows]
                table_outputs.append(f"### Page {page_idx} (Single Column / Text):\n" + "\n".join(text_lines))
                continue

            # بناء جدول Markdown
            header_row = reconstructed_rows[0]
            header_row += [""] * (max_cols - len(header_row))
            header_str = "| " + " | ".join(header_row) + " |"
            sep_str = "| " + " | ".join(["---"] * max_cols) + " |"

            data_str_rows = []
            for row in reconstructed_rows[1:]:
                row += [""] * (max_cols - len(row))
                data_str_rows.append("| " + " | ".join(row) + " |")

            table_md = f"### Page {page_idx} Extracted Table:\n{header_str}\n{sep_str}\n" + "\n".join(data_str_rows)
            table_outputs.append(table_md)

        if not table_outputs:
            return f"OCR completed on '{file_path}', but no clear table structures were identified."

        return f"SUCCESS: Extracted Structured Tables from '{file_path}':\n\n" + "\n\n".join(table_outputs)

    except Exception as e:
        return f"Error extracting tables via OCR from '{file_path}': {str(e)}"


# قاموس التصدير للمعمارية الحديثة
EXPORTED_TOOLS = {
    "extract_text_ocr": {
        "name": "OCR Text Extractor",
        "description": "استخراج النصوص البصرية من الصور والمستندات والـ PDFs الممسوحة ضوئياً.",
        "parameters": TOOL_PARAMETERS["extract_text_ocr"],
        "fn": extract_text_ocr,
        "function": extract_text_ocr
    },
    "extract_tables_ocr": {
        "name": "OCR Table Extractor",
        "description": "استخراج الجداول والبيانات المهيكلة من الصور والـ PDFs وتحويلها لجداول Markdown.",
        "parameters": TOOL_PARAMETERS["extract_tables_ocr"],
        "fn": extract_tables_ocr,
        "function": extract_tables_ocr
    }
}
