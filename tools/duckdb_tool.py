"""
DuckDB Tool – tools/duckdb_tool.py
أداة تحليل واستعلام قواعد البيانات والملفات الضخمة (CSV, Parquet, JSON) بسرعة فائقة عبر محرك DuckDB OLAP.
تدعم الاستعلامات المباشرة، فحص المخطط الإحصائي (Schema & Profiling)، والتحويل الفوري بين الصيغ.
"""

import os
import time
from typing import Any, Dict, List, Optional
import duckdb

from tools import register_tool


TOOL_PARAMETERS = {
    "query_duckdb": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "استعلام SQL المراد تنفيذه (يدعم SELECT, Aggregations, Window Functions)"},
            "file_path": {"type": "string", "description": "مسار ملف CSV أو Parquet للاستعلام المباشر عنه (اختياري)"},
            "limit": {"type": "integer", "description": "الحد الأقصى للأسطر المعروضة في النتيجة (افتراضياً: 50)"}
        },
        "required": ["query"]
    },
    "inspect_dataset_duckdb": {
        "type": "object",
        "properties": {
            "file_path": {"type": "string", "description": "مسار ملف CSV أو Parquet المطلوب فحصه واستخراج إحصائياته"}
        },
        "required": ["file_path"]
    },
    "convert_dataset_duckdb": {
        "type": "object",
        "properties": {
            "input_file": {"type": "string", "description": "مسار الملف المصدر (.csv أو .parquet)"},
            "output_file": {"type": "string", "description": "مسار الملف الهدف الناتج (.parquet أو .csv)"}
        },
        "required": ["input_file", "output_file"]
    }
}





@register_tool(
    name="query_duckdb",
    description="تنفيذ استعلامات SQL فائقة السرعة عبر DuckDB مباشرة على ملفات CSV و Parquet وقواعد البيانات."
)
def query_duckdb(
    query: str = "",
    file_path: str = "",
    db_path: str = ":memory:",
    limit: int = 50,
    **kwargs
) -> str:
    """
    تنفيذ استعلام SQL باستخدام DuckDB على ملفات محلية أو قاعدة بيانات في الذاكرة.
    """
    for k in ["sql", "statement", "command"]:
        if k in kwargs and kwargs[k]:
            query = kwargs[k]
            break

    for k in ["file", "path", "dataset", "table"]:
        if k in kwargs and kwargs[k]:
            file_path = kwargs[k]
            break

    for k in ["max_rows", "rows_limit"]:
        if k in kwargs and kwargs[k]:
            try:
                limit = int(kwargs[k])
            except (ValueError, TypeError):
                pass
            break

    clean_file = file_path.strip().replace("\\", "/") if file_path else ""

    # إذا تم تمرير مسار ملف دون كتابة استعلام كامل، ننشئ استعلام عرض افتراضي
    if not query.strip() and clean_file:
        query = f"SELECT * FROM '{clean_file}'"

    if not query.strip():
        return "Error: No SQL query or file_path provided for DuckDB."

    clean_query = query.strip()

    # إذا كان هناك ملف ممرر ولم يُذكر اسمه بالاستعلام
    if clean_file and ("FROM" not in clean_query.upper()):
        clean_query = f"{clean_query} FROM '{clean_file}'"

    t0 = time.perf_counter()

    try:
        conn = duckdb.connect(database=db_path, read_only=False)

        # تنفيذ الاستعلام
        rel = conn.sql(clean_query)

        if rel is None:
            conn.close()
            elapsed_ms = (time.perf_counter() - t0) * 1000
            return f"SUCCESS: SQL command executed successfully in {elapsed_ms:.2f}ms."

        col_names = rel.columns
        total_rows = rel.shape[0]

        # استخراج عينة للعرض بناءً على limit
        preview_rel = rel.limit(limit)
        rows = preview_rel.fetchall()
        conn.close()

        elapsed_ms = (time.perf_counter() - t0) * 1000

        if not rows:
            return f"SUCCESS: Query executed in {elapsed_ms:.2f}ms. Returned 0 rows."

        # تنسيق الجدول النصي
        col_widths = [len(str(c)) for c in col_names]
        str_rows = []
        for row in rows:
            row_strs = [str(val) if val is not None else "NULL" for val in row]
            for i, val_s in enumerate(row_strs):
                col_widths[i] = max(col_widths[i], min(len(val_s), 40))
            str_rows.append(row_strs)

        header_parts = [col_names[i].ljust(col_widths[i]) for i in range(len(col_names))]
        header = " | ".join(header_parts)
        separator = "-+-".join(["-" * col_widths[i] for i in range(len(col_names))])

        data_lines = []
        for r in str_rows:
            truncated_cells = [r[i][:40].ljust(col_widths[i]) for i in range(len(col_names))]
            data_lines.append(" | ".join(truncated_cells))

        table_output = f"{header}\n{separator}\n" + "\n".join(data_lines)
        limit_note = f" (Showing top {len(rows)} of {total_rows} total rows)" if total_rows > len(rows) else ""

        return (
            f"SUCCESS: DuckDB Query executed in {elapsed_ms:.2f}ms{limit_note}:\n\n"
            f"{table_output}"
        )

    except Exception as e:
        return f"Error executing DuckDB query: {str(e)}"


