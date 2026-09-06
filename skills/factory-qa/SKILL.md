---
name: factory-qa
description: The QA gate — actually use the thing you just built, as a user would, before anyone else has to. Stands the feature up, writes a list of real user scenarios, walks every one of them on the running stack, and iterates (fix → re-push → re-QA) until functionality, intent, hidden assumptions, and UI/UX paper-cuts are all clean — checking both mobile and desktop viewports for frontend work, and real prompts/context/output quality across 3–5 examples for backend/LLM work. Ends by posting a QA report with screenshots to the issue and handing every artifact to an external second-opinion reviewer ("what did I miss? what paper-cuts am I not seeing?"). Runs in `factory-implement` after the code review and BEFORE the demo, as a blocking gate. Use when the user says "factory qa", "QA this", "test it like a user", or when `factory-implement` reaches its QA step.
---

# Factory — QA (the "actually use it yourself" gate)

*A code review reads the diff. This step **uses the product**. Nothing gets demoed or handed off until you have driven the feature yourself, with your own eyes on the real thing.*

> **Precondition:** the change is built, `factory-recheck` passed, the stack is up, and the branch/PR
> exists. If nothing has been built yet, there is nothing to QA — **invoke the `factory-implement`
> driver via the Skill tool** and run the full pipeline instead of starting work here.

---

## Why this skill exists — read it, it is about you

The failure mode this gate was written to kill:

> The implementation gets written. A recheck reads it. A code review reads the diff. Then a demo gets
> recorded — and **nobody ever actually looked at the feature**. The UI is broken, the text overflows,
> the buttons don't line up, a shortcut was taken during the build that is obvious the moment you open
> the page — and none of it is caught, because every gate so far only ever read *code*.

So:

- **Reading the diff is not QA.** Recording a demo is not QA. QA is *you, using the feature, on the
  running stack, trying to break it and judging the result.*
- **Looking is mandatory.** If it has a UI, you open it and **look at it**. If it's a pipeline, you read
  the **actual prompts and payloads** that went out and the **actual output** that came back.
- **"It probably works" is not a finding.** Every claim you make in the QA report must be backed by
  something you actually did, with an artifact (screenshot, log excerpt, output sample) to show it.
- **You are not done when you are tired.** You are done when the list is clean.
- **Do not be lazy here.** Being lazy at this step is precisely how the user ends up doing this QA
  themselves — which wastes their time and makes the whole run worthless.

---

## Step 1 — Ground yourself

1. **Re-read the requirements.** The full tracker issue *and every comment, start to finish* — the same
   non-negotiable rule as the rest of Factory. Comments carry the corrections and decisions that
   supersede the original description; the intent you are QAing against lives there.
2. **Re-read the plan** (`./tasks/*.md`) and skim the diff (`git diff <base>...HEAD`) — not to review it,
   but so you know **what to go poke at** and which shortcuts to be suspicious of.
3. **Read `factory/qa.md`** — this project's own QA checklist: the things that only show up on the
   running thing and that this codebase gets wrong repeatedly. If the file doesn't exist, run the
   generic checks only and say so in the report.
4. **Confirm the stack is genuinely up and serving the new code.** Provision/reload exactly as the
   repo's `factory/` docs say (`factory/dev-manager.md` if present, else `factory/deployment.md`), and
   use the URLs/ports that tooling actually reports — never a hardcoded address. If you're QAing stale
   builds you are wasting the whole step, so verify the running thing includes your change.

## Step 2 — Write the scenario list BEFORE you start clicking

Write out, explicitly, **the things a real user would actually do with this feature.** Not test cases
against your implementation — *user intentions*. Ground them in the issue: whoever asked for this had
something they wanted to do.

Cover, at minimum:
- The **happy path**, end to end, the way it will really be used.
- The **entry points** — how a user even arrives here, including from a cold start / fresh load / logged out.
- **Empty, single, and many** states (no data, one row, a realistic pile of rows — and the long-name /
  long-text case).
- **Failure and recovery** — bad input, a rejected action, a dropped request. Does it tell the user
  what happened, or just die silently?
- **Adjacent things you might have broken** — the feature next door that shares the component, route,
  or table you touched.

