---
name: factory-humanizer
description: Removes the cues that make prose read as AI-generated and forces a deliberate human voice, in English or Japanese. English runs a two-mode flow — Build (pin a register and a speaker before drafting) and Audit (a deterministic scanner, `scripts/unslop_text_scan.py`, with a scored/CI-gateable exit code) — grounded in an audited analysis of 89,239 Reddit posts. Japanese runs a 3-phase prompted rewrite (draft → mandatory self-critique "anti-AI pass" → final rewrite) against a 25-pattern catalog spanning symbol residue, vocabulary bias, and thought-structure — Japanese has no scanner in v1, audit is manual by design. Use when the user says "de-slop this", "humanize this text", "remove AI tells", "this reads like AI", "make it sound like me", or the Japanese equivalents ("AI臭い", "人間らしく書き直して", "AIっぽさを消して"), or when any other factory skill's content needs a de-AI pass before publishing.
---

# Factory — Humanizer (de-slop, EN + JA)

*Two narrow jobs: remove the cues that make text read as machine-written, and — where it reads as AI
because nobody chose a voice — force a deliberate one. It has no house style and does not write for
you. A guardrail is not a writer.*

## Step 0 — Which language?

If it isn't obvious from the text itself or the request, ask. The two paths below are **not**
interchangeable — they have different mechanics, not just different vocabularies.

## English

Two modes. Both apply to prose for a reader: posts, email, essays, READMEs, marketing copy.

### Mode 1: Build — when drafting something new

Most "sounds like AI" outcomes are a specification problem, not a wording problem. Before writing
anything for a reader, pin a **register** (A casual / B conversational-professional / C expository /
D formal — see [references/writing-with-intent.md](references/writing-with-intent.md)), then a
**speaker** inside it (a real person with a stake, not "a helpful assistant"), then the **claim** the
piece actually asserts, then let **structure** follow the argument rather than a template. Vary
sentence length on purpose — uniform rhythm is the single most-cited, least-fixable tell.

### Mode 2: Audit — when reviewing or cleaning existing prose

Run the scanner first, then fix in priority order, then do the human pass the scanner can't do:

```bash
python3 scripts/unslop_text_scan.py <path>                 # full report + slop score
python3 scripts/unslop_text_scan.py <path> --severity high # only the strongest signals
python3 scripts/unslop_text_scan.py <path> --json          # machine-readable, for CI (exit code = high-severity count)
```

The scanner is a thin lexical filter — it catches the mechanical tells (em dash, "not just X, it's
Y", assistant boilerplate, diction memes, formatting tics). It **cannot** see the highest-value
tells: uniform sentence rhythm, sycophancy, hedging, saying nothing at length. A clean scan means
the lexical layer is clean, not that the writing reads as human. After every scan, read the draft
aloud and check the Part B structural tells in [references/english.md](references/english.md) by
ear — that pass is the real work.

**Do not over-correct.** The over-corrected "trying not to sound like AI" register (staccato
fragments, forced lowercase, fake typos, conspicuous em-dash avoidance) is itself a tell, cataloged
in references/english.md Part B #20. Applying these rules too hard lands you in that second voice
just as visibly as the first.

**Reporting.** Lead with the verdict and the single highest-impact change. Then findings by
priority with file:line and the fix. Close with the slop score and the top three changes.

## Japanese (日本語)

No scanner in v1 — audit is prompted, not scripted. See
[references/japanese.md](references/japanese.md) for the full pattern catalog (第1層/第2層/第3層),
the humanity/warmth section, per-model tics, and the EN↔JA AI-buzzword mapping. **This is an
intentional v1 boundary, not an oversight** — a Japanese lexical scanner is real new engineering
(different surface tics than English, no audited-corpus basis yet) and is deliberately deferred.

Three-phase flow:

1. **Draft.** Read the input carefully. Scan for all 25 patterns + 11b across the three layers.
   Rewrite the problem spots. Confirm the rewrite reads naturally aloud, varies sentence length,
   states specifics instead of vague claims, and carries the writer's own subjectivity/temperature.
2. **★most important★ Anti-AI pass (self-interrogation audit).** Read the draft start to finish as
   if someone else wrote it. Ask "where does this still look AI-generated?" using the checklist:
   - Ctrl+F for 「これにより」「さらに」「重要」「不可欠」 — high hit count means still smells.
   - Are all sentences the same length? (short and long mixed is natural)
   - Does deleting any one paragraph leave the rest intact? (too independent = AI-like)
   - Is 語尾 looping through 2-3 patterns (です/でしょう/ます)?
   - Is there an actual opinion, or is everything neutral reporting?
   - Concrete names/places/dates/numbers, or all "ある企業"/"専門家"?
   - Read sentence by sentence: "would a human write this?"
   - Would a coworker say "this is obviously AI" on seeing it?
   - Is it *too* polished — perfect structure, uniform rhythm, balanced points, i.e. missing the
     human mess?
   List the remaining friction points as concise bullets.
3. **Final rewrite.** Fix everything the anti-AI pass found. No compromises here.

**Output format:** (1) draft, (2) "where does this still look AI-ish?" bullets, (3) final version,
(4) optional change summary. Preserve this exact 4-part contract — it's what makes the self-critique
step actually happen instead of getting skipped.

## Using this from another skill

Any factory skill that needs a de-AI pass before publishing invokes this skill with a language
argument (`factory-humanizer, language: ja` or `en`) rather than assuming which catalog applies.
