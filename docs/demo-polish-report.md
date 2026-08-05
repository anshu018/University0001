# Brand Visibility Agent — Demo Polish Assessment & Fix Plan

**Date:** 2026-08-05  
**Stage:** Post-Stage 2 polish  
**Status:** Pipeline functional, output quality needs improvement before demo/judge readiness  
**Authors:** Anshu + Hermes Agent  

---

## 1. Executive Summary

Stage 2 implementation is **complete and verified**. The end-to-end pipeline (CHECK → SHOW WHY → FIX IT → PROVE IT) runs successfully with real Gemini/Groq API wiring, per-engine circuit breakers, and 37/37 tests passing.

However, **demo/judge readiness is blocked by question generation quality**. Buyer-intent questions extracted from brand websites are grammatically awkward and semantically weak, which undermines the credibility of the entire pipeline when shown to external stakeholders.

This document outlines the problem, root causes, and a prioritized fix plan to make the output judge-ready without adding heavy dependencies or breaking offline testability.

---

## 2. Current State

### What Works
- Full 4-stage pipeline executes successfully
- Real API wiring for Gemini (engine_a) and Groq (engine_b)
- Per-engine circuit breakers, retries, timeouts, and call budgets
- 37/37 tests passing (21 existing + 14 new Stage 2 tests)
- Both mock mode and real API mode functional
- Brand files generate and replay correctly
- Step 4 proves visibility improvement with before/after

### What Doesn’t Work Well
- **Buyer-intent question generation** produces weak outputs like:
  - `"What is the best Earn in software & technology solutions?"`
  - `"What is the best Online in food & restaurant services?"`
- These questions appear in Step 1 CHECK results, which are the primary judge-facing output
- Poor questions make the AI look unintelligent, even though the underlying architecture is solid

---

## 3. Problems Identified

### Problem 1: Noisy Topic Extraction
**Location:** `src/brand_visibility/scorer.py::_extract_page_topics()`

The function extracts single words from page text using a basic noise filter. It captures verbs, adverbs, and promotional action words like:
- `Earn`, `Money`, `Online` (Uber)
- `Click`, `Apply`, `Drive` (generic CTAs)

These words pass through the current filter because they are 4+ characters and not in the hardcoded NOISE_WORDS set.

### Problem 2: Template Grammar Forces Bad Fit
**Location:** `src/brand_visibility/scorer.py::generate_questions()`

Questions use templates like:
- `"What is the best {topic} in {business_type}?"`

When `{topic}` is a verb/adverb (`Earn`, `Online`), the result is grammatically broken:
- `"What is the best Earn in software & technology solutions?"` ❌

The template assumes `{topic}` is a noun phrase, but extraction often returns non-nouns.

### Problem 3: No Semantic Validation
There is no check that extracted topics are actually buyer-intent relevant. The pipeline trusts extraction output and injects it directly into user-facing questions.

---

## 4. Root Causes

| Root Cause | Evidence | Impact |
|------------|----------|--------|
| Single-word extraction is too loose | `Earn`, `Online`, `Click` pass filters | Verb/adverb noise reaches templates |
| NOISE_WORDS is static and brand-specific | Works for some brands, fails for others | Maintenance burden, not scalable |
| Templates are grammatically rigid | `"What is the best X in Y?"` assumes X is noun-phrase | Broken output when X is not a noun phrase |
| No fallback quality gate | Bad extraction → bad question, no interception | User-facing errors visible to judges |

---

## 5. Proposed Solution

### Approach: Frequency-Ranked N-Grams + Lightweight Heuristics + Template Fallback

**Do NOT use:** LLM-based question rewrite (violates offline-friendly requirement, adds API dependency)

**Do NOT use:** Per-brand whitelist/blacklists (does not scale, maintenance burden)

**DO use:** Pure-Python n-gram extraction with lightweight filtering and graceful fallback

### Solution Architecture

#### 5.1 Extract Candidate Phrases
Instead of single words, generate:
1. **Bigrams** — two consecutive valid words (e.g., `"Ride Sharing"`, `"Cloud Migration"`)
2. **Title-case raw phrases** — proper nouns from the page (e.g., `"Gourmet Pizza"`, `"Driver Earnings"`)
3. **High-signal singles** — valid words as fallback

Rank all candidates by frequency, deduplicate, and keep top 2-3.

#### 5.2 Lightweight Noise Filtering
Apply heuristics without NLP libraries:
- **Stopword filter:** Remove common English stopwords
- **Noise-word filter:** Hardcoded set of known non-topic words (verbs, adverbs, CTAs)
- **Suffix filter:** Block words ending in verb/adverb suffixes (`-ing`, `-tion`, `-ment`, `-ive`, `-ly`, etc.)
- **Length filter:** Block words < 4 or > 40 chars
- **Title-case priority:** Prefer proper nouns over generic lowercase words

This stays offline-friendly and dependency-free.

