---
name: factory-marketing-clips
description: Find videos where credible commentators discuss a topic, transcribe the relevant windows, and cut short frame-accurate clips to pair with your own published content — an article, a paper, a post. Covers YouTube discovery (Chrome tools + yt-dlp), the auto-caption trap, Whisper two-stage timestamping, tight ffmpeg cuts, and pairing each clip to a specific finding. Draft-only — never publishes on its own. Use when the user says "find clips", "promo clips", "clips to quote tweet", "find videos about this", "promote the paper/post", or invokes /factory-marketing-clips.
user-invocable: true
---

# Factory Marketing — Clips (video quotes that sell a finding)

Take a finished piece of published content and produce a **ranked list of videos, each with several
short clips**, ready to pair with it in a post. Born from a real run where a 3.3-second clip of a
commentator restating the exact thesis of a paper — in his own words, independently — turned out to
be more persuasive than any chart the paper itself contained.

## The core principle — pair, don't decorate

A clip is worth using only if it **sets up a specific finding**. Two shapes work:

1. **The clip asks the question your content answers.** Best possible pairing — post the clip, then
   the answer.
2. **The clip states the mechanism your content measured.** The speaker supplies the *why* in their
   own words; your content supplies the *number*.

A clip that is merely *about the same topic* is decoration — skip it. Better to ship three clips that
each land a point than twelve that are only on-theme.

**Prefer contradiction or independent convergence.** A well-known commentator saying something your
content refutes is a stronger pairing than one simply agreeing — and someone reaching your
conclusion *without* having seen your content at all is the strongest pairing of all.

---

## Phase 1 · Discovery

Two tools, different jobs. Use both.

### 1a · yt-dlp for bulk shortlisting (fast, scriptable)

The `ytsearch25:` URL scheme is **unsupported on some builds** (`Unsupported url scheme`). Point it
at a real results URL instead:

```bash
yt-dlp --no-update --flat-playlist --skip-download \
  --print "%(duration>%H:%M:%S)s | %(view_count)s | %(uploader)s | %(id)s | %(title)s" \
  "https://www.youtube.com/results?search_query=YOUR+TERMS&sp=CAI%253D"
```

`&sp=CAI%253D` sorts by upload date (note the double-encoded `%253D`) — useful for a live/recent
event. Omit it to sort by relevance and surface big-view evergreen explainers instead. Run 3-5
different query angles (the mechanism, the specific subject, the narrative framing, the skeptical
framing) — they tend to return largely disjoint result sets.

### 1b · Chrome tools for triage (richer metadata)

`navigate` to the same results URL, then `get_page_text`. You get descriptions **and — the real
prize — chapter lists**:

```
mcp__claude-in-chrome__navigate  { url: "https://www.youtube.com/results?search_query=…&sp=CAI%253D" }
mcp__claude-in-chrome__get_page_text { tabId }
```

**Chapters locate your clips for free.** A chapter title tells you which minute to transcribe
without touching the audio first. Pull them per-video with
`yt-dlp --skip-download --print "%(chapters)s" <id>`. Always check chapters before transcribing —
it can cut the work by 10x.

### 1c · Ranking the shortlist

Score each candidate on: **credibility** (a domain expert beats a hype channel), **reach** (view
count — though a low-view video with the perfect line still wins), **specificity** (does the
description/chapters promise the actual mechanism, or just the headline?), and **recency**. Prefer
speakers your audience already respects — a clip's persuasive weight is mostly borrowed from them.

---

## Phase 2 · Transcription

### 2a · Never trust the platform's own auto-captions for this

Auto-captions **silently mangle exactly the proper nouns you're searching for** — a video whose own
title contains a specific name/ticker/term can still come back with zero hits for that term in its
auto-captions. Grepping them then falsely concludes the video is irrelevant. Auto-captions are fine
only for a rough "is this topic present at all" sniff. They also arrive as rolling partial cues with
inline timing tags and heavy duplication, so any use needs de-duping first (keep the cue start time,
strip tags, drop lines contained in their predecessor).

### 2b · A hosted transcription API, prompted with the vocabulary

```python
r = client.audio.transcriptions.create(
    model="whisper-1", file=fh, response_format="verbose_json",
    timestamp_granularities=["segment"],
    prompt="<every proper noun, ticker/index, acronym, and person's name you expect to hear>",
)
```

