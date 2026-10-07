"""
The three FitFindr tools.

Each one is a standalone function you can call and test on its own, before any
of them are wired into the loop. Build and test them one at a time — three
untested tools joined by a loop is one problem that looks like six, because you
can't tell which layer is lying to you.

    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)             → str
    create_fit_card(outfit, new_item)              → str

All three are stubs right now. They run and they do nothing — that's the
starting position and it's deliberate.

⚠️ Before you write any of them, fill in the **Tool Inventory** section of your
README (Milestone 2). Four lines per tool: what it does, each input with its
type, exactly what it returns, and what it returns when it has nothing to give.
That last line is what your loop branches on. "Returns a list" earns nothing —
the description has to say what is *in* the list.
"""

import re

import config
from generate import generate
from utils.data_loader import load_listings


# ── Tool 1: search_listings ───────────────────────────────────────────────────

# Words that carry no search meaning in a shopping query.
_STOPWORDS = {
    "a", "an", "and", "the", "for", "in", "of", "on", "with", "to", "or",
    "i", "im", "me", "my", "want", "need", "looking", "find", "some", "something",
    "under", "below", "less", "than", "size", "sized", "price",
}


def _words(text: str) -> list[str]:
    """Lowercase alphanumeric words; dots kept so `8.5` stays one word."""
    return re.findall(r"[a-z0-9.]+", text.lower().replace("'", ""))


def _size_words(size: str) -> set[str]:
    """Words of a size string with `us` dropped: 'US 8.5' -> {'8.5'}, 'S/M' -> {'s', 'm'}."""
    return {w for w in re.split(r"[\s/()]+", size.lower()) if w and w != "us"}


def _size_matches(wanted: str, listing_size: str) -> bool:
    if "one size" in listing_size.lower():
        return True
    return bool(_size_words(wanted) & _size_words(listing_size))


def _score(query_words: list[str], listing: dict) -> int:
    """2 per word in title, tags or category; 1 per word only in description, colors or brand."""
    strong = set(_words(" ".join([listing["title"], listing["category"], *listing["style_tags"]])))
    weak = set(_words(" ".join([listing["description"], *listing["colors"], listing["brand"] or ""])))
    score = 0
    for word in query_words:
        if word in strong:
            score += 2
        elif word in weak:
            score += 1
    return score


