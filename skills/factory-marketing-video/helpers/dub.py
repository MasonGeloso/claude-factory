"""Voice-clone dubbing: blocks -> clone -> synth -> fit -> mux -> captions.

Replaces a finished cut's audio with a scripted translation spoken in a clone of
the original speaker's voice, time-locked to the original edit.

Why not automatic dubbing
-------------------------
Hosted auto-dub runs its own ASR and MT. On a real recording that means false
starts and abandoned clauses get translated literally, and in a verb-final
language like Japanese an abandoned clause often hasn't reached the verb yet, so
it carries no meaning at all. Scripting also lets you FIX factual misstatements
in the dub, which matters when the video shows on-screen figures.

The timing model: per-block re-anchoring
----------------------------------------
The cut is split into blocks at real pauses. Each block is synthesised and fitted
to its OWN window on the original timeline. Because every block re-anchors to its
original start time, a line that lands short or long only ever drifts inside its
own block -- error cannot accumulate across a 15-minute video.

Fit order, least destructive first:
  1. within tolerance -> place as-is
  2. absorb up to --pad-allow of shortfall as silence at the block tail
     (that was a real pause in the original anyway)
  3. atempo, capped at +/-12% -- past that the voice sounds processed
  4. still out of range -> report it; the fix is rewriting the target text
     shorter or longer, never stretching harder

Subcommands:
    blocks   segment the cut into dubbing blocks (needs <name>.runs.json)
    clone    upload voice samples, save the voice_id (do this once, ever)
    samples  auto-pick clean voice-cloning samples from the cut
    synth    TTS each block, reporting fill % against its window
    build    fit every block, assemble the track, mux to <output>
    srt      build a caption file from the block script and timings

Usage:
    python helpers/dub.py samples --edit-dir DIR --video cut.mp4
    python helpers/dub.py clone   --edit-dir DIR --name "Speaker JA"
    python helpers/dub.py blocks  --edit-dir DIR --video cut.mp4 --anchors 107,137
    #   ... fill in each block's "target" text in blocks.json ...
    python helpers/dub.py synth   --edit-dir DIR [--only 4,17] [--force]
    python helpers/dub.py build   --edit-dir DIR --video cut.mp4 -o dubbed.mp4
    python helpers/dub.py srt     --edit-dir DIR --video dubbed.mp4
"""
from __future__ import annotations

import argparse, json, os, re, subprocess, sys, tempfile
from pathlib import Path

# High similarity carries the SOURCE language accent into the target. The clone is
# built from English speech, so for a Japanese audience low is correct.
SIMILARITY = 0.3
API = "https://api.elevenlabs.io/v1"
MODEL = os.environ.get("DUB_MODEL", "eleven_multilingual_v2")
TEMPO_MIN, TEMPO_MAX = 0.88, 1.12
SLACK_OK = 0.20


def key() -> str:
    """ElevenLabs key. Note the name: some setups export ELEVENLABS_KEY instead."""
    k = os.environ.get("ELEVENLABS_API_KEY") or os.environ.get("ELEVENLABS_KEY")
    if not k:
        env = Path(__file__).resolve().parent.parent / ".env"
        if env.exists():
            for line in env.read_text().splitlines():
                if line.startswith("ELEVENLABS_API_KEY="):
                    k = line.split("=", 1)[1].strip().strip("\"'")
    if not k:
        sys.exit("no ElevenLabs key (ELEVENLABS_API_KEY / ELEVENLABS_KEY / skill .env)")
    return k


