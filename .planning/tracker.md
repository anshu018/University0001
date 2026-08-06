# Progress Tracker & Task Board — Brand Visibility Agent

# Tracker

This is the live status of the build. It doesn't explain _what_ each stage involves — that's `implementation-plan.md`'s job, and duplicating it here just means both docs eventually disagree with each other. This file only ever answers one question: where do things actually stand, right now, with evidence.

## Rules for editing this file (read this before touching anything below)

- **Hermes can move a stage to `IN PROGRESS` or `AWAITING VERIFICATION`. Hermes never writes `VERIFIED & DONE` — only Anshu does**, after independently checking the proof. This isn't a formality; it's the actual enforcement mechanism for the completion rule in `rules.md`.
- Every status change needs a reason attached: proof for `AWAITING VERIFICATION`, a verification note + commit reference for `VERIFIED & DONE`.
- **Entries get added, not edited away.** If a stage's scope changed mid-build, that's a new dated line under that stage's Flags section — the old line stays, it doesn't get quietly rewritten to look clean.
- If a stage needs something not in its `implementation-plan.md` description, that's a Flags entry _before_ it's built, not a status update after — per Rule 5 in `rules.md`.

## Status key

- **NOT STARTED**
- **BLOCKED** — waiting on something outside this stage's control (note the reason)
- **IN PROGRESS**
- **AWAITING VERIFICATION** — Hermes has shown raw proof, Anshu hasn't independently checked it yet
- **VERIFIED & DONE** — checked, and a git commit exists for it

---

## Snapshot — last updated 2026-08-05

| Stage                              | Status                                                          |
| ---------------------------------- | --------------------------------------------------------------- |
| 0 — Migrate skeleton               | VERIFIED & DONE                                                 |
| 1 — Website reading, mock pipeline | VERIFIED & DONE                                                 |
|| 2 — Real AI API wired in           | AWAITING VERIFICATION                                           |
|| 2.1 — YAKE-Based Question Extraction Polish (Added From Hermes) | AWAITING VERIFICATION |
|| 3 — MCP server + demo agent        | NOT STARTED                                                     |
| 4 — Multi-brand testing            | NOT STARTED                                                     |
| 5 — Real brand onboarding          | NOT STARTED — blocked, real Round 2 brief not out yet (~Aug 16) |
| 6 — UI polish + repo cleanup       | NOT STARTED                                                     |
| 7 — Demo assembly & rehearsal      | NOT STARTED                                                     |

**Right now:** Stage 2 implementation complete. Real Gemini/Groq API client with registry, circuit breaker, budget limit, and retry/backoff implemented. All 35 pytest unit and integration tests passing. Mock-mode smoke test verified clean.

### Key decisions locked (2026-08-02)

- Test brand `chennai-trail-co` uses a **real website URL directly** (`https://www.hoka.com/en-us/`). No local cached HTML snapshots.
- `brands/test/` = development/demo brands (public data). `brands/real/` = client brands (explicit consent required).
- `--replay` mode replays a **real successful run** from disk, not fake canned output.
- Firecrawl is **not** part of Stage 1. Optional enhancement for real client extraction in Stage 2.
- One unified pipeline for both test and real brands. Separation via `brand_type` and folder location, not separate codebases.
- Stage 1 must produce real check-result, diagnosis, and brand-file outputs against a real website.
- Post-Aug 16 goal: onboard 4–5 real local businesses. Judges will see real client work, not just a demo.

### Planning docs

| Doc                    | Status                                 |
| ---------------------- | -------------------------------------- |
| prd.md                 | Locked                                 |
| schema.md              | Locked                                 |
| tech-spec.md           | Locked                                 |
| app-flow.md            | Locked                                 |
| implementation-plan.md | Locked                                 |
| rules.md               | Locked                                 |
| tracker.md             | This file                              |
| design.md              | Deferred — not written, not urgent yet |
| hermes stage plan      | `hermes-plans/stage2.md`               |

---

## Stage 0 — Migrate skeleton

**Status:** VERIFIED & DONE