def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search the listings data for items matching a description, and optionally a
    size and a price ceiling.

    This is the tool that doesn't call the model, which makes it the easiest one
    to test and the one to move onto MCP in unit 4.

    Args:
        description: keywords describing what the user wants
                     (e.g. "vintage graphic tee").
        size:        a size string to filter by, or None to skip size filtering.
                     Match case-insensitively — "M" should match "S/M".

                     ⚠️ Read the sizes in the data before you reach for a plain
                     substring test. `"s" in "us 9"` is True, and so is
                     `"l" in "xl"`. A filter that returns shoes when someone
                     asked for a small top reads like a broken search, and it
                     will quietly cost you in unit 4 when you test criterion 1.
                     What counts as a size match is part of your spec — decide
                     it and write it into your Tool Inventory.
        max_price:   maximum price, inclusive, or None to skip price filtering.

    Returns:
        A list of matching listing dicts, best match first.
        **Returns an empty list when nothing matches — an empty list, not None,
        and not an exception.** Your loop branches on this.

    Each listing dict has these fields:
        id, title, description, category, style_tags (list), size,
        condition, price (float), colors (list), brand (str or None), platform

    Note that `brand` is None for most listings. That is deliberate and
    realistic — thrift listings often have no brand. If something you write
    assumes a brand is always there, you will find out in unit 4.

    TODO:
        1. Load every listing with load_listings().
        2. Filter by max_price and by size, when each is provided.
        3. Score what's left by keyword overlap with `description`.
        4. Drop anything scoring zero.
        5. Sort by score, highest first, and return the listing dicts —
           at most config.SEARCH_RESULT_LIMIT of them.

    Test it from a terminal before you move on:
        python -c "from tools import search_listings; print(search_listings('graphic tee', max_price=30))"
    """
    query_words = list(dict.fromkeys(w for w in _words(description) if w not in _STOPWORDS))

    scored = []
    for listing in load_listings():
        if max_price is not None and listing["price"] > max_price:
            continue
        if size and not _size_matches(size, listing["size"]):
            continue
        score = _score(query_words, listing)
        if score > 0:
            scored.append((score, listing))

    # sorted() is stable, so equal scores keep dataset order
    scored = sorted(scored, key=lambda pair: pair[0], reverse=True)
    return [listing for _, listing in scored[: config.SEARCH_RESULT_LIMIT]]


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Given a thrifted item and the user's wardrobe, suggest one or two outfits.

    This one calls the model, through `generate()`. You don't need to think
    about rate limits — the adapter handles pacing for you.

    Args:
        new_item: a listing dict — the item the user is considering.
        wardrobe: a wardrobe dict with an 'items' key holding a list of items.
                  **It may be empty.** Handle that.

    Returns:
        A non-empty string with outfit suggestions.
        With an empty wardrobe, return general styling advice rather than
        raising or returning "". Unit 4 has you trigger the empty wardrobe on
        purpose, so decide now what it should do.

    TODO:
        1. Check whether wardrobe['items'] is empty.
        2. If it is, ask the model for general styling ideas for this item.
        3. If it isn't, format the wardrobe items into the prompt and ask for
           specific combinations naming pieces the user already owns.
        4. Return the model's response.

    Test it from a terminal before you move on:
        python -c "from tools import suggest_outfit; from utils.data_loader import get_example_wardrobe, load_listings; print(suggest_outfit(load_listings()[0], get_example_wardrobe()))"
    """
    item_text = _describe_item(new_item)
    items = wardrobe.get("items") or []

    if items:
        closet = "\n".join(_describe_wardrobe_item(piece) for piece in items)
        prompt = (
            f"Someone is thinking about buying this thrifted piece:\n{item_text}\n\n"
            f"Their wardrobe:\n{closet}\n\n"
            "Suggest one or two complete outfits built around the thrifted piece. "
            "Use only pieces from their wardrobe, and name each one exactly as it "
            "is written above. Say in one sentence why each outfit works. "
            "Plain text, no markdown, under 120 words."
        )
    else:
        prompt = (
            f"Someone is thinking about buying this thrifted piece:\n{item_text}\n\n"
            "They have not saved any clothes yet, so you know nothing about what "
            "they own. Give general styling advice: one or two outfits described "
            "by kinds of pieces and colours (for example 'straight-leg dark jeans'). "
            "Do not say or imply that they already own anything — no 'your', "
            "'you already have', or 'from your closet'. "
            "Plain text, no markdown, under 120 words."
        )

    reply = generate(prompt, system=_STYLIST_SYSTEM).strip()
    if not reply:
        return f"Pair the {new_item['title']} with simple basics in neutral colours and let it be the focus."
    return reply


_STYLIST_SYSTEM = (
    "You are a practical thrift stylist. You suggest outfits a real person could "
    "put together today. You never invent clothing the user owns."
)


def _describe_item(item: dict) -> str:
    """One listing as prompt text; brand is omitted when the listing has none."""
    lines = [
        f"- {item['title']} ({item['category']})",
        f"- ${item['price']:.2f} on {item['platform']}, condition: {item['condition']}, size {item['size']}",
        f"- colours: {', '.join(item['colors'])}; style: {', '.join(item['style_tags'])}",
        f"- {item['description']}",
    ]
    if item.get("brand"):
        lines.insert(1, f"- brand: {item['brand']}")
    return "\n".join(lines)


def _describe_wardrobe_item(piece: dict) -> str:
    line = f"- {piece['name']} ({piece['category']}; {', '.join(piece['colors'])})"
    if piece.get("notes"):
        line += f" — {piece['notes']}"
    return line


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Write a short caption someone would actually post about the find.

    This calls the model too.

    Args:
        outfit:   the outfit suggestion string from suggest_outfit().
        new_item: the listing dict for the item.

    Returns:
        A two-to-four sentence caption.
        If `outfit` is empty or whitespace, return a descriptive message rather
        than raising.

    The caption should read like a real post rather than a product description,
    mention the item and its price and platform once each, and be specific about
    the vibe.

    It should also come out **differently for different inputs**. If you run
    this three times on the same item and get three word-for-word identical
    strings, it's one of two things, and both are near the top of `config.py`:

        • CACHE_ENABLED — the adapter handed back an answer it already had
        • TEMPERATURE   — at 0.0 the model gives the same words every time

    TODO:
        1. Guard against an empty or whitespace-only `outfit`.
        2. Build a prompt with the item details and the outfit.
        3. Call generate() and return the response.

    Test it from a terminal before you move on:
        python -c "from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card('jeans and white sneakers', load_listings()[0]))"
    """
    # TODO: replace this with your implementation
    return ""
