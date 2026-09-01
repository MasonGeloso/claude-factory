#!/usr/bin/env python3
"""factory-marketing-dub helper — transcribe, clone, TTS, verify, assemble.

Every subcommand is independently runnable; the skill drives them in order.
See ../SKILL.md for the workflow and the reasoning behind the defaults.

Env:
  OPENAI_API_KEY   used for transcription
  ELEVENLABS_KEY   pasted by the user; trailing paste junk is auto-trimmed
"""
import argparse
import difflib
import json
import os
import re
import subprocess
import sys
import unicodedata
import urllib.error
import urllib.request

XI = "https://api.elevenlabs.io/v1"
OA = "https://api.openai.com/v1"
MODEL_TTS = "eleven_multilingual_v2"
MODEL_STT = "gpt-4o-transcribe"

# Phase 6 tight-mode timing. Measured: 0.40s reads as a breath, 0.7s+ as dead air.
LEAD, GAP, TAIL = 0.25, 0.40, 0.60
LOUDNORM = "loudnorm=I=-16:TP=-1.5:LRA=11"


def die(msg):
    sys.exit(f"error: {msg}")


def sh(args, **kw):
    r = subprocess.run(args, capture_output=True, text=True, **kw)
    if r.returncode:
        die(f"{args[0]} failed:\n{r.stderr.strip()}")
    return r.stdout


def dur(path):
    return float(sh(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                     "-of", "csv=p=0", path]).strip())


def el_key():
    k = (os.environ.get("ELEVENLABS_KEY") or os.environ.get("ELEVENLABS_API_KEY") or "").strip()
    if not k:
        die("ELEVENLABS_KEY not set")
    # A pasted key often carries trailing junk (measured: '...f56b039AT').
    m = re.match(r"(sk_[0-9a-f]{48})", k)
    if m and m.group(1) != k:
        print(f"note: trimmed {len(k) - len(m.group(1))} trailing char(s) from key", file=sys.stderr)
        k = m.group(1)
    return k


def oa_key():
    k = (os.environ.get("OPENAI_API_KEY") or "").strip()
    if not k:
        die("OPENAI_API_KEY not set")
    return k


def req(url, *, headers, data=None, method=None):
    r = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(r) as resp:
            return resp.read()
    except urllib.error.HTTPError as e:
        die(f"HTTP {e.code} from {url}\n{e.read().decode('utf-8', 'replace')[:600]}")


def multipart(fields, files):
    """Minimal multipart/form-data builder (avoids a requests dependency)."""
    b = "----jpdub7f3a9c1e"
    out = bytearray()
    for k, v in fields.items():
        out += f"--{b}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n".encode()
    for k, path in files.items():
        name = os.path.basename(path)
        out += (f"--{b}\r\nContent-Disposition: form-data; name=\"{k}\"; filename=\"{name}\"\r\n"
                f"Content-Type: application/octet-stream\r\n\r\n").encode()
        with open(path, "rb") as f:
            out += f.read()
        out += b"\r\n"
    out += f"--{b}--\r\n".encode()
    return bytes(out), f"multipart/form-data; boundary={b}"


def to_wav16(src, dst):
    sh(["ffmpeg", "-y", "-v", "error", "-i", src, "-vn", "-ac", "1", "-ar", "16000",
        "-c:a", "pcm_s16le", dst])
    return dst


# ---------------------------------------------------------------- transcribe

def transcribe(path):
    """Transcribe via gpt-4o-transcribe. Never download a local Whisper model for this."""
    tmp = path
    if not path.lower().endswith(".wav"):
        tmp = os.path.join(os.path.dirname(path) or ".", ".jpdub_stt.wav")
        to_wav16(path, tmp)
    body, ctype = multipart({"model": MODEL_STT, "language": "ja", "response_format": "text"},
                            {"file": tmp})
    out = req(f"{OA}/audio/transcriptions",
              headers={"Authorization": f"Bearer {oa_key()}", "Content-Type": ctype},
              data=body).decode("utf-8").strip()
    if tmp != path:
        os.remove(tmp)
    return out


def cmd_transcribe(a):
    print(transcribe(a.media))


# ---------------------------------------------------------------- voices / clone

