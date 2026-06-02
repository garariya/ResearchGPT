import chromadb
import uuid
import os
import sqlite3

DB_PATH = os.path.join(os.getcwd(), "chroma_db")

client = chromadb.PersistentClient(path=DB_PATH)

try:
    collection = client.get_or_create_collection(name="research_papers")
except sqlite3.OperationalError as e:
    # This typically happens when an existing persisted ChromaDB directory was
    # created by a different Chroma version and the SQLite schema doesn't match.
    # Example: "no such column: collections.topic"
    raise RuntimeError(
        "ChromaDB failed to open the persisted database.\n\n"
        "This is usually caused by a schema mismatch from an older/newer "
        "ChromaDB version.\n\n"
        "Fix:\n"
        f"1) Stop Streamlit\n"
        f"2) Delete the persisted DB folder: {DB_PATH}\n"
        "3) Restart the app and re-ingest your PDFs/arXiv papers\n\n"
        "If you need to keep your existing vector store, pin ChromaDB to the "
        "exact version used when it was created, or migrate the DB."
    ) from e

def store_chunks(chunks, embeddings, source_type, metadata):
    """
    Store chunks + embeddings in ChromaDB, along with per-chunk metadata.

    Added metadata enables professional-style citations (paper metadata + chunks)
    during retrieval and UI rendering.
    """
    if len(chunks) != len(embeddings):
        raise ValueError(
            f"chunks ({len(chunks)}) and embeddings ({len(embeddings)}) "
            "must have the same length"
        )

    title = metadata.get("title", "Unknown")
    authors = metadata.get("authors", "Unknown")
    year = metadata.get("year", "Unknown")
    source_name = metadata.get("source_name", title)
    pdf_filename = metadata.get("pdf_filename", "")
    document_id = metadata.get("document_id", "")

    ids = [
        str(uuid.uuid4())
        for _ in chunks
    ]

    # 1-based chunk_index is more natural for users (Chunk 1, Chunk 2, ...).
    metadatas = [
        {
            "document_id": document_id,
            "title": title,
            "authors": authors,
            "year": year,
            "source_type": source_type,
            "source_name": source_name,
            "pdf_filename": pdf_filename,
            "chunk_index": i + 1,
        }
        for i in range(len(chunks))
    ]

    collection.add(
        ids=ids,
        documents=chunks,
        embeddings=embeddings.tolist(),
        metadatas=metadatas,
    )