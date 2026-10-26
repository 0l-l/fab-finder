"""Download Wikipedia article intros for fab-finder's starting corpus.

Usage:
    python fetch_wiki.py

Output: data/wiki_articles.jsonl, one article per line:
    {"title", "url", "category", "domain", "text"}
"""

import json
import time
from pathlib import Path

import requests

API_URL = "https://en.wikipedia.org/w/api.php"

# Wikimedia asks every API client to identify itself with contact info.
# Fill in your own repo URL or email before running.
USER_AGENT = "fab-finder (CMU 15-114 student project; oulanl@andrew.cmu.edu" \
")"

OUTPUT_PATH = Path(__file__).parent / "data" / "wiki_articles.jsonl"
MAX_PER_CATEGORY = 300  # titles come back alphabetically, so a low cap cuts off late letters
PAUSE_SECONDS = 0.5     # wait between requests, to be polite to the API
EXTRACTS_BATCH = 20     # the API returns intros for at most 20 titles per request

CATEGORIES = [
    ("Category:Woodworking tools", "woodworking"),
    ("Category:Machining", "woodworking"),
    ("Category:Saws", "woodworking"),
    ("Category:Fasteners", "hardware"),
    ("Category:Sensors", "electronics"),
    ("Category:Microcontrollers", "electronics"),
    ("Category:Light-emitting diodes", "lighting_display"),
    ("Category:Display technology", "lighting_display"),
    ("Category:Loudspeakers", "audio"),
    ("Category:Audio amplifiers", "audio"),
]

# Articles we know our builds need but that aren't listed directly in the
# categories above (they sit in subcategories). Titles that don't exist on
# Wikipedia are skipped.
EXTRA_TITLES = {
    "woodworking": [
        "Hole saw", "Forstner bit", "Spade bit", "Drill bit", "Router (woodworking)",
        "CNC router", "Laser cutting", "Band saw", "Scroll saw", "Table saw",
        "Mortise and tenon", "Dovetail joint", "Pocket-hole joinery", "Biscuit joiner",
        "Dowel", "Wood glue", "Plywood", "Medium-density fibreboard", "Sandpaper",
    ],
    "hardware": [
        "Threaded insert", "Hinge", "Caster", "Drawer slide", "T-slot nut",
        "Hook-and-loop fastener", "Cable tie",
    ],
    "electronics": [
        "Passive infrared sensor", "Ultrasonic transducer", "Time-of-flight camera",
        "Arduino", "Raspberry Pi", "Relay", "Servomotor", "Stepper motor",
        "Breadboard", "Printed circuit board", "Soldering iron", "Heat-shrink tubing",
        "Terminal block", "Resistor", "Capacitor", "Potentiometer",
    ],
    "lighting_display": [
        "LED strip light", "Dimmer", "DMX512", "Projection mapping", "Diffuser (optics)",
    ],
    "audio": [
        "Sound from ultrasound", "Directional sound", "Subwoofer", "Tactile transducer",
    ],
}


def api_query(session, params):
    """Run one MediaWiki query, following 'continue' until all results are in.

    Yields each response's 'query' section.
    """
    params = {**params, "action": "query", "format": "json", "formatversion": "2"}
    while True:
        response = session.get(API_URL, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        time.sleep(PAUSE_SECONDS)

        if "query" in data:
            yield data["query"]
        if "continue" not in data:
            break
        params.update(data["continue"])


def get_category_titles(session, category):
    """Titles of the articles listed directly in a category (no subcategories)."""
    titles = []
    for query in api_query(session, {
        "list": "categorymembers",
        "cmtitle": category,
        "cmtype": "page",       # pages only, not subcategories or files
        "cmnamespace": 0,       # main article namespace
        "cmlimit": 500,
    }):
        titles.extend(member["title"] for member in query.get("categorymembers", []))
    return titles


def get_intros(session, titles):
    """Plain-text intros and URLs for a list of titles.

    Returns {title: {"url": ..., "text": ...}}. Disambiguation pages and pages
    with an empty intro are left out.
    """
    intros = {}
    for start in range(0, len(titles), EXTRACTS_BATCH):
        batch = titles[start:start + EXTRACTS_BATCH]
        for query in api_query(session, {
            "prop": "extracts|pageprops|info",
            "titles": "|".join(batch),
            "exintro": 1,           # only the text before the first heading
            "explaintext": 1,       # plain text, not HTML
            "exlimit": EXTRACTS_BATCH,
            "ppprop": "disambiguation",
            "inprop": "url",
            "redirects": 1,         # follow redirects to the real article
        }):
            for page in query.get("pages", []):
                if "disambiguation" in page.get("pageprops", {}):
                    continue
                text = (page.get("extract") or "").strip()
                if text:
                    intros[page["title"]] = {"url": page.get("fullurl", ""), "text": text}
    return intros


def main():
    if "CONTACT_INFO_HERE" in USER_AGENT:
        raise SystemExit("Edit USER_AGENT at the top of fetch_wiki.py with your contact info first.")

    session = requests.Session()
    session.headers["User-Agent"] = USER_AGENT

    seen_titles = set()
    records = []

    def add_articles(titles, category, domain):
        """Fetch intros for titles and append new ones to records. Returns how many were added."""
        intros = get_intros(session, titles)
        added = 0
        # Iterate over what came back: because of redirects, a returned title
        # can differ from the one we asked for.
        for title, page in intros.items():
            if title in seen_titles:
                continue
            records.append({
                "title": title,
                "url": page["url"],
                "category": category,
                "domain": domain,
                "text": page["text"],
            })
            seen_titles.add(title)
            added += 1
        return added

    for category, domain in CATEGORIES:
        titles = get_category_titles(session, category)
        titles = [
            t for t in titles
            if not t.startswith("List of") and t not in seen_titles
        ][:MAX_PER_CATEGORY]

        added = add_articles(titles, category, domain)
        warning = "   <-- check this category exists" if added == 0 else ""
        print(f"{category:35} {added:4} articles{warning}")

    for domain, titles in EXTRA_TITLES.items():
        label = f"Extra titles ({domain})"
        added = add_articles(titles, label, domain)
        missing = len(titles) - added
        print(f"{label:35} {added:4} articles ({missing} skipped: missing, redirect duplicate or already loaded)")

    OUTPUT_PATH.parent.mkdir(exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    print(f"\nTotal: {len(records)} articles saved to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