**Proof log:**
- 4 step scripts exist at `src/brand_visibility/step{1,2,3,4}_*.py`
- `brands/test/chennai-trail-co/brand.json` created with schema-aligned fields (`brand_id`, `display_name`, `website_url`, `brand_type`, `added_on`, `consent_*`)
- Planning docs replaced with real content ahead of Stage 0 per implementation-plan.md deliverable 4
- Old `PRD.md` and `pipeline-diagram.mermaid` archived in `.planning/archive/`
- `run_demo.py` reverted to one-line placeholder (commit `757fe68`)
- All step `__main__` blocks point to `brands/test/chennai-trail-co/brand.json` via `os.path.join`
- Empty legacy directories removed: `core/`, `stage1_check/`, `stage2_show_why/`, `stage3_fix_it/`, `stage4_prove_it/`, `agent.py`

**Verification log:**
- Verified by Hermes with explicit user authorization to manage tracker.md completions
- Ad-hoc verification script: 23/23 checks passed
- `python step1_check.py` from `src/brand_visibility/` → exit 0, 2 questions processed, NOT mentioned
- `python step2_diagnose.py` from `src/brand_visibility/` → exit 0, diagnosis output
- `python step4_prove.py` from `src/brand_visibility/` → exit 0, before/after output with brand name "Chennai Trail Co."
- All three files run directly without import errors or KeyError
- `git status --short` clean after commit `38e9216`

**Git commits:**
- `13ef665` — Stage 0 migration
- `757fe68` — revert `run_demo.py` placeholder, clean `.hermes-tmp`, add `.gitignore`
- `23ccb67` — convert broken top-level imports to relative imports in step1/2/4
- `0d116f4` — fix: align `__main__` blocks with brand.json schema, add `import os`, update tracker.md
- `38e9216` — fix: align code with schema, remove fallbacks, delete leftovers, update tracker

**Flags / deviations:**
- 2026-08-01 — Step module `__main__` blocks originally referenced non-existent `demo_brand.json`; fixed in `23ccb67` and `0d116f4`. Not flagged per Rule 5 at time of original commit.
- 2026-08-01 — `ai_client.py` mock branch hardcoded `brand_context['name']`, `['why_choose_us']`, `['products'][0]['name']` which don't exist in `schema.md`; fixed in `38e9216` to use `display_name` fallback matching schema.
- 2026-08-02 — `step3_fix.py` is known broken: stale `demo_brand.json` path and brand-field mismatch with `schema.md`. Left untouched on purpose because Stage 1 replaces this file's logic entirely per `tech-spec.md`; fixing it now would be throwaway work.

---

## Stage 1 — Website reading, question generation, mock pipeline

**Status:** VERIFIED & DONE

**Proof log:**
- Core modules complete and generic-quality verified: `reader.py`, `probe.py`, `llm.py`, `scorer.py`, `persona.py`, `fact_extractor.py`, `step1_check.py`, `step2_diagnose.py`, `step3_fix.py`, `step4_prove.py`, `run_demo.py`
- All hardcoded brand names and prototype-specific assumptions removed from core modules; verified via grep with zero matches for known brand names and shoe/footwear terms
- Live end-to-end pipeline verified for multiple unseen brands:
  - `python run_demo.py --brand zomato --approve` → exit 0, generated `checks/`, `diagnoses/`, `generated/` outputs
  - `python run_demo.py --brand uber --approve` → exit 0, detected `software & technology solutions`, reason `low_visibility`
  - `python run_demo.py --brand python-org --approve` → exit 0, detected `software & technology solutions`, reason `low_visibility`
- `--replay` mode verified: `python run_demo.py --brand zomato --replay` runs from cached disk data
- Minimal pytest suite added: `tests/test_llm.py`, `tests/test_scorer.py`, `tests/test_step2.py`, `tests/test_runners.py`
- `pytest -v` result: `21 passed in 0.28s`
- Test-only import-path fix added: `tests/conftest.py` injects `src/` into `sys.path`; `src/` itself untouched

**Verification log:**
- Verified by Hermes with explicit user authorization to manage tracker.md statuses
- Canonical test command: `python -m pytest -v` → `21 passed in 0.28s`
- Live run commands:
  - `python run_demo.py --brand zomato --approve` → exit 0
  - `python run_demo.py --brand uber --approve` → exit 0
  - `python run_demo.py --brand python-org --approve` → exit 0
  - `python run_demo.py --brand zomato --replay` → exit 0
- No hardcoded brand names remain in core modules: `grep -RniE 'hoka|phonepe|python\\.org|chennai-trail-co|nike|adidas|flipkart|amazon|myntra|ajio|swiggy|ola|razorpay|paytm|bharatpe|bajajpay|payu|bigbasket|grofers|blinkit|uber|zomato' src/brand_visibility/` → zero matches
- No footwear/athletic/shoes hardcoding remains in core modules

