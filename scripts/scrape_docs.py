#!/usr/bin/env python3

import re
import requests
from pathlib import Path
from bs4 import BeautifulSoup

# Directories and paths
ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = ROOT / "docs"
RAW_DIR = DOCS_DIR / "raw"
REQS_FILE = ROOT / "requirements.txt"

DOCS_DIR.mkdir(exist_ok=True)
RAW_DIR.mkdir(exist_ok=True)


def parse_requirements_with_docs() -> dict[str, dict[str, str]]:
    """
    Parses requirements.txt and extracts libraries with [DOC_SCRAPE] URLs.
    Returns a dictionary of package metadata: {name: {url, version}}.
    """
    pattern = re.compile(r"^([a-zA-Z0-9_\-]+)==([0-9\.]+)")
    docs: dict[str, dict[str, str]] = {}

    with REQS_FILE.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            match = pattern.match(line)
            if match:
                pkg_name = match.group(1)
                version = match.group(2)
                m = re.search(r"\[DOC_SCRAPE\]:\s*(\S+)", line)
                if m:
                    docs[pkg_name] = {
                        "version": version,
                        "url": m.group(1)
                    }
    return docs


def sanitize_html(html: str) -> str:
    """
    Removes non-essential elements from HTML to reduce noise and token size.
    """
    soup = BeautifulSoup(html, "html.parser")

    for selector in [
        "nav", "header", "footer", ".toctree", ".sphinxsidebar",
        ".searchbox", "#sidebar", "#searchbox", ".docutils.footer",
        ".related", ".relation", ".highlight-python", ".edit-on-github"
    ]:
        for tag in soup.select(selector):
            tag.decompose()

    for tag in soup.find_all(["script", "style", "head"]):
        tag.decompose()

    return soup.prettify()


def scrape_all() -> None:
    """
    Scrapes raw HTML and produces a sanitized version for each
    [DOC_SCRAPE] requirement. Saves both to the docs/ folder.
    """
    docs = parse_requirements_with_docs()

    for pkg, meta in docs.items():
        print(f"\nFetching docs for {pkg} {meta['version']}")
        try:
            response = requests.get(meta["url"], timeout=10)
            response.raise_for_status()
        except Exception as e:
            print(f"  Failed to fetch {meta['url']}: {e}")
            continue

        clean = sanitize_html(response.text)

        out_path = RAW_DIR / f"{pkg}-{meta['version']}.html"
        with out_path.open("w", encoding="utf-8") as f:
            f.write(clean)
        print(f"  Saved sanitized HTML to {out_path}")

    print(
        "\nReminder: Upload each file in docs/raw/ one at a time using "
        "the prompt in docs/process_raw_prompt.txt."
    )


if __name__ == "__main__":
    scrape_all()
