---
name: factory-reresearch
description: Re-research an existing plan to find holes — missing requirements, anti-patterns, utils being re-created that already exist, functions used incorrectly. Updates the existing plan document in place rather than creating a new one. The hole-finding step of the factory pipeline; also usable standalone. Use when the user says "factory reresearch", "re-research the plan", or "find holes in the plan".
---

# Factory — Re-research

Re-research your plan and find anything that doesn't make sense: missing requirements, anti-patterns, new utils that already exist in the codebase, functions used incorrectly, wrong assumptions, edge cases the plan skips.

The goal is to attack **your own plan** and fix it before any code is written.

- Do **not** create a new document — update the current plan document in place and state what you changed.
- Look in areas of the codebase you haven't examined yet, not the same files again.

## Iteration depth (factory runs)
The number of rounds depends on the task's E-level:
- **E3** — one round is enough.
- **E2** — about two rounds.
- **E1** — a minimum of three to four rounds, more if holes keep appearing. Stop only when a fresh pass stops finding real issues.
