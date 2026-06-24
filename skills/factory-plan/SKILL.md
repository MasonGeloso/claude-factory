---
name: factory-plan
description: Form a well-researched implementation plan for a single task and write it to a markdown file in ./tasks. Heavily researches the codebase for patterns, norms, opinionated logic, and existing utils before proposing anything. The planning step of the factory pipeline; also usable standalone. Use when the user says "factory plan", "plan this task", or "make a plan for <task>".
---

# Factory — Plan

You are given a task. Form a **well-researched** plan for it. Read the docs, check for utils/services/stores that already exist, do web research if needed.

## Diagnose first — before any code, before any plan

Reading code is the *last* research step, not the first. Treat the reported problem (or the requirement) as a **hypothesis to confirm**, not a fact. In order:

1. **Read the docs.** Start with the project's docs — how the system works and, specifically, **how it's meant to be diagnosed/observed** (runbooks, `docs/`, READMEs, ENGINEERING guides). Learn the intended way to inspect this thing before guessing.
2. **Read the logs / observability.** Pull the actual logs, errors, metrics, traces relevant to the task. Let real signal point you at the area, instead of inferring it from source.
3. **Reproduce it locally.** Stand up the stack and **set up an experiment** to make the reported behavior actually happen (or to observe the current behavior you're about to change). 
4. **Validate the claim.** Confirm what the user/issue says is true *before* trusting it. If repro contradicts the report, say so — don't code against a wrong premise.
5. **Only then read the code** — now you know which code, and why.

Write what you find (logs, repro steps, what you confirmed/disproved) into the plan doc. Jumping straight to editing code without this is wrong, even when it looks faster.

## Steps
- Heavily research the codebase **once diagnosis points you there**. Look for patterns, norms, opinionated logic, existing interfaces.
- Pull as much context as relates to completing the task — including the full tracker issue and its comments if this is a factory run.
- Write all findings, context, and the plan to a markdown file in the `./tasks` directory (inside the worktree, for factory runs).
- Re-read your plan with a critical lens.
- Re-research the codebase in **new** areas you hadn't looked, and start finding holes or issues with the plan.
- Revise the plan with your findings.

## Rules
- Do not introduce anti-patterns.
- Do not duplicate logic/utils/services/stores that already exist — find and reuse them.
- Do not add comments on *what* is happening. If something needs explaining, add a comment **block** on *why*.
- Plan to put imports at the top of the file, never inline.
- Do not run things to "test" at this stage — this is planning. (Execution and verification happen in later steps.)
