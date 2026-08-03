# Stage 1 — Website Reading, Mock Pipeline
# Hermes Working Plan

> **This is Hermes's working brain for Stage 1.** 
> Read this before starting any work. Update Tracker and Current Context only.
> Everything else is locked.
> For real project tracker: `.planning/tracker.md`

---

## Current Context

**Where we are:** Stage 0 is functionally complete and committed. Stage 1 core modules are complete and cleaned up. Generic pipeline verified for multiple unseen brands (`zomato`, `phonepe`, `python.org`, `uber`). Obsolete test brands removed. No active blockers.

**Latest decisions:**
- Test brand folder renamed from `chennai-trail-co` to `hoka` with real Hoka identity (`brand_id=hoka`, `display_name=Hoka`, `website_url=https://www.hoka.com/en-us/`)
- `brands/test/` = development/demo brands (public data, no individual consent needed)
- `brands/real/` = client brands (explicit consent required, `consent_given: true`)
- `--replay` mode replays a real successful run from disk, not fake canned output
- Firecrawl is NOT part of Stage 1. Optional enhancement for real client extraction in Stage 2
- One unified pipeline for both test and real brands. Separation via `brand_type` and folder location, not separate codebases
- Stage 1 must produce real check-result, diagnosis, and brand-file outputs against a real website
- Post-Aug 16 goal: onboard 4-5 real local businesses. Judges will see real client work, not just a demo.
- `step4_prove.py` kept minimal in Stage 1; full before/after demo agent with MCP tools is Stage 3 deliverable
- All modules must pass prototype assumption audit: no hardcoded shoe/footwear assumptions, no hardcoded use-case phrases in `scorer.py`
- Removed all hardcoded brand-specific assumptions from core modules. Category detection uses generic domain/title/meta/body signals with safe default.
- Added `BRAND_AUTO_APPROVE=1` environment flag to `step3_fix.py` for non-interactive Windows/demo execution
- Fixed `step2_diagnose.py` to select latest check result by mtime, not alphabetical order
- Deleted obsolete test brands: `brands/test/phonepe/`, `brands/test/python-org/`
- Stage 1 validation approach: ad-hoc direct execution verified; moving to minimal automated pytest suite before Stage 2

**Active blockers:** None. Ready to build minimal pytest suite.

**Next action:** Create `tests/` folder with 4 focused test files, add `pytest` to `requirements.txt`, run `pytest -v`, verify all green, then mark Stage 1 complete.

**Last completed:** Core module cleanup and generic-quality verification completed. Verified end-to-end with `run_demo.py --brand zomato --approve` (exit 0). Direct runner verification passed with `BRAND_AUTO_APPROVE=1`. All hardcoded brand names removed from `llm.py`, `scorer.py`, `step1_check.py`, `step2_diagnose.py`, `step3_fix.py`, `step4_prove.py`. Obsolete test brands deleted.

**Currently working on:** Phase 10 — minimal automated regression test suite for Stage 1 critical paths.

---

## Tracker

