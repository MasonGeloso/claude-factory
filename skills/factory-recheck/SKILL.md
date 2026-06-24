---
name: factory-recheck
description: Fresh-eyes, read-only re-review of your own just-finished implementation against the original requirements. Produces a PASS/WARN/FAIL table across correctness, bugs, duplication, conventions, docs, and security, plus a YES/NO verdict. The verification step of the factory pipeline; also usable standalone. Use when the user says "factory recheck", "recheck my work", or "review what I just did".
---

# Factory — Recheck

> Precondition: this reviews an implementation that already exists. If nothing has been built yet (you were handed a raw issue with no work done), there's nothing to recheck — say so and point to `/factory-execute <issue>` for the full pipeline. Don't start building here.

You've just finished an implementation. Before it's tested or validated, do a fresh-eyes re-review of your own work. **Do not run anything.** Read the code only. The output is ultimately a yes/no: *will this work as intended and meet every requirement?*

## Ground yourself first
- Re-read any engineering guides in the docs — usually `docs/ENGINEERING.md` (check for other ALL-CAPS guides in `docs/` too). These are the conventions you're held to.
- Recover the **original requirements**, not just the written plan — including the full tracker issue and its comments. If the original request/transcript is still in context, scroll back to it. The plan is not assumed perfect; judge against what was actually asked.

## Run every check below
For each category decide PASS / WARN / FAIL.

1. **Correctness** — Did you implement everything required? Does the expected behavior actually work when you trace it? Anything missing or half-done?
2. **Bugs & edge cases** — Hunt obvious *and* non-obvious bugs. Actively try to break it. What inputs, states, or paths does the new code fail on?
3. **Code smells & duplication** — Did you duplicate something already in the repo? Existing utils/helpers you should have reused? Watch for the lazy pattern: a fresh bespoke function written because finding the reusable one was harder. Flag it.
4. **Conventions & interfaces** — Are you using the codebase's existing interfaces, patterns, and practices? Anything off the rails of the normal codebase?
5. **Documentation** — Did you document what warrants it (e.g. a `CLAUDE.md` reference)? Did this change make any existing docs stale? Could another agent/dev understand *why* this exists?
6. **Security** — Any holes? Admin endpoint that never checks for admin, missing auth, leaked secrets, unvalidated input on a sensitive path.

## Output
End with a single uniform table — one row per category — using ✅ / ⚠️ / ❌:

| Check | Status | Note |
|-------|--------|------|
| Correctness | ✅/⚠️/❌ | one-line TLDR |
| Bugs & edge cases | ✅/⚠️/❌ | one-line TLDR |
| Code smells & duplication | ✅/⚠️/❌ | one-line TLDR |
| Conventions & interfaces | ✅/⚠️/❌ | one-line TLDR |
| Documentation | ✅/⚠️/❌ | one-line TLDR |
| Security | ✅/⚠️/❌ | one-line TLDR |

Then a **Verdict: YES / NO** — will it work as intended and meet all requirements?

If anything is ❌ or ⚠️, list it below the table. Be ruthlessly concise — no word salad.
- ❌ **Fix:** `file:line` — what's wrong, what it should be.
- ⚠️ **Heads up:** `file:line` — what looks off, why it's not critical.

If everything passes, say so in one line and stop.

## In a factory run
This is a loop, not a gate. If the verdict is **NO** (or anything is ❌), go back and fix it — and if the problem is structural, go all the way back to `factory-plan` / `factory-reresearch`. Don't accept a flawed result just to wrap up.
