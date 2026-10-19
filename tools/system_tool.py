"""
System Tool – tools/system_tool.py
أداة مستقلة لعمليات النظام: قراءة/كتابة الملفات واستعراض المجلدات وتشغيل الأكواد.
مفصولة عن brain.py لضمان النظافة المعمارية وسهولة الصيانة.
"""

import os

TOOL_PARAMETERS = {
    "list_system_files": {
        "type": "object",
        "properties": {
            "folder": {"type": "string", "description": "مسار المجلد المراد استعراض ملفاته"}
        }
    },
    "read_system_file": {
        "type": "object",
        "properties": {
            "filename": {"type": "string", "description": "مسار الملف المراد قراءة محتواه"}
        },
        "required": ["filename"]
    },
    "write_system_file": {
        "type": "object",
        "properties": {
            "filename": {"type": "string", "description": "مسار الملف المراد الكتابة فيه"},
            "content": {"type": "string", "description": "النص المراد حفظه داخل الملف"}
        },
        "required": ["filename", "content"]
    },
    "run_system_code": {
        "type": "object",
        "properties": {
            "file_path": {"type": "string", "description": "مسار ملف البايثون المراد تشغيله"}
        },
        "required": ["file_path"]
    }
}


def list_system_files(folder: str = ".", **kwargs) -> str:
    """استعراض قائمة الملفات والمجلدات الموجودة في مسار معين."""
    for k in ["folder", "path", "directory", "dir"]:
        if k in kwargs and kwargs[k]:
            folder = kwargs[k]
            break
    try:
        if not os.path.exists(folder):
            return f"Error: Directory '{folder}' not found."
        files = sorted(os.listdir(folder))
        return "\n".join(files) if files else "Directory is empty."
    except Exception as e:
        return f"Error listing directory files: {str(e)}"


def read_system_file(filename: str = "", **kwargs) -> str:
    """قراءة المحتوى النصي لأي ملف محلي على الحاسوب."""
    for k in ["filename", "file", "path", "file_path"]:
        if k in kwargs and kwargs[k]:
            filename = kwargs[k]
            break
    if not filename:
        return "Error: No filename provided to read."
    try:
        if not os.path.exists(filename):
            return f"Error: File '{filename}' not found."
        with open(filename, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        return content[:4000] if content else f"File '{filename}' is empty."
    except Exception as e:
        return f"Error reading file '{filename}': {str(e)}"


def write_system_file(filename: str = "notes.txt", content: str = "", **kwargs) -> str:
    """كتابة وحفظ النصوص داخل ملف محدد في النظام."""
    for k in ["filename", "file", "path"]:
        if k in kwargs and kwargs[k]:
            filename = kwargs[k]
            break
    for k in ["content", "text", "data"]:
        if k in kwargs and kwargs[k]:
            content = kwargs[k]
            break
    try:
        folder = os.path.dirname(filename)
        if folder:
            os.makedirs(folder, exist_ok=True)
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)
        return f"SUCCESS: Content written successfully to '{filename}'."
    except Exception as e:
        return f"Error writing to file '{filename}': {str(e)}"


def run_system_code(file_path: str = "", timeout: int = 15, **kwargs) -> str:
    """تشغيل كود بايثون في بيئة معزولة واسترجاع المخرجات بأمان (مع فحص AST مسبق)."""
    from code_runner import run_python_code
    for k in ["file_path", "file", "script", "filename", "path"]:
        if k in kwargs and kwargs[k]:
            file_path = kwargs[k]
            break
    if not file_path:
        return "Error: No Python script path provided."
    return run_python_code(file_path, timeout=timeout)


# سجل الأدوات المُصدَّرة من هذا الموديول
EXPORTED_TOOLS = {
    "list_system_files": {
        "name": "List Directory Files",
        "description": "استعراض قائمة الملفات والمجلدات في مجلد محدد بالنظام.",
        "parameters": TOOL_PARAMETERS["list_system_files"],
        "fn": list_system_files,
        "function": list_system_files
    },
    "read_system_file": {
        "name": "Read System File",
        "description": "قراءة المحتوى النصي لأي ملف محلي على جهاز الحاسوب.",
        "parameters": TOOL_PARAMETERS["read_system_file"],
        "fn": read_system_file,
        "function": read_system_file
    },
    "write_system_file": {
        "name": "Write System File",
        "description": "كتابة وحفظ النصوص داخل ملف محدد في النظام.",
        "parameters": TOOL_PARAMETERS["write_system_file"],
        "fn": write_system_file,
        "function": write_system_file
    },
    "run_system_code": {
        "name": "Run Python Script",
        "description": "تشغيل ملف كود بايثون بأمان داخل النظام واسترجاع المخرجات (مع حماية AST).",
        "parameters": TOOL_PARAMETERS["run_system_code"],
        "fn": run_system_code,
        "function": run_system_code
    }
}
