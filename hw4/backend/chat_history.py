"""Persisting a logged-in shopper's chat history to `chat_messages`.

Problem 8: only logged-in users get persisted history — guests can still
chat, but nothing is written for them. `products_json` stores just the list
of product_ids the assistant showed with that message (not full product
objects), so history always reloads with *current* price/stock rather than
whatever was true when the message was saved; main.py re-expands those ids
through the normal product lookup on the way back out.
"""

from __future__ import annotations

import json
from typing import Any

import database


def save_message(user_id: int, role: str, content: str, product_ids: list[str]) -> None:
    conn = database.get_connection()
    try:
        conn.execute(
            "INSERT INTO chat_messages (user_id, role, content, products_json) VALUES (?, ?, ?, ?)",
            (user_id, role, content, json.dumps(product_ids)),
        )
        conn.commit()
    finally:
        conn.close()


def load_history(user_id: int) -> list[dict[str, Any]]:
    """Oldest-first list of {role, content, product_ids}.

    The seed database already had some chat_messages rows (from before this
    project wrote any of its own) whose products_json holds full enriched
    product objects, not a plain list of id strings. Those don't match what
    this app writes, so they're detected and treated as "no products" for
    that row rather than guessed at or crashed on — the message text still
    loads fine, it just won't have product cards attached.
    """
    conn = database.get_connection()
    try:
        rows = conn.execute(
            "SELECT role, content, products_json FROM chat_messages WHERE user_id = ? ORDER BY id ASC",
            (user_id,),
        ).fetchall()
    finally:
        conn.close()

    result = []
    for row in rows:
        product_ids: list[str] = []
        if row["products_json"]:
            try:
                parsed = json.loads(row["products_json"])
                if isinstance(parsed, list) and all(isinstance(item, str) for item in parsed):
                    product_ids = parsed
            except json.JSONDecodeError:
                pass
        result.append({"role": row["role"], "content": row["content"], "product_ids": product_ids})
    return result
