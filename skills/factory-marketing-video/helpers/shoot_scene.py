"""Frame-grab a deterministic HTML scene to PNGs, then encode.

Scenes in scenes/ expose `window.__render(t)` as a PURE function of time, so the
grabber can seek to an exact timestamp and get an identical frame every run. That
is what makes captures reproducible and lets the beat sheet be driven from a
transcript rather than hand-keyframed.

    python helpers/shoot_scene.py scenes/scene-mechanism-vertical.html out.mp4 \
        --dur 9 --fps 24 --w 1080 --h 1920 [--query d=3]
"""
import argparse, asyncio, shutil, subprocess, tempfile
from pathlib import Path
from playwright.async_api import async_playwright


async def grab(scene: Path, tmp: Path, dur: float, fps: int, w: int, h: int, query: str):
    url = f"file://{scene.resolve()}" + (f"?{query}" if query else "")
    async with async_playwright() as p:
        # swiftshader so this works headless on a box with no GPU
        b = await p.chromium.launch(args=["--use-gl=angle", "--use-angle=swiftshader",
                                          "--enable-webgl"])
        pg = await b.new_page(viewport={"width": w, "height": h}, device_scale_factor=1)
        await pg.goto(url)
        await pg.wait_for_timeout(900)          # let fonts and the GL context settle
        for i in range(int(dur * fps)):
            await pg.evaluate(f"window.__render({i / fps})")
            await pg.locator("#stage").screenshot(path=str(tmp / f"f{i:05d}.png"))
        await b.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("scene", type=Path)
    ap.add_argument("out", type=Path)
    ap.add_argument("--dur", type=float, default=9.0)
    ap.add_argument("--fps", type=int, default=24)
    ap.add_argument("--w", type=int, default=1080)
    ap.add_argument("--h", type=int, default=1920)
    ap.add_argument("--query", default="")
    a = ap.parse_args()

    tmp = Path(tempfile.mkdtemp())
    try:
        asyncio.run(grab(a.scene, tmp, a.dur, a.fps, a.w, a.h, a.query))
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-framerate", str(a.fps),
                        "-i", str(tmp / "f%05d.png"), "-c:v", "libx264", "-preset", "fast",
                        "-crf", "18", "-pix_fmt", "yuv420p", str(a.out)], check=True)
        print(f"{int(a.dur*a.fps)} frames @ {a.w}x{a.h} -> {a.out}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
