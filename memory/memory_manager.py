from memory.short_memory import ShortMemory
from memory.long_memory import LongMemory

from config import MAX_CONVERSATION_MESSAGES


class MemoryManager:
    """
    الطبقة الوحيدة التي يتعامل معها المشروع.
    كل instance مرتبطة بـ session_id محدد لضمان عزل كامل بين المستخدمين.
    """

    def __init__(self, session_id: str = "default"):
        self.session_id = str(session_id)
        self.short = ShortMemory(MAX_CONVERSATION_MESSAGES)
        self.long = LongMemory(session_id=self.session_id)
        self.long.ensure_defaults()

    # =====================================
    # Short Memory
    # =====================================

    def add_message(self, role, content):
        self.short.add(role, content)

    def get_conversation(self):
        return self.short.get()

    def clear_conversation(self):
        self.short.clear()

    # =====================================
    # Long Memory
    # =====================================

    def remember(self, key, value):
        self.long.remember(key, value)

    def recall(self, key):
        return self.long.recall(key)

    def forget(self, key):
        self.long.forget(key)

    def all_memory(self):
        return self.long.all()

    def learn(self, user_message):
        self.long.learn(user_message)

    def build_context(self):
        return self.long.build_context()

    def load_conversation(self, chat_id):
        return self.long.load_conversation(chat_id)

    def save_conversation(self, chat_id, messages):
        self.long.save_conversation(chat_id, messages, MAX_CONVERSATION_MESSAGES)

    def delete_session(self):
        """حذف كل بيانات الجلسة الحالية."""
        self.long.delete_session()

    @staticmethod
    def list_sessions():
        """عرض جميع الجلسات الموجودة في قاعدة البيانات."""
        return LongMemory.list_sessions()
