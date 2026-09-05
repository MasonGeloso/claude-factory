# Factory — a backlog intake & execution system for Claude Code

Factory is a suite of [Claude Code](https://claude.com/claude-code) skills that turn an unstructured brain-dump (or a meeting transcript) into a groomed, prioritized backlog in your real tracker — and then pick tasks back up and drive them to *ready-for-review*, autonomously.

It's two halves:

- **Intake** — talk through everything you have to do; Factory parses it into well-formed issues, classifies each, dedupes against what already exists, and files them in your tracker (GitHub / GitLab / Jira / …).
- **Execute** — point Factory at one issue; it sets up an isolated git worktree and runs a disciplined pipeline (diagnose → plan → re-research → implement → recheck → code review → **QA it like a real user** → demo → handoff), keeping the issue updated the whole way.

Every project is different, so the rules aren't hard-coded. Each repo gets a `factory/` directory describing how *that* project tracks work, runs its stack, communicates, and hands off. One skill — `factory-onboard` — sets that directory up and back-fills it as new capabilities need new context. Factory reads it; if something's missing, it onboards it with you first.

## How it fits together

```mermaid
flowchart TB
    subgraph setup [One-time / incremental]
      CLI["factory CLI\ninstall · update · agents"] --> ONB["/factory-onboard\n→ factory/*.md"]
    end

    ONB -.reads.-> CTX[("factory/ context\nintake · ownership · codebases\ndeployment · communication\npriority · meetings")]

    subgraph backlog [Fill the backlog]
      INTAKE["/factory-intake\nbrain-dump / transcript → issues"]
      RECAP["/factory-sync-recap\nmeeting transcript → issue updates + priorities"]
    end

    subgraph deliver [Take work to done]
      IMPL["/factory-implement (driver)"]
      IMPL --> PLAN["/factory-plan"] --> PR1["/factory-plan-review\n(optional gate)"] --> EXE["/factory-execute"] --> RC["/factory-recheck"] --> REVIEW["/factory-code-review\n(optional PR gate)"] --> QA["/factory-qa\n(required gate)"] --> DEMO["demo-video / demo-terminal"]
      PLAN --> RR["/factory-reresearch"] --> PR1
      QA -.->|FAIL| EXE
    end

    subgraph sync [Alignment loop]
      SCHED["/factory-schedule-sync\nbuild the agenda"] --> MEET([the meeting]) --> RECAP
    end

    subgraph report [Report out]
      WEEKLY["/factory-weekly-report\ntracker → tech-tree board (PNG)"]
    end

    subgraph agents [Scheduled agents cron/launchd]
      AIPM["ai-pm\nchannels → reconcile board"]
      DIGEST["daily-digest\nactivity → daily TLDR"]
    end

    CTX -.-> INTAKE & IMPL & SCHED & RECAP & AIPM & DIGEST & WEEKLY
    INTAKE --> TRACKER[(work tracker)]
    RECAP --> TRACKER
    AIPM --> TRACKER
    TRACKER --> IMPL
    RECAP --> PRI[("priority.md")]
    PRI -.-> DIGEST & SCHED
```

## Install

### As a Claude Code plugin (recommended)

Factory ships as a plugin with its own marketplace, so installing and updating it are two commands inside Claude Code:

```
/plugin marketplace add MasonGeloso/factory
/plugin install factory@factory
```

Or from a terminal:

```bash
claude plugin marketplace add MasonGeloso/factory
claude plugin install factory@factory
```

Claude Code loads the skills straight from the plugin — nothing is copied into `~/.claude/skills`. Update with `/plugin update factory`, remove with `/plugin uninstall factory`.

Skills installed by a plugin are namespaced: `/factory:factory-intake`, `/factory:factory-implement`, and so on. (Typing the bare name still resolves — the namespaced form is what shows up in the skill list.)

The scheduled agents need the **Factory CLI**, which lives inside the plugin. `/factory-cli` runs it for you, or link it onto your PATH once:

```
/factory-cli install       # symlinks ~/.local/bin/factory → the plugin's bin/factory
```

After that, `factory agents install ai-pm /path/to/repo` works from any terminal. In plugin mode `factory install` only does the symlink — it never copies skills, and `factory update` defers to `/plugin update`.

### From a git checkout

```bash
git clone https://github.com/MasonGeloso/factory.git
cd factory
./install.sh
```

This copies the skills into `~/.claude/skills/` (any existing same-named skill is backed up to `<name>.bak-<timestamp>`; unchanged skills are skipped). Set `CLAUDE_SKILLS_DIR` to install elsewhere. Skill names are un-namespaced this way: `/factory-intake`.

Pick one or the other — running both gives every skill a duplicate.

`install.sh` is a thin wrapper around the **Factory CLI** (`bin/factory`, Python 3, zero dependencies). `factory install` also symlinks the CLI itself onto your PATH (`~/.local/bin/factory` by default — override with `FACTORY_BIN_DIR`), so after the first install you can run `factory` from anywhere:

```bash
factory install     # copy the skills into ~/.claude/skills AND link the CLI onto PATH
factory update      # git pull the checkout, then re-install only changed skills
factory status      # what's installed, and what has updates available
factory agents      # install / update / remove cron-style agents
factory             # no args → full-screen TUI (arrow-key nav) for all of the above
```

One-liner:

```bash
git clone https://github.com/MasonGeloso/factory.git /tmp/factory && /tmp/factory/install.sh
```

## Quick start

In any repo:

1. `/factory-intake` — first run onboards a `factory/` directory (tracker, CLI, classification, ownership, handoff). After that, paste a transcript and it files the issues.
2. `/goal /factory-execute <issue>` — first run onboards `codebases.md` + `deployment.md` (repos, worktrees, how to run the stack, demo mode). After that, it builds the task end to end.

## The skills

| Skill | Role |
|-------|------|
| `factory-onboard` | One-stop, partial-aware setup of the repo's `factory/` directory; back-fills missing context files |
| `factory-intake` | Brain-dump / transcript → classified, deduped issues in the tracker |
| `factory-execute` | Orchestrator: pick up one issue, run the pipeline, hand off |
| `factory-plan` | Diagnose (docs → logs → reproduce → validate) then write a plan |
| `factory-reresearch` | Attack the plan, find holes, fix them in place |
| `factory-implement` | Granular todo list, build, verify — don't stop until done |
| `factory-recheck` | Fresh-eyes review → PASS/FAIL verdict |
| `factory-plan-review` | Optional second-opinion review of the *plan*, before any code is written; blocking pre-Execute gate |
| `factory-code-review` | Optional second-opinion review of the opened PR — runnable by an external CLI agent (e.g. Codex) or in-context; blocking gate right after the PR opens |
| `factory-qa` | **Required** gate: actually use the feature on the running stack — real user scenarios, desktop + mobile, paper-cuts and polish, real prompts/output over 3–5 examples — then post a QA report with screenshots and get an external second opinion |
| `factory-demo-video` | Record a browser screencast of the change (web UI) |
| `factory-demo-terminal` | Record a terminal screencast (CLI / stdout) |
| `factory-terminal-demo-video` | Narrated, subtitled video of a **real interactive** CLI/agent session, replayed inside a CSS "OS" window |
| `factory-schedule-sync` | Build a high-leverage sync agenda from the backlog + attendees + priorities |
| `factory-sync-recap` | Meeting transcript → issue updates, decisions, and a refreshed `priority.md` |
| `factory-weekly-report` | Weekly tech-tree board as a shareable image: what shipped, what's in flight, what's blocked behind what |
| `factory-ai-pm` | Scheduled AI Product Manager: read the org's channels, reconcile the tracker |
| `factory-daily-digest` | Scheduled daily TLDR of activity across the org's systems |
| `factory-communication-setup` | Reference question-set for `communication.md` (used by `factory-onboard`) |

`factory-execute` invokes the others by name. `factory-onboard` sets up the `factory/` context all of them read.

## Agents (cron-style)

Beyond the on-demand skills, Factory can install **agents** that run on a schedule — a trivial `claude -p "…" --dangerously-skip-permissions` command wired to your OS scheduler (crontab on Linux, launchd on macOS). The scheduled command is identical on every machine; all the per-org behavior comes from the target repo's `factory/` directory.

Three agents ship today:

- **AI Product Manager** (`ai-pm`) — every few minutes, reads the org's communication channels since it last checked, then reconciles the work tracker against the conversation (opening, closing, assigning, commenting).
- **Daily Activity Digest** (`daily-digest`) — once a day, surveys recent activity across the org's systems (commits, issues, conversation) and posts a concise TLDR of what's being worked on, factoring in `priority.md` and flagging it when it's stale.
- **Weekly Tech-Tree Report** (`weekly-report`) — curates the tracker into a tech-tree investment board (what shipped, what's in flight, what's blocked behind what), renders it to a PNG, and posts the image. The board covers a rolling 7-day window; it posts each morning by default, or once a week with `--interval 10080`.

Where each scheduled post goes is per-org config: the **Scheduled posts** table in `factory/communication.md` names the channel, format, and upload call. No destination means the agent builds its artifact and posts nothing — it never guesses a channel.

Agent definitions live in `factory-agents/` in this repo (one directory per agent: `agent.json` + `prompt.md`). Not `agents/` — Claude Code reads a plugin's `agents/` directory as subagent definitions, and these are cron jobs, not subagents.

```bash
factory agents list                          # available + installed, with update flags
factory agents install ai-pm /path/to/repo   # per-repo; onboards missing context first
factory agents install daily-digest /path/to/repo --interval 1440   # once a day
factory agents update  ai-pm /path/to/repo   # re-render if the agent's prompt/skill changed
factory agents remove  ai-pm /path/to/repo   # unschedule + clean up
```

Intervals accept sub-hour (`--interval 5`), hourly (`--interval 120`), or daily (`--interval 1440`) cadences.

Agents are **per-repo**: the target repo must already have a `factory/` directory (run `/factory-intake` once). If the agent needs config that isn't there yet — the AI PM needs `factory/communication.md` — install launches an interactive Claude Code session running the matching setup skill (`factory-communication-setup`), then schedules the agent once the file exists. Installed agents, their wrappers, logs, and last-read state live under `~/.claude/factory/`.

## The classification system

Each item gets a **T** (priority) and an **E** (complexity / autonomy) — independent axes. **T does not imply size.**

- **T1 / T2 / T3** — must-ship-now / imminent-and-important / amorphous-or-later (framed against a product launch).
- **E1 / E2 / E3** — hands-on & spec-heavy / semi-autonomous / fully hands-off & likely auto-mergeable.

A project can opt out and use a simpler scheme; its `factory/intake.md` declares the mapping onto real labels/fields. `factory-execute` uses the E-level to set how autonomous the run is (E3 never asks; E1 is expected to ask design questions) and how many re-research rounds it does.

## Requirements

- Claude Code.
- Your tracker's CLI (`gh`, `glab`, `jira`, …) — whatever your `factory/intake.md` declares.
- For demos: `factory-demo-video` drives a browser via the `playwright-cli` skill; `factory-demo-terminal` needs Python `playwright` (`pip install playwright && playwright install chromium`) + `ffmpeg`.
- `factory-terminal-demo-video` additionally needs `pexpect` and, if you want narration, a TTS provider; it ships no icon set (licence decision — see its `chrome/README.md`).

## License

MIT — see [LICENSE](LICENSE).
