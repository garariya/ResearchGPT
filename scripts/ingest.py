from src.pdf_processor import extract_text
from src.chunker import chunk_text
from src.embedding import generate_embeddings
from src.vectordb import store_chunks

pdf_path = "data/pdfs/sample.pdf"

text = extract_text(pdf_path)

chunks = chunk_text(text)

embeddings = generate_embeddings(chunks)

store_chunks(chunks, embeddings)

print(f"Stored {len(chunks)} chunks successfully!")