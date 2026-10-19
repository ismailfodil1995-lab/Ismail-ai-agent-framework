import os

from modules.pdf_ai import pdf_ai
from modules.docx_ai import docx_ai
from modules.excel_ai import excel_ai


class DocumentAI:

    # =====================================

    def analyze(self, filename):

        ext = os.path.splitext(filename)[1].lower()

        if ext == ".pdf":
            return pdf_ai.summarize(filename)

        elif ext == ".docx":
            return docx_ai.summarize(filename)

        elif ext == ".xlsx":
            return excel_ai.summarize(filename)

        elif ext == ".xls":
            return excel_ai.summarize(filename)

        else:
            return f"Unsupported file type: {ext}"

    # =====================================

    def ask(self, filename, question):

        ext = os.path.splitext(filename)[1].lower()

        if ext == ".pdf":
            return pdf_ai.ask(filename, question)

        elif ext == ".docx":
            return docx_ai.ask(filename, question)

        elif ext == ".xlsx":
            return excel_ai.ask(filename, question)

        elif ext == ".xls":
            return excel_ai.ask(filename, question)

        else:
            return f"Unsupported file type: {ext}"


document_ai = DocumentAI()