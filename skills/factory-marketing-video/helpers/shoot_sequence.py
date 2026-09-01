"""Render a MULTI-SCENE animation matched to a clip's real length.

A 40-60s short makes three or four points. One scene held for the whole clip
wastes the format, and a scene rendered at some default length against a 50s
clip is obviously wrong. So the sequence is declared against the CLIP timeline:
each entry names an archetype and the span it covers, taken from the transcript
moments where the speaker turns to that point.

Each scene still renders as a pure function of ITS OWN local time, so archetypes
stay reusable and a scene never needs to know where it sits in the clip.

    python helpers/shoot_sequence.py scenes/sequence.json out.mp4 [--fps 24]
"""
import argparse, asyncio, json, shutil, subprocess, tempfile
from pathlib import Path
from playwright.async_api import async_playwright

XFADE = 0.45          # scenes cross-dissolve rather than hard-cut


async def grab(scene_html: Path, seq: dict, tmp: Path, fps: int, w: int, h: int):
    total = float(seq["duration"])
    lang = seq.get("lang", "en")
    scenes = seq["scenes"]
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=angle", "--use-angle=swiftshader",
                                          "--enable-webgl"])
        pages = {}
        for sc in {s["s"] for s in scenes}:      # one page per archetype, reused
            pg = await b.new_page(viewport={"width": w, "height": h}, device_scale_factor=1)
            await pg.goto(f"file://{scene_html.resolve()}?s={sc}&lang={lang}")
            await pg.wait_for_timeout(800)
            pages[sc] = pg

        n = int(total * fps)
        for i in range(n):
            t = i / fps
            idx = next((k for k, s in enumerate(scenes) if s["at"] <= t < s["until"]),
                       len(scenes) - 1)
            cur = scenes[idx]
            await pages[cur["s"]].evaluate(f"window.__render({t - cur['at']})")
            await pages[cur["s"]].locator("#stage").screenshot(path=str(tmp / f"f{i:05d}.png"))
            # cross-dissolve into the next scene rather than hard-cutting
            nxt = scenes[idx + 1] if idx + 1 < len(scenes) else None
            if nxt and t > cur["until"] - XFADE:
                k = (t - (cur["until"] - XFADE)) / XFADE
                await pages[nxt["s"]].evaluate(f"window.__render({t - nxt['at']})")
                await pages[nxt["s"]].locator("#stage").screenshot(path=str(tmp / "_b.png"))
                from PIL import Image
                a_im = Image.open(tmp / f"f{i:05d}.png").convert("RGB")
                b_im = Image.open(tmp / "_b.png").convert("RGB")
                Image.blend(a_im, b_im, min(1.0, max(0.0, k))).save(tmp / f"f{i:05d}.png")
        await b.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("sequence", type=Path)
    ap.add_argument("out", type=Path)
    # the sequence names its own episode file; --scene only overrides it
    ap.add_argument("--scene", type=Path, default=None)
    ap.add_argument("--fps", type=int, default=24)
    ap.add_argument("--w", type=int, default=1080)
    ap.add_argument("--h", type=int, default=1920)
    a = ap.parse_args()

    seq = json.loads(a.sequence.read_text())
    scene = a.scene or (a.sequence.parent / seq.get("scene_file", "scene-kit.html"))
    if not scene.exists():
        raise SystemExit(f"scene file not found: {scene}")
    tmp = Path(tempfile.mkdtemp())
    try:
        asyncio.run(grab(scene, seq, tmp, a.fps, a.w, a.h))
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-framerate", str(a.fps),
                        "-i", str(tmp / "f%05d.png"), "-c:v", "libx264", "-preset", "fast",
                        "-crf", "18", "-pix_fmt", "yuv420p", str(a.out)], check=True)
        print(f"{seq['duration']}s / {len(seq['scenes'])} scenes / lang={seq.get('lang','en')} -> {a.out}")
        for s in seq["scenes"]:
            print(f"  {s['at']:6.1f}-{s['until']:6.1f}  {s['s']:6}  {s.get('note','')}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
