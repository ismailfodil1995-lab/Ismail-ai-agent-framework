from openai import OpenAI

client = OpenAI()


def ask_llm(prompt):
    """
    إرسال الطلب إلى نموذج OpenAI.
    """

    response = client.responses.create(
        model="gpt-5-mini",
        input=prompt,
    )

    return response.output_text