"""
Append-only audit trail for every chat turn (Problem 12).

output/audit_trail.json is a single flat JSON array that only ever grows.
Every `/api/chat` call gets its own `run_id`, and every step the deterministic
brain takes inside that call -- each tool call, plus the final structured-
output step -- appends one `AuditEntry` (models.py) the moment that step
completes, not batched at the end. A run that errors partway through still
leaves a usable partial trail. The file survives across separate requests and
process restarts (never wiped) -- same pattern as HW3's audit.py.

"Append" here means read-modify-write on one JSON array (matching the
assignment's .json extension, not .jsonl), so it's append-only from the
outside -- nothing already written is ever removed or overwritten -- without
being a true O(1) filesystem append. At the scale of a homework chat agent's
own audit trail this is a non-issue.
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any, Callable, Iterator

from models import AuditEntry

ROOT = Path(__file__).resolve().parent.parent
AUDIT_PATH = ROOT / "output" / "audit_trail.json"


def new_run_id() -> str:
    return uuid.uuid4().hex[:12]


def append_entry(entry: AuditEntry, path: Path | None = None) -> None:
    """Append one entry, never truncating whatever is already there.

    `path` defaults to the module-level `AUDIT_PATH`, resolved at call time
    (not as a bound default) so it can be swapped for tests.
    """
    if path is None:
        path = AUDIT_PATH
    existing: list[dict[str, Any]] = []
    if path.is_file():
        try:
            loaded = json.loads(path.read_text())
            if isinstance(loaded, list):
                existing = loaded
        except json.JSONDecodeError:
            existing = []  # corrupt file: don't crash the run over the audit log itself
    existing.append(json.loads(entry.model_dump_json()))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(existing, indent=2))


def summarize(value: Any, max_len: int = 220) -> str:
    """Short, safe text summary of a tool argument or return value.

    Deliberately not a full raw dump: `get_stock` on 5 candidates is 30
    size/quantity pairs, and an audit log that repeats that in full on every
    step stops being readable as an audit log. Works generically off
    duck-typed pydantic models (anything with `.product_id`) rather than
    importing every model type, so a new tool with a new return type doesn't
    need audit.py updated to stay readable.
    """

    def render(v: Any) -> str:
        if isinstance(v, list) and v and hasattr(v[0], "product_id"):
            ids = [item.product_id for item in v[:5]]
            more = f" (+{len(v) - 5} more)" if len(v) > 5 else ""
            return f"{len(v)} item(s): {ids}{more}"
        if isinstance(v, list) and v and hasattr(v[0], "role") and hasattr(v[0], "content"):
            return f"{len(v)} turn(s) of prior history"
        if isinstance(v, list):
            return f"{len(v)} item(s)"
        if isinstance(v, dict):
            return ", ".join(f"{k}={render(val)}" for k, val in v.items())
        if hasattr(v, "model_dump"):
            return render(v.model_dump())
        return str(v)

    try:
        s = render(value)
    except Exception as exc:  # audit logging must never break the run it's watching
        s = f"<unsummarizable {type(value).__name__}: {exc}>"

    s = " ".join(s.split())  # collapse whitespace/newlines to one line
    return s if len(s) <= max_len else s[: max_len - 1] + "…"


def log_step(run_id: str, iteration: int, tool_name: str, args: Any, result: Any, stop_reason: str = "continue") -> None:
    entry = AuditEntry(
        run_id=run_id,
        iteration=iteration,
        tool_name=tool_name,
        args_summary=summarize(args),
        result_summary=summarize(result),
        stop_reason=stop_reason,
    )
    append_entry(entry)


def run_and_log(
    run_id: str, counter: Iterator[int], tool_name: str, args: Any, fn: Callable, *fn_args: Any, **fn_kwargs: Any
) -> Any:
    """Call `fn`, log one entry for it (success or failure), then return its
    result or re-raise. Keeps auditing out of tools.py's own business logic
    -- agent.py's tool wrappers are the one place each tool is actually
    invoked, same as HW3."""
    try:
        result = fn(*fn_args, **fn_kwargs)
    except Exception as exc:
        log_step(run_id, next(counter), tool_name, args, f"ERROR: {type(exc).__name__}: {exc}", stop_reason="error")
        raise
    log_step(run_id, next(counter), tool_name, args, result)
    return result