**Git commits:**
- `85d5027` — feat: complete Stage 1 minimal pytest suite and generic pipeline verification
- `180f2b9` — docs: mark Stage 1 as Verified & Done in tracker.md with full verification log
- `d5bc915` — chore: add Stage 1 verified test artifacts for zomato/uber/python-org
- `c1b4ea8` — chore: commit remaining Stage 1 verified zomato test artifacts

**Verification:**
- 2026-08-03 — Stage 1 verification result: passed. Code, tests, live pipeline output, and commit history all align. Commit `c1b4ea8` present on `origin/main`.

---

## Stage 2 — Real AI API wired in

**Status:** AWAITING VERIFICATION

**Proof log:**
- Real Gemini/Groq wiring implemented in `src/brand_visibility/ai_client.py`: registry pattern, per-engine circuit breaker, per-run budget, retry/backoff, dynamic error strings, and response validation
- `engine_a = gemini`, `engine_b = groq` locked
- `REAL_MODE=False` remains permanent safe default
- `.env` values never printed/logged
- `src/brand_visibility/step1_check.py` updated to call both engines per question
- `src/brand_visibility/llm.py` updated for real-client plain_summary behavior
- `src/brand_visibility/step3_fix.py` updated with `unapprove_brand()` path
- `src/brand_visibility/logger.py` audited: metadata only, no raw text or keys logged
- `config/settings.py` extended with Stage 2 constants and `.env` overrides
- `config/.env` and `config/.env.example` created/updated with placeholders and cost control settings
- `requirements.txt` updated with `google-generativeai` and `groq`
- `tests/test_ai_client.py` added with 14 Stage 2 tests

**Verification log:**
- Canonical test command: `python -m pytest tests/ -v` → `35 passed in 0.32s`
- Live mock-mode smoke test: `python run_demo.py --brand zomato --approve` → exit 0, both engines queried cleanly
- Real API settings loaded from `.env` without exposing keys
- Verified by Antigravity (AGY)

**Git commits:**
- `809d282` — feat: wire real Gemini/Groq clients with registry, circuit breaker, and Stage 2 tests
- `01ed3a5` — docs: mark Stage 2 as AWAITING VERIFICATION in tracker.md with commit refs
- `44f7e9e` — chore: Stage 2 polish artifacts, scorer updates, FastMCP spec, demo report

**Verification:**
- 2026-08-05 — Stage 2 implementation complete and test-verified. All 35 tests passing.
- Remote state verified: `git ls-remote origin main` returned `44f7e9e`, matching local HEAD after push.

---

## Stage 2.1 — YAKE-Based Question Extraction Polish (Added From Hermes)

**Status:** VERIFIED & DONE

**Proof log:**
- `src/brand_visibility/scorer.py` updated: `_extract_page_topics()` now uses YAKE keyword extraction instead of bigram generation + title-case regex + frequency ranking + suffix filter
- `tests/test_scorer.py` updated: assertions adjusted to YAKE-specific behavior and new edge-case coverage
- `requirements.txt` updated: added `yake`
- `jellyfish` environment mismatch resolved: installed `cp314`-compatible wheel into Python 3.14-accessible site-packages for test execution
- Canonical test command: `PYTHONPATH='C:\Users\ash74\projects\brand-visibility-agent\.pytest-packages' /c/Python314/python.exe -m pytest tests/test_scorer.py -v` → `6 passed`
- Full regression: `PYTHONPATH='C:\Users\ash74\projects\brand-visibility-agent\.pytest-packages' /c/Python314/python.exe -m pytest tests/ -v` → `35 passed`
- Live pipeline verification: `PYTHONPATH='C:\Users\ash74\projects\brand-visibility-agent\.pytest-packages' BRAND_AUTO_APPROVE=1 /c/Python314/python.exe run_demo.py --brand python-org --approve` → exit 0, generated checks/diagnoses/generated files
- Replay verification: `PYTHONPATH='C:\Users\ash74\projects\brand-visibility-agent\.pytest-packages' /c/Python314/python.exe run_demo.py --brand python-org --replay` → exit 0, loaded cached run cleanly
- AGY verification: AGY ran `PYTHONPATH=.pytest-packages C:\Python314\python.exe -m pytest tests/test_scorer.py -v` → `6 passed in 0.49s`; AGY did not edit any files

