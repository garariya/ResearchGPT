from src.retriever import retrieve
from src.llm import ask_llm


def answer_question(question):

    docs = retrieve(question)

    context = "\n\n".join(docs)

    answer = ask_llm(
        context,
        question
    )

    return answer