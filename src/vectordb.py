import chromadb
import uuid

client = chromadb.PersistentClient(path="chroma_db")

collection  = client.get_or_create_collection(name="research_papers")

def store_chunks(chunks, embeddings):

    ids = [
        str(uuid.uuid4())
        for _ in chunks
    ]

    collection.add(
        ids=ids,
        documents=chunks,
        embeddings=embeddings.tolist()
    )