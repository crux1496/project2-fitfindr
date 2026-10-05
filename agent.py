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
from tools import search_listings, suggest_outfit, create_fit_card
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

_PRICE = re.compile(
    r"(?:under|below|less than|max(?:imum)?|up to|at most|<)\s*\$?\s*(\d+(?:\.\d+)?)"
    r"|\$\s*(\d+(?:\.\d+)?)",
    re.IGNORECASE,
)
_SIZE = re.compile(
    r"(?:\bin\s+)?(?:\ba\s+)?\bsize\s+"
    r"(us\s*\d+(?:\.\d+)?|w\d+(?:\s*l\d+)?|\d+(?:\.\d+)?|(?:xx?[sl]|[sml])(?:/(?:xx?[sl]|[sml]))?)\b",
    re.IGNORECASE,
)
_LEAD_IN = re.compile(
    r"^(?:i'?m\s+|i\s+am\s+)?(?:looking\s+for|find\s+me|show\s+me|i\s+want|i\s+need)\s+(?:an?\s+|some\s+)?",
    re.IGNORECASE,
)


def parse_query(query: str) -> dict:
    text = query
    max_price = None
    size = None

    price_match = _PRICE.search(text)
    if price_match:
        max_price = float(price_match.group(1) or price_match.group(2))
        text = text[: price_match.start()] + " " + text[price_match.end():]

    size_match = _SIZE.search(text)
    if size_match:
        size = size_match.group(1).upper()
        text = text[: size_match.start()] + " " + text[size_match.end():]

    description = _LEAD_IN.sub("", text.strip())
    description = re.sub(r"\s+", " ", re.sub(r"[,;]", " ", description)).strip()
    return {"description": description, "size": size, "max_price": max_price}


def _no_match_message(parsed: dict) -> str:
    asked = f"'{parsed['description']}'"
    changes = []
    if parsed["max_price"] is not None:
        asked += f" under ${parsed['max_price']:g}"
        changes.append(f"raise the ${parsed['max_price']:g} price ceiling")
    if parsed["size"]:
        asked += f" in size {parsed['size']}"
        changes.append(f"drop size {parsed['size']}")
    changes.append(
        "use broader words, like a category (tops, bottoms, outerwear, shoes, "
        "accessories) or a style (vintage, streetwear, y2k, grunge)"
    )
    return f"No listings matched {asked}. Try to " + ", or ".join(changes) + "."


def run_agent(query: str, wardrobe: dict) -> dict:
    session = new_session(query, wardrobe)
    session["parsed"] = parse_query(query)

    count = 0
    next_step = "search_listings"
    while next_step != "done":
        count += 1
        trace.check_iterations(count)

        if next_step == "search_listings":
            session["search_results"] = search_listings(
                session["parsed"]["description"],
                size=session["parsed"]["size"],
                max_price=session["parsed"]["max_price"],
            )
            if not session["search_results"]:
                session["error"] = _no_match_message(session["parsed"])
                next_step = "done"
            else:
                session["selected_item"] = session["search_results"][0]
                next_step = "suggest_outfit"

        elif next_step == "suggest_outfit":
            session["outfit_suggestion"] = suggest_outfit(
                session["selected_item"], session["wardrobe"]
            )
            next_step = "create_fit_card"

        elif next_step == "create_fit_card":
            session["fit_card"] = create_fit_card(
                session["outfit_suggestion"], session["selected_item"]
            )
            next_step = "done"

    return session


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