def cmd_voices(a):
    h = {"xi-api-key": el_key()}
    s = json.loads(req(f"{XI}/user/subscription", headers=h))
    used, lim = s.get("character_count") or 0, s.get("character_limit") or 0
    print(f"tier={s.get('tier')}  chars={used:,}/{lim:,}"
          f"  ivc={s.get('can_use_instant_voice_cloning')}"
          f"  slots={s.get('voice_slots_used')}/{s.get('voice_limit')}")
    if lim and used > lim:
        print(f"WARNING: over quota by {used - lim:,} chars. TTS may still serve on "
              f"overage billing — report this to the user.")
    v = json.loads(req("https://api.elevenlabs.io/v2/voices?page_size=100", headers=h))
    mine = [x for x in v.get("voices", []) if x.get("category") == "cloned"]
    print(f"\n{len(mine)} cloned voice(s):")
    for x in mine:
        print(f"  {x['voice_id']}  {x.get('name')}")
    if not mine:
        print("  (none — clone one, see Phase 4)")


def cmd_clone(a):
    body, ctype = multipart(
        {"name": a.name, "remove_background_noise": "true",
         "description": a.description or "Cloned for redubbing"},
        {"files": a.audio})
    r = json.loads(req(f"{XI}/voices/add",
                       headers={"xi-api-key": el_key(), "Content-Type": ctype}, data=body))
    print(r["voice_id"])
    print(f"note: if '{os.path.basename(a.audio)}' came from an existing dub this is a "
          f"clone-of-a-clone — tell the user to ear-check it.", file=sys.stderr)


# ---------------------------------------------------------------- tts

def blocks(script_path):
    txt = open(script_path, encoding="utf-8").read()
    return [b.strip() for b in re.split(r"\n\s*\n", txt) if b.strip()]


def cmd_tts(a):
    bl = blocks(a.script)
    only = {int(x) for x in a.only.split(",")} if a.only else set(range(len(bl)))
    os.makedirs(a.outdir, exist_ok=True)
    total = 0
    for i, text in enumerate(bl):
        path = os.path.join(a.outdir, f"p{i:02d}.mp3")
        if i not in only:
            if os.path.exists(path):
                print(f"p{i:02d} {dur(path):6.2f}s  (kept)")
            continue
        payload = json.dumps({
            "text": text, "model_id": MODEL_TTS,
            "voice_settings": {"stability": a.stability, "similarity_boost": a.similarity,
                               "style": a.style, "use_speaker_boost": True},
        }).encode()
        data = req(f"{XI}/text-to-speech/{a.voice}?output_format=mp3_44100_192",
                   headers={"xi-api-key": el_key(), "Content-Type": "application/json"},
                   data=payload)
        with open(path, "wb") as f:
            f.write(data)
        total += len(text)
        print(f"p{i:02d} {dur(path):6.2f}s  {text[:36]}")
    print(f"\n{len(bl)} block(s), {total} chars generated -> {a.outdir}")
    print("NEXT: build, then `verify` the result. Phase 5 is not optional.")


# ---------------------------------------------------------------- verify

# Transcriber artifacts on synthetic audio — clipped vowels, not TTS misreads.
ARTIFACTS = {("ツール", "ツル"), ("ベータ", "ベタ"), ("ポートフォリオ", "ポトフォリオ"),
             ("気持ちいい", "気持ち"), ("重くて", "うまくて")}


KANJI = re.compile(r"[一-鿿]")
KANA_ONLY = re.compile(r"^[぀-ヿー]+$")


def norm(s):
    s = unicodedata.normalize("NFKC", s)
    return re.sub(r"[\s、。，．,\.！？!?「」『』（）\(\)〜~・]", "", s)


def classify(w, g):
    """Bucket one divergence. Only CHECK needs human attention.

    kana-ok  : script deliberately spelled a word in kana (Phase 5 fix) and the
               transcriber wrote it back as kanji. This is the fix working.
    noise    : single-character particle/長音 drift from the transcriber.
    artifact : known clipped-vowel mishears on synthetic audio, or the heard side
               is just a shortening of what was written.
    """
    if (w, g) in ARTIFACTS:
        return "artifact"
    if KANA_ONLY.match(w or "x") and KANJI.search(g or ""):
        return "kana-ok"
    if len(w) <= 1 and len(g) <= 1:
        return "noise"
    if g and len(g) < len(w) and g in w:
        return "artifact"
    return "CHECK"


