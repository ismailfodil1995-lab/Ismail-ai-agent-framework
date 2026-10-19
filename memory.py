import json
import os
import re


MEMORY_FILE = "memory.json"


# ==========================================
# Load Memory
# ==========================================

def load_memory():

    if not os.path.exists(MEMORY_FILE):

        return {
            "user_name": None,
            "history": []
        }

    try:

        with open(
            MEMORY_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            data = json.load(f)

        # دعم النسخة القديمة
        if isinstance(data, list):

            return {
                "user_name": None,
                "history": data
            }

        return data

    except Exception:

        return {
            "user_name": None,
            "history": []
        }


# ==========================================
# Save Memory
# ==========================================

def save_memory(memory):

    with open(
        MEMORY_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            memory,
            f,
            ensure_ascii=False,
            indent=4
        )


# ==========================================
# Extract Name
# ==========================================

def extract_name(text):

    text = text.strip()

    # English

    match = re.search(
        r"my name is\s+(.+)",
        text,
        re.IGNORECASE
    )

    if match:

        return match.group(1).strip()

    # Arabic

    match = re.search(
        r"اسمي\s+(.+)",
        text
    )

    if match:

        return match.group(1).strip()

    return None


# ==========================================
# Add Memory
# ==========================================

def add_memory(user, assistant):

    memory = load_memory()

    name = extract_name(user)

    if name:

        memory["user_name"] = name

    memory["history"].append({

        "user": user,

        "assistant": assistant

    })

    memory["history"] = (
        memory["history"][-50:]
    )

    save_memory(memory)


# ==========================================
# Get Context
# ==========================================

def get_context():

    memory = load_memory()

    history = memory["history"]

    if not history:

        return ""

    context = []

    for item in history[-15:]:

        context.append(
            f"User: {item['user']}"
        )

        context.append(
            f"Assistant: {item['assistant']}"
        )

    return "\n".join(context)


# ==========================================
# Find User Name
# ==========================================

def find_user_name():

    memory = load_memory()

    return memory.get(
        "user_name"
    )


# ==========================================
# Clear Memory
# ==========================================

def clear_memory():

    save_memory({

        "user_name": None,

        "history": []

    })


# ==========================================
# Learn
# ==========================================

def learn(text):

    memory = load_memory()

    name = extract_name(text)

    if name:

        memory["user_name"] = name

        save_memory(memory)


# ==========================================
# Conversation
# ==========================================

def get_conversation():

    memory = load_memory()

    conversation = []

    for item in memory.get(
        "history",
        []
    )[-30:]:

        conversation.append({

            "role": "user",

            "content": item.get(
                "user",
                ""
            )

        })

        conversation.append({

            "role": "assistant",

            "content": item.get(
                "assistant",
                ""
            )

        })

    return conversation


# ==========================================
# All Memory
# ==========================================

def all_memory():

    memory = load_memory()

    return {

        "user_name":
            memory.get(
                "user_name"
            ),

        "history":
            memory.get(
                "history",
            []
            )
    }


# ==========================================
# Memory Class
# ==========================================

class Memory:

    def learn(self, text):

        learn(text)

    def all_memory(self):

        return all_memory()

    def get_conversation(self):

        return get_conversation()

    def get_context(self):

        return get_context()

    def add_message(
        self,
        role,
        content
    ):

        memory = load_memory()

        memory["history"].append({

            "user":
                content if role == "user"
                else "",

            "assistant":
                content if role == "assistant"
                else ""

        })

        memory["history"] = (
            memory["history"][-50:]
        )

        save_memory(memory)

    def add_memory(
        self,
        user,
        assistant
    ):

        add_memory(
            user,
            assistant
        )

    def find_user_name(self):

        return find_user_name()

    def clear_memory(self):

        clear_memory()


# ==========================================
# Memory Instance
# ==========================================

memory = Memory()
