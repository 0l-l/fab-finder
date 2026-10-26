# Prompt Log: fab-finder

## Tools used

I used Claude (Claude Opus 5.5, in the claude.ai chat app) for the whole project. I used it to understand the assignment, come up with and pick an idea, plan, fix my Windows setup, write and debug the code, and build the web page.

For the coding steps, Claude first helped me draft a plan with one prompt per step. I edited each prompt and sent them one at a time, ran the code myself, and pasted the output or errors back. That's why the coding prompts below sound more formal than my other messages.

Why: [Fill in one or two sentences in your own words.]

The prompts below are copied exactly as I sent them. My early messages were in Chinese, so each one has an English translation in brackets. When I mostly pasted terminal output or a screenshot, I describe it instead.

---

## Phase 0: Brainstorming

> 可以给我举个例子吗
> [Can you give me an example?]

Claude showed me an example project (a Sherlock Holmes reading helper) and how it would meet each requirement.

> 我现在最简单的想法就是1.关于cmu一些课程交的东西 2. 某个比较长的剧集或者电影的剧情查找。但这些都不算对我很有用的，我还在想
> [My simplest ideas right now are 1. something about CMU coursework I've submitted, 2. plot lookup for a long TV series or movie. But neither is that useful to me; I'm still thinking.]

Claude said idea 1 could cause academic integrity problems and might not have enough data. It suggested searching across languages (ask in Chinese, find English text) to make things more interesting.

> 我觉得跨语言这个很好，但是具体要和什么内容相结合呢
> [I like the cross-language idea, but what content should it be combined with?]

> 我在思考有没有可能是关于书籍的，比如所有哲学类的书，但哲学家的理论都不一样吗
> [Could it be about books, like philosophy books? But don't philosophers' theories all differ?]

Claude said the different views would actually help, because the search finds passages about the same question and the app could compare the answers. I kept thinking about what I would actually use.

---

## Phase 1: Choosing the idea

> 我还想到一个但是不一定有数据，我是做entertainment technoogy的，我们最近就在为了一个新的屏幕做physical buildups，其中有木制的桌子，也有电子芯片等。采买的时候比较复杂，因为不知道专业名字，只知道想要什么功能的东西，去哪里做加工也是这样，比如我们知道要给木板中间切一个圆形，但是不知道具体应该去哪里等等。你觉得这个想法有可能吗
> [I thought of another one, but I'm not sure there's data. I'm in Entertainment Technology, and we're doing physical buildups for a new screen, including wooden tables and electronic chips. Purchasing is complicated because we don't know the technical names, only what function we need. Same for fabrication: e.g., we know we need to cut a circle in the middle of a wooden board, but don't know where to get that done. Do you think this idea could work?]

Claude thought this was a really good fit. The whole problem is "I know what it does but not what it's called," and that's exactly where keyword search fails. The plan: use Wikipedia articles for what things are called and what they do, let the team add notes about where to buy or make things, and search across languages.

