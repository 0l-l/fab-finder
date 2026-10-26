# Fab Finder

<!--
DRAFT. The course requires the first four sections (What it does, What's stored,
Adding and searching, The two semantic queries) to be written by you, in your own
words. Use the text below as reference for the facts and numbers, then rewrite
those four sections yourself and delete this comment before submitting.
-->

## What it does and why

When my Entertainment Technology team builds physical installations (wooden tables, screens, sensors, lights, speakers), we usually know what we need something to *do*, but not what it's *called*, so we can't search for it or buy it. Fab Finder lets you describe the need in English or Chinese ("I need to open a round hole in a board to run wires through") and comes back with the technical name, a short comparison of options, search keywords for supplier sites, and anything our team has written down about it before.

## What's stored in the database

**Wikipedia passages (the starting corpus).** The intro sections of 830 English Wikipedia articles: every article listed directly in 10 categories (Woodworking tools, Machining, Saws, Fasteners, Sensors, Microcontrollers, Light-emitting diodes, Display technology, Loudspeakers, Audio amplifiers), plus a hand-picked list of about 50 articles our builds need that sit in subcategories (Hole saw, Passive infrared sensor, Laser cutting, DMX512, Directional sound, and others).

- **One item** is one chunk of an article's intro. Paragraphs longer than about 100 words are split at sentence boundaries; paragraphs shorter than 30 words are merged with the next one; each article keeps at most its first 3 chunks.
- The article title is put in front of each chunk ("Hole saw: A hole saw is…"), because the document text is what gets embedded.
- **Size:** 1,622 chunks, about 100,000 words.
- **Metadata:** `source` ("wikipedia"), `title`, `domain` (woodworking / hardware / electronics / lighting_display / audio), `category`, `url`, `chunk`.

**Team notes (added while the app runs).** Free-text notes in English or Chinese, like "Used a 2-inch hole saw on 3/4 inch plywood for cable pass-through at the campus shop; drill slowly and finish from the other side to avoid tear-out."

- **Metadata:** `source` ("team_note"), `domain` (one of the five above, or a custom area like "Paint and finishes"), `author`, `date`.
- Notes get a random unique id, so Chroma never silently ignores one because of a duplicate id.

Both kinds of items live in one collection, so a single search finds reference material and team experience together.

## Adding and searching

**Searching:** type what the thing needs to do and where it goes. The app:

1. Embeds the description and pulls the 15 closest Wikipedia chunks.
2. Keeps the best chunk per article and takes the top 4 articles, then loads each article's full stored intro so the model sees sizes and uses that may be in a later chunk.
3. Separately searches the team notes and keeps notes within the distance cutoff.
4. If nothing is closer than a cosine distance of **0.72**, it says there's no reliable match and suggests rephrasing, without calling the language model.
5. Otherwise it sends the passages and notes to an OpenAI model as numbered sources and asks for an **advice card** built only from them: technical names (English and Chinese, with aliases), a comparison of 2–3 options, English search keywords, and relevant team experience, with a source number on every point. The answer is in the same language as the question.
6. The app (not the model) lists the sources the card actually cited, with links, and folds away the ones it retrieved but didn't use.

**Adding:** choose "Add a note", write what you bought, where you got something made, or what worked, pick an area (or name your own), and add your name. The note is searchable immediately.

There are two interfaces with the same features: a command-line menu (`app.py`) and a minimal web page (`server.py`).

## The two semantic queries

| Query | What comes back | Distance |
|---|---|---|
| 我要在木板中间开一个圆形的洞，用来穿电线 ("I need to open a round hole in the middle of a board to run wires through") | **Hole saw**, ranked 1st | 0.662 |
| 一个能感应到有人从屏幕前走过的小零件 ("a small part that can sense someone walking past the screen") | **Motion detector**, plus the **Sensor** article's passage naming PIR sensors, in the top 3 | 0.635 |

**Why keyword search would fail:** the queries are in Chinese and the articles are in English, so they share no words at all; and even translated, "open a round hole" never contains "hole saw," and "sense someone walking past" never contains "motion detector" or "infrared."

For comparison, two queries that should match nothing ("a recipe for chocolate cake", "who won the 1998 world cup") had best distances of 0.770 and 0.797, which is how I chose the 0.72 cutoff.

**What I learned getting there:** my first version of query 1 was "我要在木桌面中间挖一个很圆的大圆" ("cut a big, very round circle out of a tabletop"). It ranked Hole saw only 10th, because it described the *shape* instead of the *purpose*. Hole saw also wasn't in the database at first: it lives in a Wikipedia subcategory, so I added a hand-picked title list. Rephrasing the query around what the hole is for put Hole saw in first place.

