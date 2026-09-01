---
name: factory-marketing-video
description: Edit any video by conversation. Transcribe, cut, color grade, generate overlay animations, burn subtitles, dub into another language with a cloned voice, publish to YouTube, cut shorts — for talking heads, montages, tutorials, travel, interviews, and recurring commentary/recap videos. No presets, no menus. Ask questions, confirm the plan, execute, iterate, persist. Production-correctness rules are hard; everything else is artistic freedom. Vendored from the open-source video-use project (MIT) with a dubbing pipeline and YouTube publishing/shorts workflow added.
---

# Video Use

## Principle

1. **LLM reasons from raw transcript + on-demand visuals.** The only derived artifact that earns its keep is a packed phrase-level transcript (`takes_packed.md`). Everything else — filler tagging, retake detection, shot classification, emphasis scoring — you derive at decision time.
2. **Audio is primary, visuals follow.** Cut candidates come from speech boundaries and silence gaps. Drill into visuals only at decision points.
3. **Ask → confirm → execute → iterate → persist.** Never touch the cut until the user has confirmed the strategy in plain English.
4. **Generalize.** Do not assume what kind of video this is. Look at the material, ask the user, then edit.
5. **Artistic freedom is the default.** Every specific value, preset, font, color, duration, pitch structure, and technique in this document is a *worked example* from one proven video — not a mandate. Read them to understand what's possible and why each worked. Then make your own taste calls based on what the material actually is and what the user actually wants. **The only things you MUST do are in the Hard Rules section below.** Everything else is yours.
6. **Invent freely.** If the material calls for a technique not described here — split-screen, picture-in-picture, lower-third identity cards, reaction cuts, speed ramps, freeze frames, crossfades, match cuts, L-cuts, J-cuts, speed ramps over breath, whatever — build it. The helpers are ffmpeg and PIL. They can do anything the format supports. Do not wait for permission.
7. **Verify your own output before showing it to the user.** If you wouldn't ship it, don't present it.
8. **Every video gets visuals built for it.** Graphics are made from what is being said in *this* video, not selected from a library of shapes that worked before. Reusing last episode's layout with new numbers in it makes the channel look templated and makes the visuals stop carrying information. Archetypes and helpers are for thinking and rendering — the content is always new. See *Build the visuals for THIS video* under scene animation.

## Hard Rules (production correctness — non-negotiable)

These are the things where deviation produces silent failures or broken output. They are not taste, they are correctness. Memorize them.

1. **Subtitles are applied LAST in the filter chain**, after every overlay. Otherwise overlays hide captions. Silent failure.
2. **Per-segment extract → lossless `-c copy` concat**, not single-pass filtergraph. Otherwise you double-encode every segment when overlays are added.
3. **30ms audio fades at every segment boundary** (`afade=t=in:st=0:d=0.03,afade=t=out:st={dur-0.03}:d=0.03`). Otherwise audible pops at every cut.
4. **Overlays use `setpts=PTS-STARTPTS+T/TB`** to shift the overlay's frame 0 to its window start. Otherwise you see the middle of the animation during the overlay window.
5. **Master SRT uses output-timeline offsets**: `output_time = word.start - segment_start + segment_offset`. Otherwise captions misalign after segment concat.
6. **Never cut inside a word.** Snap every cut edge to a word boundary from the Scribe transcript.
7. **Pad every cut edge.** Working window: 30–200ms. Scribe timestamps drift 50–100ms — padding absorbs the drift. Tighter for fast-paced, looser for cinematic.
8. **Word-level verbatim ASR only.** Never SRT/phrase mode (loses sub-second gap data). Never normalized fillers (loses editorial signal).
9. **Cache transcripts per source.** Never re-transcribe unless the source file itself changed.
10. **Parallel sub-agents for multiple animations.** Never sequential. Spawn N at once via the `Agent` tool; total wall time ≈ slowest one.
11. **Strategy confirmation before execution.** Never touch the cut until the user has approved the plain-English plan.
12. **All session outputs in `<videos_dir>/edit/`.** Never write inside the `video-use/` project directory.
13. **Never report a step done without the check that proves it.** This is the single most
    repeated failure in this skill's history, and it is a REPORTING failure, not a technical
    one. In one session: two renders were summarised as "in flight" while a broken wait loop
    had them stalled for fourteen hours; a video language was reported set when the click had
    silently not committed; a whole caption-upload phase was summarised as complete without
    having been started. Each check was seconds of work. Before writing "done", name the
    evidence — the frame you looked at, the field you re-opened, the row that now reads
    Published. If you cannot name it, write "not verified" instead.
14. **Hand over every artifact you build.** Publishing is not delivering. Two finished videos
    were uploaded to the platform and never sent to the client, who had to ask where they
    were. When a run produces files, send all of them, and say which ones the client has not
    seen yet.
15. **Verify against the rendered output, never against the plan.** Every silent failure in
    this skill's history was a plan that looked right and a render that wasn't: cut edges that
    read as clean in the EDL but clipped 81 of 118 word endings; a description that was correct
    in the source file and dropped a digit when typed into the form; a webcam inset that was
    perfectly specified and played at half speed because the source was 60fps and the output 30.
    In every case the check that would have caught it was cheap and mechanical — re-transcribe
    the whole render and diff it, read the form field back, difference the composited inset
    against its source frame. Do the mechanical check before showing the user, not after they
    spot it.

16. **A dub script is not finished when it fits — quality passes are a HARD GATE, not a step you can defer.** This is the rule that shipped a Japanese dub a viewer could not understand, and the lesson had already been written down and was skipped anyway. Fitting is measured in seconds and gives constant feedback, so it eats all the iteration; quality is silent and gets zero. **Every dub script MUST clear all three before a single block is synthesised:**
    - **De-AI / naturalness pass** on the target language (run the `factory-humanizer` skill in that language). Not optional, not "if it looks off".
    - **Terminology audit** — every domain term checked against how the target language's own press writes it, not transliterated. `システマティックな投資家` and `タクソノミー` are what carrying English across produces.
    - **Pronunciation lint** — any word whose kanji has more than one plausible reading gets rewritten in kana. TTS read 鈍って as ドンって and 転んだ as 終わった; no voice setting fixes that, because it is the script handing the synthesiser an ambiguous string.

    Then, and only then, fit for length — and **re-run the quality passes after every length rewrite**, because a rewrite made to hit a character count is exactly where stiff phrasing enters. `dub.py synth` enforces this and refuses to run without it; do not work around the gate.

17. **A synthetic dub is not verified until a native speaker has heard it.** ASR recovery is NOT a proxy — a native voice reading the same script fails the same words, so the measurement cannot separate a bad accent from a weak recogniser. Sixty seconds of a human listening decides what no amount of analysis will. Get it before publishing, not after a viewer comments.

Everything else in this document is a worked example. Deviate whenever the material calls for it.

## Directory layout

The skill lives at `skills/factory-marketing-video/` in this repo. User footage lives wherever they put it. All session outputs go into `<videos_dir>/edit/`.

```
<videos_dir>/
├── <source files, untouched>
└── edit/
    ├── project.md               ← memory; appended every session
    ├── takes_packed.md          ← phrase-level transcripts, the LLM's primary reading view
    ├── edl.json                 ← cut decisions
    ├── transcripts/<name>.json  ← cached raw Scribe JSON
    ├── animations/slot_<id>/    ← per-animation source + render + reasoning
    ├── clips_graded/            ← per-segment extracts with grade + fades
    ├── master.srt               ← output-timeline subtitles
    ├── downloads/               ← yt-dlp outputs
    ├── verify/                  ← debug frames / timeline PNGs
    ├── preview.mp4
    └── final.mp4
```

## Delivery conventions

Per-project defaults that are easy to forget and expensive to notice late. Confirm them against
the project's `project.md` at the start of a session.

- **English cuts ship at 1.5x.** `setpts=PTS/1.5` + `atempo=1.5`. Apply it last, scale overlay
  start times by 1/1.5 but keep their durations, and divide chapter timestamps by 1.5.
- **Dubbed cuts ship at 1x**, since the synthesised delivery is already even-paced.
- Both versions go on the same channel; the dub declares itself in the description.