def dur(p: Path) -> float:
    return float(subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", str(p)], capture_output=True, text=True).stdout.strip())


# ---------------------------------------------------------------- samples ----
def cmd_samples(a):
    """Pick the densest-speech windows, spread across the cut, for voice cloning.

    Instant Voice Cloning wants a few minutes of clean speech. Density matters
    more than length: a window that is 85% speech clones better than a longer
    one full of pauses.
    """
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from tighten import Envelope, extract_audio
    import numpy as np

    out = a.edit_dir / "voice_samples"; out.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        w = Path(tmp) / "a.wav"; extract_audio(a.video, w); env = Envelope(w)
        speech = (env.db > env.pause).astype(float)
        n = int(a.length / 0.005)
        cov = np.convolve(speech, np.ones(n) / n, mode="valid")
        picks, c = [], cov.copy()
        while len(picks) < a.count:
            i = int(np.argmax(c))
            picks.append((i * 0.005, float(cov[i])))
            c[max(0, i - n):i + n] = -1
        for k, (t, f) in enumerate(sorted(picks), 1):
            subprocess.run(["ffmpeg", "-y", "-ss", f"{t:.2f}", "-i", str(a.video),
                            "-t", str(a.length), "-vn", "-ac", "1", "-ar", "44100",
                            "-c:a", "libmp3lame", "-b:a", "192k", str(out / f"sample_{k}.mp3")],
                           check=True, capture_output=True)
            print(f"  sample {k}: {t:7.1f}s  speech {100*f:.0f}%")


def cmd_clone(a):
    import requests
    samples = sorted((a.edit_dir / "voice_samples").glob("*.mp3"))
    if not samples:
        sys.exit("no samples -- run `dub.py samples` first")
    files = [("files", (s.name, open(s, "rb"), "audio/mpeg")) for s in samples]
    r = requests.post(f"{API}/voices/add", headers={"xi-api-key": key()},
                      data={"name": a.name}, files=files, timeout=600)
    if r.status_code != 200:
        sys.exit(f"clone failed {r.status_code}: {r.text[:400]}")
    vid = r.json()["voice_id"]
    (a.edit_dir / "dub").mkdir(exist_ok=True)
    (a.edit_dir / "dub/voice.json").write_text(json.dumps({"voice_id": vid, "name": a.name}, indent=2))
    print(f"voice_id: {vid}   <- cloning is free; never redo this")


# ----------------------------------------------------------------- blocks ----
def cmd_blocks(a):
    runs = json.loads((a.edit_dir / "transcripts" / f"{a.video.stem}.runs.json").read_text())["runs"]
    anchors = [float(x) for x in a.anchors.split(",")] if a.anchors else []
    # Force a seam just before each on-screen event so the dub is always on-topic
    # while a card/graphic is up.
    forced = {max([r["index"] for r in runs if r["end"] <= t], default=-1) for t in anchors}

    blocks, cur = [], []
    for r in runs:
        cur.append(r)
        span = cur[-1]["end"] - cur[0]["start"]
        gap = r["gap_after"] if r["gap_after"] is not None else 99
        if ((r["index"] in forced and span >= 6.0)
                or (gap >= a.min_gap and span >= a.min_block)
                or span >= a.max_block):
            blocks.append(cur); cur = []
    if cur:
        blocks.append(cur)

    out = []
    for i, b in enumerate(blocks, 1):
        start, end = b[0]["start"], b[-1]["end"]
        tail = min(b[-1]["gap_after"] or 0.0, 0.45)
        out.append({"id": i, "start": round(start, 3), "end": round(end + tail, 3),
                    "duration": round(end + tail - start, 3),
                    "source": " ".join(r["text"].strip() for r in b), "target": "",
                    "has_anchor": any(start <= t <= end for t in anchors)})
    p = a.edit_dir / "dub/blocks.json"; p.parent.mkdir(exist_ok=True)
    p.write_text(json.dumps({"blocks": out}, indent=2, ensure_ascii=False))
    tot = sum(b["duration"] for b in out)
    print(f"{len(out)} blocks, mean {tot/len(out):.1f}s, "
          f"{sum(1 for b in out if b['has_anchor'])} containing an anchor -> {p}")


# ------------------------------------------------------------------ synth ----

# --------------------------------------------------------------- quality ----
# Fitting a script to a duration gives constant numeric feedback, so it eats every
# iteration; script quality is silent and gets none. That asymmetry shipped a dub a
# native viewer could not follow, with the lesson already written down and skipped.
# So the passes are a gate in the tool, not advice in a runbook.
QUALITY_PASSES = ("humanizer", "terminology", "pronunciation")


def quality_ok(edit_dir):
    """Every pass recorded against the CURRENT script, or synthesis is refused."""
    import hashlib
    data = json.loads((edit_dir / "dub/blocks.json").read_text())
    script = "\u0000".join(b.get("target", "") for b in data["blocks"])
    digest = hashlib.sha256(script.encode()).hexdigest()[:16]
    q = data.get("quality") or {}
    missing = [p for p in QUALITY_PASSES if not q.get(p)]
    stale = q.get("script") not in (None, digest)
    return digest, missing, stale, q


# Reading failures observed in shipped output. A regex cannot judge whether a kanji
# is ambiguous, so this is a curated list and it GROWS: every time a synthesiser is
# heard to read something wrong, add it here with the kana that forces the reading.
RISKY_READINGS = {
    "鈍っ":  "にぶっ",   # read with the on-reading: 鈍って -> ドンって
    "転ん":  "ころん",   # heard as 終わった / 滅んだ
    "転が":  "ころが",
    "効い":  "きい",     # heard as 兼ねて / 跳ね返って
    "被っ":  "かぶっ",
    "空い":  "あい",
    "止ま":  "とま",
    "細っ":  "ほそっ",   # heard as 失って / 使った (S1_funnel dub, 2026-08-19) -- ASR-diff caught
                        # it 3/3 occurrences in one block, all changing the sentence's meaning
    "成り立":"なりた",   # heard as 重ねちゃわない / 乗り出す / 乗り立つ, 4/4 attempts (S1_funnel,
                        # 2026-08-19) -- kana renders awkwardly in captions, so prefer rephrasing
                        # around it (e.g. 起きる) over the kana substitution when the caption matters
    "減っ":  "へっ",     # heard as 離っている / dropped context-dependent, only in a longer
                        # multi-sentence block (S1_funnel, 2026-08-19) -- also: shorter, more
                        # isolated blocks were consistently more reliable across this whole
                        # session than longer multi-sentence ones. Splitting a block is a real
                        # mitigation, not just a kana substitution.
    "頼り":  "たより",   # heard as あおりになる / よりになる / 代理になる -- failed 6/6 attempts
                        # across three different surrounding rephrasings (S1_funnel, 2026-08-19).
                        # The word itself is the problem, not the sentence around it -- when a
                        # word fails across multiple rewrites, stop rephrasing and kana it.
    "речь": "",          # placeholder guard: never let a non-target script through
}


def cmd_qa(a):
    """Lint the readings a synthesiser gets wrong, and record the passes."""
    import hashlib
    path = a.edit_dir / "dub/blocks.json"
    data = json.loads(path.read_text())
    hits = {}
    for b in data["blocks"]:
        t = b.get("target", "")
        for bad, kana in RISKY_READINGS.items():
            if bad and bad in t:
                hits.setdefault((bad, kana), []).append(b["id"])
    if hits:
        print("  KNOWN mis-readings present — rewrite the stem in kana so the")
        print("  synthesiser cannot choose:")
        for (bad, kana), ids in sorted(hits.items(), key=lambda kv: -len(kv[1])):
            print(f"    {bad} -> {kana}    blocks {','.join(str(i) for i in ids)}")
    else:
        print("  no known mis-readings in the script")
    # anything non-Japanese that slipped into a Japanese script reads as a defect
    foreign = {b["id"] for b in data["blocks"]
               if re.search(r"[A-Za-z]{4,}", b.get("target", ""))}
    if foreign:
        print(f"\n  latin words present in blocks {sorted(foreign)} — confirm each is a")
        print("  term the target-language press actually uses, not a transliteration")
    if a.mark:
        script = "\u0000".join(b.get("target", "") for b in data["blocks"])
        data["quality"] = {p: True for p in QUALITY_PASSES}
        data["quality"]["script"] = hashlib.sha256(script.encode()).hexdigest()[:16]
        data["quality"]["note"] = a.note or ""
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False))
        print(f"\n  recorded {', '.join(QUALITY_PASSES)} — synth unblocked for THIS script")
        print("  (any later edit to a target line re-arms the gate)")
    else:
        print("\n  NOT recorded. Run all three passes, then re-run with --mark.")


