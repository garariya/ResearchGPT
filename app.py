import streamlit as st
import os

from src.pdf_processor import extract_text
from src.chunker import chunk_text
from src.embedding import generate_embeddings
from src.vectordb import store_chunks
from src.rag_pipeline import answer_question
from src.arxiv_fetcher import search_papers, download_paper


st.title("📚 ResearchGPT - RAG AI Assistant")

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


# Ensure the sidebar is populated even on fresh sessions.
_bootstrap_library_from_disk()


# -----------------------------
# SIDEBAR: downloaded/uploaded papers
# -----------------------------
with st.sidebar:
    st.subheader("Your library")
    if st.button("Refresh library"):
        # Re-scan on demand (useful if files are added externally).
        _bootstrap_library_from_disk()

    if not st.session_state.library:
        st.caption("Downloaded/uploaded papers will appear here.")
    else:
        for idx, item in enumerate(st.session_state.library):
            source_type = item.get("source_type", "unknown")
            source_name = item.get("source_name", "Unknown")
            file_path = item.get("file_path")

            icon = "📄" if source_type == "pdf" else ("📚" if source_type == "arxiv" else "🔎")
            st.markdown(f"{icon} **{source_name}**")

            if file_path and os.path.exists(file_path):
                try:
                    with open(file_path, "rb") as f:
                        data = f.read()
                    st.download_button(
                        label="Download PDF",
                        data=data,
                        file_name=os.path.basename(file_path),
                        mime="application/pdf",
                        key=f"dl_{idx}",
                    )
                except Exception:
                    st.caption(f"Saved at: `{file_path}`")
            elif file_path:
                st.caption(f"Saved at: `{file_path}`")

            st.divider()


# -----------------------------
# MODE SELECTION
# -----------------------------
mode = st.radio(
    "Choose Mode",
    ["Upload PDF", "Search arXiv"]
)

# =========================================================
# 1. PDF UPLOAD MODE
# =========================================================
if mode == "Upload PDF":

    st.subheader("Upload your research paper (PDF)")

    uploaded_file = st.file_uploader(
        "Upload PDF",
        type=["pdf"]
    )

    if uploaded_file is not None:

        # Save file
        file_path = f"data/pdfs/{uploaded_file.name}"
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        st.success(f"{uploaded_file.name} uploaded successfully!")
        _add_to_library(
            source_type="pdf",
            source_name=uploaded_file.name,
            file_path=file_path,
        )

        # Process button (IMPORTANT to avoid re-processing)
        if st.button("Process & Store PDF"):

            text = extract_text(file_path)

            chunks = chunk_text(text)

            embeddings = generate_embeddings(chunks)

            # Store with metadata so we can cite sources later.
            store_chunks(
                chunks,
                embeddings,
                source_type="pdf",
                source_name=uploaded_file.name,
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

        if st.button(f"Download & Add Paper {i}"):

            pdf_path = f"data/pdfs/arxiv_{i}.pdf"

            try:
                with st.spinner("Downloading paper..."):
                    download_paper(
                        paper["pdf_url"],
                        pdf_path
                    )
                st.success("Downloaded!")
                _add_to_library(
                    source_type="arxiv",
                    source_name=paper["title"],
                    file_path=pdf_path,
                )

                # Auto ingest into RAG pipeline
                with st.spinner("Extracting text..."):
                    text = extract_text(pdf_path)

                with st.spinner("Chunking..."):
                    chunks = chunk_text(text)

                with st.spinner("Generating embeddings (this can take a bit)..."):
                    embeddings = generate_embeddings(chunks)

                # Store with arXiv paper title as the cite-able source_name.
                with st.spinner("Storing in vector DB..."):
                    store_chunks(
                        chunks,
                        embeddings,
                        source_type="arxiv",
                        source_name=paper["title"],
                    )

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
            # Render grouped, de-duplicated sources (Perplexity/Deep Research style).
            for src in sources:
                source_type = src.get("source_type", "unknown")
                source_name = src.get("source_name", "Unknown Source")
                chunk_indices = src.get("chunk_indices", [])

                if source_type == "pdf":
                    st.markdown(f"📄 **{source_name}**")
                    if chunk_indices:
                        chunks_label = ", ".join(str(i) for i in chunk_indices)
                        st.write(f"Chunks used: {chunks_label}")
                elif source_type == "arxiv":
                    st.markdown(f"📚 **{source_name}**")
                else:
                    st.markdown(f"🔎 **{source_name}**")
                    if chunk_indices:
                        chunks_label = ", ".join(str(i) for i in chunk_indices)
                        st.write(f"Chunks used: {chunks_label}")

    else:
        st.warning("Please enter a question")