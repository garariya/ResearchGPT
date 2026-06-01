import requests
from bs4 import BeautifulSoup
import os


def search_papers(query, max_results=5):

    url = (
        f"https://export.arxiv.org/api/query?"
        f"search_query=all:{query}"
        f"&start=0"
        f"&max_results={max_results}"
    )

    response = requests.get(url, timeout=30)

    if response.status_code != 200:
        print(
            f"Error: arXiv API returned status code "
            f"{response.status_code}"
        )
        return []

    soup = BeautifulSoup(
        response.text,
        "xml"
    )

    entries = soup.find_all("entry")

    papers = []

    for entry in entries:

        title = (
            entry.title.text.strip()
            if entry.title
            else "No Title"
        )

        summary = (
            entry.summary.text.strip()
            if entry.summary
            else "No Summary"
        )

        pdf_url = (
            entry.id.text.replace(
                "abs",
                "pdf"
            )
            + ".pdf"
        )

        papers.append(
            {
                "title": title,
                "summary": summary,
                "pdf_url": pdf_url
            }
        )

    return papers


def download_paper(pdf_url, save_path):
    """
    Download a PDF from arXiv.
    """

    os.makedirs(
        os.path.dirname(save_path),
        exist_ok=True
    )

    response = requests.get(
        pdf_url,
        timeout=60
    )

    if response.status_code != 200:
        raise Exception(
            f"Failed to download PDF. "
            f"Status code: {response.status_code}"
        )

    with open(
        save_path,
        "wb"
    ) as f:
        f.write(response.content)

    return save_path