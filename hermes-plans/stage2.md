# Stage 2 — Real AI API Wiring, Cost Control, Extensible Engine Registry
# Hermes Working Plan

> **This is Hermes's working brain for Stage 2.**
> Read this before starting any work. Update Tracker and Current Context only.
> Everything else is locked.
> For real project tracker: `.planning/tracker.md`

---

## Current Context

**Where we are:** Stage 2 implementation is completed and all 35 pytest tests are passing.
- `config/.env`, `config/.env.example`, `config/settings.py`, `requirements.txt` updated.
- `src/brand_visibility/ai_client.py` full rewrite with registry (`engine_a` -> Gemini, `engine_b` -> Groq), circuit breaker, per-run budget, retry/backoff, response validation, and automatic settings reset.
- `src/brand_visibility/step1_check.py` updated for Option B (calling `ask_ai()` for both engines).
- `src/brand_visibility/logger.py` audited for metadata-only logging.
- `src/brand_visibility/step3_fix.py` updated with `unapprove_brand()`.
- `src/brand_visibility/llm.py` updated to append actionable line in real-client mode.
- Mock-mode smoke test `run_demo.py --brand zomato --approve` verified clean.
- All 35 tests pass in 0.32s (`pytest tests/ -v`).

**Active blockers:** None.

**Next action:** Perform git commit for Stage 2 implementation.

---

## Tracker

| Phase | Task | Status | Notes |
|-------|------|--------|-------|
| Phase 0 | Stage 2 plan in `hermes-plans/stage2.md` | COMPLETED | This file |
| Phase 1 | `config/.env` placeholder | COMPLETED | Never print real values |
| Phase 1 | `config/.env.example` update | COMPLETED | Documented placeholders |
| Phase 1 | `config/settings.py` extensions | COMPLETED | Keys + AI knobs from `.env` |
| Phase 1 | `requirements.txt` additions | COMPLETED | `google-generativeai`, `groq` |
| Phase 2 | `src/brand_visibility/ai_client.py` rewrite | COMPLETED | Registry, circuit breaker, budget, validation |
| Phase 2 | `src/brand_visibility/step1_check.py` minimal change | COMPLETED | Option B: call `ask_ai()` twice per question |
| Phase 3 | TDD GREEN — all 14 tests pass | COMPLETED | Including new Stage 2 tests |
| Phase 4 | Mock-mode smoke test | COMPLETED | `run_demo.py --brand zomato --approve` with `REAL_MODE=False` |
| Phase 5 | Full regression suite | COMPLETED | `pytest tests/ -v` all 35 green |
| Phase 6 | Update `.planning/tracker.md` | COMPLETED | Stage 2 proof log updated |
| Phase 7 | Git commit | IN PROGRESS | One commit for Stage 2 implementation |

---

## Locked Decisions

**Architecture:**
- Registry pattern: `ENGINE_REGISTRY` dict maps engine name → call function. Adding engines = one entry.
- `ask_ai(question, brand_context=None, engine="engine_a")` — default preserves all existing callers.
- Two-condition real gate: real call only when `REAL_MODE is True` AND valid key exists.
- Per-engine circuit breaker, independent per engine. Not global.
- Per-run real call budget caps total real API calls per pipeline run.
- Both-engines-failed signal: caller can detect when both engines returned errors for same question.
- Response shape validation after every real call: empty/None/malformed → visible error.
- Brand context passed through to real engines when provided.

**Cost control:**
- `AI_REQUEST_TIMEOUT` default 15s, from `.env` with Python fallback.
- `AI_MAX_RETRIES` default 1, from `.env` with Python fallback.
- `AI_RETRY_BACKOFF_SECONDS` default 2s, from `.env` with Python fallback.
- `AI_MAX_REAL_CALLS_PER_RUN` default 10, from `.env` with Python fallback.
- `AI_CONSECUTIVE_FAILURE_LIMIT` default 3, from `.env` with Python fallback.
- Retry on: timeout, 429, 502, 503, 504. No retry on: 401/403, malformed response.
- Backoff between retries: fixed `AI_RETRY_BACKOFF_SECONDS`, not instant.

