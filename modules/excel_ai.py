from llm.manager import generate
from computer_tools import read_excel


class ExcelAI:
    """
    تحليل ملفات Excel باستخدام الـ LLM.
    """

    # =====================================

    def summarize(self, filename):

        print("=" * 60)
        print("STEP 1 : Opening Excel")

        text = read_excel(filename)

        print("STEP 2 : Excel Loaded")

        if (
            text.startswith("Excel file not found")
            or
            text.startswith("Error")
        ):
            return text

        print(f"Characters : {len(text)}")

        if len(text) > 3000:
            text = text[:3000]

        print(f"Characters Sent : {len(text)}")

        prompt = f"""
You are an expert data analyst.

Analyze the following Excel sheet.

Return:

1. Summary.

2. Important columns.

3. Interesting patterns.

4. Numbers worth noting.

Excel Data:

{text}
"""

        print("STEP 3 : Sending Prompt To Ollama")

        result = generate(prompt)

        print("STEP 4 : Ollama Finished")

        return result

    # =====================================

    def ask(self, filename, question):

        text = read_excel(filename)

        if (
            text.startswith("Excel file not found")
            or
            text.startswith("Error")
        ):
            return text

        if len(text) > 3000:
            text = text[:3000]

        prompt = f"""
Answer ONLY using this Excel sheet.

Excel:

{text}

Question:

{question}

Answer:
"""

        return generate(prompt)


excel_ai = ExcelAI()