def cmd_synth(a):
    import requests
    digest, missing, stale, q = quality_ok(a.edit_dir)
    if missing or stale:
        why = (f"script changed since the passes were recorded ({q.get('script')} -> {digest})"
               if stale else f"never run: {', '.join(missing)}")
        sys.exit(
            "REFUSING TO SYNTHESISE — the script has not cleared its quality passes.\n"
            f"  {why}\n"
            "  A dub script is not finished when it FITS. Fitting is measured in seconds and\n"
            "  eats every iteration; quality is silent and gets none. That is how a dub ships\n"
            "  that a native speaker cannot follow.\n\n"
            "  Required before any block is synthesised:\n"
            "    1. de-AI / naturalness pass on the target language (JA: the humanizer-ja skill)\n"
            "    2. terminology audit — how the target language's own press writes each term,\n"
            "       not a transliteration of the English\n"
            "    3. pronunciation lint — ambiguous-reading kanji rewritten in kana\n\n"
            "  See what needs fixing:   dub.py --edit-dir . qa\n"
            "  Record them and unblock: dub.py --edit-dir . qa --mark\n"
            "  Re-run the passes after EVERY length rewrite — the gate re-arms on script change.")
    vid = json.loads((a.edit_dir / "dub/voice.json").read_text())["voice_id"]
    blocks = json.loads((a.edit_dir / "dub/blocks.json").read_text())["blocks"]
    only = {int(x) for x in a.only.split(",")} if a.only else None
    audio = a.edit_dir / "dub/audio"; audio.mkdir(parents=True, exist_ok=True)
    for b in blocks:
        if only and b["id"] not in only:
            continue
        txt = b.get("target", "").strip()
        if not txt:
            continue
        out = audio / f"block_{b['id']:02d}.mp3"
        if out.exists() and not a.force:
            continue
        r = requests.post(f"{API}/text-to-speech/{vid}",
                          headers={"xi-api-key": key(), "Content-Type": "application/json"},
                          json={"text": txt, "model_id": MODEL,
                                "voice_settings": {"stability": 0.45, "similarity_boost": SIMILARITY,
                                                   "style": 0.0, "use_speaker_boost": True}},
                          timeout=300)
        if r.status_code != 200:
            print(f"  [{b['id']:02d}] FAILED {r.status_code}: {r.text[:160]}"); continue
        out.write_bytes(r.content)
        d = dur(out); fill = d / b["duration"]
        # chars/sec varies hugely with content -- report it so the rewrite is
        # measured against THIS block, not a global constant
        flag = "  <-- rewrite" if not (0.88 <= fill <= 1.08) else ""
        print(f"  [{b['id']:02d}] {d:6.2f}s /{b['duration']:6.2f}s = {fill:4.0%}  "
              f"{len(txt)/d:4.1f} ch/s{flag}")


