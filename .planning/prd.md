# Product Requirement Document (PRD) — Brand Visibility Agent

## 0. Document Status & How To Use This Doc

- **Status:** Draft, pending Anshu's approval. Once approved, this document is LOCKED — do not edit it during the build. If scope must change, that change is proposed and re-approved explicitly; it is not made silently.
- **Owner:** Anshu + Claude.
- **Audience:** This document is written to be read by both humans (Anshu, teammate, judges) and AI coding agents (Hermes, Antigravity CLI). It defines **what** we are building and **why**. It deliberately does NOT define technical implementation (APIs, MCP tool schemas, code structure — see `tech-spec.md`) or data shapes (see `schema.md`). If an agent needs a technical detail not covered here, the correct behavior is to flag the gap and ask, not to infer or invent one.
- **Companion documents:** `tech-spec.md` (how it's built), `app-flow.md` (what the operator/judges see, screen by screen), `schema.md` (exact data shapes), `design.md` (visual look, written later), `implementation-plan.md` (step-by-step build order), `tracker.md` (live progress log), `rules.md` (hard guardrails — read this alongside the PRD, not instead of it).

---

## 1. One-Line Summary

A tool that checks whether AI engines (like ChatGPT or Gemini) can find and correctly describe a brand, explains why they can't when they can't, automatically generates a structured, agent-readable fact file about the brand from its own real website, and proves — live, in front of judges — that giving AI agents access to that file fixes the problem.

---

## 2. Background & Context

### 2.1 The hackathon

This is being built for **Adobe University Hackathon 2026** (via Unstop, national-level, India), under the theme **"Speak to Agents: The New Language of Brand Visibility."** Team of two: Anshu (team lead, sole coder) and one teammate (pitching + later, real-business outreach). Round 2 — the round this project is built for — begins when Adobe releases the real problem statement (~Aug 16, 2026) and runs to submission (~Sep 6, 2026) via GitHub. Problem statements in this hackathon come from real Adobe product teams, and judges/mentors may be the people who built the actual products this project is adjacent to — accuracy and honesty about what is real vs. simulated matters more than usual.

### 2.2 The real-world grounding

This project is not a guess at what Adobe might care about — it mirrors a real, recent Adobe product direction:

- Adobe acquired **Semrush for $1.9B** (announced Nov 2025, deal closed April 28, 2026).
- Adobe shipped **LLM Optimizer** (GA October 2025) and **Adobe Brand Visibility** (June 2026), combining Semrush's large AI-prompt dataset with LLM Optimizer's analysis.
- Adobe's own stated framework for this problem space is **Sense → Generate → Reach → Learn**. This project uses that exact vocabulary throughout, because it's the language the judges' own company already uses.
- AI-driven traffic to brand sites is a real and growing phenomenon (Adobe has reported year-over-year growth in this channel), which is why "is my brand visible to AI agents" is now a live business problem, not a hypothetical one.

### 2.3 The competitive gap this project targets

At least nine funded companies (Profound, Scrunch AI, Otterly, Peec AI, AthenaHQ, Bluefish, Semrush's own toolkit, and others) already do the **"Sense"** part of this problem well — monitoring and scoring how AI engines talk about a brand. That part is commoditized; a hackathon team cannot out-build it in three weeks. Almost none of them do the **"Reach"** part — actually _serving_ structured, correct brand data directly to AI agents so those agents have something accurate to say. Only Scrunch AI and Adobe's own LLM Optimizer currently do this. **This project's core bet is that the Reach layer — not another monitoring dashboard — is the differentiated, defensible thing to build.**

---

## 3. Problem Statement

Small and mid-sized brands are increasingly discovered, compared, and recommended by AI agents (chat assistants, shopping agents, research agents) rather than found through traditional search. Most of these brands have no structured, machine-readable information about themselves anywhere — AI agents either omit them entirely, or worse, generate confidently wrong descriptions of them because there's nothing accurate to draw from. Existing tools mostly _tell you this is happening_ (monitoring). Almost none _fix it_. There is no simple, self-serve way for a brand to go from "invisible or misrepresented to AI agents" to "agents can find and correctly describe me" in one guided flow.

---

## 4. Goals

### 4.1 Hackathon goals (what this document is ultimately in service of)

- Produce a working, demoable Round 2 GitHub submission that a judge who built the real Adobe product could look at and recognize genuine understanding of the Sense→Generate→Reach→Learn framework, not a surface-level copy of it.
- Win or place well enough in Round 2 to advance to Round 3 (prototype showcase) and ideally Round 4 (grand finale).
- Do this as a two-person team with one coder, no mentor, and a from-scratch codebase built primarily by directing AI agents.

### 4.2 Product goals

- **G1:** Given only a brand's website URL, automatically determine whether AI engines can currently find and correctly describe that brand.
- **G2:** When they can't, explain the specific, concrete reason in plain language a non-technical brand owner would understand.
- **G3:** Automatically generate a structured, agent-readable fact file about the brand, built _only_ from facts actually present on the brand's real website — never invented, estimated, or assumed.
- **G4:** Require a human to explicitly approve that generated file before it is ever served to any agent.
- **G5:** Serve the approved file to AI agents via a small MCP (Model Context Protocol) server, so the "Reach" claim is a real, working mechanism — not a slide.
- **G6:** Prove the fix works with a live, controlled, repeatable before/after demonstration, without depending on real-world AI engines re-indexing content on demand (which takes days to weeks and is outside anyone's control).

---

## 5. Non-Goals / Out of Scope (Headline List)

The authoritative, complete out-of-scope list lives in `rules.md`. The headline exclusions, so no agent builds toward them by mistake:

- **No live dependency on real ChatGPT/Gemini re-indexing during the demo.** The judged, repeatable proof (Step 4 / "Learn") always uses our own controlled demo agent. Real AI engine screenshots are an unpromised bonus only, never a claim made in advance.
- **No user accounts or login system.** Single-operator model — see Section 6.
- **No payments of any kind.**
- **No multi-brand database or CRM.** Brands are represented as simple folder records under `brands/test/` or `brands/real/` — see `schema.md`.
- **No non-English language support.**
- **No calling a real, paid AI API without asking first** (see `rules.md`) — the system defaults to mock mode and only uses a real API when a key is present and use has been explicitly confirmed.

---

## 6. Users & Personas

This project has an unusual user model because it is built to be _demonstrated_, not deployed publicly.

- **The Operator (primary user of the software itself):** Anshu. Runs every step of the tool personally, for every brand — test or real. There is no self-serve signup flow and no second operator role. This is intentional: it keeps scope manageable for a solo coder and matches the "white-glove" real-business outreach plan (Section 8).
- **The Represented User (the story the product tells):** A small business owner whose brand is either invisible to AI shopping/recommendation agents or described incorrectly by them. This persona is never a literal login-in user of the software; they are the beneficiary the Operator runs the tool on behalf of.
- **Judges:** Observe the tool running live, operated by Anshu. Judges do not get their own account or interface — see `app-flow.md` for the exact screen-by-screen walkthrough of what they see.

---

## 7. The Core Flow

Four steps, mapped directly to Adobe's own Sense → Generate → Reach → Learn framework. This mapping should be used consistently in every doc, in the pitch, and in code comments — it is not decorative, it is how we tell judges we understood their own framework.

### Step 1 — CHECK _(maps to: Sense)_

**Input:** One brand website URL.
**What happens:** The system reads the site, determines the business type, and auto-generates a small set of realistic buyer-intent questions a real customer might ask an AI engine (e.g., "best trail running shoes for rocky terrain in India"). It sends those questions to at least two AI engines and checks whether, and how, the brand is mentioned.
**Output:** A check-result record (exact shape defined in `schema.md`) — mentioned / not mentioned / mentioned-but-wrong, per question, per engine.
**Must-have:** Auto-question-generation from a single URL; querying at least two engines; a clear mentioned/not-mentioned/incorrect classification.
**Nice-to-have:** Configurable number of questions; support for more than two engines.

### Step 2 — SHOW WHY _(maps to: Sense → Generate, the diagnostic bridge)_

**Input:** The Step 1 check-result record.
**What happens:** The system explains, in plain language a non-technical brand owner would understand, _why_ the brand was missed or misdescribed — the core reason in scope is "there is no structured, AI-readable information about this brand anywhere," but the diagnosis should be specific to what was actually found (or not found) on the site.
**Output:** A diagnosis record (shape defined in `schema.md`).
**Must-have:** A clear, specific, plain-language explanation tied to real findings from Step 1 — not a generic canned message.
**Nice-to-have:** Categorized diagnosis types (e.g., "no structured data," "thin content," "site unreachable").

### Step 3 — FIX IT _(maps to: Generate + Reach)_

**Input:** The brand's real website content (already fetched in Step 1) and the Step 2 diagnosis.
**What happens:** The system auto-generates a clean, structured, agent-readable fact file about the brand (llms.txt-style — exact format defined in `schema.md`), built **only** from facts actually present on the real source website. Nothing is invented, estimated, or filled in from general knowledge of the brand's category. This file is then shown to the human operator for review. **Nothing is published or served until the operator explicitly approves it** — this is a required, single, concrete approval action (the exact interaction is defined in `app-flow.md`, not left as a vague "human approves" phrase). Once approved, a small MCP server exposes the file so AI agents can fetch it directly — this is the "Reach" delivery mechanism and the project's headline differentiator.
**Output:** An approved, published brand info file, retrievable via the MCP server.
**Must-have:** Facts-only generation; an explicit, single, human approval gate before publishing; a working MCP server exposing the approved file.
**Nice-to-have:** Editing the generated file before approval (not just approve/reject).

### Step 4 — PROVE IT _(maps to: Learn)_

**Input:** The same buyer-intent question, and the approved brand file from Step 3.
**What happens:** Our own small, controlled demo AI agent answers the same question twice, live: once with no access to the brand's file (baseline — generic or missing answer), once with MCP access to the brand's file (correct, brand-specific answer). This is run live, in front of judges, and is fully repeatable on demand — it does not depend on external AI engines re-indexing anything.
**Output:** A visible, side-by-side before/after answer comparison.
**Must-have:** A working controlled demo agent; a repeatable, on-demand before/after run; correct behavior in both the "without access" and "with access" cases.
**Nice-to-have:** Real ChatGPT/Gemini screenshots as a bonus appendix, only if they happen to land in time — never promised to judges in advance, never part of the core judged demo.

---

## 8. Feature List — Must-Have vs. Nice-to-Have

| #   | Feature                                                | Priority                   | Maps to Flow Step | Maps to Build Stage             |
| --- | ------------------------------------------------------ | -------------------------- | ----------------- | ------------------------------- |
| 1   | Read a brand's real website from a URL                 | Must-have                  | Step 1            | Stage 1                         |
| 2   | Auto-generate realistic buyer-intent questions         | Must-have                  | Step 1            | Stage 1 / Stage 2.1 polish            |
| 3   | Query 2+ AI engines and classify brand mention         | Must-have                  | Step 1            | Stage 1 (mock) / Stage 2 (real)       |
| 4   | Plain-language diagnosis of why brand is missing/wrong | Must-have                  | Step 2            | Stage 1                         |
| 5   | Auto-generate structured, facts-only brand file        | Must-have                  | Step 3            | Stage 1–2                       |
| 6   | Single explicit human approval gate before publishing  | Must-have                  | Step 3            | Stage 1                         |
| 7   | MCP server exposing the approved brand file            | Must-have                  | Step 3            | Stage 3                         |
| 8   | Controlled before/after demo agent                     | Must-have                  | Step 4            | Stage 3                         |
| 9   | Mock-mode / real-mode switch (single control point)    | Must-have                  | All               | Stage 1–2                       |
| 10  | Multi-brand support (2–3 test brands, not hardcoded)   | Must-have                  | All               | Stage 4                         |
| 11  | Real small-business onboarding (white-glove)           | Nice-to-have (post-Aug-16) | All               | Stage 5                         |
| 12  | UI/UX polish                                           | Nice-to-have               | App-flow          | Stage 6                         |
| 13  | Real AI engine screenshots as bonus proof              | Nice-to-have, unpromised   | Step 4            | Stage 7                         |
| 14  | Editable brand file before approval                    | Nice-to-have               | Step 3            | Unscheduled                     |
| 15  | More than 2 AI engines queried                         | Nice-to-have               | Step 1            | Unscheduled                     |
| 16  | Configurable question count                            | Nice-to-have               | Step 1            | Unscheduled                     |

---

## 9. Differentiation — Why This Approach

Most competitors and most likely competing hackathon submissions will build another **monitoring dashboard**: score my brand's AI visibility, show a number, maybe a trend line. That is the "Sense" layer, and it is already commercially commoditized by well-funded companies. This project's headline feature is that it does not stop at telling the brand owner there's a problem — **it fixes it and proves the fix works, live, through a real mechanism (MCP)**, not a projected/faked score. This is a deliberate, considered choice made after evaluating the alternative (simulating a "before/after visibility score" without a real mechanism behind it) and rejecting it as less honest and less technically interesting than actually building the Reach layer.

---

## 10. Key Product Decisions Already Locked

These are settled. Agents should build to these, not question or silently reinterpret them:

- **Mock mode is the default state.** The system runs entirely on mocked AI responses until a real API key is present in `.env` (never committed) — see `tech-spec.md` for the exact real-vs-mock table.
- **No real, paid API is ever called without asking first**, even once a key exists.
- **Generated brand info files must only ever contain facts actually found on the real source website.** Never invented, never inferred from category knowledge, never filled in with plausible-sounding defaults. This rule gets stricter once real businesses are involved (Stage 5+), not looser.
- **The Step 3 approval gate is a single, explicit, concrete action** — not an implied or automatic step. Its exact UI/interaction is defined in `app-flow.md`.
- **The live judged demo (Step 4) always uses our own controlled agent**, never a live call to real ChatGPT/Gemini as the primary proof.
- **Single-operator model.** No login system, no multi-user roles, for the hackathon build.
- **Folder structure is locked** (see `README.md` / `tech-spec.md` for the full layout): `.planning/`, `src/`, `brands/test/` vs `brands/real/` (strictly separate, real business data never mixed into test), `config/settings.py` as the one and only mock/real switch, `config/.env.example` documenting required key names with no real keys ever committed.
- **Any scope addition must be flagged before it is built, not after.** This directly addresses a known behavior gap where autonomous build agents have silently made unflagged decisions in past sessions.

---

## 11. Assumptions

- At least one AI provider API (for real-mode operation) will be obtained before Stage 2 begins; until then, all development and testing proceeds in mock mode.
- The 2–3 real businesses used for Stage 5 onboarding will be sourced through the teammate's personal network, per the outreach plan in `rules.md` / `implementation-plan.md`.
- Judges will observe a live run, not use the software themselves — this justifies the single-operator, no-login model.
- The exact Round 2 problem statement (released ~Aug 16) may require adapting features, which is why the architecture and this feature list are intentionally modular (see Section 8 stage mapping).

---

## 12. Risks & Mitigations

| Risk                                                                          | Impact                                                           | Mitigation                                                                                                                                                                           |
| ----------------------------------------------------------------------------- | ---------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Solo coder, no mentor, borrowed laptop                                        | High — could stall the whole build                               | Heavy use of AI agent orchestration (Hermes + Antigravity CLI) with a strict verify-don't-trust process; detailed docs (this doc + tech-spec + schema) so agents don't need to guess |
| MCP server (Step 3/Reach) is the least-proven part of the build               | High — it's the headline differentiator                          | Given its own dedicated build stage (Stage 3), not bundled with other work                                                                                                           |
| Hardcoding to the one test brand (shoe brand)                                 | Medium — would undercut the "real, general tool" claim to judges | Multi-brand support and testing across 2–3 distinct test brands is a Must-have (Feature 10, Stage 4), before any real-brand work begins                                              |
| Build agents (Hermes) silently switching approach or scope without disclosure | Medium — known, previously observed behavior gap                 | `rules.md` mandates flagging any scope change before building it; `tracker.md` requires raw proof + independent human verification + a git commit before any step counts as done     |
| Real AI engines don't re-index brand content in time for a live "real" demo   | Medium — would look like the tool doesn't work if promised live  | Step 4 / Learn explicitly never depends on this; real screenshots are an unpromised bonus only                                                                                       |
| Round 2's real problem statement doesn't match this exact plan                | Medium — three weeks of work could be misaligned                 | Architecture kept modular; stage order explicitly split into pre-Aug-16 (safe to build regardless) and post-Aug-16 (adapts to the real brief)                                        |
| Real business data mishandled or shown without consent                        | Medium — trust and ethical issue with real people                | `brands/real/` kept fully separate from `brands/test/`; explicit consent required before any real data is shown to judges (see `rules.md`)                                           |

---

## 13. Success Metrics

**For the hackathon submission:**

- The GitHub repo is clean, runs end-to-end from a fresh clone in mock mode with no real API key required, and is understandable to a judge reading it cold.
- The live demo (Step 4) runs successfully and repeatably without depending on anything outside our control.
- The submission clearly demonstrates understanding of Adobe's own Sense→Generate→Reach→Learn framework, using that exact language, tied to a real working mechanism (the MCP server) rather than a description of one.

**For the product itself, if judged on merit:**

- Given a real, arbitrary brand website, the system correctly determines mention/no-mention/incorrect-mention status.
- The generated brand file contains zero invented facts, verifiable against the source site.
- The before/after demo shows a measurable, correct difference in agent answer quality with vs. without MCP access.

---

## 14. Glossary

To prevent ambiguity across docs and agents, these terms are used consistently everywhere in this project:

- **Brand:** The business being checked. Represented as a folder record under `brands/test/` or `brands/real/` (exact shape in `schema.md`).
- **Operator:** The single human running the tool (Anshu). Not a generic "user" — there is no other operator role in this build.
- **Sense / Generate / Reach / Learn:** Adobe's own framework for AI visibility. Sense = detect/monitor (Step 1 here). Generate = create structured content (part of Step 3). Reach = deliver that content to agents (the MCP server, part of Step 3). Learn = measure impact (Step 4 here).
- **CHECK / SHOW WHY / FIX IT / PROVE IT:** This project's own four-step flow names, mapped 1:1 to Sense/Generate+diagnose/Generate+Reach/Learn respectively. See Section 7.
- **Mock mode:** The system runs entirely on simulated/fake AI responses, no real external paid API calls made. Default state.
- **Real mode:** A real AI provider API key is present and explicitly enabled; the system makes real calls. Never entered silently — see `rules.md`.
- **Test brand:** A fake or demo brand used for development and testing, stored under `brands/test/`. Safe to break, delete, or experiment on.
- **Real brand:** An actual small business onboarded via the Stage 5 outreach plan, stored under `brands/real/`. Never mixed with test brand data; requires consent before being shown to judges.
- **Approval gate:** The single, explicit, human-confirmed action required before a generated brand file is published/served. Not automatic, not implied.
- **Demo agent:** The small, self-hosted AI agent used for Step 4 / Prove It, run with and without MCP access to a brand's file. Distinct from real-world engines like ChatGPT or Gemini.
- **MCP (Model Context Protocol):** The protocol/mechanism used to expose an approved brand's structured file to AI agents. Exact tool names, schemas, and transport defined in `tech-spec.md`.
- **llms.txt-style file:** The structured, agent-readable brand fact file generated in Step 3. Exact format in `schema.md`.

---

## 15. Related Documents

| Document                 | Covers                                                                     |
| ------------------------ | -------------------------------------------------------------------------- |
| `tech-spec.md`           | MCP server spec, demo agent spec, error handling, real-vs-mock table       |
| `app-flow.md`            | Screen-by-screen operator/judge experience, the exact approval interaction |
| `schema.md`              | Formal data shapes: brand record, check-result, diagnosis, generated file  |
| `design.md`              | Visual look and feel (written later)                                       |
| `implementation-plan.md` | Step-by-step build plan matching the stage order in Section 8              |
| `tracker.md`             | Live, verified progress log                                                |
| `rules.md`               | Hard guardrails, out-of-scope list, scope-change-flagging rule             |

---

## 16. Change Log

| Version | Date                    | Change                                                                        |
| ------- | ----------------------- | ----------------------------------------------------------------------------- |
| 1.0     | Draft, pending approval | Initial PRD covering full project scope, flow, features, and locked decisions |
