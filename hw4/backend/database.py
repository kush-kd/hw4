import json
import sqlite3
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DB_PATH = DATA_DIR / "campus_customs.db"

# Garment size order, not alphabetical. `ORDER BY size` in SQL sorts
# alphabetically (L, M, S, XL, XS, XXL) -- found while testing the chat
# agent: it misreported a real 12-in-stock Small as sold out, reproducibly,
# and the likely cause is exactly this scrambled order putting M=0 directly
# before S=12 in the list the model reads. Sorting sizes in true garment
# order fixes both that and the same confusing order on the product detail
# page's size grid.
SIZE_ORDER = ["XS", "S", "M", "L", "XL", "XXL"]


def sort_sizes(rows: list[sqlite3.Row]) -> list[sqlite3.Row]:
    def key(row: sqlite3.Row) -> int:
        try:
            return SIZE_ORDER.index(row["size"])
        except ValueError:
            return len(SIZE_ORDER)

    return sorted(rows, key=key)


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _row_to_product_summary(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "product_id": row["product_id"],
        "name": row["name"],
        "garment_type": row["garment_type"],
        "description": row["description"],
        "price": row["price"],
        "image_url": f"/media/{row['image_file_path']}",
    }


def list_products() -> list[dict[str, Any]]:
    """Problem 10: colors and total_stock added so product cards can show a
    real color swatch and a truthful "low stock" badge — grounded in the
    same inventory numbers the chat agent and the detail page use, not a
    decorative guess."""
    conn = get_connection()
    try:
        rows = conn.execute("SELECT * FROM catalogue ORDER BY name").fetchall()
        stock_by_id = {
            r["product_id"]: r["total"] or 0
            for r in conn.execute(
                "SELECT product_id, SUM(quantity) AS total FROM inventory GROUP BY product_id"
            ).fetchall()
        }
        result = []
        for row in rows:
            summary = _row_to_product_summary(row)
            summary["colors"] = json.loads(row["colors"])
            summary["total_stock"] = stock_by_id.get(row["product_id"], 0)
            result.append(summary)
        return result
    finally:
        conn.close()


def get_product(product_id: str) -> dict[str, Any] | None:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM catalogue WHERE product_id = ?", (product_id,)
        ).fetchone()
        if row is None:
            return None

        sizes = sort_sizes(
            conn.execute(
                "SELECT size, quantity FROM inventory WHERE product_id = ?",
                (product_id,),
            ).fetchall()
        )

        summary = _row_to_product_summary(row)
        summary["colors"] = json.loads(row["colors"])
        summary["search_tags"] = json.loads(row["search_tags"])
        summary["sizes"] = [{"size": s["size"], "quantity": s["quantity"]} for s in sizes]
        summary["total_stock"] = sum(s["quantity"] for s in sizes)
        return summary
    finally:
        conn.close()