def cmd_verify(a):
    heard = transcribe(a.media)
    want = norm("".join(blocks(a.script)))
    got = norm(heard)
    sm = difflib.SequenceMatcher(None, want, got, autojunk=False)
    diffs = [(want[i1:i2], got[j1:j2]) for op, i1, i2, j1, j2 in sm.get_opcodes() if op != "equal"]
    print("--- heard ---")
    print(heard)
    print(f"\n--- {len(diffs)} divergence(s), similarity {sm.ratio():.3f} ---")
    buckets = {}
    for w, g in diffs:
        buckets.setdefault(classify(w, g), []).append((w, g))
    for tag in ("CHECK", "artifact", "kana-ok", "noise"):
        for w, g in buckets.get(tag, []):
            print(f"  [{tag:8s}] script {w!r:22s} -> heard {g!r}")
    real = len(buckets.get("CHECK", []))
    if not real:
        print("\nPASS — no unexplained divergences.")
        return
    print(f"\n{real} needing a look:")
    print("  phonetically distant (使い勝手 -> すばやい開口) = TTS misread, fix with kana")
    print("  clipped/shortened (ツール -> ツル)             = transcriber, ignore")
    print("  unsure? slice that one block and re-transcribe it alone")
    sys.exit(1)


# ---------------------------------------------------------------- build

TRIM = ("silenceremove=start_periods=1:start_threshold=-50dB:start_silence=0.05:detection=peak,"
        "areverse,"
        "silenceremove=start_periods=1:start_threshold=-50dB:start_silence=0.05:detection=peak,"
        "areverse")


def trimmed(outdir, clip):
    """Strip the clip's own leading/trailing silence so GAP is the real gap.

    ElevenLabs mp3s carry 0.16-0.26s of padding (measured). Left in, a designed
    0.40s gap becomes 0.7-0.9s of actual silence.
    """
    src = os.path.join(outdir, clip)
    dst = os.path.join(outdir, f".trim_{clip}")
    if not os.path.exists(dst) or os.path.getmtime(dst) < os.path.getmtime(src):
        sh(["ffmpeg", "-y", "-v", "error", "-i", src, "-af", TRIM, dst])
    return dst


def plan(outdir, mode, anchors, video_len):
    clips = sorted(f for f in os.listdir(outdir) if re.fullmatch(r"p\d\d\.mp3", f))
    if not clips:
        die(f"no p*.mp3 in {outdir} — run `tts` first")
    paths = [trimmed(outdir, c) for c in clips]
    starts, t = [], LEAD
    if mode == "anchored":
        if not anchors:
            die("--mode anchored needs --anchors")
        an = [float(x) for x in anchors.split(",")]
        if len(an) != len(clips):
            die(f"{len(an)} anchors for {len(clips)} clips")
        end = 0.0
        for p, want in zip(paths, an):
            s = max(want, end + 0.35)
            starts.append(s)
            end = s + dur(p)
        t = end
    else:
        for p in paths:
            starts.append(t)
            t += dur(p) + GAP
        t -= GAP
    audio_len = t + TAIL
    return clips, paths, starts, audio_len


