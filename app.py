import streamlit as st
import os

from src.pdf_processor import extract_text, extract_pdf_metadata
from src.chunker import chunk_text
from src.embedding import generate_embeddings
from src.vectordb import store_chunks
from src.rag_pipeline import answer_question
from src.arxiv_fetcher import search_papers, download_paper
from src.vectordb import collection
from src.paper_library import (
    load_library,
    save_library,
    next_document_id,
    find_duplicate,
    upsert_paper,
    delete_paper,
)


st.set_page_config(
    page_title="ResearchGPT",
    layout="wide",
)

st.title("📚 ResearchGPT - RAG AI Assistant")

# --- UI styling: make 2 panels feel distinct and spaced out ---
st.markdown(
    """
<style>
  /* Increase perceived separation between columns */
  div[data-testid="stHorizontalBlock"] {
    column-gap: 2.25rem;
  }

  /* Card-like section styling */
  .rgpt-card {
    background: rgba(255, 255, 255, 0.85);
    border: 1px solid rgba(49, 51, 63, 0.12);
    border-radius: 14px;
    padding: 16px 16px 8px 16px;
    box-shadow: 0 1px 10px rgba(0,0,0,0.04);
  }

  /* Tighten internal spacing a bit so cards feel clean */
  .rgpt-card .stButton button {
    width: 100%;
  }
</style>
""",
    unsafe_allow_html=True,
)

# -----------------------------
# SESSION STATE (library + arXiv papers)
# -----------------------------
if "papers" not in st.session_state:
    st.session_state.papers = []

if "library" not in st.session_state:
    # Items look like:
    # {
    #   "source_type": "pdf" | "arxiv",
    #   "source_name": "filename.pdf" | "paper title",
    #   "file_path": "data/pdfs/....pdf",
    # }
    st.session_state.library = []

if "paper_library" not in st.session_state:
    # Persistent library loaded from disk.
    st.session_state.paper_library = load_library()

if "selected_paper_key" not in st.session_state:
    st.session_state.selected_paper_key = None

if "search_scope_document_ids" not in st.session_state:
    st.session_state.search_scope_document_ids = []


def _add_to_library(*, source_type, source_name, file_path):
    """
    Track downloaded/uploaded documents so users can see them in the sidebar.

    We dedupe by (source_type, source_name, file_path).
    """
    item = {
        "source_type": source_type,
        "source_name": source_name,
        "file_path": file_path,
    }
    key = (source_type, source_name, file_path)
    existing_keys = {
        (x.get("source_type"), x.get("source_name"), x.get("file_path"))
        for x in st.session_state.library
    }
    if key not in existing_keys:
        st.session_state.library.append(item)


def _paper_key(paper):
    # Stable dedupe key across sessions.
    return paper.get("document_id")


def _upsert_paper_library(paper):
    """
    Insert paper-level metadata into session library (deduped).
    """
    st.session_state.paper_library = upsert_paper(
        st.session_state.paper_library,
        document_id=paper["document_id"],
        title=paper["title"],
        authors=paper["authors"],
        year=paper["year"],
        source_type=paper["source_type"],
        pdf_filename=paper["pdf_filename"],
        file_path=paper["file_path"],
        chunk_count=paper.get("chunk_count"),
    )
    save_library(st.session_state.paper_library)
    st.session_state.selected_paper_key = paper["document_id"]


