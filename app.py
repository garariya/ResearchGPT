import streamlit as st

from src.pdf_processor import extract_text
from src.chunker import chunk_text
from src.embedding import generate_embeddings
from src.vectordb import store_chunks
from src.rag_pipeline import answer_question
from src.arxiv_fetcher import search_papers, download_paper


st.title("📚 ResearchGPT - RAG AI Assistant")


# -----------------------------
# MODE SELECTION
# -----------------------------
mode = st.radio(
    "Choose Mode",
    ["Upload PDF", "Search arXiv"]
)

# -----------------------------
# SESSION STATE (for arXiv papers)
# -----------------------------
if "papers" not in st.session_state:
    st.session_state.papers = []


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

        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        st.success(f"{uploaded_file.name} uploaded successfully!")

        # Process button (IMPORTANT to avoid re-processing)
        if st.button("Process & Store PDF"):

            text = extract_text(file_path)

            chunks = chunk_text(text)

            embeddings = generate_embeddings(chunks)

            store_chunks(chunks, embeddings)

            st.success(f"{len(chunks)} chunks stored in knowledge base!")


# =========================================================
# 2. ARXIV MODE
# =========================================================
elif mode == "Search arXiv":

    st.subheader("Search research papers from arXiv")

    query = st.text_input("Enter research topic")

    if st.button("Search Papers"):

        st.session_state.papers = search_papers(query)

    # Display results
    for i, paper in enumerate(st.session_state.papers):

        st.markdown(f"### {paper['title']}")
        st.write(paper["summary"][:300] + "...")

        if st.button(f"Download & Add Paper {i}"):

            pdf_path = f"data/pdfs/arxiv_{i}.pdf"

            download_paper(
                paper["pdf_url"],
                pdf_path
            )

            st.success("Downloaded!")

            # Auto ingest into RAG pipeline
            text = extract_text(pdf_path)

            chunks = chunk_text(text)

            embeddings = generate_embeddings(chunks)

            store_chunks(chunks, embeddings)

            st.success(
                "Paper added to knowledge base!"
            )


# =========================================================
# 3. QUESTION ANSWERING (COMMON FOR BOTH MODES)
# =========================================================
st.divider()

st.subheader("Ask Questions")

question = st.text_input("Enter your question")

if st.button("Ask"):

    if question:

        answer = answer_question(question)

        st.subheader("Answer")
        st.write(answer)

    else:
        st.warning("Please enter a question")