Keep the list as a live todo list and **extend it as you go**. Poking at a real running app always
surfaces scenarios you couldn't have predicted from the code — when it does, add them and walk them.
Adding items is a sign the QA is working, not a sign of scope creep.

## Step 3 — Walk every scenario on the running stack

Go through the list one item at a time and confirm each is *actually true*. For each, capture evidence
as you go (screenshot for UI, output/log excerpt for backend) — you need it for the report and you will
not remember the details later.

### Tooling

- **Frontend / anything with a UI:** drive a real browser. Use **`claude-in-chrome`** first (invoke the
  `claude-in-chrome` skill, then its `mcp__claude-in-chrome__*` tools). If it isn't available, fall back
  to the **`playwright-cli`** skill. Either is fine — what is *not* fine is skipping the browser and
  asserting from the source that it must render correctly.
  - Take screenshots. **Actually read the screenshots you take** — they are the point, not a checkbox.
  - Check the **browser console and network tab** for errors/warnings and failed requests while you
    click around. A page that renders but throws on every interaction is a fail.
- **Backend / CLI / API:** exercise it for real — the CLI, real requests, the actual job/queue — and read
  the logs while it runs.

### The five things you are checking

Score each of these; every one gets a row in the report.

**1. Functionality — does it work?**
No obvious functional problems. Every scenario on the list does what it should. Nothing 500s, hangs,
silently no-ops, or throws in the console. Errors are handled visibly rather than swallowed.

**2. Intent — does it do what it was actually *meant* to do?**
Different question from "does it work". Re-read the issue and ask: *if the person who filed this opened
what I just built, would they say "yes, that's what I asked for"?* A feature can be bug-free and still
be the wrong feature, or a technically-correct reading of a request that misses the point.

**3. Hidden assumptions — what did you decide without asking?**
Every implementation makes judgment calls the issue didn't specify. Some are invisible in code review
and blatant the second you use the thing. Now that you're the user, hunt them:
- Did you **narrow the scope** to whatever was easiest, and is that narrowing now visible?
- Did you **take a shortcut that fakes the outcome instead of building the mechanism** — seeded/hardcoded
  data standing in for a real pipeline, a stubbed call, a fixture masquerading as a live result, one
  path implemented and the others left as "future work"? **This is the single most important thing to
  catch here.** If a real user's run would not produce this result, it is not built — say so.
- Did you pick a default, a limit, an ordering, a copy string, or an edge-case behavior that a
  reasonable person might have wanted different?

Every assumption you surface gets **posted on the issue and @-mentioned to the owner** (from
`factory/ownership.md`) — that is the driver's standing rule and this is the step that most often
triggers it. If an assumption is *wrong*, fix it; if it's merely *a choice*, flag it.

**4. Paper-cuts, polish, and design quality.**
Look at it — critically, as a designer would, not as the person who wrote it.
- **Both viewports, every time:** desktop **and** mobile (resize the window / use a real mobile
  viewport). "It's a desktop feature" is not an excuse to skip mobile unless the issue says so.
- Text: overflow, truncation, wrapping, clipped labels, placeholder/lorem text left in, typos,
  inconsistent capitalization, developer-ese leaking into user-facing copy.
- Layout: misalignment, broken centering, inconsistent spacing/padding, cramped or stranded elements,
  things that don't line up with the rest of the app, horizontal scrollbars.
- States: hover/focus/active/disabled, loading states, empty states, error states — do they exist at
  all, or does the UI just sit there looking broken while something loads?
- Consistency: does it look like it belongs in this product, using the app's own components, spacing,
  and type — or does it look bolted on?
- **The bar is professional and polished. Amateurish is a FAIL.** Consult the **`frontend-design`**
  skill for the standard you're holding it to. Do not accept "good enough" — if you'd be embarrassed
  showing it to the user, it isn't done. Keep fixing until it is genuinely right.

**5. The project's own checklist (`factory/qa.md`).**
Turn **every bullet into its own todo** and walk them one at a time, on the running thing. Each bullet
gets its own targeted look — open the surface it names, run the case it describes — not one glance at
the feature answering all of them at once. Each gets its own row in the report table, and its note
must cite what you actually did or saw (a screenshot, a value, a viewport width), or `n/a — <why this
change cannot violate it>`. "Looks fine" on a checklist row is not a QA of that row.

