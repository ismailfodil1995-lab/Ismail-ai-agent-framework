from openai import OpenAI

client = OpenAI()


def generate(prompt):

    response = client.responses.create(
        model="gpt-5-mini",
        input=prompt,
    )

    return response.output_text