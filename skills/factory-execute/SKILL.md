---
name: factory-execute
description: 'The /execute (build) step of the factory pipeline — take an ALREADY-FORMED, heavily-researched plan and build it: set a granular todo list and implement it one item at a time, verifying as you go, never stopping until 100% done. REQUIRES an existing plan; it is NOT the entry point for a raw task. The factory-implement driver runs plan + re-research first and then invokes this; recheck, stand-up, verify, demo, and handoff happen back in the driver after this returns. Use when the user says "factory execute", "execute the plan", "build the plan", or "build it" AND a researched plan already exists.'
---

# Factory — Execute (build the researched plan)

This is the **build** step of the factory pipeline. You've already planned and heavily re-researched;
now it's time to execute that plan into working code. It is **not** the entry point for a task — the
[`factory-implement`](../factory-implement/SKILL.md) driver owns the full lifecycle (read comments →
plan → re-research → **execute** → recheck → stand up + verify live → demo → handoff) and invokes this
step in the middle.

## STOP — precondition check (do this BEFORE anything else)

This step assumes a formed, re-researched plan **already exists**.

1. Look for the plan document for this task in `./tasks/` (the file `factory-plan` writes), or a formed plan already present in the conversation.
2. **If there is no plan** — e.g. you were handed a raw issue, a URL, or a one-line description and `./tasks/` has nothing for it — **do not build, and do not write a single line of code yet.** The task needs the full pipeline. **Invoke the `factory-implement` driver yourself, right now, via the Skill tool, passing this same task** — it reads the comments, plans, re-researches, and then calls back into this step with a real plan. Do **not** just print a message telling the user to go run it themselves.
   - This will not loop: inside `factory-implement` the plan + re-research phases run *before* this build step, so by the time execution is reached the precondition is satisfied.
   - Only if you genuinely cannot invoke `factory-implement` (skill missing) should you fall back to telling the user: *"no plan exists — run `/factory-implement <issue>`."*
3. Only when a real plan document exists may you continue and build.

**Asking a few clarifying questions is NOT a plan.** Four answered questions do not substitute for the plan + re-research phases. If you catch yourself about to start writing files off the back of a Q&A instead of a written, re-researched plan, you are in the wrong skill — escalate to `factory-implement` as above.

## Build (only once the precondition passes)

The plan is formed. Now build it.

First gauge how complex the plan is. If it spans multiple services or is genuinely complex, form an **agent team** (not just parallel agents) to execute it. Otherwise, set a todo list and complete each item one at a time.

### Verifying as you build

You build here; the **driver runs the live stand-up, demo, and handoff after this returns** (and it
provisions infra per the repo's `factory/` docs — `factory/dev-manager.md` if present, else
`factory/deployment.md`). If a build item genuinely needs a running stack to verify *as you go*, bring
it up the way those `factory/` docs say — never hand-roll provisioning or hardcode it here, and
**never delete a data volume**; prefer pausing a stack over destroying it. Otherwise, focus on getting
the code correct and leave the end-to-end live verification to the driver.

## Rules
- **Do NOT stop at any time until the plan is 100% complete.** You have as much time as you need — keep going.
- Always start by setting a **granular** todo list.
- Work slowly; don't rush.
- **Don't blindly follow the plan — verify always.** Plans are sometimes lazy or wrong; when reality disagrees with the plan, fix the approach.
- Do not leave dead code unless explicitly told to.
- No comments on *what*; only *why*, as a comment block. Imports at the top, never inline.
- Never commit secrets or hard-coded sensitive values.
- **Codebase-agnostic:** any infra you touch follows the working repo's `factory/` docs — never hardcode project specifics here.
