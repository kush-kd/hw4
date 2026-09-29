# Usability improvements

Two front-end, two agent/backend. Each one below names a real gap found by testing the running app (not a hypothetical), what was added, and why it matters to a Campus Customs shopper or the business — then gets verified against the live app after the fact.

## Front-end #1: Mobile navigation actually reaches every link

**The gap, confirmed by testing:** at a real phone width (375px), the nav bar's old rule (`NavBar.css`) simply hid "Log in" and "Log out" outright with `display: none` and nothing to replace them — there was no menu, no icon, no way to reach them at all. A guest shopper on a phone could see "Create account" but had no way to find "Log in." A logged-in shopper on a phone had no way to log out.

**What was added:** a real hamburger menu (`NavBar.tsx`/`NavBar.css`) that appears only below 760px, replacing the old blanket-hiding rule. Tapping it opens a full-width dropdown listing every link the desktop nav has — Home, Products, About Us, then Log in/Create account or "Signed in as {name}"/Log out — each a full-height tappable row, closing itself on navigation or on logout. Desktop layout (>760px) is untouched.

**Why it helps:** most shopping traffic is mobile. A shopper who can't find "Log in" on their phone either can't restore their saved chat history (Problem 8) or gives up — that's a real, avoidable drop-off, not a cosmetic nitpick.

**Verified:** screenshotted at 375×812 before (Log in/Log out both invisible, no alternative) and after (hamburger opens, every link present and tappable, confirmed "Log in" navigates to `/login` and closes the menu); confirmed desktop (1440px) is pixel-identical to before.

## Front-end #2: A real 404 page instead of a blank one

**The gap, confirmed by testing:** the router had no catch-all route. Navigating to any URL that isn't one of the exact defined paths — a typo, an old bookmark, a dead link from somewhere else — rendered the nav bar and footer with a completely blank white `<main>` in between. No message, no way back except the browser's back button.

**What was added:** `pages/NotFound.tsx`, matching the site's own design system (same type, same button styles), with a short explanation and two ways to recover — "Back to Home" and "Browse products" — wired up as the router's `path="*"` catch-all in `App.tsx`.

**Why it helps:** a dead-end blank page is a lost visitor with no next step — actively bad for the business (a shopper who hits a blank page assumes the site is broken and leaves) versus one clean recovery screen that keeps them shopping.

**Verified:** navigated to a nonexistent path before (blank `<main>`, confirmed via screenshot) and after (full 404 page renders); clicked "Back to Home" and confirmed it lands on `/`.

## Agent/backend #1: Typo-tolerant catalogue search (more accurate)

**The gap, confirmed by testing:** `tools.search_catalogue`'s keyword matching was exact-substring only. Real, plausible typos returned zero matches — tested `sweatshirst` (for "sweatshirt") and `jaket` (for "jacket") against the live catalogue and both came back empty, which means the agent would have honestly-but-wrongly told a shopper "we don't carry that," even though the catalogue has dozens of matching items.

**What was added:** a similarity-ratio fallback in `_token_matches_word` (`difflib.SequenceMatcher`, threshold 0.85) that only kicks in when the existing substring check doesn't match. The threshold was picked by checking it against real near-miss pairs, not guessed: it catches `sweatshirst`↔`sweatshirt` (0.95), `jaket`↔`jacket` (0.91), and `crewnek`↔`crewneck` (0.93), while staying below `shirt`↔`short` (0.80) — two genuinely different garment words that must not collapse into the same typo.

**Why it helps:** a shopper who mistypes a garment name shouldn't be told the shop doesn't carry something it actually does — that's a false negative that costs a sale for no reason. This makes the agent's answers more accurate to what the catalogue actually contains, exactly the "more accurate" improvement category this problem asks for.

**Verified:** re-ran `sweatshirst`, `jaket`, and `crewnek` after the fix — all now return real, correctly-categorized products (checked their actual `garment_type`/tags to confirm the matches make sense, not just that *something* came back) — and re-confirmed the Problem 8 size-word fix (`"do you have this in a large?"`) still correctly returns zero catalogue matches so the page-context fallback still fires, i.e. this didn't quietly undo an earlier fix.

## Agent/backend #2: Bounded conversation cost (faster / cheaper)

**The gap, confirmed by reading the code, not assumed:** the backend is stateless per request — Problem 8's history only persists to the database, but the live prompt sent to the model on every single message rebuilds itself from the *entire* `history` list the frontend sends. Nothing capped how large that could get. A long-running conversation would resend more and more transcript on every turn, so cost and latency for the one real `claude -p` call would climb without bound the longer a shopper kept chatting — worse right when a shopper is most engaged.

**What was added:** two guardrails, both applied before any model call happens:
1. `ChatRequest.message` now has `max_length=2000` (`models.py`) — an oversized message is rejected by Pydantic validation at the API boundary with an instant 422, before the request handler (and so the paid model call) ever runs.
2. `tools.compose_reply` now only includes the most recent `MAX_HISTORY_TURNS = 10` turns in the prompt it builds, regardless of how long the full conversation has gotten, so every turn costs roughly the same instead of growing with conversation length.

**Why it helps:** this is a direct cost and latency control for the business (the subscription-routed model call is the expensive/slow part of every chat turn) without changing what a shopper experiences in an ordinary conversation — ordinary questions never come close to 10 turns of relevant context or 2000 characters. It also closes off a crude cost-abuse vector: without the length cap, nothing stopped a single message from being arbitrarily large.

**Verified:** unit-tested the trim directly (30 synthetic turns → confirmed exactly the last 10 survive, in order); sent a 2500-character message to the live running API and confirmed it comes back `422` immediately (checked no chat call was made — the validation error is Pydantic's own, produced before `main.py`'s route body executes); re-sent a normal chat message afterward and confirmed the assistant still replies correctly, so the guardrails don't interfere with real usage.
