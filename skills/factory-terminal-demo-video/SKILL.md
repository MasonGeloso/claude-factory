---
name: factory-terminal-demo-video
description: 'Build a polished, narrated demo video of a REAL interactive CLI or coding-agent session — captured in a PTY to an asciinema cast, time-warped, replayed inside a CSS "OS" window (macOS chrome, frosted glass, dock, localisable menu bar), recorded at 2560x1440, then dubbed with a voice-over and burned-in subtitles. Use when the demo subject is an agent/REPL/CLI session that takes minutes and needs editing down, when the output must look like a real screen recording rather than a terminal pastiche, or when it needs narration in another language. Triggers: "terminal demo video", "record my agent session", "make a video of this CLI with a voiceover", "dub this terminal demo", "MCP demo video". For a quick silent screencast of command output use `factory-demo-terminal` instead; for a web app use `factory-demo-video`.'
---

# Terminal Demo Video

Records a **real** interactive terminal session and turns it into a narrated, subtitled video that
looks like a screen capture of a desktop, not a web page pretending to be a terminal.

Every byte on screen is what the program actually printed. Nothing is retyped, reconstructed or
mocked up. The only editing is *when* each byte plays.

## When to use this instead of `factory-demo-terminal`

| | `factory-demo-terminal` | this skill |
|---|---|---|
| capture | runs commands, collects stdout | `pexpect` PTY of a live **interactive** session (agents, REPLs, TUIs) |
| replay | hand-built animated HTML terminal | real `asciinema-player` fed a real v2 cast |
| framing | terminal panel | CSS "OS" window — wallpaper, menu bar, dock, frosted glass |
| editing | typing animation | piecewise time-warp + freeze-frames on the payoff |
| audio | none | voice-over, humaniser-gated, with anchored subtitles |
| output | `.webm` | `.mp4` + `.webm` + subtitled `.mp4` + sidecar `.srt` |

Use `factory-demo-terminal` when a short silent screencast will do. Use this when the session is
long, has a payoff worth holding on, and is going somewhere public.

## The shape of the pipeline

```
real PTY capture ──► asciinema v2 .cast ──► piecewise time-warp ──► asciinema-player
(pexpect)                                                           inside a CSS "OS" page
                                                                            │
VO script ──► humaniser gate ──► TTS ──► per-block verify ──► anchored track
                                                                            │
                                          Playwright records 2560x1440 ─────┴──► ffmpeg mux
                                                                                 + SRT + burn-in
```

**Why this shape.** The cast is the source of truth. Once captured, a look change re-renders in about
two minutes instead of re-running a ten-minute session. That single property is what makes iterating
on the visuals affordable, and it is the reason the pipeline is split this way rather than recording
the screen directly.

## Configuration

The consuming project writes one `demo.json`; nothing else here is project-specific.

```json
{
  "command": "claude",
  "args": ["--dangerously-skip-permissions"],
  "cwd": "demo",
  "cols": 92, "rows": 30,
  "prompt_file": "demo/prompt.txt",
  "done_when": { "file": "demo/output.md", "min_bytes": 1500, "stable_polls": 4 },
  "timeout_s": 780,
  "segments": [[0, 12, 3], [12, 30, 20], [30, 300, 12], [300, 340, 1]],
  "dwells": [[31.0, 8.0], [338.0, 6.0]],
  "chrome": { "theme": "macos", "locale": "ja-JP", "title": "claude", "wallpaper": "chrome/wall.jpg" },
  "voice": { "script": "vo.txt", "display_script": "vo-display.txt", "anchors": [1.0, 4.6], "voice_id": "..." },
  "subtitles": true,
  "out_basename": "out/my-demo"
}
```

`segments` and `dwells` are the edit. Everything else is capture or framing.

## Stages

Run them in order. Each writes a file the next one reads, so any stage can be re-run alone.

1. **`scripts/rec_cast.py`** — PTY capture → `session.cast`
2. **`scripts/warp_cast.py`** — edit the timeline → `final.cast`
3. **`chrome/macos.html`** — the OS page (served over HTTP by `scripts/serve.py`)
4. **`scripts/record_web.py`** — Playwright → raw `.webm`
5. voice-over — script → **humaniser gate** → TTS → per-block verification
6. **`scripts/mux_web.py`** — rescale, anchor audio, SRT, burn-in → final artefacts

## The rules that are not negotiable

These each cost a full run to learn. They are in `references/traps.md` with the symptom that led to
them; the short version:

- **Detect completion from the ARTEFACT, never from the agent's prose.** Matching a sentence in which
  the agent *says* it is about to save a file interrupts the run mid-work. Wait for the output file
  to exist and stop growing.
- **A multi-line prompt must be sent as ONE line.** `\n` → `\r` submits every line as its own
  message. Single-line prompt, or bracketed paste (`\x1b[200~` … `\x1b[201~`).
- **Decode the PTY incrementally** (`codecs.getincrementaldecoder`). Per-read decoding splits
  multibyte characters and leaves stray glyphs on screen.
- **Verify the player theme actually applied** by reading a CSS custom property back. A `<style>`
  block in the wrong place is silently ignored and every render uses the default palette — the
  symptom looks exactly like a content bug.
- **Playwright's capture does not run at real time**, and not consistently in one direction. Bracket
  the animation with two solid-colour markers and time-rescale the span. Find the markers as **runs**
  and take `runs[0]` end / `runs[-1]` start — the recorder emits warm-up frames first.
- **The humaniser is a hard gate and must be re-run after every rewrite.** A timing re-cut silently
  deleted a structural beat from a narration script that had passed the gate on its first draft.
- **Verify voice-over blocks individually**, and measure that the audio actually landed
  (`volumedetect` per narration window, silence in the gaps). "It muxed" is not evidence.
- **Keep the spoken script and the on-screen script separate.** TTS needs words opened to kana or
  respelled; those spellings must never reach the subtitles. Assert equal block counts.

## Verification discipline

Do these, not a visual once-over — each of them caught a real defect that eyeballing had missed:

- Sample a frame at each narration beat; confirm the screen shows what the voice is describing.
- Detect scene transitions by pixel-diffing a small region over time; compare against planned times.
- Prove a freeze is a freeze: identical bright-pixel fraction across the dwell.
- Measure text contrast numerically (WCAG), including the echoed prompt block, which sits on a
  different background colour from the body text.
- Read back CSS custom properties to prove a theme applied.

## Localising the OS chrome

Two things look the same on screen and are not:

- **The CLI's own TUI is usually not localisable.** Verified for Claude Code: the bundle contains no
  translations of any on-screen string, and a `language` setting is accepted and ignored.
- **The chrome around it is yours** — it is your own CSS. If you leave it in English, the frame reads
  as an English desktop with a foreign-language app inside it. `chrome.locale` drives the menu bar,
  the clock format and the window title. Compute the weekday; do not hand-write it.
- A Latin UI font has no CJK. The stack needs a Japanese face behind it or the menu bar renders as
  tofu.

## Licence note for the icon set

Real OS icons matter — hand-drawn approximations read as fake, mostly because macOS icons are
squircles (superellipse, n≈5) rather than rounded rectangles. The set this was built against is
**WhiteSur** (GPL-3.0). That is a licence decision for the consuming project: bundle nothing, and
have the project point `chrome.icons` at a set it has cleared.

## Known gap

Publishing the finished video is out of scope and, in at least one environment, blocked: X's composer
will not attach a video if the browser cannot decode it locally. See the `x-post` starter in
`factory-marketing-onboard` before promising an end-to-end autonomous post that includes video.
