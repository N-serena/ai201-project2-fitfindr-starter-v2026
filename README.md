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

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |  |  |
| 2.  |  |  |  |  |  |  |  |
| 3.  |  |  |  |  |  |  |  |
| 4.  |  |  |  |  |  |  |  |
| 5.  |  |  |  |  |  |  |  |

**Real output from one try**, pasted as text, naming the file and function
that produced it:

```

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
| 1 |  |  |  |  |
| 2 |  |  |  |  |
| 3 |  |  |  |  |
| 4 |  |  |  |  |
| 5 |  |  |  |  |

**Diagnoses**



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

```

**Empty search**

```

```

**On the MCP move:** <!-- what changed in your code, and whether anything
behaved differently afterwards. If the rewire didn't work, say exactly where it
broke — the error text and the last thing that worked. That earns the point in
full. -->



---

## The Improvement

<!-- What you changed, why your diagnosis pointed at it, and the after-run in
     the same table format. One change, measured properly.

     `python run_eval.py --label after` -->

**What I changed:**

**Which failure it was meant to fix:**

### Run Log — After

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |  |  |
| 2.  |  |  |  |  |  |  |  |
| 3.  |  |  |  |  |  |  |  |
| 4.  |  |  |  |  |  |  |  |
| 5.  |  |  |  |  |  |  |  |

**Did it help, and how do I know:**

<!-- If it made things worse, say that. Honestly reported, that earns full
     credit and is more interesting than one that worked. -->



---

## What's Still Broken

<!-- For each criterion still missed: what you'd do, and why you stopped where
     you did. "I ran out of time" is fine if it's true. Pretending nothing is
     left is not. -->



<!-- ═════════════════════════════════════════════════════════════════════

     SUBMISSION CHECKLIST — unit 3

       [ ] criteria.md has five numbered criteria, each with a target
       [ ] Each criterion has a reason underneath it
       [ ] All five unit 3 sections above have real content
       [ ] Tool Inventory: all three tools, inputs WITH TYPES, a specific
           return value, and the empty case
       [ ] Planning Loop names the branch rule and agent.py::run_agent
       [ ] Sample Run: one full query plus the three per-tool tests, as text
       [ ] At least four new commits
       [ ] Repository URL submitted — WRITE IT DOWN, you submit the same one
           next unit

     SUBMISSION CHECKLIST — unit 4

       [ ] mcp_server.py exists with one tool registered
           (or a written record of exactly where the rewire broke)
       [ ] Run Log — Before, five criteria, five tries each
       [ ] Real output pasted underneath, naming file and function
       [ ] A verdict on every criterion
       [ ] A diagnosis for every miss, naming a place AND a mechanism
       [ ] Loop Trace, with the MCP call visible in it
       [ ] All three failure modes triggered and handled
       [ ] One improvement, with Run Log — After in the same format
       [ ] What's Still Broken
       [ ] At least four new commits
       [ ] The SAME repository URL as last unit

     Do not delete and recreate this repository. Your commit history is what
     shows your criteria existed before your results did.
     ═════════════════════════════════════════════════════════════════════ -->

---

📖 **How to run this project: [RUNNING.md](RUNNING.md)**
