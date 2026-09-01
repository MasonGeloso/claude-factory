"""Build a vertical short (1080x1920) from a 16:9 source cut.

Structure of the output:

    [hook]   ~3s   a question in the speaker's cloned voice over a blurred,
                   muted first frame — gives the clip the context it would
                   otherwise be missing, and sets up the answer
    [body]   ~45s  the real clip: board panel, big webcam, animated captions
    [outro]  ~2.6s a card pointing at the full recap

Why it is rebuilt rather than cropped: the source is a wide screencast with the
webcam as a small inset in the bottom-right. A centre-crop to 9:16 loses the
board's outer thirds and buries the speaker. So each element is lifted out and
re-seated: headline and logo on top, board in the middle, webcam full-bleed
across the bottom third where a phone viewer actually looks.

The body's end must land on a sentence boundary — a short that stops mid-clause
reads as broken. `snap_end` does that against the caption source.
"""
from __future__ import annotations

import argparse, json, re, subprocess
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1080, 1920, 30
BG = (14, 17, 22)
FG = (255, 255, 255)
ACCENT = (255, 214, 10)

BOLD = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
REG = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"

HOOK_Y = 44
BOARD_Y, BOARD_H = 196, 830     # the graphic is the point — give it the room
CAP_Y, CAP_H = 1046, 176
CAM_Y, CAM_H = 1240, 680        # the whole bottom third
STROKE = 12                     # heavy outline, the way social captions are set


def rounded(img, r):
    m = Image.new("L", img.size, 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, img.width - 1, img.height - 1], r, fill=255)
    o = img.convert("RGBA"); o.putalpha(m); return o


def fit(img, bw, bh):
    s = min(bw / img.width, bh / img.height)
    return img.resize((max(1, int(img.width * s)), max(1, int(img.height * s))), Image.LANCZOS)


def cover(img, bw, bh):
    """Fill the box, cropping overflow — the webcam must not letterbox."""
    s = max(bw / img.width, bh / img.height)
    im = img.resize((int(img.width * s) + 1, int(img.height * s) + 1), Image.LANCZOS)
    x, y = (im.width - bw) // 2, (im.height - bh) // 2
    return im.crop((x, y, x + bw, y + bh))


def secs(x):
    h, m, rest = x.split(":"); s, ms = rest.split(",")
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000


def load_cues(path: Path):
    if path.suffix.lower() == ".srt":
        out = []
        for blk in path.read_text(encoding="utf-8").strip().split("\n\n"):
            ln = blk.strip().split("\n")
            m = re.match(r"([\d:,]+) --> ([\d:,]+)", ln[1]) if len(ln) > 2 else None
            if m:
                out.append((secs(m.group(1)), secs(m.group(2)), " ".join(ln[2:]).strip()))
        return out
    ws = [w for w in json.loads(path.read_text())["words"] if w.get("type", "word") == "word"]
    return [(w["start"], w["end"], w["text"].strip()) for w in ws]


TAIL = 0.42          # breath left after the final word


def snap_end(cues, target, window=8.0):
    """Nearest sentence end, plus a tail.

    Cutting on the exact end timestamp of the last word clips its decay and the
    clip sounds truncated even though the sentence is complete. Always leave a
    breath.
    """
    ends = [e for _, e, t in cues
            if abs(e - target) <= window and re.search(r"[.!?。！？]$", t.strip())]
    end = min(ends, key=lambda e: abs(e - target)) if ends else target
    # The tail must not reach into the next word, or the clip ends on a clipped
    # syllable and sounds worse than no tail at all.
    nxt = min((t0 for t0, _, _ in cues if t0 > end + 0.02), default=end + TAIL + 1)
    return end + max(0.10, min(TAIL, nxt - end - 0.12))


def snap_start(cues, target, window=8.0):
    """Nearest phrase start to `target`. Opening mid-clause loses the viewer."""
    starts = [t0 for t0, _, _ in cues if abs(t0 - target) <= window]
    return min(starts, key=lambda x: abs(x - target)) if starts else target


