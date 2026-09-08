---
name: factory-demo-terminal
description: 'Factory-suite copy of the demo-terminal skill. Record polished terminal-style screencast demos by capturing real CLI output and replaying it in an animated HTML "terminal" page via Playwright. Outputs a .webm plus a numbered PNG still of every scene and an artifacts.md manifest, so the work can be reviewed without watching a video. Invoked by the factory-implement driver for `terminal` demo mode; also usable standalone. Use when the user wants to demo a CLI tool, script, REPL session, or other terminal workflow — anything where the artifact lives in stdout rather than a browser. Triggers: "factory demo terminal", "demo a CLI", "record a terminal session", "screencast a script", "make a video of this command", "demo my tool". Use `factory-demo-video` (browser-based) when the subject is a web app instead.'
---

# Terminal Demo Recorder

Builds a self-contained HTML "terminal" page that plays back **real** CLI output with animated typing + scene markers, then records it as a `.webm` via Playwright — **and grabs a still PNG of every scene while it records**, so the result can be skimmed in 20 seconds instead of watched. The output is suitable for sharing in PRs, Slack, docs, or social posts — same format as the project's `demos/*.webm` browser screencasts.

The terminal is rendered in a browser, but the **command output is captured live from the actual CLI** before recording — nothing is fabricated.

## What a finished run leaves on disk

The recorder writes all three of these into the output directory. A run that produced only the
`.webm` is **not finished**:

```
demos/<feature>/
  <feature>-demo.webm     the video
  01-<slug>.png           still of scene 1, taken the moment its output is fully on screen
  02-<slug>.png           still of scene 2
  artifacts.md            one captioned line per file above
```

The stills and the manifest are automatic — the template handles both. The slug comes from the
scene's `command`, or from an explicit `"shot": "my-slug"` key on the scene if you want a better
name; the caption in `artifacts.md` comes from the scene's `narration`. So **writing a good
`narration` for each scene now also writes the caption the reviewer reads.**

`artifacts.md` is what the handoff comment and `/factory-explain` read to list what was produced.

## When to Use

- Demoing a CLI script, REPL, or any stdout-based workflow
- A `playwright-cli` browser demo doesn't fit because the artifact is text
- The user wants a video (not a static asciinema cast or screenshot)

## When NOT to Use

- The demo is of a web UI → use the `factory-demo-video` skill instead
- The user only wants a transcript or static screenshot
- `asciinema` is available and the user wants a cast file specifically — record directly with that

## Prerequisites

- Python with `playwright` installed (`pip install playwright && playwright install chromium`)
- `ffmpeg` (only if you want to extract preview frames; not required for the .webm itself)
- The CLI you want to demo is runnable end-to-end in the current environment

## Workflow

### Step 1 — Clarify the demo

Ask the user (if not obvious):
1. **Which CLI commands?** Pick 3–6 representative invocations. The first scene is often a "stats / overview" command; the rest are real-world queries.
2. **One-line narration per scene?** Optional but greatly improves the demo — appears above each prompt as a grey comment.
3. **Branding** — does this project have a colour palette / font / wordmark? If yes, match it (see "Theming" below). If not, default to the warm dark palette in the template.
4. **Output path** — usually `demos/<feature>-demo.webm` next to other project demos.

### Step 2 — Capture real CLI output

Run each scene's command and save stdout to a temp file. **Always capture before recording** so the demo shows real data.

```bash
mkdir -p /tmp/demo-captures
my-cli stats          > /tmp/demo-captures/01-stats.txt 2>&1
my-cli query "foo"    > /tmp/demo-captures/02-query.txt 2>&1
# ...
```

If a command fails or returns nothing interesting, **fix the command and re-capture** — do not edit the output text. The point is that what's on screen is what the CLI actually does.

### Step 3 — Copy and adapt the recorder template

Copy `assets/recorder-template.py` into the project's `demos/` directory (or wherever local demos live). Rename it to match the feature, e.g. `demos/<feature>-demo.py`.

Edit the `SCENES` list at the top:

```python
SCENES = [
    {"title": "My Feature", "subtitle": "One-line pitch", "duration_ms": 3500},

    {
        "command": "my-cli stats",
        "narration": "Inspect the new collection",
        "output": _read(CAPTURES_DIR / "01-stats.txt"),
        "type_delay_ms": 35,  # per-char typing delay; 25-40 is natural
        "hold_ms": 2800,      # how long to leave the result on screen
        "shot": "stats-overview",  # optional: filename slug for this scene's PNG
                                   # (defaults to a slug of the command)
    },
    # … more command scenes …

    {"title": "Closing line", "subtitle": "Optional pithy summary", "duration_ms": 3000},
]
```

Two scene shapes:
- **Splash** — `{title, subtitle, duration_ms}` — full-screen title card; one at start, optionally one at end. Splash scenes are not screenshotted (a picture of your own title card proves nothing).
- **Command** — `{command, narration, output, type_delay_ms, hold_ms, shot?}` — animated prompt + typed command + revealed output, **and one PNG still** taken right after the output finishes rendering.

