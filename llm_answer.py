import os
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def generate_answer(question, pages, history=None):
    context = "\n\n".join([
        f"File: {page['file_name']} | Page: {page['page_number']}\n{page['text']}"
        for page in pages
    ])

    chat_history = ""
    if history:
        chat_history = "\n".join([
            f"User: {q}\nAssistant: {a}"
            for q, a in history
        ])

    prompt = f"""
You are DocMind, a detailed PDF question-answering chatbot.

Rules:
1. Answer ONLY using the PDF context.
2. Do not use outside knowledge.
3. If the answer is not in the PDF context, say:
"I could not find this information in the uploaded PDFs."
4. Use previous conversation only to understand follow-up questions.
5. Give a detailed answer when the PDF context has enough information.
6. Explain in simple language.
7. Use headings and bullet points.
8. Include examples if the PDF context supports them.
9. Do not give only a short summary unless the user asks for short answer.

Previous Conversation:
{chat_history}

User Question:
{question}

PDF Context:
{context}

Now give a detailed, well-structured answer.
"""

    response = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[
        {"role": "user", "content": prompt}
    ],
    temperature=0.2,
    max_tokens=1500
)

    return response.choices[0].message.content