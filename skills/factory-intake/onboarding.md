# Factory — Onboarding

Run this when a repo has **no `factory/` directory**. Goal: capture how *this* project tracks work, write it down, and scaffold the directory so future `/factory-intake` runs are fully automatic. Today onboarding covers only **`intake.md`** and **`ownership.md`** (plus the `intake/` run directory).

## 1. Stop and set expectations
Tell the user there's no `factory/` here, so intake can't run yet, and you'll build it together now. Keep any pasted transcript aside — offer to run intake on it the moment onboarding finishes.

## 2. Interview the user
Ask in small batches (use the AskUserQuestion tool where it fits). Cover:

**Tracker & interface**
- Which system holds the issues? (GitHub Issues/Projects, GitLab, Jira, Zapier, plain markdown, other.)
- How do you create / update / monitor issues there? Which CLI — `gh`, `glab`, `jira` — and any project/board IDs, repos, or endpoints needed?

**Issue taxonomy**
- What are the issue *types*? What constitutes an **epic** vs. a regular **issue** vs. a **spike** vs. a task?
- What **labels**, priority fields, or custom fields exist and what do they mean?
- Big, enormous, unresearched items — should they become **spikes**, or something else?

**Classification scheme**
- Use the standard **T1/T2/T3 × E1/E2/E3** system (see [classification.md](classification.md)), or opt out for something simpler (e.g. a flat priority)? If opting out, capture the exact scheme and how it maps onto the tracker's fields/labels.

**Intake sources**
- Default is a solo voice transcript of the user. Any other sources — e.g. a **weekly team sync** with multiple speakers? For each, note the *indicators* that identify it and how to handle it (e.g. extract action items only).

**Ownership**
- Team members, their areas of ownership, and their tracker handles/usernames.

**Rules & conventions**
- Context to always capture, title conventions, description format, and anything to **never** include (beyond the universal no-secrets rule).

**Handoff & status** (also used later by `/factory-execute`)
- When a task is finished and demoed, where do updates go and what status means **ready for review**?
- Should a demo be uploaded as a comment on the issue?
- Conventions for posting assumptions (@-mention the owner), decisions, and questions as comments while work is in progress.
- Handoff style: auto-commit-and-push, or finish-in-worktree and wait for the user to push.

## 3. Recon pass — read the live tracker
Before writing the files, actually use the chosen CLI to inspect the real setup, and fold what you learn into `intake.md` so future runs match existing conventions:
- List available projects/boards and existing issues (`gh issue list`, `gh project list`, `glab issue list`, `jira issue list`, …).
- Read the existing labels / issue types / custom fields and a sample of current issues to learn the house style (titles, description shape, how epics/spikes are tagged).
- Note the IDs/paths needed to create and query issues non-interactively.

## 4. Scaffold the directory and write the files
Create:
```
factory/
  intake.md      # from templates/intake.md, filled with the answers + recon findings
  ownership.md   # from templates/ownership.md, filled with the team
  intake/        # run-log directory (add a .gitkeep so it commits empty)
```
Fill `templates/intake.md` and `templates/ownership.md` with everything gathered. Be concrete — embed the actual CLI commands, project IDs, label names, and type-mapping rules so intake is unambiguous later.

## 5. Confirm and (optionally) run intake
Show the user the written `intake.md` and `ownership.md`, confirm it matches how they work, then offer to run intake immediately on the held-aside transcript.
