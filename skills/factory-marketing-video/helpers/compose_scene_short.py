"""Composite a rendered scene sequence with the real speaker feed and audio.

The scene kit reserves a speaker cell in its bottom rail; this pastes the actual
webcam into that cell and takes the audio from the finished short, so the art,
the voice and the speaker all stay locked together.

    python helpers/compose_scene_short.py --anim seq.mp4 --short EN_3.mp4 \
        --cam 28,1232,1052,1920 --box 553,1645,501,262 --out final.mp4
"""
import argparse, subprocess
from pathlib import Path
import cv2, numpy as np
from PIL import Image


def cover(img, bw, bh):
    s = max(bw / img.width, bh / img.height)
    im = img.resize((int(img.width * s) + 1, int(img.height * s) + 1), Image.LANCZOS)
    x, y = (im.width - bw) // 2, (im.height - bh) // 2
    return im.crop((x, y, x + bw, y + bh))


def rounded(img, r):
    m = Image.new("L", img.size, 0)
    from PIL import ImageDraw
    ImageDraw.Draw(m).rounded_rectangle([0, 0, img.width - 1, img.height - 1], r, fill=255)
    o = img.convert("RGBA"); o.putalpha(m); return o


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--anim", type=Path, required=True)
    ap.add_argument("--short", type=Path, required=True)
    ap.add_argument("--cam", required=True, help="x0,y0,x1,y1 in the short")
    ap.add_argument("--box", required=True, help="x,y,w,h speaker cell in the scene")
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--fps", type=int, default=20)
    a = ap.parse_args()

    cx = [int(v) for v in a.cam.split(",")]
    bx = [int(v) for v in a.box.split(",")]

    av = cv2.VideoCapture(str(a.anim))
    sv = cv2.VideoCapture(str(a.short))
    s_fps = sv.get(cv2.CAP_PROP_FPS) or a.fps
    n = int(av.get(cv2.CAP_PROP_FRAME_COUNT))
    W = int(av.get(cv2.CAP_PROP_FRAME_WIDTH)); H = int(av.get(cv2.CAP_PROP_FRAME_HEIGHT))

    tmp = a.out.with_suffix(".silent.mp4")
    vw = cv2.VideoWriter(str(tmp), cv2.VideoWriter_fourcc(*"mp4v"), a.fps, (W, H))
    consumed = 0
    last = None
    for i in range(n):
        ok, fr = av.read()
        if not ok:
            break
        # pull the speaker frame that belongs to this output frame
        want = int(round((i + 1) * s_fps / a.fps))
        while consumed < want - 1:
            sv.grab(); consumed += 1
        ok2, sfr = sv.read(); consumed += 1
        if ok2:
            last = sfr
        src = last if last is not None else None
        if src is not None:
            cam = Image.fromarray(cv2.cvtColor(src[cx[1]:cx[3], cx[0]:cx[2]], cv2.COLOR_BGR2RGB))
            cam = rounded(cover(cam, bx[2], bx[3]), 18)
            base = Image.fromarray(cv2.cvtColor(fr, cv2.COLOR_BGR2RGB)).convert("RGBA")
            base.alpha_composite(cam, (bx[0], bx[1]))
            fr = cv2.cvtColor(np.array(base.convert("RGB")), cv2.COLOR_RGB2BGR)
        vw.write(fr)
    vw.release(); av.release(); sv.release()

    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(tmp), "-i", str(a.short),
                    "-map", "0:v", "-map", "1:a", "-shortest",
                    "-c:v", "libx264", "-preset", "fast", "-crf", "19",
                    "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", str(a.out)],
                   check=True)
    tmp.unlink(missing_ok=True)
    print(f"{n} frames -> {a.out}")


if __name__ == "__main__":
    main()
