# -*- coding: utf-8 -*-
"""Stage 6 — rescale the recording onto the intended timeline, anchor the voice-over,
write the SRT, and mux. Also burns a subtitled copy for muted-autoplay feeds."""
import json, os, re, subprocess
from _config import load, rel

cfg = load()
V = cfg.get("voice") or {}
ANCHORS = V.get("anchors", [])
TARGET_EXTRA = cfg["end_hold_s"]

TRIM = ("silenceremove=start_periods=1:start_threshold=-50dB:start_silence=0.05:detection=peak,"
        "areverse,"
        "silenceremove=start_periods=1:start_threshold=-50dB:start_silence=0.05:detection=peak,"
        "areverse")

def sh(c): subprocess.run(c, check=True, capture_output=True)
def dur(p):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                 "-of", "default=nw=1:nk=1", p],
                                capture_output=True, text=True).stdout)

raw = open(rel(cfg, "webraw.txt")).read().strip()
cast_dur = json.loads(open(rel(cfg, cfg.get("cast_final", "final.cast"))).read().splitlines()[-1])[0]
TARGET = cast_dur + TARGET_EXTRA

# --- locate the animation span via the two marker frames -----------------------------
FPS = 50
cx, cy = cfg["width"] // 2 - 3, cfg["height"] // 2 - 3
buf = subprocess.run(["ffmpeg", "-v", "error", "-i", raw,
                      "-vf", f"fps={FPS},crop=6:6:{cx}:{cy}",
                      "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
n = len(buf) // 108
def is_marker(i):
    px = buf[i * 108:(i + 1) * 108]           # magenta
    return px[0] > 200 and px[2] > 200 and px[1] < 80

# Collect every marker RUN. The recorder emits a couple of blank warm-up frames BEFORE the
# hold, so scanning from frame 0 for "still a marker" bails immediately and reports t0=0 —
# a drift that reads as a page bug for hours. Take run[0]'s end and run[-1]'s start.
runs, cur = [], None
for i in range(n):
    m = is_marker(i)
    if m and cur is None: cur = i
    if not m and cur is not None: runs.append((cur, i - 1)); cur = None
if cur is not None: runs.append((cur, n - 1))
if len(runs) < 2:
    raise SystemExit(f"expected a start and an end marker, found {len(runs)}: {runs}")
t0 = (runs[0][1] + 1) / FPS
t1 = runs[-1][0] / FPS
span = t1 - t0
scale = TARGET / span
print(f"marker runs (s): {[(round(a/FPS,2), round(b/FPS,2)) for a, b in runs]}")
print(f"t0={t0:.2f} t1={t1:.2f} span={span:.2f}s -> target {TARGET:.2f}s (scale {scale:.4f})")

OUT = rel(cfg, cfg["out_basename"])
os.makedirs(os.path.dirname(OUT), exist_ok=True)

# --- voice-over anchored on the same timeline ----------------------------------------
have_audio = bool(ANCHORS)
if have_audio:
    adir = rel(cfg, V.get("audio_dir", "audio"))
    os.makedirs(os.path.join(adir, "trim"), exist_ok=True)
    ins, filt = [], []
    for idx, a in enumerate(ANCHORS):
        src = os.path.join(adir, f"p{idx:02d}.mp3")
        dst = os.path.join(adir, "trim", f"p{idx:02d}.wav")
        sh(["ffmpeg", "-y", "-v", "error", "-i", src, "-af", TRIM,
            "-ar", "48000", "-ac", "2", dst])
        ins += ["-i", dst]
        filt.append(f"[{idx}:a]adelay={int(a*1000)}|{int(a*1000)}[a{idx}]")
        print(f"  p{idx:02d} @ {a:5.2f}s  len {dur(dst):4.2f}s  ends {a+dur(dst):5.2f}s")
    mix = "".join(f"[a{i}]" for i in range(len(ANCHORS)))
    fc = (";".join(filt) + f";{mix}amix=inputs={len(ANCHORS)}:normalize=0:duration=longest,"
          f"apad,atrim=0:{TARGET}[out]")
    vo = rel(cfg, "vo.wav")
    sh(["ffmpeg", "-y", "-v", "error"] + ins + ["-filter_complex", fc, "-map", "[out]",
        "-ar", "48000", "-ac", "2", "-c:a", "pcm_s16le", vo])
    print("vo track:", round(dur(vo), 2), "s")

    # Subtitles come from the DISPLAY script. The spoken script has words respelled so the
    # TTS reads them correctly; those spellings must never reach the screen.
    disp_path = rel(cfg, V.get("display_script") or V["script"])
    disp = [x.strip() for x in re.split(r"\n\s*\n", open(disp_path, encoding="utf-8").read())
            if x.strip()]
    assert len(disp) == len(ANCHORS), f"{len(disp)} subtitle blocks vs {len(ANCHORS)} anchors"
    def ts(t):
        h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
        return f"{h:02d}:{m:02d}:{s:06.3f}".replace(".", ",")
    srt = f"{OUT}.{cfg.get('sub_lang','ja')}.srt"
    with open(srt, "w", encoding="utf-8") as f:
        for i, (a, text) in enumerate(zip(ANCHORS, disp), 1):
            d = dur(os.path.join(adir, "trim", f"p{i-1:02d}.wav"))
            f.write(f"{i}\n{ts(a)} --> {ts(min(a + d + 0.35, TARGET))}\n{text}\n\n")
    print("wrote", srt)

# --- final mux ------------------------------------------------------------------------
vf = (f"[0:v]trim={t0}:{t1},setpts=(PTS-STARTPTS)*{scale},fps=30,"
      f"scale={cfg['width']}:{cfg['height']}:flags=lanczos,format=yuv420p[v]")
if have_audio:
    vf += f";[1:a]afade=t=in:st=0:d=0.06,afade=t=out:st={TARGET-0.5}:d=0.5[a]"

for ext, vcodec, extra in (("mp4", "libx264", ["-preset", "slow", "-crf", "19",
                                               "-movflags", "+faststart"]),
                           ("webm", "libvpx-vp9", ["-crf", "28", "-b:v", "0", "-row-mt", "1"])):
    cmd = ["ffmpeg", "-y", "-v", "error", "-i", raw]
    if have_audio: cmd += ["-i", rel(cfg, "vo.wav")]
    cmd += ["-filter_complex", vf, "-map", "[v]"]
    if have_audio:
        cmd += ["-map", "[a]"] + (["-c:a", "aac", "-b:a", "192k"] if ext == "mp4"
                                  else ["-c:a", "libopus", "-b:a", "160k"])
    cmd += ["-c:v", vcodec] + extra + ["-t", f"{TARGET:.3f}", f"{OUT}.{ext}"]
    sh(cmd)
    print(f"{OUT}.{ext}  {os.path.getsize(OUT+'.'+ext)//1024} KB  {dur(OUT+'.'+ext):.2f}s")

if have_audio and cfg.get("subtitles", True):
    # ffmpeg's ASS PlayResY defaults to 288, so FontSize scales ~5x on a 1440-tall frame:
    # 8 lands at ~40px, while 25 renders ~80px and swamps the frame. MarginV must clear
    # whatever chrome sits at the bottom (a dock will otherwise render OVER the line).
    style = cfg.get("sub_style",
                    "FontName=Noto Sans CJK JP,FontSize=8,PrimaryColour=&H00F5F5F5,"
                    "OutlineColour=&HC8000000,BorderStyle=1,Outline=1,Shadow=1,"
                    "Alignment=2,MarginV=31")
    sub = f"{OUT}-subbed.mp4"
    sh(["ffmpeg", "-y", "-v", "error", "-i", f"{OUT}.mp4",
        "-vf", f"subtitles={OUT}.{cfg.get('sub_lang','ja')}.srt:force_style='{style}'",
        "-c:v", "libx264", "-preset", "slow", "-crf", "19", "-pix_fmt", "yuv420p",
        "-c:a", "copy", "-movflags", "+faststart", sub])
    print(f"{sub}  {os.path.getsize(sub)//1024} KB  (burned-in subtitles)")
