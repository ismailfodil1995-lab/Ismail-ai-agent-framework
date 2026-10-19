from brain import process_user_query

def run_comprehensive_test():
    print("==========================================")
    print("🤖 Running Full Agent Capability Test...")
    print("==========================================\n")

    # قائمة بالاختبارات الشاملة لكل قدرات الوكيل
    test_prompts = [
        "Hello! Who are you and what model are you running on?",
        "My name is Ismail and I am building an AI lead qualification framework for Upwork. Remember this.",
        "What is my name and what project am I working on?",
        "List all available tools and explain how you can use them.",
        "Can you check or read any available local PDF files or documents in the workspace?"
    ]

    for i, prompt in enumerate(test_prompts, 1):
        print(f"\n--- Test Step {i} ---")
        print(f"You: {prompt}")
        
        # إرسال الطلب للدماغ والأدوات
        response = process_user_query(prompt, chat_id=1)
        print(f"\n🤖 Agent:\n{response}\n")
        print("-" * 40)

if __name__ == "__main__":
    run_comprehensive_test()