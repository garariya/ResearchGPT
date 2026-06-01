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