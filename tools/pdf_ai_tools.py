import os
from tools import register_tool
from modules.pdf_ai import pdf_ai


def _resolve_file_path(file_path: str = "", **kwargs) -> str:
    for key in ["file_path", "path", "filename", "pdf_path", "file"]:
        if key in kwargs and kwargs[key]:
            file_path = kwargs[key]
            break
    return file_path


@register_tool(
    name="summarize_pdf_file",
    description="تلخيص ملف PDF ذكياً مع استخراج أهم النقاط والأسماء والتواريخ."
)
def summarize_pdf_file(file_path: str = "", **kwargs) -> str:
    file_path = _resolve_file_path(file_path, **kwargs)
    if not file_path:
        return "Error: No PDF file path provided."
    if not os.path.exists(file_path):
        return f"Error: File '{file_path}' not found."
    return pdf_ai.summarize(file_path)


@register_tool(
    name="ask_pdf_question",
    description="الإجابة على أسئلة المستخدم حول محتوى ملف PDF بدقة."
)
def ask_pdf_question(file_path: str = "", question: str = "", **kwargs) -> str:
    file_path = _resolve_file_path(file_path, **kwargs)

    for key in ["question", "q", "query", "prompt"]:
        if key in kwargs and kwargs[key]:
            question = kwargs[key]
            break

    if not file_path:
        return "Error: No PDF file path provided."
    if not os.path.exists(file_path):
        return f"Error: File '{file_path}' not found."
    if not question:
        return "Error: No question provided."

    return pdf_ai.ask(file_path, question)
