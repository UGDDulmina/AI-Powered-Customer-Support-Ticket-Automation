import os
from openai import OpenAI
from dotenv import load_dotenv


def generate_test_response() -> str:
    load_dotenv()

    client = OpenAI(
        api_key=os.getenv("OPENROUTER_API_KEY"),
        base_url="https://openrouter.ai/api/v1"
    )

    response = client.chat.completions.create(
        model="openrouter/free",
        messages=[
            {
                "role": "system",
                "content": "You are a helpful customer support assistant."
            },
            {
                "role": "user",
                "content": "Write a short greeting for a customer."
            }
        ]
    )

    return response.choices[0].message.content or ""