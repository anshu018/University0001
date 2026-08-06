# Security & Bug Re-Audit Report (Round 2)

**Repository:** `brand-visibility-agent`  
**Date:** 2026-08-07  
**Auditor:** AGY Senior Security & Code Quality Audit Pipeline  
**Scope:** Complete re-audit of all 17 source files under `src/brand_visibility/`, `src/mcp_server.py`, `config/settings.py`, `requirements.txt`, and test coverage gaps in `tests/`.  
**Audit Methodology:** Static line-by-line inspection using `audit-context-building`, `code-reviewer`, `sharp-edges`, `vibe-code-auditor`, `007`, `vulnerability-scanner`, and `code-review-checklist`.

---

## 1. Executive Summary

A comprehensive post-remediation security re-audit was executed across the entire `brand-visibility-agent` codebase following the completion of Phase 1, Phase 2, and Phase 3 security hardening work. 

### Overall Security Posture: **SIGNIFICANTLY HARDENED / READY FOR STAGE 3 SPECIFICATION**
- **Phase 1-3 Remediation Status:** Path traversal defenses in `exceptions.py`, thread-safe state locks in `ai_client.py`, SDK timeout parameter forwarding, basic SSRF IP range checks in `reader.py`, YAKE noise filtering in `scorer.py`, and stdio isolation in `step4_prove.py` are **FULLY MITIGATED and verified**.
- **Remaining Production & Stage 3 Attack Surfaces:** 
  1. **Prompt Injection Vector:** External website text passed directly into Gemini/Groq prompt templates without XML delimiter isolation or role boundary enforcement (`ai_client.py`).
  2. **DNS Rebinding / TOCTOU SSRF Vulnerability:** Time-of-check to time-of-use IP resolution gap between `_is_safe_url()` and `requests.get()` (`reader.py`).
  3. **Unrestricted `BRAND_AUTO_APPROVE` Override:** `step3_fix.py` allows `BRAND_AUTO_APPROVE=1` to bypass operator approval for real business records.
  4. **MCP Transport Stdio Pollution:** `step1_check.py`, `step2_diagnose.py`, and `step3_fix.py` contain direct `print()` statements to `stdout` that will corrupt MCP JSON-RPC frames if invoked within MCP tool handlers.

---

## 2. Complete Audit Findings Table

