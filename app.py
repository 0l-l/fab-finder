"""Fab Finder: describe what you need, get the technical name, options and team experience.

Usage:
    python app.py
"""

import sys

from advisor import advise
from db import get_collection
from notes import DOMAINS, add_note, list_notes

MENU = """
- Fab Finder -
1. Describe what you need -> get an advice card
2. Add a team note
3. Show all team notes
4. Quit"""


def ask(prompt):
    """input() that strips whitespace. Ctrl+C / Ctrl+Z are handled by the caller."""
    return input(prompt).strip()


def describe_need():
    query = ask("Describe what you need (English or Chinese): ")
    if not query:
        print("Nothing entered.")
        return
    print("\nSearching...\n")
    try:
        print(advise(query))
    except KeyboardInterrupt:
        print("\nCancelled.")
    except Exception as error:   # e.g. no network for the embedding call
        print(f"Something went wrong while searching: {error}")


def choose_domain():
    for number, domain in enumerate(DOMAINS, start=1):
        print(f"  {number}. {domain}")
    while True:
        choice = ask(f"Domain (1-{len(DOMAINS)}): ")
        if choice.isdigit() and 1 <= int(choice) <= len(DOMAINS):
            return DOMAINS[int(choice) - 1]
        print("Please enter one of the numbers above.")


def add_team_note():
    text = ask("Note (what you bought, where you got something made, what worked or didn't): ")
    if not text:
        print("Nothing entered, note not saved.")
        return
    domain = choose_domain()
    author = ask("Your name: ") or "unknown"
    try:
        add_note(text, domain, author)
    except Exception as error:
        print(f"Couldn't save the note: {error}")
        return
    print("Saved. It's searchable right away.")


def show_notes():
    notes = list_notes()
    if not notes:
        print("No team notes yet. Use option 2 to add one.")
        return
    print(f"\n{len(notes)} team note(s):\n")
    for note in notes:
        print(f"[{note['date']}] {note['author']} ({note['domain']})")
        print(f"  {note['text']}\n")


def main():
    collection = get_collection()
    total = collection.count()
    if total == 0:
        print("The database is empty. Run `python fetch_wiki.py` and then `python build_db.py` first.")
        sys.exit(1)
    note_count = len(list_notes())
    print(f"Database ready: {total} items ({total - note_count} Wikipedia chunks, {note_count} team notes).")

    actions = {"1": describe_need, "2": add_team_note, "3": show_notes}
    while True:
        print(MENU)
        choice = ask("Choose an option: ")
        if choice == "4":
            break
        if choice in actions:
            print()
            actions[choice]()
        else:
            print("Please choose 1, 2, 3 or 4.")
    print("Bye!")


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        # Ctrl+C (or Ctrl+Z then Enter on Windows) anywhere in the menu exits cleanly.
        print("\nBye!")
