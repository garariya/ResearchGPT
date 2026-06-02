from src.pdf_processor import extract_text, extract_pdf_metadata
from src.chunker import chunk_text
from src.embedding import generate_embeddings
from src.vectordb import store_chunks
from src.paper_library import load_library, next_document_id, upsert_paper, save_library

pdf_path = "data/pdfs/sample.pdf"

text = extract_text(pdf_path)

chunks = chunk_text(text)

embeddings = generate_embeddings(chunks)

pdf_md = extract_pdf_metadata(pdf_path)
papers = load_library()
doc_id = next_document_id(papers)
papers = upsert_paper(
    papers,
    document_id=doc_id,
    title=pdf_md["title"],
    authors=pdf_md["authors"],
    year=pdf_md["year"],
    source_type="pdf",
    pdf_filename="sample.pdf",
    file_path=pdf_path,
    chunk_count=0,
)
save_library(papers)

store_chunks(
    chunks,
    embeddings,
    source_type="pdf",
    metadata={
        "document_id": doc_id,
        "title": pdf_md["title"],
        "authors": pdf_md["authors"],
        "year": pdf_md["year"],
        "source_name": pdf_md["title"],
        "pdf_filename": "sample.pdf",
    },
)

print(f"Stored {len(chunks)} chunks successfully!")