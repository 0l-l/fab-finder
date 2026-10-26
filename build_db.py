"""Chunk the Wikipedia intros and load them into the fab_finder collection.

Usage:
    python build_db.py             # load everything
    python build_db.py --limit 50  # load only the first 50 chunks (to time it)

Safe to rerun: ids are deterministic and loading uses upsert, so existing
chunks are replaced instead of duplicated.
"""

import argparse
import json
import re
import time
from pathlib import Path

from db import get_collection

INPUT_PATH = Path(__file__).parent / "data" / "wiki_articles.jsonl"

MAX_CHUNK_WORDS = 100
MIN_PARAGRAPH_WORDS = 30
MAX_CHUNKS_PER_ARTICLE = 3
BATCH_SIZE = 100
TOKENS_PER_WORD = 1.3   # rough average for English text

SENTENCE_END = re.compile(r"(?<=[.!?])\s+")


def word_count(text):
    return len(text.split())


def merge_short_paragraphs(paragraphs):
    """Join paragraphs shorter than MIN_PARAGRAPH_WORDS onto the next one."""
    merged = []
    carry = ""
    for paragraph in paragraphs:
        text = f"{carry} {paragraph}".strip() if carry else paragraph
        if word_count(text) < MIN_PARAGRAPH_WORDS:
            carry = text
        else:
            merged.append(text)
            carry = ""
    if carry:
        # A short leftover at the end goes onto the last paragraph.
        if merged:
            merged[-1] = f"{merged[-1]} {carry}"
        else:
            merged.append(carry)
    return merged


def split_long_paragraph(paragraph):
    """Split a paragraph into chunks of at most ~MAX_CHUNK_WORDS words, at sentence ends."""
    if word_count(paragraph) <= MAX_CHUNK_WORDS:
        return [paragraph]

    chunks = []
    current = []
    current_words = 0
    for sentence in SENTENCE_END.split(paragraph):
        sentence_words = word_count(sentence)
        if current and current_words + sentence_words > MAX_CHUNK_WORDS:
            chunks.append(" ".join(current))
            current, current_words = [], 0
        current.append(sentence)
        current_words += sentence_words
    if current:
        chunks.append(" ".join(current))
    return chunks


def chunk_article(text):
    """Turn one article intro into at most MAX_CHUNKS_PER_ARTICLE chunks."""
    paragraphs = [p.strip() for p in text.split("\n") if p.strip()]
    chunks = []
    for paragraph in merge_short_paragraphs(paragraphs):
        chunks.extend(split_long_paragraph(paragraph))
    return chunks[:MAX_CHUNKS_PER_ARTICLE]


def build_items():
    """Read the JSONL file and return (ids, documents, metadatas) for every chunk."""
    ids, documents, metadatas = [], [], []
    with INPUT_PATH.open(encoding="utf-8") as f:
        for line in f:
            article = json.loads(line)
            for index, chunk in enumerate(chunk_article(article["text"])):
                ids.append(f"wiki::{article['title']}::{index}")
                # The title goes into the embedded text so the technical name
                # is part of what gets matched.
                documents.append(f"{article['title']}: {chunk}")
                metadatas.append({
                    "source": "wikipedia",
                    "title": article["title"],
                    "domain": article["domain"],
                    "category": article["category"],
                    "url": article["url"],
                    "chunk": index,
                })
    return ids, documents, metadatas


def main():
    parser = argparse.ArgumentParser(description="Load Wikipedia chunks into Chroma.")
    parser.add_argument("--limit", type=int, help="only load the first N chunks")
    args = parser.parse_args()

    if not INPUT_PATH.exists():
        raise SystemExit(f"{INPUT_PATH} not found. Run fetch_wiki.py first.")

    ids, documents, metadatas = build_items()
    if args.limit:
        ids, documents, metadatas = ids[:args.limit], documents[:args.limit], metadatas[:args.limit]

    total_words = sum(word_count(d) for d in documents)
    print(f"{len(documents)} chunks, about {total_words:,} words "
          f"(~{int(total_words * TOKENS_PER_WORD):,} tokens to embed)")

    collection = get_collection()
    start = time.time()
    for i in range(0, len(ids), BATCH_SIZE):
        end = i + BATCH_SIZE
        collection.upsert(ids=ids[i:end], documents=documents[i:end], metadatas=metadatas[i:end])
        done = min(end, len(ids))
        print(f"  {done}/{len(ids)} chunks loaded, {time.time() - start:.1f}s elapsed")

    print(f"\nDone in {time.time() - start:.1f}s. Collection now has {collection.count()} items.")


if __name__ == "__main__":
    main()
