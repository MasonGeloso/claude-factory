---
name: video-use-install
description: One-time machine setup for the factory-marketing-video skill — ffmpeg, Python deps, and the ElevenLabs API key. The skill itself is already installed; this file never clones or symlinks anything.
---

# factory-marketing-video setup

Use this file only for machine setup or reconnect on a fresh box. For daily editing, read `SKILL.md`. Always read `helpers/` — that's where the scripts live.

## ⚠️ This copy is modded — never re-install it from git

This skill is versioned as part of this repo's `skills/factory-marketing-video/`. It started as
`browser-use/video-use` but has been heavily modified since (a dubbing pipeline, YouTube publishing,
shorts), and the upstream link was deliberately cut. There is no remote and no upstream history here.

- **Do not** `git clone https://github.com/browser-use/video-use` anywhere.
- **Do not** `git pull` this directory from upstream, or re-run any "install video-use" flow.
- **Do not** symlink it elsewhere — the factory skill installer discovers it in place.

Anything that re-fetches upstream will silently overwrite local work: `SKILL.md`, `helpers/render.py`,
the dubbing/publishing sections, and the local-only helpers that exist only here. Changes go in as
ordinary commits to this repo.

## What must exist on this machine

The skill files are already present. Setup is only about the things that live outside the repo:

1. `ffmpeg` + `ffprobe` on `$PATH` (plus optional `yt-dlp` for online sources).
2. Python deps from `pyproject.toml`.
3. An ElevenLabs API key, for Scribe transcription (and for the dubbing pipeline's voice cloning/TTS).

Paths below are written relative to this directory (`skills/factory-marketing-video/`).
Resolve them against the directory containing this file — this repo may also be worked on in git
worktrees, so don't hardcode an absolute path to it.

## Setup contract

- Do everything yourself. Only ask the user for things you cannot generate — the ElevenLabs API key, and confirmation before any package install that needs sudo.
- The skill references helpers by bare name (`transcribe.py`, `render.py`). That works because `SKILL.md` and `helpers/` are siblings — keep them that way.
- Verify by running one real command against one real file. Don't declare success on file-existence checks alone.

## Steps

### 1. Python deps

From this directory:

```bash
# Prefer uv if available; fall back to pip.
command -v uv >/dev/null && uv sync || pip install -e .
```

`pyproject.toml` lists `requests`, `librosa`, `matplotlib`, `pillow`, `numpy`. No console scripts — helpers are invoked directly as `python helpers/<name>.py`.

### 2. ffmpeg (+ optional yt-dlp)

`ffmpeg` and `ffprobe` are hard requirements. `yt-dlp` is only needed if the user wants to pull sources from URLs. Animation engines such as HyperFrames, Remotion, and Manim are installed lazily the first time a project actually needs them.

```bash
# Debian / Ubuntu
# sudo apt-get update && sudo apt-get install -y ffmpeg
# pip install yt-dlp

# macOS
# command -v ffmpeg >/dev/null || brew install ffmpeg
# command -v yt-dlp >/dev/null || brew install yt-dlp     # optional

# Arch
# sudo pacman -S ffmpeg yt-dlp
```

If the package manager requires a sudo prompt, tell the user the exact command and wait. Do not invent a password.

### 3. ElevenLabs API key

Scribe (ElevenLabs) does all transcription, and the dubbing pipeline's voice cloning/TTS also runs on ElevenLabs. Without a key, neither works.

1. Check existing state in this order and stop at the first hit:

    ```bash
    # a) env var already exported
    [ -n "$ELEVENLABS_API_KEY" ] && echo "env"
    # b) .env in this directory already has it
    grep -q '^ELEVENLABS_API_KEY=..' .env 2>/dev/null && echo "dotenv"
    ```

2. If neither is set, ask the user exactly once:

    > I need an ElevenLabs API key for transcription (word-level timestamps, speaker diarization, filler tagging) and dubbing. Grab one at https://elevenlabs.io/app/settings/api-keys and paste it here — I'll write it to the skill's `.env`. Or if you already have it exported as `ELEVENLABS_API_KEY`, say "use env" and I'll skip.

    When the user pastes a key, write it to `.env` in this directory:

    ```bash
    printf 'ELEVENLABS_API_KEY=%s\n' "$KEY" > .env
    chmod 600 .env
    ```

    Never echo the key back in tool output. Never commit `.env` — it is ignored both by this
    directory's own `.gitignore` and (if configured) by the repo's root `.gitignore`, but that is a
    safety net, not a licence to be careless. Write it here, never to the user's `<videos_dir>`.

3. Sanity check with a cheap, quota-free call:

    ```bash
    curl -s -o /dev/null -w '%{http_code}\n' \
      -H "xi-api-key: $(sed -n 's/^ELEVENLABS_API_KEY=//p' .env)" \
      https://api.elevenlabs.io/v1/user
    ```

    `200` means the key works. `401` means the user pasted a wrong/expired key — ask once more and stop. Anything else (network, 5xx), move on and verify during first real transcription.

### 4. Verify end-to-end

Run one real thing. Prefer the lightest verification that still proves the pipeline is wired up:

```bash
python helpers/timeline_view.py --help >/dev/null && echo "helpers OK"
ffprobe -version | head -1
```

Full transcription test is optional at setup time — it burns Scribe credits. Better to wait until the user hands you their first clip.

### 5. Hand off

Tell the user, in one short message:

- That setup is done and the skill is live in this repo.
- That a good first message is: *"edit these into a launch video"* or *"inventory these takes and propose a strategy."*
- That all outputs land in `<videos_dir>/edit/` — the repo stays clean.

## Keeping the skill current

There is nothing to pull. This skill evolves through ordinary commits to this repo: edit `SKILL.md` /
`helpers/` in place and commit them like any other file. If `pyproject.toml` changes deps, re-run
`uv sync` / `pip install -e .`.

## Cold-start reminders

- Keep `SKILL.md` and `helpers/` as siblings. The helpers are resolved relative to `SKILL.md`.
- If `.env` exists but the key is empty, treat it the same as missing — don't assume existence means validity.
- `ffmpeg` from static builds works fine. Any modern (≥ 4.x) build is enough.
- `yt-dlp` is optional. Don't block setup on it; install lazily the first time a user asks to pull from a URL.
- Node.js/npm are only needed for HyperFrames or Remotion slots. HyperFrames currently requires Node.js 22+.
- HyperFrames, Remotion, and Manim are optional animation engines. Don't install or prefer one globally during setup; pick the engine per animation slot in `SKILL.md`. HyperFrames can run through `npx --yes hyperframes ...` in the slot directory. Remotion can be scaffolded with `npx create-video@latest` or installed inside the slot before rendering.
- Never run transcription as part of setup verification unless the user explicitly asks — Scribe costs real money.