| Phase | Task | Status | Notes |
|-------|------|--------|-------|
| Phase 0 | AGY context handoff | DONE | Interactive WezTerm handoff complete. AGY produced execution plan and is building modules in pane 5. |
| Phase 1 | requirements.txt | DONE | requests, beautifulsoup4, python-dotenv |
| Phase 1 | config/settings.py | DONE | REAL_MODE = False, FIRE_CRAWL_ENABLED = False, OPERATOR_NAME = Anshu |
| Phase 1 | exceptions.py | DONE | Custom errors, ID generators, path utilities, schema field constants |
| Phase 2 | Update test brand identity | DONE | brand_id=hoka, display_name=Hoka, URL=hoka.com, folder=brands/test/hoka/ |
| Phase 3a | reader.py | DONE | fetch_url + read_cached_html, timeout 10s, retry once, live fetch against hoka.com verified |
| Phase 3b | schema_generator.py | DONE | validate_brand_record, validate_check_result, validate_diagnosis, normalize_record |
| Phase 3c | logger.py | DONE | log_run_start, log_run_end, log_extraction_stats |
| Phase 3d | fact_extractor.py | DONE | extract_facts, extract_questions, business-type agnostic |
| Phase 4a | llm.py | DONE | get_diagnosis, analyze_persona, REAL_MODE aware |
| Phase 4b | persona.py | DONE | analyze_audience, audience_to_persona, score_persona_fit, detect_business_type |
| Phase 4c | probe.py | DONE | build_engine_queries, run_probe, extract_text, count_words, detect_thin_content |
| Phase 4d | scorer.py | DONE | generate_questions, score_visibility, dynamic context words |
| Phase 5a | ai_client.py | DONE | get_brand_context, ask_ai, display_name wired, footwear references removed |
| Phase 5b | reporter.py | DONE | write_check_result, write_diagnosis, tested with hoka |
| Phase 6a | Rewrite step1_check.py | DONE | Verified end-to-end; status=error + site_unreachable correctly handled |
| Phase 6b | Rewrite step2_diagnose.py | DONE | Verified latest-check linkage now correct; diagnosis reason built dynamically |
| Phase 7a | fact_extractor.py | DONE | Rule-based extractor, writes brand-info.json + .llms.txt |
| Phase 7b | Approval gate | DONE | APPROVE flow implemented; verified manually with piped input |
| Phase 8a | Keep step4_prove.py minimal | DONE | Minimal placeholder implemented and verified importable |
| Phase 8b | Build run_demo.py | DONE | Orchestrator implemented with --brand, --list, --replay; verified end-to-end |
|| Phase 9 | End-to-end verification | DONE | Full live run completed; schema validation passed; --replay verified |
||| Phase 10 | Minimal pytest suite | AWAITING VERIFICATION | 21 tests added, pytest -v 0.29s all green, src/ untouched |

---

## Locked Decisions

**Architecture:**
- One unified pipeline for both test brands and real clients
- `brands/test/` = development/demo brands (public data, no individual consent needed)
- `brands/real/` = client brands (explicit consent required, `consent_given: true`)
- No separate demo folder, no separate codebase

**Data source:**
- Test brands use real website URLs directly
- No local cached HTML snapshots
- Fetcher handles errors gracefully: `status: "error"`, `error_detail: "site_unreachable"`
- `--replay` mode for demo reliability, replays real successful runs from disk

**Demo strategy:**
- Live demo uses `--replay` mode: instant, deterministic, never fails
- Judges see real brand data extracted from real websites
- Before/after proof: agent without tools vs agent with tools
- The simulated part is only the "before" agent not having access — that's the whole point

**Real client strategy (post-Aug 16):**
- Same pipeline, same commands
- Real business owner gives consent
- Their data goes in `brands/real/`
- Firecrawl as optional fetcher backend for real brands in Stage 2

**Module design:**
- Single-responsibility modules, one per file
- Standard Python dicts/lists between steps — no hidden state
- Schema shapes are the contracts between steps
- Each module independently testable before wiring

**AGY execution rules:**
- Context handoff before any build work
- One module per task, verify between steps
- Narrow prompts with exact done signals
- Never vague instructions like "fix step 1"
- Inspect exact touched files with git diff after each task

**Prototype assumption audit (mandatory for every module):**
- As each module is built, actively look for carryover from the old shoe-brand prototype
- Flag any hardcoded business-type assumptions, product structures, material/season keywords, or layout assumptions
- Never quietly generalize without telling the user what changed and why
- `persona.py`, `scorer.py`, `probe.py`, `fact_extractor.py` are highest-risk modules — audit them first

**Issue handling:**
- If I face any problem or issue during execution:
  1. Try to solve it myself first
  2. If unable, search online/internet for correct solution
  3. If user provides a solution, understand it, learn it, apply it
  4. Update `.planning/tracker.md` with the issue and resolution (NOT this file)
  5. Continue execution

---

## Detailed Task Breakdown

### Phase 0: AGY Context Handoff

**Objective:** AGY reads project docs and proves understanding before writing code.

**Files read by AGY:**
- `.planning/prd.md`
- `.planning/tech-spec.md`
- `.planning/schema.md`
- `.planning/app-flow.md`
- `.planning/implementation-plan.md`
- `src/brand_visibility/ai_client.py`
- `brands/test/chennai-trail-co/brand.json`

