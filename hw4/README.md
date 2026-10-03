# Campus Customs

A React + Vite + TypeScript storefront for a fictional Yale campus apparel
shop, with a Python FastAPI backend whose chat assistant is a real
PydanticAI agent — grounded entirely in a local SQLite catalogue/inventory
database, never inventing a price or a stock count.

Every AI model call runs on the developer's own Claude Code subscription via
the `claude` CLI (`backend/llm/claude_client.py`) — **not** an API key.
`ANTHROPIC_API_KEY` is explicitly scrubbed from the child process even if
one happens to be set in your shell, so it can never silently take over.

See `AI_prompts.md` for the problem-by-problem build log, and `output/` for
the design/usability/system writeups (`harness.md` is the full system
reference: models, tools, safety rules, specs).

## Prerequisites

- **Node.js** 18+ and npm
- **Python** 3.11+
- **The `claude` CLI**, installed and logged in to your own Claude Code
  subscription. Run `claude` once in a terminal and follow the login prompt
  before starting the backend — the chat feature calls out to this CLI on
  every message, so if it isn't authenticated, chat replies will fail.

## 1. Get the data pack

All commands below are run from this `hw4/` folder (after
`git clone <repo-url> && cd <repo>/hw4`).

The database and product photos are **not** in this repo (see `.gitignore`)
— they're the assignment's own data pack. Unzip it so you end up with:

```
data/
├── campus_customs.db
└── products/          # product photos referenced by the catalogue
```

`data/` sits inside `hw4/`, alongside `frontend/` and `backend/`.

## 2. Backend setup

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r ../requirements.txt
uvicorn main:app --reload --port 8000
```

The API is now at `http://localhost:8000`. (`.env.example` exists for the
standard convention, but there's nothing to actually configure — see the
comments in that file for why.)

## 3. Frontend setup

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

The site is now at `http://localhost:5173` — the dev server proxies `/api`
and `/media` to the backend on port 8000, so both need to be running.

## 4. Try it

- Browse products, or use the search/filter on the Products page.
- Log in with the seed test account: `test@campuscustoms.yale.edu` /
  `password` (or create a new one — signup works end to end).
- Open the chat widget (bottom right) and ask something like "what hoodies
  do you have?" or "do you have this in a small?" on a product page —
  answers are grounded in the same database the site displays, including
  honest out-of-stock answers.

## Project layout

```
hw4/
├── AI_prompts.md          # every prompt given to the AI vibe coder, problem by problem
├── requirements.txt        # backend Python dependencies
├── .env.example
├── .gitignore
├── README.md               # this file
├── frontend/                # Vite + React + TypeScript app
├── backend/
│   ├── main.py              # FastAPI app — run with: uvicorn main:app --reload --port 8000
│   ├── agent.py              # PydanticAI agent + FunctionModel wiring
│   ├── models.py              # Pydantic types (catalogue, chat, audit, ...)
│   ├── tools.py                # the agent's tools (search/description/price/stock/reply)
│   ├── prompts/prompt.md        # the agent's system prompt (voice, grounding, safety)
│   ├── auth.py                # signup/login, password hashing
│   ├── database.py             # catalogue/inventory DB access
│   ├── chat_history.py          # persisted chat history for logged-in shoppers
│   ├── audit.py                # append-only agent-loop audit log
│   └── llm/claude_client.py     # the subscription-only model transport
└── output/
    ├── harness.md              # full system reference (models/tools/safety/specs)
    ├── design.md                # design pass writeup
    ├── usability.md              # usability improvements writeup
    ├── app_check.html             # live app check with screenshots
    ├── app_check_images/           # screenshots linked from app_check.html
    └── audit_trail.json            # append-only agent-loop activity log
```

`data/` (the local-only data pack — `campus_customs.db` and `products/`) is
gitignored and expected to sit inside `hw4/` alongside the folders above;
see step 1.