> 那就行下来是这个了。你可以引导我从哪里开始。
> [OK, let's go with this one. Can you guide me on where to start?]

---

## Phase 2: Environment setup

Setting up Python on my laptop took a few tries. I sent screenshots of each error.

First, `py -m venv .venv` said `py` wasn't recognized, and `python --version` told me to install Python from the Microsoft Store. Python just wasn't installed; Windows only had a shortcut that points to the Store. I installed Python from python.org (with "Add python.exe to PATH" checked) and turned off those Store shortcuts in Windows settings.

Next, activating the virtual environment failed with "running scripts is disabled on this system." Because of that, my first `pip install chromadb` went into the main Python instead of the venv. I allowed scripts with `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`, activated the venv, and installed again with `python -m pip install chromadb`. In the end I had ChromaDB 1.5.9 on Python 3.13.

---

## Phase 3: Building

### Step 3: Smoke test

**Prompt:**
> I'm starting a new Python project called fab-finder on Windows (PowerShell, Python 3.13, venv). I have chromadb 1.5.9 and sentence-transformers installed.
>
> Write smoke_test.py that:
> 1. Creates chromadb.PersistentClient(path="./chroma_store") so data is saved to disk.
> 2. Uses Chroma's SentenceTransformer embedding function with the model "paraphrase-multilingual-MiniLM-L12-v2", because my queries will be in Chinese and my documents in English.
> 3. Creates (or gets) a collection named "smoke_test" with that embedding function, using cosine distance.
> 4. Adds about 12 short English descriptions of things used in physical builds, each with fixed string ids and a "domain" metadata field (woodworking / electronics / hardware / lighting_display / audio). Include: hole saw, jigsaw, CNC router, passive infrared (PIR) sensor, ultrasonic distance sensor, Arduino, addressable LED strip, wood screw, threaded insert, full-range speaker, audio amplifier, soldering iron. Describe what each one does, but don't write the descriptions to match my test query on purpose.
> 5. Prints collection.count().
> 6. Queries with the Chinese text "我要在木桌面中间挖一个很圆的大圆" with n_results=3 and prints the full raw result object.
>
> Only use APIs that exist in chromadb 1.x. Do not use chromadb.Client(Settings(...)) or collection.persist().
>
> After the code, explain:
> - what each argument does,
> - the exact shape of the query result (why it's a list of lists),
> - what happens to the add() call when I run the script a second time with the same ids.

**What happened:** This step took the longest to get working, mostly because of misleading errors.

The first version used a free local model through sentence-transformers. It crashed saying "The sentence_transformers python package is not installed." That wasn't true. Higher up in the error was the real problem: "DLL load failed... An Application Control policy has blocked this file." Windows Smart App Control had blocked a file from scikit-learn (which sentence-transformers needs), and Chroma reported it as a missing package. I decided to switch to OpenAI's embedding model (`text-embedding-3-small`), since I was going to use the OpenAI API for the advice card anyway.

(Funny enough, the local version did run once later without getting blocked. Its top 3 were hole saw, jigsaw and wood screw. The OpenAI version below got hole saw, jigsaw and CNC router, all cutting tools, so I stayed with OpenAI.)

The OpenAI version then said "The OPENAI_API_KEY environment variable is not set." My `.env` file had only the key, without `OPENAI_API_KEY=` in front of it. One of the commands we used to check the file ended up printing the key, so I deleted that key and made a new one. After fixing `.env`, everything worked. There were 12 items, and running it again still showed 12, so the data was saved on disk and adding the same ids twice didn't make duplicates. The Chinese query found hole saw, jigsaw and CNC router (distances 0.74, 0.77, 0.78). The printed result looked like Claude said it would (a list inside a list), with three extra fields it hadn't mentioned.

### Step 4a: Shared database setup

**Prompt:**
> Now I'm building the real app. Create db.py with one function, get_collection(), that every other script will import, so they all use the same settings:
> - PersistentClient at "./chroma_store"
> - collection name "fab_finder"
> - the same OpenAI embedding function (text-embedding-3-small, key from OPENAI_API_KEY via python-dotenv) and cosine distance as in smoke_test.py
>
> Keep model name, collection name and store path as constants at the top of the file. Explain why all scripts must use the same embedding function for one collection.

**What happened:** Claude changed one thing. Instead of `./chroma_store`, it put the database folder next to `db.py`, so running a script from a different folder can't accidentally create a second, empty database. I asked why every script needs the same embedding model. Different models turn text into numbers in different ways, so mixing them either crashes or quietly gives nonsense results.

### Step 4b: Fetch Wikipedia data

**Prompt:**
> First, open each category in a browser and confirm it exists and the articles look relevant. Edit the list below.
>
> Write fetch_wiki.py that downloads article intros from English Wikipedia using the MediaWiki API with the requests library, and saves them to data/wiki_articles.jsonl.
>
> Categories and the domain label for each:
> - Category:Woodworking tools → woodworking
> - Category:Woodworking joints → woodworking
> - Category:Machining → woodworking
> - Category:Fasteners → hardware
> - Category:Sensors → electronics
> - Category:Electronic components → electronics
> - Category:Microcontrollers → electronics
> - Category:Light-emitting diodes → lighting_display
> - Category:Display technology → lighting_display
> - Category:Loudspeakers → audio
> - Category:Audio amplifiers → audio
>
> Requirements:
> - Use list=categorymembers to get pages directly in each category (pages only, no subcategories, no recursion).
> - Skip titles starting with "List of" and disambiguation pages.
> - Get the plain-text intro of each article with prop=extracts (explaintext, intro only), batching titles per request as the API allows.
> - Set a descriptive User-Agent header, as Wikimedia's API policy asks: "fab-finder (CMU 15-114 student project; [your email])".
> - Pause briefly between requests.
> - Each line in the output: {"title", "url", "category", "domain", "text"}. If the same article appears in two categories, keep it once.
> - Print how many articles came from each category and the total.
> - Add a MAX_PER_CATEGORY constant (default 80).

**What happened:** I pasted the reminder line at the top along with the prompt, but I didn't actually go check the categories in a browser first. That came back to bite me in Step 5. The script won't run until you put your contact info in the User-Agent, which Wikipedia asks for.

### Step 4c: Chunk and load into Chroma

**Prompt:**
> Write build_db.py that reads data/wiki_articles.jsonl and loads it into the collection from db.get_collection().
>
> Chunking:
> - Split each article's text into paragraphs. If a paragraph is longer than about 100 words, split it at sentence boundaries into chunks of roughly 80–100 words. Merge paragraphs shorter than about 30 words with the next one.
> - Keep at most the first 3 chunks per article.
> - Prepend the article title to each chunk's document text, like "Hole saw: <chunk text>", because the document text is what gets embedded.
>
> Loading:
> - ids must be deterministic, like "wiki::<title>::<chunk index>", and use upsert so rerunning the script doesn't create duplicates.
> - metadata: source="wikipedia", title, domain, category, url, chunk (int).
> - Add in batches of 100, print progress and elapsed time.
> - Add a --limit N command-line option so I can time a small run first.
> - At the end, print the total count in the collection.
>
> Also tell me roughly how many tokens the whole corpus will be, so I can estimate the embedding cost with text-embedding-3-small.

**What happened:** Loading 50 chunks took 1.8 seconds. The full load was 1,017 chunks (about 81,000 tokens) in 9.8 seconds. The final count was 1,017, not 1,067, so loading the first 50 again didn't create duplicates.

### Step 5: Explore results and pick a cutoff

**Prompt:**
> Write explore.py that runs these queries against the collection with n_results=5 and, for each result, prints title, domain, distance and the first 100 characters of the document:
> - "我要在木桌面中间挖一个很圆的大圆"
> - "一个能感应到有人从屏幕前走过的小零件"
> - "让声音只在屏幕前一小块地方能听到"
> - the same three queries in English
> - two queries that should match nothing, like "a recipe for chocolate cake" and "who won the 1998 world cup"
>
> Explain what cosine distance values mean here (range, lower = more similar), and help me read the output to choose a cutoff distance for "no reliable match".

**What happened:** The good queries had best distances between 0.566 and 0.672, and the two nonsense queries were at 0.770 and 0.797. So I picked **0.72** as the cutoff for "no reliable match."

Query 2 worked right away. Motion detector and the Sensor article (which mentions PIR sensors) were in the top 3. Query 1 did not. The Chinese version came back with Pencil milling, Featherboard and Wood scribe, and Hole saw wasn't even in the database.

Fixing query 1 took a few rounds of pasting output back to Claude. There turned out to be two problems.

The first was missing data. Three of my categories (Woodworking joints, Drill bits, Electronic components) had 0 articles, and Woodworking tools only had 22. Wikipedia keeps most of those articles in subcategories, and my script only looked at the top level. Also, articles come back in alphabetical order, so my limit of 80 per category cut off anything late in the alphabet. We removed the empty categories, added Saws, raised the limit to 300, and added a hand-picked list of about 50 articles our builds need, like Hole saw, Passive infrared sensor, Laser cutting, DMX512 and Directional sound. That brought the database to 830 articles and 1,622 chunks (about 130,000 tokens, loaded in 12.7 seconds). The backup query now found Directional sound first (0.547).

The second problem was how I worded the query. Even with Hole saw in the database, it only came in 10th. Claude wrote `check_query.py` to show where Hole saw ranked for different wordings:

| Wording | Hole saw rank |
|---|---|
| 我要在木桌面中间挖一个很圆的大圆 (cut a big, very round circle in a tabletop) | 10 |
| **我要在木板中间开一个圆形的洞，用来穿电线** (open a round hole in a board to run wires) | **1 (0.662)** |
| 在桌面上开一个圆口，把音箱嵌进去 (open a round opening to fit a speaker) | not in top 50 |
| a drill attachment that cuts a round opening in one go | 4 |

My first wording described the *shape* ("big," "very round") instead of what the hole is *for*. And a strong word like "speaker" pulled the results toward audio gear. I switched query 1 to the cable version, which is also closer to what we really need for the screen table. A nice surprise: the English cable query also found Cable grommet, which is exactly the part that goes in that hole.

Two smaller hiccups: a check command Claude gave me had `$in` inside double quotes, and PowerShell treated it as an empty variable, so Chroma got a blank operator (fixed by adding a backtick, `` `$in ``). And once I pasted two commands on the same line, so `fetch_wiki.py` never ran and I re-tested the old data by mistake.

### Step 6: Adding team notes

**Prompt:**
> Write notes.py with:
> - add_note(text, domain, author): adds a note to the same collection with a uuid id and metadata source="team_note", domain, author, date (today, ISO format). The note text itself is the document.
> - list_notes(): returns all notes using collection.get with a where filter on source="team_note", sorted by date.
>
> Then add a small test at the bottom (under if __name__ == "__main__") that adds one note and immediately queries for it using different wording, to prove it's searchable right away.
>
> **Check yourself:** add a note like "Laser-cut 3mm basswood at [the campus shop], clean edges, took 10 minutes", then search "去哪里切薄木板" and confirm it comes back.

**What happened:** Searching "去哪里切薄木板" (where can I cut thin wood boards?) found the English test note right away (distance 0.577). Claude also made the test delete its note at the end, so running the test doesn't leave junk in the real database.

### Step 7: Advice card

**Prompt:**
> Write advisor.py with a function advise(query) that builds a buying / fabrication advice card. I'll use the OpenAI API; the key is in .env as OPENAI_API_KEY, loaded with python-dotenv. Read the model name from an OPENAI_MODEL environment variable with a sensible small, cheap default (tell me which default you chose so I can check it against OpenAI's current model list).
>
> Steps:
> 1. Query the collection with where source="wikipedia", n_results=15.
> 2. Deduplicate by title, keeping each title's best (lowest-distance) chunk, and keep the top 4 titles.
> 3. Separately query with where source="team_note", n_results=3, and keep only notes under the distance threshold.
> 4. If the best Wikipedia result is above THRESHOLD = 0.72 and there are no good notes, return a message saying there's no reliable match and suggest rephrasing. Don't call the API in that case.
> 5. Otherwise, send the retrieved chunks and notes to the model as numbered sources, and instruct it to use ONLY those sources and to say so if they don't answer the need.
>
> The card must contain:
> - Technical name(s), in English and Chinese, with common aliases
> - A short comparison of 2–3 options (what size, precision and difficulty each suits)
> - English search keywords to paste into shopping or electronics supplier sites
> - Relevant past team experience, if any notes were retrieved
> - A source number on every point
>
> Answer in the same language as the query.
>
> After the model's answer, print a "Sources" list built by my code (not by the model): title + url for Wikipedia, author + date for notes.
>
> If the API call fails (no key, network error), print the retrieved titles and notes instead of crashing.

**What happened:** Before picking a default model, Claude checked OpenAI's current model list. Older cheap models like `gpt-4o-mini` and `gpt-4.1-mini` were already being phased out, so it used `gpt-6-luna`. The cake query correctly said "no reliable match" without calling the API.

Then I improved the card over a few rounds, pasting each one back. The first card was too thin: the model said the sources didn't include sizes or difficulty. That was because we only kept one chunk per article, and the sizes were in a different chunk. Now, after picking the top 4 articles, the app loads each one's full intro, and the next card had hole sizes (over 25 mm) and cutting depths (38, 45 and 60 mm). The "Team experience" section was also citing sources even when there were no notes, so we tightened the instructions to the model. And the source list showed articles the card never used, like Electrical discharge machining and Circle cotter. Now the code checks which numbers the card actually cites, lists those first, and puts the rest under "Also retrieved, but not used."

Then I added a real note: "Used a 2-inch hole saw on 3/4 inch plywood for cable pass-through at the campus shop; drill slowly and finish from the other side to avoid tear-out." Query 1's card used it in both the options and the team experience sections. Query 2's card suggested a motion detector, a photoelectric sensor and a PIR sensor, and was honest about where the sources didn't have enough detail.

### Step 8: Command-line menu

**Prompt:**
> Write app.py, the main entry point, with a menu loop:
>
> - Fab Finder -
> 1. Describe what you need → get an advice card
> 2. Add a team note
> 3. Show all team notes
> 4. Quit
>
> - On start, print how many items are in the database. If it's empty, tell the user to run build_db.py first and exit.
> - For "Add a team note", ask for the note text, a domain (show the five options as a numbered list), and the author's name.
> - Handle empty input and Ctrl+C gracefully.
> - Keep app.py thin: import from db.py, notes.py and advisor.py.

**What happened:** It worked end to end. I added a note, found it with different wording, quit, started the app again, and the note was still there.

### Step 9: Web page

Once everything worked, I asked about adding a front end:

> 作业可以制作frontend吗，我想做一些ui
> [Can the assignment have a front end? I want to make some UI.]

Claude said that's allowed once the main app works. It suggested Flask with one HTML page instead of Streamlit or Gradio, because those come with lots of compiled files that Windows might block again. Here's what I asked for:

> 技术选择flask加网页是可以的。极简就要，所有东西居中，我需要他非常简单。网页中间有一个选项，可以说什么。然后旁边有一些菜单，必须非常简单，清晰明了，黑白就好，字体需要美观。
> [Flask plus a web page is fine. Minimal: everything centered, I need it very simple. In the middle of the page, one input where you can say what you need. A menu on the side, which has to be very simple, clear and easy to understand. Black and white is fine; the font needs to look good.]

Claude changed `advisor.py` so the command line and the web page share the same code, then built `server.py` and `static/index.html`, checking the page with screenshots as it went. A couple of things broke along the way. The card's formatting didn't show up in Claude's test because the outside libraries it loaded from the internet were blocked there, so it wrote a small formatter into the page instead (which also means the page can't run any code hidden in the model's answer). Citations like [1][5] were showing up as "15", which got fixed to "1, 5".

On my laptop, the page first said "Failed to fetch." The server log showed an error 500 when loading the page. `index.html` wasn't in the `static` folder, so I had just opened the file directly. Claude's error handling had also turned the "not found" error into a general server error, which hid what was going on. We fixed the error handling, made the server check for the page when it starts, and made the page tell you how to start the server when it can't connect.

Then I asked for a second round of changes:

> 先调整网页，我想要roboto作为字体。另外现在的UI太挤了，add note里面能不能加一个其他类别，可以自己定义的。然后find以后的结果也是，文字感觉很拥挤，不宜读。
> [Let's adjust the page first. I want Roboto as the font. The UI is too cramped. Can "Add a note" have an "Other" category you can name yourself? And the results after Find also feel crowded and hard to read.]

The page now uses Roboto, with Noto Sans SC for Chinese since Roboto doesn't have Chinese characters. There's a lot more space everywhere, especially in the advice card, and you can pick "Other" and name your own area when adding a note, on both the web page and the command line.

**Summary of the UI requests** (Claude wrote this at the end to sum up my two messages above; I didn't send it as a prompt):
> A Flask web page for Fab Finder. Very minimal, black and white, everything centered. One big input in the middle where you say what you need, and a small, clear menu on the side (Ask, Add a note, Team notes). Roboto font with a matching Chinese font, and plenty of space so the advice card is easy to read. When adding a note, show the five areas plus "Other," which you can name yourself.


---

## One place AI got it wrong

The Wikipedia categories. The list Claude suggested in my plan looked right by name, but three of them (Woodworking joints, Drill bits, Electronic components) had no articles directly in them. And the article I needed most for query 1, Hole saw, wasn't in any of them. Nothing crashed. The script just said "0 articles," the database loaded, and query 1 quietly came back with the wrong tools. I only noticed because I ran `explore.py`, read the actual results, and then checked whether Hole saw was in the database at all. We fixed it with a hand-picked list of articles. What I learned: check that the data has what you expect before you trust the search.

There were a few smaller mistakes too. A PowerShell command had `$in` inside double quotes, so PowerShell swapped it for an empty variable. A command for checking `.env` printed my API key when the file was set up wrong, so I had to replace the key. And the Flask error handling turned a "not found" error into a server error, which hid that `index.html` was in the wrong folder.

Not the AI's fault, but just as confusing: Chroma said sentence-transformers wasn't installed, when really it was installed and Windows was blocking one of its files.
