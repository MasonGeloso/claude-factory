---
name: factory-intake
description: Intake and groom a backlog from an unstructured brain-dump or meeting transcript into prioritized, complexity-classified issues in the project's tracker (GitHub / GitLab / Jira / etc.). Reads per-project rules from a `factory/` directory at the repo root, and onboards that directory if it is missing. Use when the user runs /factory-intake, drops a transcript to triage, or says "factory intake", "intake this", "groom the backlog", "turn this dump into issues".
---

# Factory — Backlog Intake

*Talk through everything you have to do. Get back a groomed, prioritized, classified backlog in your tracker.*

The user periodically does a long unstructured brain-dump — a solo voice transcript, or a team sync where several people talk — covering everything from tiny paper-cuts to giant future initiatives. This skill turns that dump into well-formed issues in whatever tracker the project uses, following rules the project itself declares.

**Every project is different**, so the rules are not hard-coded here. They live in a `factory/` directory at the root of each repo. This skill reads those rules and follows them. If that directory does not exist, the skill cannot guess how the project works, so it **stops and onboards** instead.

---

## Step 0 — Locate the `factory/` directory (always do this first)

Look for a `factory/` directory at the repository root. Check `./factory` and the git top-level (`git rev-parse --show-toplevel`). Expected layout once onboarded:

```
factory/
  intake.md        # how THIS project does intake: sources, tracker, CLI, classification mapping, rules
  ownership.md     # team members, areas of ownership, tracker handles
  intake/          # one timestamped markdown file per intake run (the run log + parsed tasks)
```

Then branch:

- **`factory/` is missing** → do **not** attempt intake. Tell the user plainly:
  > You don't have a `factory/` directory in this repo, so I don't know how this project tracks work. I'm not going to guess. Let's set it up together first.

  Then run **`/factory-onboard`** — the single, partial-aware onboarding skill that sets up the whole `factory/` directory (it uses this skill's [onboarding.md](onboarding.md) as its reference for the `intake.md`/`ownership.md` question sets). If `factory-onboard` isn't available, fall back to running Onboarding from [onboarding.md](onboarding.md) directly. Do this even if the user pasted a transcript; hold the transcript and offer to run intake on it once onboarding completes.

- **`factory/` exists** → read `factory/intake.md` and `factory/ownership.md` in full, then run **Intake** below.

> Today, onboarding only sets up `ownership.md` and `intake.md` (plus the `intake/` run directory). Other `factory/` sections may exist or be added later; this skill only depends on those two files.

---

## Intake procedure

Run this only when `factory/` exists and you have read `intake.md` and `ownership.md`.

### 1. Get the input
The user normally pastes a large transcript right after `/factory-intake`. If nothing was provided, ask for the dump (transcript, meeting notes, or pasted text). Do not invent items.

### 2. Detect the source type
Use the **Intake sources** section of `factory/intake.md`. The default source is a **solo voice transcript** of the user talking. Other sources are project-specific — e.g. a **weekly team sync** (indicators: multiple distinct speakers, meeting/back-and-forth format rather than one continuous monologue). For a team sync, your job is to **cipher out the action items** from the discussion, not transcribe opinions. Pick the matching source and follow its handling notes.

### 3. Open a run file
Create `factory/intake/YYYY-MM-DD-NN.md` (NN = a counter starting at `01`, incremented if there is already a run today). This file is both the working scratchpad and the permanent record of the run. Seed it with: date, detected source type, and a raw item list.

### 4. First pass — parse into a stub list
Extract **every** distinct item from the dump — granular paper-cuts through giant initiatives. These are raw voice transcripts: **ignore disfluencies, filler, tangents, and non-actionable chatter** ("hold on, feeding my dog") — pull out only real work items. For each, write one stub line and a first-guess classification using [classification.md](classification.md) (or the project's opted-out scheme declared in `intake.md`). Do **not** plan the work yet. Just capture and roughly classify.

### 5. Set a todo list
Create one todo per parsed item so the run is trackable and nothing is dropped.

### 6. Research pass — lightweight context, not planning
For each item, poke around the codebase and the relevant services just enough to:
- add a few bullet points of caveats / context / unknowns under the item in the run file, and
- **reclassify** if the research changes your read of priority or complexity.

You are gauging *roughly how big and how hands-on* this is — **not** writing a spec or a plan. Keep it shallow and fast.

### 7. Per-item processing — run these three checks for every item
Work the todo list. For each item, in order:

1. **Duplicate check.** Search the tracker (via its CLI) for an existing issue covering this.
   - **Obvious / straight-up duplicate** → do not create a second one; note it in the run file and skip.
   - **Very similar but not identical** → create the issue, but **flag it**. Collect these and surface them to the user at the very end: "I created X, but there's an existing issue Y that's very similar — what do you want to do?"
2. **Determine the type.** Map the item's classification (Tn / En, or the project's scheme) to the tracker's actual issue type per `intake.md` — e.g. epic vs. issue vs. spike vs. task, plus labels / priority / custom fields. Big, enormous, unresearched items may become **spikes** if the project says so. Honor the project's opinionated rules; ask during onboarding what constitutes each type so this is already written down.
3. **Create the task.** Concise, pointy title — obvious at a glance, not a paragraph. Description leads with a short **TLDR**, then expands a little (context, acceptance hints, owner if known from `ownership.md`). Capture the right context for this tracker.

### 8. Hard rules (non-negotiable)
- **Never, ever** put secrets, tokens, credentials, or hard-coded values of any kind (API keys, passwords, connection strings, URLs-with-creds, internal hostnames/IPs) into an issue title, body, or comment. Describe them abstractly instead.
- Titles stay short and specific; put the elaboration in the description.
- Don't over-plan — the issue captures *what* and *why*, not a full implementation spec (unless the project's rules say otherwise).
- Assign owners only from `ownership.md`; never guess a person.

### 9. Submit and report back
Create all the issues through the project's CLI (`gh`, `glab`, `jira`, Zapier webhook, etc. — whatever `intake.md` declares). Then:
- Update the run file with each created issue's ID / URL and final classification.
- Write a short summary at the top of the run file (counts per Tn/En, anything skipped as a dupe).
- Present the **flagged near-duplicates** to the user for a decision.

---

## Classification framework

See [classification.md](classification.md) for the full **T1/T2/T3 × E1/E2/E3** system (priority × complexity-and-autonomy). A project may opt out of it entirely in favor of a simpler scheme (e.g. a flat priority field) — if so, `intake.md` says so and you follow that instead.

## Worked example
A project using **GitHub Projects** via the **`gh` CLI**. Its `factory/intake.md` declares the project board, the labels that encode T/E, what counts as an epic vs. issue, and that the default source is a solo transcript plus a "weekly team sync" source. An intake run there: detect source → open run file → parse + classify → research → for each item `gh issue list`/search for dupes, pick type+labels, `gh issue create` (and add to the project board) → report links + near-dupe flags.
