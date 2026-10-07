"""
The FitFindr planning loop.

This is the file that makes FitFindr an agent rather than a script. It decides
which tool to run next based on what the last one returned.

If your loop calls all three tools no matter what comes back, you have a list
of function calls. A loop looks at the last result before it picks the next
step. **That branch is the graded part of this unit.**

Build and test your three tools in `tools.py` first. Then come here.

    python agent.py          runs both example paths below
"""

import re

import config
import trace
from mcp_client import call_tool
from tools import suggest_outfit, create_fit_card
from generate import ModelUnavailable


# ── session state ─────────────────────────────────────────────────────────────

def new_session(query: str, wardrobe: dict) -> dict:
    """
    A fresh session for one user interaction.

    The session is the single source of truth for a run. Every tool result goes
    in here, and the next tool reads it back out.

    You could pass values straight from one call to the next. It would work,
    and you would not be able to test it — you can't print a variable you have
    already overwritten. Going through the session is what makes the state
    visible, and unit 4 has you write a criterion about exactly that.

    Add fields if you need them.
    """
    return {
        "query": query,              # what the user typed
        "parsed": {},                # description / size / max_price you pulled out of it
        "search_results": [],        # everything search_listings returned
        "selected_item": None,       # the one you chose — goes into suggest_outfit
        "wardrobe": wardrobe,        # the user's wardrobe
        "outfit_suggestion": None,   # what suggest_outfit returned
        "fit_card": None,            # what create_fit_card returned
        "error": None,               # set when the run ended early
    }


# ── planning loop ─────────────────────────────────────────────────────────────

def run_agent(query: str, wardrobe: dict) -> dict:
    """
    Run the loop once and return the finished session.

    Args:
        query:    what the user asked for, in plain language
                  (e.g. "vintage graphic tee under $30, size M").
        wardrobe: a wardrobe dict — get_example_wardrobe() or
                  get_empty_wardrobe() from utils/data_loader.py.

    Returns:
        The session dict. **Check session["error"] first** — if it isn't None,
        the run ended early and the later fields will still be None.

    ─────────────────────────────────────────────────────────────────────────
    TODO — build this, following the branch rule you wrote in Milestone 2.

      1. Start a session with new_session().

      2. Count the times round the loop, and call trace.check_iterations(count)
         on each one before you go again. It raises when the count passes
         MAX_ITERATIONS in config.py — see trace.py.

      3. Parse the query into a description, a size, and a max_price. Regex,
         string splitting, or asking the model are all fine — say which you
         chose in your README. Put the result in session["parsed"].

      4. Call search_listings() with what you parsed.
         Put the results in session["search_results"].

         ⚠️ THIS IS THE BRANCH. If nothing came back:
              - put a message in session["error"] saying what the user could
                change — "No results" is not that message
              - return the session
              - do NOT call suggest_outfit with nothing

      5. Choose an item — the first result is fine. Put it in
         session["selected_item"].

      6. Call suggest_outfit() with the selected item and the wardrobe.
         Put the result in session["outfit_suggestion"].

      7. Call create_fit_card() with the outfit and the item.
         Put the result in session["fit_card"].

      8. Return the session.

    ─────────────────────────────────────────────────────────────────────────
    IN UNIT 4 you come back and add two things:

      • Trace calls. One per step. `trace.step("search_listings", inputs=...,
        returned=...)` — see trace.py. Your README needs the output.

      • A handler for ModelUnavailable, so a bad key produces a message rather
        than a stack trace. The import is already at the top of this file.
    """
    session = new_session(query, wardrobe)
    count = 0

    # Each pass reads the session, picks the one step it is missing, and runs it.
    try:
        while True:
            count += 1
            trace.check_iterations(count)

            if not session["parsed"]:
                session["parsed"] = parse_query(query)
                trace.step("parse_query", inputs=query, returned=repr(session["parsed"]))

            elif session["selected_item"] is None:
                parsed = session["parsed"]
                session["search_results"] = search_listings(
                    parsed["description"], parsed["size"], parsed["max_price"]
                )
                found = session["search_results"]
                trace.step(
                    "search_listings (via MCP)",
                    inputs=f"description={parsed['description']!r}, size={parsed['size']!r}, "
                           f"max_price={parsed['max_price']!r}",
                    returned=found,
                    note="branch: empty, stopping before suggest_outfit" if not found
                         else f"branch: {len(found)} results, continuing",
                )
                if not found:
                    session["error"] = _no_results_message(parsed)
                    return session
                session["selected_item"] = found[0]
                trace.step("select_item", returned=_item_ref(session["selected_item"]))

            elif session["outfit_suggestion"] is None:
                item = session["selected_item"]
                session["outfit_suggestion"] = suggest_outfit(item, session["wardrobe"])
                trace.step(
                    "suggest_outfit",
                    inputs=f"new_item={_item_ref(item)}, "
                           f"wardrobe={len(session['wardrobe'].get('items') or [])} items",
                    returned=session["outfit_suggestion"],
                )

            elif session["fit_card"] is None:
                item = session["selected_item"]
                session["fit_card"] = create_fit_card(session["outfit_suggestion"], item)
                trace.step(
                    "create_fit_card",
                    inputs=f"new_item={_item_ref(item)}, "
                           f"outfit={len(session['outfit_suggestion'])} chars",
                    returned=session["fit_card"],
                )

            else:
                return session

    except ModelUnavailable as exc:
        found = session["selected_item"]
        session["error"] = (
            f"{exc} The search still worked"
            + (f" — it found {found['title']} (${found['price']:g} on {found['platform']})." if found else ".")
        )
        trace.step("model unavailable", returned=str(exc), note="stopping, error set in session")
        return session


