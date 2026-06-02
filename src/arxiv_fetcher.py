import requests
import os
import time
import xml.etree.ElementTree as ET


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

    # Parse Atom XML using the Python stdlib to avoid requiring lxml in production.
    # arXiv returns an Atom feed (http://www.w3.org/2005/Atom).
    try:
        root = ET.fromstring(response.text)
    except ET.ParseError as e:
        raise RuntimeError("Failed to parse arXiv XML response.") from e

    ns = {"atom": "http://www.w3.org/2005/Atom"}
    entries = root.findall("atom:entry", ns)

    papers = []

    for entry in entries:

        title_el = entry.find("atom:title", ns)
        summary_el = entry.find("atom:summary", ns)
        id_el = entry.find("atom:id", ns)
        author_els = entry.findall("atom:author", ns)
        published_el = entry.find("atom:published", ns)

        title = title_el.text.strip() if (title_el is not None and title_el.text) else "No Title"
        summary = summary_el.text.strip() if (summary_el is not None and summary_el.text) else "No Summary"

        # Authors: "Author A, Author B, ..."
        authors = []
        for author_el in author_els:
            name_el = author_el.find("atom:name", ns)
            if name_el is not None and name_el.text:
                authors.append(name_el.text.strip())
        authors_str = ", ".join(authors) if authors else "Unknown"

        # published: 2023-04-15T12:30:00Z -> year: 2023
        published = published_el.text.strip() if (published_el is not None and published_el.text) else ""
        year = published[:4] if len(published) >= 4 and published[:4].isdigit() else "Unknown"

        # arXiv id looks like: http://arxiv.org/abs/XXXX.XXXXXvN
        # Convert to a PDF link: http://arxiv.org/pdf/XXXX.XXXXXvN.pdf
        abs_url = id_el.text.strip() if (id_el is not None and id_el.text) else ""
        pdf_url = abs_url.replace("abs", "pdf") + ".pdf" if abs_url else ""

        papers.append(
            {
                "title": title,
                "authors": authors_str,
                "year": year,
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