# Factory — a backlog intake & execution system for Claude Code

Factory is a suite of [Claude Code](https://claude.com/claude-code) skills that turn an unstructured brain-dump (or a meeting transcript) into a groomed, prioritized backlog in your real tracker — and then pick tasks back up and drive them to *ready-for-review*, autonomously.

It's two halves:

- **Intake** — talk through everything you have to do; Factory parses it into well-formed issues, classifies each, dedupes against what already exists, and files them in your tracker (GitHub / GitLab / Jira / …).
- **Execute** — point Factory at one issue; it sets up an isolated git worktree and runs a disciplined pipeline (diagnose → plan → re-research → implement → recheck → demo → handoff), keeping the issue updated the whole way.

Every project is different, so the rules aren't hard-coded. Each repo gets a `factory/` directory describing how *that* project tracks work, runs its stack, and hands off. Factory reads it; if it's missing, it onboards it with you first.

## Install

```bash
git clone https://github.com/MasonGeloso/claude-factory.git
cd claude-factory
./install.sh
```

This copies the eight skills into `~/.claude/skills/` (any existing same-named skill is backed up to `<name>.bak-<timestamp>`). Set `CLAUDE_SKILLS_DIR` to install elsewhere.

One-liner:

```bash
git clone https://github.com/MasonGeloso/claude-factory.git /tmp/claude-factory && /tmp/claude-factory/install.sh
```

## Quick start

In any repo:

1. `/factory-intake` — first run onboards a `factory/` directory (tracker, CLI, classification, ownership, handoff). After that, paste a transcript and it files the issues.
2. `/goal /factory-execute <issue>` — first run onboards `codebases.md` + `deployment.md` (repos, worktrees, how to run the stack, demo mode). After that, it builds the task end to end.

## The skills

| Skill | Role |
|-------|------|
| `factory-intake` | Brain-dump / transcript → classified, deduped issues in the tracker |
| `factory-execute` | Orchestrator: pick up one issue, run the pipeline, hand off |
| `factory-plan` | Diagnose (docs → logs → reproduce → validate) then write a plan |
| `factory-reresearch` | Attack the plan, find holes, fix them in place |
| `factory-implement` | Granular todo list, build, verify — don't stop until done |
| `factory-recheck` | Fresh-eyes review → PASS/FAIL verdict |
| `factory-demo-video` | Record a browser screencast of the change (web UI) |
| `factory-demo-terminal` | Record a terminal screencast (CLI / stdout) |

`factory-execute` invokes the others by name.

## The classification system

Each item gets a **T** (priority) and an **E** (complexity / autonomy) — independent axes. **T does not imply size.**

- **T1 / T2 / T3** — must-ship-now / imminent-and-important / amorphous-or-later (framed against a product launch).
- **E1 / E2 / E3** — hands-on & spec-heavy / semi-autonomous / fully hands-off & likely auto-mergeable.

A project can opt out and use a simpler scheme; its `factory/intake.md` declares the mapping onto real labels/fields. `factory-execute` uses the E-level to set how autonomous the run is (E3 never asks; E1 is expected to ask design questions) and how many re-research rounds it does.

## Requirements

- Claude Code.
- Your tracker's CLI (`gh`, `glab`, `jira`, …) — whatever your `factory/intake.md` declares.
- For demos: `factory-demo-video` drives a browser via the `playwright-cli` skill; `factory-demo-terminal` needs Python `playwright` (`pip install playwright && playwright install chromium`) + `ffmpeg`.

## License

MIT — see [LICENSE](LICENSE).