---

## How I used AI

I used Claude (claude.ai chat) throughout: to understand the assignment, brainstorm and choose the idea, plan the data and queries, write the code step by step from my prompts, debug errors on my Windows machine, and build the web front end. I ran every step myself, checked the output, and decided what to change (for example, which embedding model to use, which test queries to keep, and the UI design). The full process and my prompts are in `prompt_log.md`.

**Citations**
- Article text: [Wikipedia](https://en.wikipedia.org), via the [MediaWiki API](https://www.mediawiki.org/wiki/API:Main_page). Wikipedia text is licensed under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/); it is downloaded locally and not committed to this repo.
- [ChromaDB documentation](https://docs.trychroma.com)
- [OpenAI API documentation](https://platform.openai.com/docs) (embeddings and chat models)
- Fonts: [Roboto](https://fonts.google.com/specimen/Roboto) and [Noto Sans SC](https://fonts.google.com/noto/specimen/Noto+Sans+SC) from Google Fonts

---

## AI-generated documentation

*The sections below were generated by AI (Claude) and checked against the code.*

### Vector database and models

- **Vector database:** ChromaDB 1.5.9, using `PersistentClient`, so everything is saved in `chroma_store/` and survives restarts.
- **Embedding model:** OpenAI `text-embedding-3-small`, through Chroma's OpenAI embedding function, with cosine distance. It is multilingual, which is what lets Chinese queries match English text.
  - I first tried the local model `paraphrase-multilingual-MiniLM-L12-v2` (sentence-transformers). On my Windows laptop, Smart App Control blocked a scikit-learn DLL it depends on, so I switched to OpenAI embeddings.
- **Chat model for the advice card:** `gpt-6-luna` by default. Set `OPENAI_MODEL` in `.env` to use another.
- **Downloads on first run:** no models are downloaded; embeddings and the advice card are computed by the OpenAI API. The web page loads its fonts from Google Fonts.
- **Cost:** embedding the whole corpus is about 130,000 tokens (well under one US cent with `text-embedding-3-small`). Each search makes two small embedding calls and one chat call.

### Getting and loading the data

The raw data and the database are not in this repo (`data/` and `chroma_store/` are in `.gitignore`). To build them:

1. Open `fetch_wiki.py` and replace `CONTACT_INFO_HERE` in `USER_AGENT` with your email or repo URL. Wikimedia asks API clients to identify themselves.
2. `python fetch_wiki.py` downloads the article intros to `data/wiki_articles.jsonl` (about 1–2 minutes).
3. `python build_db.py` chunks them and loads them into Chroma (about 15 seconds). Use `python build_db.py --limit 50` to time a small run first. Rerunning is safe: it uses deterministic ids and `upsert`, so nothing is duplicated.

### Setup and running

Requires Python 3.10+ and an OpenAI API key.

```powershell
python -m venv .venv
.venv\Scripts\activate          # macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements.txt
```

Create a file named `.env` in the project folder containing one line:

```
OPENAI_API_KEY=sk-...
```

Then build the database (see above) and start either interface:

```powershell
python app.py        # command-line menu
python server.py     # web page at http://127.0.0.1:5000
```

### Files

| File | What it does |
|---|---|
| `app.py` | Command-line menu: get an advice card, add a team note, show notes |
| `server.py` | Flask server for the web page |
| `static/index.html` | The web page |
| `advisor.py` | Retrieval, distance cutoff, and advice card generation |
| `notes.py` | Adding and listing team notes |
| `db.py` | Opens the shared Chroma collection (one place for model, path and distance settings) |
| `fetch_wiki.py` | Downloads Wikipedia intros |
| `build_db.py` | Chunks and loads them into Chroma |
| `smoke_test.py` | First test: persistence and one cross-language query on 12 hand-written items |
| `explore.py`, `check_query.py` | Development tools used to test queries and choose the distance cutoff |
| `planning.md` | My planning notes from before and during the build |

### Known limitations

- Some relevant articles aren't in the corpus (e.g. Forstner bit), because they only appear in Wikipedia subcategories. The hand-picked title list in `fetch_wiki.py` is the place to add them.
- Wording matters: a query that describes what something is *for* works much better than one that only describes its shape, and a strong noun ("speaker") can pull results toward that topic.
- Searching needs an internet connection and an OpenAI API key, since embeddings come from the OpenAI API.
