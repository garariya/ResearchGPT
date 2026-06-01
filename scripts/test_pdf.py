from src.pdf_processor import extract_text

text = extract_text("data/pdfs/paper1.pdf")

print(text[:5000])

print("\n\nLength:", len(text))