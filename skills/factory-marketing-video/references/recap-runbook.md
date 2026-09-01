# Runbook — recorded screencast → edited → sourced → dubbed → published

End-to-end flow for a recurring commentary/recap video: one or more raw screen
recordings in, a cleaned English cut plus a voice-cloned foreign-language version
published to YouTube out. Read `SKILL.md` for the reasoning behind each rule;
this file is the order of operations.

Timings below are from a real 17-minute two-part recording that produced a 14:54
finished cut, for calibration.

---

## 0. Before touching anything

```bash
mkdir -p ~/Videos/masters && cp -n "<src>.mp4" ~/Videos/masters/
md5sum "<src>.mp4" "~/Videos/masters/<src>.mp4"     # verify, don't assume
```

The user may have exactly one copy. Copy first, verify the hashes match, then work.
All outputs go to `<videos_dir>/edit/` — never write next to the sources.

---

## 1. Transcribe (two passes, they do different jobs)

```bash
python3 helpers/transcribe_local.py "<src>.mp4" --edit-dir edit/     # word-level
python3 helpers/transcribe_runs.py  "<src>.mp4" --edit-dir edit/ --workers 12
```

- **word-level** (faster-whisper, GPU): positions of individual filler words.
- **run-level** (silencedetect + per-run hosted ASR): exact speech boundaries and
  accurate text. This is the one you read to understand the material.

Word-level timestamps are *not* trustworthy for cut placement — see §2.

---

## 2. Cut: fillers, dead air, asides, dead tails

```bash
python3 helpers/tighten.py "<src>.mp4" --edit-dir edit/ --edl edit/edl.json \
    --keep-until 740.35 --drop 317.78-325.20 --drop 544.85-549.28 --filler-pause 16
python3 helpers/render.py edit/edl.json -o edit/part1.mp4 --native --no-subtitles
```

`--native` matters: sources below 1080p get upscaled by default, which softens
on-screen text, and 60→24fps judders cursor movement.

**The failure that matters here** is clipping word endings. Never pick an absolute
dB threshold; derive it from the measured speech level. Watch the `CUT-QUALITY`
line — it should read `0 ends`. Then verify by transcribing the *whole* render and
diffing it against the plan, discounting fillers and the speaker's own stutters.
Sampling a few joins is what let a broken cut through the first time.

Joining two recordings: render each part separately, then lossless concat.

```bash
printf "file 'part1.mp4'\nfile 'part2.mp4'\n" > cat.txt
ffmpeg -y -f concat -safe 0 -i cat.txt -c copy final.mp4
```

Loudness-normalise each part *before* joining so levels match across the seam.

---

## 3. Source cards (B-roll)

Read the transcript, list every checkable claim, research each in the browser,
**fact-check as you go**, then:

```bash
python3 helpers/broll_cards.py edit/overlays/spec.json
```

Research in the language the video ships in. Expect to find real errors in the
narration — on the reference recording, a "1.8 times" increase was narrated as
"1.8 trillion". Surface mismatches; never quietly pick a screenshot that agrees
with the voiceover when the source disagrees. An `correction` caption on the card
is the fix when the take is worth keeping.

Hold 8s minimum. Never overlay a screenshot of something already on screen.

---

## 4. Dub

```bash
python3 helpers/dub.py samples --edit-dir edit/ --video final.mp4
python3 helpers/dub.py clone   --edit-dir edit/ --name "<Speaker> <Lang>"   # once, ever
python3 helpers/dub.py blocks  --edit-dir edit/ --video final.mp4 --anchors 107,137,310,518,851
```

Fill each block's `target` in `edit/dub/blocks.json`. Write to roughly
`duration × 6.2` characters as a first guess, then let measurement correct it.
Fix the speaker's factual errors here — the dub should agree with the on-screen
cards. Then run a de-AI pass on the script (±8% length constraint).

```bash
python3 helpers/dub.py synth --edit-dir edit/                   # reports fill % + ch/s
python3 helpers/dub.py synth --edit-dir edit/ --only 4,17,21 --force   # after rewriting
python3 helpers/dub.py build --edit-dir edit/ --video final.mp4 -o final_dub.mp4
python3 helpers/dub.py srt   --edit-dir edit/ --video final_dub.mp4
```

Iterate `synth` until every block is 88–112%. Three passes is normal. Verify the
result by measuring gaps, not by trusting the fitter:

```bash
ffmpeg -hide_banner -nostats -i edit/dub/track.wav \
  -af "silencedetect=noise=-45dB:d=0.35" -f null - 2>&1 | grep -oP "silence_duration: [\d.]+"
```

Target: median ~0.6s, very few over 1.0s.

---

## 5. Publish

1. **Switch channel first.** Avatar → Switch account. Confirm the sidebar name.
2. **User selects the video file** — the bridge caps uploads at 10 MB.
3. Title, description with chapters, tags. **Read the description back and diff it**
   against your source text; synthesised typing drops characters.
4. Category (defaults wrong), video language, made-for-kids (user answers).
5. Stop at Visibility. **Get explicit confirmation before Publish.**
6. Thumbnail: capture the source page, hide app chrome surgically, park the cursor
   in a croppable area, extend the background to 16:9 rather than cropping content.
   Upload via the file input (small enough to pass), then Save.
7. Captions: upload the SRT to the **(video language)** row and Publish — YouTube's
   auto-generated captions do not unlock auto-translate.

---

## 6. Second-language canvas version (optional)

Only if the on-screen board exists in the delivery language.

```bash
# capture the target board as tiles (set scrollX/scrollY/zoom in localStorage, reload)
# stitch -> board_xx.png, then:
cp helpers/canvas_camera_example.py camera.py    # edit VIEW_W, S, BLOCK_SECTION
python3 helpers/canvas_swap.py                    # camera + webcam inset + audio
python3 helpers/broll_cards.py spec_xx.json       # re-composite the cards
```

Set `VIEW_W` from what the original actually showed:
`video_width / (video_px per scene unit)`. Guessing produces a comically zoomed cut.

**Verify the inset**: difference the composited webcam against the source frame it came
from at three timestamps. Single-digit mean pixel difference is sync. This catches the
frame-rate trap (reading one source frame per output frame at 60->30 halves its speed).

## 7. Speed pass, if the delivery convention calls for it

```bash
ffmpeg -i canvas.mp4 -filter_complex "[0:v]setpts=PTS/1.5[v];[0:a]atempo=1.5[a]" \
       -map "[v]" -map "[a]" -r 30 ... out.mp4
```

Do this BEFORE compositing cards, then composite at `start/1.5` with durations unchanged —
a sped-up card is not easier to read. Divide chapter timestamps by the same factor.

---

## 8. Shorts — the phase order that matters

Do NOT start shorts until both long versions are live **and their transcripts are uploaded**.
The caption upload is what unlocks YouTube auto-translate, and it is the step most easily
forgotten once the video is published and looks finished.

The order is: **publish both → upload both transcripts → cut 3-5 English shorts → build scene
animation for each → then the Japanese cuts.** English first is not arbitrary: it is the
language you can judge fastest, so layout faults surface there and are already fixed by the
time the Japanese cuts are built on the same geometry.

### 8a. Cut the clips

```bash
# one hook VO per clip, in a NARRATOR voice, not the speaker's
python3 helpers/make_short.py --source final_en_15x.mp4 \
    --cues transcripts/final_en_15x.json --start 344.4 --end 386 \
    --hook-audio hooks/EN_3.mp3 --hook-text "In Japan, wages are up. Spending fell 3.3%." \
    --board "380,48,782,500" --caps --out EN_3_spending.mp4
```

`--board` is the single most important argument: grid-probe a source frame and read off the
rect for ONE complete graphic. Use `--cjk --words-per-line 5` and an SRT for dubbed tracks;
the dub's own SRT is ground truth for what is spoken.

Pick clips that are **self-contained**: an argument that starts and finishes inside 60s. A clip
that opens mid-thought cannot be rescued by a hook.

> **QC gate — before any animation work.** For EVERY clip, measure the real end from the
> waveform and set the final duration there:
> ```python
> env = 20*log10(rms + 1e-9); th = percentile(env[env > env.max()-40], 75) - 22
> last_loud = where(env > th)[-1]          # then snap to a gap, tail <= next_start - 0.12
> ```
> Every clip in the reference run carried a 2.6s silent outro card, and two Japanese cuts ended
> on a fragment (a dangling 「日本の」, a clipped 「あめ-」). Trim the source to that point NOW —
> discovering it after a sequence render costs ~1150 frames of rework.
>
> Do not trust ASR timings for this. On one clip Scribe reported words running to 49.74s when
> the audio was digital silence from 47.17s.

