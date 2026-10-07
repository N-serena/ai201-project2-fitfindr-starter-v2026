# FitFindr

> ### 👋 Start here
>
> **New to this repo? Read [RUNNING.md](RUNNING.md) first** — setup, every
> command, and what to do when something breaks.
>
> Once `python test.py` passes:
>
> ```bash
> python app.py listings --full -n 6      # read the data (Milestone 1)
> python app.py fields                    # what you can filter on
> python app.py ask 'vintage graphic tee under $30'
> ```
>
> All three tools are stubs, so that last command will do nothing useful yet.
> That's the starting position.
>
> **The rest of this file is your submission.** Fill it in as you go.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     HOW TO USE THIS FILE

     This is your submission. Fill each section in as you finish the milestone
     it belongs to — don't leave it all to the end.

     Unit 3 asks for the first five sections. Unit 4 adds the five below them.
     Leave the unit 4 sections alone until then; they're here so you know
     what's coming.

     Everything is pasted as TEXT. No screenshots, no images, no video links.
     A typed block of output gets full credit; a picture of the same output
     gets none.
     ───────────────────────────────────────────────────────────────────────── -->

<!-- ═══════════════════════ UNIT 3 — THE BUILD ═══════════════════════ -->

## What This Does

<!-- Three or four sentences: what a user asks for, and what they get back. -->

You describe a thrift item in plain language, such as
`vintage graphic tee under $30` or `platform sneakers size 8`. FitFindr
searches 40 secondhand listings and picks the best match. It then suggests one
or two outfits built from pieces already in your wardrobe, and writes a short
caption you could post about the find. If nothing matches, it stops before
calling the model and tells you which change would help: raising the price
ceiling, dropping the size, or using different words.

---

## Tool Inventory

<!-- Four lines per tool. This is worth 2 points and it's the single most
     common place students lose them.

     "Returns a list" earns NOTHING. The description has to say what is IN
     the list.

     The empty case isn't optional either — it's the thing your loop branches
     on, and if you don't decide it here you'll discover it as a crash in
     Milestone 5. -->

### `search_listings`

- **What it does:** Filters the 40 listings in `data/listings.json` by price
  and size, then scores each remaining listing by how many words from the
  description appear in it. A word that matches the title, `style_tags` or
  `category` scores 2. A word that matches only the `description` or `colors`
  scores 1. Common words ("a", "the", "for", "looking") are ignored. No model
  call.
- **Inputs:** `description` (str): keywords such as `"vintage graphic tee"`.
  `size` (str or None): `None` skips the size filter. `max_price` (float or
  None): an inclusive ceiling, and `None` skips the price filter.
  **Size match rule:** both sizes are lowercased and split on spaces, `/` and
  parentheses, and the word `us` is dropped. A listing matches when any of its
  size words equals any requested size word, so `M` matches `S/M` and `M/L`,
  `L` matches `L/XL` but not `XL`, `8` matches `US 8` but not `US 8.5`, `S`
  matches `S/M` but not `US 9` or `XS`, and `W30` matches `W30 L30`. A listing whose size says "One Size" matches any requested size.
- **Returns:** A `list[dict]` of at most `config.SEARCH_RESULT_LIMIT` (10)
  listing dicts, highest score first, with ties in dataset order. Each dict is
  the full listing: `id`, `title`, `description`, `category`, `style_tags`
  (list), `size`, `condition`, `price` (float), `colors` (list), `brand` (str
  or None), `platform`.
- **When it has nothing:** It returns `[]`, an empty list, never `None` and
  never an exception. That happens when the filters leave nothing or every
  remaining listing scores 0. The loop stops when it sees `[]`.

### `suggest_outfit`

- **What it does:** Asks the model for one or two outfits built around the
  thrifted item. With a wardrobe, every outfit has to name pieces the user
  already owns, by their `name`. Without one, the model gives general styling
  advice for the item: what kinds of pieces and colours go with it.
- **Inputs:** `new_item` (dict): one listing dict from `search_listings`.
  `wardrobe` (dict): has an `items` key holding a list of wardrobe-item dicts
  (`id`, `name`, `category`, `colors`, `style_tags`, `notes`), and that list
  may be empty.
- **Returns:** A non-empty `str` of plain-text outfit suggestions, a short
  paragraph or a few lines per outfit.
- **When it has nothing:** An empty `wardrobe["items"]` is not an error. It
  switches to the general-advice prompt and still returns a non-empty string.
  If the model comes back blank, it returns a fixed fallback sentence that
  names the item. A `ModelUnavailable` from `generate()` is passed up to
  `run_agent` unchanged.

### `create_fit_card`

- **What it does:** Asks the model for a short social-media caption about the
  find. It should read like a real post, mention the item's title, price and
  platform once each, and describe the vibe of the outfit.
- **Inputs:** `outfit` (str): the string `suggest_outfit` returned.
  `new_item` (dict): the same listing dict that went into `suggest_outfit`.
- **Returns:** A `str` caption of 2 to 4 sentences.
- **When it has nothing:** If `outfit` is empty or only whitespace, it returns
  `"No outfit to caption yet — run suggest_outfit for <title> first."` and
  makes no model call. If the model comes back blank, it returns a plain
  fallback caption built from the title, price and platform. A
  `ModelUnavailable` is passed up to `run_agent` unchanged.

