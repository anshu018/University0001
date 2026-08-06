# Security Fixes: Solution Plan

**Repository:** `brand-visibility-agent`
**Plan Date:** 2026-08-06
**Author:** Hermes senior-dev review
**Source Input:** `hermes-plans/security-report.md` + AGY deep-plan output
**Status:** PLANNED — not yet implemented

---

## 1. Solution Philosophy

These are the rules I’m using to choose the implementation path. Nothing here is a temporary patch.

- **Preserve existing behavior first:** Stage 2.1 YAKE question generation, existing tests, and the current demo flow must keep working. Fixes should be additive or localized, not architectural rewrites.
- **Fix at the boundary, not in the middle:** Input validation, URL fetching, path resolution, and API calls are system boundaries. Hardening belongs there, not scattered across business logic.
- **Make failure safe by default:** If a security control blocks something invalid, it should fail closed and clearly, not fall back to unsafe behavior or leak internals.
- **Keep the system brand-agnostic and offline-friendly:** No hardcoded brand lists, no mandatory external services, and no heavyweight new dependencies.
- **Stage 3 must stay viable:** Stdio discipline, timeout behavior, and dependency pinning should move the project closer to a safe MCP server, not create new transport or packaging problems.
- **Verify before and after:** Every change should have a direct test or verification command. If I can’t verify it, I won’t merge the fix.

---

## 2. Fix Execution Order

I’m ordering fixes by blast radius and Stage 3 readiness, not just severity labels.

### Phase 1 — Protocol & boundary hardening
1. **Stdio discipline**
2. **URL validation + SSRF defense**
3. **Path traversal protection**
4. **Response payload limits**

### Phase 2 — Reliability and secret handling
5. **Apply SDK timeouts**
6. **Thread-safe client state**
7. **Sanitize exception messages**
8. **Dependency hygiene**

### Phase 3 — Quality and regression safety
9. **YAKE noise-word tuning**
10. **Edge-case test expansion**

**Why this order:**
- Phase 1 removes the highest-risk production blockers and prepares the codebase for stdio-based MCP usage.
- Phase 2 fixes runtime reliability and secret handling without changing external behavior.
- Phase 3 improves accuracy and coverage last, because it’s the safest place to refine without breaking shipped behavior.

---

## 3. Per-Fix Implementation Notes

### Fix 1 — Stdio discipline
**Files:** `src/brand_visibility/step4_prove.py`, plus audit of other modules used by or likely to be used by Stage 3.
**Issue:** `print()` and uncontrolled stdout writes can corrupt MCP JSON-RPC frames.
**Approach:**
- Replace direct `print()` diagnostic output with `logging` or redirect to `sys.stderr`.
- Keep user-facing output minimal and explicit.
- Add a small stdio-pollution test that asserts zero stdout writes during module import and normal execution paths.
**Risk:** LOW
**Rollback:** Revert only the stdio-redirection changes; business logic stays untouched.

