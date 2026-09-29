"""Tools the chat agent can call. All but one are pure, zero-model-call
lookups against campus_customs.db; the exception (`compose_reply`) is the one
step that actually calls the model, via the subscription CLI in
llm/claude_client.py.

Problem 6 split what used to be one bundled product lookup into three
single-purpose tools -- get_descriptions, get_prices, get_stock -- so each
maps to exactly one of the assignment's three asks (description / price /
stock-by-size) and each is independently auditable: given a tool's name and
its result, you can tell exactly which real column(s) it read, with no need
to cross-reference another tool's output."""

from __future__ import annotations

import json
import re
from difflib import SequenceMatcher

import database
from llm.claude_client import call_json
from models import (
    CandidateProduct,
    ChatTurn,
    ChatUser,
    ProductCard,
    ProductDescription,
    ProductMatch,
    ProductPrice,
    ProductStock,
    SizeStock,
)

_STOPWORDS = {
    "a", "an", "the", "is", "are", "do", "does", "you", "have", "has", "i",
    "it", "this", "that", "in", "on", "of", "for", "to", "and", "or", "my",
    "your", "me", "please", "can", "could", "would", "want", "looking",
    "need", "some", "any", "what", "which", "show", "see", "got", "with",
}

# Garment sizes, excluded separately from _STOPWORDS: these are plain English
# words ("small", "large") that also show up constantly in real catalogue
# *descriptions* ("large white YALE lettering", "small Davenport crest") --
# 23 and 15 rows respectively, checked directly against the DB. Scoring them
# as search keywords made a pure size question like "do you have this in a
# large?" spuriously match products whose description happens to contain the
# word, which starved out the page-context/continuity fallback that should
# have resolved "this". A size on its own should never drive catalogue
# search -- it's a follow-up on whatever product is already in view.
_SIZE_WORDS = {"xs", "xxs", "xl", "xxl", "small", "medium", "large", "extra"}

# Problem 9 (agent cost/speed improvement): see compose_reply for why.
MAX_HISTORY_TURNS = 10


def _tokenize(text: str) -> list[str]:
    words = re.findall(r"[a-z0-9]+", text.lower())
    return [w for w in words if w not in _STOPWORDS and w not in _SIZE_WORDS and len(w) > 1]


# Problem 9 (agent accuracy improvement): plain substring matching missed
# real typos entirely -- "sweatshirst"/"sweatshirt" and "jaket"/"jacket"
# scored zero matches before this, so the agent would honestly-but-wrongly
# tell a shopper "we don't carry that." A similarity-ratio fallback catches
# these without a hardcoded typo list. Threshold picked by checking it
# against real near-miss pairs: 0.85 catches "sweatshirst"~"sweatshirt"
# (0.95), "jaket"~"jacket" (0.91), and "crewnek"~"crewneck" (0.93), but stays
# below "shirt"~"short" (0.80), which are two different real garment words
# and must not be treated as the same typo.
_FUZZY_RATIO_THRESHOLD = 0.85
_FUZZY_MIN_LEN = 4


def _token_matches_word(token: str, word: str) -> bool:
    # Substring either direction so simple plurals match ("hoodies" <-> "hoodie").
    # Require length >= 3 on whichever side is doing the containing, so short
    # words like "cc" or "us" don't fuzzy-match half the catalogue.
    if token in word and len(token) >= 3:
        return True
    if word in token and len(word) >= 3:
        return True
    if token == word:
        return True
    if len(token) >= _FUZZY_MIN_LEN and len(word) >= _FUZZY_MIN_LEN:
        return SequenceMatcher(None, token, word).ratio() >= _FUZZY_RATIO_THRESHOLD
    return False


def search_catalogue(query: str, limit: int = 5) -> list[ProductMatch]:
    """Score every catalogue row by keyword overlap with `query` (name matches
    count double) and return the top matches -- just which products, not
    their price/description/stock. No model call. Those specifics come from
    get_descriptions/get_prices/get_stock, so this tool can't itself be a
    source of an invented price or quantity.
    """
    tokens = _tokenize(query)
    if not tokens:
        return []

    conn = database.get_connection()
    try:
        rows = conn.execute("SELECT * FROM catalogue").fetchall()
    finally:
        conn.close()

    scored: list[tuple[int, str, str]] = []
    for row in rows:
        colors = " ".join(json.loads(row["colors"]))
        tags = " ".join(json.loads(row["search_tags"]))
        haystack = " ".join(
            [row["name"], row["name"], row["garment_type"], row["description"], colors, tags]
        ).lower()
        haystack_words = re.findall(r"[a-z0-9]+", haystack)
        score = sum(1 for token in tokens if any(_token_matches_word(token, w) for w in haystack_words))
        if score > 0:
            scored.append((score, row["product_id"], row["name"]))

    scored.sort(key=lambda triple: triple[0], reverse=True)
    return [ProductMatch(product_id=pid, name=name) for _, pid, name in scored[:limit]]


