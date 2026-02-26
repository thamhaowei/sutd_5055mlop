# src/extract_faq.py
from __future__ import annotations

import argparse
import re
import shutil
from pathlib import Path
from typing import List, Tuple

from bs4 import BeautifulSoup

SEPARATOR = "---------------------------"


def clean(text: str) -> str:
    # to make it look nicer
    text = re.sub(r"\s+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_faq_from_html(html: str) -> List[Tuple[str, str]]:
    soup = BeautifulSoup(html, "html.parser")

    accordion = soup.select_one("section#accordion")
    if not accordion:
        return []

    qa_pairs: List[Tuple[str, str]] = []

    for h6 in accordion.select("h6"):
        q = clean(h6.get_text(" ", strip=True))
        if not q:
            continue

        ans_div = h6.find_next("div", class_="richText")
        if not ans_div:
            continue

        a = clean(ans_div.get_text("\n", strip=True))
        if not a:
            continue

        qa_pairs.append((q, a))

    return qa_pairs


def write_qa_txt(qa_pairs: List[Tuple[str, str]], out_path: Path) -> None:
    parts = []
    for q, a in qa_pairs:
        parts.append(SEPARATOR)
        parts.append(q)
        parts.append("")  # blank line
        parts.append(a)
        parts.append("")  # blank line


    out_text = "\n".join(parts).rstrip()
    out_path.write_text(out_text, encoding="utf-8")


def combine_faq_txt(processed_dir: Path, combined_filename: str) -> Path:
    # combine into one file
    faq_files = sorted(processed_dir.glob("*_faq.txt"))
    if not faq_files:
        raise RuntimeError(f"No *_faq.txt files found in {processed_dir}. Run extraction first.")

    combined_path = processed_dir / combined_filename
    combined_text = "\n\n".join(f.read_text(encoding="utf-8") for f in faq_files)
    combined_path.write_text(combined_text, encoding="utf-8")
    return combined_path


def count_questions_in_combined(combined_path: Path) -> int:
    # count for verification
    text = combined_path.read_text(encoding="utf-8")
    return text.count(SEPARATOR)

def archive_per_page_files(processed_dir: Path, archive_dir: Path):
    """Move all *_faq.txt files into data/archive after combining."""
    archive_dir.mkdir(parents=True, exist_ok=True)

    for f in processed_dir.glob("*_faq.txt"):
        shutil.move(str(f), archive_dir / f.name)

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract SUTD FAQ Q&A from raw HTML, save per-page txt, and optionally combine into one corpus."
    )
    parser.add_argument("--raw", default="data/raw", help="Directory containing raw .html files")
    parser.add_argument("--out", default="data/processed", help="Directory to write extracted FAQ .txt files")
    parser.add_argument(
        "--combine",
        action="store_true",
        help="Combine all per-page *_faq.txt outputs into a single corpus file",
    )
    parser.add_argument(
        "--combined_name",
        default="sutd_undergrad_faq_all.txt",
        help="Filename for the combined corpus (written into --out directory)",
    )
    args = parser.parse_args()

    raw_dir = Path(args.raw)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    html_files = sorted(raw_dir.glob("*.html"))
    if not html_files:
        raise RuntimeError(f"No .html files found in {raw_dir}. Did you run fetch_html.py?")

    total_qas = 0

    # 1) Extract per-page FAQ files
    for html_path in html_files:
        html = html_path.read_text(encoding="utf-8", errors="ignore")
        qa = extract_faq_from_html(html)

        out_path = out_dir / f"{html_path.stem}_faq.txt"
        write_qa_txt(qa, out_path)

        total_qas += len(qa)
        print(f"{html_path.name} → {out_path.name} | extracted {len(qa)} Q&A")

    print(f"Done. Extracted {total_qas} total Q&A pairs from {len(html_files)} pages.")

    # 2) Combine + count (optional)
    if args.combine:
        combined_path = combine_faq_txt(out_dir, args.combined_name)
        print(f"Combined {len(sorted(out_dir.glob('*_faq.txt')))} files → {combined_path}")

        num_questions = count_questions_in_combined(combined_path)
        print("Number of questions:", num_questions)

        archive_per_page_files(out_dir, Path("data/archive"))
        print("Moved per-page FAQ files to data/archive/")


if __name__ == "__main__":
    main()

# to run: python -m src.extract_faq --raw data/raw --out data/processed --combine