"""Run test queries against the fab_finder collection and print what comes back.

Used to check that the semantic queries work and to pick a distance cutoff
for "no reliable match".

Usage:
    python explore.py
"""

from db import get_collection

N_RESULTS = 5

# (label, query)
QUERIES = [
    ("test 1 (zh)", "我要在木板中间开一个圆形的洞，用来穿电线"),
    ("old test 1 (zh)", "我要在木桌面中间挖一个很圆的大圆"),
    ("test 2 (zh)", "一个能感应到有人从屏幕前走过的小零件"),
    ("backup (zh)", "让声音只在屏幕前一小块地方能听到"),
    ("test 1 (en)", "make an opening in the middle of a wooden board so wires can pass through"),
    ("test 2 (en)", "a small part that can sense someone walking past the screen"),
    ("backup (en)", "make sound audible only in a small area in front of the screen"),
    ("nonsense", "a recipe for chocolate cake"),
    ("nonsense", "who won the 1998 world cup"),
]


def main():
    collection = get_collection()
    print(f"Collection has {collection.count()} items.\n")

    best_distances = []

    for label, query in QUERIES:
        results = collection.query(query_texts=[query], n_results=N_RESULTS)

        # One query was sent, so take the first (and only) inner list of each field.
        metadatas = results["metadatas"][0]
        distances = results["distances"][0]
        documents = results["documents"][0]

        print("=" * 80)
        print(f"[{label}] {query}")
        print("-" * 80)
        for rank, (meta, dist, doc) in enumerate(zip(metadatas, distances, documents), start=1):
            title = meta.get("title", "(note)")
            domain = meta.get("domain", "")
            snippet = doc[:100].replace("\n", " ")
            print(f"{rank}. {dist:.3f}  {title}  [{domain}]")
            print(f"   {snippet}")
        print()

        best_distances.append((label, query, distances[0]))

    print("=" * 80)
    print("Best (top-1) distance for each query:")
    for label, query, dist in best_distances:
        print(f"  {dist:.3f}  [{label}] {query}")


if __name__ == "__main__":
    main()
