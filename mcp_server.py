"""
Your MCP server. ← UNIT 4, MILESTONE 1

Right now your tools only exist inside your own program. Nothing else can reach
them. MCP is an agreed shape you wrap a tool in so that anything speaking the
same protocol can call it — your agent today, a different agent tomorrow,
someone else's app after that.

**You're moving one tool. Not three.** The point is to see the seam.
`search_listings` is the one to move: it doesn't call the model, so nothing is
slow and nothing changes between runs while you're learning the shape.

    python mcp_server.py        starts the server (it will just sit there — that's right)
    python mcp_client.py        asks the server what it offers

─────────────────────────────────────────────────────────────────────────────
TODO — register one tool.

Uncomment the block below and fill it in. Three things matter:

  1. **The name.** Exactly what your agent will ask for.

  2. **The description.** This is the part that isn't code and matters most.
     Write it before you look at the example. You are not writing it for your
     agent — you're writing it for an agent someone else builds, that will
     never see your implementation. That isn't hypothetical; it's what every
     MCP server on the registry is.

     Two things to get right: name units and types ("price" is ambiguous,
     "max_price, in whole dollars" isn't), and state the empty case. Last unit
     the empty case was on your spec sheet for your loop's benefit. Here it's
     part of a published contract.

  3. **The typed inputs.** These come straight from your Tool Inventory. If the
     types here don't match your README, one of the two is wrong — fix it.

Then point your agent at it. In `run_agent()`, swap the direct call:

    results = search_listings(description, size, max_price)

for the MCP one:

    from mcp_client import call_tool
    results = call_tool("search_listings", {
        "description": description,
        "size": size,
        "max_price": max_price,
    })

**What comes back should not change.** If it does, that difference is your
first clue about what your tool was really returning before.

🛑 Stop rule: if this isn't connecting after 40 minutes, stop. Keep your direct
call, and write down in your README exactly where it broke — the error text and
the last thing that worked. Then carry on to Milestone 2. Everything after this
works with a direct call, and **a documented failure earns the point in full.**
─────────────────────────────────────────────────────────────────────────────
"""

from mcp.server.fastmcp import FastMCP

from tools import create_fit_card as _create_fit_card_impl
from tools import search_listings as _search_listings_impl

# log_level="WARNING" keeps the server from printing an INFO line for every
# request. Without it your terminal fills with "Processing request of type
# CallToolRequest" and the output you actually care about scrolls away.
mcp = FastMCP("fitfindr", log_level="WARNING")


@mcp.tool()
def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search 40 secondhand clothing listings (Depop, ThredUp, Poshmark) by
    keywords, with an optional size and price ceiling.

    Inputs:
      description: keywords for the item, e.g. "vintage graphic tee". Matched
                   word by word against each listing's title, style tags,
                   category, description and colours.
      size:        a size as written on a label, e.g. "M", "L", "8", "W30".
                   Matches whole size words only: "M" matches "S/M" and "M/L"
                   but "L" does not match "XL". "One Size" listings always
                   match. Omit or pass null for any size.
      max_price:   inclusive price ceiling in US dollars, e.g. 30 or 29.99.
                   Omit or pass null for no ceiling.

    Returns up to 10 listing objects, best keyword match first. Each has: id,
    title, description, category, style_tags (list), size, condition,
    price (number, USD), colors (list), brand (string or null), platform.

    When nothing matches, returns an empty list [] — not an error.
    """
    return _search_listings_impl(description, size, max_price)


# Two notes on the block above.
#
# The registered name is the *function* name — so the block above registers
# "search_listings", which is exactly what call_tool("search_listings", ...)
# asks for. That is also why the import at the top of this file brings the real
# implementation in under an alias: without it, the registered function and the
# one it calls would be the same name, and the tool would call itself.
#
# FastMCP builds the input schema from your type hints, which is why the hints
# are not optional here. `description: str` becomes a required string;
# `max_price: float | None = None` becomes an optional number. Getting these
# wrong is the most common reason a call is rejected.



# Stretch feature: a second tool on MCP.
@mcp.tool()
def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Write a 2-4 sentence social-media caption about a thrifted item, in a
    casual first-person voice, mentioning the item, its price (e.g. "$24")
    and its platform once each.

    Inputs:
      outfit:   plain-text description of how the item is being styled.
      new_item: one listing object exactly as search_listings returns it
                (needs title, category, price, platform, condition, size,
                colors, style_tags, description; brand may be null).

    Returns the caption as a string. If outfit is empty or only whitespace,
    returns a short message saying there is no outfit to caption, without
    calling the model. If the language model can't be reached, the call
    fails with an error whose text says why (e.g. a rejected API key).
    """
    return _create_fit_card_impl(outfit, new_item)


if __name__ == "__main__":
    mcp.run()
