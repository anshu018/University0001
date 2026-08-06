# Implementation Plan — Brand Visibility Agent

# Implementation Plan

I'm drafting this one. Hermes can refine the details inside each stage, but the stage boundaries, order, and definitions of done below are what you're approving — treat this as the thing that turns four planning docs into actual commits. Same lock rule as the rest: approved once, and re-approved only if scope genuinely shifts, not touched casually.

## Read this before anything else: "Step" and "Stage" are two different numbering systems

This project has two separate 1-through-N lists and they will get confused if nobody says this out loud:

- **Pipeline Steps (1–4)** — CHECK, SHOW WHY, FIX IT, PROVE IT. Defined in `prd.md`. These describe what the _software does_ every time it runs, for any brand, forever. They don't change based on what week it is.
- **Build Stages (0–7)** — defined in this document. These describe the _order we write the code in_. A single Stage can touch multiple Steps, and a single Step's logic can get built across more than one Stage (Step 3 / Fix It, for example, gets built partly in Stage 1 and hardened in Stage 2).

Whenever either number shows up, say "Step" or "Stage" out loud with it — never just "3."

---

## Stage overview

| Stage | What gets built                                                                                                              | Blocked on                                     | Main files touched                                           |
| ----- | ---------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------- | ------------------------------------------------------------ |
| 0     | Move the old skeleton into the locked structure, reconcile it against `schema.md`                                            | Scaffold folder must already exist             | `src/`, `brands/test/`, `.planning/`                         |
| 1     | Real website reading, rule-based question generation, mock-mode check + diagnose, draft brand-file generation, approval gate | Stage 0 verified                               | Step 1/2/3 scripts (draft-only)                              |
| 2     | Real AI API wired into `ai_client.py`; harden the brand-file extractor against real sites                                    | Stage 1 verified **and** a real API key exists | `ai_client.py`, `config/`                                    |
| 2.1   | YAKE-based question extraction polish                                                                                          | Stage 2 verified                               | `src/brand_visibility/scorer.py`, `tests/test_scorer.py`     |
| 3     | MCP server + the before/after demo agent                                                                                     | Stage 1 verified (does **not** need Stage 2)   | `src/mcp_server.py`, Step 4 script                           |
| 4     | Multi-brand testing, `requirements.txt`, README quick-start                                                                  | Stages 1–3 verified                            | `brands/test/` (2–3 brands), `README.md`, `requirements.txt` |
| 5     | Real brand onboarding sessions                                                                                               | Real Round 2 brief known + Stage 4 verified    | `brands/real/`                                               |
| 6     | Optional UI polish + repo cleanup                                                                                            | Stage 5 underway                               | `README.md`, optional viewer                                 |
| 7     | Demo assembly & rehearsal                                                                                                    | Stages 1–6                                     | Final mock-vs-real call for the live demo                    |

Stages 0–4 don't depend on the real Round 2 brief at all and can happen anytime. Stages 5–7 do — they're deliberately written provisionally, and I'd expect at least a light re-approval pass once the real brief lands on Aug 16, per the modular-skeleton approach we already agreed on.

---

## How every stage actually gets run (read once, applies to all of them)

- **One stage, one task.** Hermes gets handed one stage at a time — never "here's the whole plan, go." Each stage below is written to be a complete, self-contained brief on its own.
- **Hermes runs its own build-workflow pipeline inside each stage** (PRD → one approval → full build → permission wall → handoff) — this document feeds that pipeline, it doesn't replace it.
- **Nothing is "done" without three things:** Hermes shows raw proof it actually ran (file dumps, real output, real diffs — not a spoken summary), you independently re-verify it yourself, and a git commit exists for that stage. All three, every time. This is `tracker.md`'s job to enforce, but it starts here — a stage doesn't get marked started-and-forgotten.
- **Scope surprises get flagged before they get built, not after.** If a stage turns out to need something not listed in its deliverables below, that's a stop-and-ask moment.
- **Git commit after every verified stage.** Non-negotiable — keeps the branch safe overnight regardless of what happens next session.
- **The repo is git-tracked from Stage 0 onward**, so `git diff` / `git log` against the last commit is your independent-verification tool for every stage from here on — same idea as `Compare-Object` against a `.bak` file, just using git instead since that's what actually exists in this project.