### 8b. Scene animation, per clip

One episode file per EPISODE (not per language), including the chassis, declaring its own
scenes and a `setCopy({en:{...},ja:{...}})` table. One sequence JSON per language cut.

1. Read that clip's transcript and list what is actually claimed in each stretch.
2. Design a visual per claim. Expect to build new scenes — reaching for an existing archetype
   is the exception, not the plan.
3. Bind spans to the clip's own phrase boundaries in `sequence-<name>.json`.
4. Render, composite the speaker cell, verify.

> **QC gate — stills before frames.** Grab one PNG per scene at a moment when it is fully
> built, with `page.on("pageerror")` armed, and LOOK at each one. A 48s sequence is ~1150
> Playwright screenshots and 10+ minutes; every fault below was visible in a still:
> dead space filling the bottom third; a label grazing the shape it annotates; text running off
> frame; graphics undersized for their panel; an animation END-state that reads wrong (a stack
> depleting from the bottom looks like it is floating).
>
> A scene that throws renders as a black frame, not an error — the sequence will happily
> produce 1150 of them. A copy lookup named `L()` shadowed by a local `const L` is exactly this
> failure, and `const` block scoping makes it throw rather than fall back.

> **QC gate — after compositing.** Difference the pasted speaker cell against the source at
> t=5, 20, 35, 46. A flat diff means it is in sync; a diff that grows means the frame-rate
> ratio is wrong and the inset is drifting (60fps source into a 30fps output plays at half
> speed and ends minutes behind).

### 8c. The Japanese cuts

Build these on the SAME episode file. Add a `ja` block to the copy table and a second sequence.

**Read each Japanese transcript before assuming it mirrors the English.** In the reference run
only one of three did. The others were re-scripted: one spent 12s on a date sequence the
English never mentions and stopped before the causal chain; another stopped two-thirds through.
Both needed their own spans, and the first needed three scenes that exist only in the JA cut.

Take figures from `dub/blocks.json`, never from ASR of the dub — Scribe on synthetic Japanese
produced 「一四八兆円」 for 1.48兆, 「百九十円」 for 160円, 「人件」 for 賃金.

> **QC gate — untranslated literals.** Hand-retrofitting a copy table misses strings built
> inside closures, ternaries and row tables. Grep for what still reaches the canvas:
> ```python
> lits = set(re.findall(r"T\('([^']+)'", src))
> bad  = [x for x in lits if re.search(r'[A-Za-z]{2,}', x)]
> ```
> Run until the only survivors belong to scenes that cut never shows — and name them, do not
> assume. This caught `SPENDING`, `UP`, `DOWN`, `UNITED STATES`, `JAPAN`, `almost always` and
> `not here` still rendering inside Japanese frames.

> **QC gate — look at a Japanese still anyway.** Order is not a string problem. Two correctly
> translated lines can be in an order that only reads in English.

Budget: hook (~3s) + body < 60s, and no trailing CTA card over silence — the rail already
carries the brand, so end on the last word.


### 8d. Publish each short — the settings that default WRONG

Uploading is the easy part. Every field below defaulted to the wrong value on a real run and
none of them announce themselves:

> **QC gate — per short, before clicking Publish.**
> 1. **Video language.** Inherits the CHANNEL default, so English shorts arrive tagged
>    Japanese. Set it, then RE-OPEN the field and confirm it stuck — one click silently failed
>    and the video published in the wrong language.
> 2. **Title and description language.** A SEPARATE field further down the same panel. Setting
>    video language does not set it.
> 3. **Made for kids.** Required, unset by default.
> 4. **Category / tags.** Category may inherit correctly; tags never do.
> 5. **Wait for "Checks complete. No issues found."** Publishing while the checks bar still
>    reads a percentage triggers a "We're still checking your content" warning — going ahead
>    risks a strike or restricted visibility. Waiting costs ~60s.

**Typing CJK into a browser field corrupts characters.** Do not build the string from `\u`
escapes — a single wrong digit produced 「翼日」 for 翌日 and 「以尿」 for 以来 in a published
description. Type literal characters, then `zoom` on the field and read every line back.

### 8e. Caption tracks for the shorts

