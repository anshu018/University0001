# Data Schema Specifications — Brand Visibility Agent

# Schema

Read `prd.md` first if you haven't — that's the why. This one's just the how of the data: every JSON shape that gets passed between steps in the pipeline lives here, so nobody (me, Hermes, Antigravity) has to guess a field name halfway through a build.

Four records total, one per pipeline step: **brand record** (input), **check result** (Step 1 / CHECK output), **diagnosis** (Step 2 / SHOW WHY output), and **generated brand file** (Step 3 / FIX IT output). Step 4 (PROVE IT) doesn't produce a stored record — it just runs the demo agent live against an already-approved generated file, so there's nothing new to define for it here.

One rule that applies to everything below: if code disagrees with this file, this file wins, until we sit down and change it together. Same lock rule as the PRD — once I approve this, it's locked.

---

## Where it all lives on disk

```
brands/
  test/                        <- fake demo brands, safe to break
    <brand_id>/
      brand.json                <- the input record
      checks/
        <check_id>.json          <- one file per CHECK run, never overwritten
      diagnoses/
        <diagnosis_id>.json      <- one file per SHOW WHY run
      generated/
        brand-info.json           <- metadata + approval state
        brand-info.llms.txt        <- actual content served over MCP once approved
  real/
    <brand_id>/
      (identical structure, plus consent fields on brand.json — see below)
```

**IDs:** `brand_id` is a lowercase, hyphenated slug and has to match its own folder name exactly (e.g. `trailblaze-shoes`). `check_id` and `diagnosis_id` follow `YYYY-MM-DD-xxxx` — date plus a short random alphanumeric suffix, so files sort chronologically in a directory listing and never collide. The actual code that generates that suffix belongs in `tech-spec.md`, not here — this file just defines the format they have to look like.

---

## 1. Brand record — `brand.json`

The one input everything else derives from.

```json
{
  "brand_id": "trailblaze-shoes",
  "display_name": "TrailBlaze",
  "website_url": "https://trailblazeshoes.example.com",
  "brand_type": "test",
  "added_on": "2026-07-15",
  "consent_given": null,
  "consent_given_by": null,
  "consent_given_on": null
}
```

A few notes:

- `website_url` is the _only_ source the whole pipeline is allowed to read from. Nothing gets pulled from anywhere else, ever — this matters for the facts-only rule later.
- `brand_type` is `"test"` or `"real"`, and has to match whichever folder it's physically sitting in (`brands/test/` vs `brands/real/`). Yes, that's redundant with the folder path — I did that on purpose. A `real` brand sitting under `brands/test/` is now a one-line grep away from being caught instead of a silent bug.
- `consent_given` / `consent_given_by` / `consent_given_on` only apply to real brands. Leave them `null` for test brands. A real brand's data doesn't get shown to judges unless `consent_given` is `true` — the schema just holds the flag, the actual enforcement of "don't show this without consent" is an app-flow / operator responsibility, not something the JSON can stop by itself.

---

## 2. Check result — `checks/<check_id>.json`

Step 1's output. New file every run — I want to be able to re-run a check on the same brand later and compare against the old one, not clobber it.

```json
{
  "check_id": "2026-07-30-x7k2",
  "brand_id": "trailblaze-shoes",
  "run_at": "2026-07-30T14:22:00Z",
  "status": "completed",
  "error_detail": null,
  "business_type_detected": "trail running footwear",
  "questions": [
    {
      "question_id": "q1",
      "question_text": "best trail running shoes for rocky terrain in India",
      "engine_results": [
        {
          "engine": "engine_a",
          "mention_status": "not_mentioned",
          "response_excerpt": "..."
        },
        {
          "engine": "engine_b",
          "mention_status": "mentioned_inaccurate",
          "response_excerpt": "..."
        }
      ]
    }
  ]
}
```

Notes:

