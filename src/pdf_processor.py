import fitz


def extract_text(pdf_path):
    doc = fitz.open(pdf_path)

    text = ""

    for page_num, page in enumerate(doc):
        page_text = page.get_text()

        text += f"\n\n--- PAGE {page_num + 1} ---\n\n"
        text += page_text

    doc.close()

    return text