# Security & Code Quality Review Report

**Repository:** `brand-visibility-agent`  
**Date:** 2026-08-06  
**Reviewers:** AGY & Hermes Security Audit Pipeline  
**Scope:** `src/mcp_server.py`, `src/brand_visibility/ai_client.py`, `src/brand_visibility/step4_prove.py`, `src/brand_visibility/scorer.py`, `src/brand_visibility/reader.py`, `src/brand_visibility/probe.py`, `requirements.txt`, `tests/test_scorer.py`  
**Review Method:** Read-only static analysis using `audit-context-building`, `code-reviewer`, `sharp-edges`, `vibe-code-auditor`, `007`, `vulnerability-scanner`, `code-review-checklist`.

---

## 1. Executive Summary

A comprehensive, multi-perspective security and code quality review was conducted across the core modules of the `brand-visibility-agent` repository. The codebase demonstrates solid architectural separation and offline-first design principles. However, several **High** and **Medium** severity vulnerabilities and architectural risks were identified that must be remediated prior to production deployment and Stage 3 MCP integration.

### Overall Risk Assessment: **MEDIUM-HIGH**
- **Security & Attack Surface:** Unsanitized URL fetching in `reader.py` poses Server-Side Request Forgery (SSRF) and DoS risks. Path traversal risk exists in `exceptions.py` directory resolution routines. Hardcoded secret placeholders in `ai_client.py` create brittle authentication gates.
- **Protocol & Inter-Process Safety:** The impending Stage 3 MCP server relies on strict stdio protocol isolation. Direct `sys.stdout` printing in scripts like `step4_prove.py` or diagnostic logging threatens to corrupt JSON-RPC transport frames.
- **API Hardening & Reliability:** `AI_REQUEST_TIMEOUT` is defined in configuration settings but is **not passed** to the underlying Google Gemini (`genai`) and Groq SDK calls, leaving requests vulnerable to infinite thread hangs.
- **Stage 2.1 Regression & Edge-Case Coverage:** YAKE keyword extraction in `scorer.py` improves topic generation over bigrams but introduces over-filtering on common business terms and lacks handling for non-ASCII/malformed website text.

---

## 2. Comprehensive Findings Table

| # | File | Skill Focus | Issue | Severity | Evidence | Recommended Fix |
|---|------|-------------|-------|----------|----------|-----------------|
| 1 | `src/brand_visibility/reader.py` | `007`, `vulnerability-scanner` | SSRF vulnerability via unvalidated URL fetching | **HIGH** | Lines 35–48: `fetch_url()` accepts any URL scheme/host including `localhost` and `169.254.169.254` | Validate scheme (`http`/`https`), reject private IP ranges (RFC 1918/4193), block cloud metadata endpoints, and enforce domain allowlists if applicable. |
| 2 | `src/brand_visibility/exceptions.py` | `007`, `sharp-edges` | Path traversal risk in `brand_id` directory resolution | **HIGH** | Lines 82–102: `get_brand_dir()` concatenates `brand_id` directly into `base_dir / "brands" / ...` | Validate `brand_id` against `^[a-zA-Z0-9_-]+$` and ensure `Path.resolve()` remains inside the intended `brands/` base directory. |
| 3 | `src/brand_visibility/ai_client.py` | `sharp-edges`, `vibe-code-auditor` | Defined API timeout (`AI_REQUEST_TIMEOUT`) is never passed to Gemini or Groq SDKs | **HIGH** | Lines 60, 83: `model.generate_content(prompt)` and `client.chat.completions.create()` lack timeout parameters | Pass `request_options={"timeout": timeout}` to Gemini SDK and explicit `timeout` parameter to Groq client instantiation. |
| 4 | `src/brand_visibility/ai_client.py` | `007`, `security-auditor` | Hardcoded string check for API key placeholder `"***"` | **HIGH** | Line 202: `if not key or key == "***":` | Perform strict validation on key existence and length. Avoid relying on literal string sentinel values in application logic. |
| 5 | `src/mcp_server.py` & `src/brand_visibility/step4_prove.py` | `sharp-edges`, `007` | Potential stdout pollution corrupting MCP stdio JSON-RPC transport | **HIGH** | `step4_prove.py:38-43` uses `print()`. `mcp_server.py` is placeholder. | Enforce stdio discipline across all modules used by MCP server: direct all logs, tracebacks, and prints to `sys.stderr` or file logging. |
| 6 | `requirements.txt` | `vulnerability-scanner`, `code-review-checklist` | Unpinned dependencies and missing required `mcp` SDK pin | **MEDIUM** | Lines 1–7: All packages listed without version bounds; `mcp>=1.27,<2` missing | Pin exact or bounded versions for all dependencies (`requests>=2.31.0`, etc.) and add `mcp>=1.27,<2` per tech-spec. |
| 7 | `src/brand_visibility/ai_client.py` | `vibe-code-auditor`, `sharp-edges` | Module-level global state (`_real_call_count`, `_circuit_state`) is thread-unsafe | **MEDIUM** | Lines 17–19: Global primitives mutated in `ask_ai()` without synchronization | Encapsulate call counters and circuit breaker state inside a thread-safe client class or use `threading.Lock`. |
| 8 | `src/brand_visibility/ai_client.py` | `code-reviewer`, `007` | Raw exception detail leakage in return payloads | **MEDIUM** | Line 137: `return f"[{engine_name} error: {exc}] {both_signal}"` appends unhandled exception strings | Log raw exceptions securely to internal logs/stderr; return generic sanitized error messages to caller (`"[engine_a error: provider request failed]"`). |
| 9 | `src/brand_visibility/reader.py` | `vulnerability-scanner` | Uncapped HTTP response payload consumption (DoS vector) | **MEDIUM** | Line 45: `response.text` reads entire HTTP response body into memory without size limits | Stream HTTP responses and enforce maximum response body size (e.g. 5 MB max) before reading into memory. |
| 10 | `src/brand_visibility/scorer.py` | `sharp-edges`, `code-reviewer` | Aggressive `NOISE_WORDS` set over-filters legitimate category terms | **MEDIUM** | Lines 27–34: Includes terms like `"products"`, `"services"`, `"technology"`, `"software"` | Move generic category words to dynamic post-processing instead of hard noise filters to prevent keyword suppression on tech brands. |
| 11 | `src/brand_visibility/probe.py` | `vibe-code-auditor` | Unbounded regex matching on raw page text | **LOW** | Line 58: `re.findall(r"\b[A-Za-z]{4,}\b", brand_text)` runs across full string | Truncate `brand_text` (e.g. first 10,000 characters) before running regex extractions. |
| 12 | `tests/test_scorer.py` | `testing-qa`, `code-review-checklist` | Missing edge-case test coverage for YAKE extraction | **LOW** | Lines 13–46: Tests happy path and empty string, but lacks malformed/unicode/HTML inputs | Add test cases for noisy HTML snippets, non-ASCII characters, and prompt-injection style website text. |

