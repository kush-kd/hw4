"""
Sonnet 5 calls routed through the local Claude Code CLI.

Every model call in this project goes through `claude -p` (headless mode),
which authenticates with the user's Claude Code *subscription*. No API key is
read or required -- ANTHROPIC_API_KEY is explicitly scrubbed from the child
environment so a stray key can never silently take over billing. Same
approach as HW3's llm/claude_client.py, adapted for a chat backend instead of
a batch CLI script.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

MODEL = "claude-sonnet-5"
DEFAULT_TIMEOUT = 60
MAX_ATTEMPTS = 3


class ClaudeError(RuntimeError):
    """A model call failed."""


class AuthError(ClaudeError):
    """The Claude Code subscription session is not usable."""

    HINT = (
        "Claude Code is not authenticated.\n"
        "Open a terminal, run `claude`, and complete the browser login "
        "(or `/login` inside the session). Then re-run this script."
    )

    def __init__(self, detail: str = "") -> None:
        super().__init__(f"{self.HINT}\n\nCLI said: {detail}".rstrip())


@dataclass
class Reply:
    """One model response plus the bookkeeping we care about."""

    text: str
    cost_usd: float = 0.0
    duration_ms: int = 0
    num_turns: int = 0
    session_id: str = ""
    raw: dict[str, Any] = field(default_factory=dict)

    def json(self) -> Any:
        """Parse the reply as JSON, tolerating prose or code fences around it."""
        return _extract_json(self.text)


def _cli() -> str:
    path = shutil.which("claude")
    if not path:
        raise ClaudeError(
            "The `claude` CLI is not on PATH. Install Claude Code first: "
            "https://claude.com/claude-code"
        )
    return path


def _child_env() -> dict[str, str]:
    """Environment for the child CLI, with any API key removed.

    The assignment requires subscription auth. Dropping these vars guarantees
    the child cannot fall back to metered API billing.
    """
    env = os.environ.copy()
    for var in ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_BASE_URL"):
        env.pop(var, None)
    # Avoid inheriting this session's own agent context.
    env.pop("CLAUDE_CODE_SSE_PORT", None)
    env.pop("CLAUDECODE", None)
    return env


_AUTH_SIGNS = (
    "oauth session expired",
    "failed to authenticate",
    "invalid api key",
    "please run `claude login`",
    "not logged in",
    "authentication_error",
)


def _looks_like_auth_failure(text: str) -> bool:
    low = text.lower()
    return any(sign in low for sign in _AUTH_SIGNS)


def _extract_json(text: str) -> Any:
    """Pull a JSON value out of a model reply.

    Handles: bare JSON, ```json fenced blocks, and JSON preceded/followed by
    commentary. Raises ClaudeError if nothing parses.
    """
    text = text.strip()
    if not text:
        raise ClaudeError("Model returned an empty reply.")

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    fenced = re.findall(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    for block in fenced:
        try:
            return json.loads(block.strip())
        except json.JSONDecodeError:
            continue

    for opener, closer in (("{", "}"), ("[", "]")):
        start, end = text.find(opener), text.rfind(closer)
        if start != -1 and end > start:
            try:
                return json.loads(text[start : end + 1])
            except json.JSONDecodeError:
                continue

    raise ClaudeError(f"Could not parse JSON from model reply:\n{text[:800]}")


def call(
    prompt: str,
    *,
    system: str | None = None,
    timeout: int = DEFAULT_TIMEOUT,
    attempts: int = MAX_ATTEMPTS,
    model: str = MODEL,
) -> Reply:
    """Send one prompt to the model via the Claude Code CLI and return the reply."""
    cmd = [
        _cli(),
        "-p",
        prompt,
        "--model",
        model,
        "--output-format",
        "json",
        "--permission-mode",
        "dontAsk",
        "--allowedTools",
        "",
    ]
    if system:
        cmd += ["--append-system-prompt", system]

    last: Exception | None = None
    for attempt in range(1, attempts + 1):
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                env=_child_env(),
                cwd=str(Path(__file__).resolve().parent.parent),
            )
        except subprocess.TimeoutExpired:
            last = ClaudeError(f"Model call timed out after {timeout}s.")
            if attempt < attempts:
                time.sleep(2 * attempt)
                continue
            raise last

        blob = (proc.stdout or "") + (proc.stderr or "")
        if _looks_like_auth_failure(blob):
            raise AuthError(blob.strip()[:400])

        if proc.returncode != 0:
            last = ClaudeError(f"claude exited {proc.returncode}.\n{blob.strip()[:800]}")
            if attempt < attempts:
                time.sleep(2 * attempt)
                continue
            raise last

        try:
            env_obj = json.loads(proc.stdout)
        except json.JSONDecodeError:
            last = ClaudeError(f"Unparseable CLI envelope:\n{proc.stdout[:800]}")
            if attempt < attempts:
                time.sleep(2 * attempt)
                continue
            raise last

        if env_obj.get("is_error"):
            last = ClaudeError(f"Model reported an error: {env_obj.get('result')!r}")
            if attempt < attempts:
                time.sleep(2 * attempt)
                continue
            raise last

        return Reply(
            text=env_obj.get("result", ""),
            cost_usd=float(env_obj.get("total_cost_usd") or 0.0),
            duration_ms=int(env_obj.get("duration_ms") or 0),
            num_turns=int(env_obj.get("num_turns") or 0),
            session_id=env_obj.get("session_id", ""),
            raw=env_obj,
        )

    raise last or ClaudeError("Model call failed for an unknown reason.")


def call_json(prompt: str, **kw: Any) -> Any:
    """`call`, but insist the reply parses as JSON (one automatic re-ask)."""
    reply = call(prompt, **kw)
    try:
        return reply.json()
    except ClaudeError:
        strict = f"{prompt}\n\nCRITICAL: reply with raw JSON only. No prose, no markdown fences."
        return call(strict, **kw).json()


def preflight() -> str:
    """Cheap check that subscription auth works. Returns the model's reply."""
    return call("Reply with exactly: OK", timeout=30, attempts=1).text.strip()
