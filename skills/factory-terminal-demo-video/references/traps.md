# Traps, with the symptom that led to each

Every entry here cost at least one full run. They are grouped by stage. The symptom is included
because in almost every case the symptom pointed at the wrong stage.

## Stage 1 — PTY capture

| trap | symptom |
|---|---|
| A startup dialog ("do you trust this folder?") eats the typed prompt and the process exits. | Recording ends seconds in with no prompt on screen. **Pre-accept the dialog in the tool's own config before recording** — don't script past it. |
| `PROMPT.replace("\n","\r")` submits **every line as its own message**. | Seven queued messages on camera. Send a single-line prompt, or use bracketed paste (`\x1b[200~` … `\x1b[201~`). |
| Decoding each 64 KB read separately splits multibyte UTF-8. | A stray `€` on screen (an orphaned `0x80` rendered as cp1252). Use `codecs.getincrementaldecoder("utf-8")`. |
| Naming a non-tool in `--disallowedTools`. | `Permission deny rule "advisor" matches no known tool` printed **into the recording**. `advisor` is a *setting*, not a tool — disable it by lifting the setting for the run, with a restore trap. |
| Detecting completion from the agent's prose. | Matching 「…を保存します」 — an *intention* — interrupted the run mid-work. Watch the **artefact**: exists, ≥ N bytes, size stable across several polls. |
| A prompt in language X does not reliably get an answer in X. | One full run came back in English from a Japanese prompt. Force it with an explicit system-prompt instruction. |
| Terminal width chosen by habit. | 108 cols left a dead third of the window; 92×30 fit. **Pick cols from the content.** |
| Parent-session env markers. | The child printed a "transcript saving is off" warning across the status line, on camera. Drop the marker env prefixes before spawning. |

## Stage 2 — editing the cast

- **Piecewise speed, not uniform**: boot ×3, typing ×20, tool calls ×9–18, the payoff ×1.
- **Idle-gap capping barely helps** — the time is inside the spinner, not in idle gaps.
- **Freeze-frames are mandatory for the payoff.** The result table scrolled out of view and was never
  fully visible in normal playback. `DWELLS=[[real_time, seconds]]` holds the last rendered frame.
- **Skip the typing.** Collapse it to ~2s (reads as a paste) and DWELL ~8s on the completed prompt so
  the viewer can read it while the narration explains it. Watching characters appear is dead time.
- **Substitute U+00A0 → space.** Some CLIs pad the input line with no-break spaces; both `agg` and the
  player draw them as tofu.

## Stage 3 — the OS page

See `chrome/README.md`. The two that cost the most: a `<style>` block after `</html>` is silently
ignored (every render used the default palette while we chased a "white-on-white content bug"), and
the echoed prompt sits on `--term-color-8` rather than the body background.

## Stage 4 — recording

- **Playwright's capture does not run at real time, and not consistently in one direction.**
  Measured 47.08s for a 51.5s animation (fast) and 59.04s for 55.3s (slow).
- **Bracket the animation with two solid marker frames** and time-rescale the span.
- **Find markers as RUNS**; take `runs[0]` end and `runs[-1]` start. The recorder emits blank warm-up
  frames *before* the hold, so scanning from frame 0 for "still a marker" reports `t0=0` and silently
  breaks sync — a drift that reads as a page bug for hours.

## Stage 5 — voice-over

- **The humaniser is a hard gate and must be re-run after every rewrite.** We ran it on the first
  draft, then rewrote four times for TTS and timing and never re-ran it. The audit found a real
  regression: a re-cut had deleted the speaker's belief line — the structural turn — and without it
  the reveal had nothing to land against and every block was independently deletable, which is the
  classic machine-structure tell. **Losing a structural beat to a timing edit is the failure mode.**
- **Voice settings can produce unintelligible audio.** ElevenLabs at `stability 0.45 / style 0.25`
  gave genuinely broken speech on short blocks; two independent ASRs agreed. `0.80 / 0.85 / 0.0`
  fixed it. Suspect the settings before suspecting the script.
- **Verify blocks individually.** A concatenated pass introduces its own artefacts and sends you
  chasing phantoms. Concatenating mp3s with `-c copy` glitches at every boundary — re-encode.
- **Per-word respelling is unavoidable for Japanese TTS.** Ours: 株→かぶ, 五つ→いつつ, 円安→えんやす
  (standalone), 節約志向→せつやくしこう, 追い風→おいかぜ (read おいふう), 日付→ひづけ (read 皮膚器),
  開示→かいじ, 行います→おこないます. Verify each with ASR; do not assume.
- **Keep a separate display script.** Those spellings are TTS hacks and must never reach the screen.
  Subtitles come from the proper-orthography version, asserted to have the same block count.

## Stage 6 — mux and subtitles

- Anchor each block at an explicit time; build the track with `adelay` + `amix` + `apad`, trimming
  each block's own leading/trailing silence first.
- **Verify the audio landed** by measuring `volumedetect` mean per narration window and confirming
  true silence in the gaps. "It muxed" is not evidence.
- **ffmpeg's ASS `PlayResY` defaults to 288**, so `FontSize` scales ~5× on a 1440-tall frame:
  `FontSize=8` ≈ 40 px, while `25` rendered ~80 px and swamped the frame.
- **`-ss` before `-i` breaks subtitle timing** when burning at extract time — nothing is active at
  the sought frame. Burn the whole file, then extract to check.
- Watch for occlusion: at a low `MarginV` the subtitle rendered *behind the dock* and looked absent.
- Ship three artefacts: clean video, burned-in-subtitle video (for muted autoplay feeds), sidecar
  `.srt` (for platforms that take one).

## Verification discipline that actually caught things

- Sample a frame at each narration beat; confirm the screen shows what the voice describes.
- Detect scene transitions by pixel-diffing a small region over time; compare against planned times.
- Prove a freeze is a freeze: identical bright-pixel fraction across the dwell.
- Measure text contrast numerically (WCAG) rather than judging by eye.
- Read back CSS custom properties to prove a theme applied.
