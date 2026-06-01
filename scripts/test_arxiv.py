from src.arxiv_fetcher import search_papers, download_paper

papers = search_papers("Retrieval Augmented Generation")

if not papers:
    print("No papers found.")
    exit()

print("\nFound Papers:\n")

for i, paper in enumerate(papers):
    print(f"{i+1}. {paper['title']}")

first_paper = papers[0]

pdf_path = download_paper(
    first_paper["pdf_url"],
    "data/pdfs/paper1.pdf"
)

print("\nDownloaded:", pdf_path)