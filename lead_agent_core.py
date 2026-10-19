from llm.manager import generate
from memory import memory

from config import (
    AGENT_NAME,
    CREATOR_NAME,
)


def analyze_lead(user_message):
    """
    العقل الرئيسي للوكيل.
    """

    # =====================================
    # تعلم تلقائي
    # =====================================

    memory.learn(user_message)

    # =====================================
    # استرجاع الذاكرة
    # =====================================

    long_memory = memory.all_memory()

    conversation = memory.get_conversation()

    memory_text = ""

    for key, value in long_memory.items():

        memory_text += f"{key}: {value}\n"

    conversation_text = ""

    for msg in conversation:

        conversation_text += (
            f"{msg['role']}: {msg['content']}\n"
        )

    # =====================================
    # Prompt
    # =====================================

    prompt = f"""
You are {AGENT_NAME}.

Rules:

- Your name is {AGENT_NAME}.
- Your creator is {CREATOR_NAME}.
- Never say you are Qwen.
- Never say you are Alibaba Cloud.
- Never say you are an AI model.
- Stay in character.

Long Memory:

{memory_text}

Conversation:

{conversation_text}

Current User Message:

{user_message}

Assistant:
"""

    # =====================================
    # LLM
    # =====================================

    answer = generate(prompt)

    # =====================================
    # تنظيف الإجابة
    # =====================================

    banned = [

        "Qwen",
        "Qwen2",
        "Qwen2.5",
        "Alibaba Cloud"

    ]

    for word in banned:

        answer = answer.replace(
            word,
            AGENT_NAME
        )

    # =====================================
    # تحديث المحادثة
    # =====================================

    memory.add_message(
        "user",
      user_message
    )

    memory.add_message(
        "assistant",
        answer
    )

    return answer  