---

## Planning Loop

<!-- Your branch rule, stated as a rule — the condition AND both paths — plus
     the file and function that holds it.

     Like this:
       "If search_listings returns an empty list, put a message in the session
        and stop. Otherwise take the first result and go to suggest_outfit."
        — agent.py::run_agent

     The grader checks your code against what you claim here, so the file and
     function have to be real. -->

**Branch rule:** If `search_listings` returns an empty list, put a message in
`session["error"]` that names what to change and return the session, without
calling `suggest_outfit` or `create_fit_card`. Otherwise take the first result
as `session["selected_item"]` and go to `suggest_outfit`.

The message is built by `agent.py::_no_results_message`. It re-runs the local
search with the price ceiling removed, then with the size removed. It suggests
whichever change would return results, and suggests different wording when
neither would.

**Where it lives:** `agent.py::run_agent`

Each time round the loop, `run_agent` increments a counter, calls
`trace.check_iterations(count)`, and runs the first step whose session field is
still empty. When every field is filled, it returns the session.

**How the query is parsed:** With a regex, in `agent.py::parse_query`.
`under / below / less than / max / up to $N` becomes `max_price` (a float).
`size X` becomes `size` (a str). Whatever is left, with commas and similar
punctuation removed, becomes `description`. The search ignores filler words
such as "looking", "for" and "in".

**What moves through the session:** in this order:

1. `query`: the user's text, as typed.
2. `parsed`: `{"description", "size", "max_price"}` from `parse_query`.
3. `search_results`: everything `search_listings` returned. If this is `[]`,
   `error` is set and the run stops here.
4. `selected_item`: `search_results[0]`.
5. `outfit_suggestion`: `suggest_outfit(selected_item, wardrobe)`.
6. `fit_card`: `create_fit_card(outfit_suggestion, selected_item)`.

`wardrobe` is set when the session is created and only read after that.
`error` stays `None` on a full run.

---

## Sample Run

<!-- Two things go here.

     1. One FULL query and its output, pasted as text.
     2. Your three per-tool terminal tests — the command and what it printed. -->

**One full query**

```
$ python app.py ask 'vintage graphic tee under $30'

  Found:    Y2K Baby Tee — Butterfly Print — $18.0 on depop

  Outfit:   Outfit 1: Y2K Baby Tee — Butterfly Print paired with Baggy straight-leg jeans, dark wash, Chunky white sneakers, and Black cropped zip hoodie. This outfit works because the fitted baby tee balances the loose jeans while the cropped hoodie adds a true early 2000s silhouette.

Outfit 2: Y2K Baby Tee — Butterfly Print paired with Wide-leg khaki trousers, Chunky white sneakers, and Vintage black denim jacket. This outfit works because it blends casual streetwear with a soft vintage aesthetic, letting the butterfly graphic stand out against the neutral bottoms.

  Fit card: Scored this little butterfly tee on depop for $18 and I am obsessed. I’ve been living in it layered under my black cropped zip hoodie with baggy dark wash jeans for that ultimate early 2000s silhouette. It also looks so good dressed down with khaki trousers and a vintage denim jacket when I want a softer streetwear vibe.

0 model calls this session, 2 served from cache
```

The cache line means both answers were reused from the first real run of this
same query.

The empty-search path, for comparison:

```
$ python app.py ask 'designer ballgown size XXS under $5'

  Nothing matched 'designer ballgown' in size XXS under $5. Try to describe the item with a category or style word like 'jacket', 'jeans', 'tee', 'y2k' or 'vintage'.

0 model calls this session
```

**The three tools, tested one at a time**

```
$ python -c "from tools import search_listings; print(search_listings('graphic tee', max_price=30))"
[{'id': 'lst_002', 'title': 'Y2K Baby Tee — Butterfly Print', 'description': 'Super cute early 2000s baby tee with butterfly graphic. Fitted crop length. Tag says medium but fits like a small.', 'category': 'tops', 'style_tags': ['y2k', 'vintage', 'graphic tee', 'cottagecore'], 'size': 'S/M', 'condition': 'excellent', 'price': 18.0, 'colors': ['white', 'pink', 'purple'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_006', 'title': 'Graphic Tee — 2003 Tour Bootleg Style', 'description': 'Vintage-style bootleg tee with faded graphic. Slightly boxy fit. 100% cotton, soft and worn-in.', 'category': 'tops', 'style_tags': ['graphic tee', 'vintage', 'grunge', 'streetwear', 'band tee'], 'size': 'L', 'condition': 'good', 'price': 24.0, 'colors': ['black'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_033', 'title': 'Vintage Band Tee — Faded Grey', 'description': 'Faded grey band-style tee with distressed graphic. Crew neck. Fits boxy. Well-loved but no holes or major damage.', 'category': 'tops', 'style_tags': ['vintage', 'grunge', 'band tee', 'graphic tee', 'streetwear'], 'size': 'L', 'condition': 'fair', 'price': 19.0, 'colors': ['grey', 'charcoal'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_015', 'title': 'Vintage Graphic Hoodie — Faded Black', 'description': 'Faded black pullover hoodie with barely-visible vintage graphic on the chest. Cozy interior. Some pilling but adds to the worn-in look.', 'category': 'tops', 'style_tags': ['vintage', 'grunge', 'graphic', 'streetwear'], 'size': 'L', 'condition': 'fair', 'price': 26.0, 'colors': ['black', 'charcoal'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_017', 'title': 'Mesh Long-Sleeve Top — Black', 'description': 'Sheer black mesh long-sleeve. Great for layering under a graphic tee or over a bralette. Stretchy material, fits true to size.', 'category': 'tops', 'style_tags': ['y2k', 'grunge', 'goth', 'layering'], 'size': 'S/M', 'condition': 'excellent', 'price': 15.0, 'colors': ['black'], 'brand': None, 'platform': 'depop'}]
```

