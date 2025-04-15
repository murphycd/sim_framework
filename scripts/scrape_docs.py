#!/usr/bin/env python3

import re
import requests
from pathlib import Path
from bs4 import BeautifulSoup

# Directory setup
ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = ROOT / "docs"
RAW_DIR = DOCS_DIR / "raw"
REQS_FILE = ROOT / "requirements.txt"

DOCS_DIR.mkdir(exist_ok=True)
RAW_DIR.mkdir(exist_ok=True)

# Parse requirements.txt for libraries tagged with [DOC_SCRAPE]: <url>


def parse_requirements_with_docs():
    pattern = re.compile(r"^([a-zA-Z0-9_\-]+)==([0-9\.]+)")
    docs = {}

    with open(REQS_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            match = pattern.match(line)
            if match:
                pkg_name = match.group(1)
                doc_url = None
                m = re.search(r"\[DOC_SCRAPE\]:\s*(\S+)", line)
                if m:
                    doc_url = m.group(1)
                if doc_url:
                    docs[pkg_name] = {"url": doc_url,
                                      "version": match.group(2)}
    return docs

# Minimal HTML sanitization to reduce noise


def sanitize_html(html):
    soup = BeautifulSoup(html, "html.parser")

    for selector in [
        "nav", "header", "footer", ".toctree", ".sphinxsidebar", ".searchbox",
        "#sidebar", "#searchbox", ".docutils.footer", ".related", ".relation",
        ".highlight-python", ".edit-on-github"
    ]:
        for tag in soup.select(selector):
            tag.decompose()

    for tag in soup.find_all(["script", "style"]):
        tag.decompose()

    return soup.prettify()

# Main scraping and sanitization logic


def scrape_all():
    docs = parse_requirements_with_docs()

    for pkg, meta in docs.items():
        print(f"\nFetching docs for {pkg} {meta['version']}")
        try:
            response = requests.get(meta["url"], timeout=10)
            response.raise_for_status()
        except Exception as e:
            print(f"  Failed to fetch {meta['url']}: {e}")
            continue

        raw_path = RAW_DIR / f"{pkg}.raw.html"
        out_path = DOCS_DIR / f"{pkg}.html"

        with open(raw_path, "w", encoding="utf-8") as f:
            f.write(response.text)
        print(f"  Saved raw HTML to {raw_path}")

        clean = sanitize_html(response.text)

        with open(out_path, "w", encoding="utf-8") as f:
            f.write(clean)
        print(f"  Saved sanitized HTML to {out_path}")

    print("\nReminder: Upload each file in docs/raw/ one at a time using the prompt in docs/process_raw_prompt.txt.")


if __name__ == "__main__":
    scrape_all()