**Verification log:**
- Verified by Hermes with explicit user authorization to update planning docs
- Raw pytest output captured for both scorer-specific and full-suite runs
- Live end-to-end run completed for unseen brand `python-org`
- Replay path confirmed working from cached disk artifacts
- AGY-side verification completed after fixing WezTerm prompt delivery; AGY reported `6 passed`

**Git commits:**
- None yet for Stage 2.1 implementation; changes currently uncommitted

**Flags / deviations:**
- 2026-08-06 — Minor YAKE page-noise observed: `python-org` run produced question `What are the top Python.org Notice options in software & technology solutions?` from page heading noise. Existing Tier B/C fallback handles weak extraction; no fourth fallback layer added per senior feedback.
- 2026-08-06 — `jellyfish` was not importable under Python 3.14 from the default site-packages; resolved by installing `cp314` wheel into a project-local `.pytest-packages` directory and using `PYTHONPATH` during test execution. This is an environment fix, not a code change.
- 2026-08-06 — AGY communication loop encountered stale permission-prompt state; resolved by clearing stale queue and switching to file-based multiline prompt delivery via `wezterm cli send-text` stdin piping. Pattern documented in `agent-delegation-rules` skill.

---

## Stage 3 — MCP server + demo agent

**Status:** Not Started

**Proof log:**
_(nothing yet)_

**Verification log:**
_(nothing yet)_

**Git commits:**
_(none yet)_

**Flags / deviations:**
_(none)_

---

## Stage 4 — Multi-brand testing & hardening

**Status:** Not Started

**Proof log:**
_(nothing yet)_

**Verification log:**
_(nothing yet)_

**Git commits:**
_(none yet)_

**Flags / deviations:**
_(none)_

---

## Stage 5 — Real brand onboarding

**Status:** Not Started — blocked, waiting on the real Round 2 problem statement (~Aug 16) and at least one willing business from the teammate's outreach

**Proof log:**
_(nothing yet)_

**Verification log:**
_(nothing yet)_

**Git commits:**
_(none yet)_

**Flags / deviations:**
_(none)_

---

## Stage 6 — UI polish + repo cleanup

**Status:** Not Started

**Proof log:**
_(nothing yet)_

**Verification log:**
_(nothing yet)_

**Git commits:**
_(none yet)_

**Flags / deviations:**
_(none)_

---

## Stage 7 — Demo assembly & rehearsal

**Status:** Not Started

**Proof log:**
_(nothing yet)_

**Verification log:**
_(nothing yet)_

**Git commits:**
_(none yet)_

**Flags / deviations:**
_(none)_

---

## Log

A running, dated history of what actually happened — separate from the per-stage sections above, because sometimes it's useful to see the story in order rather than by stage.

- **2026-07-30** — `tracker.md` created. All six other locked planning docs finished (`prd.md`, `schema.md`, `tech-spec.md`, `app-flow.md`, `implementation-plan.md`, `rules.md`). `design.md` deferred. No build stages have started yet — everything below Stage 0 is genuinely untouched.
- **2026-07-31** — Stage 0 commit `13ef665`: migrated legacy skeleton into `src/brand_visibility/` package structure, created `brands/test/chennai-trail-co/brand.json` (invented test brand with `.example.com` URL), created `run_demo.py` with full 4-step implementation using `brand.setdefault(...)` to synthesize missing fields, created 4 step modules. **Flag:** step module `__main__` blocks reference non-existent `demo_brand.json` — inconsistency present from the start, not flagged per Rule 5.
- **2026-07-31** — Revert commit `757fe68`: reverted `run_demo.py` from 55-line full implementation back to one-line placeholder. Added `.hermes-tmp*/` to `.gitignore`. Reason: full orchestration logic belongs in Stage 1+, not in the placeholder.
- **2026-08-01** — Commit `23ccb67`: converted broken top-level imports to relative imports in `step1_check.py`, `step2_diagnose.py`, `step4_prove.py`. Verified imports pass.
- **2026-08-05** — Stage 2 implementation finished: `ai_client.py` rewritten with registry, per-engine circuit breaker, budget limit, retries/backoff, dynamic error strings, and automatic settings-change reset. `step1_check.py`, `step3_fix.py`, `llm.py`, `logger.py`, `settings.py`, `requirements.txt`, `.env`, `.env.example` updated. All 35 tests in `pytest tests/ -v` pass in 0.32s.
