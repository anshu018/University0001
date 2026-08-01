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

## Snapshot — last updated 2026-07-30

| Stage                              | Status                                                          |
| ---------------------------------- | --------------------------------------------------------------- |
| 0 — Migrate skeleton               | Not Started                                                     |
| 1 — Website reading, mock pipeline | Not Started                                                     |
| 2 — Real AI API wired in           | Not Started — blocked, no API key yet                           |
| 3 — MCP server + demo agent        | Not Started                                                     |
| 4 — Multi-brand testing            | Not Started                                                     |
| 5 — Real brand onboarding          | Not Started — blocked, real Round 2 brief not out yet (~Aug 16) |
| 6 — UI polish + repo cleanup       | Not Started                                                     |
| 7 — Demo assembly & rehearsal      | Not Started                                                     |

**Right now:** Confirm the scaffold folder actually exists at `C:\Users\ash74\projects\brand-visibility-agent\` with the structure from the original setup task. Once confirmed, Stage 0 can begin.

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

Note: `prd.md`, `schema.md`, `tech-spec.md`, `app-flow.md`, `rules.md`, and `tracker.md` were written with real content directly, ahead of Stage 0 — so the “replace stub” deliverable is already satisfied.

---

## Stage 0 — Migrate skeleton

**Status:** Verified & Done

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

---

## Stage 1 — Website reading, question generation, mock pipeline

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

## Stage 2 — Real AI API wired in

**Status:** Not Started — blocked, no real API key acquired yet

**Proof log:**
_(nothing yet)_

**Verification log:**
_(nothing yet)_

**Git commits:**
_(none yet)_

**Flags / deviations:**
_(none)_

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
- **2026-08-01** — Uncommitted: AGY fixed `__main__` blocks in `step1_check.py`, `step2_diagnose.py`, `step4_prove.py` to load `brands/test/chennai-trail-co/brand.json` via `os.path.join`. Added missing `import os` to `step1_check.py`. Verification: `python -c "import brand_visibility.step1_check; import brand_visibility.step2_diagnose; import brand_visibility.step4_prove; print('OK')"` → `OK`. Git shows 3 modified files, uncommitted. Status: **AWAITING VERIFICATION** — Anshu has not independently checked this yet.
