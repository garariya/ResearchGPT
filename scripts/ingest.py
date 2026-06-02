from src.pdf_processor import extract_text, extract_pdf_metadata
from src.chunker import chunk_text
from src.embedding import generate_embeddings
from src.vectordb import store_chunks

pdf_path = "data/pdfs/sample.pdf"

text = extract_text(pdf_path)

chunks = chunk_text(text)

embeddings = generate_embeddings(chunks)

pdf_md = extract_pdf_metadata(pdf_path)

store_chunks(
    chunks,
    embeddings,
    source_type="pdf",
    metadata={
        "title": pdf_md["title"],
        "authors": pdf_md["authors"],
        "year": pdf_md["year"],
        "source_name": pdf_md["title"],
        "pdf_filename": "sample.pdf",
    },
)

print(f"Stored {len(chunks)} chunks successfully!")