**Error handling:**
- All error messages dynamically include engine name: `f"[{engine} error: ...]"`
- Error classes: `timeout`, `rate limited`, `auth failed`, `malformed response`, `missing API key`, `real call budget exhausted`, `circuit breaker tripped after N consecutive failures`
- No silent fallback to mock content under any condition.

**Security:**
- `.env` is gitignored. Real values never printed, logged, or committed.
- Placeholder values are `***` in `.env` and `.env.example`.
- `config/.env` existence confirmed, contents never shown in chat output.
- Logger must never capture raw client data: no API responses, no extracted page text, no keys. Only metadata: `brand_id`, `run_id`, timestamps, status, engine names, error classes.
- Approval is reversible: `step3_fix.py` / `run_demo.py` must provide an unapprove path that resets `approved=false`, `approved_by=null`, `approved_at=null` without deleting the file.
- Diagnosis `plain_summary` must include one actionable line for real-client mode, not just technical diagnosis. Technical-only summaries are acceptable only when no real brand is involved.

**Real-client trust:**
- No raw client business data in logs or replay files.
- Approval errors are recoverable without manual JSON editing.
- Diagnosis output is readable by a non-technical business owner, not just a developer/judge.

**Scope:**
- Files touched: `config/.env`, `config/.env.example`, `config/settings.py`, `requirements.txt`, `src/brand_visibility/ai_client.py`, `src/brand_visibility/step1_check.py`, `src/brand_visibility/logger.py`, `src/brand_visibility/step3_fix.py`, `src/brand_visibility/llm.py`
- Files untouched: `step2_diagnose.py`, `step4_prove.py`, `reader.py`, `probe.py`, `persona.py`, `scorer.py`, `fact_extractor.py`, `reporter.py`, `run_demo.py`, `src/mcp_server.py`, all planning docs
- Scope expansion: logger audit, unapprove path, and client-facing plain_summary are now in Stage 2 per user direction on 2026-08-04

**Demo/real balance:**
- Real-client-first. Demo is a byproduct of real infrastructure, not a separate simulation layer.
- Mock mode remains for reliability when keys are absent or demo stability is required.

---

## Detailed Task Breakdown

### Phase 1: Config Foundation

**Task 1a: `config/.env`**
- Create gitignored placeholder file.
- Contents:
  ```
  GEMINI_API_KEY=***
  GROQ_API_KEY=***
  AI_REQUEST_TIMEOUT=15
  AI_MAX_RETRIES=1
  AI_RETRY_BACKOFF_SECONDS=2
  AI_MAX_REAL_CALLS_PER_RUN=10
  AI_CONSECUTIVE_FAILURE_LIMIT=3
  ```
- Verify file exists. Never print contents.

**Done signal:** `test -f config/.env` passes. Contents never displayed.

**Task 1b: `config/.env.example`**
- Update from comment-only to documented placeholders matching `.env`.
- Same keys with `***` values and one-line comments explaining each.

**Done signal:** File exists with all expected keys documented.

**Task 1c: `config/settings.py`**
- Load `.env` via `python-dotenv`.
- Add:
  - `GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")`
  - `GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")`
  - `AI_REQUEST_TIMEOUT = int(os.getenv("AI_REQUEST_TIMEOUT", "15"))`
  - `AI_MAX_RETRIES = int(os.getenv("AI_MAX_RETRIES", "1"))`
  - `AI_RETRY_BACKOFF_SECONDS = int(os.getenv("AI_RETRY_BACKOFF_SECONDS", "2"))`
  - `AI_MAX_REAL_CALLS_PER_RUN = int(os.getenv("AI_MAX_REAL_CALLS_PER_RUN", "10"))`
  - `AI_CONSECUTIVE_FAILURE_LIMIT = int(os.getenv("AI_CONSECUTIVE_FAILURE_LIMIT", "3"))`
