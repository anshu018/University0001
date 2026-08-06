# Security Fixes: Integrated Implementation Plan (Round 2)

**Repository:** `brand-visibility-agent`
**Plan Date:** 2026-08-07
**Author:** Hermes senior-dev review + AGY security engineering
**Source:** `hermes-plans/security-audit-round2.md` + `hermes-plans/security-solutions-round2.md`

## How to Approach This Without Breaking Things

1. **One fix at a time**, in the order below.
2. **Keep tests green after every change.** Run:
   ```
   PYTHONPATH='src;.pytest-packages' C:\Python314\python.exe -m pytest tests/ -v
   ```
3. **No secrets in logs or prompts.**
4. **No live external scans.**
5. **Brand-agnostic only.** No per-brand exceptions.
6. **Rollback-ready:** each change is isolated and can be reverted independently.

## Fix Order

| Phase | Issue | Files | Severity | Why This Order |
|-------|-------|-------|----------|----------------|
| R2-1 | Prompt injection boundary isolation | `src/brand_visibility/ai_client.py` | HIGH | Affects every AI call; must be fixed before any live AI use |
| R2-2 | DNS rebinding / TOCTOU SSRF | `src/brand_visibility/reader.py` | HIGH | Affects every URL fetch; must be fixed before live fetching |
| R2-3 | Auto-approval guardrail | `src/brand_visibility/step3_fix.py` | HIGH | Prevents accidental publication of real brand data |
| R2-4 | MCP stdio pollution | `step1_check.py`, `step2_diagnose.py`, `step3_fix.py` | MEDIUM | Required for Stage 3 FastMCP transport integrity |

## Issue R2-1: Prompt Injection Defense

**Problem:** Scraped website text is interpolated directly into AI prompts. A malicious page can inject instructions that the LLM may follow.

**AGY’s solution:** XML boundary tags `<untrusted_content>` + system safety instruction + tag escaping.

**My analysis:** Directionally correct. The XML boundary approach is strong because:
- Gemini and Llama models respect XML-style delimiters
- It creates a clear “data zone” vs “instruction zone”

**Integrated final approach:**
1. Add a helper to escape closing boundary tags in untrusted input
2. Wrap `display_name`, `website_url`, `facts`, and `question` inside `<untrusted_content>` tags
3. Prepend a system-style instruction stating that content inside the tags is untrusted data only
4. Apply the same pattern to both `_call_gemini` and `_call_groq`
5. Add unit test that injects a fake instruction inside brand facts and asserts it is not executed as a system instruction

**Test strategy:**
- Mock SDK calls and verify the prompt contains boundary tags and safety instruction
- Verify that injected `</untrusted_content>` sequences are neutralized
- Keep all existing `ask_ai` tests green

## Issue R2-2: DNS Rebinding / TOCTOU SSRF Fix

**Problem:** `_is_safe_url()` validates IP on first DNS lookup, but `requests.get()` does a second lookup. A malicious DNS server can bypass the check.

**AGY’s solution:** Return validated IP from `_is_safe_url()`, pin HTTP request to that IP, pass original hostname in `Host` header.

**My analysis:** Correct direction, but needs HTTPS handling refinement for production.

**Integrated final approach:**
1. Refactor `_is_safe_url()` to return `(is_safe, resolved_ip, hostname)`
2. In `fetch_url()`, after validation:
   - Replace the URL’s netloc with the resolved IP
   - Pass the original hostname in the `Host` header
   - For HTTPS: use a custom `HTTPAdapter` that preserves SNI/hostname verification while connecting to the pinned IP
3. Add a secondary defense: if `requests` ever resolves DNS again, the IP pinning ensures it connects to the validated address
4. Add unit test that mocks `socket.getaddrinfo` to return a safe IP, then verifies `requests.get` is called with the IP-pinned URL

**Tradeoffs:**
- Some CDNs may reject direct IP connections; the `Host` header mitigates this
- HTTPS certificate validation may need adjustment; use `requests` with custom adapter rather than `verify=False`

**Test strategy:**
- Mock DNS to return controlled IPs
- Verify `requests.get` receives IP-pinned URL with correct `Host` header
- Test that unsafe IPs are still blocked before reaching `requests.get`

## Issue R2-3: Auto-Approval Guardrail

**Problem:** `BRAND_AUTO_APPROVE=1` bypasses operator approval even for `brand_type == "real"` records.

**AGY’s solution:** Check `brand_type == "real"`, require `ALLOW_REAL_AUTO_APPROVE=1` for real brands.

**My analysis:** Solid fail-safe design. It preserves test convenience while preventing accidental live publication.

**Integrated final approach:**
1. In `approval_gate()`:
   - Read `BRAND_AUTO_APPROVE` and `ALLOW_REAL_AUTO_APPROVE`
   - If `BRAND_AUTO_APPROVE=1` and `brand_type == "real"` and `ALLOW_REAL_AUTO_APPROVE != "1"`: reject auto-approval, log warning to stderr, fall back to interactive prompt or cancel
   - If `BRAND_AUTO_APPROVE=1` and `brand_type == "test"`: allow auto-approval (preserves existing test behavior)
2. Write all auto-approval decisions to stderr, never stdout
3. Add unit test covering all four combinations of flags and brand types

**Test strategy:**
- Test matrix: real/test brand × auto-approve on/off × explicit override on/off
- Verify real brands are never auto-approved without explicit override
- Verify test brands still auto-approve for backward compatibility

## Issue R2-4: MCP Stdio Transport Discipline

**Problem:** `print()` to `stdout` in step scripts corrupts FastMCP JSON-RPC frames.

**AGY’s solution:** Add `file=sys.stderr` to all progress `print()` calls.

**My analysis:** Minimal, correct, zero-risk fix. Terminal users won’t notice because stderr/stdout are merged in most terminals.

**Integrated final approach:**
1. Audit every `print()` in `step1_check.py`, `step2_diagnose.py`, `step3_fix.py`
2. Add `file=sys.stderr` to all non-data `print()` calls
3. Keep `print()` for actual data returns only if explicitly required by the function contract
4. Add unit tests that capture `sys.stdout` during `run_check()`, `run_diagnose()`, and `approval_gate()` and assert 0 bytes written

**Test strategy:**
- Redirect `sys.stdout` to `io.StringIO()` during test execution
- Assert `stdout.getvalue() == ""`
- Run full suite to ensure no regressions

## Implementation Checklist

- [ ] R2-1: Prompt injection boundary isolation in `ai_client.py`
- [ ] R2-1: Unit tests for prompt injection defense
- [ ] R2-2: DNS rebinding fix in `reader.py`
- [ ] R2-2: Unit tests for IP pinning and SSRF defense
- [ ] R2-3: Auto-approval guardrail in `step3_fix.py`
- [ ] R2-3: Unit tests for approval gate matrix
- [ ] R2-4: Stdio discipline in step scripts
- [ ] R2-4: Unit tests for stdout isolation
- [ ] Full test suite passes: `48+ passed` in `< 1.5s`
- [ ] No source files outside the 4 target files modified

## Verification Criteria

- All 4 HIGH/MEDIUM issues from Round 2 audit are mitigated
- Full test suite remains green
- No new secrets or sensitive data in prompts/logs
- No live external commands run
- Solutions are production-grade, not temporary band-aids