---

## 3. Prioritized Fix List

### Phase 1: Immediate Security & Protocol Hardening (Pre-Stage 3)
1. **Fix Stdio Discipline (`mcp_server.py`, `step4_prove.py`):** Audit all imported modules to ensure `sys.stdout` is exclusively reserved for MCP JSON-RPC protocol frames. Redirect all debug output to `sys.stderr`.
2. **Implement URL Validation & SSRF Defense (`reader.py`):** Restrict `fetch_url()` to HTTP/HTTPS schemes, filter out private IP subnets (127.0.0.1, 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16, 169.254.169.254), and enforce a 5 MB payload size limit.
3. **Path Traversal Protection (`exceptions.py`):** Sanitize `brand_id` using a strict regex whitelist (`^[a-zA-Z0-9_-]+$`) and verify resolved paths remain inside `brands/`.
4. **Enforce API Call Timeouts (`ai_client.py`):** Pass `AI_REQUEST_TIMEOUT` parameter explicitly into Gemini and Groq API client invocations.

### Phase 2: Stage 3 MCP Implementation & Dependency Hygiene
5. **Pin Dependencies (`requirements.txt`):** Add `mcp>=1.27,<2` and pin version bounds for `requests`, `beautifulsoup4`, `python-dotenv`, `pytest`, `google-generativeai`, `groq`, `yake`.
6. **Thread-Safe AI Client State (`ai_client.py`):** Refactor `_real_call_count` and `_circuit_state` into a class instance with thread safety for multi-threaded MCP request handlers.
7. **Sanitize AI Client Exceptions (`ai_client.py`):** Prevent internal exception stack traces or SDK errors from being returned directly in user-facing response strings.

### Phase 3: Stage 2.1 Refinements & Quality Assurance
8. **Tune YAKE Keyword Extraction (`scorer.py`):** Refine noise word lists to avoid discarding valid industry terms for software/technology brands.
9. **Expand Test Coverage (`tests/test_scorer.py`):** Add comprehensive unit tests covering malformed website text, unicode handling, and edge cases.

---

## 4. Verification & Handoff Confirmation

- **File Path:** `hermes-plans/security-report.md`
- **Execution Mode:** Read-only review (Zero code files modified).
- **Top 3 Findings Summary:**
  1. **Stdio Protocol Corruption Risk (Stage 3 Readiness):** Uncontrolled `print()` statements to `sys.stdout` will break stdio JSON-RPC transport when the MCP server is called by agent orchestrators.
  2. **SSRF & Uncapped Fetch in `reader.py`:** `fetch_url()` accepts internal IP addresses/metadata endpoints without scheme validation or content size limits.
  3. **SDK Timeout Omission in `ai_client.py`:** Gemini and Groq SDK calls omit timeout parameters, bypassing configured `AI_REQUEST_TIMEOUT` and introducing thread hang risks.
