---
name: factory-content-review
description: Independent, fresh-eyes review of one finished piece of published-facing content (a post, article, card, reply, recap) — the content-side counterpart to `factory-code-review`. Reads the finished text, the full source-material packet behind every checkable claim, and the project's own config (`factory/content-review.md`) for audience/voice and project-specific checks, then checks accuracy, tone, and quality in that order and posts a table + a SHIP/FIX/BLOCK verdict. Built to run two ways — invoked in-context via the Skill tool by Claude itself, or run cold by ANY CLI-based coding agent (e.g. Codex CLI's `codex exec`) that was only handed this file's absolute path and the content packet, with no prior conversation context. `factory-marketing-post` runs this as the last gate before publishing, for every content type. Use when the user says "factory content review", "review this post/article before it goes out", "second opinion on this content", or when `factory-marketing-post` invokes it before publishing.
---

# Factory — Content Review (external / second-opinion)

*A different set of eyes — sometimes literally a different model — on the finished piece, after every
factual check and de-slop pass has already run, right before it goes out.*

This skill is read two ways:
1. **In-context (Claude, via the Skill tool).** You already have the conversation's context — the
   content type, the sources you gathered, the draft. Skip straight to **Step 2**.
2. **Cold, by an external CLI agent** (Codex CLI or similar) that was handed nothing but this file's
   absolute path and the content packet. You have no prior context — do **Step 1** first.

> If you're an external agent reading this file directly: this is a plain markdown instruction file,
> not a Claude Code skill invocation — just follow it as your task.

---

## Step 1 — Establish context (skip if you already have it)

- Find `factory/` at the repo root. Read `factory/content-review.md` for this project's audience,
  voice rules, and project-specific checks. If that file doesn't exist, stop and say so — do not
  guess at a project's audience or tone from the content alone.
- Identify what you're reviewing from the prompt you were given: the finished text, which content
  type it is, and where the source packet lives (a file, or pasted directly into the prompt).

## Step 2 — Read everything

- The **finished text**, verbatim, exactly as it will publish (not a summary of it).
- **The full source-material packet behind every checkable claim** — filing figures, API responses,
  screenshots, whatever the content type's own build steps produced as evidence. A reviewer with no
  sources can only comment on style, not accuracy.

  **Put every verified fact in the packet, including ones that feel too small to bother with.** A
  gap in the packet reads to the reviewer exactly like an overclaim in the content — you cannot tell
  the two apart from the report, and a missing-but-true fact costs a wasted re-verification cycle to
  clear. If something in the finished text isn't independently checkable from what you were handed,
  that itself is worth a note, not silence.
- `factory/content-review.md`'s audience and voice section, and the content type's own file (voice
  quirks, banned words/registers, structural rules) if it's named in the prompt.
- Whether this is code-adjacent content (a technical explainer, a paper) or pure marketing copy — the
  bar for precision differs, and the config should say which this project treats it as by default.

## Step 3 — Review

Check these three, **in this order** — accuracy first, because a beautifully-written wrong claim is
worse than a plain true one:

1. **Accuracy** — does every number, name, date, and capability claim match a source in the packet?
   Is anything stated with more confidence than the evidence carries? Flag anything uncheckable from
   what you were given, separately from anything actually contradicted by a source.
2. **Tone** — does it match the account/publication's documented voice? Free of hype, of apology, of
   anything that reads as machine-produced (see the project config's banned-register list if it has
   one)?
3. **Is it actually good** — would a reader in the stated target audience find this engaging, clear,
   and worth their time? Does it earn its length? Does the opening line survive the "would a stranger
   stop scrolling" test if the project config says that's the bar?
4. **Project-specific checklist** — every bullet from `factory/content-review.md`'s checklist, each
   scored on its own line.

**Calibration: not nitpicky.** You're asked for what would materially embarrass the account or lose a
reader — a wrong figure, a claim the source doesn't support, a passage that drags, a tonal misfire. Do
not bikeshed word choice or restyle sentences you merely would have written differently.

## Output

| Check | Status | Note |
|-------|--------|------|
| Accuracy | ✅/⚠️/❌ | one-line TLDR |
| Tone | ✅/⚠️/❌ | one-line TLDR |
| Quality | ✅/⚠️/❌ | one-line TLDR |
| *(project checklist item)* | ✅/⚠️/❌ | one-line TLDR |

Then, on its own line, exactly one of:
```
VERDICT: SHIP
VERDICT: FIX
VERDICT: BLOCK
```
`SHIP` — nothing above is ❌, ship as-is. `FIX` — one or more ⚠️/❌ that a targeted revision clears
without redoing the whole piece. `BLOCK` — a ❌ serious enough (a wrong hard number, a claim the
source contradicts, a tonal or factual problem that would embarrass the account) that the piece must
not go out until it's rebuilt, not just patched.

Be ruthlessly concise below the table — no word salad:
- ❌ **Fix:** what's wrong, what it should say instead, which source (or its absence) makes the case.
- ⚠️ **Heads up:** what looks off, why it's not blocking.

Make this table + verdict your **final printed output** — a headless caller (`codex exec -o <path>`,
etc.) captures only that and needs the full table and the `VERDICT:` line present so it can be grepped
without re-running anything.

## What to do with the result

For each accuracy flag, first check whether the claim is actually wrong or merely **absent from the
packet** — then either fix the content or go verify it for real. Do not just delete a flagged sentence
to make the report go quiet; that throws away true material. Weigh tone and quality notes on the
merits — disagreeing is allowed, but say why, and record that reasoning wherever this content type's
own ledger/history lives.

**Re-run the project's own mechanical gates after applying fixes** — a fix written in a hurry can
reintroduce something the de-slop pass already banned. Re-run this review only if the changes were
substantial, not for a one-word correction.

## In a `factory-marketing-post` run

This is the **last gate before publishing**, for every content type — after the de-slop pass and after
every factual check the content type's own file requires, before the composer opens. `VERDICT: BLOCK`
means the run does not publish this tick; treat it the same as any other `NOT_POSTED` outcome and say
why. `VERDICT: FIX` means apply the fix, re-run the project's mechanical gates, and re-review only if
the changes were substantial before publishing. Skip this gate entirely if `factory/content-review.md`
doesn't exist or says `Enabled: no` for this project — do not block a project that hasn't opted in.
