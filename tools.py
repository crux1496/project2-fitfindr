import re

import config
from generate import generate
from utils.data_loader import load_listings


# ── Tool 1: search_listings ───────────────────────────────────────────────────

_STOPWORDS = {
    "a", "an", "and", "the", "for", "in", "of", "on", "with", "to", "some",
    "looking", "want", "need", "i", "im", "me", "my", "something", "any",
}


def _words(text: str) -> set[str]:
    return {_stem(w) for w in re.findall(r"[a-z0-9]+", text.lower())}


def _stem(word: str) -> str:
    return word[:-1] if len(word) > 3 and word.endswith("s") and not word.endswith("ss") else word


def _size_parts(size: str) -> set[str]:
    return {part for part in re.split(r"[\s/()]+", size.upper()) if part}


def _size_matches(wanted: str, listing_size: str) -> bool:
    if listing_size.upper().startswith("ONE SIZE"):
        return True
    wanted_parts = _size_parts(wanted) - {"US", "SIZE"}
    return bool(wanted_parts) and wanted_parts <= _size_parts(listing_size)


def _score(query_words: set[str], listing: dict) -> int:
    title = _words(listing["title"])
    tags = _words(" ".join(listing["style_tags"]))
    weak = _words(" ".join([
        listing["description"],
        listing["category"],
        " ".join(listing["colors"]),
        listing["brand"] or "",
    ]))
    return sum(3 if w in title else 2 if w in tags else 1 if w in weak else 0 for w in query_words)


def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    query_words = _words(description) - _STOPWORDS
    if not query_words:
        return []

    scored = []
    for listing in load_listings():
        if max_price is not None and listing["price"] > max_price:
            continue
        if size and not _size_matches(size, listing["size"]):
            continue
        score = _score(query_words, listing)
        if score > 0:
            scored.append((score, listing))

    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [listing for _, listing in scored[: config.SEARCH_RESULT_LIMIT]]


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

_OUTFIT_SYSTEM = (
    "You are a thrift stylist. Suggest one or two complete outfits built around "
    "the thrifted item. Name the item by its title. Keep it to a few short lines "
    "of plain text, no headings and no markdown."
)


def _describe_item(item: dict) -> str:
    details = [
        f"Title: {item['title']}",
        f"Category: {item['category']}",
        f"Colors: {', '.join(item['colors'])}",
        f"Style: {', '.join(item['style_tags'])}",
        f"Size: {item['size']}",
        f"Condition: {item['condition']}",
    ]
    if item.get("brand"):
        details.append(f"Brand: {item['brand']}")
    return "\n".join(details)


def _describe_wardrobe_item(piece: dict) -> str:
    line = f"- {piece['name']} ({piece['category']}; {', '.join(piece['colors'])}; {', '.join(piece['style_tags'])})"
    return f"{line} - {piece['notes']}" if piece.get("notes") else line


def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    pieces = wardrobe.get("items") or []
    item = _describe_item(new_item)

    if pieces:
        closet = "\n".join(_describe_wardrobe_item(piece) for piece in pieces)
        prompt = (
            f"Thrifted item:\n{item}\n\nThe user's wardrobe:\n{closet}\n\n"
            "Suggest one or two outfits pairing the thrifted item with pieces "
            "from this wardrobe. Name each wardrobe piece exactly as listed."
        )
    else:
        prompt = (
            f"Thrifted item:\n{item}\n\nThe user hasn't saved any wardrobe "
            "pieces yet. Give general styling advice: one or two outfits "
            "describing the kinds of pieces, colors and shoes to pair it with."
        )

    suggestion = generate(prompt, system=_OUTFIT_SYSTEM).strip()
    if suggestion:
        return suggestion
    return (
        f"Style the {new_item['title']} as a {new_item['category']} piece with "
        f"{', '.join(new_item['style_tags'])} basics in matching colors."
    )


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

_CAPTION_SYSTEM = (
    "You write captions people post about their thrift finds. Write like a real "
    "person posting, not a product listing. Two to four sentences, plain text, "
    "no hashtags."
)


def _price(value: float) -> str:
    return f"${value:.0f}" if value == int(value) else f"${value:.2f}"


def create_fit_card(outfit: str, new_item: dict) -> str:
    if not outfit or not outfit.strip():
        return f"No outfit to caption for {new_item['title']} yet. Run suggest_outfit first."

    brand = f" by {new_item['brand']}" if new_item.get("brand") else ""
    prompt = (
        f"The find: {new_item['title']}{brand}, {new_item['condition']} condition, "
        f"{_price(new_item['price'])} on {new_item['platform']}.\n"
        f"How I'm wearing it: {outfit.strip()}\n\n"
        "Write the caption. Mention the item, the price written exactly as "
        f"{_price(new_item['price'])}, and {new_item['platform']} once each, and "
        "be specific about the vibe of the outfit."
    )
    return generate(prompt, system=_CAPTION_SYSTEM).strip()
