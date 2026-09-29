# Design pass (Problem 10)

Builds on the earlier visual pass (Problem 3 follow-up: type system, hero collage, footer, card shadows). This round adds motion, real-data product presentation, and a chat experience designed to lower the barrier to that first message — concrete changes, each backed by real data, not decoration for its own sake.

## What changed

**Scroll-reveal motion system** — `Reveal`/`useInView` (IntersectionObserver-based, respects `prefers-reduced-motion`). Applied to Home's highlight cards, featured picks (staggered), and the About page. Sections arrive as the shopper scrolls instead of all appearing flat at once.

**Animated stat counters** — Home's "100+ styles / 11 colleges / 6 sizes" count up from 0 when they scroll into view (`StatCounter` + `useCountUp`), instead of static text.

**Product cards now show real color swatches and a truthful "low stock" badge.** Extended `/api/products` (and the chat agent's product responses) to include `colors` and `total_stock` — the same fields already used on the detail page and by the chat agent, so nothing here is invented. A card shows "Low stock — N left" only when `total_stock` is genuinely ≤20 (checked against the real distribution: 4 of 102 products qualify, not an arbitrary label slapped on everything).

**Chat: suggestion chips + an invite pulse.** The first time a shopper opens the chat with no conversation yet, three tappable prompts appear ("Show me hoodies," "What crewnecks do you have?," "Anything under $40?") instead of a blank input waiting to be filled. The launcher button also gives a soft pulse a couple seconds after page load (once, never again after it's opened) so shoppers who don't know a chatbot exists notice it.

**A collegiate texture, not a flat gradient.** A faint diagonal pinstripe sits under the hero and footer's navy gradient — subtle enough to not read as "busy," but enough to make the brand feel considered rather than templated. Reused a "game day red" accent (already used for form errors) for the low-stock badge, so urgent/attention colors stay consistent site-wide instead of introducing a new one-off color.

## Why it should help customers stick around and buy

- **Motion gives the page a pulse instead of a wall of static sections** — shoppers scroll further because something keeps happening, which is more time in front of product and more chances to notice something they want.
- **Truthful scarcity ("Low stock — 9 left") is a proven, honest nudge toward buying now** rather than bookmarking and forgetting — and because it's sourced from the same real inventory numbers the chat agent already grounds itself in, it can't drift into the kind of fake urgency that erodes trust the moment someone notices it's always "almost sold out."
- **Suggestion chips remove the "what do I even ask a chatbot" hesitation** that kills first-touch engagement — a shopper who never types their first message never gets the honest price/stock answer that's this site's actual differentiator. Chips make that first message a tap, not a typing task.
- **A site that feels considered (texture, timed motion, a color system used consistently) reads as more trustworthy than a flat template** — and trust is what turns "just Browse" into "actually buy," especially for a fictional shop's chatbot claiming to check real stock.

## Verified

- Color swatches and low-stock badge checked against live `/api/products` data (confirmed the swatch colors match `colors`, and exactly the 4 products with `total_stock ≤ 20` show the badge, not more, not fewer).
- Count-up, scroll-reveal, and the chat invite pulse all confirmed firing correctly in the browser (screenshotted mid-animation and after).
- Suggestion chip clicked end-to-end: sent a real message, got a grounded reply, and the results shelf populated with real product cards (swatches included, since it's the same `ProductCard` component).
- Re-ran `npx tsc --noEmit` (clean) and checked the backend logs after all changes (no errors) before calling this done.

## Second pass — fixing what actually looked generic, not just adding more

The first pass above was real polish, but on a second honest look the page still read as a well-styled SaaS template wearing Yale colors, not a heritage collegiate brand. Three specific, fixable problems, not vague "make it fancier":

**The hero photo collage looked like a mistake.** 73 of the 102 catalogue photos are shot on black, 29 on white/near-white — and the hero was blindly using `products.slice(0, 3)` (first 3 alphabetically), which happened to mix a white-backdrop photo with two black-backdrop ones. Overlapping, rotated tiles with clashing backgrounds reads as a bug, not a design choice — confirmed by checking the actual pixel colors of the source images before touching any CSS. Fixed by curating three specific, checked black-backdrop products (hoodie/crewneck/tee) for the hero instead of taking whatever loads first. (The regular product grid was never actually broken by this — each card has its own bordered frame, so a mixed photo background doesn't clash there; only the hero's tight overlapping composite did.)

**There was no real brand mark.** A gold rounded square with "CC" in it reads as a placeholder, not a logo — because it is one. Replaced it everywhere (nav, footer, mobile menu) with an actual designed shield crest (`Crest.tsx`, inline SVG), the classic collegiate-heritage device, plus a large, very low-opacity version watermarked into the hero background for depth. This is the single highest-leverage change for "looks like a professional website" — a real logo versus initials-in-a-box is the difference most people register first, even subconsciously.

**Everything was navy, white, or cool gray — no warmth.** Heritage/collegiate brands (Yale's own merch, J.Crew's collegiate line) lean on warm neutrals, not sterile SaaS white. Added a cream tone (`--cream`) used for the stats strip and the highlight cards, plus small gold icon glyphs on each highlight card (a mini crest, a check, a pennant) so they're not just text in a box. Also added a subtle entrance animation to the hero copy on load, so the page doesn't feel static even before anyone scrolls.

**Verified again after this pass:** screenshotted the hero at desktop and mobile widths (collage now three consistent black-backdrop photos, watermark visible but not distracting), confirmed the crest renders correctly at every size it's used (32px nav, 34px footer, 340px watermark) without distortion, re-ran `tsc --noEmit` (clean), and re-checked the browser console (no errors) after all of it.
