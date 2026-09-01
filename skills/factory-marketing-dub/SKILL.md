---
name: factory-marketing-dub
description: Take a screen-recorded product demo whose dub is grammatically correct but obviously machine-translated, and produce a natural-sounding redub in a cloned voice, plus a matching short-form social post. Covers transcribing the existing dub, auditing it for translationese/register-crashes/meaning-inversion, rewriting the script, voice cloning, the mandatory generate-then-verify loop that catches silent kanji/word misreads, tight audio assembly, and the companion post. Draft/deliverable only — never publishes or uploads on its own. Use when the user says "dub this video", "redub", "make this sound native", "fix the language in this video", or invokes /factory-marketing-dub.
user-invocable: true
---

# Factory — Marketing Dub (machine dub → native redub)

Take a demo video whose dub is *correct but obviously translated* and produce a redub that sounds
like a real person talking, in a cloned voice, plus the companion post to ship it with.

## The core principle — grammar is not the bar

A machine dub fails at **register**, not grammar. Three failure classes, in descending severity:

1. **Phrases that invert their own meaning.** A line translated from a stock idiom or a joke can
   land as its literal opposite in the target language/culture — delivered earnestly, it reads as a
   red flag or as unintentionally comic. These actively damage the post; fix or cut them first.
2. **Register crashes.** Casual narration that suddenly drops into press-release formality, or into
   childish phrasing, inside the same clip. Any single register would be fine; the whiplash is the
   tell.
3. **Translationese calques.** Grammatical, understandable, and unmistakably a translation
   underneath — noun-stacking, unnatural conditionals, idioms carried over literally.

Fix in that order. A dub with class-1 problems is worse than no dub at all.

---

## Phase 1 — Probe and transcribe

```bash
ffprobe -v error -show_entries format=duration -show_entries stream=codec_type,codec_name \
  -of default=nw=1 "<video>"
ffmpeg -y -v error -i "<video>" -vn -ac 1 -ar 16000 -c:a pcm_s16le audio.wav
python3 scripts/dub.py transcribe audio.wav
```

**Prefer a hosted transcription API over a large local model.** A local `whisper --model large-v3`
run triggers a multi-gigabyte model download for what's usually a short clip; a hosted API returns
in seconds for a fraction of a cent per minute. Use a local model only if there's a specific reason
not to hit an API (offline environment, no key available).

**Do not trust a single pass on proper nouns.** Two independent transcripts agreeing is the cheap
confidence signal; where they disagree, slice that window and re-transcribe it alone:

```bash
ffmpeg -y -v error -ss 48 -t 6 -i audio.wav seg.wav
python3 scripts/dub.py transcribe seg.wav
```

Distinguish a genuine transcription artifact from a real dub error before "fixing" audio that was
already correct — a slice-and-recheck is cheap insurance either way.

---

## Phase 2 — Audit the language

Report findings to the user before rewriting — they may want to keep something you'd cut. Work
down the three classes from the core principle above. Treat any example catalog you build up over
time as a pattern library, not a complete set — every new source clip adds cases.

**Cultural adjustments that are not language errors:** modesty conventions (a flat, confident
self-assessment can read as bragging in some languages/cultures — hedge it), expected
openers/closers (many locales expect a greeting before diving into content), and register-specific
vocabulary that's fine in one context (e.g. gaming slang) but wrong for the actual audience (e.g. a
finance audience). These aren't grammar — get them right anyway.

---

## Phase 3 — Write the script

Plain UTF-8 text, **one paragraph per blank-line-separated block**. Blocks are the unit of TTS
generation and of timing, so break them where a speaker would take a breath, not by topic.

Hard rules:

- **Drop first-person pronouns where the target language makes them optional and gendered/register-
  coded** (many languages allow or prefer subject omission). Never infer the speaker's gender from
  their name — if a specific pronoun matters, ask once, in the delivery report, rather than guessing.