| # | File & Line Reference | Skill Focus | Issue / Risk Description | Severity | Current Status | Concrete Fix Recommendation |
|---|----------------------|-------------|--------------------------|----------|----------------|-----------------------------|
| 1 | `src/brand_visibility/ai_client.py` (L53–56, L76–79) | `007`, `red-team-tactics` | **Prompt Injection Vector:** Scraped website text and facts carrying potential prompt injection payloads are interpolated directly into user prompt templates without delimiter isolation. | **HIGH** | OPEN | Wrap `display_name`, `website_url`, `facts`, and `question` inside strict XML tags (e.g. `<brand_facts>...</brand_facts>`) and instruct model to treat contents strictly as untrusted data. |
| 2 | `src/brand_visibility/reader.py` | `007`, `vulnerability-scanner` | **DNS Rebinding / TOCTOU SSRF:** `_is_safe_url()` resolves DNS to validate IP, but `requests.get()` resolves DNS a second time. A malicious DNS server returning a safe IP first and `127.0.0.1` second bypasses check. | **HIGH** | OPEN | Bind HTTP requests directly to the validated IP address resolved during `_is_safe_url()`, passing original domain in the HTTP `Host` header. |
| 3 | `src/brand_visibility/step3_fix.py` (L124–126) | `007`, `security-auditor` | **Unrestricted Auto-Approval in Production:** `BRAND_AUTO_APPROVE=1` environment variable bypasses human operator approval even for `brand_type == "real"` records. | **HIGH** | OPEN | Restrict `BRAND_AUTO_APPROVE=1` to execute only when `brand_type == "test"` or when explicit `TEST_MODE=True` environment variable is active. |
| 4 | `src/brand_visibility/step1_check.py` (L66, 93, 97, 103, 130, 148), `step2_diagnose.py` (L87–89), `step3_fix.py` (L103, 122) | `sharp-edges`, `007` | **MCP Stdio Transport Pollution:** Direct `print()` statements to `sys.stdout` across pipeline step scripts threaten to corrupt JSON-RPC frames if step scripts are called by Stage 3 MCP tools. | **MEDIUM** | OPEN | Redirect all diagnostic logging and step progress prints in step scripts to `sys.stderr` (`file=sys.stderr`), preserving `sys.stdout` exclusively for RPC frames. |
| 5 | `src/mcp_server.py` (L1–2) | `vulnerability-scanner`, `007` | **Stage 3 Server Placeholder (Pre-Implementation Gap):** Placeholder file lacks authentication, schema validation, rate limiting, and `approved == True` brand record filters. | **MEDIUM** | OPEN (Pre-Stage 3) | Implement `FastMCP` server with strict input schema types, `approved == True` filter, and non-distinguishable `{found: false}` error outputs per `tech-spec.md`. |
| 6 | `src/brand_visibility/ai_client.py` (L202) | `code-reviewer`, `security-auditor` | **Hardcoded Placeholder Key Check:** Checks `key == "***"` as API key sentinel. | **LOW** | MITIGATED (Safe fallback) | Replace string comparison with strict key format/length validation helper `_is_valid_key()`. |
| 7 | `src/brand_visibility/scorer.py` (L145–151) | `code-reviewer` | **Score Calculation Quirk:** Accuracy rate calculation gives 100% accuracy weight on 1 mention out of 2 queries, yielding overall "High" score (70/100) for a 50% mention rate. | **LOW** | OPEN | Calculate accuracy rate relative to total query evaluations rather than total mentions, balancing overall score metrics. |
| 8 | `src/brand_visibility/fact_extractor.py` (L39–40) | `vibe-code-auditor` | **Raw HTML Tag Residue:** Decomposes standard tags, but leaves custom XML or `<svg>`/`<iframe>` inline script blocks if malformed HTML is passed. | **LOW** | MITIGATED | Enforce pre-cleaning using `BeautifulSoup` script/style decomposition. |
| 9 | `tests/` | `testing-qa`, `code-review-checklist` | **Test Coverage Gaps for Production Risks:** Test suite lacks specific coverage for DNS rebinding protection, prompt injection masking, and stdio pollution in `step1_check.py` through `step3_fix.py`. | **MEDIUM** | OPEN | Add unit test cases in `tests/test_phase3_security.py` verifying DNS rebinding defense, prompt injection escaping, and step script stdio isolation. |

---

## 3. Comprehensive Audit of `src/brand_visibility/` Modules

### 3.1 `src/brand_visibility/ai_client.py`
- **Thread Safety:** `_state_lock = threading.Lock()` protects `_real_call_count`, `_circuit_state`, and `_last_settings`. Race condition free. (**MITIGATED**)
- **SDK Timeouts:** `AI_REQUEST_TIMEOUT` forwarded to Gemini (`request_options={"timeout": timeout}`) and Groq (`timeout=timeout`). (**MITIGATED**)
- **Exception Leakage:** Raw exceptions logged to `sys.stderr`, sanitized string `"[engine_a error: request failed]"` returned. (**MITIGATED**)
- **Prompt Injection:** `prompt = f"Brand: {display_name}\nWebsite: {website_url}\nFacts: {json.dumps(facts)}\nQuestion: {question}"` contains unescaped user HTML text. (**OPEN - HIGH**)

