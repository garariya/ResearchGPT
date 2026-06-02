import json
import os
from datetime import datetime, timezone


LIBRARY_PATH = os.path.join("data", "paper_library.json")


def _utc_now_iso():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def load_library(path: str = LIBRARY_PATH):
    """
    Load the persistent paper library.

    Returns a list of paper dicts:
    {
      "document_id": "doc_001",
      "title": "...",
      "authors": "...",
      "year": "...",
      "source_type": "pdf" | "arxiv",
      "pdf_filename": "...",
      "file_path": "...",
      "chunk_count": int,
      "upload_date": "ISO8601",
    }
    """
    if not os.path.exists(path):
        return []

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
    except Exception:
        return []

    return []


def save_library(papers, path: str = LIBRARY_PATH):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(papers, f, indent=2, ensure_ascii=False)


def next_document_id(papers) -> str:
    """
    Generate the next doc id as doc_###.
    """
    max_n = 0
    for p in papers:
        doc_id = (p.get("document_id") or "").strip()
        if doc_id.startswith("doc_"):
            suffix = doc_id.replace("doc_", "")
            if suffix.isdigit():
                max_n = max(max_n, int(suffix))
    return f"doc_{max_n + 1:03d}"


def normalize(s: str) -> str:
    return (s or "").strip().lower()


def find_duplicate(papers, *, title: str, pdf_filename: str):
    """
    Return existing paper dict if we already have it.

    Duplicate criteria: title OR pdf_filename match (case-insensitive).
    """
    t = normalize(title)
    f = normalize(pdf_filename)

    for p in papers:
        if t and normalize(p.get("title")) == t:
            return p
        if f and normalize(p.get("pdf_filename")) == f:
            return p
    return None


def upsert_paper(
    papers,
    *,
    document_id: str,
    title: str,
    authors: str,
    year: str,
    source_type: str,
    pdf_filename: str,
    file_path: str,
    chunk_count: int | None,
):
    """
    Insert/update a paper entry (in-memory).
    """
    now = _utc_now_iso()
    for i, p in enumerate(papers):
        if p.get("document_id") == document_id:
            papers[i] = {
                **p,
                "title": title,
                "authors": authors,
                "year": year,
                "source_type": source_type,
                "pdf_filename": pdf_filename,
                "file_path": file_path,
                "chunk_count": chunk_count if chunk_count is not None else p.get("chunk_count"),
                "upload_date": p.get("upload_date") or now,
            }
            return papers

    papers.append(
        {
            "document_id": document_id,
            "title": title,
            "authors": authors,
            "year": year,
            "source_type": source_type,
            "pdf_filename": pdf_filename,
            "file_path": file_path,
            "chunk_count": chunk_count if chunk_count is not None else 0,
            "upload_date": now,
        }
    )
    return papers


def delete_paper(papers, document_id: str):
    return [p for p in papers if p.get("document_id") != document_id]