- **One register, start to finish.** Casual-but-not-rude generally suits a product demo — contractions,
  fragments, informal connectives throughout. Pick one and hold it.
- **Fragments are good.** A native speaker uses them; a complete-sentence rendering of the same idea
  often reads as more artificial, not less.
- **Target length.** A natural redub typically runs meaningfully *shorter* than a dub that was
  time-matched to the original narration (expect on the order of 30%+ shorter — measure your own
  source/target pair rather than assuming an exact figure). Don't pad the script to fill the video —
  Phase 6 cuts the video to fit the audio, not the other way around.

Apply the misread-safety pass from Phase 5's lessons *while writing*, not after — it's much cheaper
to write around a known-bad word than to discover it after generating audio.

---

## Phase 4 — Clone the voice

Check what already exists before cloning:

```bash
python3 scripts/dub.py voices
```

If a usable clone of the speaker already exists, **reuse it** — a fresh clone is strictly worse than
a proven one.

```bash
ffmpeg -y -v error -i "<video>" -vn -ac 1 -ar 44100 -b:a 128k clone_sample.mp3
python3 scripts/dub.py clone clone_sample.mp3 --name "<label>"
```

**Cloning from an existing dub is a clone of a clone.** Modern voice-cloning services generally
preserve underlying speaker timbre through a dub, so this does work — but say so explicitly in the
delivery report and tell the user to ear-check it. If an un-dubbed original recording of the same
speaker exists, clone from that instead; check before falling back to the dub.

**Validate the API key before doing anything else** — a bad key can fail silently as an empty
response rather than a loud error:

```bash
python3 scripts/dub.py voices   # prints tier + quota, or the auth failure
```

Two gotchas worth checking for on every run: a pasted key can carry **trailing paste junk**
(mismatched length vs. the expected key format), and being **over quota can still silently serve
requests** on some billing tiers (overage billing) — report any overage rather than assuming a quota
error would have stopped the run if it were actually over.

---

## Phase 5 — Generate, then verify the reading

```bash
python3 scripts/dub.py tts script.txt --voice <VOICE_ID>
```

### The verification loop is MANDATORY

**TTS engines can misread compound words in some languages, silently** (e.g. a kanji compound read
with the wrong pronunciation, entirely changing its meaning, with no error surfaced). This is the
single highest-value step in this skill and the one that will otherwise ship a broken video.
Transcribe the generated audio back and diff it against the script:

```bash
python3 scripts/dub.py verify mixed.wav --script script.txt
```

**Fix a genuine misread by writing it phonetically** (kana, or the target language's phonetic
script), or by choosing a different word entirely — phonetic spelling is invisible to the listener
and unambiguous to the model.

**Distinguish a real misread from a transcriber artifact.** A transcriber clipping short vowels or
similar-sounding syllables on synthetic audio needs no fix; a **phonetically distant** divergence (a
completely different, unrelated-sounding word or reading) is the TTS engine actually misreading the
text. When genuinely unsure, slice that one paragraph and re-transcribe it alone.

Expect the diff to flag your own phonetic substitutions as "different from the original spelling" —
that's the fix working as intended, not a problem.

Regenerate only the changed blocks (`dub.py tts --only <block numbers>`), then re-verify. Iterate
until the only divergences left are transcriber-artifact class, not real misreads.

---

## Phase 6 — Assemble and cut

**Default to tight-cut.** Padding audio with silence to fill a time-matched video produces dead-air
gaps that read as broken, and the visuals rarely line up anyway once the script has been rewritten
to a natural length.

```bash
python3 scripts/dub.py build "<video>" --out "<video-dir>/<name>_redub.mp4" --mode tight
```

- `--mode tight` (default): trims each generated clip's own leading/trailing silence, applies a
  fixed lead-in/inter-block-gap/tail, then trims the video to the resulting audio length.
- `--mode anchored --anchors <t1,t2,...>`: places each block at a timestamp so narration tracks
  on-screen events. Only worth it when specific moments in the demo must line up with specific
  words; it reintroduces gaps between blocks.
