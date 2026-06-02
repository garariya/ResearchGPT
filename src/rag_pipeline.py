from src.retriever import retrieve
from src.llm import ask_llm


def answer_question(question, document_ids=None):

    retrieved = retrieve(question, document_ids=document_ids)

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
        source_name = md.get("source_name", md.get("title", "Unknown Source"))
        title = md.get("title", source_name)
        authors = md.get("authors", "Unknown")
        year = md.get("year", "Unknown")
        chunk_index = md.get("chunk_index")

        document_id = md.get("document_id")
        key = (document_id, source_type, source_name)
        if key not in aggregated:
            aggregated[key] = {
                "document_id": document_id,
                "source_type": source_type,
                "source_name": source_name,
                "title": title,
                "authors": authors,
                "year": year,
                "chunk_indices": set(),
            }

        if chunk_index is not None:
            aggregated[key]["chunk_indices"].add(chunk_index)

    sources = []
    for (_, _, _), entry in aggregated.items():
        sources.append(
            {
                "document_id": entry.get("document_id"),
                "source_type": entry["source_type"],
                "source_name": entry["source_name"],
                "title": entry["title"],
                "authors": entry["authors"],
                "year": entry["year"],
                "chunk_indices": sorted(entry["chunk_indices"]),
            }
        )

    # Stable order for nicer UX.
    sources.sort(key=lambda s: (s["source_type"], s["source_name"]))

    return {
        "answer": answer,
        "sources": sources,
    }