### If it's an LLM / data pipeline, QA the pipeline, not the plumbing

For LLM-backed or data-processing work, "it ran without erroring" is not QA. You must inspect:
- **The actual prompt(s) sent** — dump/log the fully-rendered prompt, not the template. Is the context
  you *think* you're passing really in there? Anything missing, duplicated, truncated, empty, or
  obviously junk?
- **The context and inputs** — is the retrieved/assembled data correct and relevant, or did it silently
  come back empty and the model made something up?
- **The quality of the output** — read it. Is it *correct*, and is it *good*? Would you ship this text /
  this classification / this record to a user?
- **Run 3–5 real examples, never one.** One example proves nothing — it is exactly how a pipeline that
  works for a single cherry-picked input reaches handoff. Pick genuinely different inputs (different
  companies / records / shapes, including an awkward one) and compare the outputs against each other
  for consistency as well as correctness.
- **Confirm the mechanism is real** for these runs — that the output came from the pipeline actually
  doing the work, not from seeded data, a cached fixture, or a hand-written sample.

## Step 4 — The loop: fix, re-push, re-QA

This is an **iterative loop, not a single pass.**

```
stack up → scenario list → walk it → findings → fix → re-apply/reload → re-walk the affected scenarios
   ↑                                                                              │
   └──────────────────────────────────────────────────────────────────────────────┘
```

- Fix what you find. Small paper-cuts and clear bugs: **just fix them.** Something structural or a wrong
  interpretation of the issue: it is **never too late to go back** to `factory-plan` /
  `factory-execute` — reaching the QA step is not permission to ship something half-working.
- **Commit and push the fixes to the task branch** so the PR reflects what you actually QA'd.
- Then **re-run the affected scenarios** against the reloaded stack. A fix you didn't re-verify is not a
  fix.
- **Note for the driver:** if QA pushed any commits, the code-review gate that already passed is now
  looking at stale code — re-run the code-review gate once before moving to the demo.
- Stay in this loop until the list is clean and you would be comfortable if the user opened it right
  now without warning.

## Step 5 — Post the QA report on the issue

A QA run that isn't written down didn't happen. Post a comment on the issue with:

1. **What you actually did to test it** — the scenario list, and the result of each. Concrete, e.g.
   "created a report from the dashboard with 0 / 1 / 40 rows; mobile 390px + desktop 1440px", not
   "tested the feature".
2. **The findings and what you did about them** — every issue you found, and fixed vs. flagged.
3. **Assumptions surfaced**, @-mentioning the owner from `factory/ownership.md`.
4. **Evidence — screenshots at minimum.** Not a full demo video (that's the next step), but the
   feature visibly working: the happy path, the mobile view, and the notable states. For backend/LLM
   work: a rendered prompt excerpt and output samples from the 3–5 runs.
   - Attach them per the project's handoff config — the same channel the demo uses. If the tracker CLI
     can't attach images directly (`gh issue comment` cannot), commit them into the worktree's
     demo/QA output dir on the task branch and link them, and say in the comment where they live.
5. The **table + verdict** below.

## Output

| Check | Status | Note |
|-------|--------|------|
| Functionality | ✅/⚠️/❌ | one-line TLDR |
| Intent (does what the issue asked) | ✅/⚠️/❌ | one-line TLDR |
| Hidden assumptions / shortcuts | ✅/⚠️/❌ | one-line TLDR |
| UI/UX paper-cuts — desktop | ✅/⚠️/❌ | one-line TLDR |
| UI/UX paper-cuts — mobile | ✅/⚠️/❌ | one-line TLDR |
| Design polish (professional bar) | ✅/⚠️/❌ | one-line TLDR |
| Pipeline/output quality (3–5 examples) | ✅/⚠️/❌ | one-line TLDR, or `n/a` |
| Evidence captured (screenshots/output) | ✅/⚠️/❌ | one-line TLDR |
| *(one row per `factory/qa.md` bullet)* | ✅/⚠️/❌ | what you looked at, or `n/a — reason` |

Rows that genuinely don't apply (e.g. the UI rows on a pure-backend change, the pipeline row on a UI
change) are marked `n/a` — but "n/a" for a UI row on anything a user can see is not acceptable.

