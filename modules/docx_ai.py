from docx import Document
from llm.manager import generate


class DOCXAI:
    """
    مسؤول عن قراءة وتحليل ملفات Word.
    """

    # =====================================
    # Read DOCX
    # =====================================

    def read(self, filename):

        try:

            doc = Document(filename)

            text = ""

            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text += paragraph.text + "\n"

            return text.strip()

        except Exception as e:

            return f"Error reading DOCX: {e}"

    # =====================================
    # Summarize
    # =====================================

    def summarize(self, filename):

        print("=" * 60)
        print("STEP 1 : Opening DOCX")

        text = self.read(filename)

        print("STEP 2 : DOCX Loaded")

        if text.startswith("Error"):
            return text

        if not text:
            return "Document is empty."

        print(f"Characters : {len(text)}")

        # مؤقتاً مثل PDF
        if len(text) > 3000:
            text = text[:3000]

        print(f"Characters Sent : {len(text)}")

        prompt = f"""
You are an expert document analyst.

Read the following Word document.

Return:

1. Short summary.

2. Important points.

3. Important names.

4. Important dates.

5. Important numbers.

Document:

{text}
"""

        print("STEP 3 : Sending Prompt To Ollama")

        result = generate(prompt)

        print("STEP 4 : Ollama Finished")

        return result

    # =====================================
    # Ask
    # =====================================

    def ask(self, filename, question):

        print("=" * 60)
        print("STEP 1 : Opening DOCX")

        text = self.read(filename)

        print("STEP 2 : DOCX Loaded")

        if text.startswith("Error"):
            return text

        if not text:
            return "Document is empty."

        print(f"Characters : {len(text)}")

        if len(text) > 3000:
            text = text[:3000]

        print(f"Characters Sent : {len(text)}")

        prompt = f"""
Answer ONLY using the following Word document.

Document:

{text}

Question:

{question}

Answer:
"""

        print("STEP 3 : Sending Prompt To Ollama")

        result = generate(prompt)

        print("STEP 4 : Ollama Finished")

        return result


docx_ai = DOCXAI()