### Fix 2 — URL validation and SSRF defense
**Files:** `src/brand_visibility/reader.py`, `src/brand_visibility/probe.py`
**Issue:** Unvalidated URLs can reach internal IPs, metadata endpoints, or arbitrary hosts.
**Approach:**
- Allow `http` and `https` only.
- Block private/reserved ranges: `127.0.0.0/8`, `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, `169.254.0.0/16`, `0.0.0.0/8`, `::1`, `fc00::/7`, `fe80::/10`.
- Block cloud metadata endpoints like `169.254.169.254`.
- Enforce max response size before reading full body.
**Risk:** MEDIUM
**Rollback:** Feature-flag the validation block so old behavior can be restored quickly if a legitimate fetch target is blocked incorrectly.

### Fix 3 — Path traversal protection
**Files:** `src/brand_visibility/exceptions.py`
**Issue:** `get_brand_dir()` can be manipulated with `../` sequences.
**Approach:**
- Whitelist `brand_id` to `^[a-zA-Z0-9_-]+$`.
- After path resolution, assert the resolved path is inside the intended `brands/` base directory.
- Raise `BrandNotFoundError` or `ValueError` on violation.
**Risk:** LOW
**Rollback:** Revert validation regex and resolved-path assertion only.

### Fix 4 — Response payload limits
**Files:** `src/brand_visibility/reader.py`
**Issue:** Full response body is loaded into memory without limits.
**Approach:**
- Stream responses where possible.
- Hard-cap read size, e.g. 5 MB.
- Return `site_unreachable` or a dedicated `payload_too_large` diagnosis when the cap is exceeded.
**Risk:** LOW
**Rollback:** Remove cap and stream wrapper; keep diagnosis mapping unchanged.

### Fix 5 — Apply SDK timeouts
**Files:** `src/brand_visibility/ai_client.py`
**Issue:** `AI_REQUEST_TIMEOUT` exists but is never passed to Gemini or Groq SDKs.
**Approach:**
- Pass the configured timeout into actual SDK calls.
- Keep fallback behavior unchanged when SDKs do not accept the parameter.
- Add tests that monkeypatch or mock the SDK call and assert timeout is forwarded.
**Risk:** MEDIUM
**Rollback:** Revert SDK call wrappers only; keep settings intact.

### Fix 6 — Thread-safe client state
**Files:** `src/brand_visibility/ai_client.py`
**Issue:** Module-level `_real_call_count` and `_circuit_state` are not thread-safe.
**Approach:**
- Encapsulate state in a small client/state object.
- Add `threading.Lock` around mutations.
- Keep `reset_client_state()` behavior semantically identical.
**Risk:** MEDIUM
**Rollback:** Restore module-level globals if concurrency behavior changes unexpectedly in tests.

### Fix 7 — Sanitize exception messages
**Files:** `src/brand_visibility/ai_client.py`
**Issue:** Raw exception text is returned to callers.
**Approach:**
- Log raw exceptions to `sys.stderr` or structured logger.
- Return sanitized, generic error strings to callers.
**Risk:** LOW
**Rollback:** Revert only the message sanitization mapping.

### Fix 8 — Dependency hygiene
**Files:** `requirements.txt`
**Issue:** Versions are loose and `mcp` pin is missing.
**Approach:**
- Add bounded versions for all declared dependencies.
- Add `mcp>=1.27,<2`.
- Use existing Python environment; do not introduce new package managers.
**Risk:** LOW
**Rollback:** Revert `requirements.txt` to prior state; venv can be rebuilt from backup.

### Fix 9 — YAKE noise-word tuning
**Files:** `src/brand_visibility/scorer.py`
**Issue:** Noise list over-filters legitimate category terms.
**Approach:**
- Move broad business/category words out of hard noise filters.
- Prefer post-extraction filtering or brand-type-aware filtering instead of silent suppression.
- Keep existing YAKE tests passing.
**Risk:** MEDIUM
**Rollback:** Restore original noise set if topic quality regresses on test brands.

### Fix 10 — Edge-case test expansion
**Files:** `tests/test_scorer.py`
**Issue:** Missing coverage for malformed/unicode/HTML inputs.
**Approach:**
- Add deterministic tests only.
- Do not rely on live network or live AI calls.
- Keep test count manageable.
**Risk:** LOW
**Rollback:** Remove new test cases without changing production code.

---

## 4. Implementation Rules

- One fix area at a time, in the order above.
- After each fix: run `pytest tests/ -v` and confirm green before continuing.
- After Phase 1: run the live pipeline smoke test if the user authorizes it; otherwise use offline verification only.
- After Phase 2: rerun the stdio pollution and timeout tests explicitly.
- After Phase 3: rerun full test suite plus YAKE-specific regression tests.
- No secret material in logs, error strings, or test artifacts.
- All changes must remain offline-friendly and brand-agnostic.

---

## 5. Verification Checklist

- [ ] `pytest tests/ -v` passes with all existing tests green
- [ ] Zero stdout pollution confirmed for `step4_prove` import/run path
- [ ] `fetch_url()` rejects `127.0.0.1`, `169.254.169.254`, and private ranges without sending requests
- [ ] `get_brand_dir("../../etc/passwd")` raises `ValueError` / `BrandNotFoundError`
- [ ] Gemini and Groq call wrappers forward timeout from settings
- [ ] Concurrent `ask_ai()` calls do not corrupt shared state
- [ ] `requirements.txt` includes `mcp>=1.27,<2` and bounded versions
- [ ] YAKE extraction still produces sensible topics for test brands
- [ ] New edge-case tests added and passing
- [ ] No code change introduces new `print()` to stdout in modules used by Stage 3

---

## 6. Notes

- This plan favors **safe, reversible, test-backed changes** over quick hacks.
- If any fix proves riskier than expected, the recommended move is to stop, revert that fix only, and redesign rather than pushing through broken hardening.
- Stage 3 implementation should not start until Phase 1 and Phase 2 are verified.
