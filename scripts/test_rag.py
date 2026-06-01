from src.rag_pipeline import answer_question

question = input("Ask a question: ")

response = answer_question(question)

print("\nAnswer:\n")
print(response)