## Runbooks

[`references/recap-runbook.md`](references/recap-runbook.md) — the full end-to-end order of
operations for a recurring commentary/recap video: back up masters, transcribe, tighten, add
source cards, dub with a cloned voice, publish with chapters and captions, then cut shorts and
build scene animation for them. Read it when the task spans more than one stage; the sections
below carry the reasoning, the runbook carries the sequence, the QC gates and the calibration
numbers from a real run. (The pre-production half of a recap — research, script, whiteboard
board — is the `factory-marketing-recap` skill's job; this runbook picks up once you have
footage to edit.)

The phase order is load-bearing: **publish both long versions → upload both transcripts →
cut 3-5 English shorts → build scene animation → then the Japanese cuts.** Uploading the
transcripts is what unlocks auto-translate and is the step most easily skipped once the video
looks finished. English first means layout faults surface in the language you can judge
fastest, before the other language is built on the same geometry.

## Setup

Machine setup lives in `install.md` (deps, ffmpeg, API key). This skill is vendored and heavily
modified — **never re-clone or pull it from `browser-use/video-use`**; that overwrites work that
exists only here. Don't re-run setup every session; on cold start just verify:

- `ELEVENLABS_API_KEY` resolves — either in the environment or in `.env` in this skill directory. If missing, ask the user to paste one and write it to `.env` (never to the user's `<videos_dir>`).
- `ffmpeg` + `ffprobe` on PATH.
- Python deps installed (`uv sync` or `pip install -e .` inside the repo).
- Node.js + npm available if the session needs HyperFrames or Remotion slots. HyperFrames currently requires Node.js 22+.
- `yt-dlp`, HyperFrames, Remotion, Manim installed only on first use.
- First-use animation setup happens inside the slot directory, never at this skill's own root. HyperFrames can be invoked with `npx --yes hyperframes ...`; Remotion can be scaffolded with `npx create-video@latest` or installed as a project-local dependency before using its `remotion render` command.
- For Manim, use the `factory-manim-video` skill (ships alongside this one) when building a Manim slot — read its SKILL.md for the full pipeline (creative planning, code generation, rendering, iteration).

Helpers (`helpers/transcribe.py`, `helpers/render.py`, etc.) live alongside this SKILL.md. Resolve their paths relative to the directory containing this file — this skill may also be worked on in git worktrees, so never hardcode an absolute path to it.

## Helpers

- **`transcribe.py <video>`** — single-file Scribe call. `--num-speakers N` optional. Cached.
- **`transcribe_batch.py <videos_dir>`** — 4-worker parallel transcription. Use for multi-take.
- **`transcribe_local.py <video>`** — local faster-whisper fallback when there's no `ELEVENLABS_API_KEY`. Word-level, verbatim-biased, GPU if available. Same JSON schema. Prefer Scribe when a key exists.
- **`transcribe_runs.py <video>`** — silence-segmented batch transcription. `silencedetect` partitions the timeline into speech runs with exact boundaries; each run is transcribed in parallel. Writes `<name>.runs.json`. The right transcriber for take-structured recordings. See *Retake markers* below.
- **`broll_cards.py <spec.json>`** — build source-screenshot cards and composite them onto a finished cut. See *B-roll from real sources* below.
- **canvas rebuild in another language** — see *Rebuilding the on-screen canvas in another language* below for the full technique; `canvas_swap.py` + `canvas_camera_example.py` are the starting point for your own per-project camera/render scripts.
- **`shoot_scene.py <scene.html> <out.mp4>`** — frame-grab a deterministic scene and encode it. `--query s=<archetype>`. Templates in `scenes/`.
- **`make_short.py`** — cut a vertical 1080x1920 short with a voiced hook, animated captions and a CTA. See *Shorts* below.
- **`canvas_swap.py`** + **`canvas_camera_example.py`** — re-render a screencast over the same board in another language. See *Rebuilding the on-screen canvas in another language*.
- **`dub.py <cmd> --edit-dir DIR`** — voice-clone dubbing: `samples`, `clone`, `blocks`, `synth`, `build`, `srt`. See *Dubbing with a cloned voice* below.
- **`tighten.py <video> --edl <out>`** — filler removal + silence tightening. Cuts "um"/"uh", trims long pauses, drops explicit ranges (`--drop A-B`) and a dead tail (`--keep-until T`). See *Tightening* below.
- **`pack_transcripts.py --edit-dir <dir>`** — `transcripts/*.json` → `takes_packed.md` (phrase-level, break on silence ≥ 0.5s).
- **`timeline_view.py <video> <start> <end>`** — filmstrip + waveform PNG. On-demand visual drill-down. **Not a scan tool** — use it at decision points, not constantly.
- **`render.py <edl.json> -o <out>`** — per-segment extract → concat → overlays (PTS-shifted) → subtitles LAST. `--preview` for 720p fast. `--build-subtitles` to generate master.srt inline.
- **`grade.py <in> -o <out>`** — ffmpeg filter chain grade. Presets + `--filter '<raw>'` for custom.

For animations, create `<edit>/animations/slot_<id>/` with `Bash` and spawn a sub-agent via the `Agent` tool.

## The process

1. **Inventory.** `ffprobe` every source. `transcribe_batch.py` on the directory. `pack_transcripts.py` to produce `takes_packed.md`. Sample one or two `timeline_view`s for a visual first impression.
2. **Pre-scan for problems.** One pass over `takes_packed.md` to note verbal slips, obvious mis-speaks, or phrasings to avoid. Plain list, feed into the editor brief.
3. **Converse.** Describe what you see in plain English. Ask questions *shaped by the material*. Collect: content type, target length/aspect, aesthetic/brand direction, pacing feel, must-preserve moments, must-cut moments, animation and grade preferences, subtitle needs. Do not use a fixed checklist — the right questions are different every time.
4. **Propose strategy.** 4–8 sentences: shape, take choices, cut direction, animation plan, grade direction, subtitle style, length estimate. **Wait for confirmation.**
5. **Execute.** Produce `edl.json` via the editor sub-agent brief. Drill into `timeline_view` at ambiguous moments. Build animations in parallel sub-agents. Apply grade per-segment. Compose via `render.py`.
6. **Preview.** `render.py --preview`.
7. **Self-eval (before showing the user).** Run `timeline_view` on the **rendered output** (not the sources) at every cut boundary (±1.5s window). Check each image for:
   - Visual discontinuity / flash / jump at the cut
   - Waveform spike at the boundary (audio pop that slipped past the 30ms fade)
   - Subtitle hidden behind an overlay (Rule 1 violation)
   - Overlay misaligned or showing wrong frames (Rule 4 violation)

   Also sample: first 2s, last 2s, and 2–3 mid-points — check grade consistency, subtitle readability, overall coherence. Run `ffprobe` on the output to verify duration matches the EDL expectation.

   If anything fails: fix → re-render → re-eval. **Cap at 3 self-eval passes** — if issues remain after 3, flag them to the user rather than looping forever. Only present the preview once the self-eval passes.
8. **Iterate + persist.** Natural-language feedback, re-plan, re-render. Never re-transcribe. Final render on confirmation. Append to `project.md`.

## Cut craft (techniques)

- **Audio-first.** Candidate cuts from word boundaries and silence gaps.
- **Preserve peaks.** Laughs, punchlines, emphasis beats. Extend past punchlines to include reactions — the laugh IS the beat.
- **Speaker handoffs** benefit from air between utterances. Common values: 400–600ms. Less for fast-paced, more for cinematic. Taste call.
- **Audio events as signals.** `(laughs)`, `(sighs)`, `(applause)` mark beats. Extend past them.
- **Silence gaps are cut candidates.** Silences ≥400ms are usually the cleanest. 150–400ms phrase boundaries are usable with a visual check. <150ms is unsafe (mid-phrase).
- **Example cut padding** (the launch video shipped with this): 50ms before the first kept word, 80ms after the last. Tighter for montage energy, looser for documentary. Stay in the 30–200ms working window (Hard Rule 7).
- **Never reason audio and video independently.** Every cut must work on both tracks.

## The packed transcript (primary reading view)

`pack_transcripts.py` reads all `transcripts/*.json` and produces one markdown file where each take is a list of phrase-level lines, each prefixed with its `[start-end]` time range. Phrases break on any silence ≥ 0.5s OR speaker change. This is the artifact the editor sub-agent reads to pick cuts — it gives word-boundary precision from text alone at 1/10 the tokens of raw JSON.

Example line:
```
## C0103  (duration: 43.0s, 8 phrases)
  [002.52-005.36] S0 Ninety percent of what a web agent does is completely wasted.
  [006.08-006.74] S0 We fixed this.
```

## Tightening (filler removal, dead air, asides)

The most common ask on a single-take talking-head recording: strip the "um"s, kill the dead
air, cut the bits where the speaker breaks character ("let me pull up my notes"), and drop a
tail that got interrupted. `tighten.py` does all four by subtracting intervals from the
timeline and emitting an EDL.

**Never pick an absolute dB threshold.** This is the mistake that ruins these edits. A fixed
`silencedetect=noise=-35dB` sounds conservative and is not: measured against a recording whose
noise floor is -87dB and speech level -29dB, it treats every word's decay tail as silence, and
*81 of 118 cuts landed inside a word*. Measure the floor and speech level, then derive
thresholds **relative to speech**: ~22dB down is a real inter-word pause, and anything within
15dB of speech level at a boundary is a truncated word.

**Expand outward through contiguous silence; never search a window for the local minimum.**
A windowed search finds the quietest point nearby — which is frequently on the *far side of
the next word*. That point is genuinely silent, so the cut sounds clean, but every word in
between is deleted: "…the regular stock market" silently becomes "…the regular stock". Walking
outward frame by frame cannot jump a word, because the word's own energy halts the walk.

**When an edge lands in speech, retreat inward — but not past the word you are removing.**
ASR word boundaries are routinely 300ms out, so a hand-typed or transcript-derived edge often
starts mid-vowel. Retreating inward to the next quiet frame keeps more audio and never
truncates. Bound that retreat to the first removed word's own span, or it skips whole words
and strands them in the output ("…stock market, let me, there's a bit…").

**Guard every cut, however derived**: if either edge sits above the clipping threshold, drop
the cut entirely. Leaving a filler in is always better than truncating a word.

**Expect most fillers to survive, and say so.** A speaker who says "a lot of, uh, lot going on"
without pausing gives you nothing to cut into. On real material this can be 60+ of 64 fillers.
That is the honest answer, not a bug — `--filler-pause` trades it off (lower = more fillers
cut, more splice artefacts) but there is no setting that removes an embedded filler cleanly
with a butt cut. Crossfades are the only real fix, and this pipeline's lossless concat
cannot do them.

**Trim long pauses, don't eliminate them.** `--gap-threshold 0.55` leaves shorter pauses alone;
they are speech rhythm. A recording with every gap removed sounds like a ransom note.

**Verify by transcribing the whole rendered output and diffing it against the plan.** Not a
few sample joins — the whole thing. Build the expected word list from the source transcript
filtered to the kept ranges, then `difflib` it against a fresh transcript of the render.
Discount fillers and the speaker's own stutters; what remains are real losses. A per-boundary
energy report (`CUT-QUALITY`) is the fast proxy, but the diff is the proof.

## B-roll from real sources (screenshot cards)

Cutting a commentary video against nothing but the speaker's screen wastes the claims they
make. Every named figure — an earnings number, a policy decision, a statistic — is a place a
real source can go on screen. `broll_cards.py` takes browser screenshots and burns them in as
consistent centred cards.

**Work in the language the video will be delivered in.** If it is being dubbed to Japanese,
the sources must be Japanese — an English headline under a Japanese dub reads as a mistake.
Ask which language ships before researching anything.

**The flow:**

1. **Read the transcript with timestamps** and list the checkable claims. Roughly one card
   per named figure or event; ~1 per 90s of runtime is a comfortable density.
2. **Research each claim in the browser and fact-check it as you go.** This is the step that
   earns its keep — see below.
3. **Screenshot with `save_to_disk` and crop precisely afterwards.** Do not rely on the
   browser's zoom-to-region: it re-renders at a different scale and clips text. Take the full
   viewport, crop with PIL.
4. **Build and composite** via `broll_cards.py spec.json`.
5. **Verify frames at the start *and end* of every window**, not just the middle.

**Fact-check while you research, and report what you find.** Real material from a live
recording will contain errors, and a dub makes them permanent. Expect to find figures that
are off by an order of magnitude ("1.8 times" narrated as "1.8 trillion"), levels that moved
after recording, and causes attributed differently by the source than by the speaker. Never
quietly pick a screenshot that agrees with the narration when the source disagrees — an
overlay that contradicts the voiceover is worse than no overlay. Surface the mismatch and let
the user choose: re-record, drop the card, or keep the take with a `correction` caption.

**Never overlay a screenshot of something already on screen.** If the speaker navigates to
the page they are plugging, a card of that same page covers the real thing with a picture of
it. Check the underlying frames before placing product or website cards, and move them to a
moment where the screen shows something else.

**Crop out account chrome.** Logged-in dashboards leak avatars, usernames, ADMIN menus, and
personalised panels. Crop them out before the screenshot becomes a published frame.

**Sizing and placement.** Cards are capped at 70% frame width / 69% height *before* the drop
shadow, which keeps a real margin on every side at any frame size. Centre them; a card that
touches an edge reads as a mistake. Hold 8s by default — long enough to read a Japanese
headline and glance at a number. 4s is too short for anything with text in it.

**Official sources beat news sites** where one exists: ministry statements and statistics
bureau tables are clean, uncluttered, paywall-free, and carry more authority on screen. Watch
for cookie banners; an exchange's own explainer page is often background prose with no
figures on it, in which case use a news source instead.

## Dubbing with a cloned voice

Replacing a finished cut's audio with a scripted translation, spoken in a clone of the
speaker's own voice, locked to the original edit. `dub.py` runs the whole pipeline.

**Script it; don't auto-dub.** Hosted auto-dubbing runs its own ASR and MT, so the speaker's
false starts and abandoned clauses get translated literally. That is worse in a verb-final
language: an abandoned English clause has usually delivered subject and verb already, but an
abandoned Japanese clause often hasn't reached the verb, so it carries no meaning at all.
MT then invents one. Scripting also lets the dub **correct** figures the speaker misstated,
which is what you want when the video shows the real number on screen.

**The dubbing slider is not a translation control.** ElevenLabs' "speaker similarity" only
governs how closely the cloned voice mimics the original timbre and accent — high values
carry the source accent into the target language. It changes nothing about the words. For a
target-language audience, low is right.

**Per-block re-anchoring is the timing model.** Split the cut into blocks at real pauses,
synthesise each independently, and fit each to *its own* window. A block that lands short
never pushes the next one, so error cannot accumulate over 15 minutes. Force a seam just
before every on-screen card (`--anchors`) so the dub is always on-topic while a graphic is up.

**Fit order, least destructive first:** place as-is if within tolerance → absorb up to
`--pad-allow` of shortfall as silence at the block tail (it was a real pause anyway) →
atempo, capped ±12% → otherwise report and rewrite the text. Stretching is the fallback,
never the fix. Tune `--pad-allow` by measuring: dropping it from 0.80 to 0.45 on a real cut
took gaps over 1.0s from 28 down to 7.

**Blocks that overrun are the dangerous case.** The fitter's `-t target` *truncates*, so a
block at 118% loses its final words. Always fix those by shortening the target text; never by
raising the tempo cap.

**There is no usable chars-per-second constant.** Measured rates on one recording ranged
**5.3 to 9.0 chars/sec** — prose runs fast, dates and figures run slow, and adding a single
sentence-ending mark swung one block from 9.0 to 6.1. The loop that works is: draft → synth →
measure → rewrite against *that block's own* measured rate → re-synth. Budget three passes.

**Voice cloning is free and permanent — save the `voice_id`.** Instant cloning wants a few
minutes of clean speech; density beats length, so `dub.py samples` picks the windows with the
highest speech coverage, spread across the cut. Never re-clone for a later episode.

**Keep the speaker's verbal tics.** Scrubbing every filler out of the target script makes it
read as written prose rather than speech. If the source says "pretty much" constantly, the
target should have an equivalent tic at a similar rate.

**Run a de-AI pass on the target script** (run the `factory-humanizer` skill in that language). On a
real script this caught: one connective opening ten consecutive sentences, one sentence-ending
form used seven times, a textbook AI intensifier, and eight near-identical variants of "this
is worth watching". Constrain the rewrite to ±8% length or it breaks the timing fit.

**Captions come from the block script, not a re-transcription.** Each block's audio was fitted
to fill its window, so distributing its text across that window by character count lands
within a few hundred ms. `dub.py srt` does this, and it guarantees the captions match the
spoken script exactly — including corrections.

**Cost, for calibration:** a 15-minute dub including three retune passes was ~8,400 credits
(a few dollars), against ~45,000 credits for hosted auto-dubbing of the same runtime.

## Publishing to YouTube

**The browser bridge caps file uploads at 10 MB.** Thumbnails and caption files go through
`file_upload` fine; a 58 MB video does not. Hand the video off to the user to select, then
take over the metadata. Do not build workarounds unless asked.

**`127.0.0.1` and `localhost` are different entries** in the Chrome extension's site
permissions. If a local URL is refused, try the other spelling before concluding it's blocked.

**Switch channel before anything else.** Avatar → Switch account. Confirm the channel name in
the sidebar; a video published to the wrong channel is a real mess to undo.

**Typing long text into the form is error-prone.** Synthesised keystrokes dropped a digit in a
figure that had been carefully verified three times over. Read the field back and diff it
against the source before moving on, or paste instead.

**Defaults that are usually wrong:** Category lands on "People & Blogs"; video language is
unset. Set both.

**Chapter rules:** first must be `00:00`, at least three, at least 10s apart, and the last at
least 10s before the end. Derive them from real section boundaries, not round numbers.

**Auto-translate needs *published* captions in the original language.** YouTube's
auto-generated captions do not qualify — the option stays greyed out with an unhelpful
tooltip. Upload a real caption track to the "(video language)" row and publish it.

**Publishing is irreversible and outward-facing.** Walk the whole flow, stop at the visibility
step, and get explicit confirmation before clicking Publish. "Made for kids" is a legal
declaration — the user answers that, not you.

### Thumbnails from a live page

**The screenshot capture is a fixed size regardless of window size** (~1568×765 here), so the
canvas is wider than 16:9 and something must give. Cropping to 16:9 costs real content;
extending the page's own background colour vertically costs nothing and reads as more canvas
rather than letterboxing. Sample the background rather than assuming white.

**Hide app chrome surgically.** Hiding a broad set of selectors caught a parent and blanked
the canvas. For Excalidraw, hiding only `.layer-ui__wrapper` removes toolbar, zoom, and
library while leaving the drawing intact.

**Park the mouse somewhere that gets cropped** before capturing — the cursor renders into the
screenshot, and it landed in the middle of a chart on the first attempt. Detect and trim any
page bars by scanning for non-background rows rather than hardcoding an offset.

## Rebuilding the on-screen canvas in another language

When the recording is a screencast of a whiteboard/canvas that exists in a second language,
the whole screen can be replaced while keeping the original narration and webcam. Worked
end-to-end on a 15-minute Excalidraw recap.

**Capture the target board as one big image, deterministically.** Excalidraw restores
`scrollX/scrollY/zoom` from `localStorage` on load, so setting that state and reloading gives
exact, repeatable tiles — far better than trying to drive pan gestures. Read the scene JSON
first (`localStorage.excalidraw`) to get the element bounding box, then tile across it and
stitch. Hide only `.layer-ui__wrapper`; broader selector sets catch a parent and blank the
canvas. **Record the canvas rect per tile** — its CSS height can change between calls and
mismatched rows leave gaps.

**Do not try to pixel-track the viewport and reuse the transform.** It fails for a real
reason: two translations of the same board share section *order* but not *coordinates*,
because text extents differ, so everything below the first section shifts. Template matching
(on a colour-ink mask — text differs across languages, coloured shapes don't) locks onto the
right section but the wrong offset. There is no single scale+translate mapping one board to
the other.

**Drive the camera from the transcript instead.** The block table already says what is being
discussed each second, so assign each block a named region of the target board and ease
between them. This is what a human editor does, and it is immune to layout drift.

**Frame it like the original.** Compute the width the original actually showed —
`video_width / (video_px per scene unit)` — and use that. On the reference run the original
showed ~1700 board-px; an early guess of 820 looked absurdly zoomed in. One constant
(`VIEW_W`) controls the zoom of the entire video.

**Hold static, move only at seams.** Emit two keyframes per block (start and end) with the
same rect, so the camera is motionless while a section is discussed and travels only at the
handover. Drifting or pushing over a dense board just makes it hard to read.

**Lift the webcam straight from the source frames — and mind the frame rate.** Reading one
source frame per output frame silently plays the inset at `src_fps / out_fps` speed: 60->30
is half speed, starting in sync and ending minutes behind. Advance `src_fps / out_fps` source
frames per output frame. **Verify by differencing the composited inset against the source
frame it came from** at several timestamps; a mean pixel difference in the single digits is
sync, anything larger is drift. This check is cheap and catches the whole class of bug. Find its rectangle by temporal variance over consecutive frames rather than by
eye. Re-composite any overlay cards afterwards, against the rebuilt video.

**Speed changes come last.** `setpts=PTS/N` + `atempo=N` (pitch-preserving). Scale card start
times by `1/N` but keep their durations — a card sped up is not easier to read, so an 8s hold
must still be 8s in the delivered file. Divide chapter timestamps by N too.

## Shorts (vertical clips from a finished cut)

The last stage after both language versions are published: 3-6 clips per language, each
under 60s, cut from the finished videos. `make_short.py` renders one.

**Rebuild the frame; never centre-crop.** A 16:9 screencast cropped to 9:16 loses the
graphic's outer thirds and buries the speaker. Lift each element and re-seat it: headline
plus logo on top, the graphic in the middle, the webcam full-bleed across the bottom third
where a phone viewer looks, captions between.

**The graphic is the point — frame it deliberately.** Grid-probe a source frame (draw
labelled 100px gridlines over it and read off the rect) so the crop lands on one complete
graphic. A panel that clips its neighbours, or cuts its own title, reads as careless. Give
the board panel real height; legibility comes from the crop being close to the graphic's own
aspect, not from output resolution.

**Open with a voiced hook in a different voice.** ~2-3s of a narrator voice — *not* the
speaker's — asking the question the clip answers, over a blurred and dimmed first frame,
source audio muted. This is what makes a clip self-contained: no surrounding context needed.
Lead with a number rather than an adjective ("Toyota made 1.48 trillion yen" beats "record
profits"), and land it inside the first three seconds.

**Localise the hook's framing, not just its language.** An English hook for foreign-market
content needs the geography stated ("In Japan, wages are up"); the native-language version
can leave it implied, because the audience already knows where they are.

**Set the hook as huge type revealing with the voiceover**, word by word, filling the screen.

**Snap both ends to phrase boundaries.** Starting mid-clause loses the viewer and ending
mid-sentence reads as broken. Snap the end *inward* when a total is near the 60s ceiling —
snapping to the nearest boundary can push you over.

**Caption styling is what separates "made for the feed" from "default".** Heavy black stroke
(~12px) around white text, active word in an accent colour, upper-case for latin scripts,
few words on screen at once. The stroke matters more than the font.

**Match assets to language.** Check that a clip does not contain a burned-in card in the
other language; move the clip range rather than shipping the mismatch.

**Close with a CTA card** pointing at the full recap.

**The webcam inset has a hard resolution ceiling** set by the original capture — a 295x168
inset in a 720p recording cannot fill a 1080-wide frame sharply. Diagnose it before promising
a fix, and if the capture is the limit, say so and fix it at record time.

### Purpose-built scene animation (replacing a screen-recorded board)

Instead of filming a whiteboard and panning over it, render the explainer itself. Prototype your
own scene HTML files alongside `scenes/chassis.js`, rendered with `helpers/shoot_scene.py` /
`helpers/shoot_sequence.py` (the frame grabbers below).

**Render contract: every scene is a pure function of `window.__render(t)`.** No
requestAnimationFrame, no internal clock. Playwright seeks to an exact time and screenshots,
so captures never race the animation and the output is reproducible. It also means the beat
sheet can be driven from `blocks.json`, so an element appears exactly when the speaker names
it — that is the whole point of "explain it while I'm saying it".

**Author vertical first when the target is shorts.** A 16:9 scene re-composed to 9:16 wastes
the format. 1080x1920 native.

**A labelled box communicates nothing.** This was the biggest failure: five glass cards
reading YEN BUYING / DOLLAR RESERVES / SELL TREASURIES down a diagonal taught the viewer five
nouns and zero relationships. Two rules fix it:

- **The arrows carry the argument.** Label every edge with the causal verb — "but it needs
  dollars", "so it must sell", "which lifts", "so instead". Read the connectors alone and the
  whole explanation should hold.
- **Every node carries a graphic of the quantity**, drawn live: a reserve draining, a bond
  stack losing slabs, a yield curve steepening, a loop returning to the stack. The state must
  be visible before the text is read.

Colour does semantic work — red where it hurts, accent on the resolution — never decoration.

**Offer structurally different directions, not palettes.** Three colourways of one chart is
one direction. Genuinely different means: chart-led (data is the interface), kinetic type (no
chart, the numbers are the visual), mechanism graph (the causal chain). Mechanism scales best
for explainer content because most explanations are chains; chart and kinetic are single-fact
formats.

**Shaders are cheap and worth it.** A GLSL fBm bed with a dither term (kills banding) plus
hand-built frosted panels — layered gradient fills, hairline border, clipped to a rounded
rect — gets the shadergradient/liquid-glass look with no dependencies.

**Fake data reads as fake.** A price line built from a sine wave is instantly wrong; use a
seeded momentum walk and pin it to the real endpoints.

**Split the chassis from the episode.** `scenes/chassis.js` holds everything that must NOT
change between videos — frame contract, palette, `panel()` brackets, `graticule()`, the rail,
type helpers, and `mount()`. Each episode gets its OWN html file that includes the chassis and
defines only its own scenes:

    scenes/chassis.js                 the brand. Shared. Rarely edited.
    scenes/scene-<episode-a>.html     EPISODE: e.g. "2026-01-05-launch"
    scenes/scene-<episode-b>.html     EPISODE: e.g. "2026-01-12-earnings"
    scenes/sequence-<name>.json       spans + `scene_file` naming its episode html

This is the factoring that makes "unique per video" cheap instead of tempting to skip: sharing
identity costs nothing, and there is no shared scene table to raid. `shoot_sequence.py` reads
`scene_file` from the sequence JSON so a sequence can never be pointed at the wrong episode.
Never edit the chassis to make one episode work; never import another episode's scenes.

Render a single scene with
`helpers/shoot_scene.py <episode.html> out.mp4 --dur 9 --w 1080 --h 1920 --query s=chain`,
or the whole clip with `helpers/shoot_sequence.py scenes/sequence-<name>.json out.mp4`.

**Build the visuals for THIS video. Never ship the same graphics twice.**

This is the most important rule in the section and the one most easily got wrong. The archetype
list below is a way of *thinking* about what a claim needs — it is not a catalogue to pick from.
Two failures happen when it is treated as a catalogue:

1. **Off-topic content.** A "contradiction" scene about Toyota dropped into a segment about
   household spending fits the shape and communicates nothing — worse, it misleads, because the
   viewer trusts that what is on screen is what is being discussed.
2. **Sameness.** If every episode gets the same four scenes with the numbers swapped, the
   channel looks templated and the visuals stop carrying information. Each episode's graphics
   should be recognisably *about that week*.

So: read the transcript for the clip, list what is actually claimed in each stretch, and design
a visual for each claim. Reach for an existing archetype only when it genuinely fits the claim,
and expect to build new ones — a threshold being crossed, a proportion flowing between two
parties, one number given physical scale, a sequence collapsing. The kit grows every episode.

**Translating an episode is not reusing it.** "Build fresh per video" is about *content*, so
the boundary is the episode, not the file. The Japanese dub of an episode argues exactly the
same thing in the same order — it gets the SAME scenes with translated copy, re-timed to the
dub's own word timings, because the dub is a different performance with different pacing. A
*different* episode gets new scenes even if its argument rhymes with a previous one. Shipping
the EN and JA cuts of one week with different visuals would be a bug, not variety.

**Organise the thinking by SHAPE OF ARGUMENT, not by topic.** A presenter makes a handful of
recurring rhetorical moves; naming them helps you spot what a claim needs:
  * `bars`   — "everyone expected X, it came in Y"  (a miss against forecast)
  * `index`  — "a population shrinks"               (N of M things leave)
  * `split`  — "two true things that can't both last" (a contradiction)
  * `flow`   — "A forces B forces C"                 (a causal chain)
  plus: a level breaking, and one number given physical scale.
Naming the move tells you what the visual has to *do*. It does not tell you what to draw — that
comes from the claim itself, and usually means a new scene. Treat a returning archetype as a
starting geometry to depart from, never as a finished scene waiting for new numbers.

**Fixed frame contract** so the art never has to dodge the speaker:
  * bottom rail = 15% of height; logo cell left, speaker cell right
  * the logo sits hard-left in its cell with text starting after it — centring both in the
    same cell makes them collide
  * art area is everything above the rail; expose the speaker rect (`window.__SPEAKER_BOX`)
    so the compositor knows where to paste the real webcam

**Pull brand tokens from the product, not from taste** — but expect the client to have a
register in mind that the tokens don't capture. On one project, the design system's own CSS gave
cream on near-black and a gold accent, which beat generic cyan-on-black but still read as a
product UI. What actually landed was pure black FUI (below). Tokens tell you the hues; they say
nothing about temperature, fill discipline, or numeral treatment. Ask for screenshots.

**Match the animation to the clip, not to a default.** A scene rendered at a fixed 7-9s
against a 48s clip is obviously wrong. Scene length comes from the transcript span it covers.

**One clip usually needs SEVERAL scenes.** A 40-60s short makes three or four points; give
each its own scene and sequence them. One scene per short wastes the format.

**Status: promising, not there yet.** Direction of travel confirmed as vertical and more
diagrammatic. Still open: making each scene genuinely communicate at a glance, and wiring the
beat sheet to real transcript timings.

## Editor sub-agent brief (for multi-take selection)

When the task is "pick the best take of each beat across many clips," spawn a dedicated sub-agent with a brief shaped like this. The structure is load-bearing; the pitch-shape example is not.

```
You are editing a <type> video. Pick the best take of each beat and 
assemble them chronologically by beat, not by source clip order.

INPUTS:
  - takes_packed.md (time-annotated phrase-level transcripts of all takes)
  - Product/narrative context: <2 sentences from the user>
  - Speaker(s): <name, role, delivery style note>
  - Expected structure: <pick an archetype or invent one>
  - Verbal slips to avoid: <list from the pre-scan pass>
  - Target runtime: <seconds>

Common structural archetypes (pick, adapt, or invent):
  - Tech launch / demo:   HOOK → PROBLEM → SOLUTION → BENEFIT → EXAMPLE → CTA
  - Tutorial:             INTRO → SETUP → STEPS → GOTCHAS → RECAP
  - Interview:            (QUESTION → ANSWER → FOLLOWUP) repeat
  - Travel / event:       ARRIVAL → HIGHLIGHTS → QUIET MOMENTS → DEPARTURE
  - Documentary:          THESIS → EVIDENCE → COUNTERPOINT → CONCLUSION
  - Music / performance:  INTRO → VERSE → CHORUS → BRIDGE → OUTRO
  - Or invent your own.

RULES:
  - Start/end times must fall on word boundaries from the transcript.
  - Pad cut boundaries (working window 30–200ms).
  - Prefer silences ≥ 400ms as cut targets.
  - Unavoidable slips are kept if no better take exists. Note them in "reason".
  - If over budget, revise: drop a beat or trim tails. Report total and self-correct.

OUTPUT (JSON array, no prose):
  [{"source": "C0103", "start": 2.42, "end": 6.85, "beat": "HOOK",
    "quote": "...", "reason": "..."}, ...]

Return the final EDL and a one-line total runtime check.
```

## Color grade (when requested)

Your job is to **reason about the image**, not apply a preset. Look at a frame (via `timeline_view`), decide what's wrong, adjust one thing, look again.

Mental model is ASC CDL. Per channel: `out = (in * slope + offset) ** power`, then global saturation. `slope` → highlights, `offset` → shadows, `power` → midtones.

**Example filter chains** (`grade.py` has `--list-presets`; use them as starting points or mix your own):

- **`warm_cinematic`** — retro/technical, subtle teal/orange split, desaturated. Shipped in a real launch video. Safe for talking heads.
- **`neutral_punch`** — minimal corrective: contrast bump + gentle S-curve. No hue shifts.
- **`none`** — straight copy. Default when the user hasn't asked.

For anything else — portraiture, nature, product, music video, documentary — invent your own chain. `grade.py --filter '<raw ffmpeg>'` accepts any filter string.

Hard rules: apply **per-segment during extraction** (not post-concat, which re-encodes twice). Never go aggressive without testing skin tones.

## Subtitles (when requested)

Subtitles have three dimensions worth reasoning about: **chunking** (1/2/3/sentence per line), **case** (UPPER/Title/Natural), and **placement** (margin from bottom). The right combo depends on content.

**Worked styles** — pick, adapt, or invent:

**`bold-overlay`** — short-form tech launch, fast-paced social. 2-word chunks, UPPERCASE, break on punctuation, Helvetica 18 Bold, white-on-outline, `MarginV=35`. `render.py` ships with this as `SUB_FORCE_STYLE`.

```
FontName=Helvetica,FontSize=18,Bold=1,
PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BackColour=&H00000000,
BorderStyle=1,Outline=2,Shadow=0,
Alignment=2,MarginV=35
```

**`natural-sentence`** (if you invent this mode) — narrative, documentary, education. 4–7 word chunks, sentence case, break on natural pauses, `MarginV=60–80`, larger font for readability, slightly wider max-width. No shipped force_style — design one if you need it.

Invent a third style if neither fits. Hard rules: subtitles LAST (Rule 1), output-timeline offsets (Rule 5).

## Animations (when requested)

Animations match the content and the brand. **Get the palette, font, and visual language from the conversation** — never assume a default. If the user hasn't told you, propose a palette in the strategy phase and wait for confirmation before building anything.

**Tool options:**

Pick the engine per animation slot. Do not default to Remotion just because the animation is web-adjacent.

- **HyperFrames** — Browser-native HTML/CSS/GSAP video compositions: product UI motion, website-to-video or mockup-to-video captures, kinetic typography, landing-page/storyboard promos, data-driven UI states, transparent WebM overlays, and clips that need deterministic frame capture plus HyperFrames lint/validate/render checks. Best when the animation should be authored and verified like a web composition instead of a React component tree.
- **Remotion** — React/CSS compositions with component state, reusable React primitives, or an existing Remotion brand system. Best when the user specifically asks for React/Remotion or when React composition is the simpler authoring model.
- **Manim** — formal diagrams, state machines, equation derivations, graph morphs. Use the `factory-manim-video` skill for the full pipeline — same rule as under Setup above.
- **PIL + PNG sequence + ffmpeg** — simple overlay cards: counters, typewriter text, single bar reveals, progressive draws. Fast to iterate, any aesthetic you want. The launch video used this.

For HyperFrames slots, scaffold the slot inside `edit/animations/slot_<id>/` with `npx --yes hyperframes init . --example blank --non-interactive --skip-skills`, build the HTML composition there, run the HyperFrames checks that fit the slot (`lint`, `validate`, and a draft render when practical), then produce the final overlay video with `npx --yes hyperframes render . -o render.mp4` or `--format webm -o render.webm` when alpha is required. Point the EDL overlay `file` at the actual rendered path.

For Remotion slots, keep the Remotion project isolated inside the same slot directory, scaffold with `npx create-video@latest` or install Remotion locally there, render the composition to `render.mp4` with the project-local `remotion render` command, and verify duration and dimensions with `ffprobe`.

None is mandatory. Invent hybrids if useful (e.g., PIL background with a HyperFrames or Remotion layer on top).

**Duration rules of thumb, context-dependent:**

- **Sync-to-narration explanations.** A viewer needs to parse the content at 1×. Rough floor 3s, typical 5–7s for simple cards, 8–14s for complex diagrams. The launch video shipped at 5–7s per simple card.
- **Beat-synced accents** (music video, fast montage). 0.5–2s is fine — they're visual accents, not information. The "readable at 1×" rule becomes *"recognizable at 1×"*, not *"fully parseable."*
- **Hold the final frame ≥ 1s** before the cut (universal).
- **Over voiceover:** total duration ≥ `narration_length + 1s` (universal).
- **Never parallel-reveal independent elements** — the eye can't track two new things at once. One thing, pause, next thing.

**Animation payoff timing (rule for sync-to-narration):** get the payoff word's timestamp. Start the overlay `reveal_duration` seconds earlier so the landing frame coincides with the spoken payoff word. Without this sync the animation feels disconnected.

**Easing** (universal — never `linear`, it looks robotic):

```python
def ease_out_cubic(t):    return 1 - (1 - t) ** 3
def ease_in_out_cubic(t):
    if t < 0.5: return 4 * t ** 3
    return 1 - (-2 * t + 2) ** 3 / 2
```

`ease_out_cubic` for single reveals (slow landing). `ease_in_out_cubic` for continuous draws.

**Typing text anchor trick:** center on the FULL string's width, not the partial-string width — otherwise text slides left during reveal.

**Example palette** (the launch video — one aesthetic among infinite):
- Background `(10, 10, 10)` near-black
- Accent `#FF5A00` / `(255, 90, 0)` orange
- Labels `(110, 110, 110)` dim gray
- Font: Menlo Bold at `/System/Library/Fonts/Menlo.ttc` (index 1)
- ≤ 2 accent colors, ~40% empty space, minimal chrome
- Result: terminal / retro tech feel

This is one style. If the brand is warm and serif, use that. If it's colorful and playful, use that. If the user handed you a style guide, follow it. If they didn't, propose one and confirm.

**Parallel sub-agent brief** — each animation is one sub-agent spawned via the `Agent` tool. Each prompt is self-contained (sub-agents have no parent context). Include:

1. One-sentence goal: *"Build ONE animation: [spec]. Nothing else."*
2. Absolute output path (`<edit>/animations/slot_<id>/render.mp4`)
3. Exact technical spec: resolution, fps, codec, pix_fmt, CRF, duration
4. Style palette as concrete values (RGB tuples, hex, or reference to a design system)
5. Font path with index
6. Frame-by-frame timeline (what happens when, with easing)
7. Anti-list ("no chrome, no extras, no titles unless specified")
8. Code pattern reference (copy helpers inline, don't import across slots)
9. Deliverable checklist (script, render, verify duration via ffprobe, report)
10. **"Do not ask questions. If anything is ambiguous, pick the most obvious interpretation and proceed."**

One sub-agent = one file (unique filenames, parallel agents don't overwrite each other).

## Output spec

Match the source unless the user asked for something specific. Common targets: `1920×1080@24` cinematic, `1920×1080@30` screen content, `1080×1920@30` vertical social, `3840×2160@24` 4K cinema, `1080×1080@30` square. `render.py` defaults the scale to 1080p from any source; pass `--filter` or edit the extract command for other targets. Worth asking the user which delivery format matters.

## EDL format

```json
{
  "version": 1,
  "sources": {"C0103": "/abs/path/C0103.MP4", "C0108": "/abs/path/C0108.MP4"},
  "ranges": [
    {"source": "C0103", "start": 2.42, "end": 6.85,
     "beat": "HOOK", "quote": "...", "reason": "Cleanest delivery, stops before slip at 38.46."},
    {"source": "C0108", "start": 14.30, "end": 28.90,
     "beat": "SOLUTION", "quote": "...", "reason": "Only take without the false start."}
  ],
  "grade": "warm_cinematic",
  "overlays": [
    {"file": "edit/animations/slot_1/render.mp4", "start_in_output": 0.0, "duration": 5.0}
  ],
  "subtitles": "edit/master.srt",
  "total_duration_s": 87.4
}
```

`grade` is a preset name or raw ffmpeg filter. `overlays` are rendered animation clips. `subtitles` is optional and applied LAST.

## Memory — `project.md`

Append one section per session at `<edit>/project.md`:

```markdown
## Session N — YYYY-MM-DD

**Strategy:** one paragraph describing the approach
**Decisions:** take choices, cuts, grades, animations + why
**Reasoning log:** one-line rationale for non-obvious decisions
**Outstanding:** deferred items
```

On startup, read `project.md` if it exists and summarize the last session in one sentence before asking whether to continue.

## Anti-patterns

Things that consistently fail regardless of style:

- **Hierarchical pre-computed codec formats** with USABILITY / tone tags / shot layers. Over-engineering. Derive from the transcript at decision time.
- **Hand-tuned moment-scoring functions.** The LLM picks better than any heuristic you'll write.
- **Whisper SRT / phrase-level output.** Loses sub-second gap data. Always word-level verbatim.
- **Running Whisper locally on CPU.** Slow and it normalizes fillers. Use hosted Scribe.
- **Burning subtitles into base before compositing overlays.** Overlays hide them. (Hard Rule 1.)
- **Single-pass filtergraph when you have overlays.** Double re-encodes. Use per-segment extract → concat.
- **Linear animation easing.** Looks robotic. Always cubic.
- **Hard audio cuts at segment boundaries.** Audible pops. (Hard Rule 3.)
- **Typing text centered on the partial string.** Text slides left as it grows.
- **Sequential sub-agents for multiple animations.** Always parallel.
- **Editing before confirming the strategy.** Never.
- **Re-transcribing cached sources.** Immutable outputs of immutable inputs.
- **Assuming what kind of video it is.** Look first, ask second, edit last.
- **Reusing a previous episode's graphics with the numbers swapped.** Templated channel, visuals stop carrying information. Build for this video's words. (Principle 8.)
- **Placing a scene because its geometry was convenient.** A "contradiction" layout dropped onto a segment that isn't about a contradiction fits the shape and misleads the viewer, who trusts that what is on screen is what is being discussed.
- **Inventing on-screen instrument readouts** — timecodes, "FIG 02", source IDs — to make a technical look feel authentic. Reads as clutter immediately.
- **Cutting on an ASR timestamp.** Measure the waveform. ASR drifts ~200ms and worse on sped-up speech.
- **A trailing outro card over silence.** Reads as the video breaking. End on the last word.
- **Looping ambient motion: scan sweeps, travelling bands, pulsing glows, drifting particles.**
  A band crossing the frame top-to-bottom on a repeat is a screensaver — it carries no
  information, it repeats, and it pulls the eye off whatever the scene is building. Everything
  that moves must be moving *because the argument moved*. Background beds may drift only if the
  motion is imperceptible frame to frame.

### Scene sequencing (multi-scene per clip)

`helpers/shoot_sequence.py <sequence.json> out.mp4` renders several archetypes across one
clip; `helpers/compose_scene_short.py` then pastes the real speaker feed into the rail's
speaker cell and takes the audio from the finished short, so art, voice and speaker stay
locked.

- **Scene spans come from the transcript**, declared against the clip timeline in
  `sequence.json` (`at` / `until`). Never render a scene at a default length — a 7s scene
  under a 50s clip is instantly wrong.
- **Each scene still renders in its OWN local time**, so archetypes stay reusable and never
  need to know where they sit in the clip.
- **Cross-dissolve between scenes**, don't hard-cut.
- **Expose the speaker rect** from the scene (`window.__SPEAKER_BOX`) so the compositor has
  one source of truth for where the webcam lands.

### Scene content must match the words, not just the shape

The trap: build a library of archetypes, then place them by shape. A "contradiction" scene
about Toyota dropped into a segment about household spending fits the *shape* and communicates
nothing — worse, it actively confuses, because the viewer trusts that what is on screen is
what is being discussed.

**The archetype is a LAYOUT. The content comes from the transcript span it sits over.**
Before building a sequence, pull the words for that clip and list what is actually claimed in
each stretch; then build a scene per claim. Never carry a scene over from another clip because
its geometry was convenient.

Two layout rules learned the hard way:
- **Inner elements must fill their container.** Boxes occupying ~25% of their card read as a
  mistake. Size children from the parent, don't place them at fixed offsets.
- **Round line caps on thick strokes reach back half the stroke width.** An 80px stream with a
  round cap smears 40px into whatever sits above its start point. Use butt caps and begin the
  stroke clear of neighbouring elements.

### Ending a clip cleanly

Three separate things, all needed:
1. **Snap to a sentence end** — never stop mid-clause.
2. **Leave a tail** — cutting on the exact end timestamp of the final word clips its decay and
   sounds truncated even though the sentence is grammatically complete.
3. **Clamp that tail to the next word's start.** A fixed tail will run into whatever follows,
   so the clip ends on a clipped syllable — worse than no tail. `end + min(TAIL, next_start -
   end - 0.12)`.

When verifying, trust the word timings over a re-transcription: ASR drops trailing words on
fast or sped-up speech, so a short ending "missing" from a transcript may be perfectly intact.
Compare against the same window of the SOURCE before believing a clip is truncated.

### Matching a product's visual identity

Pulling hex values from a stylesheet is not the same as matching a product's look. On the
reference run the tokens were right and the result still felt generic, because identity lives
in things the token list does not record:

- **Temperature.** One product's darks were warm — olive/brown-tinted near-black, not neutral
  grey. A neutral dark with the correct accent still reads as someone else's product.
- **Numerals.** The product sets almost every figure in monospace with wide letter-spacing.
  That single choice carries more brand recognition than any colour.
- **Surface treatment.** Panels are near-solid warm darks with hairline borders, not the
  translucent glass I reached for by default.
- **Chroma.** Every hue is desaturated. Saturated accents look wrong next to it.

**Ask for screenshots of the real product before designing.** Two screenshots of the live app
told me more than the entire CSS token dump. Do this at the start, not after a rejected pass.

### Logo lockups

Size the mark and wordmark against the rail, not against each other, and give them a shared
optical centre. Too small reads as a watermark rather than a brand; centring both in the same
cell makes them collide (see the frame contract above).

### FUI (fictional user interface) as the visual register

The look the client landed on: pure black, fine white linework, near-zero fill, colour only
where it carries meaning. Reference points were dot-field globes, flow-field line families,
white candles on near-black, and evilcharts area charts.

What actually produces it:
- **Pure black, not "dark".** `#000`. Warm or neutral dark greys read as a product UI.
- **Corner brackets instead of closed boxes.** A full outline reads as a card; brackets read
  as an instrument registering something. This single change carries most of the register.
- **Hairline graticule** at very low alpha. Static. Structure, not decoration.
- **Monospace numerals with tracking.** Every figure.
- **Colour is semantic only** — one hue for up, one for down, everything else white or grey.
- **Fills at ~15% alpha** where a shape must read as a quantity; outlines alone make a bar
  chart look like empty frames.

**Minimal means no invented information.** Fake instrument readouts — timecodes, "FIG 02",
source IDs, coordinate ticks — are the obvious way to fake this register and the first thing a
client will call out as clutter. Everything on screen must be real information about the
subject. If it isn't a number the speaker said, it should not be there.

### Trust measured audio over ASR timings when cutting

Whisper put the final word's end at 387.4; the waveform put it at 387.60. Cutting on the ASR
number clipped the word. Measure real silences (`tighten.Envelope.silences`) and cut inside a
genuine gap. ASR timing drifts badly on sped-up speech.

Related: **a trailing outro card over silence reads as the video breaking.** If the rail
already carries the brand, drop the outro (`--no-cta`) and end on the last word.

---

## Scene animation — consolidated notes

Everything learned building purpose-made explainer animation to replace a screen-recorded
whiteboard. Read alongside *Shorts* and *Purpose-built scene animation* above.

### The non-negotiables

1. **Unique per video.** See the rule at the top of the animation section. Same look every
   week = templated channel. The archetypes are thinking tools, not a catalogue.
2. **Content follows the transcript, always.** Pull the words for the clip first, list the
   claims, then design. Never place a scene because its geometry was convenient.
3. **Timings come from the clip, not from a default.** Scene spans are declared against the
   clip timeline (`sequence.json`), and a clip usually needs 3-4 scenes, not one.
4. **Nothing on screen that isn't real information.** No invented timecodes, figure numbers or
   source IDs. Faking an instrument readout is the first thing a client calls out as clutter.

### The visual register (FUI)

Pure black `#000`. Fine white linework. Near-zero fill. Corner brackets rather than closed
boxes — that one change carries most of the look. A static hairline graticule at very low
alpha. Monospace numerals with tracking. Colour is semantic only: one hue up, one
down, everything else white or grey. Shapes that represent a quantity need ~15% fill or they
read as empty frames.

Warm palettes, glass panels and gold accents were all tried and rejected. "Dark" is not the
same as black.

### Frame contract

Bottom rail = 15% of height. Logo hard-left in its cell with the wordmark starting after it —
centring both in one cell makes them collide. Speaker occupies the right cell; expose that rect
(`window.__SPEAKER_BOX`) so the compositor has one source of truth. Art area is everything
above, and no scene should need to dodge the speaker.

### Render + timing contract

Every scene is a pure function of `window.__render(t)`. No rAF, no internal clock. That makes
captures reproducible *and* lets the beat sheet be driven from transcript timings.
`helpers/shoot_sequence.py` renders multiple scenes across a clip with cross-dissolves;
`helpers/compose_scene_short.py` pastes the real speaker feed into the rail and takes the audio
from the finished short.

### Cutting audio

Trust measured audio over ASR timings — Whisper drifts badly on sped-up speech and will put a
word's end 200ms early, so cutting on its number clips the word. Measure real silences and cut
inside a genuine gap. Snap to a sentence end, leave a tail, and clamp that tail so it cannot
reach the next word. Where the natural sentence end runs into the following clause and there is
no clean option, `--hard-end` sets an exact time.

A trailing outro card over silence reads as the video breaking. If the rail already carries the
brand, use `--no-cta` and end on the last word.

### Getting the look right faster

Ask for **screenshots of the real product** before designing, and ask what the look is *called*.
Two screenshots taught more than the whole CSS token dump, and the word "FUI" changed the
details more than three palette iterations had. Hex values do not capture temperature, numeral
treatment, surface style or chroma discipline.

### Measure the clip's real end BEFORE writing the sequence

Shorts built earlier may carry a silent outro card. Run the envelope check first and set the
sequence `duration` to `last_loud_frame + ~0.4s`, then trim the source clip to the same point.
Doing it afterwards means re-rendering ~1150 frames, or shipping the silent tail again.

### Scene animation is iterated to a confirmed-good state, not rendered once

Scenes are never done on the first render. The loop is: build → still-check every scene →
fix → render the sequence → WATCH IT → fix → re-render, and keep going until the result is
confirmed good. Budget for several passes; treat a first render as a draft, never as a
deliverable. Do not present a scene render as finished on the strength of the plan or of a
single still — the faults that matter (a label grazing a shape, dead space, an end-state that
reads wrong, motion that repeats without meaning) only show up when you look.

Every visual note the client has ever given became a permanent check, not a one-off fix. When
new feedback arrives, add it to this list rather than just correcting the current file:

- no looping ambient motion (scan sweeps, travelling bands, drifting particles)
- no invented on-screen metadata (fake timecodes, figure numbers, source IDs)
- nothing off-topic: every scene illustrates what is being said in its span
- no dead space filling a third of the frame; no text touching the shape it annotates
- graphics sized from their container, not guessed
- end on the last word — no trailing card over silence

### Check every scene as a still before rendering the sequence

A 48s sequence render is ~1150 Playwright screenshots and takes minutes. Grab one PNG per scene
at a moment when it is fully built (and a second one for long scenes) and actually look at them
first. The layout faults that matter are all visible in a still:

- **dead space** — content clustered in the top half with 400px of empty black under it
- **collisions** — a label overlapping the shape it annotates, text wider than its circle
- **animation end-states that read wrong** — a depleting stack that empties from the bottom
  looks like it is floating; only the top should go
- **graphics too small for their panel** — size node art from the panel, not from a guess

Hook the page's `pageerror` while grabbing: a scene that throws renders as a black frame and
the sequence render will happily produce 1150 of them.

### Japanese scene copy

Type:
- **Gothic, not Mincho.** `"Noto Sans CJK JP"` at 700–800 for display. Serif reads editorial;
  the analytical register wants gothic. Add the CJK family to every font stack in the chassis
  so a stray kana in an English scene still renders instead of tofu.
- **No letter-spacing on Japanese text.** Latin small-caps labels take `tr:4`; kana and kanji
  take `tr:0`. Tracking that flatters `US TREASURY ACTION` mangles 「日本の消費」.
- **Keep numerals latin.** 「1兆4,770億円」 sets better than full-width digits and keeps the
  monospace numeral treatment consistent with the English cut.
- **Break lines by hand at phrase boundaries.** There is no wrapping in the canvas helper, and
  Japanese has no spaces to break on — an over-long string silently runs off the frame.

Copy:
- **Take figures from the dub script (`blocks.json`), never from the ASR of the dub.** Scribe
  on synthetic Japanese produced 「一四八兆円」 for 1.48兆, 「百九十円」 for 160円, 「人件」
  for 賃金 and 「稲ふれ」 for 下振れ. Use the ASR only for *timing*; use the script for *words*.
- The scene is not a subtitle. Short noun phrases, the number, and the direction.

### Audit for untranslated literals — retrofitting misses whole arrays

Routing an existing English episode through a copy table by hand WILL miss strings: labels
built inside a helper closure, ternaries (`linked?'UP':'DOWN'`), and row tables passed as
arguments never show up when you eyeball the file. Grep for what still reaches the canvas:

    lits = set(re.findall(r"T\('([^']+)'", src))
    bad  = [x for x in lits if re.search(r'[A-Za-z]{2,}', x)]

Run it until it returns only strings belonging to scenes that language's cut never shows, and
list those explicitly rather than assuming. On the first pass this caught `SPENDING`, `UP`,
`DOWN`, `UNITED STATES`, `JAPAN`, `almost always` and `not here` still rendering inside a
Japanese frame — all invisible in a read-through, all obvious in a still.

Then look at a Japanese still anyway: order is not a string problem. 「将来に備えるクッション /
使うのではなく」 is a literal translation of two English lines whose order only works in
English.

### Watch for a copy lookup shadowed by a local

Naming the lookup `L()` collides with any `const L=` inside a scene — and because `const` is
block-scoped with a temporal dead zone, the collision throws a ReferenceError that renders as a
silent black frame, not an error. Grab a still per scene and watch `pageerror`.

### Background jobs: never guard with a self-matching pgrep

`while pgrep -f "helpers/shoot_sequence.py"; do sleep 15; done` never exits — the waiting
shell's own command line contains that string, so pgrep matches itself. It blocked two renders
for fourteen hours while reporting "in flight". Two lessons: match on something the waiter
cannot contain (a PID, a lock file, an output path test), and treat an unchanged progress
counter across two checks as evidence of a stall, not of slowness. Also confirm the temp
directory you are counting frames in is the CURRENT run's — a stale one from a killed render
reads as plausible progress.

### Known unresolved

- **The English spending clip still ends slightly into "it seems."** Accepted by the client for
  now. The cause is that the only clean sentence boundaries sit either too early (cutting the
  whole point) or too late; a proper fix needs sub-word cut placement measured from the
  waveform rather than snapping to transcript sentence ends.
- **Title and description language** stays on the channel default (Japanese) even after video
  language is corrected. It is a separate field; fix it per video.
- **Long-form English cut has no caption track**, so auto-translate is unlocked on the Japanese
  long-form only.
- **Scene spans are hand-authored.** With word timings available they should be proposed
  automatically from the transcript.