The `prompt` field is a vocabulary hint, not an instruction — load it with everything specific to
this subject; it materially improves proper-noun accuracy. Roughly $0.006/min, so a 20-minute video
costs about $0.12. Keep audio under the request's size cap (commonly 25MB):
`yt-dlp -f bestaudio -x --audio-format mp3 --audio-quality 5` typically gets well under that for a
20-minute video. For longer streams, slice with ffmpeg and transcribe windows — guided by chapters,
you rarely need the whole thing.

### 2c · Two-stage timestamping (the part that matters)

- **Stage 1 — locate.** `timestamp_granularities=["segment"]` over the whole file (or the chaptered
  windows). Segments run 10-30s — enough to find the passage, too coarse to cut on.
- **Stage 2 — bound.** Slice roughly ±15s around each candidate and re-transcribe that slice with
  `timestamp_granularities=["word"]`. Add the slice offset back. This gives cut points accurate to
  about 0.1s.

Stage 2 is not optional. A speaker can pivot from the exact line you want straight into an unrelated
tangent within 2-3 seconds — cutting on segment boundaries alone risks shipping a clip where the
punchline is immediately followed by unrelated chatter.

---

## Phase 3 · Cutting

```bash
ffmpeg -y -loglevel error -ss <start> -to <end> -i full.mp4 \
  -c:v libx264 -preset veryfast -crf 20 -c:a aac -b:a 160k -movflags +faststart out.mp4
```

- **Re-encode; do not `-c copy`.** Stream copy snaps to keyframes and will miss by seconds. These
  clips are 3-30s, so re-encoding costs nothing.
- `-movflags +faststart` for web/social playback.
- Download video separately from the audio you transcribed:
  `yt-dlp -f "bv*[height<=1080]+ba/b[height<=1080]" --merge-output-format mp4`.

**Cut ruthlessly tight.** Speakers derail mid-thought constantly — end the clip on the last word of
the point, not at the end of whatever sentence they wander into next. Verify any clip you're unsure
of by re-transcribing the cut file itself.

**Length guide:** a quote-card line 3-8s · a claim 10-20s · an explained mechanism 20-40s. Past
roughly 45s it's no longer a promo clip.

**Name files for the point, not the timestamp** — you'll be choosing between them later from
filenames alone.

---

## Phase 4 · Deliver

Write clips to a dedicated directory and hand back, per clip: the **filename**, **source
timestamp**, a **one-line description**, and **which finding it pairs with and why**. Then propose a
thread/post order that alternates clip → claim → clip.

If your project has its own long-form-content skill (e.g. `factory-marketing-recap`), its promo
clips may belong as part of that skill's own deliverable rather than a separate step — check whether
that's how this project already does it before treating this as a standalone task. Aim for 2-4
videos × 2-4 clips.

If the audience reads a different language than the source clip, supply a translated pull-quote,
attributed inline, kept to a single sentence. Translate the **image/rhetoric** the speaker is making
rather than substituting an idiom that flattens it, when the speaker is deliberately playing with a
figure of speech.

---

## Hard rules

- **Never post anything.** Produce files and draft copy; publishing is the user's call, every time.
  Do not upload, post, or DM without an explicit per-action go-ahead. No `RESULT:` contract — this is
  always a draft-only deliverable.
- **Quote briefly and attribute.** Short verbatim lines for identification and pull-quotes; never
  reproduce a transcript at length, and never republish someone's video as your own content. Clips
  are quotation in service of commentary — keep them short and always name the speaker.
- **Verify the claim before you amplify it.** If a clip asserts a number, check it against your own
  data before building a post around it — independent corroboration is the whole point of using a
  third-party clip, so confirm it actually corroborates before shipping it.
- **Keep yt-dlp current.** A stale build can 403 on audio downloads or warn about a missing JS
  runtime — `python3 -m pip install -U yt-dlp` is the usual fix.
- **Report what the video actually is.** If a video was billed as covering more than it does, say so
  rather than implying broader coverage than exists.

## Cost and time

| Item | Cost |
|---|---|
| Discovery (yt-dlp + Chrome) | free |
| Transcription, per 20-min video | ~$0.12 |
| Word-level boundary passes | ~$0.01 each |
| **Per video, end to end** | **~$0.15, roughly 10 minutes** |