def _bootstrap_library_from_disk():
    """
    Populate sidebar library from already-downloaded PDFs on disk.

    This makes the "library" visible even after Streamlit restarts (session state
    resets) and avoids confusion when files exist under data/pdfs/.
    """
    pdf_dir = os.path.join("data", "pdfs")
    if not os.path.isdir(pdf_dir):
        return

    try:
        filenames = sorted(
            [f for f in os.listdir(pdf_dir) if f.lower().endswith(".pdf")]
        )
    except Exception:
        return

    # Start with persisted library.
    st.session_state.paper_library = load_library()

    for fname in filenames:
        file_path = os.path.join(pdf_dir, fname)
        # We can't reliably recover the arXiv title from the PDF without extra
        # parsing, so we show the filename as the label.
        source_type = "arxiv" if fname.startswith("arxiv_") else "pdf"
        _add_to_library(
            source_type=source_type,
            source_name=fname,
            file_path=file_path,
        )

        # If a PDF exists on disk but not in the persisted library, add it once.
        dup = find_duplicate(st.session_state.paper_library, title=fname, pdf_filename=fname)
        if dup is None:
            doc_id = next_document_id(st.session_state.paper_library)
            if source_type == "pdf":
                md = extract_pdf_metadata(file_path)
                _upsert_paper_library(
                    {
                        "document_id": doc_id,
                        "title": md["title"],
                        "authors": md["authors"],
                        "year": md["year"],
                        "source_type": "pdf",
                        "pdf_filename": fname,
                        "file_path": file_path,
                        "chunk_count": 0,
                    }
                )
            else:
                _upsert_paper_library(
                    {
                        "document_id": doc_id,
                        "title": fname,
                        "authors": "Unknown",
                        "year": "Unknown",
                        "source_type": "arxiv",
                        "pdf_filename": fname,
                        "file_path": file_path,
                        "chunk_count": 0,
                    }
                )


# Ensure the sidebar is populated even on fresh sessions.
_bootstrap_library_from_disk()


# -----------------------------
# MODE SELECTION
# -----------------------------
mode = st.radio("Choose Mode", ["Upload PDF", "Search arXiv"])


# =========================================================
# DASHBOARD LAYOUT
# =========================================================
left_col, main_col = st.columns([1, 4], gap="large")


with left_col:
    st.markdown('<div class="rgpt-card">', unsafe_allow_html=True)
    st.subheader("📚 Knowledge Base")
    if st.button("Refresh library"):
        _bootstrap_library_from_disk()

    if not st.session_state.paper_library:
        st.caption("Upload or download papers to build your library.")
    else:
        # --- Knowledge base statistics ---
        total_papers = len(st.session_state.paper_library)
        total_chunks = sum(int(p.get("chunk_count") or 0) for p in st.session_state.paper_library)
        all_authors = []
        years = []
        for p in st.session_state.paper_library:
            a = (p.get("authors") or "").strip()
            if a and a != "Unknown":
                all_authors.extend([x.strip() for x in a.split(",") if x.strip()])
            y = (p.get("year") or "").strip()
            if y.isdigit():
                years.append(int(y))

        st.caption(f"Total Papers: **{total_papers}**")
        st.caption(f"Total Chunks: **{total_chunks}**")
        st.caption(f"Total Authors: **{len(set(all_authors))}**" if all_authors else "Total Authors: **0**")
        if years:
            st.caption(f"Years Covered: **{min(years)}–{max(years)}**")
        else:
            st.caption("Years Covered: **Unknown**")

        st.divider()

        for i, paper in enumerate(st.session_state.paper_library):
            title = paper.get("title", "Untitled")
            year = paper.get("year", "Unknown")
            source_type = paper.get("source_type", "unknown")
            doc_id = paper.get("document_id")
            chunk_count = int(paper.get("chunk_count") or 0)

            icon = "📄" if source_type == "pdf" else ("📚" if source_type == "arxiv" else "🔎")
            label = f"{icon} {title} ({year}) — {chunk_count} chunks"

            with st.expander(label, expanded=(st.session_state.selected_paper_key == doc_id)):
                st.caption(paper.get("authors", "Unknown"))
                st.caption(f"Document ID: `{doc_id}`")
                st.caption(f"Uploaded: {paper.get('upload_date', 'Unknown')}")

                if st.button("Select", key=f"select_{i}"):
                    st.session_state.selected_paper_key = doc_id
                    # One-click single-paper QA scope.
                    st.session_state.search_scope_document_ids = [doc_id]

                file_path = paper.get("file_path")
                if file_path and os.path.exists(file_path):
                    with open(file_path, "rb") as f:
                        data = f.read()
                    st.download_button(
                        label="Download PDF",
                        data=data,
                        file_name=os.path.basename(file_path),
                        mime="application/pdf",
                        key=f"download_{i}",
                    )

                if st.button("🗑 Remove Paper", key=f"delete_{i}"):
                    try:
                        collection.delete(where={"document_id": doc_id})
                    except Exception as e:
                        st.error(f"Failed to delete from vector DB: {e}")
                    st.session_state.paper_library = delete_paper(st.session_state.paper_library, doc_id)
                    save_library(st.session_state.paper_library)
                    st.success("Paper removed.")
    st.markdown("</div>", unsafe_allow_html=True)