### 3.2 `src/brand_visibility/reader.py`
- **SSRF Defense:** `_is_safe_url()` blocks loopback, private IP subnets, link-local, reserved, and cloud metadata IPs (`169.254.169.254`). (**MITIGATED**)
- **Response Size Cap:** `MAX_RESPONSE_BYTES = 5 * 1024 * 1024` (5 MB) enforced via chunk streaming. (**MITIGATED**)
- **DNS Rebinding:** Time-of-check to time-of-use gap exists between `_is_safe_url()` DNS lookup and `requests.get()` DNS lookup. (**OPEN - HIGH**)

### 3.3 `src/brand_visibility/exceptions.py`
- **Path Traversal Protection:** `get_brand_dir()` validates `brand_id` via `^[a-zA-Z0-9_-]+$` and asserts resolved path stays within `base_dir / "brands"`. (**MITIGATED**)

### 3.4 `src/brand_visibility/scorer.py`
- **YAKE Noise Tuning:** `STRUCTURAL_NOISE` separates web controls/cookies from legitimate category words (`software`, `technology`, `services`). (**MITIGATED**)
- **Topic Phrase Post-Filtering:** `_is_valid_topic_phrase()` rejects keywords consisting entirely of web noise or stop words. (**MITIGATED**)
- **HTML Stripping & Bounded Input:** HTML tags stripped and text truncated to 20,000 chars before YAKE extraction. (**MITIGATED**)
- **Malformed Input Safety:** `score_visibility()` validates `isinstance(questions, list)` before iteration. (**MITIGATED**)

### 3.5 `src/brand_visibility/step4_prove.py`
- **Stdio Discipline:** Diagnostic prints redirected to `sys.stderr` (`file=sys.stderr`). 0 stdout writes confirmed. (**MITIGATED**)

### 3.6 `src/brand_visibility/step1_check.py`, `step2_diagnose.py`, `step3_fix.py`
- **Stdio Discipline for Stage 3:** Direct `print()` statements still write progress updates to `stdout`. Must be redirected to `sys.stderr` before Stage 3 MCP integration. (**OPEN - MEDIUM**)
- **Auto-Approval Safety:** `step3_fix.py` permits `BRAND_AUTO_APPROVE=1` to auto-publish real brand records. (**OPEN - HIGH**)

### 3.7 `src/mcp_server.py`
- **Stage 3 Readiness:** Placeholder file. Tech spec requirements (`get_brand_info`, `list_brands`, stdio transport, `{found: false}` non-distinguishable outputs for unapproved/missing brands) must be built in Stage 3. (**OPEN - PRE-IMPLEMENTATION**)

---

## 4. Prioritized Fix Recommendations

### Priority 1: High Severity (Pre-Production / Stage 3 Blockers)
1. **Remediate Prompt Injection (`ai_client.py`):** Wrap extracted site facts and inputs inside `<untrusted_brand_context>` tags and enforce strict system prompt instructions.
2. **Fix DNS Rebinding SSRF (`reader.py`):** Pin HTTP requests directly to the IP address resolved during `_is_safe_url()` validation.
3. **Restrict `BRAND_AUTO_APPROVE` (`step3_fix.py`):** Disallow `BRAND_AUTO_APPROVE=1` for `brand_type == "real"` records unless explicitly running in a test suite.

### Priority 2: Medium Severity (Stage 3 MCP Protocol Safety)
4. **Complete Stdio Discipline (`step1_check.py`, `step2_diagnose.py`, `step3_fix.py`):** Redirect all progress prints in step scripts to `sys.stderr`.
5. **Expand Security Unit Test Suite (`tests/`):** Add unit tests for DNS rebinding protection, prompt injection escaping, and step script stdio isolation.

---

## 5. Verification Confirmation

- **Report Status:** Complete read-only security re-audit report written to `hermes-plans/security-audit-round2.md`.
- **Files Audited:** All 17 source files under `src/brand_visibility/`, `src/mcp_server.py`, `config/settings.py`, `requirements.txt`, and `tests/`.
- **Codebase Modifications:** 0 source code files modified (Read-only audit).
