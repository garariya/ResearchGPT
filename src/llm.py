from groq import Groq
from dotenv import load_dotenv
import os


load_dotenv()

client = Groq(
    api_key=os.getenv(
        "GROQ_API_KEY"
    )
)


def ask_llm(context, question):

    prompt = f"""
You are a research assistant.

Use ONLY the provided context.

If the answer cannot be found in the context, say:
'I could not find sufficient information in the uploaded documents.'

Do not invent facts.
Provide concise and accurate answers.

Context:
{context}

Question:
{question}
    """

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return response.choices[0].message.content