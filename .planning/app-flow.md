# App Flow & User Journey — Brand Visibility Agent

_End-to-end execution workflow for the 4-stage pipeline._

---

# App Flow

`prd.md` for what and why, `schema.md` for data shapes, `tech-spec.md` for how the pieces are built — this one's about what actually shows up on screen, who's looking at it, and exactly what has to happen for something to get published. Locked once I approve it, same as the rest.

## The direct answer to "how many screens"

One. There's no dashboard, no login, no separate judge-facing view. The whole thing runs as a single terminal session, top to bottom, and whatever's on that screen is what the operator (me) and the judges are both looking at, at the same time. No sanitized front-end standing between what's actually happening and what the room sees — I think that's actually a point in our favor for this specific theme, not a limitation. If Stage 6 adds a nicer visual layer later, it's a skin on top of this exact flow, not a different flow.

---

## Before anyone's watching: picking the brand

The brand isn't chosen live by fumbling through a menu in front of judges — it's picked ahead of time via a command-line flag:

```
python run_demo.py --brand trailblaze-shoes
```

`python run_demo.py --list` shows what's available if I need to check. There's no interactive "choose a brand" prompt in the demo path — one less thing that can go sideways live.

### The consent gate (real brands only)

If the brand being loaded has `brand_type: "real"` and its `consent_given` field isn't `true`, the tool refuses to run at all:

```
$ python run_demo.py --brand some-real-cafe

ERROR: This is a real brand (brand_type: real) and consent_given
is not set to true in brand.json. Refusing to run.

Record consent first before running this brand.
```

This is what actually enforces the "no real business shown to judges without consent" rule — the flag in `schema.md` doesn't stop anything by itself, this check does. Test brands (`brand_type: "test"`) skip this entirely; there's nothing to consent to for a fake demo brand.

---

## Walking through the session

This is one continuous run, no page reloads, no separate views — just output scrolling down the same terminal:

```
$ python run_demo.py --brand trailblaze-shoes

=========================================
 BRAND VISIBILITY AGENT
 Brand: TrailBlaze (test)
=========================================

[1/4] CHECK — reading https://trailblazeshoes.example.com ...
Detected business type: trail running footwear

Generated buyer questions:
  Q1: "best trail running shoes for rocky terrain in India"
  Q2: "durable trail running shoes under 5000 rupees"

Querying engine_a...
Querying engine_b...

Results:
  Q1 x engine_a   [NOT MENTIONED]
  Q1 x engine_b   [MENTIONED - INACCURATE]
  Q2 x engine_a   [NOT MENTIONED]
  Q2 x engine_b   [NOT MENTIONED]

------------------------------------------
[2/4] SHOW WHY
------------------------------------------
AI engines can't find TrailBlaze because there's no structured,
machine-readable information about the brand anywhere online for
them to read from.

Reason: no_structured_data
  -> No llms.txt, schema.org markup, or similar structured content
     found on the site.

------------------------------------------
[3/4] FIX IT — generating brand file from real site content
------------------------------------------
Draft generated. Preview:

  # TrailBlaze
  Website: https://trailblazeshoes.example.com
  Last verified: 2026-07-30

  ## Summary
  TrailBlaze designs trail running shoes built for rocky and
  uneven terrain.

  ## Facts
  - Sells trail running shoes designed for rocky/uneven terrain.
    (source: https://trailblazeshoes.example.com/about)

=== APPROVAL REQUIRED ===
This will be published and made reachable by AI agents via MCP.
Type APPROVE to publish, or anything else to cancel:
> APPROVE

Published. TrailBlaze's info is now live and reachable via MCP.

------------------------------------------
[4/4] PROVE IT — same question, with and without access
------------------------------------------
Question: "best trail running shoes for rocky terrain in India"

WITHOUT brand access (before):
  "I don't have specific brand recommendations, but look for shoes
   with aggressive lug soles and reinforced toe caps for rocky
   terrain..."

WITH brand access (after):
  "For rocky terrain in India, TrailBlaze is worth checking out —
   they specifically design trail running shoes for rocky and
   uneven terrain..."

=========================================
 Done. Run again with --replay for an instant cached re-run.
=========================================
```

If something errors out (site unreachable, timeout, whatever) it prints a clear error block right there in the flow instead of silently continuing — the exact wording and conditions for that are in `tech-spec.md`, this doc just shows that it's visible, not hidden.

---

## The approval step, specifically

Since this needed to be a real interaction and not just a phrase: the operator has to type the literal word `APPROVE` — not press Enter, not type `y` — before anything gets published. Anything else typed there cancels. This is deliberate for two reasons: it's a hard guard against accidentally publishing something during a live demo from a stray keypress, and it also happens to be a good beat in the demo itself — judges watching literally see the human-approval gate happen, not just hear about it in the pitch.

`approved_by` in the resulting `brand-info.json` gets filled automatically from a fixed operator-name value in the code — not typed at approval time. No reason to add friction to a single-operator flow.

---

## The safety net: `--replay`

```
python run_demo.py --brand trailblaze-shoes --replay
```

Same exact terminal presentation, but instead of live-generating everything, it replays the last completed, already-approved run for that brand straight from disk. This exists so that if something's acting up right before or during a demo slot (slow site, flaky real API call), there's an instant, guaranteed-to-work fallback that still shows the real output from a real earlier run — not a fake one built just for show.

---

## One note for later

None of this changes if Stage 6 adds a lightweight visual layer on top — same four steps, same single approval gate, same consent check, same before/after proof. A nicer coat of paint doesn't get to quietly change what's actually happening underneath; if it ever needs to, that's a re-approval of this doc, not a silent swap.
