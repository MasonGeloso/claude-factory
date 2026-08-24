---
description: Run the Factory CLI (skills status, scheduled agents) from the installed plugin.
argument-hint: "[status | agents list | agents install <agent> <repo> | …]"
allowed-tools: Bash(*/bin/factory:*), Bash(python3:*)
---

Run the Factory CLI that ships with this plugin:

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/bin/factory" $ARGUMENTS
```

If `$ARGUMENTS` is empty, run `python3 "${CLAUDE_PLUGIN_ROOT}/bin/factory" status` instead — the
no-argument form opens a full-screen TUI, which cannot be driven from here.

Then report the output back to the user verbatim-ish (trim noise, keep paths and errors).

Useful subcommands:

- `status` — installed skills and scheduled agents
- `install` — symlink the `factory` CLI onto PATH (`~/.local/bin/factory`) so the user can run it
  directly; in plugin mode it does **not** copy skills, since Claude Code already loads them
- `agents list` — available and installed cron-style agents
- `agents install <agent> <repo> [--interval N]` — schedule an agent for a repo
- `agents update|remove <agent> <repo>`

Agent installs can launch an interactive Claude Code session to onboard missing
`factory/` config — if the user needs that, tell them to run the command in their own terminal:
`factory agents install <agent> <repo>`.
