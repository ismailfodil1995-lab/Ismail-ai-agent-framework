import sqlite3
import os
from typing import Any, List, Optional
from tools import register_tool


def _ensure_default_tables(cursor: sqlite3.Cursor) -> None:
    """إنشاء الجداول الافتراضية إذا لم تكن موجودة مسبقاً لخدمة الوكيل"""
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_name TEXT,
            score INTEGER,
            category TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_name TEXT,
            status TEXT DEFAULT 'PENDING',
            result TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)


@register_tool(
    name="query_local_db",
    description="تخزين واسترجاع وإدارة البيانات في قاعدة بيانات SQLite محلية."
)
def query_local_db(
    query: str = "",
    params: Optional[List[Any]] = None,
    db_name: str = "agent_data.db",
    **kwargs
) -> str:
    """
    تنفيذ استعلامات SQL وقراءة وكتابة البيانات في قاعدة بيانات SQLite محلية.
    """
    for k in ["sql", "command", "statement"]:
        if k in kwargs and kwargs[k]:
            query = kwargs[k]
            break

    for k in ["parameters", "args", "values"]:
        if k in kwargs and kwargs[k]:
            params = kwargs[k]
            break

    for k in ["database", "db", "db_path"]:
        if k in kwargs and kwargs[k]:
            db_name = kwargs[k]
            break

    if not query or not query.strip():
        # إذا لم يتم تمرير استعلام، نعرض ملخص الجداول الموجودة
        query = "SELECT name FROM sqlite_master WHERE type='table';"

    params = params or []
    if isinstance(params, tuple):
        params = list(params)
    elif not isinstance(params, list):
        params = [params]

    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        _ensure_default_tables(cursor)
        conn.commit()

        clean_query = query.strip()
        cursor.execute(clean_query, params)

        # استعلام قراءة (SELECT)
        if clean_query.upper().startswith("SELECT") or clean_query.upper().startswith("PRAGMA"):
            rows = cursor.fetchall()
            col_names = [desc[0] for desc in cursor.description] if cursor.description else []
            conn.close()

            if not rows:
                return f"SUCCESS: Query executed on '{db_name}'. Result: 0 rows returned."

            # تنسيق مخرجات الجدول
            header = " | ".join(col_names)
            separator = "-" * max(40, len(header))
            data_rows = [" | ".join(str(val) for val in row) for row in rows[:50]]
            table_preview = f"{header}\n{separator}\n" + "\n".join(data_rows)
            return f"SUCCESS: Query returned {len(rows)} row(s) from '{db_name}':\n{table_preview}"

        # استعلام كتابة / تعديل (INSERT, UPDATE, DELETE, CREATE, DROP)
        else:
            conn.commit()
            affected = cursor.rowcount
            conn.close()
            return f"SUCCESS: SQL statement executed successfully on '{db_name}'. Rows affected: {affected}."

    except Exception as e:
        return f"Error executing database query on '{db_name}': {str(e)}"
