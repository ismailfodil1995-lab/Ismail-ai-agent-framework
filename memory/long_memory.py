import json
import sqlite3
import threading
from contextlib import contextmanager

from config import MEMORY_DB_FILE


class LongMemory:
    """
    الذاكرة الطويلة — مدعومة بـ SQLite مع دعم Multi-tenancy الكامل.
    كل مستخدم/جلسة معزولة تماماً عبر session_id.
    """

    def __init__(self, session_id: str = "default"):
        self.session_id = str(session_id)
        self._lock = threading.Lock()   # حماية الكتابة عند تعدد الخيوط
        self._init_db()

    # ------------------------------------------------------------------
    # DB Bootstrap
    # ------------------------------------------------------------------

    def _init_db(self):
        with self._conn() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS memory (
                    session_id TEXT NOT NULL,
                    key        TEXT NOT NULL,
                    value      TEXT NOT NULL,
                    PRIMARY KEY (session_id, key)
                );

                CREATE TABLE IF NOT EXISTS conversations (
                    session_id TEXT NOT NULL,
                    chat_id    TEXT NOT NULL,
                    messages   TEXT NOT NULL DEFAULT '[]',
                    PRIMARY KEY (session_id, chat_id)
                );
            """)

    @contextmanager
    def _conn(self):
        """Thread-safe SQLite connection."""
        conn = sqlite3.connect(MEMORY_DB_FILE, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # Core KV Operations (scoped to session_id)
    # ------------------------------------------------------------------

    def remember(self, key: str, value):
        serialized = json.dumps(value, ensure_ascii=False)
        with self._lock:
            with self._conn() as conn:
                conn.execute(
                    "INSERT INTO memory (session_id, key, value) VALUES (?, ?, ?)"
                    " ON CONFLICT(session_id, key) DO UPDATE SET value=excluded.value",
                    (self.session_id, key, serialized),
                )

    def recall(self, key: str):
        with self._conn() as conn:
            row = conn.execute(
                "SELECT value FROM memory WHERE session_id=? AND key=?",
                (self.session_id, key),
            ).fetchone()
        return json.loads(row["value"]) if row else None

    def forget(self, key: str):
        with self._lock:
            with self._conn() as conn:
                conn.execute(
                    "DELETE FROM memory WHERE session_id=? AND key=?",
                    (self.session_id, key),
                )

    def all(self) -> dict:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT key, value FROM memory WHERE session_id=?",
                (self.session_id,),
            ).fetchall()
        return {r["key"]: json.loads(r["value"]) for r in rows}

    # ------------------------------------------------------------------
    # Conversation History (scoped to session_id + chat_id)
    # ------------------------------------------------------------------

    def load_conversation(self, chat_id) -> list:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT messages FROM conversations WHERE session_id=? AND chat_id=?",
                (self.session_id, str(chat_id)),
            ).fetchone()
        return json.loads(row["messages"]) if row else []

    def save_conversation(self, chat_id, messages: list, max_messages: int):
        trimmed = messages[-max_messages:] if messages else []
        with self._lock:
            with self._conn() as conn:
                if trimmed:
                    conn.execute(
                        "INSERT INTO conversations (session_id, chat_id, messages) VALUES (?, ?, ?)"
                        " ON CONFLICT(session_id, chat_id) DO UPDATE SET messages=excluded.messages",
                        (self.session_id, str(chat_id), json.dumps(trimmed, ensure_ascii=False)),
                    )
                else:
                    conn.execute(
                        "DELETE FROM conversations WHERE session_id=? AND chat_id=?",
                        (self.session_id, str(chat_id)),
                    )

    # ------------------------------------------------------------------
    # Learning & Context
    # ------------------------------------------------------------------

    def learn(self, user_message: str):
        text = user_message.strip()
        lower = text.lower()

        if lower.startswith("my name is "):
            name = text[11:].strip()
            if name:
                self.remember("name", name)

        elif lower.startswith("my project is "):
            project = text[14:].strip()
            if project:
                self.remember("project", project)

        elif lower.startswith("i am ") and not text[5:].strip().isdigit():
            name = text[5:].strip()
            if name:
                self.remember("name", name)

        elif "اسمي" in text:
            parts = text.split("اسمي", 1)
            if len(parts) > 1:
                name = parts[1].strip(" :،.-")
                if name:
                    self.remember("name", name)

        elif "مشروعي" in text:
            parts = text.split("مشروعي", 1)
            if len(parts) > 1:
                project = parts[1].strip(" :،.-")
                if project:
                    self.remember("project", project)

        elif any(kw in lower for kw in ["lead qualification", "تأهيل العملاء", "upwork"]):
            if any(kw in lower for kw in ["working on", "building", "project", "مشروع", "أعمل على", "أبني"]):
                self.remember(
                    "project",
                    "إطار تأهيل العملاء المحتملين (Lead Qualification) لمشاريع Upwork",
                )

    def build_context(self) -> str:
        facts = self.all()
        lines = []
        if facts.get("name"):
            lines.append(f"- اسم المستخدم: {facts['name']}")
        if facts.get("project"):
            lines.append(f"- مشروع المستخدم: {facts['project']}")
        for key, value in facts.items():
            if key in {"name", "project"}:
                continue
            if isinstance(value, str) and value.strip():
                lines.append(f"- {key}: {value}")
        return "\n".join(lines)

    def ensure_defaults(self):
        """تعيين القيم الافتراضية بمعاملة واحدة آمنة تجنباً لتعارض الخيوط."""
        default_project = json.dumps(
            "إطار تأهيل العملاء المحتملين (Lead Qualification) لمشاريع Upwork",
            ensure_ascii=False,
        )
        with self._lock:
            with self._conn() as conn:
                conn.execute(
                    "INSERT INTO memory (session_id, key, value) VALUES (?, 'name', ?)"
                    " ON CONFLICT(session_id, key) DO NOTHING",
                    (self.session_id, json.dumps("Ismail", ensure_ascii=False)),
                )
                conn.execute(
                    "INSERT INTO memory (session_id, key, value) VALUES (?, 'project', ?)"
                    " ON CONFLICT(session_id, key) DO NOTHING",
                    (self.session_id, default_project),
                )

    # ------------------------------------------------------------------
    # Admin helpers (cross-session)
    # ------------------------------------------------------------------

    def delete_session(self):
        """حذف كل بيانات الجلسة الحالية نهائياً."""
        with self._lock:
            with self._conn() as conn:
                conn.execute("DELETE FROM memory WHERE session_id=?", (self.session_id,))
                conn.execute("DELETE FROM conversations WHERE session_id=?", (self.session_id,))

    @staticmethod
    def list_sessions() -> list:
        """إرجاع قائمة بجميع session_ids الموجودة في قاعدة البيانات."""
        with sqlite3.connect(MEMORY_DB_FILE) as conn:
            rows = conn.execute(
                "SELECT DISTINCT session_id FROM memory "
                "UNION SELECT DISTINCT session_id FROM conversations"
            ).fetchall()
        return [r[0] for r in rows]
