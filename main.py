import brain

def main():
    print("==========================================")
    print("🤖 AI Agent Core Online & Ready.")
    print("Type 'exit' or 'quit' to stop.")
    print("==========================================\n")

    while True:
        try:
            user_input = input("You: ")
            if user_input.lower().strip() in ["exit", "quit"]:
                print("Shutting down Agent. Goodbye!")
                break

            if not user_input.strip():
                continue

            # تشغيل الدالة الصحيحة مباشرة
            brain.qualify_lead(user_input)
            print()

        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"System Error: {e}\n")

if __name__ == "__main__":
    main()