# ------------------------------------------------------------------ build ----
def cmd_build(a):
    blocks = json.loads((a.edit_dir / "dub/blocks.json").read_text())["blocks"]
    audio, work = a.edit_dir / "dub/audio", a.edit_dir / "dub/fitted"
    work.mkdir(parents=True, exist_ok=True)
    parts, problems = [], []
    for b in blocks:
        src = audio / f"block_{b['id']:02d}.mp3"
        if not src.exists():
            problems.append((b["id"], "no audio")); continue
        target, actual = b["duration"], dur(src)
        absorbed = min(max(0.0, target - actual), a.pad_allow)
        eff = target - absorbed
        tempo = 1.0 if abs(actual - eff) <= SLACK_OK else min(max(actual / eff, TEMPO_MIN), TEMPO_MAX)
        ratio = actual / target
        if not (TEMPO_MIN <= ratio <= TEMPO_MAX) and abs(ratio - 1) > 0.02:
            problems.append((b["id"], f"{ratio:.0%} — rewrite {'shorter' if ratio>1 else 'longer'}"))
        af = f"atempo={tempo:.4f}," if abs(tempo - 1) > 0.001 else ""
        out = work / f"block_{b['id']:02d}.wav"
        subprocess.run(["ffmpeg", "-y", "-i", str(src), "-af",
                        f"{af}apad=whole_dur={target:.3f}", "-t", f"{target:.3f}",
                        "-ac", "1", "-ar", "48000", str(out)], check=True, capture_output=True)
        parts.append((b["start"], out))

    total = dur(a.video)
    inputs, filt = [], []
    for i, (start, p) in enumerate(parts):
        inputs += ["-i", str(p)]
        filt.append(f"[{i}:a]adelay={int(start*1000)}|{int(start*1000)}[d{i}]")
    filt.append("".join(f"[d{i}]" for i in range(len(parts)))
                + f"amix=inputs={len(parts)}:dropout_transition=0:normalize=0[out]")
    track = a.edit_dir / "dub/track.wav"
    subprocess.run(["ffmpeg", "-y", *inputs, "-filter_complex", ";".join(filt),
                    "-map", "[out]", "-t", f"{total:.3f}", "-ar", "48000", "-ac", "2",
                    str(track)], check=True, capture_output=True)
    subprocess.run(["ffmpeg", "-y", "-i", str(a.video), "-i", str(track),
                    "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac",
                    "-b:a", "192k", "-shortest", str(a.output)], check=True, capture_output=True)
    print(f"assembled {len(parts)} blocks -> {a.output}")
    for bid, why in problems:
        print(f"  [{bid:02d}] {why}")


