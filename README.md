# ResearchGPT - Multi-PDF RAG Research Platform

ResearchGPT is a Streamlit-based research assistant that turns PDFs and arXiv papers into a searchable, persistent knowledge base.
It supports multi-document retrieval, paper-level metadata, citations, and corpus management on top of a standard RAG pipeline.

---

## What it does

- Ingest research papers from:
  - local PDF upload
  - arXiv search + download
- Extract text + metadata (title, authors, year)
- Chunk and embed content with Sentence Transformers
- Store chunks in ChromaDB with document metadata
- Answer questions using Groq LLM with context-only prompting
- Show answer sources grouped by paper
- Manage a persistent paper library (document IDs, chunk counts, deletion)

---

## Tech stack

- Streamlit
- ChromaDB
- Sentence Transformers (`all-MiniLM-L6-v2`)
- Groq API (`llama-3.3-70b-versatile`)
- PyMuPDF
- arXiv API (Atom feed)

---

## Core architecture

```text
PDF/arXiv
  -> metadata extraction + text extraction
  -> chunking
  -> embeddings
  -> ChromaDB (documents + embeddings + metadata)
  -> retrieval (top-k, optional doc filter)
  -> Groq LLM
  -> answer + paper-level citations
```

---

## Multi-PDF knowledge base features

### 1) Persistent paper library

- Stored in `data/paper_library.json`
- Rebuilt on app startup
- Each paper has:
  - `document_id` (e.g. `doc_001`)
  - `title`, `authors`, `year`
  - `source_type`
  - `pdf_filename`, `file_path`
  - `chunk_count`
  - `upload_date`

### 2) Rich metadata in Chroma

Each chunk stores metadata such as:
- `document_id`
- `title`
- `authors`
- `year`
- `source_type`
- `source_name`
- `pdf_filename`
- `chunk_index`

### 3) Duplicate prevention

Before ingestion, the app checks for existing papers by:
- title OR
- PDF filename

If found, it skips duplicate indexing.

### 4) Cross-document retrieval

- Default behavior: retrieval searches across the full collection
- Optional scope filtering via `Search scope` multiselect (document IDs)
- Sidebar **Select** button sets one-click single-paper scope

### 5) Paper management

- Sidebar knowledge base view with stats:
  - total papers
  - total chunks
  - total authors
  - years covered
- Per-paper actions:
  - Select
  - Download PDF
  - Remove paper (deletes all associated chunks from Chroma)

---

## Repository structure (key files)

```text
app.py
src/
  arxiv_fetcher.py
  chunker.py
  embedding.py
  llm.py
  paper_library.py
  pdf_processor.py
  rag_pipeline.py
  retriever.py
  vectordb.py
scripts/
  ingest.py
  test_rag.py
data/
  pdfs/
  paper_library.json
chroma_db/
```

---

## Setup

### 1) Install dependencies

```bash
pip install -r requirements.txt
```

### 2) Configure environment

Create `.env` in project root:

```env
GROQ_API_KEY=your_api_key_here
```

### 3) Run app

```bash
streamlit run app.py
```

---

## How to use

1. Add papers (Upload PDF or Search arXiv and Download & Add)
2. Confirm papers appear in **Knowledge Base**
3. Ask questions:
   - leave scope empty = search all papers
   - select one/more papers = filtered retrieval
4. Review **Sources** under answers for paper-level attribution

---

## Reset / clear knowledge base

From project root:

```bash
rm -f data/paper_library.json
rm -f data/pdfs/*.pdf
rm -rf chroma_db
```

Then restart:

```bash
streamlit run app.py
```

---

## Notes

- `paper_library.json` is app data, not source code.
  If you do not want local paper history in git, add it to `.gitignore`.
- If you hit Chroma schema mismatch errors after version changes, clear `chroma_db/` and re-ingest.
# ResearchGPT - Multi-PDF RAG Research Platform

ResearchGPT is a Streamlit-based research assistant that turns PDFs and arXiv papers into a searchable, persistent knowledge base.
It supports multi-document retrieval, paper-level metadata, citations, and corpus management on top of a standard RAG pipeline.

---

## What it does

- Ingest research papers from:
  - local PDF upload
  - arXiv search + download
- Extract text + metadata (title, authors, year)
- Chunk and embed content with Sentence Transformers
- Store chunks in ChromaDB with document metadata
- Answer questions using Groq LLM with context-only prompting
- Show answer sources grouped by paper
- Manage a persistent paper library (document IDs, chunk counts, deletion)