The shorts need their own tracks — the long-form upload does not cover them, and YouTube's
auto-generated captions are explicitly listed as **Ineligible** for auto-translate.

Build from the cached word transcripts, clipped to the trimmed duration:

    b = min(cue_end + 0.10, next_cue_start - 0.02, clip_end)   # never overlap

> **QC gate — overlapping cues.** Padding each cue end pushes it past the next cue's start;
> YouTube mangles the result. Assert zero overlaps before uploading.

> **QC gate — ASR text in the dub language.** Scribe on synthetic Japanese produced
> 「一四八兆円」 for 1兆4,770億円, 「百九十円」 for 160円, 「人件」 for 賃金, 「稲ふれ」 for
> 下振れ, 「松明」 for 将来. Correct against `dub/blocks.json` BEFORE upload — these captions
> feed auto-translate, so an error propagates into every language.

If a cue is empty, Publish raises "Cannot publish empty subtitles" — Continue drops it and
publishes the rest.

In Studio: video → Subtitles → the row for the video language → ⋮ → Upload file → "With
timing" → Continue → the file input is the LAST one on the page. Then Publish. Confirm the
result shows a "Published" row separate from the "(automatic captions) — Ineligible" row.

---


## Calibration numbers from the reference run

| | |
|---|---|
| Source | 821s + 199s raw |
| After tighten + join | 894s (14:54) |
| Fillers removable safely | 1 of 64 — most were embedded with no pause |
| Cut quality after fix | 0 of 53 segment ends landing in speech (was 81 of 118) |
| Dub script | 5,341 chars across 37 blocks |
| TTS rate observed | 5.3–9.0 chars/sec |
| Retune passes needed | 3 |
| ElevenLabs credits | ~8,400 total |
| Caption cues | 267, mean 3.3s |
| Board tiles to stitch | 10 (2 cols x 4 rows + 2 gap fills) |
| Canvas re-render | 26.8k frames in ~2 min |
| English delivery | 1.5x -> 9:57 |
| Shorts per episode | 3 per language, 48-51s each |
| Deliverables per episode | 2 long-form + 6 shorts + 6 caption tracks = 14 published items |
| Silent outro tail on every short | 2.6s — trim before writing any sequence |
| ASR overshoot past digital silence | up to 2.6s of words reported that do not exist |
| Scene sequence render | ~1150 frames @ 24fps, 10-14 min per 48s clip |
| Scenes per clip | 3-6, one per claim; 5-6 for a dense argument |
| JA cuts that mirrored their EN cut | 1 of 3 — always read the dub transcript |
| Untranslated literals found by grep after a hand retrofit | 7 |
| Webcam inset in source | 295x168 (720p capture) — the sharpness ceiling |

## Dub quality gate — run this BEFORE synthesis, every time

This exists because it was skipped once and a viewer commented 「ニホンゴワカラナイ」
("I don't understand Japanese") on a published video. The lesson was already written
down and got skipped anyway, so it is now enforced by `dub.py`.

The failure has a mechanism, not just carelessness: **fitting a script to a duration
produces a number on every iteration, and quality produces silence.** In the run that
broke, the script went through four rewrite passes — all four driven by chars-per-second
fitting, none by whether the Japanese was any good.

    dub.py --edit-dir . qa            # lint the readings, see what needs fixing
    # 1. de-AI / naturalness pass on the target language (run factory-humanizer in that language)
    # 2. terminology audit — how the target language's own press writes each term
    # 3. rewrite every flagged reading in kana
    dub.py --edit-dir . qa --mark     # record the passes; unblocks synth
    dub.py --edit-dir . synth

`synth` refuses to run until all three are recorded, and the record is bound to a hash
of the script — **any later edit to a target line re-arms the gate**, because the length
rewrites are exactly where stiff phrasing gets introduced.

Two things the gate cannot do, so do them by hand:

- **`similarity_boost` is an accent control.** High values carry the SOURCE language's
  accent into the target. The clone is built from English speech, so for a Japanese
  audience low is right. Default is now 0.3; it shipped once at 0.8.
- **A native speaker must hear it before publish.** ASR recovery is NOT a proxy: a
  native Japanese voice reading the same script fails the same words, so the measurement
  cannot tell a bad accent from a weak recogniser. Sixty seconds of a human listening
  settles what no amount of analysis will.

