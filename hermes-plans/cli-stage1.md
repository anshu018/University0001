# Stage 1 Execution Plan — Brand Visibility Agent

## 1) Project summary

The **Brand Visibility Agent** is being built for the **Adobe University Hackathon 2026** under the theme **"Speak to Agents: The New Language of Brand Visibility."** The system addresses a critical problem for small and mid-sized brands: as AI agents (chatbots, shopping assistants, research agents) increasingly drive discovery and recommendations, brands without structured, machine-readable data are either omitted or confidently misrepresented.

While existing market tools focus solely on monitoring ("Sense"), our tool aligns with Adobe's **Sense → Generate → Reach → Learn** framework to deliver an end-to-end solution:
1. **CHECK (Sense):** Detects whether AI engines recommend a brand for realistic buyer-intent queries.
2. **SHOW WHY (Sense → Generate):** Provides plain-language diagnosis of why the brand was missed or misrepresented.
3. **FIX IT (Generate → Reach):** Automatically extracts facts from the brand's real website to generate a structured `llms.txt`-style brand file, enforces a strict human approval gate (`APPROVE`), and serves approved content over a local MCP (Model Context Protocol) server.
4. **PROVE IT (Learn):** Demonstrates improved AI response accuracy using a controlled before/after demo agent.

### Stage 1 Focus
Stage 1 implements the core 4-step pipeline in **Mock Mode** using live website HTML fetching from `https://www.hoka.com/en-us/` (for test brand `hoka`). It extracts site content, detects business type, generates buyer questions dynamically, queries a mock AI client, produces schema-validated check and diagnosis JSON records, generates facts-only brand files with mandatory source URLs, enforces terminal human approval, and provides a CLI orchestrator with `--replay` support.

---

## 2) Stage 1 deliverables

1. **`requirements.txt`**: Pinned minimal dependencies (`requests`, `beautifulsoup4`, `python-dotenv`). No Firecrawl or MCP v2 dependencies in Stage 1.
2. **`config/settings.py`**: Centralized configuration holding `REAL_MODE = False`, `FIRE_CRAWL_ENABLED = False`, and `OPERATOR_NAME = "Anshu"`.
3. **`src/brand_visibility/exceptions.py`**: Custom exceptions (`SiteUnreachableError`, `ThinContentError`, `BrandNotFoundError`), ID generators for `check_id` and `diagnosis_id` (`YYYY-MM-DD-xxxx`), path resolution utility `get_brand_dir(brand_id)`, and schema field validation constants.
4. **Test Brand Identity Verification**: `brands/test/hoka/brand.json` configured for Hoka (`brand_id: "hoka"`, `website_url: "https://www.hoka.com/en-us/"`, `brand_type: "test"`).
5. **`src/brand_visibility/reader.py`**: Live HTTP website reader module with 10s timeout, 1 retry, returning `status: "completed"` or `status: "error"` (`error_detail: "site_unreachable"`).
6. **`src/brand_visibility/probe.py`**: Content parsing module using BeautifulSoup to extract clean text, count words, and detect thin content (< 100 words).
7. **`src/brand_visibility/persona.py`**: Dynamic business type detection module (`detect_business_type`) without hardcoded shoe or footwear bias.
8. **`src/brand_visibility/scorer.py`**: Dynamic buyer-intent question generator (`generate_questions`) parameterized by detected business type and extracted page keywords.
9. **`src/brand_visibility/reporter.py`**: Disk persistence module for `checks/<check_id>.json` and `diagnoses/<diagnosis_id>.json`, strict to `schema.md`.
10. **`src/brand_visibility/step1_check.py`**: Pipeline script executing Step 1 (CHECK) by combining `reader`, `probe`, `persona`, `scorer`, mock `ai_client`, and `reporter`.
11. **`src/brand_visibility/step2_diagnose.py`**: Pipeline script executing Step 2 (SHOW WHY), reading Step 1 output and in-memory raw text to produce a diagnosis JSON.
12. **`src/brand_visibility/fact_extractor.py`**: Rule-based brand file generator creating `brand-info.json` (metadata + facts with mandatory `source` URLs) and `brand-info.llms.txt`.
13. **Human Approval Gate Interaction**: Terminal interaction requiring the literal string `APPROVE` to set `approved: true`, `approved_by`, and `approved_at` timestamp.
14. **`src/brand_visibility/step4_prove.py` (minimal placeholder)**: Lightweight script invoking `ai_client.ask_ai()` so end-to-end execution completes without error (full MCP before/after agent is deferred to Stage 3).
15. **`run_demo.py`**: Master CLI orchestrator executing the pipeline with flags: `--brand <brand_id>`, `--list`, and `--replay`.

