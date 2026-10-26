# Planning: fab-finder

## 1. What the app does (one sentence)
A tool for an Entertainment Technology team building physical installations: describe what you need in English or Chinese ("something that can do X"), and the app finds the technical name, a few options to choose from, and the team's past experience, so we know what to buy and where to get it fabricated.

## 2. Items

### Knowledge items (initial corpus)
- Source: English Wikipedia articles, pulled by category
- One item: one paragraph of an article (only the first few paragraphs of each article, since the opening usually explains what the thing is and what it's used for)
- Chunking: split long paragraphs by sentence into chunks of roughly 80–100 English words (smaller chunks retrieve more precisely); merge very short paragraphs with the next one
- Metadata:
  - `source`: "wikipedia"
  - `title`: article title (i.e., the technical name)
  - `domain`: woodworking / electronics / hardware / lighting_display / audio
  - `category`: the Wikipedia category it was pulled from
  - `url`: article link
  - `chunk`: paragraph index

### Team notes (added by users at runtime)
- Who adds them: me and my teammates, after buying something, getting something fabricated, or running into a problem
- One item: one free-text note, in English or Chinese, e.g. "Laser-cut 3mm basswood at the campus shop, worked well"
- Metadata:
  - `source`: "team_note"
  - `domain`: chosen by the user when adding
  - `author`: who added it
  - `date`: date added
- IDs: use uuid, so duplicate IDs don't get silently ignored by Chroma

## 3. Wikipedia categories (check each one in a browser before loading)
- Woodworking: Category:Woodworking tools, Category:Woodworking joints, Category:Machining
- Hardware: Category:Fasteners
- Electronics: Category:Sensors, Category:Electronic components, Category:Microcontrollers
- Lighting and display: Category:Light-emitting diodes, Category:Display technology
- Audio: Category:Loudspeakers, Category:Audio amplifiers
- Only pull articles listed directly in each category; don't recurse into subcategories
- Expected size: ~10 categories × 30–80 articles × 2–3 chunks ≈ 1,000–1,500 items
- Time embedding on 50 items first, then decide whether to cut the corpus down

## 4. Two semantic queries

### Query 1
- Query: "我要在木桌面中间挖一个很圆的大圆" ("I need to cut a big, very round circle out of the middle of a wooden tabletop")
- Expected result: paragraphs about Hole saw, Circle cutter, or CNC router
- Why keyword search would fail: the query is in Chinese and the articles are in English; and even translated, "cut a circle" never contains the technical term "hole saw"

### Query 2
- Query: "一个能感应到有人从屏幕前走过的小零件" ("a small part that can sense someone walking past the screen")
- Expected result: the Passive infrared sensor (PIR) paragraph
- Why keyword search would fail: the article talks about "measuring infrared radiation emitted by objects," which shares no words with "someone walking past" or "screen," and it's in a different language

### Backup query (in case the two above don't work well)
- "让声音只在屏幕前一小块地方能听到" ("make sound audible only in a small area in front of the screen") → paragraphs about directional sound / parametric speakers

## 5. Query language and embedding model
- Support both English and Chinese queries
- Embedding model: OpenAI `text-embedding-3-small`, plugged in through Chroma's OpenAI embedding function (multilingual, so Chinese queries can match English text)
- Originally planned to use `paraphrase-multilingual-MiniLM-L12-v2` from sentence-transformers, but Windows Smart App Control blocked a scikit-learn DLL that sentence-transformers imports, so I switched to OpenAI embeddings
- Needs `OPENAI_API_KEY` in `.env`; embedding the corpus and every search/added note calls the API (cost is very small)
- Set the embedding model when the collection is created; if the model ever changes, delete `chroma_store/` and rebuild

## 6. What the app does with results: the buying / fabrication advice card
Flow:
1. User types a description of what they need
2. Retrieve more results than needed (e.g. 15), deduplicate by `title` so there are several distinct options
3. Run a separate query filtered to `source = team_note` for team experience
4. Check distances: if even the best result is above a threshold, tell the user "no reliable match, try rephrasing" (threshold decided in Step 5 from real data)
5. Send the retrieved chunks to an OpenAI model and ask it to build the advice card **using only those chunks**

The advice card includes:
- Technical name (English and Chinese, plus common aliases)
- Comparison of 2–3 candidate options (what size, precision, and difficulty each suits)
- English search keywords to paste into shopping or electronics supplier sites
- Relevant past team experience (if any)
- A source for every point (Wikipedia article title or note author)

The same API key in `.env` is used for embeddings and the advice card, read with `python-dotenv`; `.env` is already in `.gitignore`.

## CLI menu (Step 8)
1. Describe a need, get an advice card
2. Add a team note
3. Show all team notes
4. Quit

## To verify
- [ ] Each Wikipedia category exists and its articles are relevant
- [ ] Embedding time for 50 items
- [ ] Whether the two queries retrieve the expected items on real data
- [ ] Distance threshold