def get_descriptions(product_ids: list[str]) -> list[ProductDescription]:
    """Real `catalogue.description` text for each id. No model call."""
    if not product_ids:
        return []
    conn = database.get_connection()
    try:
        placeholders = ",".join("?" for _ in product_ids)
        rows = conn.execute(
            f"SELECT product_id, name, description FROM catalogue WHERE product_id IN ({placeholders})",
            product_ids,
        ).fetchall()
    finally:
        conn.close()
    return [ProductDescription(product_id=r["product_id"], name=r["name"], description=r["description"]) for r in rows]


def get_prices(product_ids: list[str]) -> list[ProductPrice]:
    """Real `catalogue.price` for each id. No model call."""
    if not product_ids:
        return []
    conn = database.get_connection()
    try:
        placeholders = ",".join("?" for _ in product_ids)
        rows = conn.execute(
            f"SELECT product_id, name, price FROM catalogue WHERE product_id IN ({placeholders})",
            product_ids,
        ).fetchall()
    finally:
        conn.close()
    return [ProductPrice(product_id=r["product_id"], name=r["name"], price=r["price"]) for r in rows]


def get_stock(product_ids: list[str]) -> list[ProductStock]:
    """Real per-size `inventory` rows for each id, plus a total. Always
    returns the full size breakdown -- whether the reply mentions one size or
    all of them is a wording choice made by compose_reply, not something this
    tool should guess at. No model call."""
    if not product_ids:
        return []
    conn = database.get_connection()
    try:
        placeholders = ",".join("?" for _ in product_ids)
        names = {
            r["product_id"]: r["name"]
            for r in conn.execute(
                f"SELECT product_id, name FROM catalogue WHERE product_id IN ({placeholders})", product_ids
            ).fetchall()
        }
        result = []
        for product_id in product_ids:
            if product_id not in names:
                continue
            sizes = database.sort_sizes(
                conn.execute("SELECT size, quantity FROM inventory WHERE product_id = ?", (product_id,)).fetchall()
            )
            size_list = [SizeStock(size=s["size"], quantity=s["quantity"]) for s in sizes]
            result.append(
                ProductStock(
                    product_id=product_id,
                    name=names[product_id],
                    sizes=size_list,
                    total_stock=sum(s.quantity for s in size_list),
                )
            )
        return result
    finally:
        conn.close()


def get_products_by_ids(product_ids: list[str]) -> list[ProductCard]:
    """Frontend-facing product cards (adds image_url/garment_type on top of
    the agent's three lookups) -- used by main.py to expand the agent's final
    product_ids into what the chat widget renders, not called by the agent
    itself."""
    products = []
    for product_id in product_ids:
        data = database.get_product(product_id)
        if data is not None:
            products.append(ProductCard(**data))
    return products


def compose_reply(
    system_prompt: str,
    user_message: str,
    history: list[ChatTurn],
    candidates: list[CandidateProduct],
    user: ChatUser | None = None,
) -> dict:
    """The one real model call: write the shopper-facing reply, grounded only
    in `candidates` (assembled from get_descriptions/get_prices/get_stock).
    Returns a plain dict matching ChatReply's fields."""
    # Problem 9 (agent cost/speed improvement): only the most recent turns go
    # into the prompt, no matter how long the full conversation has gotten.
    # Without this, a long-running conversation resends its *entire* history
    # on every single message (the backend is stateless — Problem 8's history
    # only persists to the DB, the live prompt is built fresh each time), so
    # token cost and latency for the one real model call would grow without
    # bound turn after turn. Capping it keeps every turn roughly the same
    # cost regardless of how long the shopper has been chatting.
    recent_history = history[-MAX_HISTORY_TURNS:]
    history_text = "\n".join(f"{turn.role}: {turn.content}" for turn in recent_history) or "(no earlier messages)"
    candidates_json = json.dumps([c.model_dump() for c in candidates], indent=2)
    shopper_line = f"{user.first_name} {user.last_name} ({user.email}), logged in" if user else "a guest, not logged in"

    prompt = f"""Shopper: {shopper_line}

Conversation so far:
{history_text}

Shopper's new message: {user_message}

Candidate products, looked up directly from campus_customs.db (the ONLY products/prices/stock you may reference — do not invent others or recall numbers from general knowledge):
{candidates_json}

Reply as the Campus Customs assistant. Return ONLY raw JSON (no prose, no markdown fences) matching exactly:
{{"reply": "<your reply text>", "product_ids": ["<subset of candidate product_id values you actually reference, in relevance order>"]}}

If none of the candidates answer the shopper's question, say so honestly in "reply" and use an empty "product_ids" list."""

    result = call_json(prompt, system=system_prompt)
    if not isinstance(result, dict) or "reply" not in result:
        raise ValueError(f"Model reply did not match the expected shape: {result!r}")
    result.setdefault("product_ids", [])
    return result
