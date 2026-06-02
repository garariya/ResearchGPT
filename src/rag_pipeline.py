from src.retriever import retrieve
from src.llm import ask_llm


def answer_question(question):

    retrieved = retrieve(question)

    docs = [item["text"] for item in retrieved]
    context = "\n\n".join(docs)

    answer = ask_llm(
        context,
        question
    )

    # Aggregate citations by unique source to avoid duplicates in UI.
    # Output shape is optimized for the Streamlit display layer.
    aggregated = {}
    for item in retrieved:
        md = item.get("metadata") or {}
        source_type = md.get("source_type", "unknown")
        source_name = md.get("source_name", "Unknown Source")
        chunk_index = md.get("chunk_index")

        key = (source_type, source_name)
        if key not in aggregated:
            aggregated[key] = {
                "source_type": source_type,
                "source_name": source_name,
                "chunk_indices": set(),
            }

        if chunk_index is not None:
            aggregated[key]["chunk_indices"].add(chunk_index)

    sources = []
    for (_, _), entry in aggregated.items():
        sources.append(
            {
                "source_type": entry["source_type"],
                "source_name": entry["source_name"],
                "chunk_indices": sorted(entry["chunk_indices"]),
            }
        )

    # Stable order for nicer UX.
    sources.sort(key=lambda s: (s["source_type"], s["source_name"]))

    return {
        "answer": answer,
        "sources": sources,
    }