---

## Stage 0 — Migrate the skeleton, reconcile it against schema.md

**Goal:** Get the already-scaffolded project folder populated with the real skeleton code, with the input brand record actually matching `schema.md`, and a clean starting git history.

**Prerequisites:** The scaffold folder exists at `C:\Users\ash74\projects\brand-visibility-agent\` — `.planning/`, `src/`, `brands/test/`, `brands/real/`, `config/`, `README.md`, `.gitignore`, and a git repo with an initial scaffold commit. If this hasn't happened yet, or happened at a different path, fix that first before anything else in this stage.

**Deliverables:**

1. Confirm the real filenames of the four existing skeleton scripts before touching anything — I only know `step1_check.py` and `step4_prove.py` for certain; the middle two need to be confirmed from what's actually on disk, not assumed.
2. Move the legacy skeleton (`demo_brand.json`, `ai_client.py`, the four step scripts, `run_demo.py`) into `src/` (code) and `brands/test/` (`demo_brand.json`).
3. Reshape `demo_brand.json` into `brands/test/<brand_id>/brand.json`, matching `schema.md`'s brand record exactly. If any field in the old file doesn't cleanly map to the new shape, that's a flag-it-back moment — don't silently drop it or silently invent a mapping.
4. Replace the four already-approved `.planning/*.md` stub files (`prd.md`, `schema.md`, `tech-spec.md`, `app-flow.md`) with their real content. Leave `rules.md`, `tracker.md`, `design.md` as stubs — they're not written yet — and drop this file in as `implementation-plan.md` once I approve it.
5. Archive the old `PRD.md` draft and `pipeline-diagram.mermaid` somewhere clearly marked superseded (e.g. `.planning/archive/`) — don't delete them, but don't treat them as current either.
6. Do **not** rewrite any pipeline logic yet. This stage is "put things in the right place and fix the one data shape," not "start building."

**Definition of done:** Full recursive directory listing, a diff of `demo_brand.json` → `brand.json` showing exactly what changed, `git log --oneline` showing the migration commit. I verify independently before this counts as done.

---

## Stage 1 — Website reading, question generation, mock check/diagnose, draft brand file, approval gate

**Goal:** An end-to-end pipeline run, in mock mode, that reads a real website and produces a real check-result, diagnosis, and an approved draft brand file — everything except real AI-engine calls and MCP serving.

**Prerequisites:** Stage 0 verified.

**Deliverables:**

1. **Real website fetching** (this is real from day one — it is _not_ gated by mock/real mode, only the AI-engine querying is). Timeout 10s, retry once, then `status: "error"`, `error_detail: "site_unreachable"` per `tech-spec.md`.
2. **Thin-content handling without a schema change:** Step 1 and Step 2 run in the same process. Step 1 keeps the raw extracted page text in memory and hands it to Step 2 directly — Step 2 decides `reason_code: "thin_content"` by looking at that in-memory content itself, not by reading a stored flag from the check-result JSON (schema.md has no such field, and it shouldn't need one for this).
3. **Business type detection** from the fetched content, written into `business_type_detected`.
4. **Rule-based, templated question generation** — not an LLM call. This needs to work with zero API keys, which matches where we actually are right now. Real questions, parameterized by the detected business type and whatever category/product words show up on the site.
5. **Engine mention-checking still calls the existing mock `ai_client.py` function** — Stage 2 is what makes this real, not this stage.
6. **Check-result JSON** written to `brands/test/<brand_id>/checks/<check_id>.json`, matching `schema.md` exactly.
7. **Diagnosis JSON** written to `brands/test/<brand_id>/diagnoses/<diagnosis_id>.json`, with a genuinely specific `plain_summary` tied to what was actually found — not a canned line.
8. **Draft brand-file generation** — the rule-based extractor from `tech-spec.md` (title, meta description, about-page text, product listings, each fact carrying a real `source` URL). Written as a draft, not yet approved.
9. **The approval gate itself** — the `[y/n]` terminal interaction from `app-flow.md`, wired to actually set `approved` / `approved_by` / `approved_at` in `brand-info.json` on yes.

**Boundary — do not do this yet:** No real API calls of any kind. No MCP server work. No UI work. Don't touch Step 4 beyond whatever's needed to keep `run_demo.py` running end to end without crashing.

**Definition of done:** A real run against at least one real website, full check-result and diagnosis JSON shown raw, the approval prompt actually working, git commit. I'd also suggest (not require) trying one second throwaway URL here just as an early smoke test that nothing's hardcoded — full multi-brand proof is Stage 4's job, but catching an obvious hardcoding bug now is cheap.

---

## Stage 2 — Real AI API wired in, extractor hardened

**Goal:** Real engine calls behind the mock/real gate, once a key actually exists.

**Prerequisites:** Stage 1 verified, **and** at least one real API key acquired. Don't start this stage without a key — there's nothing to wire it into.

**Hard rule, repeated because this is exactly where it matters most:** no real, paid API call happens without asking you first, even with a key present and even with `REAL_MODE` flipped in code. This stage sets up the _capability_ — actually spending real API budget on a real call still needs a green light in the moment.

**Deliverables:**

1. **Touch only `ai_client.py` and the `config/` files.** The original design intent — "the one file that changes when a real key is added" — is a real constraint, not just a nice description. If wiring this in seems to require touching `step1_check.py` or anything else, that's a signal to stop and flag it rather than push through.
2. Real HTTP calls to whichever provider(s) you actually have keys for, matching the exact function signature the mock version already used, so nothing upstream needs to change.
3. The 15s timeout / 1 retry / visible-error-on-failure behavior from `tech-spec.md` — never a silent fallback to a mock answer.
4. **Lock in the actual engine identifier strings here** (e.g. whatever the real provider's short name ends up being) — check-result records reference these, so once picked, don't change them casually later.
5. Confirm `REAL_MODE: False` still produces the exact same mock behavior as before — this is a regression check, not optional, since mock has to stay a safe, reliable default forever, not just until this stage.
6. If time allows: harden the rule-based extractor from Stage 1 against real-world site quirks you actually hit while testing with real engines.

**Definition of done:** One real, redacted API response captured as proof it's genuinely hitting a real provider, one confirmation run showing mock mode still works unchanged with `REAL_MODE: False`, git commit.

---

## Stage 2.1 — YAKE-Based Question Extraction Polish (Added From Hermes)

**Goal:** Replace the brittle bigram + suffix-filter question extraction in `scorer.py` with YAKE-based keyword extraction, keeping the existing three-tier question template system and grammar-safe behavior unchanged.

**Prerequisites:** Stage 2 verified.

**Deliverables:**
1. `src/brand_visibility/scorer.py`: replace `_extract_page_topics()` extraction logic with YAKE while preserving `generate_questions()` templates and fallback behavior.
2. `tests/test_scorer.py`: update extraction assertions and cover YAKE-specific behavior, including weak/short-text fallback.
3. `requirements.txt`: add `yake`.

**Definition of done:** `pytest tests/ -v` green, live `run_demo.py` run completes for an unseen test brand, and question output no longer includes the previous suffix-blocked/noise patterns that broke legitimate category terms.

---

## Stage 3 — MCP server + the before/after demo agent

**Goal:** The actual differentiator. Built and tested together, since you can't verify an MCP server without something calling it.

**Prerequisites:** Stage 1 verified. Stage 2 is _not_ required first — the MCP server just serves whatever's approved, mock-generated or real-generated, so if the API key situation is still pending, this stage can go ahead of Stage 2 without breaking anything.

**Deliverables:**

1. `requirements.txt` gets `mcp>=1.27,<2` pinned — the version constraint from `tech-spec.md` is deliberate, don't let anything upgrade it to v2 without checking with me first.
2. `src/mcp_server.py` implementing exactly the two tools from `tech-spec.md`: `get_brand_info(brand_id)` and `list_brands()`, stdio transport, reading straight from `brand-info.json`, serving only where `approved == true`.
3. Confirm the "same response whether missing or unapproved" behavior actually holds — `{found: false}` in both cases, no way to distinguish them from the outside.
4. The Step 4 script rebuilt as the before/after demo agent from `tech-spec.md`: one agent instance with no tools registered (before), one with the two MCP tools registered (after), same question, same underlying `ai_client.py` call function wrapped in a thin tool-calling loop.

**Definition of done:** A captured transcript of both tools being called directly — `get_brand_info` for a real approved brand, `get_brand_info` for an unapproved/missing one, and `list_brands` — plus one full before/after demo agent run showing a real difference in the two answers. Git commit.

---

## Stage 4 — Multi-brand testing and hardening

**Goal:** Prove nothing's secretly hardcoded to the one shoe brand, and get the repo submission-ready.

**Prerequisites:** Stages 1–3 verified.

**Deliverables:**

1. Add 2–3 test brands under `brands/test/` from genuinely different categories — not three variations on shoes.
2. Run the full pipeline on each and confirm `business_type_detected`, the generated facts, and the MCP responses are actually different per brand, not copy-pasted.
3. Finalize `requirements.txt` with everything actually used by this point.
4. Write the real `README.md` — what the project is, the Sense→Generate→Reach→Learn mapping, a quick-start that runs fully in mock mode with no key required, and a short real-mode section.

**Definition of done:** Terminal output from all 2–3 brands showing genuinely distinct results, `README.md` content shown raw, git commit.

---

## Stage 5 — Real brand onboarding

**Goal:** Run the real-client flow from `app-flow.md` against 2–3 actual small businesses.

**Prerequisites:** The real Round 2 brief has landed, Stage 4 verified, and the teammate's outreach has actually produced a willing business to run this with.

**Deliverables:** This stage is mostly _using_ what's already built, not building new things — `app-flow.md` already specifies the exact interaction (both consent gates, the testimonial capture). The only build work here, if any, is whatever small adjustments come up from actually running it with a real person watching, which should get flagged individually rather than assumed in advance.

**Definition of done:** A completed real-client session with both gates correctly recorded in `brand.json`, git commit (with real business data staying strictly in `brands/real/`, never touching `brands/test/`).

---

## Stage 6 — Optional UI polish + repo cleanup

**Goal:** Whatever final polish time allows.

**Prerequisites:** Stage 5 underway or done.

**Deliverables:** A simple read-only viewer for generated files, if there's time — this is explicitly a nice-to-have, not required. Repo cleanliness (clear `.gitignore` coverage, no stray files, secrets genuinely never committed) is closer to required, since judges will read this repo directly.

**Definition of done:** Whatever was actually built, shown raw, git commit.

---

## Stage 7 — Demo assembly and rehearsal

**Goal:** Get to a rehearsed, reliable live demo.

**Prerequisites:** Stages 1–6.

**Deliverables:**

1. The mock-vs-real decision for the live judged demo (flagged as open in `tech-spec.md`) needs to actually get made by this stage, not left open.
2. Decide which real brand(s), if any and with confirmed consent, get shown to judges.
3. Rehearse the full before/after proof enough times to be confident it holds up live.
4. Real AI engine screenshots go in as a bonus only if they've genuinely landed by now — never promised, never rushed to fake.

**Definition of done:** A rehearsed run-through that works without intervention, git commit of anything that changed to get there.
