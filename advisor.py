"""Build a buying / fabrication advice card from what the database retrieves.

Usage (try it directly):
    python advisor.py "我要在木板中间开一个圆形的洞，用来穿电线"
"""

import os
import re
import sys

from openai import OpenAI, OpenAIError

from db import get_collection   # importing db also loads .env

THRESHOLD = 0.72        # cosine distance cutoff, chosen in Step 5 from real queries
N_WIKI = 15             # how many Wikipedia chunks to pull before deduplicating
TOP_TITLES = 4          # how many distinct articles to send to the model
N_NOTES = 3             # how many team notes to consider
DEFAULT_MODEL = "gpt-6-luna"

SYSTEM_PROMPT = """You help an Entertainment Technology team that builds physical installations \
(furniture, screens, electronics, lighting, audio) figure out what to buy and how to fabricate things. \
The team usually knows what they need something to DO, but not what it is called.

Use ONLY the numbered sources you are given. Do not add facts from your own knowledge. \
If the sources don't answer the request, say so plainly and suggest how to rephrase it.

Write the card in the same language as the user's request, using these sections:

1. Technical names: the English name of each relevant item, its Chinese translation, and common aliases.
2. Options: compare the 2-3 most relevant options (what size, precision and difficulty each suits). \
If the sources only support one option, give one.
3. Search keywords: English phrases to paste into shopping or electronics supplier sites.
4. Team experience: what the team notes say, if any notes were provided, citing those notes. \
Otherwise write only that there are no related team notes yet, with no source number.

End every point with the source number(s) it actually comes from, like [2] or [1][3]. \
Skip sources that aren't relevant to the request. \
Translating a name into Chinese is fine; cite the source of the English name. Keep it under about 250 words."""

_collection = None


def collection():
    """Open the collection once and reuse it."""
    global _collection
    if _collection is None:
        _collection = get_collection()
    return _collection


def is_chinese(text):
    return re.search(r"[一-鿿]", text) is not None


def retrieve(query):
    """Return (wiki, notes): the best chunk per article, and notes under THRESHOLD."""
    wiki_results = collection().query(
        query_texts=[query], n_results=N_WIKI, where={"source": "wikipedia"}
    )
    wiki = []
    seen_titles = set()
    # Results come back sorted by distance, so the first chunk seen for a
    # title is that title's best one.
    for doc, meta, dist in zip(wiki_results["documents"][0],
                               wiki_results["metadatas"][0],
                               wiki_results["distances"][0]):
        if meta["title"] in seen_titles:
            continue
        seen_titles.add(meta["title"])
        wiki.append({"text": doc, "meta": meta, "distance": dist})
        if len(wiki) == TOP_TITLES:
            break

    # Search finds the best-matching chunk, but the model gives better advice
    # with the article's whole intro (sizes and uses are often in a later chunk).
    # So fetch every stored chunk of the chosen articles and join them in order.
    if wiki:
        full = collection().get(where={"$and": [
            {"source": "wikipedia"},
            {"title": {"$in": [item["meta"]["title"] for item in wiki]}},
        ]})
        chunks_by_title = {}
        for doc, meta in zip(full["documents"], full["metadatas"]):
            # Each chunk starts with "Title: "; drop it so the joined text reads normally.
            text = doc.split(": ", 1)[1] if doc.startswith(meta["title"] + ": ") else doc
            chunks_by_title.setdefault(meta["title"], []).append((meta["chunk"], text))
        for item in wiki:
            chunks = sorted(chunks_by_title.get(item["meta"]["title"], []))
            if chunks:
                item["text"] = " ".join(text for _, text in chunks)

    note_results = collection().query(
        query_texts=[query], n_results=N_NOTES, where={"source": "team_note"}
    )
    notes = [
        {"text": doc, "meta": meta, "distance": dist}
        for doc, meta, dist in zip(note_results["documents"][0],
                                   note_results["metadatas"][0],
                                   note_results["distances"][0])
        if dist <= THRESHOLD
    ]
    return wiki, notes


