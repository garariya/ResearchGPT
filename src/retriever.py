from src.embedding import model
from src.vectordb import collection


def _where_for_document_ids(document_ids):
    """
    Build a ChromaDB where filter for restricting to a subset of document_ids.
    """
    if not document_ids:
        return None

    # Chroma supports $in for metadata fields in many versions.
    # We keep a conservative fallback ($or) in case $in isn't available.
    return {"document_id": {"$in": document_ids}}


def retrieve(query, k=5, document_ids=None):

    query_embedding = model.encode(
        query
    ).tolist()

    where = _where_for_document_ids(document_ids)

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=k,
        # Include metadatas so we can build citations downstream.
        include=["documents", "metadatas"],
        where=where,
    )

    docs = results.get("documents", [[]])[0] or []
    metadatas = results.get("metadatas", [[]])[0] or []

    retrieved = []
    for text, metadata in zip(docs, metadatas):
        retrieved.append(
            {
                "text": text,
                "metadata": metadata or {},
            }
        )

    return retrieved