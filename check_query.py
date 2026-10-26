"""Check where an expected article ranks for different phrasings of a query.

Usage:
    python check_query.py

Edit EXPECTED and PHRASINGS below to test other queries.
"""

from db import get_collection

EXPECTED = "Hole saw"
SEARCH_DEPTH = 50   # how far down the ranking to look

PHRASINGS = [
    "我要在木桌面中间挖一个很圆的大圆",
    "我要在木板中间开一个圆形的洞，用来穿电线",
    "在桌面上开一个圆口，把音箱嵌进去",
    "装在电钻上、一次就能切出一个圆形开口的工具",
    "I need to cut a big, very round circle out of the middle of a wooden tabletop",
    "make an opening in a wooden panel so cables can pass through",
    "a drill attachment that cuts a round opening in one go",
]


def main():
    collection = get_collection()
    for query in PHRASINGS:
        results = collection.query(query_texts=[query], n_results=SEARCH_DEPTH)
        titles = [m["title"] for m in results["metadatas"][0]]
        distances = results["distances"][0]

        if EXPECTED in titles:
            rank = titles.index(EXPECTED)
            found = f"rank {rank + 1}, distance {distances[rank]:.3f}"
        else:
            found = f"not in top {SEARCH_DEPTH}"

        top3 = ", ".join(f"{t} ({d:.3f})" for t, d in zip(titles[:3], distances[:3]))
        print(f"{query}\n  {EXPECTED}: {found}\n  top 3: {top3}\n")


if __name__ == "__main__":
    main()
