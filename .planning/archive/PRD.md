# Brand Visibility Agent — Our Hackathon Plan (PRD)

This is our guess-project for Adobe University Hackathon 2026. Built ahead of the real question (drops Aug 16), so we're not starting from zero.

---

## 1. What we're building, in one sentence

A tool that checks if a small brand shows up when people ask AI chatbots for recommendations, explains why it doesn't, then actually fixes it — and proves the fix worked, live, in front of judges.

---

## 2. The problem, in plain words

People are starting to ask AI chatbots things like "what's the best running shoe brand" instead of Googling it. Big, famous brands get mentioned. Small brands almost never do — because the AI can't find clean, trustworthy facts about them anywhere. Adobe itself just built real products around this exact problem (LLM Optimizer, Brand Visibility), so we know this is a real, proven problem — not something we made up.

---

## 3. Our 4-step story

Adobe has its own name for this idea: **Sense → Generate → Reach → Learn**. We built our own small version of the same idea, in simpler words:

1. **CHECK** — Ask a couple of AI chatbots a few buyer questions, see if the brand shows up.
2. **SHOW WHY** — Explain in plain words why it's missing.
3. **FIX IT** — Auto-write a clean info file about the brand, and build a small tool that lets AI agents actually read that file.
4. **PROVE IT** — Ask the same question again, live. Judges watch the AI's answer change in front of them.

---

## 4. Features — what we MUST have vs. what's a bonus

**MUST HAVE (the demo doesn't work without these):**
- Brand gives us just ONE thing: their website link
- System reads the website, figures out what kind of business it is
- System writes a few realistic buyer questions on its own
- System asks those questions to 2 real AI chatbots
- System checks if the brand's name shows up in the answers
- System explains, in plain words, why it's missing
- System auto-writes a clean info file about the brand
- A small tool (MCP server) that lets an AI agent fetch that file
- Live demo: ask our own mini AI agent the same question twice, show the answer change

**NICE TO HAVE (only if time is left over):**
- A simple webpage instead of plain text on screen
- Saving results so a brand can check again later
- Supporting more than 2 AI chatbots
- A nicer-looking score number or graph

---

## 5. What we're copying vs. what's actually ours

Copying ideas is normal in hackathons — everyone builds on existing ideas. Here's what's borrowed and what's genuinely different:

**Borrowed ideas (we build our OWN version of these):**
- The basic "ask AI, check if mentioned, score it" idea — from two real open-source projects, GEO Command Center and open-geo
- The "clean info file for AI to read" idea — based on a real existing idea called `llms.txt`
- The 4-step story — Adobe's own official framework, so we're speaking Adobe's own language back to them

**What's actually ours, not copied from anyone:**
- The **FIX IT** step — almost nobody else in this space actually fixes the problem, most tools only watch and report a score. We build the fix.
- The small MCP tool that hands the brand's info directly to AI agents. A similar tool called Ansvisor exists, but it's built for *human analysts* to ask questions about the data. Ours is built for *AI shopping agents* to fetch the data themselves. Different direction — still wide open.
- The live **before/after** demo trick — showing the AI's real answer actually change in front of judges, instead of a fake score number jumping up on a slide.

---

## 6. How everything connects (the pipeline)

See `pipeline-diagram.mermaid` for the visual flowchart. In simple words:

```
Website link
    |
    v
1. Read the website
    |
    v
2. Auto-write buyer questions
    |
    v
3. Ask 2 AI chatbots
    |
    v
4. Brand mentioned? --- No --> 5. Explain why
                                     |
                                     v
                          6. Auto-write clean info file
                                     |
                                     v
                          7. Quick human check (one click)
                                     |
                                     v
                     8. Small tool serves file to AI agents
                                     |
                                     v
                     9. Ask the SAME question again, live
                                     |
                                     v
                     Judges see the answer change
```

---

## 7. The code pieces (how the actual files connect)

```
run_demo.py  <-- runs the whole story, start to finish
    |
    +-- step1_check.py     (step 1: CHECK)
    +-- step2_diagnose.py  (step 2: SHOW WHY)
    +-- step3_fix.py       (step 3: FIX IT)
    +-- step4_prove.py     (step 4: PROVE IT)
            |
            v
      ai_client.py   <-- the ONLY file that talks to real AI
            |
            v
   (later) real AI API — Gemini / OpenAI / Claude
```

Every step calls `ai_client.py` when it needs to talk to an AI. That means when we finally get a real API key, we only change ONE file — everything else keeps working exactly as it does now.

---

## 8. What we already built today

- `demo_brand.json` — a fake test business (a small Indian trail-running shoe brand)
- `ai_client.py` — currently gives fake answers, ready to swap for a real AI later
- `step1_check.py` through `step4_prove.py` — all 4 steps, working
- `run_demo.py` — runs the whole thing, tested and confirmed working

---

## 9. What's still left to build (honest list)

1. **Real website reading** — right now the brand's info is hand-typed. Need code that reads a real website and pulls out facts automatically.
2. **Auto-writing buyer questions for ANY brand** — right now the 2 questions are hardcoded for our shoe brand. Needs to work for any business type.
3. **A real AI API connection** — needs an API key (Gemini's free tier is likely our first pick, still needs confirming).
4. **An actual small MCP server** — right now step 3 just saves a text file. We haven't yet built the real tool that lets an AI agent fetch it. Need to look this up properly.
5. **The human "approve" click** — currently automatic, no pause. Needs a real yes/no step.
6. **A nicer demo screen** — optional, currently just plain text.
7. **Testing on 2-3 more fake brands** — to make sure it's not only built to work for our one shoe brand.

---

## 10. Rough plan (dates)

- **Now – Aug 8:** Build the real pieces above using our fake brand, get everything working end to end for real (not fake answers).
- **Aug 9:** Round 1 (separate — pure DSA/logic prep, no work on this project that day).
- **Aug 10–15:** Polish, test on more fake brands, prepare the pitch, keep building ahead.
- **Aug 16:** Real question drops. Compare against our guess, adjust fast (should be quick since our pieces are small and reusable).
- **Aug 16 – Sep 6:** Round 2 — finish it for real, submit on GitHub.

---

## 11. What might change once the real question drops

- Could be scoped to one specific industry — our design doesn't assume any one industry, so it should adapt fine.
- Could ask for something very specific we didn't guess (like a required integration with an actual Adobe tool) — we'd add that piece on top.
- Could want us to go deep on just ONE of our 4 steps instead of touching all 4 — we'd cut scope down, not add more.

Either way, nothing built so far gets thrown away — these are small reusable pieces, not one fixed app.