def cmd_build(a):
    video_len = dur(a.video)
    clips, paths, starts, audio_len = plan(a.outdir, a.mode, a.anchors, video_len)
    if a.mode == "anchored":
        audio_len = video_len
    parts, ins = [], []
    for i, (c, p, s) in enumerate(zip(clips, paths, starts)):
        ins += ["-i", p]
        parts.append(f"[{i}:a]adelay={int(s * 1000)}|{int(s * 1000)}[a{i}]")
        print(f"  {c} {s:7.2f} -> {s + dur(p):7.2f}")
    fc = (";".join(parts) + ";" + "".join(f"[a{i}]" for i in range(len(clips)))
          + f"amix=inputs={len(clips)}:normalize=0,apad,atrim=0:{audio_len:.3f},{LOUDNORM}[out]")
    mixed = os.path.join(a.outdir, "mixed.wav")
    fcfile = os.path.join(a.outdir, ".fc.txt")
    with open(fcfile, "w") as f:
        f.write(fc)
    sh(["ffmpeg", "-y", "-v", "error", *ins, "-filter_complex_script", fcfile,
        "-map", "[out]", "-ar", "48000", "-c:a", "pcm_s16le", mixed])
    print(f"\naudio {audio_len:.2f}s  video {video_len:.2f}s  mode={a.mode}")

    if a.mode == "speed":
        factor = video_len / audio_len
        print(f"speeding video {factor:.3f}x to preserve every frame (re-encode)")
        sh(["ffmpeg", "-y", "-v", "error", "-i", a.video, "-i", mixed,
            "-filter_complex", f"[0:v]setpts=PTS/{factor:.6f}[v]", "-map", "[v]", "-map", "1:a:0",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-c:a", "aac", "-b:a", "192k",
            "-movflags", "+faststart", a.out])
    else:
        keep = min(audio_len, video_len)
        if audio_len < video_len:
            print(f"trimming video tail: -{video_len - audio_len:.1f}s "
                  f"(report which footage this drops)")
        sh(["ffmpeg", "-y", "-v", "error", "-i", a.video, "-i", mixed,
            "-map", "0:v:0", "-map", "1:a:0", "-t", f"{keep:.3f}",
            "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", a.out])

    # NOTE: -v info is required. silencedetect logs at info level, so `-v error`
    # yields an empty stderr and this check silently always passes.
    r = subprocess.run(["ffmpeg", "-v", "info", "-i", mixed, "-af",
                        "silencedetect=n=-40dB:d=0.7", "-f", "null", "-"],
                       capture_output=True, text=True)
    gaps = re.findall(r"silence_start: ([\d.]+)", r.stderr)
    if a.mode == "anchored":
        print(f"dead-air gaps >0.7s: {len(gaps)} (expected — anchored mode trades gaps for sync)")
    elif gaps:
        print(f"dead-air gaps >0.7s: {len(gaps)} at {', '.join(gaps)}s — investigate, tight mode "
              f"should have none")
    else:
        print("dead-air gaps >0.7s: 0  (good)")
    print(f"\nwrote {a.out}  ({dur(a.out):.2f}s)")
    print("Input untouched. NEVER post this — hand it to the user.")


# ---------------------------------------------------------------- cli

def main():
    p = argparse.ArgumentParser(description="factory-marketing-dub helper")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("transcribe", help="gpt-4o-transcribe a media file (JP)")
    s.add_argument("media")
    s.set_defaults(fn=cmd_transcribe)

    s = sub.add_parser("voices", help="show ElevenLabs tier, quota, cloned voices")
    s.set_defaults(fn=cmd_voices)

    s = sub.add_parser("clone", help="instant-voice-clone from an audio sample")
    s.add_argument("audio")
    s.add_argument("--name", required=True)
    s.add_argument("--description")
    s.set_defaults(fn=cmd_clone)

    s = sub.add_parser("tts", help="generate one mp3 per script block")
    s.add_argument("script")
    s.add_argument("--voice", required=True)
    s.add_argument("--outdir", default="scratch")
    s.add_argument("--only", help="regenerate only these block indices, e.g. 4,6,8")
    s.add_argument("--stability", type=float, default=0.45)
    s.add_argument("--similarity", type=float, default=0.80)
    s.add_argument("--style", type=float, default=0.25)
    s.set_defaults(fn=cmd_tts)

    s = sub.add_parser("verify", help="re-transcribe and diff against the script (MANDATORY)")
    s.add_argument("media")
    s.add_argument("--script", required=True)
    s.set_defaults(fn=cmd_verify)

    s = sub.add_parser("build", help="assemble audio and mux into the video")
    s.add_argument("video")
    s.add_argument("--out", required=True)
    s.add_argument("--outdir", default="scratch")
    s.add_argument("--mode", choices=["tight", "anchored", "speed"], default="tight")
    s.add_argument("--anchors", help="comma-separated start times for --mode anchored")
    s.set_defaults(fn=cmd_build)

    a = p.parse_args()
    if getattr(a, "out", None) and os.path.abspath(a.out) == os.path.abspath(a.video):
        die("refusing to overwrite the source video — pick a new --out path")
    a.fn(a)


if __name__ == "__main__":
    main()
