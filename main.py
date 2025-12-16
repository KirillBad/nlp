import argparse
from pathlib import Path
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("API_KEY"),
)


def create_report(text: str) -> str | None:
    completion = client.chat.completions.create(
        extra_body={},
        model="x-ai/grok-code-fast-1",
        messages=[
            {"role": "user", "content": f"Создай реферат для этой статьи: {text}"}
        ],
    )

    return completion.choices[0].message.content


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Batch NLP Pipeline.")

    parser.add_argument("filenames", type=Path, help="Paths to source files")

    args = parser.parse_args()

    with open(args.filenames, "r", encoding="utf-8") as f:
        answer = create_report(text=f.read())

    with open(args.filenames, "w", encoding="utf-8") as f:
        answer = create_report(text=f.read())
