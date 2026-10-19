"""
Excel Tool – tools/excel_tool.py
أداة مستقلة لإنشاء وقراءة ملفات Excel (.xlsx).
مفصولة عن brain.py لضمان النظافة المعمارية وسهولة الصيانة.
"""

import os

TOOL_PARAMETERS = {
    "generate_excel_report": {
        "type": "object",
        "properties": {
            "data": {"type": "array", "description": "البيانات أو القوائم المراد تصديرها لملف إكسل"},
            "filename": {"type": "string", "description": "اسم ملف الإكسل الناتج (.xlsx)"}
        }
    },
    "read_excel_file": {
        "type": "object",
        "properties": {
            "filename": {"type": "string", "description": "مسار ملف الإكسل لقراءته"}
        },
        "required": ["filename"]
    }
}


def generate_excel_report(data=None, filename: str = "automation_report.xlsx", **kwargs) -> str:
    """توليد تقرير Excel منسق واحترافي من البيانات وحفظه في ملف .xlsx."""
    for k in ["file", "filename", "output_path", "name"]:
        if k in kwargs and kwargs[k]:
            filename = kwargs[k]
            break
    if not filename.endswith(".xlsx"):
        filename += ".xlsx"
    try:
        import pandas as pd
        if data is None or not data:
            data = [{"ملاحظة": "تقرير تلقائي تم إنشاؤه بنجاح", "الحالة": "Active"}]
        elif isinstance(data, str):
            data = [{"البيانات": data}]
        df = pd.DataFrame(data)
        df.to_excel(filename, index=False)
        return f"SUCCESS: Excel report generated successfully as '{filename}'"
    except Exception as e:
        return f"Error generating Excel report: {str(e)}"


def read_excel_file(filename: str = "automation_report.xlsx", **kwargs) -> str:
    """قراءة واستخراج محتوى جداول ملفات Excel (.xlsx, .xls)."""
    for k in ["file", "path", "file_path", "filename"]:
        if k in kwargs and kwargs[k]:
            filename = kwargs[k]
            break
    try:
        import pandas as pd
        if not os.path.exists(filename):
            return f"Error: Excel file '{filename}' not found."
        df = pd.read_excel(filename)
        return df.to_string(index=False)[:4000] if not df.empty else "Warning: Excel sheet is empty."
    except Exception as e:
        return f"Error reading Excel file: {str(e)}"


# سجل الأدوات المُصدَّرة من هذا الموديول
EXPORTED_TOOLS = {
    "generate_excel_report": {
        "name": "Generate Excel Report",
        "description": "توليد تقارير Excel (.xlsx) منسقة واحترافية من البيانات المستخرجة.",
        "parameters": TOOL_PARAMETERS["generate_excel_report"],
        "fn": generate_excel_report,
        "function": generate_excel_report
    },
    "read_excel_file": {
        "name": "Read Excel File",
        "description": "قراءة واستخراج البيانات والجداول من ملفات Excel المحلية.",
        "parameters": TOOL_PARAMETERS["read_excel_file"],
        "fn": read_excel_file,
        "function": read_excel_file
    }
}