- Keep `REAL_MODE = False` as permanent default.

**Done signal:**
```python
python -c "from config.settings import REAL_MODE, GEMINI_API_KEY, GROQ_API_KEY, AI_REQUEST_TIMEOUT, AI_MAX_RETRIES; print(REAL_MODE, bool(GEMINI_API_KEY), bool(GROQ_API_KEY), AI_REQUEST_TIMEOUT, AI_MAX_RETRIES)"
```
Expected: `False False False 15 1`

**Task 1d: `requirements.txt`**
- Add `google-generativeai` and `groq`.
- Keep existing: `requests`, `beautifulsoup4`, `python-dotenv`, `pytest`.

**Done signal:** `cat requirements.txt` shows all 6 packages.

---

### Phase 2: Engine Registry + Real Calls

**Task 2a: `src/brand_visibility/ai_client.py` — full rewrite**

**Registry:**
```python
ENGINE_REGISTRY = {
    "engine_a": {"caller": _call_gemini, "key_env": "GEMINI_API_KEY"},
    "engine_b": {"caller": _call_groq, "key_env": "GROQ_API_KEY"},
}
```

**Signature:**
```python
def ask_ai(question: str, brand_context: dict = None, engine: str = "engine_a") -> str:
```

**State tracking (module-level, per-run):**
```python
_real_call_count = 0
_circuit_state = {}  # engine -> consecutive failure count
```

**Real-call gate:**
```python
if settings.REAL_MODE:
    entry = ENGINE_REGISTRY.get(engine)
    if not entry:
        return f"[{engine} error: unknown engine]"
    key = getattr(settings, entry["key_env"], "")
    if not key:
        return f"[{engine} error: missing API key]"
    if _real_call_count >= settings.AI_MAX_REAL_CALLS_PER_RUN:
        return f"[{engine} error: real call budget exhausted]"
    # check circuit breaker...
    # make real call with retry + backoff...
    return result
# else fall through to mock path unchanged
```

**Shared retry helper:**
```python
def _call_with_retry(engine_name: str, caller, question: str, key: str, brand_context: dict = None):
    timeout = settings.AI_REQUEST_TIMEOUT
    max_retries = settings.AI_MAX_RETRIES
    backoff = settings.AI_RETRY_BACKOFF_SECONDS
    last_err = None
    for attempt in range(1, max_retries + 2):
        try:
            response = caller(question, key, brand_context=brand_context)
            _reset_circuit(engine_name)
            if not response or not isinstance(response, str):
                return f"[{engine_name} error: malformed response]"
            return response
        except TimeoutError:
            last_err = f"[{engine_name} error: timeout after {timeout}s]"
            if attempt <= max_retries:
                time.sleep(backoff)
        except Exception as exc:
            status = getattr(exc, "status_code", None)
            if status == 429:
                last_err = f"[{engine_name} error: rate limited]"
                if attempt <= max_retries:
                    time.sleep(backoff)
                continue
            if status in (502, 503, 504):
                last_err = f"[{engine_name} error: service unavailable ({status})]"
                if attempt <= max_retries:
                    time.sleep(backoff)
                continue
            if status in (401, 403):
                _trip_circuit(engine_name)
                return f"[{engine_name} error: auth failed]"
            _trip_circuit(engine_name)
            return f"[{engine_name} error: {exc}]"
    _trip_circuit(engine_name)
    return last_err or f"[{engine_name} error: request failed]"
```

**Circuit breaker helpers:**
```python
def _trip_circuit(engine_name: str):
    _circuit_state[engine_name] = _circuit_state.get(engine_name, 0) + 1
    if _circuit_state[engine_name] >= settings.AI_CONSECUTIVE_FAILURE_LIMIT:
        # circuit open for rest of run; further calls skip provider
        pass

def _reset_circuit(engine_name: str):
    _circuit_state[engine_name] = 0

def _circuit_open(engine_name: str) -> bool:
    return _circuit_state.get(engine_name, 0) >= settings.AI_CONSECUTIVE_FAILURE_LIMIT
```