def _get_selected_paper():
    if not st.session_state.paper_library:
        return None
    if st.session_state.selected_paper_key is None:
        return st.session_state.paper_library[-1]
    for p in st.session_state.paper_library:
        if p.get("document_id") == st.session_state.selected_paper_key:
            return p
    return st.session_state.paper_library[-1]


# =========================================================
# 1. PDF UPLOAD MODE
# =========================================================
with main_col:
    st.markdown('<div class="rgpt-card">', unsafe_allow_html=True)
    if mode == "Upload PDF":

        st.subheader("Upload your research paper (PDF)")

        uploaded_file = st.file_uploader("Upload PDF", type=["pdf"])

        if uploaded_file is not None:

            # Save file
            file_path = f"data/pdfs/{uploaded_file.name}"
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            st.success(f"{uploaded_file.name} uploaded successfully!")
            _add_to_library(source_type="pdf", source_name=uploaded_file.name, file_path=file_path)

            pdf_md = extract_pdf_metadata(file_path)
            existing = find_duplicate(
                st.session_state.paper_library,
                title=pdf_md["title"],
                pdf_filename=uploaded_file.name,
            )
            if existing is not None:
                st.warning("This paper already exists in the knowledge base.")
                doc_id = existing["document_id"]
            else:
                doc_id = next_document_id(st.session_state.paper_library)
                _upsert_paper_library(
                    {
                        "document_id": doc_id,
                        "title": pdf_md["title"],
                        "authors": pdf_md["authors"],
                        "year": pdf_md["year"],
                        "source_type": "pdf",
                        "pdf_filename": uploaded_file.name,
                        "file_path": file_path,
                        "chunk_count": 0,
                    }
                )

            # Process button (IMPORTANT to avoid re-processing)
            if st.button("Process & Store PDF"):
                if existing is not None and int(existing.get("chunk_count") or 0) > 0:
                    st.warning("Skipping ingestion: already indexed.")
                else:
                    text = extract_text(file_path)

                    chunks = chunk_text(text)

                    embeddings = generate_embeddings(chunks)

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
                            "pdf_filename": uploaded_file.name,
                        },
                    )

                    _upsert_paper_library(
                        {
                            "document_id": doc_id,
                            "title": pdf_md["title"],
                            "authors": pdf_md["authors"],
                            "year": pdf_md["year"],
                            "source_type": "pdf",
                            "pdf_filename": uploaded_file.name,
                            "file_path": file_path,
                            "chunk_count": len(chunks),
                        }
                    )
                    st.success(f"{len(chunks)} chunks stored in knowledge base!")