- `--mode speed`: keeps every frame by speeding the video to fit the shorter audio. Use when
  something at the tail of the recording needs to stay on screen. Re-encodes, so it's the slow path.

Audio gets loudness-normalized for social platforms; video muxing avoids re-encoding where possible.

Confirm there's no dead air left:

```bash
ffmpeg -v info -i mixed.wav -af "silencedetect=n=-40dB:d=0.7" -f null - 2>&1 | grep silence_
```

**`-v info` is load-bearing.** `silencedetect` logs at info level — `-v error` returns nothing and
the check silently always passes, which is false confidence exactly where you least want it.

**Write to a new filename** and leave the input untouched; the user may want to compare.

---

## Phase 7 — The companion post

Short, informal, with a clear bracket/tag convention if the target platform/account has one — check
`factory/marketing/platforms.md` for the account's existing convention rather than inventing one, and
don't reuse another content type's specific tag vocabulary (e.g. a signal-tag scheme meant for market
alerts has no business on a product-update post).

Run the `factory-humanizer` skill (English mode) on any English half of the post before it goes
anywhere public. For a non-English half, a language-specific structural read matters more than a
generic scan — tone monotony, sentence-length metronome, an empty hook — run `factory-humanizer` in
that language too if it supports one.

Always supply a rough translation alongside the native-language post, and flag anywhere the
translation flattens register the original carries (an idiom that reads as genuine enthusiasm in one
language can read as flat or sarcastic translated literally).

---

## Phase 8 — Deliver

Hand back:

1. **Output path**, and confirmation the input video is untouched.
2. **Duration change**, and — if cut — **what footage was dropped**, by timestamp, so the user can
   judge whether that's acceptable.
3. **The script**, with a rough translation of each block.
4. **The post**, with translation and any alternative title/tag options.
5. **Voice-clone caveat**, if it came from a dub (clone-of-a-clone) — ask them to ear-check it.
6. **Open judgment calls**, explicitly — a dropped pronoun, anything from the Phase 2 audit you cut
   that they might want reconsidered.
7. **Residual verify diffs** you classified as transcriber artifacts, with timestamps, so they can
   confirm by ear.

---

## Hard rules

- **Never post, DM, or upload anything.** Produce files and draft copy. Publishing is always the
  user's call — no exceptions.
- **Never overwrite the source video.** Write the redub to a new filename alongside it. Overwriting
  a previous *derived* output of this skill is fine; overwriting an input is not.
- **Never skip Phase 5.** A dub with an unnoticed misread is worse than the machine dub it replaced,
  and the error is inaudible to anyone not fluent in the target language reviewing the output.
- **Never guess the speaker's gender** for pronoun or register choices. Drop what can be dropped;
  ask if it genuinely matters.
- **Report any quota overage.** Some billing tiers serve requests past the nominal limit — check
  the voices/quota command and pass the real numbers on rather than assuming a limit would have
  stopped the run.
- **Tell the user to rotate a pasted API key.** It lands in the transcript and shell history.
- **Voice cloning is for the speaker's own voice**, at their request, on their own recordings. Do
  not use it to clone a third party from a video someone else made.

## Cost and time (rough calibration — from one real run, re-measure for your own provider pricing)

| Item | Cost |
|---|---|
| Transcription (hosted API) | ~$0.006/min · ~$0.01 per 2-min clip |
| Verification re-transcribes (2 rounds) | ~$0.02 |
| Instant voice clone | free on most tiers |
| TTS, ~600-char script | ~600 chars of quota (~1,800 across 3 generations) |
| ffmpeg assembly | free |
| **Per video, end to end** | **~$0.05 plus quota, roughly 15 minutes** |

The dominant cost is quota burned on regeneration, which is why the misread-safety pass belongs in
Phase 3 (while writing the script) rather than being discovered in Phase 5 (after generating audio).