```
$ python -c "from tools import suggest_outfit; from utils.data_loader import get_example_wardrobe, load_listings; print(suggest_outfit(load_listings()[0], get_example_wardrobe()))"
Outfit One: Pair the Vintage Levi's 501 Jeans with the White ribbed tank top, the Vintage black denim jacket, and the Chunky white sneakers, accented with the Brown leather belt. This outfit works because the fitted tank and cropped jacket balance the straight-leg denim for an easy, classic casual look.

Outfit Two: Style the Vintage Levi's 501 Jeans with the Oversized grey crewneck sweatshirt and the Black combat boots, wearing the Brown leather belt. This outfit works because the slouchy, oversized sweatshirt contrasts nicely with the structured mid-rise denim and rugged boots for effortless streetwear style.
```

```
$ python -c "from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card('jeans and white sneakers', load_listings()[0]))"
Scored these vintage 501s on depop for $38 and I'm obsessed with the natural fade at the knees. They’ve got that exact worn-in indigo wash I’ve been hunting for. Just keeping it simple today with crisp white sneakers for that easy streetwear look.
```

---

## How I Used AI

<!-- Two specific moments. What you asked, what came back, what you changed.

     "I used Claude to help me code" is not enough.

     "I gave Claude my search_listings spec. It returned None on no match
     instead of an empty list, so I changed it" is the level we want. -->

**Moment 1**

- *What I asked for:* I asked Claude (Claude Code) to build `search_listings`
  from my Tool Inventory spec: word-for-word size matching, weighted keyword
  scoring, and `[]` when nothing matches.
- *What came back:* A working search that passed every size example in my spec
  (`L` doesn't match `XL`, `8` doesn't match `US 8.5`). It also showed two
  side effects of the spec. Almost every listing is tagged `vintage`, so
  `vintage graphic tee` fills all 10 result slots with a belt and denim shorts
  included. And "One Size" listings leak into sized searches: `90s track
  jacket` in size M also returns a One Size bucket hat.
- *What I changed:* Nothing in the code. I kept both behaviours on purpose.
  The agent only uses the top result, and the real matches always ranked
  first (the Y2K Baby Tee and the Graphic Tee for `graphic tee`, the Track
  Jacket for `90s track jacket`). Changing the scoring to fix the padding
  wasn't worth the risk to criterion 1. I wrote both side effects down so I
  know where to look in unit 4 if a search picks the wrong item.

**Moment 2**

- *What I asked for:* `create_fit_card`, with the price written exactly as
  `$24`, so criterion 4 can check it. I asked for the same input to be run
  three times with the cache off.
- *What came back:* Three different captions, each with 3 sentences, `$24`
  and `depop`. But two of the three opened with nearly the same words,
  "Scored this … tour tee on depop for $24".
- *What I changed:* I kept the prompt as it is. The three first sentences were
  still different, so it passes criterion 4 as written, and changing the
  prompt now would mean tuning it before the unit 4 run log measures it. I
  noted the repeated "Scored this…" opener as the most likely way criterion 4
  misses, so if two of the five unit 4 cards share a first sentence, the
  `create_fit_card` prompt is the first thing to fix.

**Moment 3 (unit 4)**

- *What I asked for:* Claude scored the before run and wrote the diagnosis,
  using a small script to count sentences, check prices and platforms, and
  match outfit text against the 10 wardrobe names.
- *What came back:* Correct verdicts, but two wrong numbers in the first
  draft of the diagnosis. It said "22 of 25 cards" open with "Scored this…",
  but the impossible-query scenario makes no cards, so the real count is 18
  of 20. It also said the white tank was paired with "trousers or jeans"; it
  was trousers every time.
- *What I changed:* Every number in the diagnosis was re-counted against the
  results file with `grep` before it went in, and both were corrected.

**Moment 4 (unit 4)**

- *What I asked for:* A prompt fix for the criterion 5 miss, where the model
  kept naming "white ribbed tank top".
