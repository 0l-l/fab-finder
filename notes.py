"""Team notes: experience the team adds while the app is running.

Notes go into the same collection as the Wikipedia chunks, marked with
source="team_note", so one search can find both.

Usage (self-test):
    python notes.py
"""

import uuid
from datetime import date

from db import get_collection

# The standard areas. A note can also use its own area name (e.g. "Paint and finishes").
DOMAINS = ["woodworking", "electronics", "hardware", "lighting_display", "audio"]
MAX_DOMAIN_CHARS = 40


def add_note(text, domain, author):
    """Add one note and return its id. It is searchable as soon as this returns."""
    text = text.strip()
    domain = domain.strip()
    if not text:
        raise ValueError("Note text is empty.")
    if not domain:
        raise ValueError("Choose an area, or name your own.")
    if len(domain) > MAX_DOMAIN_CHARS:
        raise ValueError(f"Keep the area name under {MAX_DOMAIN_CHARS} characters.")

    # uuid ids are always unique, so Chroma never silently ignores a new note
    # because of a duplicate id.
    note_id = f"note::{uuid.uuid4()}"
    get_collection().add(
        ids=[note_id],
        documents=[text],
        metadatas=[{
            "source": "team_note",
            "domain": domain,
            "author": author.strip() or "unknown",
            "date": date.today().isoformat(),
        }],
    )
    return note_id


def list_notes():
    """All team notes, oldest first, as a list of dicts."""
    results = get_collection().get(where={"source": "team_note"})
    notes = [
        {"id": note_id, "text": text, **meta}
        for note_id, text, meta in zip(results["ids"], results["documents"], results["metadatas"])
    ]
    # ISO dates (YYYY-MM-DD) sort correctly as plain strings.
    return sorted(notes, key=lambda note: note["date"])


if __name__ == "__main__":
    # Self-test: add a note, find it with different wording, then remove it
    # so the test doesn't leave junk in the real database.
    collection = get_collection()

    test_text = "Laser-cut 3mm basswood at the campus makerspace, clean edges, took 10 minutes."
    note_id = add_note(test_text, "woodworking", "self-test")
    print(f"Added test note {note_id}")

    query = "去哪里切薄木板"   # "where can I cut thin wood boards?"
    results = collection.query(
        query_texts=[query],
        n_results=3,
        where={"source": "team_note"},
    )
    print(f"\nQuery: {query}")
    for found_id, text, dist in zip(results["ids"][0], results["documents"][0], results["distances"][0]):
        marker = "  <-- the note we just added" if found_id == note_id else ""
        print(f"  {dist:.3f}  {text}{marker}")

    print(f"\nNotes stored right now: {len(list_notes())}")

    collection.delete(ids=[note_id])
    print(f"Removed test note. Notes stored now: {len(list_notes())}")
