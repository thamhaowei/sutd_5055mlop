# src/extract_links.py
from __future__ import annotations

import argparse
from pathlib import Path
from typing import List, Dict

from bs4 import BeautifulSoup
import pandas as pd

SEPARATOR = "--------------"
BASE = "https://www.sutd.edu.sg"


def ensure_dirs(processed: Path, archive: Path):
    processed.mkdir(parents=True, exist_ok=True)
    archive.mkdir(parents=True, exist_ok=True)


def extract_links_from_raw(raw_dir: Path):
    # separate answers w links and wo links
    faq_with_links: List[str] = []
    faq_no_links: List[str] = []
    link_records: List[Dict[str, str]] = []

    for html_file in sorted(raw_dir.glob("*.html")):
        soup = BeautifulSoup(
            html_file.read_text(encoding="utf-8", errors="ignore"),
            "html.parser"
        )

        accordion = soup.select_one("section#accordion")
        if not accordion:
            continue

        for h6 in accordion.select("h6"):
            question = h6.get_text(" ", strip=True)

            ans_div = h6.find_next("div", class_="richText")
            if not ans_div:
                continue

            # Answer text
            answer_text = ans_div.get_text("\n", strip=True)

            # Extract hyperlinks
            links = []
            for a in ans_div.find_all("a", href=True):
                href = a["href"]
                if href.startswith("/"):
                    href = BASE + href
                links.append(href)

            entry = f"{SEPARATOR}\n{question}\n\n{answer_text}\n"

            if links:
                faq_with_links.append(entry)
                for l in links:
                    link_records.append({
                        "question": question,
                        "link": l,
                        "source_file": html_file.name
                    })
            else:
                faq_no_links.append(entry)

    return faq_no_links, faq_with_links, link_records


def main():
    parser = argparse.ArgumentParser(
        description="Separate FAQ entries with hyperlinks and record authoritative pages to scrape."
    )
    parser.add_argument("--raw", default="data/raw", help="Directory containing raw HTML files")
    parser.add_argument("--processed", default="data/processed", help="Directory for usable corpus")
    parser.add_argument("--archive", default="data/archive", help="Directory for archived entries and links")
    args = parser.parse_args()

    raw_dir = Path(args.raw)
    processed_dir = Path(args.processed)
    archive_dir = Path(args.archive)

    ensure_dirs(processed_dir, archive_dir)

    faq_no_links, faq_with_links, link_records = extract_links_from_raw(raw_dir)

    # Save outputs
    (processed_dir / "faq_no_links.txt").write_text(
        "".join(faq_no_links),
        encoding="utf-8"
    )

    (archive_dir / "faq_with_links.txt").write_text(
        "".join(faq_with_links),
        encoding="utf-8"
    )

    pd.DataFrame(link_records).to_csv(
        archive_dir / "faq_links_to_visit.csv",
        index=False
    )

    print("No-link Q&A:", len(faq_no_links))
    print("With-link Q&A:", len(faq_with_links))
    print("Links extracted:", len(link_records))


if __name__ == "__main__":
    main()

# to run: python -m src.extract_links