**Real-call gate with circuit check:**
```python
if settings.REAL_MODE:
    entry = ENGINE_REGISTRY.get(engine)
    if not entry:
        return f"[{engine} error: unknown engine]"
    key = getattr(settings, entry["key_env"], "")
    if not key:
        return f"[{engine} error: missing API key]"
    if _circuit_open(engine):
        return f"[{engine} error: circuit breaker tripped after {_circuit_state[engine]} consecutive failures]"
    if _real_call_count >= settings.AI_MAX_REAL_CALLS_PER_RUN:
        return f"[{engine} error: real call budget exhausted]"
    _real_call_count += 1
    return _call_with_retry(engine, entry["caller"], question, key, brand_context)
# fall through to mock
```

**Mock path unchanged:** when `REAL_MODE = False`, behavior is identical to Stage 1.

**Done signal:** All 14 tests in `tests/test_ai_client.py` pass. No other files needed for this task.

**Task 2b: `src/brand_visibility/step1_check.py` — minimal Option B change**

**Only change:** call `ask_ai()` twice per question.

Replace:
```python
ans_a = ask_ai(q_text, brand_context=None)
mention_a = "mentioned_accurate" if display_name.lower() in ans_a.lower() else "not_mentioned"
# ... hardcoded engine_b synthetic block ...
```

With:
```python
ans_a = ask_ai(q_text, engine="engine_a")
ans_b = ask_ai(q_text, engine="engine_b")
mention_a = "mentioned_accurate" if display_name.lower() in ans_a.lower() else "not_mentioned"
mention_b = "mentioned_accurate" if display_name.lower() in ans_b.lower() else "not_mentioned"
```

And update the payload to use both real results:
```python
questions_payload.append({
    "question_id": q_id,
    "question_text": q_text,
    "engine_results": [
        {"engine": "engine_a", "mention_status": mention_a, "response_excerpt": ans_a[:150] + "..." if len(ans_a) > 150 else ans_a},
        {"engine": "engine_b", "mention_status": mention_b, "response_excerpt": ans_b[:150] + "..." if len(ans_b) > 150 else ans_b},
    ],
})
```

**Nothing else changes in the file.**

**Done signal:** `tests/test_ai_client.py::test_step1_check_offline_uses_both_engines` passes. No new failures in existing test suite.

**Task 2c: `src/brand_visibility/logger.py` — audit and harden**

**Objective:** Ensure no raw client business data leaves the system in logs.

**Audit steps:**
1. Read `src/brand_visibility/logger.py` fully.
2. Identify every place where data is logged.
3. For each log call, verify it does NOT contain:
   - Raw API responses
   - Extracted page text / HTML
   - API keys or auth tokens
   - Full brand facts arrays
4. Allow only metadata logging:
   - `brand_id`, `run_id`, timestamps
   - `status` values (`completed`, `error`, etc.)
   - Engine names (`engine_a`, `engine_b`)
   - Error classes (`timeout`, `rate limited`, `auth failed`)
   - Retry counts, circuit breaker state changes

**If violations found:** Refactor to log metadata only. Do not log raw payloads.

**Done signal:** `grep -RniE 'raw_html|api_key|response\.text|facts\[|content\]' src/brand_visibility/logger.py` returns zero matches for sensitive fields. Logger only emits structured metadata.

**Task 2d: `src/brand_visibility/step3_fix.py` — add unapprove path**

**Objective:** Allow operators to revert an approval without manual JSON editing.

**Implementation:**
- Add `def unapprove_brand(brand_id: str, brand_type: str = None) -> dict:`
- Loads `brand-info.json`, resets:
  - `approved` → `False`
  - `approved_by` → `None`
  - `approved_at` → `None`
