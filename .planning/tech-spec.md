# Technical Specification — Brand Visibility Agent

# Tech Spec

This is the how. `prd.md` covers what and why, `schema.md` covers the exact data shapes — this doc is what actually gets built: the MCP server, the demo agent, error handling, and the real-vs-mock switch. Locked once I approve it, same as the other two.

One thing up front: the MCP Python SDK had a major version jump literally this week — v2 went stable on 2026-07-27 with a completely rebuilt internal architecture (session-based → stateless dispatcher). I'm pinning to v1.x on purpose below. v2 is brand new, has almost no tutorials or examples written against it yet, and any coding agent's training knowledge of "how MCP servers work in Python" is going to be v1-shaped. Building against v2 right now is just extra risk with zero upside for a three-week hackathon build. **Don't let this get "helpfully" upgraded later without checking with me first.**

---

## Stack

- **Language:** Python (matches the existing skeleton — `ai_client.py`, `step1_check.py` through `step4_prove.py`).
- **MCP SDK:** the official one, pinned: `mcp>=1.27,<2` in `requirements.txt`. Use the high-level `FastMCP` class (decorator-based tool functions, type hints become the schema — no manual JSON Schema writing needed). Confirm the exact import path against whatever version actually installs, since I'm working from general knowledge of the v1 API here, not a fresh read of the docs.
- **Transport:** stdio. The demo agent spawns the MCP server as a local subprocess and talks to it directly — no hosting, no network exposure, nothing that can go down mid-demo because a server crashed somewhere else. This is also just the standard local-MCP-server pattern, so there's plenty of precedent to build against.

---

## The MCP server

Two tools. Keeping this minimal on purpose — every extra tool is another thing that can misbehave live in front of judges.

**`get_brand_info(brand_id: str)`**
Returns the approved brand file content for one brand.

```
Input:  { "brand_id": "trailblaze-shoes" }
Output: { "found": true, "content": "<the full brand-info.llms.txt text>", "facts": [...] }
     or { "found": false }
```

Returns `found: false` for two different real situations — the brand doesn't exist, or it exists but isn't approved yet — and deliberately gives the same response either way. An agent (or a judge poking at the tool) shouldn't be able to tell the difference between "no such brand" and "not approved yet." That's not an accident, it's how unapproved data stays actually unreachable instead of just hidden by convention.

**`list_brands()`**
Returns every _approved_ brand, for the multi-brand demo (Stage 4).

```
Output: { "brands": [ { "brand_id": "...", "display_name": "..." }, ... ] }
```

Both tools read straight from `brands/<test|real>/<brand_id>/generated/brand-info.json` and only ever serve something where `approved == true`.

---

## The demo agent (Step 4 / Prove It)

This is the piece that has to actually work, live, twice, on demand. Two separate agent instances, same question:

- **Before:** no tools registered at all. It's not that it "chooses" not to look something up — it structurally can't. That's what makes this a real baseline and not a scripted strawman.
- **After:** `get_brand_info` (and `list_brands`) registered.

Rough system prompt for both:

```
You are a shopping assistant. A customer will ask a question about
products or brands. Answer helpfully and honestly. If you have access
to a get_brand_info tool, use it to check for verified information
about any specific brand the question is about before answering.
Only state specific claims about a brand that you can verify — from
the tool, or from your own general knowledge. Never invent details
about a brand you have no information on.
```

Both runs reuse the same underlying model-calling function from `ai_client.py` — no separate client code for the demo agent, just a thin tool-calling loop wrapped around it.

**On reliability for the live version specifically:** in mock mode this is fully scripted and 100% deterministic — the "before" mock always gives a generic answer, the "after" mock always calls the tool and returns the exact approved content. No live-model flakiness possible. In real mode, a live LLM is _choosing_ whether to call the tool, which is more impressive but does carry some risk of it just... not calling it, or answering oddly, in front of judges. Mitigations if we go real for the demo: low/zero temperature, test the after-run dozens of times beforehand to confirm it reliably calls the tool, and check whether the provider we end up with supports forcing a specific tool call as a fallback. I'll flag this as a decision for you at the end of this doc, because it's really a "how much risk do we want on demo day" call, not a technical one.