---

## 3) What you must NOT touch

- **Do NOT write any application code during this turn:** Only create `hermes-plans/cli-stage1.md`.
- **No real AI API calls:** Paid provider APIs (OpenAI, Gemini, Anthropic) must not be invoked. `REAL_MODE` remains `False`.
- **No MCP server or MCP agent implementation:** `src/mcp_server.py` and the full before/after demo agent belong strictly to Stage 3.
- **No real brand folder modifications or consent bypasses:** `brands/real/` must remain untouched. Real brand data requires explicit consent recording.
- **No user accounts, login systems, or authentication databases.**
- **No multi-brand databases or CRM frameworks:** Storage remains file/folder-based as defined in `schema.md`.
- **No separate demo folder or duplicate codebases:** Keep a single unified pipeline in `src/brand_visibility/`.
- **No local cached HTML snapshots or fake website data:** Website HTML must be fetched live from `https://www.hoka.com/en-us/`.
- **No Firecrawl integration:** Deferred to Stage 2.
- **No modification of locked planning documents:** `.planning/prd.md`, `.planning/schema.md`, `.planning/tech-spec.md`, `.planning/app-flow.md`, `.planning/implementation-plan.md`, `.planning/rules.md` are locked.
- **No `--dangerously-skip-permissions` or safety protocol overrides.**

---

## 4) Schema summary

Data shapes defined in `.planning/schema.md` are authoritative. If any code contradicts `schema.md`, `schema.md` wins.

### 4.1 On-Disk Directory Structure
```
brands/<test|real>/<brand_id>/
  brand.json                <- Input record
  checks/
    <check_id>.json         <- Step 1 output (YYYY-MM-DD-xxxx)
  diagnoses/
    <diagnosis_id>.json     <- Step 2 output (YYYY-MM-DD-xxxx)
  generated/
    brand-info.json         <- Step 3 metadata + approval state
    brand-info.llms.txt     <- Step 3 Markdown content served over MCP once approved
```

### 4.2 Record Specifications
1. **Brand Record (`brand.json`)**:
   - `brand_id`: Lowercase hyphenated slug (e.g. `"hoka"`). Must match folder name.
   - `display_name`: Human-readable brand name (e.g. `"Hoka"`).
   - `website_url`: Primary source URL (e.g. `"https://www.hoka.com/en-us/"`).
   - `brand_type`: `"test"` or `"real"`. Must match parent directory (`brands/test/` vs `brands/real/`).
   - `added_on`: ISO date string (`YYYY-MM-DD`).
   - `consent_given`, `consent_given_by`, `consent_given_on`: Null for test brands; required for real brands before execution.

2. **Check Result (`checks/<check_id>.json`)**:
   - `check_id`: `YYYY-MM-DD-xxxx` format.
   - `brand_id`: Associated brand ID slug.
   - `run_at`: ISO 8601 timestamp.
   - `status`: `"completed"` or `"error"`.
   - `error_detail`: Null or string (e.g. `"site_unreachable"`).
   - `business_type_detected`: String detected during Step 1.
   - `questions`: Array of objects containing `question_id`, `question_text`, and `engine_results` (array of objects with `engine`, `mention_status` [`"not_mentioned"`, `"mentioned_accurate"`, `"mentioned_inaccurate"`], and `response_excerpt`).

3. **Diagnosis (`diagnoses/<diagnosis_id>.json`)**:
   - `diagnosis_id`: `YYYY-MM-DD-xxxx` format.
   - `check_id`: Reference to associated check.
   - `brand_id`: Associated brand ID slug.
   - `run_at`: ISO 8601 timestamp.
   - `plain_summary`: 1-2 sentence jargon-free explanation for brand owner/judges.
   - `reasons`: Array of objects containing `reason_code` (`"no_structured_data"`, `"thin_content"`, `"site_unreachable"`, `"outdated_or_incorrect_info"`) and `detail`.

4. **Generated Brand File (`generated/brand-info.json` & `generated/brand-info.llms.txt`)**:
   - `brand-info.json`: `brand_id`, `generated_at`, `approved` (boolean), `approved_by` (operator name or null), `approved_at` (ISO timestamp or null), `content_file` (`"brand-info.llms.txt"`), and `facts` (array of objects with `fact` text and mandatory `source` URL).
   - `brand-info.llms.txt`: Plain-text Markdown containing `# <display_name>`, `Website:`, `Last verified:`, `## Summary`, `## Facts`, and `## Products`.

