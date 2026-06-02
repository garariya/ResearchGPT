from src.embedding import model
from src.vectordb import collection


def retrieve(query, k=5):

    query_embedding = model.encode(
        query
    ).tolist()

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=k,
        # Include metadatas so we can build citations downstream.
        include=["documents", "metadatas"],
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