**AGY produces:** `context_check.md` in project root with:
1. Project summary in 3 sentences
2. Stage 1's 9 deliverables listed
3. What it must NOT touch
4. Schema shapes summarized
5. Any gaps or questions

**Done signal:** Hermes reviews `context_check.md`. If incorrect, Hermes corrects and AGY revises. Only when Hermes says "context accepted" does code writing begin.

**How to verify:** Read `context_check.md`. Check all 5 sections are present and accurate. If any section is wrong or missing, send back to AGY for revision.

---

### Phase 1: Foundation

**Task 1a: `requirements.txt`**
- Create with: `requests`, `beautifulsoup4`, `python-dotenv`
- No Firecrawl here — optional Stage 2 enhancement

**Done signal:** File exists with exactly those 3 packages listed.

**Task 1b: `config/settings.py`**
- Add `REAL_MODE = False`
- Add `FIRE_CRAWL_ENABLED = False`
- Add `OPERATOR_NAME = "Anshu"`
- Add env var names for API keys (structure only, no keys)

**Done signal:** `python -c "from config.settings import REAL_MODE, FIRE_CRAWL_ENABLED, OPERATOR_NAME; print(REAL_MODE, FIRE_CRAWL_ENABLED, OPERATOR_NAME)"` prints `False False Anshu`.

**Task 1c: `exceptions.py`**
- Custom errors: `SiteUnreachableError`, `ThinContentError`, `BrandNotFoundError`
- ID generators: `make_check_id()`, `make_diagnosis_id()` → `YYYY-MM-DD-xxxx` format
- Path utility: `get_brand_dir(brand_id)` → `brands/{test|real}/{brand_id}/`
- Schema field constants: `BRAND_FIELDS`, `CHECK_RESULT_FIELDS`, `DIAGNOSIS_FIELDS`

**Done signal:**
```python
python -c "from brand_visibility.exceptions import make_check_id, get_brand_dir; print(make_check_id()); print(get_brand_dir('chennai-trail-co'))"
```
Expected: prints a valid check ID and the correct path.

---

### Phase 2: Update Test Brand Identity

**Task:** Fix the fictional/real mismatch in `brands/test/chennai-trail-co/brand.json`
- Set `brand_id` to `hoka`
- Set `display_name` to `Hoka`
- Set `website_url` to `https://www.hoka.com/en-us/`
- Keep `brand_type: "test"`
- **Verify folder/brand_id consistency:** if `brand_id` is `hoka`, the folder should be `brands/test/hoka/`, not `brands/test/chennai-trail-co/`
- No shoe-specific language, no fake product names, no fictional brand identity

**Done signal:** `brand.json` matches Hoka identity. Folder name matches `brand_id`. No shoe-specific leakage in any field.

---

### Phase 3: Core Modules

**Task 3a: `reader.py`**
- `fetch_url(url, timeout=10, retries=1)` → `(status, content, error_detail)`
- Uses `requests` with timeout, catches `ConnectionError`, `HTTPError`, `Timeout`
- Returns `status: "completed"` or `status: "error"` per schema
- On error: `error_detail: "site_unreachable"`

**Done signal:**
```python
from brand_visibility.reader import fetch_url
status, content, error = fetch_url("https://www.hoka.com/en-us/")
assert status in ("completed", "error")
if status == "completed":
    assert len(content) > 1000
```

**Task 3b: `probe.py`**
- `extract_text(html)` → clean text string
- `count_words(text)` → int
- `detect_thin_content(text, threshold=100)` → bool
- Uses BeautifulSoup, looks for `<article>`, `<main>`, `<p>` tags

**Done signal:**
```python
from brand_visibility.probe import extract_text, detect_thin_content
from brand_visibility.reader import fetch_url
_, html, _ = fetch_url("https://www.hoka.com/en-us/")
text = extract_text(html)
assert len(text) > 100
assert not detect_thin_content(text)
```

**Task 3c: `persona.py`**
- `detect_business_type(text, url)` → string like "trail running footwear" or None
- Keyword/pattern matching on extracted text
- NOT hardcoded to shoes — works for any business type
- Looks for product/category words in text
- **Audit for footwear bias:** keyword lists must not secretly favor shoe/footwear terms just because the original prototype was shoe-based
- **Non-footwear test:** must detect something sensible for a restaurant, SaaS tool, or consulting firm — not fall back to shoe-shaped assumptions

