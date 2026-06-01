import chromadb
import uuid
import os

DB_PATH = os.path.join(os.getcwd(), "chroma_db")

client = chromadb.PersistentClient(path=DB_PATH)

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