# -------------------------------------------------------------------- srt ----
def cmd_srt(a):
    """Captions from the block script.

    No re-transcription needed: each block's audio was fitted to fill its window,
    so distributing the block's text across that window by character count lands
    within a few hundred ms -- fine for subtitles, and it guarantees the captions
    match the spoken script exactly (including any corrections made in it).
    """
    blocks = json.loads((a.edit_dir / "dub/blocks.json").read_text())["blocks"]
    sent = re.compile(r"(?<=[。？！.!?])")
    clause = re.compile(r"(?<=[、,])")

    def cues_for(text):
        out = []
        for p in [x for x in sent.split(text) if x.strip()]:
            if len(p) <= a.max_chars:
                out.append(p); continue
            chunk = ""
            for seg in clause.split(p):
                if chunk and len(chunk) + len(seg) > a.max_chars:
                    out.append(chunk); chunk = seg
                else:
                    chunk += seg
            if chunk:
                out.append(chunk)
        return out

    def ts(t):
        h, m, s = int(t // 3600), int(t % 3600 // 60), t % 60
        return f"{h:02d}:{m:02d}:{s:06.3f}".replace(".", ",")

    cues = []
    for b in blocks:
        txt = b.get("target", "").strip()
        if not txt:
            continue
        parts = cues_for(txt); total = sum(len(p) for p in parts)
        span = max(0.5, b["duration"] - 0.35); t = b["start"]
        for p in parts:
            d = max(1.1, span * len(p) / total)
            cues.append((t, min(t + d, b["end"]), p.strip())); t += d
    for i in range(len(cues) - 1):
        if cues[i][1] > cues[i + 1][0]:
            cues[i] = (cues[i][0], max(cues[i][0] + 0.4, cues[i + 1][0] - 0.05), cues[i][2])
    D = dur(a.video)
    cues = [(x, min(z, D - 0.05), t) for x, z, t in cues if x < D - 0.1]

    out = a.edit_dir / "upload/captions.srt"; out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(f"{i}\n{ts(x)} --> {ts(z)}\n{t}\n"
                             for i, (x, z, t) in enumerate(cues, 1)), encoding="utf-8")
    print(f"{len(cues)} cues, mean {sum(z-x for x,z,_ in cues)/len(cues):.1f}s, "
          f"longest line {max(len(t) for _,_,t in cues)} chars -> {out}")


ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
ap.add_argument("--edit-dir", type=Path, required=True)
sub = ap.add_subparsers(dest="cmd", required=True)

s = sub.add_parser("samples"); s.add_argument("--video", type=Path, required=True)
s.add_argument("--count", type=int, default=5); s.add_argument("--length", type=float, default=45)
s.set_defaults(f=cmd_samples)
s = sub.add_parser("clone"); s.add_argument("--name", default="Dub Voice"); s.set_defaults(f=cmd_clone)
s = sub.add_parser("blocks"); s.add_argument("--video", type=Path, required=True)
s.add_argument("--anchors", default=""); s.add_argument("--min-gap", type=float, default=0.40)
s.add_argument("--min-block", type=float, default=16.0); s.add_argument("--max-block", type=float, default=30.0)
s.set_defaults(f=cmd_blocks)
q = sub.add_parser("qa")
q.add_argument("--mark", action="store_true",
               help="record that all three passes were run on THIS script")
q.add_argument("--note", default="")
q.set_defaults(f=cmd_qa)
s = sub.add_parser("synth"); s.add_argument("--only"); s.add_argument("--force", action="store_true")
s.set_defaults(f=cmd_synth)
s = sub.add_parser("build"); s.add_argument("--video", type=Path, required=True)
s.add_argument("-o", "--output", type=Path, required=True)
s.add_argument("--pad-allow", type=float, default=0.45); s.set_defaults(f=cmd_build)
s = sub.add_parser("srt"); s.add_argument("--video", type=Path, required=True)
s.add_argument("--max-chars", type=int, default=34); s.set_defaults(f=cmd_srt)

args = ap.parse_args(); args.f(args)