def format_sources_for_model(wiki, notes):
    """Numbered source list the model sees. Numbering: Wikipedia first, then notes."""
    lines = []
    for i, item in enumerate(wiki, start=1):
        lines.append(f'[{i}] Wikipedia article "{item["meta"]["title"]}": {item["text"]}')
    for i, item in enumerate(notes, start=len(wiki) + 1):
        meta = item["meta"]
        lines.append(f"[{i}] Team note by {meta['author']} on {meta['date']}: {item['text']}")
    return "\n\n".join(lines)


def source_entries(wiki, notes, card):
    """Sources built by this code (not the model), numbered like the model saw them.

    'cited' marks the sources the card actually refers to with [n].
    """
    cited = {int(n) for n in re.findall(r"\[(\d+)\]", card)}
    entries = []
    for i, item in enumerate(wiki, start=1):
        meta = item["meta"]
        entries.append({"n": i, "kind": "wikipedia", "label": meta["title"], "url": meta["url"],
                        "text": "", "distance": round(item["distance"], 3), "cited": i in cited})
    for i, item in enumerate(notes, start=len(wiki) + 1):
        meta = item["meta"]
        entries.append({"n": i, "kind": "note", "label": f"Team note by {meta['author']}, {meta['date']}",
                        "url": "", "text": item["text"], "distance": round(item["distance"], 3),
                        "cited": i in cited})
    return entries


def no_match_message(query):
    if is_chinese(query):
        return ("没有找到可靠的匹配。试着换一种说法，描述这个东西要做什么、用在哪里，"
                "比如“在木板上开一个圆洞用来穿线”，而不是只说形状。")
    return ("No reliable match found. Try rephrasing: describe what the thing needs to do "
            "and where it's used (e.g. 'open a round hole in a board for cables'), not just its shape.")


def build_advice(query):
    """Retrieve, then build the advice card. Returns a dict used by both the CLI and the website:

    {"status": "ok" | "no_match" | "fallback", "card": str, "message": str, "sources": [...]}
    """
    wiki, notes = retrieve(query)

    best_wiki = wiki[0]["distance"] if wiki else float("inf")
    if best_wiki > THRESHOLD and not notes:
        return {"status": "no_match", "card": "", "message": no_match_message(query), "sources": []}

    user_message = f"Request: {query}\n\nSources:\n{format_sources_for_model(wiki, notes)}"
    try:
        client = OpenAI()   # reads OPENAI_API_KEY from the environment
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", DEFAULT_MODEL),
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
        )
        card = response.choices[0].message.content.strip()
    except OpenAIError as error:
        # Show what the database found, even though the model couldn't be reached.
        return {"status": "fallback", "card": "",
                "message": f"Couldn't reach the AI model: {error}",
                "sources": source_entries(wiki, notes, "")}

    return {"status": "ok", "card": card, "message": "", "sources": source_entries(wiki, notes, card)}


def advise(query):
    """Advice card as plain text, for the command line."""
    result = build_advice(query)
    if result["status"] == "no_match":
        return result["message"]

    def line(s):
        extra = f": {s['text']}" if s["text"] else (f" - {s['url']}" if s["url"] else "")
        return f"  [{s['n']}] {s['label']}{extra}  (distance {s['distance']:.3f})"

    if result["status"] == "fallback":
        return "\n".join([f"({result['message']})", "", "Closest matches in the database:"]
                         + [line(s) for s in result["sources"]])

    used = [line(s) for s in result["sources"] if s["cited"]]
    unused = [line(s) for s in result["sources"] if not s["cited"]]
    parts = [result["card"], "", "Sources:"] + used
    if unused:
        parts += ["Also retrieved, but not used:"] + unused
    return "\n".join(parts)


if __name__ == "__main__":
    query = " ".join(sys.argv[1:]) or input("Describe what you need: ")
    print()
    print(advise(query))
