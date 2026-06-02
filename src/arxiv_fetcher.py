import requests
from bs4 import BeautifulSoup
import os
import time


_DEFAULT_HEADERS = {
    # arXiv asks for a descriptive User-Agent for API access.
    # A generic UA reduces the chance of throttling/blocks.
    "User-Agent": "ResearchGPT/1.0 (contact: local-user) requests",
}


def _get_with_retries(url, *, timeout, max_retries=4):
    """
    arXiv can return 429 (rate limit) or occasionally time out.
    We retry with exponential backoff to make the UX reliable.
    """
    last_exc = None

    for attempt in range(max_retries):
        try:
            resp = requests.get(url, timeout=timeout, headers=_DEFAULT_HEADERS)

            # Retry on transient errors.
            if resp.status_code in {429, 500, 502, 503, 504}:
                # Exponential backoff: 1s, 2s, 4s, 8s ...
                time.sleep(2**attempt)
                continue

            return resp
        except requests.RequestException as e:
            last_exc = e
            time.sleep(2**attempt)

    if last_exc:
        raise last_exc
    raise RuntimeError("Request failed after retries.")


def search_papers(query, max_results=5):

    url = (
        f"https://export.arxiv.org/api/query?"
        f"search_query=all:{query}"
        f"&start=0"
        f"&max_results={max_results}"
    )

    # Use a longer read timeout; arXiv can be slow at times.
    response = _get_with_retries(url, timeout=(10, 60))

    if response.status_code != 200:
        raise RuntimeError(
            "arXiv request failed "
            f"(status={response.status_code}). Please try again."
        )

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

    response = _get_with_retries(pdf_url, timeout=(10, 120))

    if response.status_code != 200:
        raise RuntimeError(
            f"Failed to download PDF. "
            f"Status code: {response.status_code}"
        )

    with open(
        save_path,
        "wb"
    ) as f:
        f.write(response.content)

    return save_path