---
name: factory-implement
description: Build step of the factory pipeline — execute an ALREADY-FORMED, re-researched plan by setting a granular todo list and building it one item at a time, verifying as you go. REQUIRES an existing plan; it is not an entry point for a raw task. If you were handed a bare issue/URL/description with no plan, do NOT use this — use factory-execute. Use when the user says "factory implement", "implement the plan", or "build it" AND a plan already exists.
---

# Factory — Implement

## STOP — precondition check (do this BEFORE anything else)

This is the **build** step. It assumes a formed, re-researched plan **already exists**. It is **not** the way to start a task from scratch.

1. Look for the plan document for this task in `./tasks/` (the file `factory-plan` writes), or a formed plan already present in the conversation.
2. **If there is no plan** — e.g. you were just handed a raw issue, a URL, or a one-line description and `./tasks/` has nothing for it — **STOP immediately. Do not research, do not ask clarifying questions, do not write a single line of code.** Say exactly this and stop:
   > This is the build step and it needs a formed, re-researched plan — there isn't one here. To do this task properly, run **`/factory-execute <issue>`** (the full pipeline: plan → re-research → implement → recheck → demo → handoff). If you only want a plan, run **`/factory-plan`** first.
3. Only when a real plan document exists may you continue below.

**Asking a few clarifying questions is NOT a plan.** Four answered questions do not substitute for the plan + re-research phases. If you catch yourself about to start writing files off the back of a Q&A instead of a written, re-researched plan, you are in the wrong skill — stop and hand off to `/factory-execute`.

## Build (only once the precondition passes)

The plan is formed. Now build it.

First gauge how complex the plan is. If it spans multiple services or is genuinely complex, form an **agent team** (not just parallel agents) to execute it. Otherwise, set a todo list and complete each item one at a time.

## Rules
- **Do NOT stop at any time until the plan is 100% complete.** You have as much time as you need — keep going.
- Always start by setting a **granular** todo list.
- Work slowly; don't rush.
- **Don't blindly follow the plan — verify always.** Plans are sometimes lazy or wrong; when reality disagrees with the plan, fix the approach.
- Do not leave dead code unless explicitly told to.
- No comments on *what*; only *why*, as a comment block. Imports at the top, never inline.
- Never commit secrets or hard-coded sensitive values.