- Writes updated file back to disk.
- Returns the updated dict.

**Done signal:**
```python
from brand_visibility.step3_fix import unapprove_brand
result = unapprove_brand("zomato", brand_type="test")
assert result["approved"] is False
assert result["approved_by"] is None
assert result["approved_at"] is None
```

**Task 2e: `src/brand_visibility/llm.py` — client-facing `plain_summary`**

**Objective:** Make diagnosis actionable for real business owners, not just technical.

**Implementation:**
- Update `get_diagnosis()` in `llm.py` to append one actionable line when the diagnosis is for a real visibility issue (not site_unreachable or thin_content).
- Append after existing `plain_summary`:
  ```
  To improve your AI visibility: approve a structured brand fact file so AI engines can reference verified information about your business.
  ```
- Keep technical summaries for `site_unreachable` and `thin_content` — those need operator action, not brand-file approval.
- Do not append the line when `REAL_MODE = False` and brand_type is `test` — keep judge/demo output clean.

**Done signal:** Running diagnosis on a real-brand-shaped check result returns a `plain_summary` ending with the actionable line. Running on a test brand in mock mode returns the original technical-only summary.

---

### Phase 3: TDD GREEN

**Objective:** Make all 14 tests pass.

**Order:**
1. Implement `settings.py` extensions → re-run tests, expect fewer `AttributeError` failures
2. Implement `ai_client.py` → re-run tests, expect functional failures first, then passes
3. Implement `step1_check.py` change → re-run tests, expect full pass
4. Run full suite `pytest tests/ -v` → confirm zero regressions

**Done signal:** `pytest tests/ -v` shows all previously passing tests still pass, all 14 `test_ai_client.py` tests pass.

---

### Phase 4: Mock-Mode Smoke Test

**Objective:** Confirm Stage 1 behavior is unchanged when `REAL_MODE=False`.

**Command:**
```bash
python run_demo.py --brand zomato --approve
```

**Expected:** identical output shape to Stage 1 baseline. No real API calls. Exit 0.

**Done signal:** Command exits 0, outputs checks/diagnoses/generated files, no errors.

---

### Phase 5: Full Regression Suite

**Objective:** Confirm zero regressions across entire codebase.

**Command:**
```bash
python -m pytest tests/ -v
```

**Expected:** All tests pass. No new failures introduced by Stage 2 changes.

**Done signal:** Green test output, under 30 seconds.

---

### Phase 6: Update Project Tracker

**Objective:** Record Stage 2 proof in `.planning/tracker.md`.

**Add to Stage 2 section:**
- Proof log: files created/modified, test results, mock-mode smoke test result
- Verification log: exact commands run and their outputs
- Git commits: list of commits made during Stage 2
- Flags/deviations: any scope changes or issues encountered

**Done signal:** `.planning/tracker.md` Stage 2 section reflects current state.

---

### Phase 7: Git Commit

**Objective:** One commit for all Stage 2 implementation.

**Message shape:** `feat: wire real Gemini/Groq API with registry, cost controls, and per-engine circuit breaker`

**Done signal:** `git log --oneline -1` shows Stage 2 commit. `git status --short` clean.

---

## Rules for This File

- Hermes may update **only** the `Current Context` and `Tracker` sections.
- All other sections are locked once written.
- If scope changes, add a new dated entry in the `Locked Decisions` section — don't edit existing entries.
- This file is the master reference for Stage 2 execution.
- `.planning/tracker.md` is the real project tracker. Update it when statuses change or issues arise.

---

## Reference Links

- `.planning/implementation-plan.md` — stage boundaries, definitions of done
- `.planning/tracker.md` — live status, proof logs, git commits
- `.planning/tech-spec.md` — how it's built, error handling, mock/real table
- `.planning/schema.md` — exact data shapes
- `hermes-plans/stage1.md` — previous stage plan, format reference