---

## Error handling

| Situation                                                                                         | Where                                    | What happens                                                                                                                                                                                                                                                                                                                 |
| ------------------------------------------------------------------------------------------------- | ---------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Website won't load / times out                                                                    | Step 1, initial fetch                    | Wait 10s, retry once, then `check.status = "error"`, `error_detail = "site_unreachable"`                                                                                                                                                                                                                                     |
| Page loads but there's almost nothing to extract (rough cutoff: under ~100 words of real content) | Step 1, content extraction               | Check still completes normally, but gets flagged so Step 2 can use `reason_code: "thin_content"`                                                                                                                                                                                                                             |
| An AI engine call or LLM call times out (real mode only)                                          | Step 1 engine queries, Step 4 demo agent | Wait 15s, retry once, then record that specific result as an error. **Never silently swap in a mock answer without showing it happened** — same "no silent substitution" rule we already hold Hermes to, applied to the system itself. If this happens live, the operator sees a visible error, not a quietly faked success. |
| MCP tool asked about an unknown or unapproved `brand_id`                                          | MCP server                               | Always `{found: false}` — see above, this is intentional, not an edge case to "fix" later                                                                                                                                                                                                                                    |

---

## Real-vs-mock table

Every piece of this system defaults to mock. Nothing flips to real on its own.

| Component                      | Mock (default)                                      | Flips to real only when                                                                                                                                       |
| ------------------------------ | --------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Step 1 — AI engine queries     | Canned/simulated responses from a local mock module | A valid provider key exists in `.env` **and** `config/settings.py`'s `REAL_MODE` flag has been manually set `True` — both conditions, not just a key existing |
| Step 3 — brand file generation | N/A — see note below                                | Stays rule-based always, real or mock mode doesn't change this                                                                                                |
| Step 4 — demo agent            | Scripted, deterministic before/after answers        | Same two-condition gate as Step 1                                                                                                                             |

**Why Step 3 stays rule-based even in real mode:** I'm deliberately choosing _not_ to use an LLM to write the generated brand file, even once we have a real API key. A simple rule-based extractor (pull the title, meta description, about-page text, listed products, off the actual HTML) is safer for the facts-only rule than asking an LLM to summarize — LLMs paraphrase and infer, which is exactly the failure mode the facts-only rule exists to prevent. It's also cheaper, faster, and fully deterministic, which matters for a live demo. This isn't a placeholder to "upgrade" later — it's the actual intended design.

---

## Repo hygiene (for the GitHub submission)

- `README.md` should cover: what the project is, a short paragraph mapping our 4 steps to Adobe's own Sense→Generate→Reach→Learn language, a "quick start" that runs entirely in mock mode with no key needed (`git clone`, `pip install -r requirements.txt`, `python run_demo.py`), and a short "enabling real mode" section (copy `.env.example` to `.env`, add a key, flip `REAL_MODE` in `settings.py`).
- `requirements.txt` doesn't exist yet — real dependencies aren't known until Stage 1 actually starts (the MCP package, an HTML parser, an HTTP client, etc.). Add it as a Stage 1 deliverable, not something to fake now.
- Before Stage 4 counts as done: run the full pipeline on at least 2–3 test brands from genuinely different categories (not three shoe brands) and confirm `business_type_detected`, the generated facts, and the MCP responses are actually different per brand — this is the check that proves nothing's secretly hardcoded to the one demo brand.

---

## One thing I actually want your call on

For the live judged demo (Step 4), do you want to:

1. **Run it in mock mode** — guaranteed to work every time, zero risk of a live API hiccup in front of judges, but it's a scripted simulation rather than a real model making a live decision, or
2. **Run it in real mode** — a real LLM actually deciding to use the tool live, more impressive and more honest to the "prove it" framing, but carries some chance of an off day right when it matters most.

My instinct is to build both, test real mode heavily in the days before, and quietly keep mock mode ready as a same-script fallback if anything about the real API looks shaky on demo day itself — but that's a risk-tolerance call, not a technical one, so it's yours to make.
