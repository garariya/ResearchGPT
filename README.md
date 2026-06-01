# 📚 ResearchGPT — RAG-based AI Research Assistant

ResearchGPT is an end-to-end **Retrieval-Augmented Generation (RAG)** system that allows users to upload research papers (PDFs) or fetch papers from arXiv, process them into embeddings, store them in a vector database, and ask intelligent questions using a Large Language Model (LLM) via Groq API.

---

## 🚀 Features

- 📄 Upload and process PDF research papers
- 🔍 Fetch papers directly from **arXiv API**
- ✂️ Intelligent text chunking for better retrieval
- 🧠 Embedding generation using SentenceTransformers
- 🗄️ Vector storage using **ChromaDB**
- 🤖 LLM-powered answering using **Groq (LLaMA 3)**
- 💬 Ask questions over your research corpus
- 🌐 Simple and interactive **Streamlit UI**

---

## 🏗️ Tech Stack

- Python 🐍
- Streamlit (Frontend UI)
- ChromaDB (Vector Database)
- SentenceTransformers (Embeddings)
- Groq API (LLM inference)
- PyMuPDF (PDF parsing)
- BeautifulSoup + Requests (arXiv scraping)

---

## ⚙️ Project Workflow

### 1. Data Ingestion
- Upload PDF OR fetch from arXiv
- Extract text using PyMuPDF

### 2. Text Processing
- Split document into overlapping chunks

### 3. Embedding Generation
- Convert chunks into vector embeddings using SentenceTransformer

### 4. Vector Storage
- Store embeddings in ChromaDB

### 5. Retrieval + QA
- Convert user query into embedding
- Retrieve top-k relevant chunks
- Pass context to Groq LLM
- Generate final answer

---

## 🖥️ How to Run Locally

### 1. Clone repository
```bash
git clone https://github.com/your-username/ResearchGPT.git
cd ResearchGPT