def to_words(cues, a, b, cjk, chunk=4):
    out = []
    for t0, t1, txt in cues:
        if t1 < a or t0 > b:
            continue
        parts = ([txt[i:i + chunk] for i in range(0, len(txt), chunk)]
                 if cjk and len(txt) > chunk else [txt])
        d = (t1 - t0) / len(parts)
        for k, p in enumerate(parts):
            out.append({"t": t0 + k * d - a, "e": t0 + (k + 1) * d - a, "s": p})
    return out


def group(ws, per):
    out, cur = [], []
    for i, w in enumerate(ws):
        cur.append(w)
        gap = i + 1 < len(ws) and ws[i + 1]["t"] - w["e"] > 0.45
        if len(cur) >= per or gap:
            out.append(cur); cur = []
    if cur:
        out.append(cur)
    return out


def wrap_text(d, text, font, maxw):
    rows, cur = [], ""
    for w in text.split(" "):
        t = (cur + " " + w).strip()
        if d.textlength(t, font=font) > maxw and cur:
            rows.append(cur); cur = w
        else:
            cur = t
    if cur:
        rows.append(cur)
    return rows


def wrap_cjk(d, text, font, maxw):
    rows, cur = [], ""
    for ch in text:
        if d.textlength(cur + ch, font=font) > maxw and cur:
            rows.append(cur); cur = ch
        else:
            cur += ch
    if cur:
        rows.append(cur)
    return rows


def draw_header(canvas, d, hook, logo, cjk):
    f = ImageFont.truetype(BOLD, 60)
    wrap = wrap_cjk if cjk else wrap_text
    rows = wrap(d, hook, f, W - 250)
    while len(rows) > 3 and f.size > 40:
        f = ImageFont.truetype(BOLD, f.size - 4)
        rows = wrap(d, hook, f, W - 250)
    y = HOOK_Y
    for r in rows:
        d.text((54, y), r, font=f, fill=FG)
        y += f.size + 14
    if logo:
        canvas.paste(logo, (W - logo.width - 44, HOOK_Y - 6), logo)


