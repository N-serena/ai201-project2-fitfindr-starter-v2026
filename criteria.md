# Acceptance criteria — FitFindr

Five criteria that say what "working" means for this agent, written in unit 3
**before** any results existed.

An acceptance criterion names a target: a number, a count, a rate, or something
a person could plainly observe. *"The agent handles errors"* is an opinion.
*"When search returns nothing, the agent stops before calling the second tool,
in 5 of 5 tries"* is a criterion.

Under each one, write a sentence or two on **why that target** and not a
stricter one. A reason that says something about your tools, your loop, or the
data earns credit; *"80% seemed reasonable"* does not.

> Missing your own targets next unit costs you nothing. Setting a target so
> easy you can't miss it does.

**Two are written for you. You write three.**

---

## 1. A matching query completes all three tools

Given a query that matches at least one listing, the agent completes all three
tool calls and returns a fit card — in at least 4 of 5 tries.

**Why this target:**
Everything before the first model call is local and deterministic: the query
is parsed with a regex and `search_listings` is a keyword match over a fixed
file, so a matching query finds its item every time. The miss I allow is on
the model side. A complete run makes two `generate()` calls on the free tier
(15 requests a minute), and the eval runs scenarios back to back, so one try
in five can end with a rate-limit error that outlasts the retries, or a
timeout, before a fit card exists.

---

## 2. An impossible query stops before the second tool

Given a query that matches no listings, the agent stops before calling
`suggest_outfit` and returns a message naming what to change — 5 of 5 tries.

**Why this target:**
This path never reaches the model. Parsing and search are deterministic, so
the same impossible query gives `[]` every time, and the branch on `[]` is a
plain `if`. There is no variance for a miss to come from, so anything short of
5 of 5 is a bug in my loop.

---

## 3. The searched item is the item every later tool receives

In a completed run, the `id` of `session["selected_item"]` equals the `id` of
`session["search_results"][0]`, and the `new_item` passed to `suggest_outfit`
and to `create_fit_card` (as shown by `--trace`) has that same `id` — all three
match in 5 of 5 tries.

**Why this target:**
Moving one dict through the session involves no model and no randomness. If
the id ever differs, the loop is reading a stale or overwritten field, which
is a wiring bug. A lower target would mean accepting captions about an item
the user never saw.

---

## 4. The fit card is a postable caption that gets the facts right

For one matching query run 5 times with the cache off, each fit card is 2 to 4
sentences long, contains the selected item's exact price (for example `$24`)
and its platform name, and no two of the five start with the same first
sentence — in at least 4 of 5 tries.

**Why this target:**
The caption comes from a small model at temperature 0.9. The prompt asks for
the price and platform, but the model sometimes rewrites a price as "24
bucks", drops the platform, or runs to five sentences. The length limit and
the facts are things I can check by reading, and the distinct-first-sentence
check catches a cache or temperature problem. 5 of 5 would assume the model
always follows formatting instructions, and a lite model doesn't.

> **Revised in unit 4:** For one matching query run 5 times with the cache
> off, each fit card is 2 to 4 sentences long, contains the selected item's
> exact price and its platform name, and opens with two words that no more
> than one other card of the five also opens with — in at least 4 of 5
> tries. A try passes only if its card meets all four parts. The first two
> words are compared lowercased.
>
> **Why revised:** "No two start with the same first sentence" measured the
> wrong thing. It was meant to catch captions that come out as one template,
> but a first sentence that differs by a single word ("Scored this 2003 tour
> tee…" against "Scored this vintage 2003 tour tee…") counted as different.
> So the original passed 5/5 while 18 of the 20 cards in the after run opened
> with "Scored this". The opening two words are what make every card read the
> same, and they can be counted. The target stays at 4 of 5; only what counts
> as different changed. Re-scored against this version, criterion 4 scores
> 0/5 in both the before and the after run (MISSED). The original verdict,
> MET (5/5) against the original wording, stays in the README as it was.

---

## 5. An empty wardrobe gets advice, not invented clothes

Given a matching query and an empty wardrobe, the agent still returns a
non-empty outfit suggestion and a fit card, and the outfit suggestion names
none of the 10 items from the example wardrobe and doesn't claim the user
already owns anything ("you already have", "from your closet") — in at least
4 of 5 tries.

**Why this target:**
`suggest_outfit` switches to a general-advice prompt when `wardrobe["items"]`
is empty, so the code path itself is deterministic. The risk is the model:
asked to style a piece, it tends to invent "your white sneakers" even when
told the user owns nothing. That is the failure I care about, because it
recommends clothes the user doesn't have. I allow one slip in five because
the guard is only a prompt instruction.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     UNIT 4 — read this before you change anything above.

     If a criterion turns out to be BROKEN rather than merely unmet, you can
     revise it, and that earns credit. But never delete or edit the original
     line. Add the revision underneath it, like this:

         ## 4. Something about the fit card

         The fit card is different every time.

         **Why this target:** ...

         > **Revised in unit 4:** For 5 different items, the 5 fit cards share
         > no opening sentence.
         >
         > **Why revised:** "different" wasn't checkable — two cards that
         > differed by one word still counted. The new version is something I
         > can actually score.

     That's a revision because the criterion couldn't be MEASURED.

     Lowering a target because you missed it is not a revision, and it costs
     you the point:

         ✗ "I said the empty search stops it 5 of 5 times, but I got 3 of 5,
            so 3 of 5 is more realistic."

     A number you missed stays where it is, gets diagnosed, and gets a fix
     attempted. That's where the points are.
     ───────────────────────────────────────────────────────────────────────── -->
