from src.pdf_processor import extract_text
from src.chunker import chunk_text
from src.embedding import generate_embeddings
from src.vectordb import store_chunks

pdf_path = "data/pdfs/sample.pdf"

text = extract_text(pdf_path)

chunks = chunk_text(text)

embeddings = generate_embeddings(chunks)

# Store with metadata so the CLI ingestion matches the Streamlit app behavior.
store_chunks(
    chunks,
    embeddings,
    source_type="pdf",
    source_name="sample.pdf",
)

print(f"Stored {len(chunks)} chunks successfully!")