#### 5.3 Fix Template Grammar
Update question templates to be:
- **Plural-tolerant:** `"What are the top {topics} options in {biz}?"` instead of `"What is the best..."` 
- **Phrase-friendly:** Work with multi-word topics, not just single words
- **Category-safe:** Use business type as semantic anchor, not just filler

#### 5.4 Three-Tier Fallback
Prevent bad extraction from reaching users:

1. **Tier A:** Strong topics extracted from page → `"What are the top {topic} options in {biz}?"`
2. **Tier B:** Weak/no topics → business-type generic → `"What are the top options in {biz}?"`
3. **Tier C:** No business type detected → fully generic → `"Which brands lead in this category?"`

This ensures the pipeline never outputs `"What is the best Earn in...?"`

---

## 6. Why This Solution

| Criterion | Our Approach | Alternatives |
|-----------|-------------|--------------|
| **Offline-friendly** | ✅ Pure Python, no network | ❌ LLM rewrite needs API |
| **Zero heavy deps** | ✅ No NLP libraries | ❌ POS tagging needs NLTK/spaCy |
| **Brand-agnostic** | ✅ Works for any industry | ❌ Per-brand lists don’t scale |
| **Minimal code change** | ✅ Modify 1 function + templates | ❌ Full pipeline rewrite |
| **Testable** | ✅ Deterministic, unit-testable | ❌ LLM output is stochastic |
| **Maintainable** | ✅ Single filter set | ❌ Growing per-brand lists |

### Why Not LLM Rewrite?
- Violates offline-friendly requirement
- Adds API cost/latency to Stage 1
- Makes test results non-deterministic
- Overkill for a deterministic extraction problem

### Why Not Per-Brand Whitelists?
- Every new brand requires manual config
- Easy to forget, leads to regressions
- Not sustainable for a generic tool

---

## 7. Implementation Plan

### Phase 1: Fix Extraction Logic (scorer.py)
- [ ] Rewrite `_extract_page_topics()` to generate bigrams + title-case phrases
- [ ] Add lightweight suffix/length/noise filters
- [ ] Rank by frequency, deduplicate, return top 2-3

### Phase 2: Fix Question Templates
- [ ] Update `generate_questions()` to use plural-tolerant templates
- [ ] Implement three-tier fallback logic
- [ ] Ensure grammatical correctness for all tiers

### Phase 3: Update Tests
- [ ] Add test: noisy text produces no verb/adverb-only questions
- [ ] Add test: extraction returns multi-word phrases when available
- [ ] Add test: fallback triggers when extraction returns empty

### Phase 4: Verify End-to-End
- [ ] Run `python -m pytest tests/ -v` → 37+ passing
- [ ] Run `python run_demo.py --brand zomato --approve` → clean questions
- [ ] Run `python run_demo.py --brand uber --approve` → clean questions
- [ ] Run `python run_demo.py --brand <new-brand>` → clean questions

### Phase 5: Cleanup
- [ ] Delete temporary verification scripts
- [ ] Update tracker/docs with polish notes
- [ ] Commit changes with clear message

**Estimated effort:** 2-3 hours  
**Risk:** Low — pure Python, no new dependencies, fully testable

---

## 8. Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Question quality | No outputs like `"What is the best Earn in..."` | Manual review of demo output |
| Grammar | All questions grammatically correct | Template review |
| Brand agnosticism | Works for any brand without config | Test with 3+ brands |
| Test coverage | 37+ tests passing | `pytest tests/ -v` |
| Demo readiness | Output suitable for judges/stakeholders | Human review |

---

## 9. Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Filter too aggressive, loses good topics | Medium | Medium | Tune noise list iteratively; keep fallback |
| N-grams produce awkward phrases | Low | Low | Title-case raw phrases as quality override |
| New brands introduce new noise | Low | Low | Generic suffix/stopword filters catch most cases |
| Template changes break existing tests | Low | Low | Update tests in Phase 3 alongside code |

---

## 10. Recommendation

**Proceed with the n-gram + lightweight heuristics + template fallback approach.**

This is the minimal-change path to demo-ready output that respects all project constraints:
- Offline-friendly
- No heavy dependencies
- Brand-agnostic
- Testable
- Maintainable

The alternative — living with broken questions or adding per-brand noise lists — is not sustainable.

---

## Appendix: Example Before/After

### Before (Current Broken Output)
```
Q1: "What is the best Earn in software & technology solutions?"
Q2: "What is the best Online in food & restaurant services?"
```

### After (Expected Output)
```
Q1: "What are the top Ride Sharing options in software & technology solutions?"
Q2: "Which Food Delivery solutions are most recommended in food & restaurant services?"
```

Or, if extraction is weak:
```
Q1: "What are the top options in software & technology solutions?"
Q2: "Which brands lead in food & restaurant services?"
```

Both are grammatically correct, semantically meaningful, and judge-ready.

---

*End of Report*
