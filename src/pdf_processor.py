import os


def extract_text(pdf_path):
    """
    Extract text from a PDF using PyMuPDF.

    Note: PyMuPDF is installed as `pymupdf` but imported as `fitz`.
    We import lazily so the Streamlit app can still start and show a helpful
    error message if the dependency is missing in the active environment.
    """
    try:
        import fitz  # PyMuPDF
    except ModuleNotFoundError as e:
        raise ModuleNotFoundError(
            "Missing dependency: PyMuPDF.\n\n"
            "Install it in the same environment where you run Streamlit:\n"
            "  pip install pymupdf\n"
            "or:\n"
            "  pip install -r requirements.txt\n\n"
            "Then restart:\n"
            "  streamlit run app.py"
        ) from e

    doc = fitz.open(pdf_path)

    text = ""

    for page_num, page in enumerate(doc):
        page_text = page.get_text()

        text += f"\n\n--- PAGE {page_num + 1} ---\n\n"
        text += page_text

    doc.close()

    return text


def extract_pdf_metadata(pdf_path):
    """
    Best-effort extraction of paper-level metadata from a PDF.

    Uses PyMuPDF's `doc.metadata` when available. Many academic PDFs either omit
    metadata or provide noisy values, so we fall back safely.
    """
    try:
        import fitz  # PyMuPDF
    except ModuleNotFoundError as e:
        raise ModuleNotFoundError(
            "Missing dependency: PyMuPDF.\n\n"
            "Install it in the same environment where you run Streamlit:\n"
            "  pip install pymupdf\n"
            "or:\n"
            "  pip install -r requirements.txt\n\n"
            "Then restart:\n"
            "  streamlit run app.py"
        ) from e

    doc = fitz.open(pdf_path)
    md = doc.metadata or {}
    doc.close()

    # Title / authors
    title = (md.get("title") or "").strip()
    authors = (md.get("author") or "").strip()

    # Year: try to parse from creationDate like "D:20190607123456Z"
    creation_date = (md.get("creationDate") or "").strip()
    year = "Unknown"
    if len(creation_date) >= 6 and creation_date.startswith("D:"):
        maybe_year = creation_date[2:6]
        if maybe_year.isdigit():
            year = maybe_year

    return {
        "title": title or os.path.basename(pdf_path),
        "authors": authors or "Unknown",
        "year": year,
    }