---
name: factory-onboard
description: One-stop onboarding for a repo's `factory/` directory. Scans which per-project context files exist, and interviews the user to fill in ONLY the missing ones — so the same skill sets up a brand-new repo end to end AND back-fills a single new context file when a later skill/agent needs one. Use when the user runs /factory-onboard, sets up Factory in a new repo/org, or when any factory skill reports a missing `factory/` file.
---

# Factory — Onboarding (holistic, partial-aware)

*Run this once per repo to set everything up — and again any time a new Factory capability needs a context file you don't have yet.*

Every Factory skill and agent reads its rules from per-project files in a `factory/` directory at the repo root. Historically each skill onboarded its own file. **This skill unifies that**: it knows the full set of context files ("modules"), checks which already exist, and interviews you for **only the ones that are missing** (or, with an explicit re-review, all of them). Add a new module to the registry below over time and a re-run cleanly back-fills it.

The ideal flow in a new org/service:

```
factory install            # CLI: copy skills + link the CLI
/factory-onboard           # this skill: rapid-fire setup of factory/
factory agents install …   # optional: schedule agents (they'll find their config ready)
```

---

## The module registry

Each row is one context file. A module is **required-by** one or more skills/agents; a repo only needs the modules for the capabilities it actually uses, but onboarding offers all of them and marks which are needed by what.

| Module (`factory/…`) | Captures | Needed by | Template / question source |
|---|---|---|---|
| `intake.md` | tracker, its CLI, classification mapping, handoff/status rules | intake, implement, ai-pm, schedule-sync, sync-recap | `factory-intake/templates/intake.md` + `factory-intake/onboarding.md` |
| `ownership.md` | team members, areas of ownership, tracker handles | intake, ai-pm, schedule-sync, sync-recap | `factory-intake/templates/ownership.md` |
| `codebases.md` | the repo(s) this service spans and where they live | implement | `factory-implement/templates/codebases.md` + `factory-implement/onboarding.md` |
| `deployment.md` | worktree base, how to run/demo the stack, demo mode | implement | `factory-implement/templates/deployment.md` |
| `communication.md` | comms medium, auth, channels, reply policy, scheduled-post destinations | ai-pm, daily-digest, sync-recap, weekly-report | `factory-communication-setup/templates/communication.md` + that skill |
| `priority.md` | current priorities (today / week / month) + last-updated | daily-digest, schedule-sync, sync-recap | [templates/priority.md](templates/priority.md) |
| `meetings.md` | sync cadence, who attends, agenda format, decision style | schedule-sync, sync-recap | [templates/meetings.md](templates/meetings.md) |

> Keep this table as the single source of truth. When a new skill needs a new context file, add a row here and add its interview + template; a re-run of `/factory-onboard` will detect and offer it automatically.

---

## Procedure

### 1. Locate / create `factory/`
Find the repo root (`git rev-parse --show-toplevel`). If there's no `factory/`, create it (and a `factory/.gitignore` with `.state/` so agent watermarks don't get committed). Also create the run-log dirs modules expect: `intake/` (intake runs) and `syncs/` (sync agendas/recaps).

### 2. Scan and report a status matrix
For each module in the registry, check whether `factory/<file>` exists. Present a compact matrix so the user sees the whole picture at a glance:

```
factory/ status
  ✓ intake.md          present
  ✓ ownership.md       present
  ✗ communication.md   missing   → needed by: ai-pm, daily-digest, sync-recap
  ✗ priority.md        missing   → needed by: daily-digest, schedule-sync, sync-recap
  … 
```

Then decide scope:
- **Default:** onboard only the **missing** modules.
- **`--all` / user asks to review everything:** walk every module, confirming or updating existing files too.
- Let the user **skip** modules for capabilities they don't use (e.g. no `codebases.md`/`deployment.md` if they'll never run `/factory-implement` here). Note skipped ones; a later re-run re-offers them.

### 3. Interview — only for the in-scope modules
Go module by module. For each, ask its questions in small batches (use the AskUserQuestion tool where it fits), pre-filling from repo recon first. **Do not re-ask what a present file already answers.**

- For `intake.md`, `ownership.md`, `codebases.md`, `deployment.md`, `communication.md`: use the detailed question sets in the referenced onboarding docs / templates (don't duplicate them here — read and follow them).
- For `priority.md` and `meetings.md`, use the inline question sets below.

**`priority.md` questions**
- What are the **current priorities**, grouped by horizon — **today**, **this week**, **this month/now** (map to the tracker's T-levels where it helps)? Link to real issues/epics where they exist.
- Who set them / as of when? (Stamp a `last_updated` date — used to flag staleness later.)
- Any explicit **non-priorities** / "not now" items worth recording so they stop resurfacing.

**`meetings.md` questions**
- Do you hold **recurring syncs**? Which ones, how often, and who usually attends? (Tie attendees to `ownership.md`.)
- What's the **goal** of a sync (alignment? decisions? status?) and how long — so the agenda can be built to fit the time.
- Preferred **agenda format** and where the agenda/recap should live (a doc, a channel post, issue comments — often ties to `communication.md`).
- How are **decisions** captured after a sync (issue comments, a decisions log, updating `priority.md`)?

### 4. Recon before writing
Use the project's real tools to pre-fill and verify — list the tracker's projects/labels, read `docker-compose*/Makefile/package.json`, list the comms channels the bot can see, etc. Fold findings into the files so they match existing conventions. **Never** write a secret into any file — capture the *env-var name*, not the value.

### 5. Write, confirm, hand back
Write each in-scope file from its template, filled concretely. Show the user the resulting matrix (now all ✓ for in-scope modules) and the files, confirm they match reality. If this run was triggered by another skill/agent needing a specific file, hand control back to it once that file exists.

---

## Relationship to the older per-skill onboarding
`factory-intake`, `factory-implement`, and `factory-communication-setup` still contain their own detailed question sets (this skill reuses them). Their Step-0 "missing config" branches should now **route here** — run `/factory-onboard` — instead of each doing a partial, siloed setup. This skill is the front door; those files are the reference material it draws on.
