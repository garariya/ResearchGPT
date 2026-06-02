from src.rag_pipeline import answer_question

question = input("Ask a question: ")

response = answer_question(question)

print("\nAnswer:\n")
print(response["answer"])

print("\nSources:\n")
for i, src in enumerate(response.get("sources", []), start=1):
    name = src.get("source_name", "Unknown Source")
    stype = src.get("source_type", "unknown")
    chunks = src.get("chunk_indices", [])
    if stype == "pdf" and chunks:
        print(f"[{i}] {name} (Chunks: {', '.join(str(c) for c in chunks)})")
    else:
        print(f"[{i}] {name}")