- *What came back:* The first draft of the new instruction listed the exact
  failing phrases as things not to say ("not 'white ribbed tank top', 'black
  combat boots'"). That would have passed the check by teaching the prompt
  the test's answer, not by fixing why the model reached for fully specified
  basics.
- *What I changed:* The named examples came out before anything was run. The
  instruction states the general rule instead: describe pieces by role, shape
  and colour family, and never spell out one exact garment. No wardrobe item
  is named anywhere in the prompt.

<!-- ═══════════════════════ UNIT 4 — THE TEST ═══════════════════════

     Don't fill these in during unit 3.
     ═══════════════════════════════════════════════════════════════════ -->

---

## Run Log — Before

<!-- Five criteria, five tries each, in this exact format.

     Five, because your criteria are written out of five. Mark each try PASS
     or FAIL, count the passes, and read that count against your target — a
     row targeting 4 of 5 with three PASS cells is MISSED (3/5).

     `python run_eval.py --label before` runs everything and writes the table
     into results/. Paste it here and fill in the verdicts. -->

From `results/run_2026-10-07_1738_before.md`: 5 tries per scenario, cache
off, temperature 0.9, 40 model calls.

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1. A matching query completes all three tools | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 2. An impossible query stops before the second tool | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 3. The searched item is the item every later tool receives | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 4. The fit card is a postable caption that gets the facts right | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 5. An empty wardrobe gets advice, not invented clothes | 4 of 5 | PASS | FAIL | FAIL | FAIL | FAIL | MISSED (1/5) |

How each try was scored:

- **1:** the session has no `error` and a non-empty `fit_card`, and the trace
  shows all five steps.
- **2:** the session `error` is set and names a change ("describe the item
  with a category or style word…"). The trace stops after
  `search_listings (via MCP)`, so `suggest_outfit` never ran.
- **3:** in the trace, `search_listings` returned 90s Track Jacket first, and
  `select_item`, `suggest_outfit` and `create_fit_card` all show `lst_004`.
- **4:** every card is 3 sentences and contains `$24` and `depop`. The five
  first sentences are all different.
- **5:** no outfit claims the user owns anything (no "your", "you already
  have" or "from your closet"). But tries 2–5 each contain "white ribbed tank
  top", which is word-for-word the name of example-wardrobe item `w_003`
  ("White ribbed tank top"). Only try 1 names none of the 10 items.

**Real output from one try**, pasted as text. This is criterion 5, try 2,
produced by `agent.py::run_agent` under `run_eval.py::main`, with the outfit
text from `tools.py::suggest_outfit`:

```
- stopped early: no
- selected_item: Denim Jacket — Light Wash, Cropped ($42.0, poshmark)
- search_results: 6

Outfit suggestion:

A light wash cropped Wrangler denim jacket is a versatile layering staple. For a balanced vintage streetwear look, pair it with high-waisted wide-leg black trousers and a fitted white ribbed tank top, finished off with retro sneakers. Alternatively, lean into double denim by styling the jacket over a black midi slip dress, adding chunky dark brown leather boots and a matching shoulder bag. Both outfits play with proportions since the jacket is cropped, and the neutral base colors let the light blue wash stand out.

Fit card:

Scored this vintage Wrangler denim jacket on Poshmark for $42 and I'm obsessed with the structured shoulders. Tossed it on over a white ribbed tank and black wide-leg trousers for a chill streetwear vibe. Can't decide if I want to add pins to it or just leave it as a blank canvas.

Trace:

[1] parse_query
      in:  denim jacket under $50
      out: {'description': 'denim jacket', 'size': None, 'max_price': 50.0}
[2] search_listings (via MCP)
      in:  description='denim jacket', size=None, max_price=50.0
      out: 6 items: Denim Jacket — Light Wash, Cropped, Vintage Levi's 501 Jeans — Medium Wash, 90s Track Jacket — Navy/White Stripe … +3 more
      →    branch: 6 results, continuing
[3] select_item
      out: lst_007 Denim Jacket — Light Wash, Cropped
[4] suggest_outfit
      in:  new_item=lst_007 Denim Jacket — Light Wash, Cropped, wardrobe=0 items
      out: A light wash cropped Wrangler denim jacket is a versatile layering staple. For a balanced vintage streetwear l…
[5] create_fit_card
      in:  new_item=lst_007 Denim Jacket — Light Wash, Cropped, outfit=519 chars
      out: Scored this vintage Wrangler denim jacket on Poshmark for $42 and I'm obsessed with the structured shoulders. …
```

---

## Verdicts and Diagnoses

<!-- MET or MISSED per criterion against LAST UNIT's target, plus a sentence on
     how you decided.

     Then, for every miss: which of the four places it happened — a tool, the
     loop's branch, the session, or the model's output — AND the mechanism.

     Not a diagnosis:  "The fit card was bad."
     A diagnosis:      "The fit card criterion missed on 2 of 5 items. Both had
                        an empty brand field. My prompt puts the brand in the
                        first sentence, so the card opened with a blank and read
                        like a fragment. The tool worked; the prompt assumed a
                        field that isn't always there."

     Look for a pattern. Three misses on the same tool is one problem, not
     three. -->

| # | Criterion | Target | Verdict | How I decided |
|---|---|---|---|---|
| 1 | A matching query completes all three tools | 4 of 5 | MET (5/5) | Every try ended with `error` None, a fit card, and a 5-step trace. |
| 2 | An impossible query stops before the second tool | 5 of 5 | MET (5/5) | Every trace stops at step 2 with "branch: empty, stopping before suggest_outfit". The error names a change, and the run made 0 model calls. |
| 3 | The searched item is the item every later tool receives | 5 of 5 | MET (5/5) | `lst_004` is first in the search result and is the item in `select_item`, `suggest_outfit` and `create_fit_card`, in all 5 traces. |
| 4 | The fit card is a postable caption that gets the facts right | 4 of 5 | MET (5/5) | Each card has 3 sentences and contains `$24` and `depop`. All 5 first sentences differ. I counted sentences and checked the price and platform with a script, and read each card. |
| 5 | An empty wardrobe gets advice, not invented clothes | 4 of 5 | MISSED (1/5) | No try claimed ownership, but tries 2–5 each name "white ribbed tank top", the exact name of example item `w_003`. The criterion says "names none of the 10 items", so those four fail. |

**Diagnoses**

**Criterion 5 (missed, 1/5).** Place: **the model's output**, shaped by the
empty-wardrobe prompt in `tools.py::suggest_outfit`.

The rest of the path was correct in every try. The trace shows
`suggest_outfit` received `wardrobe=0 items`, so the empty branch ran, and the
session carried `lst_007` throughout. The tool, the branch and the session are
all fine.

The mechanism is in the prompt. It forbids ownership language ("your", "you
already have") but says nothing about which pieces to suggest. Asked for
"kinds of pieces and colours", the model reaches for the most generic basic
there is, a white ribbed tank top. The example wardrobe is built from those
same basics, so the generic suggestion collides with an item name word for
word.

This is one problem, not four. All four failures are the same phrase and the
same item (`w_003`), and every time the tank was paired with black
trousers. The model did not invent ownership: no try says the user
owns anything. So the miss is real against the criterion as written, but the
check is broader than the failure I meant to catch. That's worth fixing in
the prompt and worth knowing about the criterion.

**A pattern in a criterion I met (4).** Criterion 4 passed on its own
scenario, but the cards from the other scenarios show what it doesn't catch.
18 of the 20 cards across the whole run open with "Scored this … on
<platform> for $<price>". In the criterion 1 scenario, three of the five
cards have a word-for-word identical first sentence ("Scored this little
butterfly baby tee on depop for $18 and I am obsessed."). That is the
`create_fit_card` prompt. It asks for the price and platform in a casual
first-person voice, and "Scored this X on Y for $Z" is the model's default
shape for that. The criterion was met, so no fix is owed, but I note it under
What's Still Broken.


---

## Loop Trace

<!-- One full run, printed step by step, with the MCP call visible in it.

     `python app.py ask '...' --trace` once you've added the trace.step()
     calls in Milestone 2.

     Worth pasting BOTH the happy path and the empty-search path. The empty
     one should be visibly shorter, because it stops. If your two traces are
     the same length, your branch isn't working — and this is the fastest way
     anyone will ever find that out. -->

**Happy path**

```
$ python app.py ask '90s track jacket in size M' --trace
[1] parse_query
      in:  90s track jacket in size M
      out: {'description': '90s track jacket in', 'size': 'M', 'max_price': None}
[2] search_listings (via MCP)
      in:  description='90s track jacket in', size='M', max_price=None
      out: 4 items: 90s Track Jacket — Navy/White Stripe, 90s Silk Slip Dress — Floral, Midi Length, 90s Leather Bomber — Black … +1 more
      →    branch: 4 results, continuing
[3] select_item
      out: lst_004 90s Track Jacket — Navy/White Stripe
[4] suggest_outfit
      in:  new_item=lst_004 90s Track Jacket — Navy/White Stripe, wardrobe=10 items
      out: Outfit One: Pair the 90s Track Jacket with the white ribbed tank top, baggy straight-leg jeans, and chunky whi…
[5] create_fit_card
      in:  new_item=lst_004 90s Track Jacket — Navy/White Stripe, outfit=505 chars
      out: Scored this vintage Champion track jacket on Poshmark for $45 and it’s basically my new uniform. It’s the ulti…

  Found:    90s Track Jacket — Navy/White Stripe — $45.0 on poshmark

  Outfit:   Outfit One: Pair the 90s Track Jacket with the white ribbed tank top, baggy straight-leg jeans, and chunky white sneakers. This look works because it leans into classic 90s athletic streetwear using effortless, casual layering.

Outfit Two: Layer the 90s Track Jacket over the black cropped zip hoodie, combined with the wide-leg khaki trousers and black combat boots. This outfit works because mixing the sporty navy jacket with tailored trousers and edgy boots creates a balanced, high-low street style.

  Fit card: Scored this vintage Champion track jacket on Poshmark for $45 and it’s basically my new uniform. It’s the ultimate 90s athletic layer whether I'm keeping it casual with baggy denim or mixing it with tailored trousers and combat boots for that high-low streetwear vibe. Either way, the sleeve stripes do all the work.

2 model calls this session, 649 prompt + 179 output tokens
```

**Empty search**

```
$ python app.py ask 'platform sneakers size 8 under $20' --trace
[1] parse_query
      in:  platform sneakers size 8 under $20
      out: {'description': 'platform sneakers', 'size': '8', 'max_price': 20.0}
[2] search_listings (via MCP)
      in:  description='platform sneakers', size='8', max_price=20.0
      out: [] (empty)
      →    branch: empty, stopping before suggest_outfit

  Nothing matched 'platform sneakers' in size 8 under $20. Try to raise the price ceiling above $20 or drop the size 8.

0 model calls this session
```

Two steps instead of five, and no model calls. The platform sneakers exist
in size 8 but cost $48, so the message points at the price ceiling.

This trace is from the required unit 4 agent. Since stretch feature 1, an
empty search that named a size retries once without it, so this exact query
now finds canvas sneakers in another size. The current traces are under
**Stretch Features**.

**The other two failure modes**

The model can't be reached. This run used a deliberately wrong key, set for
this one command only; `.env` was untouched, and the cache was off:

```
$ AI201_CACHE=0 GEMINI_API_KEY=AIzaBADKEY... python app.py ask 'denim jacket under $50' --trace
[1] parse_query
      in:  denim jacket under $50
      out: {'description': 'denim jacket', 'size': None, 'max_price': 50.0}
[2] search_listings (via MCP)
      in:  description='denim jacket', size=None, max_price=50.0
      out: 6 items: Denim Jacket — Light Wash, Cropped, Vintage Levi's 501 Jeans — Medium Wash, 90s Track Jacket — Navy/White Stripe … +3 more
      →    branch: 6 results, continuing
[3] select_item
      out: lst_007 Denim Jacket — Light Wash, Cropped
[4] model unavailable
      out: The model rejected your API key. Check GEMINI_API_KEY in your .env file, or create a fresh key at aistudio.goo…
      →    stopping, error set in session

  The model rejected your API key. Check GEMINI_API_KEY in your .env file, or create a fresh key at aistudio.google.com. The search still worked — it found Denim Jacket — Light Wash, Cropped ($42 on poshmark).

1 model calls this session
```

`agent.py::run_agent` catches `ModelUnavailable`, puts the message in
`session["error"]` and returns, so the user sees a message, not a stack
trace.

Empty wardrobe: `python app.py ask '...' --empty-wardrobe`, and the
`empty wardrobe` scenario in both run logs. The trace shows `wardrobe=0
items` going into `suggest_outfit`, and it returns general advice. That
path is criterion 5.

**On the MCP move:** `search_listings` is registered in `mcp_server.py` with
a description written for a caller who can't see the code. It gives the size
rule, the price as inclusive US dollars, every field of a listing, and `[]`
when nothing matches. `agent.py` no longer imports the search function. Its
`search_listings` wrapper calls `mcp_client.call_tool("search_listings",
...)`, and the main search and both re-runs in `_no_results_message` go
through it.

Nothing behaved differently afterwards. I compared direct and MCP results on
five queries, two of them empty, and all five were identical. The empty case
came back as a real `[]`, not `None` or a JSON string, so the branch kept
working unchanged. The only difference is speed. Each call starts the server
as a new process, so an empty search with its two diagnostic re-runs makes
three MCP calls, and `python agent.py` takes about 4 seconds.

---

## The Improvement

<!-- What you changed, why your diagnosis pointed at it, and the after-run in
     the same table format. One change, measured properly.

     `python run_eval.py --label after` -->

**What I changed:** One instruction in the empty-wardrobe prompt in
`tools.py::suggest_outfit`. The old prompt asked for outfits "described by
kinds of pieces and colours (for example 'straight-leg dark jeans')". The new
one asks for each piece by its role, shape and colour family ("a fitted top in
a light neutral", "dark, relaxed trousers"). It also says never to spell out
one exact garment with fabric, cut and colour all together, because that reads
like an item the person owns. Only the thrifted piece gets full detail. I
didn't name any wardrobe item in the prompt, so the fix targets the mechanism
and not the four words the check looks for. Nothing else changed: the
filled-wardrobe prompt, the fit card, the loop and the search are untouched.

**Which failure it was meant to fix:** Criterion 5, missed 1/5. The diagnosis
put it in the model's output. The empty-wardrobe prompt let the model pick a
fully specified everyday basic ("fitted white ribbed tank top"), which matched
example item `w_003` word for word.

### Run Log — After

From `results/run_2026-10-07_1757_after.md`: same five scenarios, 5 tries
each, cache off, 40 model calls.

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1. A matching query completes all three tools | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 2. An impossible query stops before the second tool | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 3. The searched item is the item every later tool receives | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 4. The fit card is a postable caption that gets the facts right | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 5. An empty wardrobe gets advice, not invented clothes | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |

**Did it help, and how do I know:** Yes for criterion 5, which went from 1/5
to 5/5. I checked every outfit against the 10 example-wardrobe names, and none
appear in any of the five tries. Before, four tries contained "white ribbed
tank top". The tops now read "a fitted ribbed top", "a fitted top in a light
neutral" and "a fitted top in a dark neutral".

One try needed a judgement call. Try 5 contains "your", in "depending on your
preferred daily aesthetic". That refers to the user's taste, not to something
they own, so I scored it PASS.

Criteria 1–4 stayed at 5/5, so the change didn't break the other paths. That
is expected, since only the empty-wardrobe branch's prompt changed.

The cost: the advice got vaguer. Try 5 suggests "a fluid, wide-bottom piece
in a dark neutral", which is harder to shop for than "black wide-leg
trousers". Try 5 also opened with the price spelled out ("At forty-two
dollars…"), which the outfit prompt never asked for. So the fix traded some
usefulness for the guarantee. And five tries is a small sample, so I'd want
more runs before calling the white-tank collision gone for good.

---

## What's Still Broken

<!-- For each criterion still missed: what you'd do, and why you stopped where
     you did. "I ran out of time" is fine if it's true. Pretending nothing is
     left is not. -->

No criterion is missed after the improvement. Here is what is still wrong
or untested.

- **The fit cards all sound alike.** 18 of the 20 cards in the after run
  open with "Scored this … on <platform> for $<price>". Criterion 4 passes
  because it only checks for identical first sentences, and the wording
  varies just enough. In the before run, three cards in the criterion 1
  scenario did share an identical first sentence. Next I would revise
  criterion 4 to "no two of five cards share their first four words". That
  would miss today, and I would fix it in the `create_fit_card` prompt by
  asking for a different opening, such as the vibe or the outfit, not the
  purchase. I stopped because unit 4 allows one improvement, and criterion 5
  was the actual miss.
- **Empty-wardrobe advice got vaguer.** The fix traded usefulness for the
  guarantee. "A fluid, wide-bottom piece in a dark neutral" is harder to shop
  for than "black wide-leg trousers". The criterion has no measure of
  usefulness, so a too-vague answer would still pass. I would add one.
- **Criterion 5's name check is broader than the failure it is meant to
  catch.** It flags any generic phrase that happens to match a wardrobe item,
  even when nothing claims ownership. It passed 5/5 after the fix, but five
  tries is a small sample, and "white ribbed tank top" could still come back.
- **The search pads results.** Almost every listing is tagged `vintage`, so
  `vintage …` queries fill all 10 slots, and "One Size" items show up in
  sized searches. The agent only uses the top result, and the right item
  ranked first in every run, so this hasn't caused a miss yet.
- **The query parser keeps filler words.** `'90s track jacket in size M'`
  leaves `'90s track jacket in'` as the description. The search's stopwords
  remove "in", so results are right, but the parsed field is untidy.
- **The bad-key path isn't in `scenarios.py`.** It needs a different
  environment, so it was triggered by hand once (above) and not run five
  times.

---

## Stretch Features

Declared here before any of them were built. The required unit 4 work above,
including both run logs, was finished first. These go beyond the "MCP move
plus one improvement" rule on purpose, and each one is written up below as
it lands.

1. **Retry with looser constraints.** When a search comes back empty and the
   query named a size, `run_agent` retries once without the size. If that
   finds something, the run continues and the session records what was
   dropped, so the user sees "no M in stock — showing other sizes". If the
   retry is also empty, it stops as before. The criterion 2 query (ballgown,
   XXS, under $5) is still empty without the size, so criterion 2's path is
   unchanged.
2. **A second tool on MCP: `create_fit_card`.** It is registered in
   `mcp_server.py` next to `search_listings` and called through `call_tool`.
   Two things to check: a model failure inside the server reaches the agent as
   an `MCPError`, not a `ModelUnavailable`, so the bad-key handler has to still
   work. And `generate.py`'s rate limiter counts per process, while every MCP
   call is a new process.
3. **A second improvement: the fit-card opener.** 18 of 20 cards in the after
   run open with "Scored this…". First criterion 4 is revised underneath the
   original in `criteria.md`, because it measured the wrong thing, and both
   existing run logs are re-scored against it. Then the `create_fit_card`
   prompt is changed and measured with `run_eval.py --label after2` in the
   same table format.

**Results**

**1. Retry with looser constraints — done.** In `agent.py::run_agent`, the
search step checks for an empty result with a size set. If it finds one, it
records `session["dropped"] = {"size": ...}` and goes round the loop once more.
The next pass searches with `size=None`. If that finds something,
`session["notice"]` says what was dropped and what size the item actually is,
and `app.py` prints it above the result. If the retry is also empty, the run
stops as before, and the message says the retry already happened. It only
retries once, because the retry only runs while `session["dropped"]` is unset.

The size was the only thing in the way:

```
$ python app.py ask 'denim jacket size XL' --trace
[1] parse_query
      in:  denim jacket size XL
      out: {'description': 'denim jacket', 'size': 'XL', 'max_price': None}
[2] search_listings (via MCP)
      in:  description='denim jacket', size='XL', max_price=None
      out: [] (empty)
      →    branch: empty, retrying once without size XL
[3] search_listings (via MCP)
      in:  description='denim jacket', size=None, max_price=None
      out: 6 items: Denim Jacket — Light Wash, Cropped, Vintage Levi's 501 Jeans — Medium Wash, 90s Track Jacket — Navy/White Stripe … +3 more
      →    branch: 6 results, continuing
[4] select_item
      out: lst_007 Denim Jacket — Light Wash, Cropped
[5] suggest_outfit
      in:  new_item=lst_007 Denim Jacket — Light Wash, Cropped, wardrobe=10 items
      out: Outfit one combines the Wrangler denim jacket, white ribbed tank top, baggy straight-leg jeans, brown leather …
[6] create_fit_card
      in:  new_item=lst_007 Denim Jacket — Light Wash, Cropped, outfit=610 chars
      out: Scored this vintage Wrangler denim jacket on Poshmark for $42 and I am obsessed with the structured shoulders.…

  Note:     Nothing in size XL, so I dropped the size filter. This one is size S.
  Found:    Denim Jacket — Light Wash, Cropped — $42.0 on poshmark
```

The criterion 2 query is still impossible after the retry, so it stops with
no model calls:

```
$ python app.py ask 'designer ballgown size XXS under $5' --trace
[1] parse_query
      in:  designer ballgown size XXS under $5
      out: {'description': 'designer ballgown', 'size': 'XXS', 'max_price': 5.0}
[2] search_listings (via MCP)
      in:  description='designer ballgown', size='XXS', max_price=5.0
      out: [] (empty)
      →    branch: empty, retrying once without size XXS
[3] search_listings (via MCP)
      in:  description='designer ballgown', size=None, max_price=5.0
      out: [] (empty)
      →    branch: empty, stopping before suggest_outfit

  Nothing matched 'designer ballgown' in size XXS under $5. Try to describe the item with a category or style word like 'jacket', 'jeans', 'tee', 'y2k' or 'vintage'. (Already retried without size XXS.)

0 model calls this session
```

What it gets wrong: dropping the size can change *what* is found, not just
its size. `platform sneakers size 8 under $20` now returns the Low-Top
Canvas Sneakers (US 9, $20). They match on "sneakers" but are not platforms,
because the real platform sneakers cost $48 and the price ceiling still
applies. The notice is honest about the size but says nothing about the
weaker match. A fix would be to only accept a retry result that scores as
well as a sized match would have.

**2. A second tool on MCP — done.** `create_fit_card` is registered in
`mcp_server.py`, with a description that states its inputs, the
empty-outfit case and what happens when the model can't be reached.
`agent.py::create_fit_card` calls it through `call_tool`, and its trace step
is now `create_fit_card (via MCP)`. `python mcp_client.py` lists both tools.

Unlike the search move, this one did not behave the same afterwards. Testing
it turned up two real bugs:

- **The eval would have quietly re-used cached cards.** `run_eval.py` turns
  the cache off with `config.CACHE_ENABLED = False`, but only in the agent's
  process. The MCP stdio client starts the server with a short list of system
  variables, and the server reads `.env` itself, so its cache stayed on. With
  the cache "off", three calls through MCP for the same item returned the
  identical card:

  ```
  via MCP, cache off in the agent:
     Scored this washed burgundy henley on thredUp for only $16 and the cotton is alr
     Scored this washed burgundy henley on thredUp for only $16 and the cotton is alr
     Scored this washed burgundy henley on thredUp for only $16 and the cotton is alr
  ```

  That would have made criterion 4's "five different first sentences" check
  measure the cache, not the model. The fix is in `mcp_client.py::_server_env`,
  which passes `AI201_CACHE` (and any `GEMINI_API_KEY` / `AI201_MODEL` set for
  the command) to the server. After the fix, the same test gave three
  different cards.

- **A model failure inside the server lost its reason.** The server reported
  "The model rejected your API key…", but the agent saw "unhandled errors in a
  TaskGroup (1 sub-exception)". The stdio client's task group wraps the
  `MCPError` that `call_tool` raises inside it in an `ExceptionGroup`, so
  `except MCPError` never matched. `mcp_client.py::_find_mcp_error` now
  unwraps it. `agent.py::run_agent` catches `MCPError` and says which step
  failed and what still worked.

The error path was forced by stubbing `suggest_outfit`, so that only the
server would hit the bad key:

```
[4] suggest_outfit
      in:  new_item=lst_002 Y2K Baby Tee — Butterfly Print, wardrobe=10 items
      out: Tucked into baggy dark-wash jeans with chunky white sneakers.
[5] MCP call failed
      out: The model rejected your API key. Check GEMINI_API_KEY in your .env file, or create a fresh key at aistudio.goo…
      →    stopping, error set in session

error: The fit card couldn't be written: The model rejected your API key. Check GEMINI_API_KEY in your .env file, or create a fresh key at aistudio.google.com. The search and outfit still worked — it found Y2K Baby Tee — Butterfly Print ($18 on depop), and the outfit suggestion is in the session.
```

What is still off:

- **The call counter undercounts.** A full run that made two model calls
  prints "1 model calls this session", because the fit card's call happens in
  the server's process and `generate.py` counts per process.
- **Pacing is per process too.** The rate limiter in the agent never sees the
  fit-card calls, so a back-to-back eval can go over 15 requests a minute.
  `generate.py`'s retry-with-backoff on a 429 is what catches it; the
  `after2` run in stretch 3 is the test of that.

<!-- ═════════════════════════════════════════════════════════════════════

     SUBMISSION CHECKLIST — unit 3

       [x] criteria.md has five numbered criteria, each with a target
       [x] Each criterion has a reason underneath it
       [x] All five unit 3 sections above have real content
       [x] Tool Inventory: all three tools, inputs WITH TYPES, a specific
           return value, and the empty case
       [x] Planning Loop names the branch rule and agent.py::run_agent
       [x] Sample Run: one full query plus the three per-tool tests, as text
       [x] At least four new commits
       [ ] Repository URL submitted — WRITE IT DOWN, you submit the same one
           next unit

     SUBMISSION CHECKLIST — unit 4

       [x] mcp_server.py exists with one tool registered
           (or a written record of exactly where the rewire broke)
       [x] Run Log — Before, five criteria, five tries each
       [x] Real output pasted underneath, naming file and function
       [x] A verdict on every criterion
       [x] A diagnosis for every miss, naming a place AND a mechanism
       [x] Loop Trace, with the MCP call visible in it
       [x] All three failure modes triggered and handled
       [x] One improvement, with Run Log — After in the same format
       [x] What's Still Broken
       [x] At least four new commits
       [ ] The SAME repository URL as last unit

     Do not delete and recreate this repository. Your commit history is what
     shows your criteria existed before your results did.
     ═════════════════════════════════════════════════════════════════════ -->

---

📖 **How to run this project: [RUNNING.md](RUNNING.md)**