# =========================================================
# 2. ARXIV MODE
# =========================================================
    elif mode == "Search arXiv":

        st.subheader("Search research papers from arXiv")

        query = st.text_input("Enter research topic")

        if st.button("Search Papers"):
            if not query.strip():
                st.warning("Please enter a search query.")
            else:
                try:
                    with st.spinner("Searching arXiv..."):
                        st.session_state.papers = search_papers(query)
                except Exception as e:
                    st.session_state.papers = []
                    st.error(f"arXiv search failed: {e}")

        # Display results
        for i, paper in enumerate(st.session_state.papers):

            st.markdown(f"### {paper['title']}")
            st.write(paper["summary"][:300] + "...")
            st.caption(f"Authors: {paper.get('authors', 'Unknown')} | Year: {paper.get('year', 'Unknown')}")

            if st.button(f"Download & Add Paper {i}"):

                pdf_path = f"data/pdfs/arxiv_{i}.pdf"

                try:
                    with st.spinner("Downloading paper..."):
                        download_paper(paper["pdf_url"], pdf_path)
                    st.success("Downloaded!")
                    _add_to_library(source_type="arxiv", source_name=paper["title"], file_path=pdf_path)

                    paper_obj = {
                        "title": paper.get("title", "No Title"),
                        "authors": paper.get("authors", "Unknown"),
                        "year": paper.get("year", "Unknown"),
                        "source_type": "arxiv",
                        "pdf_filename": os.path.basename(pdf_path),
                        "file_path": pdf_path,
                        "chunk_count": 0,
                    }

                    existing = find_duplicate(
                        st.session_state.paper_library,
                        title=paper_obj["title"],
                        pdf_filename=paper_obj["pdf_filename"],
                    )
                    if existing is not None:
                        st.warning("This paper already exists in the knowledge base.")
                        doc_id = existing["document_id"]
                    else:
                        doc_id = next_document_id(st.session_state.paper_library)
                        _upsert_paper_library({**paper_obj, "document_id": doc_id})

                    # Auto ingest into RAG pipeline
                    with st.spinner("Extracting text..."):
                        text = extract_text(pdf_path)

                    with st.spinner("Chunking..."):
                        chunks = chunk_text(text)

                    with st.spinner("Generating embeddings (this can take a bit)..."):
                        embeddings = generate_embeddings(chunks)

                    with st.spinner("Storing in vector DB..."):
                        store_chunks(
                            chunks,
                            embeddings,
                            source_type="arxiv",
                            metadata={
                                "document_id": doc_id,
                                "title": paper_obj["title"],
                                "authors": paper_obj["authors"],
                                "year": paper_obj["year"],
                                "source_name": paper_obj["title"],
                                "pdf_filename": paper_obj["pdf_filename"],
                            },
                        )

                    _upsert_paper_library({**paper_obj, "document_id": doc_id, "chunk_count": len(chunks)})
                    st.success("Paper added to knowledge base!")
                except Exception as e:
                    st.error(f"Failed to ingest paper: {e}")


# =========================================================
# 3. QUESTION ANSWERING (COMMON FOR BOTH MODES)
# =========================================================
    st.divider()

    st.subheader("Ask Questions")
    scope_options = {
        f"{p.get('title','Untitled')} ({p.get('year','Unknown')}) [{p.get('document_id')}]": p.get("document_id")
        for p in st.session_state.paper_library
        if p.get("document_id")
    }
    # Keep multiselect in sync with the current scope set by the Select button.
    default_selected_labels = [
        label for label, did in scope_options.items()
        if did in st.session_state.search_scope_document_ids
    ]
    selected_labels = st.multiselect(
        "Search scope (optional)",
        options=list(scope_options.keys()),
        default=default_selected_labels,
    )
    st.session_state.search_scope_document_ids = [scope_options[l] for l in selected_labels]

    question = st.text_input("Enter your question")

    if st.button("Ask"):
        if question:
            doc_ids = st.session_state.search_scope_document_ids or None
            result = answer_question(question, document_ids=doc_ids)

            st.subheader("Answer")
            st.write(result["answer"])

            st.subheader("Sources")
            sources = result.get("sources", [])

            if not sources:
                st.write("No sources found.")
            else:
                for src in sources:
                    title = src.get("title") or src.get("source_name", "Unknown")
                    authors = src.get("authors", "Unknown")
                    year = src.get("year", "Unknown")
                    stype = src.get("source_type", "unknown")
                    chunk_indices = src.get("chunk_indices", [])

                    icon = "📄" if stype == "pdf" else ("📚" if stype == "arxiv" else "🔎")
                    st.markdown(f"{icon} **{title}**")
                    st.write(f"Authors: {authors}")
                    st.write(f"Year: {year}")
                    if stype == "pdf" and chunk_indices:
                        st.write(f"Chunks: {', '.join(str(i) for i in chunk_indices)}")

        else:
            st.warning("Please enter a question")
    st.markdown("</div>", unsafe_allow_html=True)