---

## 5) Your execution plan

Execution follows a strict **one module per task** breakdown. Each module will be created and verified independently before being wired into higher-level scripts.

### Task 1: Environment & Settings Foundation (Phase 1)
- Create `requirements.txt` containing `requests`, `beautifulsoup4`, and `python-dotenv`.
- Create `config/settings.py` defining `REAL_MODE = False`, `FIRE_CRAWL_ENABLED = False`, and `OPERATOR_NAME = "Anshu"`.
- Create `src/brand_visibility/exceptions.py` defining custom exceptions (`SiteUnreachableError`, `ThinContentError`, `BrandNotFoundError`), ID generators (`make_check_id()`, `make_diagnosis_id()`), path utility `get_brand_dir(brand_id)`, and schema validation field lists.

### Task 2: Brand Identity Verification (Phase 2)
- Inspect and verify `brands/test/hoka/brand.json` for proper schema alignment (`brand_id: "hoka"`, `display_name: "Hoka"`, `website_url: "https://www.hoka.com/en-us/"`, `brand_type: "test"`).

### Task 3: Live Website Reader Module (Phase 3a)
- Implement `src/brand_visibility/reader.py` with function `fetch_url(url, timeout=10, retries=1)`.
- Use `requests` to fetch live HTML from `https://www.hoka.com/en-us/`. Handle timeouts and HTTP errors, returning `status: "error"`, `error_detail: "site_unreachable"` on failure.

### Task 4: Content Probe Module (Phase 3b)
- Implement `src/brand_visibility/probe.py` with `extract_text(html)`, `count_words(text)`, and `detect_thin_content(text, threshold=100)`.

### Task 5: Business Type Persona Detection (Phase 3c)
- Implement `src/brand_visibility/persona.py` with `detect_business_type(text, url)`.
- Extract category keywords dynamically from page content without hardcoding shoe/footwear bias.

### Task 6: Question Scorer Module (Phase 3d)
- Implement `src/brand_visibility/scorer.py` with `generate_questions(business_type, text, count=2)`.
- Dynamically inject extracted page context words into question templates without artificial fallback text.

### Task 7: Schema Reporter Module (Phase 3e)
- Implement `src/brand_visibility/reporter.py` with `write_check_result` and `write_diagnosis`.
- Persist validated JSON objects to `brands/test/<brand_id>/checks/` and `diagnoses/`.

### Task 8: Step 1 CHECK Pipeline Script (Phase 4a)
- Rewrite `src/brand_visibility/step1_check.py` to wire `reader`, `probe`, `persona`, `scorer`, mock `ai_client.ask_ai()`, and `reporter`.

### Task 9: Step 2 SHOW WHY Pipeline Script (Phase 4b)
- Rewrite `src/brand_visibility/step2_diagnose.py` to process Step 1 output alongside in-memory raw text, determine `reason_code`, generate `plain_summary`, and save diagnosis JSON.

### Task 10: Fact Extractor Module (Phase 5a)
- Implement `src/brand_visibility/fact_extractor.py` to build rule-based facts from HTML headings, meta tags, and paragraphs.
- Ensure every fact object contains a verified `source` URL. Produce `brand-info.json` and `brand-info.llms.txt`.

### Task 11: Human Approval Gate (Phase 5b)
- Implement approval interaction in terminal requiring literal input `APPROVE`.
- Update `approved: true`, `approved_by: OPERATOR_NAME`, and `approved_at` timestamp in `brand-info.json`.

### Task 12: Step 4 Placeholder & Demo Orchestrator (Phase 6a & 6b)
- Maintain minimal `src/brand_visibility/step4_prove.py` calling mock `ai_client.ask_ai()`.
- Implement `run_demo.py` with flags `--brand <brand_id>`, `--list`, and `--replay`.

---

## 6) File structure

