"""
Campus Customs shop chatbot -- agent entry point.

Built the same way as HW3's growth agent: a real PydanticAI `Agent` with real
`@agent.tool`/`@agent.tool_plain` tools (tools.py), a real `output_type`
(`ChatReply` in models.py), and a system prompt loaded from prompts/prompt.md.

Model transport: the assignment requires every AI call to run on the Claude
Code subscription via `claude -p` (see llm/claude_client.py), never an API
key. PydanticAI's built-in Anthropic model talks to the Anthropic API
directly with a key -- wrong transport here -- and `claude -p` already runs
its own internal agent loop and hands back one final result, not a live
stream of tool_use blocks, so there's no wire-level tool-calling protocol to
relay into PydanticAI's tool graph either way.

The fix is the same escape hatch HW3 used: `FunctionModel`, a "model" that is
really just a local Python function (`_brain`) deciding what happens next.
Here that function is a small deterministic state machine: search the
catalogue -> (fall back to page context, then the last-discussed products, if
nothing matched) -> look up each match's real description/price/stock
(Problem 6's three single-purpose tools) -> compose the actual reply -> return
PydanticAI's structured output. The one step that touches the network is
`compose_reply` in tools.py, which goes through the subscription CLI.
`FunctionModel` itself never touches the network.

Problem 8 adds `ChatDeps`: PydanticAI's real dependency-injection mechanism,
carrying who's chatting (if logged in) and what page they're on. The brain
itself doesn't need deps -- it's just deciding which tool to call next -- but
`compose_reply` is a genuine `@agent.tool` that receives `RunContext[ChatDeps]`
so it can personalize/ground its one real model call without the caller having
to thread that state through every tool signature by hand.

Problem 12 adds the audit trail: every tool call below is wrapped in
`audit.run_and_log`, and the brain's final structured-output step logs itself
directly -- see audit.py and output/audit_trail.json.
"""

from __future__ import annotations

import itertools
import os
from dataclasses import dataclass

# Must be set before pydantic_ai is imported: silences its startup banner so
# this process's stdout/stderr stays clean.
os.environ.setdefault("PYDANTIC_AI_NO_BANNER", "1")

from pathlib import Path  # noqa: E402

from pydantic_ai import Agent, RunContext  # noqa: E402
from pydantic_ai.messages import ModelResponse, ToolCallPart, ToolReturnPart  # noqa: E402
from pydantic_ai.models.function import AgentInfo, FunctionModel  # noqa: E402

import audit  # noqa: E402
import tools  # noqa: E402
from models import (  # noqa: E402
    CandidateProduct,
    ChatReply,
    ChatTurn,
    ChatUser,
    PageContext,
    ProductDescription,
    ProductMatch,
    ProductPrice,
    ProductStock,
)

ROOT = Path(__file__).resolve().parent
PROMPT_PATH = ROOT / "prompts" / "prompt.md"


@dataclass
class ChatDeps:
    """Who's chatting and what they're looking at -- Problem 8's "agent deps"."""

    user: ChatUser | None
    page_context: PageContext | None


def _load_system_prompt() -> str:
    if not PROMPT_PATH.is_file():
        raise RuntimeError(f"Missing system prompt file: {PROMPT_PATH}")
    return PROMPT_PATH.read_text()


def _returns_by_tool(messages) -> dict[str, object]:
    """Every ToolReturnPart seen so far, keyed by tool name -> its `.content`."""
    out: dict[str, object] = {}
    for m in messages:
        for part in getattr(m, "parts", []):
            if isinstance(part, ToolReturnPart):
                out[part.tool_name] = part.content
    return out


def _last_discussed_product_ids(history: list[ChatTurn]) -> list[str]:
    """Continuity for vague follow-ups ("do you have it in medium?"): the
    product ids the assistant most recently showed, if any."""
    for turn in reversed(history):
        if turn.role == "assistant" and turn.product_ids:
            return turn.product_ids
    return []


def _fallback_product_ids(history: list[ChatTurn], page_context: PageContext | None) -> list[str]:
    """When the keyword search finds nothing, what should "this"/"it" resolve
    to? The page the shopper is currently on is a stronger, more current
    signal than something discussed earlier in the conversation, so it wins
    when both are available."""
    if page_context and page_context.product_id:
        return [page_context.product_id]
    return _last_discussed_product_ids(history)


def _merge_candidates(
    ids: list[str],
    descriptions: list[ProductDescription],
    prices: list[ProductPrice],
    stock: list[ProductStock],
) -> list[CandidateProduct]:
    """Zip the three lookup tools' results back together by product_id into
    one row per product for compose_reply to reason over.

    Found by testing, not by inspection: the output used to follow Python
    dict insertion order, which followed SQL's `WHERE product_id IN (...)`
    result order -- and SQLite does NOT preserve the input list's order for
    an IN clause. That silently discarded search_catalogue's relevance
    ranking, so the actual best match for a question naming one specific
    product could end up buried behind less-relevant, similarly-named
    look-alikes (e.g. "Crew Left Chest Hoodie" behind "Baseball Left Chest
    Crewneck") in the JSON the model reads -- and reproducibly caused the
    model to report a real 12-in-stock size as sold out. Rebuilding the list
    in `ids` order (search_catalogue's actual ranking) puts the most relevant
    product first every time.
    """
    by_id: dict[str, dict] = {}
    for d in descriptions:
        by_id.setdefault(d.product_id, {"product_id": d.product_id, "name": d.name})["description"] = d.description
    for p in prices:
        by_id.setdefault(p.product_id, {"product_id": p.product_id, "name": p.name})["price"] = p.price
    for s in stock:
        entry = by_id.setdefault(s.product_id, {"product_id": s.product_id, "name": s.name})
        entry["sizes"] = s.sizes
        entry["total_stock"] = s.total_stock
    required = {"description", "price", "sizes", "total_stock"}
    return [CandidateProduct(**by_id[pid]) for pid in ids if pid in by_id and required.issubset(by_id[pid])]