**Done signal:**
```python
from brand_visibility.persona import detect_business_type
bt = detect_business_type(text, "https://www.hoka.com/en-us/")
assert bt is not None
assert len(bt) > 3
```
Plus mental/real test against a non-footwear site confirms sensible output, not shoe-shaped fallback.

**Task 3d: `scorer.py`**
- `generate_questions(business_type, text, count=2)` → list of question strings
- NO hardcoded use-case phrases like "trail running" or "monsoon conditions"
- Context words come from actual extracted text via `persona.py`/`probe.py`:
  - Pull use-case, occasion, material, or category words that actually appear on the page
  - Use them to fill a `{context_word}` slot dynamically
- Templates:
  - With context: "best {business_type} for {context_word}", "recommend a good {business_type} brand"
  - Without context: "best {business_type} brand", "recommend a good {business_type}"
- Never force a slot to be filled with something made up
- Must work for any business type without producing nonsense

**Done signal:**
```python
from brand_visibility.scorer import generate_questions
questions = generate_questions("trail running footwear", text, count=2)
assert len(questions) == 2
assert all(len(q) > 10 for q in questions)
assert "trail running" not in questions[0].lower() or "for trail running" not in questions[0].lower()
```

**Task 3e: `reporter.py`**
- `write_check_result(check_result, brand_id)` → writes to `brands/{test|real}/{brand_id}/checks/{check_id}.json`
- `write_diagnosis(diagnosis, brand_id)` → writes to `brands/{test|real}/{brand_id}/diagnoses/{diagnosis_id}.json`
- Validates output against schema field lists
- Creates directories if they don't exist

**Done signal:**
```python
from brand_visibility.reporter import write_check_result, write_diagnosis
import os
write_check_result(sample_check_result, "chennai-trail-co")
assert os.path.exists("brands/test/chennai-trail-co/checks/")
```

---

### Phase 4: Wire Step 1 and Step 2

**Task 4a: Rewrite `step1_check.py`**
- Uses: `reader`, `probe`, `persona`, `scorer`, `ai_client`, `reporter`
- Data flow:
  1. Load `brand.json`
  2. Fetch URL via `reader.fetch_url()`
  3. Extract text, count words, flag thin content via `probe`
  4. Detect business type via `persona`
  5. Generate questions via `scorer`
  6. For each question, call `ai_client.ask_ai()` → mock answer
  7. Check if brand name is mentioned in each answer
  8. Build check-result dict matching schema
  9. Write to disk via `reporter`
  10. Return `(check_result, raw_content)` for Step 2

**Done signal:** `python step1_check.py` from `src/brand_visibility/` → exit 0, creates `checks/<check_id>.json`.

**Task 4b: Rewrite `step2_diagnose.py`**
- Uses: `probe`, `reporter`, raw content from Step 1
- Data flow:
  1. Load `brand.json`
  2. Load latest check-result JSON from `checks/`
  3. Inspect raw content directly:
     - If thin content → `reason_code: "thin_content"`
     - If no structured data → `reason_code: "no_structured_data"`
     - If site unreachable → `reason_code: "site_unreachable"`
     - Default → `reason_code: "outdated_or_incorrect_info"`
  4. Build `plain_summary` specific to what was found
  5. Build diagnosis dict matching schema
  6. Write to disk via `reporter`

**Done signal:** `python step2_diagnose.py` from `src/brand_visibility/` → exit 0, creates `diagnoses/<diagnosis_id>.json`.

---

### Phase 5: Brand File + Approval

**Task 5a: Build `fact_extractor.py`**
- Rule-based extractor per `tech-spec.md`:
  - `<title>` → summary fact
  - `<meta name="description">` → summary fact
  - `<article>`, `<main>`, or first 3 `<p>` tags → about text fact
  - Product listings from `<h2>`/`<h3>` + following `<p>`/`<li>` patterns
  - Each fact carries `source` URL
- Writes two files:
  - `brand-info.json` — metadata + approval state + facts array
  - `brand-info.llms.txt` — human-readable rendering