```
brand-visibility-agent/
├── .gitignore
├── README.md
├── requirements.txt
├── run_demo.py
├── .planning/
│   ├── app-flow.md
│   ├── implementation-plan.md
│   ├── prd.md
│   ├── rules.md
│   ├── schema.md
│   ├── tech-spec.md
│   └── tracker.md
├── brands/
│   ├── real/
│   └── test/
│       └── hoka/
│           ├── brand.json
│           ├── checks/
│           │   └── <check_id>.json
│           ├── diagnoses/
│           │   └── <diagnosis_id>.json
│           └── generated/
│               ├── brand-info.json
│               └── brand-info.llms.txt
├── config/
│   ├── __init__.py
│   └── settings.py
├── hermes-plans/
│   ├── cli-stage1.md
│   └── stage1.md
└── src/
    └── brand_visibility/
        ├── __init__.py
        ├── ai_client.py
        ├── exceptions.py
        ├── fact_extractor.py
        ├── persona.py
        ├── probe.py
        ├── reader.py
        ├── reporter.py
        ├── scorer.py
        ├── step1_check.py
        ├── step2_diagnose.py
        └── step4_prove.py
```

---

## 7) Skills you will use

- **`python-pro` / Python Code Architecture**: For writing clean, modular Python modules, custom exceptions, strict type hinting, and file path utilities.
- **Web Scraping & Parsing (`beautifulsoup4`)**: For extracting HTML text, metadata, headings, and lists cleanly without introducing HTML noise.
- **Unit Testing & Module Verification**: For executing targeted one-line inline verification commands (`python -c "..."`) to confirm each module's contract before integration.
- **Git Version Control & Code Auditing**: For performing `git status` and `git diff` checks after each task to ensure zero unexpected modifications or scope creep.

---

## 8) Verification plan

### 8.1 Module-Level Empirical Verification
1. **Settings Verification:**
   ```bash
   python -c "from config.settings import REAL_MODE, FIRE_CRAWL_ENABLED, OPERATOR_NAME; print(REAL_MODE, FIRE_CRAWL_ENABLED, OPERATOR_NAME)"
   ```
   *Expected output:* `False False Anshu`

2. **Exceptions & ID Generator Verification:**
   ```bash
   python -c "from brand_visibility.exceptions import make_check_id, make_diagnosis_id, get_brand_dir; print(make_check_id()); print(get_brand_dir('hoka'))"
   ```
   *Expected output:* Valid timestamped ID matching `YYYY-MM-DD-xxxx` format and correct folder path `brands/test/hoka/`.

3. **Reader Module Live Fetch Verification:**
   ```bash
   python -c "from brand_visibility.reader import fetch_url; status, html, err = fetch_url('https://www.hoka.com/en-us/'); assert status == 'completed'; assert len(html) > 1000"
   ```
   *Expected result:* Successful fetch from live Hoka URL without error.

4. **Probe Module Verification:**
   ```bash
   python -c "from brand_visibility.probe import extract_text, detect_thin_content; text = extract_text('<html><body><main><p>Sample page text content here.</p></main></body></html>'); assert len(text) > 0"
   ```
   *Expected result:* Text successfully extracted from HTML DOM structure.

5. **Persona Module Verification:**
   - Execute `detect_business_type` against extracted HTML text. Confirm extracted category is sensible and contains zero hardcoded shoe fallback logic.

6. **Scorer Module Verification:**
   - Execute `generate_questions` with extracted text. Confirm 2 distinct question strings are produced using context words from the site.

7. **Reporter & Schema Writer Verification:**
   - Write sample check and diagnosis dicts to `brands/test/hoka/`. Confirm JSON schema fields strictly match `schema.md`.

8. **Fact Extractor & Approval Gate Verification:**
   - Run `fact_extractor.py` against live text. Confirm `brand-info.json` facts contain valid `source` URLs pointing to `https://www.hoka.com/en-us/`.
   - Test approval gate: typing `APPROVE` sets `approved: true`, `approved_by: "Anshu"`, and ISO timestamp; typing anything else leaves `approved: false`.

### 8.2 End-to-End Pipeline Verification
1. **Live Pipeline Execution:**
   ```bash
   python run_demo.py --brand hoka
   ```
   - Verify terminal output step by step (CHECK → SHOW WHY → FIX IT → PROVE IT).
   - Enter `APPROVE` at the prompt.
   - Verify generated JSON files in `brands/test/hoka/checks/`, `diagnoses/`, and `generated/`.
   - Confirm exit code is 0.

2. **Replay Mode Execution:**
   ```bash
   python run_demo.py --brand hoka --replay
   ```
   - Verify instant replay from cached disk data without re-fetching external URLs or prompting for approval.

3. **Git History & Safety Check:**
   - Run `git status` to ensure clean working directory.
   - Run `git diff` against last commit to verify no out-of-scope files were modified.