def make_chat_brain(
    user_message: str,
    history: list[ChatTurn],
    page_context: PageContext | None,
    run_id: str,
    counter: "itertools.count[int]",
):
    fallback_ids = _fallback_product_ids(history, page_context)

    def brain(messages, info: AgentInfo) -> ModelResponse:
        seen = _returns_by_tool(messages)

        if "search_catalogue" not in seen:
            return ModelResponse(
                parts=[ToolCallPart(tool_name="search_catalogue", args={"query": user_message})]
            )

        matches: list[ProductMatch] = seen["search_catalogue"]
        ids = [m.product_id for m in matches] or fallback_ids

        if "get_descriptions" not in seen:
            return ModelResponse(
                parts=[ToolCallPart(tool_name="get_descriptions", args={"product_ids": ids})]
            )
        if "get_prices" not in seen:
            return ModelResponse(
                parts=[ToolCallPart(tool_name="get_prices", args={"product_ids": ids})]
            )
        if "get_stock" not in seen:
            return ModelResponse(
                parts=[ToolCallPart(tool_name="get_stock", args={"product_ids": ids})]
            )

        if "compose_reply" not in seen:
            candidates = _merge_candidates(ids, seen["get_descriptions"], seen["get_prices"], seen["get_stock"])
            return ModelResponse(
                parts=[
                    ToolCallPart(
                        tool_name="compose_reply",
                        args={"user_message": user_message, "history": history, "candidates": candidates},
                    )
                ]
            )

        final = dict(seen["compose_reply"])
        out_tool = info.output_tools[0].name
        audit.log_step(run_id, next(counter), out_tool, {}, final, stop_reason="run_complete")
        return ModelResponse(parts=[ToolCallPart(tool_name=out_tool, args=final)])

    return brain


def build_agent(
    user_message: str,
    history: list[ChatTurn],
    page_context: PageContext | None,
    run_id: str,
    counter: "itertools.count[int]",
) -> Agent:
    system_prompt = _load_system_prompt()
    agent = Agent(
        model=FunctionModel(make_chat_brain(user_message, history, page_context, run_id, counter)),
        output_type=ChatReply,
        system_prompt=system_prompt,
        deps_type=ChatDeps,
    )

    @agent.tool_plain
    def search_catalogue(query: str) -> list[ProductMatch]:
        """Keyword-score the catalogue for products matching the shopper's message. No model call."""
        return audit.run_and_log(run_id, counter, "search_catalogue", {"query": query}, tools.search_catalogue, query)

    @agent.tool_plain
    def get_descriptions(product_ids: list[str]) -> list[ProductDescription]:
        """Real product descriptions from campus_customs.db. No model call."""
        return audit.run_and_log(
            run_id, counter, "get_descriptions", {"product_ids": product_ids}, tools.get_descriptions, product_ids
        )

    @agent.tool_plain
    def get_prices(product_ids: list[str]) -> list[ProductPrice]:
        """Real prices from campus_customs.db. No model call."""
        return audit.run_and_log(
            run_id, counter, "get_prices", {"product_ids": product_ids}, tools.get_prices, product_ids
        )

    @agent.tool_plain
    def get_stock(product_ids: list[str]) -> list[ProductStock]:
        """Real per-size stock counts from campus_customs.db. No model call."""
        return audit.run_and_log(
            run_id, counter, "get_stock", {"product_ids": product_ids}, tools.get_stock, product_ids
        )

    @agent.tool
    def compose_reply(
        ctx: RunContext[ChatDeps], user_message: str, history: list[ChatTurn], candidates: list[CandidateProduct]
    ) -> dict:
        """The one real model call: write the shopper-facing reply, grounded only in the given candidates and
        aware of who's chatting (ctx.deps.user, if logged in)."""
        return audit.run_and_log(
            run_id,
            counter,
            "compose_reply",
            {"user_message": user_message, "candidates": candidates},
            tools.compose_reply,
            system_prompt,
            user_message,
            history,
            candidates,
            ctx.deps.user,
        )

    return agent


def chat(
    message: str,
    history: list[ChatTurn],
    user: ChatUser | None = None,
    page_context: PageContext | None = None,
) -> ChatReply:
    run_id = audit.new_run_id()
    counter = itertools.count(1)
    agent = build_agent(message, history, page_context, run_id, counter)
    try:
        result = agent.run_sync(message, deps=ChatDeps(user=user, page_context=page_context))
    except Exception as exc:
        audit.log_step(
            run_id, next(counter), "run", {"message": message}, f"ERROR: {type(exc).__name__}: {exc}", stop_reason="error"
        )
        raise
    return result.output