Then, on its own line, exactly one of:
```
VERDICT: PASS
VERDICT: FAIL
```
FAIL if anything is ❌. Do not "PASS with known issues" — either fix it, or it's a FAIL. Below the
table, be ruthlessly concise:
- ❌ **Fix:** what's broken, where, what it should be.
- ⚠️ **Heads up:** what looks off, why it's not blocking.

## Step 6 — External second opinion (blocking)

The code review before this step judged the **code**. It had no way to judge whether the *result* is any
good, because it never ran anything. Now that you have the QA artifacts, get a fresh set of eyes on the
whole picture.

Hand **everything you produced** — the issue, the PR, the QA report, the scenario list, the screenshots
— to an external reviewer:

- If `factory/code-review.md` configures an **external tool** (with `Enabled: yes`), shell out to it now
  using that file's documented invocation, but with a **QA-specific prompt** rather than the code-review
  prompt. Point it at **this file's absolute path** (external CLI agents can't resolve Claude Code skill
  names) and tell it to start at Step 6:

  > Read `<abs path>/factory-qa/SKILL.md` and follow its Step 6 as an external QA reviewer. We just
  > finished a QA pass on PR `<PR_URL>` for issue `<ISSUE_URL>`. Read the issue and every comment to get
  > fully caught up on the context and intent, read the PR diff, and read the QA report comment and its
  > screenshots/artifacts. Then tell us: **what did we miss?** What did the QA fail to test that a real
  > user would hit? What paper-cuts, UI problems, or polish issues are still there? Did we make
  > assumptions or take shortcuts that don't hold up against what the issue actually asked for? Be
  > specific and blunt. End with `VERDICT: PASS` or `VERDICT: FAIL` on its own line.

- If no external tool is configured (or `code-review.md` is missing/disabled), do this pass
  **in-context** instead — but do it *adversarially*: re-read the issue cold, assume the QA above was
  too generous, and try to find what it let slide.

### If you're the external agent reading this file directly

You were handed nothing but this file's path, a PR, and an issue. This is a plain markdown instruction
file, not a Claude Code skill invocation — just follow it as your task:

1. Work inside the repo the PR belongs to (a read-only checkout is enough; you don't need to build).
2. Read `factory/` at the repo root — `factory/qa.md` for the project's own QA checklist,
   `factory/code-review.md` for its code checklist and reviewer config, `factory/intake.md` for the
   tracker CLI.
3. Read the **issue and every comment** in full, the **full PR diff**, and the **QA report comment** plus
   any linked screenshots/artifacts.
4. Answer the questions in the prompt above — focus on **what the QA missed**, not on re-reviewing the
   code line by line (a code review already ran). You are the check on *quality, completeness, intent,
   and polish*.
5. Post your findings as a **single comment on the PR**, and make it your final printed output so a
   headless caller can grep it. End with `VERDICT: PASS` or `VERDICT: FAIL` on its own line.

### Handling the result

Read the reviewer's `VERDICT:` line.
- **`FAIL`**, or any finding you agree with → go back to **Step 4**, fix it, re-push, re-walk the
  scenarios, update the QA report, and re-run this second opinion. Do not proceed on a FAIL.
- **`PASS`** → QA is complete. The demo may now be recorded.

Loop until `PASS`.

---

## In a `factory-implement` run

This is a **blocking gate**, not advisory. It runs **after** the code-review gate and **before** the
demo, and it is **always on** — there is no per-project config that turns QA off, and it does not get
scaled down for E3 tasks (E3 means "don't ask the user questions", not "don't check your work").

The demo that follows should be **built from the scenarios you just walked** — you already know exactly
what to show and what the interesting states are. A thorough, longer demo is preferred over a short one
that skips the real behavior.

`VERDICT: FAIL` sends the run back into the loop; it never proceeds to demo or handoff on a FAIL.
