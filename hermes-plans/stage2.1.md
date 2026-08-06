# Stage 2.1 — YAKE-Based Question Extraction Polish
# Hermes Working Plan

> **This is Hermes's working brain for Stage 2.1.**
> Read this before starting any work. Update Tracker and Current Context only.
> Everything else is locked unless the senior explicitly approves changes.
> For real project tracker: `.planning/tracker.md`

---

## Current Context

**Where we are:** Stage 2.1 implementation is complete and verified from both direct execution and AGY sides. Stage 2.1 is now awaiting Anshu's independent verification before it can be marked `VERIFIED & DONE` in `.planning/tracker.md`.

**What changed:**
- `src/brand_visibility/scorer.py` — replaced `_extract_page_topics()` extraction with YAKE keyword extraction, preserving the existing three-tier `generate_questions()` fallback and grammar-safe templates.
- `tests/test_scorer.py` — updated to YAKE-specific behavior and added weak/short-text fallback coverage.
- `requirements.txt` — added `yake`.
- `jellyfish` Python 3.14 environment mismatch — resolved by installing `cp314` wheel into project-local `.pytest-packages` and setting `PYTHONPATH` during test execution.

**Verification evidence (2026-08-06):**
- `PYTHONPATH='C:\Users\ash74\projects\brand-visibility-agent\.pytest-packages' /c/Python314/python.exe -m pytest tests/test_scorer.py -v` → `6 passed`
- Full regression: same `PYTHONPATH` + `/c/Python314/python.exe -m pytest tests/ -v` → `35 passed`
- Live pipeline: `PYTHONPATH=... BRAND_AUTO_APPROVE=1 /c/Python314/python.exe run_demo.py --brand python-org --approve` → exit 0, generated `checks/`, `diagnoses/`, `generated/`
- Replay: same runner with `--replay` → exit 0, cached run loaded cleanly
- AGY verification: AGY ran `PYTHONPATH=.pytest-packages C:\Python314\python.exe -m pytest tests/test_scorer.py -v` → `6 passed in 0.49s`; AGY did not edit files

**Active blockers:**
- Awaiting Anshu's independent verification and commit for Stage 2.1
- Minor YAKE page-noise remains: `python-org` run emitted `What are the top Python.org Notice options in software & technology solutions?` from page heading noise; handled by Tier B/C, no fourth fallback added

**Next action:** Commit Stage 2.1 after Anshu's verification.

---

## Tracker

| Phase | Task | Status | Notes |
|-------|------|--------|-------|
| Phase 0 | Empirical YAKE test | COMPLETED | Short text + 4 real brands tested; YAKE viable |
| Phase 1 | Formal plan document | COMPLETED | This file |
| Phase 2 | Senior review + approval | COMPLETED | Approved via review of plan with YAKE swap only |
| Phase 3 | Implementation | COMPLETED | scorer.py uses YAKE; requirements.txt updated |
| Phase 4 | Tests + verification | AWAITING VERIFICATION | pytest tests/ -v: 35 passed; live run + AGY verification done |

---

## Locked Decisions

**Extraction mechanism:**
- Replace `_extract_page_topics()` in `src/brand_visibility/scorer.py` with YAKE
- YAKE config: `KeywordExtractor(n=2, top=5)`
- Lower score = more relevant in YAKE; sort by score ascending

**What stays unchanged:**
- `generate_questions()` three-tier fallback logic
- Grammar-safe question templates
- All other modules (`step1_check.py`, `step3_fix.py`, `llm.py`, etc.)
- Offline-first constraint
- No LLM rewrite unless explicitly asked later

**Dependencies:**
- Add `yake` to `requirements.txt`
- No other new dependencies

**Fallback behavior:**
- If YAKE returns empty/weak results → naturally falls through to Tier B/C generic questions
- No new fourth fallback layer

---

## Detailed Task Breakdown

### Phase 3: Implementation

**Task 3a: Replace `_extract_page_topics()` in `scorer.py`**
- Remove bigram generation, title-case regex, frequency ranking, suffix filter
- New implementation uses YAKE keyword extraction
- Keep `NOISE_WORDS` and `STOP_WORDS` as secondary post-filters only, not primary extraction

**Done signal:** `_extract_page_topics()` returns YAKE phrases for test brand text; existing `generate_questions()` consumes them unchanged.

### Phase 4: Update Dependencies

**Task 4a: `requirements.txt`**
- Add `yake` on its own line
- Keep all existing packages

**Done signal:** `cat requirements.txt` shows `yake`

### Phase 5: Update Tests

**Task 5a: Update `tests/test_scorer.py`**
- Adjust any tests that assert specific extraction behavior from the old bigram/suffix approach
- Add test: YAKE returns relevant phrases for a short business text
- Add test: empty/short text falls through to Tier B/C questions
- Ensure all existing tests still pass

**Done signal:** `python -m pytest tests/ -v` passes

### Phase 6: Verify End-to-End

**Task 6a: Demo verification**
- `python run_demo.py --brand python-org --approve` → completed with YAKE-generated questions
- `python run_demo.py --brand python-org --replay` → completed from cache

**Done signal:** Both commands exit 0 and produce expected artifacts under `brands/test/python-org/`

### Phase 7: Documentation + Commit

**Task 7a: Update docs**
- `.planning/tracker.md` updated with Stage 2.1 proof/verification logs
- `.planning/implementation-plan.md` updated with Stage 2.1 stage block and overview row
- `.planning/prd.md` updated with Stage 2.1 in feature-to-stage mapping
- `docs/demo-polish-report.md` reflects YAKE approach instead of bigram+suffix

**Task 7b: Git commit**
- One commit for Stage 2.1
- Commit message: `feat: replace scorer extraction with YAKE keyword extraction`

---

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| YAKE returns UI noise on some sites | Medium | Low | Tier B/C fallback handles weak extraction |
| YAKE output format changes between versions | Low | Medium | Pin version in `requirements.txt` |
| Short text returns empty | Low | Low | Verified empirically; Tier B/C handles it |

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| No suffix-blocked legitimate words | Zero outputs like `Which Around solutions...` | Manual review of brand demos |
| Grammar | All questions grammatically correct | Template review |
| Brand agnosticism | Works for any brand without config | Tested on unseen brands + short synthetic text |
| Test coverage | All tests pass | `pytest tests/ -v` |
| Offline-friendly | No API calls needed | `REAL_MODE=False` demo runs |

---

## Approval Gate

**This plan has been reviewed and approved. Implementation is complete and awaiting independent verification.**

Changes requested by senior that are reflected here:
1. ✅ YAKE replaces only extraction step, templates stay
2. ✅ No new fallback layer; Tier B/C handles weak YAKE output
3. ✅ Empirical test includes short/thin-content example alongside real brands
4. ✅ Planning folder updated to include Stage 2.1 between Stage 2 and Stage 3 with `Added From Hermes` heading

---

*End of Plan*
