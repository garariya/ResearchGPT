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