"""Swap a screencast's canvas for the same board in another language.

Re-renders a recording as a camera move over a stitched image of the target-language
board, lifting the speaker's webcam inset straight from the source so it stays in
sync, and keeping the original audio. See "Rebuilding the on-screen canvas in
another language" in SKILL.md for the method and the traps.

Usage:
    python helpers/canvas_swap.py --board board.png --source cut.mp4 \\
        --blocks dub/blocks.json --camera camera.py [--pip X0,Y0,X1,Y1] \\
        [--chrome 62] [START END] OUT.mp4

The camera module must expose VIEW_W, S (named rects), BLOCK_SECTION and
build_keys(blocks) — copy the one in the worked example and edit its numbers.

Original docstring follows.

Render an English-canvas version of a segment: board camera + webcam PiP + original audio.

Why the camera path is transcript-driven, not pixel-tracked
-----------------------------------------------------------
Template matching the recording against the English board locks onto the right
SECTION but not the right offset: the two boards share section order, not
coordinates, because English and Japanese text have different extents so every
section below the first shifts. There is no single scale+translate that maps one
board onto the other.

But we already know what the speaker is discussing at every second -- that is
exactly what dub/blocks.json encodes. So the camera path is authored: each
segment names a rect on the English board, and the renderer eases between them.
That is also what a human editor would do, and it is robust to layout drift.

Each keyframe is (t, x, y, w) in board pixels; height follows from the output
aspect. Between keyframes the camera eases with a cubic so pushes feel deliberate.
"""
import cv2, numpy as np, subprocess, json, sys
from pathlib import Path

BASE = Path(".")
SRC = Path("source.mp4")   # override with --source
OUT_W, OUT_H, FPS = 1280, 720, 30
PIP = (985, 552, 1280, 720)          # webcam box in the source frames


def ease(t):
    return 4 * t ** 3 if t < 0.5 else 1 - (-2 * t + 2) ** 3 / 2


def camera(keys, t):
    """Interpolate the (x, y, w) camera rect at time t."""
    if t <= keys[0][0]:
        return keys[0][1:]
    if t >= keys[-1][0]:
        return keys[-1][1:]
    for i in range(len(keys) - 1):
        t0, *a = keys[i]; t1, *b = keys[i + 1]
        if t0 <= t <= t1:
            u = ease((t - t0) / (t1 - t0))
            return [p + (q - p) * u for p, q in zip(a, b)]
    return keys[-1][1:]


def render(keys, t_start, t_end, out_path):
    board = cv2.imread(str(BASE / "board_en.png"))
    BH, BW = board.shape[:2]

    # webcam strip straight from the source, so it stays perfectly in sync
    pw, ph = PIP[2] - PIP[0], PIP[3] - PIP[1]
    cap = cv2.VideoCapture(str(SRC))
    src_fps = cap.get(cv2.CAP_PROP_FPS) or FPS
    cap.set(cv2.CAP_PROP_POS_MSEC, t_start * 1000)
    consumed = 0          # source frames pulled so far

    tmp = BASE / "frames.mp4"
    vw = cv2.VideoWriter(str(tmp), cv2.VideoWriter_fourcc(*"mp4v"), FPS, (OUT_W, OUT_H))
    n = int((t_end - t_start) * FPS)
    for i in range(n):
        t = t_start + i / FPS
        x, y, w = camera(keys, t)
        h = w * OUT_H / OUT_W
        x0, y0 = int(max(0, min(x, BW - w))), int(max(0, min(y, BH - h)))
        crop = board[y0:y0 + int(h), x0:x0 + int(w)]
        if crop.size == 0:
            continue
        frame = cv2.resize(crop, (OUT_W, OUT_H), interpolation=cv2.INTER_CUBIC)

        # Pull enough source frames to stay on the output clock. Reading one
        # source frame per output frame plays the webcam at src_fps/FPS speed --
        # at 60->30 that is half speed, drifting minutes behind by the end.
        want = int(round((i + 1) * src_fps / FPS))
        while consumed < want - 1:
            cap.grab(); consumed += 1
        ok, src = cap.read(); consumed += 1
        if ok:
            pip = src[PIP[1]:PIP[3], PIP[0]:PIP[2]]
            frame[OUT_H - ph:, OUT_W - pw:] = pip
        vw.write(frame)
    vw.release(); cap.release()

    subprocess.run(["ffmpeg", "-y", "-i", str(tmp), "-ss", f"{t_start}", "-i", str(SRC),
                    "-map", "0:v", "-map", "1:a", "-t", f"{t_end - t_start}",
                    "-c:v", "libx264", "-preset", "fast", "-crf", "20",
                    "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
                    str(out_path)], check=True, capture_output=True)
    print(f"{n} frames -> {out_path}")


if __name__ == "__main__":
    import camera as campath
    blocks_path = Path(sys.argv[4]) if len(sys.argv) > 4 else Path("edit/dub/blocks.json")
    blocks = json.loads(blocks_path.read_text())["blocks"]
    KEYS = campath.build_keys(blocks)
    a = float(sys.argv[1]) if len(sys.argv) > 1 else 0.0
    b = float(sys.argv[2]) if len(sys.argv) > 2 else blocks[-1]["end"]
    out = Path(sys.argv[3]) if len(sys.argv) > 3 else BASE / "canvas_en.mp4"
    print(f"{len(KEYS)} keyframes over {b-a:.1f}s")
    render(KEYS, a, b, out)
