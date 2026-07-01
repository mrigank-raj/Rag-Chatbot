"""
Web Scraper module — fetches and cleans HTML content from the 5 Groww mutual
fund URLs defined in data/urls.json.
"""

import json
import os
import re
import time
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup


# Tags and class patterns to strip from the page
STRIP_TAGS = ["script", "style", "noscript", "svg", "img", "link", "meta"]
STRIP_CLASS_PATTERNS = [
    "header", "footer", "nav", "sidebar", "cookie", "banner",
    "advertisement", "ad-", "popup", "modal", "overlay",
    "loggedOut_", "dropdownUI_", "loader", "hoverDiv",
]


def load_urls(urls_path: str = "data/urls.json") -> list[dict]:
    """Load the source URLs from the JSON config file."""
    with open(urls_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["sources"]


def fetch_page(url: str) -> str | None:
    """Fetch raw HTML from a URL with a browser-like User-Agent."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"  [ERROR] Failed to fetch {url}: {e}")
        return None


def _should_strip_element(element) -> bool:
    """Check if an element matches any of the strip patterns based on its class or id."""
    if not hasattr(element, "attrs") or element.attrs is None:
        return False
    classes = " ".join(element.get("class", []))
    element_id = element.get("id", "")
    combined = f"{classes} {element_id}".lower()

    for pattern in STRIP_CLASS_PATTERNS:
        if pattern.lower() in combined:
            return True
    return False


def clean_html(raw_html: str) -> str:
    """
    Parse raw HTML and extract clean, readable text content.
    Strips navigation, ads, scripts, and other non-content elements.
    """
    soup = BeautifulSoup(raw_html, "html.parser")

    # 1. Remove unwanted tags entirely
    for tag_name in STRIP_TAGS:
        for tag in soup.find_all(tag_name):
            tag.decompose()

    # 2. Remove elements matching strip class patterns
    for element in soup.find_all(True):
        if _should_strip_element(element):
            element.decompose()

    # 3. Try to find the main content container
    #    Groww uses a div with id="__next" > div id="root" as the main wrapper
    main_content = soup.find("div", id="root")
    if not main_content:
        main_content = soup.find("div", id="__next")
    if not main_content:
        main_content = soup.body or soup

    # 4. Extract text with controlled whitespace
    text = main_content.get_text(separator="\n", strip=True)

    # 5. Clean up excessive whitespace and blank lines
    lines = []
    for line in text.splitlines():
        cleaned = line.strip()
        if cleaned:
            lines.append(cleaned)

    # 6. Remove duplicate consecutive lines
    deduped = []
    for line in lines:
        if not deduped or line != deduped[-1]:
            deduped.append(line)

    return "\n".join(deduped)


def generate_slug(scheme_name: str) -> str:
    """Generate a filename-safe slug from a scheme name."""
    slug = scheme_name.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = slug.strip("-")
    return slug


def scrape_all(urls_path: str = "data/urls.json", output_dir: str = "data/raw") -> list[dict]:
    """
    Scrape all URLs from the config, clean the HTML, and save to text files.

    Returns a list of dicts with scraping results for each source.
    """
    sources = load_urls(urls_path)
    os.makedirs(output_dir, exist_ok=True)

    results = []

    print(f"Starting scrape of {len(sources)} URLs...\n")

    for i, source in enumerate(sources, 1):
        url = source["url"]
        scheme_name = source["scheme_name"]
        category = source["category"]
        slug = generate_slug(scheme_name)

        print(f"[{i}/{len(sources)}] Scraping: {scheme_name}")
        print(f"  URL: {url}")

        # Fetch the page
        raw_html = fetch_page(url)
        if raw_html is None:
            results.append({
                "url": url,
                "scheme_name": scheme_name,
                "category": category,
                "status": "failed",
                "file_path": None,
                "text_length": 0,
            })
            continue

        # Clean the HTML
        cleaned_text = clean_html(raw_html)

        # Save to file
        file_path = os.path.join(output_dir, f"{slug}.txt")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(cleaned_text)

        text_length = len(cleaned_text)
        print(f"  Saved: {file_path} ({text_length} characters)")

        results.append({
            "url": url,
            "scheme_name": scheme_name,
            "category": category,
            "status": "success",
            "file_path": file_path,
            "text_length": text_length,
            "scraped_date": datetime.now(timezone.utc).isoformat(),
        })

        # Polite delay between requests
        if i < len(sources):
            time.sleep(2)

    # Print summary
    success_count = sum(1 for r in results if r["status"] == "success")
    print(f"\nScraping complete: {success_count}/{len(sources)} succeeded.")

    return results


# ---------------------------------------------------------------------------
# CLI entry point — run directly with: python -m src.ingestion.scraper
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    results = scrape_all()
    for r in results:
        status_icon = "[OK]" if r["status"] == "success" else "[FAIL]"
        print(f"  {status_icon} {r['scheme_name']}: {r['status']} ({r['text_length']} chars)")
