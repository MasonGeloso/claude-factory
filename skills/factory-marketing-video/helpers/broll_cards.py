"""Build and composite source-screenshot B-roll cards onto a finished cut.

Turns browser screenshots of news articles / official statistics / product pages
into consistent centred cards and burns them into the video for a fixed hold.

Driven by one JSON spec:

{
  "video":  "/abs/final.mp4",
  "output": "/abs/final_overlays.mp4",
  "raw_dir":  "/abs/overlays/raw",
  "card_dir": "/abs/overlays/cards",
  "hold": 8.0,                        // default seconds on screen
  "cards": [
    {"src": "01_mof.jpg", "crop": [0, 352, 1050, 588], "start": 107.0,
     "title": "財務大臣談話（令和8年8月3日）",
     "note": "米国東部時間7月31日、日米が協調して円買い介入を実施",
     "source": "出典：財務省  mof.go.jp"},
    {"src": "04_toyota.jpg", "crop": [125, 152, 800, 292], "start": 310.0,
     "title": "トヨタ自動車　2027年3月期 第1四半期決算",
     "correction": "訂正：純利益は1兆4,770億円（前年同期比 +75.6%）",
     "source": "出典：Yahoo!ニュース"}
  ]
}

`correction` renders an amber caption bar -- use it when the narration states a
figure wrong and the take is worth keeping. Per-card `hold` or `end` overrides
the default.

Usage:
    python helpers/broll_cards.py spec.json                # build + composite
    python helpers/broll_cards.py spec.json --cards-only   # just render PNGs
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageFilter

BOLD = "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"
REG = "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"

NAVY, WHITE, GREY, LINE = (22, 35, 58), (255, 255, 255), (110, 118, 130), (222, 226, 232)
ACCENT = (214, 48, 49)
AMBER_BG, AMBER_TX, AMBER_LN = (255, 244, 224), (160, 82, 12), (232, 168, 74)
FADE = 0.35


def probe(video: Path, entries: str) -> str:
    return subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", entries, "-of", "default=nw=1:nk=1",
         str(video)], capture_output=True, text=True).stdout.strip()


def fit(draw, text, path, start, maxw, minsize=15):
    for size in range(start, minsize - 1, -1):
        f = ImageFont.truetype(path, size)
        if draw.textlength(text, font=f) <= maxw:
            return f
    return ImageFont.truetype(path, minsize)


def build_card(spec: dict, raw_dir: Path, out: Path, frame: tuple[int, int]) -> Path:
    fw, fh = frame
    # Caps exclude the shadow margin added below, and are set so every card keeps
    # a visible margin on all four sides of the frame.
    max_w, max_h = int(fw * 0.70), int(fh * 0.69)

    img = Image.open(raw_dir / spec["src"]).convert("RGB")
    if spec.get("crop"):
        img = img.crop(tuple(spec["crop"]))

    pad, foot_h = 20, 38
    head_h = 60 + (30 if spec.get("note") else 0)
    corr_h = 54 if spec.get("correction") else 0

    s = min((max_w - 2 * pad) / img.width,
            (max_h - head_h - corr_h - foot_h - 2 * pad) / img.height, 1.45)
    img = img.resize((max(1, int(img.width * s)), max(1, int(img.height * s))), Image.LANCZOS)

    cw = img.width + 2 * pad
    ch = head_h + img.height + corr_h + foot_h + 2 * pad
    card = Image.new("RGBA", (cw, ch), WHITE + (255,))
    d = ImageDraw.Draw(card)
    inner = cw - 2 * pad - 12

    d.rectangle([0, 0, cw, head_h], fill=NAVY)
    d.rectangle([0, 0, 6, head_h], fill=ACCENT)
    d.text((pad + 6, 12 if spec.get("note") else 18), spec["title"],
           font=fit(d, spec["title"], BOLD, 25, inner), fill=WHITE)
    if spec.get("note"):
        d.text((pad + 6, 46), spec["note"],
               font=fit(d, spec["note"], REG, 20, inner), fill=(178, 190, 208))

    y = head_h + pad
    card.paste(img, (pad, y))
    d.rectangle([pad, y, pad + img.width - 1, y + img.height - 1], outline=LINE)
    y += img.height + pad

    if corr_h:
        top = y - pad // 2
        d.rectangle([0, top, cw, top + corr_h], fill=AMBER_BG)
        d.rectangle([0, top, 6, top + corr_h], fill=AMBER_LN)
        d.text((pad + 6, top + 15), spec["correction"],
               font=fit(d, spec["correction"], BOLD, 23, inner), fill=AMBER_TX)

    if spec.get("source"):
        d.text((pad + 6, ch - foot_h + 8), spec["source"],
               font=ImageFont.truetype(REG, 17), fill=GREY)

    mask = Image.new("L", (cw, ch), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, cw - 1, ch - 1], 16, fill=255)
    card.putalpha(mask)

    m = 26
    canvas = Image.new("RGBA", (cw + 2 * m, ch + 2 * m), (0, 0, 0, 0))
    sh = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([m, m + 6, m + cw, m + ch + 6], 16, fill=(0, 0, 0, 105))
    canvas.alpha_composite(sh.filter(ImageFilter.GaussianBlur(13)))
    canvas.alpha_composite(card, (m, m))
    canvas.save(out)
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description="Build + composite B-roll source cards")
    ap.add_argument("spec", type=Path)
    ap.add_argument("--cards-only", action="store_true")
    args = ap.parse_args()

    cfg = json.loads(args.spec.read_text())
    video = Path(cfg["video"]).resolve()
    raw_dir = Path(cfg["raw_dir"]).resolve()
    card_dir = Path(cfg.get("card_dir", raw_dir.parent / "cards")).resolve()
    card_dir.mkdir(parents=True, exist_ok=True)
    hold = float(cfg.get("hold", 8.0))

    w, h = (int(x) for x in probe(video, "stream=width,height").split()[:2])
    dur = float(probe(video, "format=duration").splitlines()[0])

    plan = []
    for i, spec in enumerate(cfg["cards"], 1):
        png = build_card(spec, raw_dir, card_dir / f"card_{i}.png", (w, h))
        im = Image.open(png)
        a = float(spec["start"])
        b = float(spec.get("end", a + float(spec.get("hold", hold))))
        plan.append((png, a, b))
        print(f"  card_{i}: {im.width}x{im.height}  margins "
              f"{(w-im.width)//2}px side / {(h-im.height)//2}px top   {a:.1f}-{b:.1f}s")
        if im.width > w or im.height > h:
            sys.exit(f"card_{i} is larger than the frame")

    if args.cards_only:
        return

    cmd = ["ffmpeg", "-y", "-i", str(video)]
    for png, _, _ in plan:
        cmd += ["-loop", "1", "-i", str(png)]
    parts, prev = [], "0:v"
    for i, (_, a, b) in enumerate(plan, start=1):
        # The looped still shares the main video's timeline, so fade timings are
        # absolute -- no setpts shifting needed.
        parts.append(f"[{i}:v]format=rgba,fade=t=in:st={a:.3f}:d={FADE}:alpha=1,"
                     f"fade=t=out:st={b-FADE:.3f}:d={FADE}:alpha=1[c{i}]")
        parts.append(f"[{prev}][c{i}]overlay=(W-w)/2:(H-h)/2:"
                     f"enable='between(t,{a:.3f},{b:.3f})'[v{i}]")
        prev = f"v{i}"

    out = Path(cfg["output"]).resolve()
    cmd += ["-filter_complex", ";".join(parts), "-map", f"[{prev}]", "-map", "0:a",
            "-c:v", "libx264", "-preset", "fast", "-crf", "20", "-pix_fmt", "yuv420p",
            "-c:a", "copy", "-movflags", "+faststart", "-t", f"{dur:.3f}", str(out)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stderr[-2500:])
        sys.exit(1)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
