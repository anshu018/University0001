# Project Guardrails & Operating Rules — Brand Visibility Agent

# Rules

This is the guardrails file. Everything in here is a hard rule, not a preference — if something elsewhere in the plan ever seems to require breaking one of these, that's a stop-and-ask moment, not a judgment call to make alone. If this file and any other planning doc ever genuinely disagree, this one wins on anything to do with scope, safety, or data integrity.

---

## 1. Out of scope — full stop, not "later"

- No user accounts or login system of any kind.
- No payments, anywhere, ever.
- No multi-brand database or CRM. Brands are simple folder records under `brands/test/` or `brands/real/` — that's the entire storage model, see `schema.md`.
- No non-English language support.
- No public self-serve signup flow. This is white-glove, operator-run only — see `app-flow.md`.
- No dependency on real AI engines (ChatGPT, Gemini, etc.) re-indexing content on demand. That takes days to weeks in reality and is outside anyone's control — the judged demo never relies on it.

These aren't "not yet built" — they're actively not being built. If a build session drifts toward any of these, that's scope creep, and it gets flagged per Rule 6 below.

---

## 2. Money and external APIs

- **Never call a real, paid AI API without asking first.** This holds even when a key is present in `.env` and `REAL_MODE` is set `True` in `config/settings.py`. Having the capability wired in is not the same as permission to spend money on a given call.
- **Mock mode is the default, always**, until a real key exists — and even then, defaults stay mock unless deliberately flipped.
- **If a real API call fails or times out, never silently fall back to a mock response.** Surface a visible error instead. A quietly faked success is worse than a visible failure — this applies during development and would be actively dangerous during a live demo.

---

## 3. Facts only, always sourced

The generated brand info file may only ever contain facts that are actually present on the real source website. Never invented, never inferred from category knowledge ("shoe brands usually..."), never filled in with something plausible.

Concretely: every entry in a brand file's `facts` array needs a real `source` URL pointing at the actual page it came from (see `schema.md`). If it can't be sourced, it doesn't go in the file — there's no exception for "but it's probably true."

This applies to test brands too, not just real ones — consistency matters for testing. But it matters _more_ once a real business is involved, because at that point a wrong or invented fact isn't a bug, it's us putting words in a real business's mouth without their knowledge.

---

## 4. Real business data and consent

- `brands/real/` and `brands/test/` never mix. A real business's data does not get copied into test folders for convenience, and test data doesn't get passed off as real.
- Publishing a real brand's file (the approval gate) and showing that brand to judges (visibility consent) are two separate questions with two separate answers — see the two-gate system in `app-flow.md`. Approval never implies consent. Consent is never assumed, inferred, or skipped because someone seemed fine with it in conversation — it's a recorded yes.
- If consent was never asked, or the answer was no, that business's data does not appear in anything judges see — even if it's technically published and servable over MCP for the working demo itself.

---

## 5. No silent decisions

This is the one rule I want to be most direct about, because it's not hypothetical — it's a documented, repeatedly-observed behavior gap: across prior testing, Hermes has silently switched approaches without disclosing it until directly confronted. This rule exists specifically to counter that pattern in this project, not as a generic best practice.

**The rule:** any scope addition, any deviation from what `implementation-plan.md` describes for the current stage, any change in technical approach (a different library, a different file touched than what was scoped, a simplified version of a requirement), gets flagged _before_ it's built — not mentioned afterward, not buried in a larger completion report, not disclosed only when directly asked.

What flagging actually looks like: stop, say plainly what's different from the plan and why it seemed necessary, wait for an explicit go-ahead before proceeding.

What does **not** count as flagging: a passing mention three paragraphs into a "here's what I did" summary, an answer that only comes out under direct questioning, or a change explained only after it's already been built and committed.

---

## 6. What "done" actually means

A build stage isn't done because Hermes says it's done. It's done when all three of these are true:

1. Raw proof is shown — actual file dumps, actual command output, actual diffs. Not a description of what happened.
2. It's independently re-verified — by reading the actual files, running `git diff` or `git log` against the last commit, not by trusting the report.
3. A git commit exists for that stage.

This applies to Antigravity CLI's own work too, not just Hermes's oversight of it — Antigravity does its own real testing as part of building, and Hermes verifies on top of that, not instead of it. Neither one skips their layer because the other one exists.

---

## 7. Submission and demo honesty

- No unverified specific claims — names, quotes, statistics — go into anything shown to judges. Every claim needs a real, checkable source.
- The live judged demo always uses the controlled internal demo agent for the before/after proof. It never claims a real AI engine has actually re-indexed anything live.
- Real AI engine screenshots, if they happen to exist by demo time, are a bonus appendix only — never promised to judges in advance, never something the schedule bends to produce.

---

## Why the must-have features actually matter here, briefly

Since judges may read these docs directly, worth being explicit about this rather than assuming it's obvious:

- **CHECK** proves the problem is real and measurable for an arbitrary brand, not assumed or staged.
- **SHOW WHY** shows this isn't just detection — there's an actual diagnosis behind the number.
- **FIX IT**, with the facts-only rule and the approval gate, is what makes the generated content trustworthy by construction, not just fast. That's the kind of thing a company that just spent $1.9B on exactly this problem would care about getting right.
- **The MCP server (Reach)** is the actual differentiator — it's the one part of this that almost nobody else in the competitive landscape does. It's a working mechanism, not a slide describing one.
- **PROVE IT** is a live, falsifiable demonstration instead of a claimed score. Judges watch the mechanism work in front of them, which is a harder and more honest thing to fake than a number on a chart.

---

## The one rule about all of these

If following a rule here would mean not finishing something on time, that's still not a reason to quietly work around it. Slower and honest beats fast and silently wrong — every rule above exists because a faster, quieter version of this project would be worth less, not more, once someone actually checks it.