- `status` is `"completed"` or `"error"`. On error, `questions` can just be `[]` and `error_detail` holds what went wrong (site down, timeout, whatever). The actual retry/timeout _logic_ is tech-spec.md's job — this field is just where the outcome gets recorded.
- `business_type_detected` gets filled in during this step by the system, it's not something typed in on `brand.json`. It feeds the question-generation logic and shows up later in the diagnosis.
- `engine` — don't hardcode an assumption about what values go here. The actual allowed engine names (mock ones now, real provider names later) are defined in `tech-spec.md`.
- `mention_status` — exactly three allowed values: `not_mentioned`, `mentioned_accurate`, `mentioned_inaccurate`. If a real build finds a case that genuinely needs a fourth value, that's a flagged conversation, not a silent addition.
- `response_excerpt` is just a short snippet kept around for debugging and demo purposes — it's not meant to be a full transcript of what the engine said.

---

## 3. Diagnosis — `diagnoses/<diagnosis_id>.json`

Step 2's output, one per `check_id`.

```json
{
  "diagnosis_id": "2026-07-30-p9q1",
  "check_id": "2026-07-30-x7k2",
  "brand_id": "trailblaze-shoes",
  "run_at": "2026-07-30T14:23:10Z",
  "plain_summary": "AI engines can't find TrailBlaze because there's no structured info about the brand anywhere online for them to read from.",
  "reasons": [
    {
      "reason_code": "no_structured_data",
      "detail": "No llms.txt, schema.org markup, or similar structured content found on the site."
    }
  ]
}
```

`reason_code` is one of: `no_structured_data`, `thin_content`, `site_unreachable`, `outdated_or_incorrect_info`. Same rule as `mention_status` above — new codes get added here first, not invented mid-build.

`plain_summary` is the field that actually gets shown to a brand owner or a judge. Keep it to a sentence or two, no jargon — this is the line that has to land in a live demo.

---

## 4. Generated brand file — `generated/brand-info.json` + `generated/brand-info.llms.txt`

Step 3's output. Two files on purpose: the JSON is metadata + approval state that the app reasons about, the `.llms.txt` is the actual plain-text content that gets served to agents over MCP once approved.

**`brand-info.json`:**

```json
{
  "brand_id": "trailblaze-shoes",
  "generated_at": "2026-07-30T14:25:00Z",
  "approved": false,
  "approved_by": null,
  "approved_at": null,
  "content_file": "brand-info.llms.txt",
  "facts": [
    {
      "fact": "TrailBlaze sells trail running shoes designed for rocky and uneven terrain.",
      "source": "https://trailblazeshoes.example.com/about"
    }
  ]
}
```

`approved` is the one flag the MCP server checks before it'll ever hand this file to an agent. Not approved means not servable — no exceptions, no partial serving.

`facts` is the important part: every single fact needs a `source` pointing at the actual page on the real site it came from. If we can't point to where something came from, it doesn't go in the array. This is what turns "never invent facts" from a rule we just say into something that's actually checkable in the data.

**`brand-info.llms.txt`** (this is the literal content an agent gets back over MCP):

```
# TrailBlaze

Website: https://trailblazeshoes.example.com
Last verified: 2026-07-30

## Summary
TrailBlaze designs trail running shoes built for rocky and uneven terrain.

## Facts
- Sells trail running shoes designed for rocky/uneven terrain.

## Products
- (whatever specific product lines the site actually lists, if any)
```

This file is basically a human-readable rendering of the `facts` array above — the JSON is the source of truth, the `.llms.txt` is generated from it. If the JSON changes after approval, regenerate this file from it; don't hand-edit the two out of sync.

---

## Two things before anyone starts building against this

The old prototype's `demo_brand.json` was written before this doc existed, so it probably doesn't match this shape field-for-field. When the old skeleton gets migrated into the real project structure in Stage 1, conform the old file to this schema — not the other way around. If something about the old file genuinely doesn't fit, that's a flag-it-back-to-me moment, not a quiet judgment call.

Also — I've deliberately left engine names, retry behavior, and how `mention_status` actually gets decided out of this file. That's `tech-spec.md`'s job. This doc only owns the shape of the data, never the logic that produces it.
