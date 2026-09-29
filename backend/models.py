from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field


class SizeStock(BaseModel):
    size: str
    quantity: int


class ProductCard(BaseModel):
    """A catalogue item enriched with stock — the same shape the REST
    /api/products/{id} endpoint already returns, so chat results and the
    Products/detail pages agree on one product shape on the frontend. This is
    what main.py hands back to the browser; it is NOT what the agent reasons
    over internally (see CandidateProduct below)."""

    product_id: str
    name: str
    garment_type: str
    description: str
    price: float
    image_url: str
    colors: list[str] = Field(default_factory=list)
    sizes: list[SizeStock]
    total_stock: int


# --- Problem 6: one small, single-purpose result type per lookup tool ---
# Each carries product_id + name alongside the one fact it looked up, so a
# tool's result is self-describing on its own (readable in isolation, e.g.
# in logs) without forcing a join back to some other tool's output just to
# know which product it was.


class ProductMatch(BaseModel):
    """search_catalogue's result: which products matched, not their details."""

    product_id: str
    name: str


class ProductDescription(BaseModel):
    product_id: str
    name: str
    description: str


class ProductPrice(BaseModel):
    product_id: str
    name: str
    price: float


class ProductStock(BaseModel):
    product_id: str
    name: str
    sizes: list[SizeStock]
    total_stock: int


class CandidateProduct(BaseModel):
    """The merged view compose_reply reasons over — one row per matched
    product, assembled from the three lookup tools' results by product_id."""

    product_id: str
    name: str
    description: str
    price: float
    sizes: list[SizeStock]
    total_stock: int


class ChatTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str
    # Product ids the assistant showed alongside this turn, if any — carried
    # in the history so a vague follow-up ("do you have it in medium?") can
    # be resolved against what was just being discussed.
    product_ids: list[str] = Field(default_factory=list)


class ChatUser(BaseModel):
    """Who's chatting — the same public shape /api/auth/login and
    /api/auth/signup already return. Sent by the frontend from the session it
    already holds; see harness.md Problem 8 for the trust model this implies
    (there's still no server-side session token, per the note left in
    Problem 4's harness entry)."""

    id: int
    first_name: str
    last_name: str
    email: str


class PageContext(BaseModel):
    """What the shopper is looking at right now, so "do you have this in
    pink?" on a product page can resolve without the item being named."""

    product_id: str | None = None


class ChatRequest(BaseModel):
    # Problem 9 (agent cost/safety improvement): max_length rejects an
    # oversized message at the API boundary with a fast 422 — before it ever
    # reaches the agent or the one paid model call, not after.
    message: str = Field(min_length=1, max_length=2000)
    history: list[ChatTurn] = Field(default_factory=list)
    user: ChatUser | None = None
    page_context: PageContext | None = None


class ChatReply(BaseModel):
    """Structured output the agent must produce."""

    reply: str
    product_ids: list[str] = Field(default_factory=list)


class ChatResponse(BaseModel):
    reply: str
    products: list[ProductCard] = Field(default_factory=list)


class ChatHistoryTurn(BaseModel):
    """One saved turn, replayed with products already expanded to full
    ProductCards (same shape a live chat response uses) so the frontend can
    render restored history exactly like a live conversation."""

    role: Literal["user", "assistant"]
    content: str
    products: list[ProductCard] = Field(default_factory=list)


class ChatHistoryResponse(BaseModel):
    messages: list[ChatHistoryTurn] = Field(default_factory=list)


class AuditEntry(BaseModel):
    """One row in the append-only output/audit_trail.json — one entry per
    agent-loop step (each tool call the deterministic brain makes, plus the
    final structured-output step), written the moment that step completes."""

    run_id: str = Field(description="Shared by every entry from one /api/chat call.")
    iteration: int = Field(description="1-based step number within this run.")
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat(timespec="seconds"))
    tool_name: str
    args_summary: str = ""
    result_summary: str = ""
    stop_reason: str = Field(default="continue", description="'continue', 'run_complete', or 'error'.")
