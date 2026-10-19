import fitz  # PyMuPDF


def read_pdf(filename):
    """
    استخراج النص الكامل من ملف PDF.
    """

    try:

        doc = fitz.open(filename)

        text = ""

        for page in doc:

            text += page.get_text()

        doc.close()

        if not text.strip():
            return "The PDF contains no readable text."

        return text

    except Exception as e:

        return f"PDF Error: {e}"