**Done signal:** Running extractor produces both files. `brand-info.llms.txt` starts with `# {display_name}`, has `## Summary`, `## Facts` sections.

**Task 5b: Approval gate**
- Terminal prompt: `Type APPROVE to publish, or anything else to cancel:`
- On "APPROVE": sets `approved: true`, `approved_by: OPERATOR_NAME`, `approved_at: ISO timestamp`
- On anything else: leaves `approved: false`, prints "Cancelled."
- Writes updated `brand-info.json`

**Done signal:** Running gate with "APPROVE" sets all three fields. Running with "cancel" doesn't.

---

### Phase 6: Demo Agent + Orchestrator

**Task 6a: Keep `step4_prove.py` minimal**
- Per `implementation-plan.md` Stage 1 boundary: don't build the before/after demo agent yet
- Keep it as a minimal script that calls `ai_client.ask_ai()` and prints a placeholder answer
- `run_demo.py` must be able to call it without crashing
- Full before/after agent with MCP tools is Stage 3's job

**Done signal:** `python step4_prove.py` runs without crash. `python run_demo.py --brand chennai-trail-co` completes all 4 steps without error.

**Task 6b: Build `run_demo.py`**
- Full orchestrator per `app-flow.md`:
  - `--brand <brand_id>` — run full pipeline
  - `--list` — show available brands
  - `--replay` — replay last approved run from disk
- Data flow:
  1. Load `brand.json`
  2. Consent check (real brands need `consent_given: true`)
  3. Run Step 1 → Step 2 → Step 3 → Step 4 in sequence
  4. Show terminal output per app-flow.md format
  5. Save replay data if not in replay mode

**Done signal:** `python run_demo.py --brand chennai-trail-co` runs end-to-end, produces all expected outputs. `python run_demo.py --brand chennai-trail-co --replay` runs instantly from disk.

---

### Phase 7: End-to-End Verification

**Objective:** Run full pipeline, validate every output against schema, verify `--replay` works.

**Checks:**
- All 4 step scripts run with exit 0
- All JSON outputs match schema shapes
- `--replay` produces identical output to live run
- `git status` clean, all changes committed

**Done signal:** Hermes shows raw proof of all checks passing. Status moves to `AWAITING VERIFICATION`. Anshu independently verifies before marking `VERIFIED & DONE`.

---

### Phase 10: Minimal Automated Regression Suite

**Objective:** Add a small pytest suite that protects the critical paths already validated manually, without over-engineering.

**Why now:** Stage 1 mechanics are verified, but we currently rely on ad-hoc manual runs. Before Stage 2 expands the codebase, we want regression tests that catch known failure modes automatically.

**What we will add:**
- `tests/test_llm.py` — category detection for multiple brands, generic fallback behavior
- `tests/test_scorer.py` — question count, noise filtering, template grammar
- `tests/test_step2.py` — diagnosis reason codes for different engine results
- `tests/test_runners.py` — direct `__main__` scripts exit 0 with env vars, `BRAND_AUTO_APPROVE=1` path works

**What we will NOT add:**
- Live network tests against real websites
- Full end-to-end pipeline tests with network I/O
- Browser/UI tests
- 100% coverage

**Done signal:**
- `requirements.txt` includes `pytest`
- `pytest -v` runs in under 30 seconds
- All tests pass on first run
- Tests are readable and focused enough that a reviewer can see what each one protects

**Time estimate:** 2–2.5 hours

---

## Rules for This File

- Hermes may update **only** the `Current Context` and `Tracker` sections.
- All other sections are locked once written.
- If scope changes, add a new dated entry in the `Locked Decisions` section — don't edit existing entries.
- This file is the master reference for Stage 1 execution.
- `.planning/tracker.md` is the real project tracker. Update it when statuses change or issues arise.

---

## Reference Links

- `.planning/implementation-plan.md` — stage boundaries, definitions of done
- `.planning/tracker.md` — live status, proof logs, git commits
- `.planning/prd.md` — what we're building and why
- `.planning/tech-spec.md` — how it's built, error handling, mock/real table
- `.planning/schema.md` — exact data shapes
- `.planning/app-flow.md` — demo walkthrough, approval gate, --replay