---

## Tech stack

- Streamlit
- ChromaDB
- Sentence Transformers (`all-MiniLM-L6-v2`)
- Groq API (`llama-3.3-70b-versatile`)
- PyMuPDF
- arXiv API (Atom feed)

---

## Core architecture

```text
PDF/arXiv
  -> metadata extraction + text extraction
  -> chunking
  -> embeddings
  -> ChromaDB (documents + embeddings + metadata)
  -> retrieval (top-k, optional doc filter)
  -> Groq LLM
  -> answer + paper-level citations
```

---

## Multi-PDF knowledge base features

### 1) Persistent paper library

- Stored in `data/paper_library.json`
- Rebuilt on app startup
- Each paper has:
  - `document_id` (e.g. `doc_001`)
  - `title`, `authors`, `year`
  - `source_type`
  - `pdf_filename`, `file_path`
  - `chunk_count`
  - `upload_date`

### 2) Rich metadata in Chroma

Each chunk stores metadata such as:
- `document_id`
- `title`
- `authors`
- `year`
- `source_type`
- `source_name`
- `pdf_filename`
- `chunk_index`

### 3) Duplicate prevention

Before ingestion, the app checks for existing papers by:
- title OR
- PDF filename

If found, it skips duplicate indexing.

### 4) Cross-document retrieval

- Default behavior: retrieval searches across the full collection
- Optional scope filtering via `Search scope` multiselect (document IDs)
- Sidebar **Select** button sets one-click single-paper scope

### 5) Paper management

- Sidebar knowledge base view with stats:
  - total papers
  - total chunks
  - total authors
  - years covered
- Per-paper actions:
  - Select
  - Download PDF
  - Remove paper (deletes all associated chunks from Chroma)

---

## Repository structure (key files)

```text
app.py
src/
  arxiv_fetcher.py
  chunker.py
  embedding.py
  llm.py
  paper_library.py
  pdf_processor.py
  rag_pipeline.py
  retriever.py
  vectordb.py
scripts/
  ingest.py
  test_rag.py
data/
  pdfs/
  paper_library.json
chroma_db/
```

---

## Setup

### 1) Install dependencies

```bash
pip install -r requirements.txt
```

### 2) Configure environment

Create `.env` in project root:

```env
GROQ_API_KEY=your_api_key_here
```

### 3) Run app

```bash
streamlit run app.py
```

---

## How to use

1. Add papers (Upload PDF or Search arXiv and Download & Add)
2. Confirm papers appear in **Knowledge Base**
3. Ask questions:
   - leave scope empty = search all papers
   - select one/more papers = filtered retrieval
4. Review **Sources** under answers for paper-level attribution

---

## Reset / clear knowledge base

From project root:

```bash
rm -f data/paper_library.json
rm -f data/pdfs/*.pdf
rm -rf chroma_db
```

Then restart:

```bash
streamlit run app.py
```

---

## Notes

- `paper_library.json` is app data, not source code.
  If you do not want local paper history in git, add it to `.gitignore`.
- If you hit Chroma schema mismatch errors after version changes, clear `chroma_db/` and re-ingest.
# ResearchGPT - Multi-PDF RAG Research Platform

ResearchGPT is a Streamlit-based research assistant that turns PDFs and arXiv papers into a searchable, persistent knowledge base.
It supports multi-document retrieval, paper-level metadata, citations, and corpus management on top of a standard RAG pipeline.

---

## What it does

- Ingest research papers from:
  - local PDF upload
  - arXiv search + download
- Extract text + metadata (title, authors, year)
- Chunk and embed content with Sentence Transformers
- Store chunks in ChromaDB with document metadata
- Answer questions using Groq LLM with context-only prompting
- Show answer sources grouped by paper
- Manage a persistent paper library (document IDs, chunk counts, deletion)

---

## Tech stack

- Streamlit
- ChromaDB
- Sentence Transformers (`all-MiniLM-L6-v2`)
- Groq API (`llama-3.3-70b-versatile`)
- PyMuPDF
- arXiv API (Atom feed)

---

## Core architecture

```text
PDF/arXiv
  -> metadata extraction + text extraction
  -> chunking
  -> embeddings
  -> ChromaDB (documents + embeddings + metadata)
  -> retrieval (top-k, optional doc filter)
  -> Groq LLM
  -> answer + paper-level citations
```

---

## Multi-PDF knowledge base features

### 1) Persistent paper library