Other things you may want to tune in the template:
- `CAPTURES_DIR` — where you saved the stdout files
- `OUTPUT_WEBM` — final video path
- `SHOTS_DIR` / `ARTIFACTS_MD` — where the stills and the manifest go (default: next to the video)
- `_colorize()` in the HTML's `<script>` — regex-based output highlighting (rank headers, separators, totals, etc.). Adapt to your CLI's output shape.
- Viewport size (default `1280×720` — matches most demo conventions)

### Step 4 — Theming (optional)

The template ships with a warm dark palette inspired by terminal aesthetics. To match a specific project brand, edit the `:root` CSS variables in the HTML template inside the recorder:

```css
--bg: #0B0D0E;       /* page background */
--panel: #0A0C0D;    /* frame background (slightly darker — depth goes down) */
--border: rgba(237, 231, 218, 0.10);
--ink: #EDE7DA;      /* main text */
--muted: rgba(237, 231, 218, 0.55);
--gold: #D8B36A;     /* accent — chapter markers, brand wordmark */
--sage: #A8C9A0;     /* prompt + positive */
--rose: #C99090;     /* negative */
```

Also update:
- `<title>` and `.titlebar .meta` text to match the project name
- `.titlebar .label` to match the local cwd ("~/code/myproject — my-cli")
- The accent word the splash highlights (search for `splashTitle.innerHTML.replace`)

### Step 5 — Record

```bash
python demos/<feature>-demo.py
```

The script prints an estimated duration, runs headless Chromium, and writes the `.webm`, one `NN-<slug>.png` per command scene (it logs each one as `shot  NN-<slug>.png`), and `artifacts.md`. Typical run takes ~the duration of the demo + a couple of seconds. A 50-second demo produces a ~2 MB video and a handful of ~100 KB stills.

If it prints `WARNING: no screenshots were captured`, the demo is incomplete — the `shot()` call in
`showOutput()` has been edited out of the template. Restore it and re-record.

### Step 6 — Sanity check

Open it in a browser:

```bash
google-chrome demos/<feature>-demo.webm    # or: xdg-open / open
```

Or extract a mid-demo frame for a quick text-only review without launching a video player:

```bash
ffmpeg -y -ss 15 -i demos/<feature>-demo.webm -frames:v 1 -update 1 /tmp/frame.png
```

Then `Read` the PNG to visually confirm layout, colour, and content.

If something is off:
- **Output gets cut off the bottom** → reduce scenes, lower `hold_ms`, or set `clearTerm()` to fire on every command instead of every other (search for `chapterIdx % 2 === 0`).
- **Typing feels too fast/slow** → tune `type_delay_ms` (25 = fast, 60 = slow).
- **Result reveal feels rushed** → bump `hold_ms` (3500–5000 is comfortable for tables).
- **Wrong colours** → tweak the `:root` CSS variables.

### Step 7 — Cleanup

Delete the intermediate HTML the script writes (it's not needed after recording) — the template already does this on success but if something errored you may have `demos/_<feature>-demo.html` lying around.

## Design Principles

- **Real output, animated playback.** Never fabricate or edit the stdout. The whole point is to show what the CLI actually does.
- **Narrate sparingly.** One short comment per command, set in italic muted grey above the prompt. If a command is self-explanatory, skip narration.
- **Pace for reading, not for typing.** The reader needs time to scan a table — `hold_ms` for output should be 2–5× the time it took to type the command.
- **One frame, no cutscenes.** A terminal is calmer than a UI demo — don't try to use overlays, banners, or chapter cards beyond the top-right "Scene 0X" marker the template provides.
- **Brand subtly.** A wordmark in the titlebar + an accent colour for `RANK`/`TOTAL`/section headers is enough. Avoid logos, gradients, or decorations inside the terminal area.

## Files

| Path | Purpose |
|---|---|
| `assets/recorder-template.py` | Self-contained Python script — HTML template, scene runner, Playwright recorder, per-scene screenshot capture, and the `artifacts.md` writer. Copy into the target project's `demos/` dir and edit `SCENES`. |

## Comparison to `factory-demo-video`

| | `demo-terminal` (this) | `factory-demo-video` |
|---|---|---|
| Subject | CLI / script / REPL | Web UI / app |
| Tool | Plain Playwright + custom HTML | `playwright-cli` skill helpers |
| Source of truth | Captured stdout | Live browser actions |
| Output | `.webm` of an HTML "terminal" + a PNG per scene + `artifacts.md` | `.webm` of a real browser session + PNGs of the key states (incl. mobile) + `artifacts.md` |
| Effort | ~10 min once template is copied | Variable — depends on UI complexity |

Use `factory-demo-video` when the user is showing a UI. Use this skill when the user is showing a command.
