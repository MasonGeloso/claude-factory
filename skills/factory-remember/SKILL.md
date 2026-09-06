---
name: factory-remember
description: Turn a correction that just happened into a durable, concise checklist rule in the right Factory gate — plan review, code review, or QA — so the same class of defect gets caught before a human has to point at it again. Generalizes the incident into a rule, picks the earliest gate whose evidence can actually decide it, dedupes against what is already there, and never mentions the originating case. Use when the user says "factory remember", "remember this", "add this to the review", "make sure this doesn't happen again", or right after fixing something the user had to catch for you.
user-invocable: true
---

# Factory — Remember

*Something just got caught by a human that a gate should have caught. Convert it into a rule and put
the rule where it will fire.*

The incident is the **trigger**. The rule is the **deliverable**. Nobody will ever read the incident
again — write as if the reader has never heard of it, because they haven't.

---

## Step 1 — Find the rule, not the anecdote

Answer these three, in order, before writing anything:

1. **Which gate could have caught this — using only the evidence that gate has?**
   A plan reviewer sees a plan. A code reviewer sees a diff. QA sees the running thing. A rule filed
   against a gate that cannot see the evidence is dead weight that never fires.
2. **What is the checkable rule?** State it so a reviewer can answer PASS / WARN / FAIL on it without
   re-deriving your reasoning. If you cannot phrase it as something to look for, you have a
   preference, not a rule — stop and say so.
3. **When should it obviously NOT apply?** Every real rule has a legitimate exception. Naming it is
   what stops the gate from FAILing correct work and getting ignored.

Generalize one level, not three. The rule should cover the class the incident belongs to — not that
one file, and not "write good code".

## Step 2 — Pick the gate

| Gate | File | Owns | Typical rules |
|---|---|---|---|
| Plan review | `factory/plan-review.md` | decidable from a **written plan**, before code exists | architecture, which store/queue/chokepoint, job & pipeline shape, scope coverage, cost/throughput approach, "does this belong in an existing X" |
| Code review | `factory/code-review.md` | decidable by **reading the diff** | conventions, reimplemented chokepoints, missing telemetry/cost/trigger/test/doc calls, unjustified constants, contract shape |
| QA | `factory/qa.md` | only visible on the **running thing** | layout, alignment, spacing, motion, empty/loading/error states, mobile, copy, real prompt + real output quality |

**Is it about this project, or about every project?** The table above is the project's own
checklist. If the rule would hold in any repo — a way of reviewing, not a fact about this codebase —
it belongs in the **gate skill itself** (`factory-code-review/SKILL.md`, `factory-plan-review/SKILL.md`,
`factory-qa/SKILL.md` in the Factory repo), as a sharpening of one of its generic categories. Check
there first: the rule may already be covered generically, in which case the project file needs nothing.

Rules of thumb:
- **Earliest gate that can decide it wins.** A wrong data store is cheapest to catch in the plan.
- **One gate**, unless the rule is genuinely checkable at two different fidelities (plan: "does the
  plan commit to it"; code: "does the diff do it"). Never copy the same bullet into all three.
- If it belongs in none of them — it is a fact about the system, not a check — it belongs in the
  project's own docs (`docs/`, `CLAUDE.md`), not here. Say so and put it there instead.

## Step 3 — Write it

Format: a **bolded imperative title**, then **1–4 lines**. Nothing longer.

```
- **<Imperative title.>** <What to look for, in one or two sentences.> <The exception, inline, if
  there is one.>
```

Hard constraints:

- **Never reference the originating incident.** No issue numbers, no "as we saw when…", no story, no
  before/after tale. A reviewer reading "like the header misalignment in #612" has to go read #612 to
  use the rule, and won't.
- **Name real symbols, and verify they exist first.** Files, functions, env vars, config constants —
  `grep` them before you write them down. A rule pointing at a symbol that doesn't exist teaches the
  reviewer to distrust the whole list.
- **One check per bullet.** If it has an "and also", it is two bullets — or, more often, one bullet
  and one thing you wanted to say.
- **No paragraphs, no rationale essays.** Rationale earns its place only when the rule looks wrong
  without it, and then it is one clause, not a paragraph.
- **Write the check, not the fix.** "Every new cache family names its invalidating writer" is a
  check. "Be careful with caches" is not.

## Step 4 — Dedupe and budget

Before adding anything:

- **`grep` the target file.** If a bullet already covers this class, **sharpen it in place** — that
  is the better outcome, and it keeps the list short. Two near-twin bullets are worse than one
  imprecise one.
- **Budget the file.** A gate checklist past roughly 25 bullets stops being read item-by-item and
  starts being skimmed, which is the same as being off. If adding pushes past that, **merge two
  existing bullets first**. Signal, not coverage.
- Check the sibling gates too — the same rule already living in code review means this one only needs
  to exist in QA if it is checking something different there.

## Step 5 — Mirror into the project's own standard (only if it belongs there)

If the project keeps its own engineering/design standard (`docs/ENGINEERING.md`, `CLAUDE.md`, a
design doc), and the rule is something an implementer needs **while building** rather than only while
reviewing, add the same one-line check to that standard's checklist. Same wording, same brevity —
do not write a second, longer version of it.

## Step 6 — Show and confirm

Print the diff of what you added or sharpened, per file, and which gate you chose and why in one
line. Do not commit unless the user asks.

---

## What not to remember

- **One-off facts** ("the token is 43 chars") — that is project memory or a doc, not a gate rule.
- **Anything already covered** by a bullet in the target file or by the gate's generic categories
  (correctness, security, duplication, conventions, tests, docs).
- **Restatements of the whole standard.** "Follow `docs/ENGINEERING.md`" is not a rule; the specific
  thing that got missed is.
- **Preferences with no observable check.** If two reasonable reviewers would disagree on whether a
  given diff satisfies it, it will fire randomly. Sharpen it or drop it.