@register_tool(
    name="inspect_dataset_duckdb",
    description="فحص وتحليل بنية ومخطط ملفات CSV و Parquet الضخمة (Schema, Columns, Row Count) عبر DuckDB."
)
def inspect_dataset_duckdb(file_path: str = "", **kwargs) -> str:
    """
    استخراج سريع لمعلومات المخطط والإحصائيات لملف CSV أو Parquet.
    """
    for k in ["file", "path", "dataset", "dataset_path"]:
        if k in kwargs and kwargs[k]:
            file_path = kwargs[k]
            break

    if not file_path:
        return "Error: No file_path provided to inspect dataset."

    if not os.path.exists(file_path):
        return f"Error: Dataset file '{file_path}' not found."

    clean_file = file_path.strip().replace("\\", "/")
    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)

    t0 = time.perf_counter()
    try:
        conn = duckdb.connect()

        # 1. حساب إجمالي عدد الأسطر
        count_res = conn.sql(f"SELECT COUNT(*) FROM '{clean_file}'").fetchone()
        total_rows = count_res[0] if count_res else 0

        # 2. استخراج المخطط (Schema)
        schema_res = conn.sql(f"DESCRIBE SELECT * FROM '{clean_file}'").fetchall()

        # 3. استخراج أول 3 أسطر كمعاينة
        sample_rel = conn.sql(f"SELECT * FROM '{clean_file}' LIMIT 3")
        sample_cols = sample_rel.columns
        sample_rows = sample_rel.fetchall()

        conn.close()
        elapsed_ms = (time.perf_counter() - t0) * 1000

        # تجميع تقرير المخطط
        schema_lines = []
        for col_info in schema_res:
            c_name = col_info[0]
            c_type = col_info[1]
            c_null = col_info[2]
            schema_lines.append(f"  - {c_name} ({c_type}) | Nullable: {c_null}")

        sample_table = ""
        if sample_rows:
            header = " | ".join(sample_cols)
            div = "-" * max(30, len(header))
            rows_str = [" | ".join(str(v)[:30] for v in r) for r in sample_rows]
            sample_table = f"\nSample Data Preview:\n{header}\n{div}\n" + "\n".join(rows_str)

        return (
            f"=== DuckDB Dataset Inspection Report ===\n"
            f"File: {file_path}\n"
            f"Size: {file_size_mb:.2f} MB\n"
            f"Total Rows: {total_rows:,}\n"
            f"Columns ({len(schema_res)}):\n"
            + "\n".join(schema_lines)
            + f"\n{sample_table}\n\n"
            f"(Analyzed in {elapsed_ms:.2f}ms via DuckDB Engine)"
        )

    except Exception as e:
        return f"Error inspecting dataset '{file_path}' via DuckDB: {str(e)}"


@register_tool(
    name="convert_dataset_duckdb",
    description="تحويل عالي السرعة بين ملفات CSV و Parquet باستخدام DuckDB (مثل تحويل CSV ضخم إلى Parquet مضغوط)."
)
def convert_dataset_duckdb(input_file: str = "", output_file: str = "", **kwargs) -> str:
    """
    تحويل صيغ البيانات بين CSV و Parquet في ثوانٍ معدودة دون تحميل الذاكرة.
    """
    for k in ["source", "src", "input", "input_path"]:
        if k in kwargs and kwargs[k]:
            input_file = kwargs[k]
            break

    for k in ["dest", "target", "output", "output_path"]:
        if k in kwargs and kwargs[k]:
            output_file = kwargs[k]
            break

    if not input_file or not output_file:
        return "Error: Both 'input_file' and 'output_file' are required for conversion."

    if not os.path.exists(input_file):
        return f"Error: Input file '{input_file}' does not exist."

    clean_in = input_file.strip().replace("\\", "/")
    clean_out = output_file.strip().replace("\\", "/")
    out_ext = os.path.splitext(clean_out)[1].lower()

    format_clause = "PARQUET" if out_ext == ".parquet" else "CSV, HEADER TRUE"

    t0 = time.perf_counter()
    try:
        conn = duckdb.connect()
        sql_cmd = f"COPY (SELECT * FROM '{clean_in}') TO '{clean_out}' (FORMAT {format_clause})"
        conn.sql(sql_cmd)
        conn.close()

        elapsed_s = time.perf_counter() - t0
        in_size_mb = os.path.getsize(input_file) / (1024 * 1024)
        out_size_mb = os.path.getsize(output_file) / (1024 * 1024)

        return (
            f"SUCCESS: Converted '{input_file}' ({in_size_mb:.2f} MB) -> "
            f"'{output_file}' ({out_size_mb:.2f} MB) in {elapsed_s:.2f}s using DuckDB."
        )

    except Exception as e:
        return f"Error converting dataset via DuckDB: {str(e)}"


EXPORTED_TOOLS = {
    "query_duckdb": {
        "name": "DuckDB SQL Query",
        "description": "تنفيذ استعلامات SQL فائقة السرعة على ملفات CSV و Parquet مباشرة.",
        "parameters": TOOL_PARAMETERS["query_duckdb"],
        "fn": query_duckdb,
        "function": query_duckdb
    },
    "inspect_dataset_duckdb": {
        "name": "DuckDB Dataset Inspector",
        "description": "فحص المخطط والعدد الإجمالي للأسطر والإحصائيات لملفات البيانات.",
        "parameters": TOOL_PARAMETERS["inspect_dataset_duckdb"],
        "fn": inspect_dataset_duckdb,
        "function": inspect_dataset_duckdb
    },
    "convert_dataset_duckdb": {
        "name": "DuckDB Format Converter",
        "description": "تحويل فوري عالي الكفاءة بين ملفات CSV و Parquet.",
        "parameters": TOOL_PARAMETERS["convert_dataset_duckdb"],
        "fn": convert_dataset_duckdb,
        "function": convert_dataset_duckdb
    }
}
