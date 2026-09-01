# factory-marketing-video

<p align="center">
  <img src="static/video-use-banner.png" alt="video-use" width="100%">
</p>

Introducing **video-use** — edit videos with Claude Code. 100% open source.

Drop raw footage in a folder, chat with Claude Code, get `final.mp4` back. Works for any content — talking heads, montages, tutorials, travel, interviews — without presets or menus.

Try video-use in [Browser Use Cloud](https://cloud.browser-use.com/v4?utm_campaign=video-use-use-in-cloud&utm_source=github).

## What it does

- **Cuts out filler words** (`umm`, `uh`, false starts) and dead space between takes
- **Auto color grades** every segment (warm cinematic, neutral punch, or any custom ffmpeg chain)
- **30ms audio fades** at every cut so you never hear a pop
- **Burns subtitles** in your style — 2-word UPPERCASE chunks by default, fully customizable
- **Generates animation overlays** via [HyperFrames](https://github.com/heygen-com/hyperframes), [Remotion](https://www.remotion.dev/), [Manim](https://www.manim.community/), or PIL — spawned in parallel sub-agents, one per animation
- **Self-evaluates the rendered output** at every cut boundary before showing you anything
- **Persists session memory** in `project.md` so next week's session picks up where you left off
- **Dubs into another language** with a cloned voice, with a mandatory verify-and-regenerate loop (added on top of upstream — see "Provenance" below)
- **Publishes to YouTube** (long-form + shorts) through a human-gated flow (added on top of upstream)

## Provenance — this is the factory suite's vendored copy

This started as [`browser-use/video-use`](https://github.com/browser-use/video-use) (MIT licensed —
see `LICENSE`) and has been extended for the Factory marketing pillar with a dubbing pipeline
(`helpers/dub.py`), YouTube publishing + shorts guidance, and a companion recap-content skill
(`factory-marketing-recap`). It lives inside this repo at `skills/factory-marketing-video/`, is
versioned here, and **has no git remote of its own** — cloning or pulling the upstream project over
it would destroy the additions layered on top (the modified `SKILL.md`, `helpers/render.py`, and the
local-only helpers: `dub.py`, `tighten.py`, `shoot_scene.py`, `broll_cards.py`, `make_short.py`, and
others). Improve it with ordinary commits to this repo instead of re-pulling upstream.

## Setup

Nothing to install for the skill itself — installing the factory plugin/skills is enough.
`install.md` covers the machine-level prerequisites only: Python deps, `ffmpeg`, and (if you use the
dubbing pipeline) an ElevenLabs API key
(grab one at [elevenlabs.io/app/settings/api-keys](https://elevenlabs.io/app/settings/api-keys)).

```bash
cd skills/factory-marketing-video
uv sync                         # or: pip install -e .
cp .env.example .env
$EDITOR .env                    # ELEVENLABS_API_KEY=...
```

`ffmpeg` is required and `yt-dlp` is optional (only for pulling sources from URLs).

Then point Claude Code at a folder of raw takes:

```bash
cd /path/to/your/videos
claude
```

And in the session:

> edit these into a launch video

It inventories the sources, proposes a strategy, waits for your OK, then produces `edit/final.mp4` next to your sources. All outputs live in `<videos_dir>/edit/` — the skill directory stays clean.

## How it works

The LLM never watches the video. It **reads** it — through two layers that together give it everything it needs to cut with word-boundary precision.

**Layer 1 — Audio transcript (always loaded).** One ElevenLabs Scribe call per source gives word-level timestamps, speaker diarization, and audio events (`(laughter)`, `(applause)`, `(sigh)`). All takes pack into a single ~12KB `takes_packed.md` — the LLM's primary reading view.

```
## C0103  (duration: 43.0s, 8 phrases)
  [002.52-005.36] S0 Ninety percent of what a web agent does is completely wasted.
  [006.08-006.74] S0 We fixed this.
```

**Layer 2 — Visual composite (on demand).** `timeline_view` produces a filmstrip + waveform + word labels PNG for any time range. Called only at decision points — ambiguous pauses, retake comparisons, cut-point sanity checks.

<p align="center">
  <img src="static/timeline-view.svg" alt="timeline_view composite — filmstrip + speaker track + waveform + word labels + silence-gap cut candidates" width="100%">
</p>

> Naive approach: 30,000 frames × 1,500 tokens = **45M tokens of noise**.
> Video Use: **12KB text + a handful of PNGs**.

Same idea as browser-use giving an LLM a structured DOM instead of a screenshot — but for video.

## Pipeline

```
Transcribe ──> Pack ──> LLM Reasons ──> EDL ──> Render ──> Self-Eval
                                                              │
                                                              └─ issue? fix + re-render (max 3)
```

The self-eval loop runs `timeline_view` on the _rendered output_ at every cut boundary — catches visual jumps, audio pops, hidden subtitles. You see the preview only after it passes.

## Design principles

1. **Text + on-demand visuals.** No frame-dumping. The transcript is the surface.
2. **Audio is primary, visuals follow.** Cuts come from speech boundaries and silence gaps.
3. **Ask → confirm → execute → self-eval → persist.** Never touch the cut without strategy approval.
4. **Zero assumptions about content type.** Look, ask, then edit.
5. **12 hard rules, artistic freedom elsewhere.** Production-correctness is non-negotiable. Taste isn't.

See [`SKILL.md`](./SKILL.md) for the full production rules and editing craft, including dubbing and
YouTube publishing.