def draw_caption(d, line, t, font, cjk, caps=False):
    """Social-style captions: heavy black outline, active word in accent colour.

    The outline is what makes text readable over any background and is the single
    biggest difference between 'default-looking' and 'made for the feed'.
    """
    sep = "" if cjk else " "
    parts = [(w["s"].upper() if caps else w["s"]) for w in line]
    widths = [d.textlength(p, font=font) for p in parts]
    sw = d.textlength(sep, font=font) if sep else 0
    rows, row, rw = [], [], 0.0
    for i in range(len(parts)):
        if rw + widths[i] > W - 110 and row:
            rows.append((row, rw)); row, rw = [], 0.0
        row.append(i); rw += widths[i] + sw
    if row:
        rows.append((row, rw))
    y = CAP_Y + (CAP_H - len(rows) * 92) // 2
    for idxs, roww in rows:
        x = (W - roww) / 2
        for i in idxs:
            on = line[i]["t"] <= t <= line[i]["e"] + 0.08
            dy = -8 if on else 0
            d.text((x, y + dy), parts[i], font=font, fill=ACCENT if on else FG,
                   stroke_width=STROKE, stroke_fill=(0, 0, 0))
            x += widths[i] + sw
        y += 92


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", type=Path, required=True)
    ap.add_argument("--cues", type=Path, required=True)
    ap.add_argument("--start", type=float, required=True)
    ap.add_argument("--end", type=float, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--hook-audio", type=Path)
    ap.add_argument("--hook-text", default="")
    ap.add_argument("--cta", default="Full recap on our channel")
    ap.add_argument("--cta-sub", default="")
    ap.add_argument("--board", default="0,0,985,720")
    ap.add_argument("--cam", default="985,552,1280,720")
    ap.add_argument("--cjk", action="store_true")
    ap.add_argument("--words-per-line", type=int, default=4)
    ap.add_argument("--caps", action="store_true", help="upper-case captions (latin)")
    ap.add_argument("--no-cta", action="store_true",
                    help="drop the outro card — trailing silence over a static card "
                         "reads as the video having ended badly")
    ap.add_argument("--hard-end", type=float, default=None,
                    help="exact end time, skipping sentence snapping — for when the "
                         "natural sentence end runs into the next clause")
    a = ap.parse_args()

    cues = load_cues(a.cues)
    start = snap_start(cues, a.start)
    end = a.hard_end if a.hard_end else snap_end(cues, a.end)
    bx = [int(v) for v in a.board.split(",")]
    cx = [int(v) for v in a.cam.split(",")]
    lines = group(to_words(cues, start, end, a.cjk), a.words_per_line)

    hook_d = 0.0
    if a.hook_audio:
        hook_d = float(subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=nw=1:nk=1", str(a.hook_audio)],
            capture_output=True, text=True).stdout.strip()) + 0.55
    outro_d = 0.0 if a.no_cta else 2.6

    logo = Image.open("assets/logo_dark.png").convert("RGBA")
    logo = logo.resize((128, int(128 * logo.height / logo.width)), Image.LANCZOS)
    f_cap = ImageFont.truetype(BOLD, 62)
    f_cta = ImageFont.truetype(BOLD, 66)
    f_sub = ImageFont.truetype(REG, 40)

    cap = cv2.VideoCapture(str(a.source))
    src_fps = cap.get(cv2.CAP_PROP_FPS) or FPS
    cap.set(cv2.CAP_PROP_POS_MSEC, start * 1000)
    ok, first = cap.read()
    cap.set(cv2.CAP_PROP_POS_MSEC, start * 1000)
    consumed = 0

    tmp = a.out.with_suffix(".silent.mp4")
    vw = cv2.VideoWriter(str(tmp), cv2.VideoWriter_fourcc(*"mp4v"), FPS, (W, H))

    def compose(fr, blurred=False):
        canvas = Image.new("RGB", (W, H), BG)
        d = ImageDraw.Draw(canvas)
        draw_header(canvas, d, a.hook_text, logo, a.cjk)
        board = fit(Image.fromarray(cv2.cvtColor(fr[bx[1]:bx[3], bx[0]:bx[2]],
                                                 cv2.COLOR_BGR2RGB)), W - 56, BOARD_H)
        if blurred:
            board = board.filter(ImageFilter.GaussianBlur(9))
        bp = rounded(board, 18)
        canvas.paste(bp, ((W - bp.width) // 2, BOARD_Y + (BOARD_H - bp.height) // 2), bp)
        cam = cover(Image.fromarray(cv2.cvtColor(fr[cx[1]:cx[3], cx[0]:cx[2]],
                                                 cv2.COLOR_BGR2RGB)), W - 56, CAM_H)
        if blurred:
            cam = cam.filter(ImageFilter.GaussianBlur(11))
        cp = rounded(cam, 22)
        canvas.paste(cp, (28, CAM_Y), cp)
        return canvas, d

    # --- hook: the question fills the screen, revealing with the voiceover -----
    # Big type carries the setup; the blurred frame behind it only hints at what
    # is coming. Words appear in step with the narration so the eye follows.
    hook_words = (list(a.hook_text) if a.cjk else a.hook_text.split(" "))
    nh = int(hook_d * FPS)
    f_hook = ImageFont.truetype(BOLD, 108)
    wrapf = wrap_cjk if a.cjk else wrap_text
    rows_all = wrapf(ImageDraw.Draw(Image.new("RGB", (10, 10))), a.hook_text, f_hook, W - 130)
    while len(rows_all) > 5 and f_hook.size > 62:
        f_hook = ImageFont.truetype(BOLD, f_hook.size - 6)
        rows_all = wrapf(ImageDraw.Draw(Image.new("RGB", (10, 10))), a.hook_text, f_hook, W - 130)
    for i in range(nh):
        frac = min(1.0, (i / max(1, nh)) / 0.72)          # finish just before the cut
        shown = max(1, int(round(frac * len(hook_words))))
        text = ("" if a.cjk else " ").join(hook_words[:shown])
        c, d = compose(first, blurred=True)
        c = Image.blend(c, Image.new("RGB", (W, H), BG), 0.45)   # push the frame back
        d = ImageDraw.Draw(c)
        rows = wrapf(d, text, f_hook, W - 130)
        lh = f_hook.size + 24
        y = (H - len(rows) * lh) // 2 - 60
        for r in rows:
            d.text(((W - d.textlength(r, font=f_hook)) / 2, y), r, font=f_hook,
                   fill=FG, stroke_width=STROKE, stroke_fill=(0, 0, 0))
            y += lh
        lg = logo.resize((132, int(132 * logo.height / logo.width)), Image.LANCZOS)
        c.paste(lg, ((W - lg.width) // 2, 150), lg)
        vw.write(cv2.cvtColor(np.array(c), cv2.COLOR_RGB2BGR))

    n = int((end - start) * FPS)
    last = first
    for i in range(n):
        t = i / FPS
        want = int(round((i + 1) * src_fps / FPS))
        while consumed < want - 1:
            cap.grab(); consumed += 1
        ok, fr = cap.read(); consumed += 1
        if not ok:
            fr = last
        last = fr
        c, d = compose(fr)
        for line in lines:
            if line[0]["t"] - 0.25 <= t <= line[-1]["e"] + 0.35:
                draw_caption(d, line, t, f_cap, a.cjk, a.caps)
                break
        vw.write(cv2.cvtColor(np.array(c), cv2.COLOR_RGB2BGR))
    cap.release()

    for _ in range(int(outro_d * FPS)):
        c = Image.new("RGB", (W, H), BG)
        d = ImageDraw.Draw(c)
        lg = logo.resize((200, int(200 * logo.height / logo.width)), Image.LANCZOS)
        c.paste(lg, ((W - lg.width) // 2, 700), lg)
        rows = (wrap_cjk if a.cjk else wrap_text)(d, a.cta, f_cta, W - 200)
        y = 1040
        for r in rows:
            d.text(((W - d.textlength(r, font=f_cta)) / 2, y), r, font=f_cta, fill=FG)
            y += 84
        d.text(((W - d.textlength(a.cta_sub, font=f_sub)) / 2, y + 26), a.cta_sub,
               font=f_sub, fill=ACCENT)
        vw.write(cv2.cvtColor(np.array(c), cv2.COLOR_RGB2BGR))
    vw.release()

    body = end - start
    total = hook_d + body + outro_d
    if a.hook_audio:
        af = (f"[1:a]adelay=200|200,apad=whole_dur={hook_d:.3f},atrim=0:{hook_d:.3f}[h];"
              f"[2:a]atrim={start}:{end},asetpts=N/SR/TB,"
              f"adelay={int(hook_d*1000)}|{int(hook_d*1000)}[b];"
              f"[h][b]amix=inputs=2:dropout_transition=0:normalize=0,"
              f"apad=whole_dur={total:.3f}[a]")
        cmd = ["ffmpeg", "-y", "-v", "error", "-i", str(tmp), "-i", str(a.hook_audio),
               "-i", str(a.source), "-filter_complex", af, "-map", "0:v", "-map", "[a]"]
    else:
        cmd = ["ffmpeg", "-y", "-v", "error", "-i", str(tmp), "-ss", f"{start}",
               "-i", str(a.source), "-map", "0:v", "-map", "1:a"]
    cmd += ["-t", f"{total:.3f}", "-c:v", "libx264", "-preset", "fast", "-crf", "20",
            "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", str(a.out)]
    subprocess.run(cmd, check=True)
    tmp.unlink(missing_ok=True)
    print(f"{a.out.name}: hook {hook_d:.1f} + body {body:.1f} "
          f"(start {a.start:.1f}->{start:.1f}, end {a.end:.1f}->{end:.1f}) + cta {outro_d} = {total:.1f}s")


if __name__ == "__main__":
    main()
