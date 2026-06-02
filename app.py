import streamlit as st
import os

from src.pdf_processor import extract_text, extract_pdf_metadata
from src.chunker import chunk_text
from src.embedding import generate_embeddings
from src.vectordb import store_chunks
from src.rag_pipeline import answer_question
from src.arxiv_fetcher import search_papers, download_paper


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
    # Paper-level metadata library (deduped).
    # Items look like:
    # {
    #   "title": "...",
    #   "authors": "...",
    #   "year": "...",
    #   "source_type": "pdf" | "arxiv",
    #   "source_name": "...",
    #   "pdf_filename": "...",
    #   "file_path": "...",
    #   "num_chunks": int | None,
    # }
    st.session_state.paper_library = []

if "selected_paper_key" not in st.session_state:
    st.session_state.selected_paper_key = None


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
    return (paper.get("source_type"), paper.get("source_name"), paper.get("pdf_filename"))


def _upsert_paper_library(paper):
    """
    Insert paper-level metadata into session library (deduped).
    """
    key = _paper_key(paper)
    existing = {_paper_key(p): i for i, p in enumerate(st.session_state.paper_library)}
    if key in existing:
        # Merge fields (keep latest values like num_chunks).
        idx = existing[key]
        st.session_state.paper_library[idx] = {**st.session_state.paper_library[idx], **paper}
    else:
        st.session_state.paper_library.append(paper)

    # Default selection: most recent paper.
    st.session_state.selected_paper_key = key


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

        # Best-effort: create a corresponding paper_library entry so the left panel
        # doesn't look empty on fresh sessions.
        if source_type == "pdf":
            md = extract_pdf_metadata(file_path)
            _upsert_paper_library(
                {
                    "title": md["title"],
                    "authors": md["authors"],
                    "year": md["year"],
                    "source_type": "pdf",
                    "source_name": md["title"],
                    "pdf_filename": fname,
                    "file_path": file_path,
                    "num_chunks": None,
                }
            )
        else:
            _upsert_paper_library(
                {
                    "title": fname,
                    "authors": "Unknown",
                    "year": "Unknown",
                    "source_type": "arxiv",
                    "source_name": fname,
                    "pdf_filename": fname,
                    "file_path": file_path,
                    "num_chunks": None,
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
    st.subheader("📚 Paper Library")
    if st.button("Refresh library"):
        _bootstrap_library_from_disk()

    if not st.session_state.paper_library:
        st.caption("Upload or download papers to build your library.")
    else:
        for i, paper in enumerate(st.session_state.paper_library):
            title = paper.get("title", "Untitled")
            year = paper.get("year", "Unknown")
            source_type = paper.get("source_type", "unknown")
            key = _paper_key(paper)

            icon = "📄" if source_type == "pdf" else ("📚" if source_type == "arxiv" else "🔎")
            label = f"{icon} {title} ({year})"

            with st.expander(label, expanded=(st.session_state.selected_paper_key == key)):
                st.caption(paper.get("authors", "Unknown"))
                if st.button("Select", key=f"select_{i}"):
                    st.session_state.selected_paper_key = key

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
    st.markdown("</div>", unsafe_allow_html=True)


def _get_selected_paper():
    if not st.session_state.paper_library:
        return None
    if st.session_state.selected_paper_key is None:
        return st.session_state.paper_library[-1]
    for p in st.session_state.paper_library:
        if _paper_key(p) == st.session_state.selected_paper_key:
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
            paper_obj = {
                "title": pdf_md["title"],
                "authors": pdf_md["authors"],
                "year": pdf_md["year"],
                "source_type": "pdf",
                "source_name": pdf_md["title"],
                "pdf_filename": uploaded_file.name,
                "file_path": file_path,
                "num_chunks": None,
            }
            _upsert_paper_library(paper_obj)

            # Process button (IMPORTANT to avoid re-processing)
            if st.button("Process & Store PDF"):

                text = extract_text(file_path)

                chunks = chunk_text(text)

                embeddings = generate_embeddings(chunks)

                store_chunks(
                    chunks,
                    embeddings,
                    source_type="pdf",
                    metadata={
                        "title": pdf_md["title"],
                        "authors": pdf_md["authors"],
                        "year": pdf_md["year"],
                        "source_name": pdf_md["title"],
                        "pdf_filename": uploaded_file.name,
                    },
                )

                _upsert_paper_library({**paper_obj, "num_chunks": len(chunks)})
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
                        "source_name": paper.get("title", "No Title"),
                        "pdf_filename": os.path.basename(pdf_path),
                        "file_path": pdf_path,
                        "num_chunks": None,
                    }
                    _upsert_paper_library(paper_obj)

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
                                "title": paper_obj["title"],
                                "authors": paper_obj["authors"],
                                "year": paper_obj["year"],
                                "source_name": paper_obj["source_name"],
                                "pdf_filename": paper_obj["pdf_filename"],
                            },
                        )

                    _upsert_paper_library({**paper_obj, "num_chunks": len(chunks)})
                    st.success("Paper added to knowledge base!")
                except Exception as e:
                    st.error(f"Failed to ingest paper: {e}")


# =========================================================
# 3. QUESTION ANSWERING (COMMON FOR BOTH MODES)
# =========================================================
    st.divider()

    st.subheader("Ask Questions")
    question = st.text_input("Enter your question")

    if st.button("Ask"):
        if question:
            result = answer_question(question)

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