def _item_ref(item: dict) -> str:
    """How a listing appears in the trace: id first, so tools' inputs can be compared."""
    return f"{item['id']} {item['title']}"


# ── search over MCP ───────────────────────────────────────────────────────────

def search_listings(description: str, size: str | None, max_price: float | None) -> list[dict]:
    """tools.search_listings, called through the MCP server in mcp_server.py."""
    return call_tool("search_listings", {
        "description": description,
        "size": size,
        "max_price": max_price,
    })


# ── query parsing ─────────────────────────────────────────────────────────────

_PRICE = re.compile(r"(?:under|below|less than|max|up to|<)\s*\$?\s*(\d+(?:\.\d+)?)", re.I)
_SIZE = re.compile(r"\bsize\s+([a-z0-9./]+)", re.I)


def parse_query(query: str) -> dict:
    """
    Regex parse: 'under $30' -> max_price 30.0, 'size M' -> size 'M'.
    Whatever is left, minus punctuation, is the description.
    """
    price = _PRICE.search(query)
    size = _SIZE.search(query)

    description = _SIZE.sub(" ", _PRICE.sub(" ", query))
    description = " ".join(re.sub(r"[,;!?]", " ", description).split())

    return {
        "description": description,
        "size": size.group(1) if size else None,
        "max_price": float(price.group(1)) if price else None,
    }


def _no_results_message(parsed: dict) -> str:
    """Say which filter emptied the search, by re-running it with each one dropped."""
    what = f"Nothing matched '{parsed['description']}'"
    if parsed["size"]:
        what += f" in size {parsed['size']}"
    if parsed["max_price"] is not None:
        what += f" under ${parsed['max_price']:g}"

    hints = []
    if parsed["max_price"] is not None and search_listings(parsed["description"], parsed["size"], None):
        hints.append(f"raise the price ceiling above ${parsed['max_price']:g}")
    if parsed["size"] and search_listings(parsed["description"], None, parsed["max_price"]):
        hints.append(f"drop the size {parsed['size']}")
    if not hints:
        hints.append(
            "describe the item with a category or style word like "
            "'jacket', 'jeans', 'tee', 'y2k' or 'vintage'"
        )
    return f"{what}. Try to {' or '.join(hints)}."


# ── running it directly ───────────────────────────────────────────────────────

def _show(session: dict) -> None:
    if session["error"]:
        print(f"  stopped: {session['error']}")
        print(f"  fit_card is {session['fit_card']!r} — it should still be None here")
        return

    item = session["selected_item"] or {}
    print(f"  found:    {item.get('title')} — ${item.get('price')} on {item.get('platform')}")
    print(f"  outfit:   {session['outfit_suggestion']}")
    print(f"  fit card: {session['fit_card']}")


if __name__ == "__main__":
    from utils.data_loader import get_example_wardrobe

    print("=== A query the data can match ===")
    _show(run_agent(
        query="looking for a vintage graphic tee under $30",
        wardrobe=get_example_wardrobe(),
    ))

    print("\n=== A query it can't ===")
    _show(run_agent(
        query="designer ballgown size XXS under $5",
        wardrobe=get_example_wardrobe(),
    ))

    print(
        "\nThe second one should stop before the fit card. If both paths look "
        "the same,\nthe branch isn't doing anything yet."
    )