- Stored in `data/paper_library.json`
- Rebuilt on app startup
- Each paper has:
  - `document_id` (e.g. `doc_001`)
  - `title`, `authors`, `year`
  - `source_type`
  - `pdf_filename`, `file_path`
  - `chunk_count`
  - `upload_date`

### 2) Rich metadata in Chroma

Each chunk stores metadata such as:
- `document_id`
- `title`
- `authors`
- `year`
- `source_type`
- `source_name`
- `pdf_filename`
- `chunk_index`

### 3) Duplicate prevention

Before ingestion, the app checks for existing papers by:
- title OR
- PDF filename

If found, it skips duplicate indexing.

### 4) Cross-document retrieval

- Default behavior: retrieval searches across the full collection
- Optional scope filtering via `Search scope` multiselect (document IDs)
- Sidebar **Select** button sets one-click single-paper scope

### 5) Paper management

- Sidebar knowledge base view with stats:
  - total papers
  - total chunks
  - total authors
  - years covered
- Per-paper actions:
  - Select
  - Download PDF
  - Remove paper (deletes all associated chunks from Chroma)

---

## Repository structure (key files)

```text
app.py
src/
  arxiv_fetcher.py
  chunker.py
  embedding.py
  llm.py
  paper_library.py
  pdf_processor.py
  rag_pipeline.py
  retriever.py
  vectordb.py
scripts/
  ingest.py
  test_rag.py
data/
  pdfs/
  paper_library.json
chroma_db/
```

---

## Setup

### 1) Install dependencies

```bash
pip install -r requirements.txt
```

### 2) Configure environment

Create `.env` in project root:

```env
GROQ_API_KEY=your_api_key_here
```

### 3) Run app

```bash
streamlit run app.py
```

---

## How to use

1. Add papers (Upload PDF or Search arXiv and Download & Add)
2. Confirm papers appear in **Knowledge Base**
3. Ask questions:
   - leave scope empty = search all papers
   - select one/more papers = filtered retrieval
4. Review **Sources** under answers for paper-level attribution

---

## Reset / clear knowledge base

From project root:

```bash
rm -f data/paper_library.json
rm -f data/pdfs/*.pdf
rm -rf chroma_db
```

Then restart:

```bash
streamlit run app.py
```

---

## Notes

- `paper_library.json` is app data, not source code.
  If you do not want local paper history in git, add it to `.gitignore`.
- If you hit Chroma schema mismatch errors after version changes, clear `chroma_db/` and re-ingest.
# ResearchGPT — RAG-based AI Research Assistant

ResearchGPT is an end-to-end Retrieval-Augmented Generation (RAG) system that allows users to upload research papers (PDFs) or fetch papers from arXiv, process them into embeddings, store them in a vector database, and ask intelligent questions using a Large Language Model (LLM) via Groq API.

---

## Features

- Upload and process PDF research papers  
- Fetch papers from arXiv API  
- Intelligent text chunking with overlap  
- Embeddings using SentenceTransformers  
- Vector storage using ChromaDB  
- LLM-based QA using Groq (LLaMA 3)  
- Interactive Streamlit UI  

---

## Architecture

### System Flow

```text id="arch2"
                ┌────────────────────┐
                │   User (Streamlit) │
                └─────────┬──────────┘
                          │
        ┌─────────────────┴─────────────────┐
        │                                   │
┌───────▼────────┐               ┌──────────▼──────────┐
│ Upload PDF     │               │   arXiv Fetcher     │
│ (PyMuPDF)      │               │ (arXiv API)         │
└───────┬────────┘               └──────────┬──────────┘
        │                                   │
        └──────────────┬────────────────────┘
                       │
              ┌────────▼─────────┐
              │ Text Extraction   │
              └────────┬─────────┘
                       │
              ┌────────▼─────────┐
              │ Chunking Engine   │
              │ (overlap chunks)  │
              └────────┬─────────┘
                       │
              ┌────────▼─────────┐
              │ Embedding Model   │
              │ (SentenceTrans.)  │
              └────────┬─────────┘
                       │
              ┌────────▼─────────┐
              │  ChromaDB Vector  │
              │     Storage       │
              └────────┬─────────┘
                       │
        ┌──────────────▼──────────────┐
        │     Retriever (Top-K)       │
        └──────────────┬──────────────┘
                       │
              ┌────────▼─────────┐
              │   Groq LLM       │
              │ (LLaMA 3 Model)  │
              └────────┬─────────┘
                       │
              ┌────────▼─────────┐
              │ Final Answer UI   │
              └───────────────────┘