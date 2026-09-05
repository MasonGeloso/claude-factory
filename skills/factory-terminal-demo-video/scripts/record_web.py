# -*- coding: utf-8 -*-
"""Stage 4 — record the OS page to a raw .webm.

The page holds a solid marker frame until playback starts and shows one again when it
ends, so the exact animation span can be located afterwards and time-rescaled. This is
required, not defensive: Playwright's capture does not run at real time, and the error is
not consistent in direction (measured 47.08s for a 51.5s animation, and 59.04s for 55.3s).
"""
import json, os, shutil, subprocess, time
from playwright.sync_api import sync_playwright
from _config import load, rel

cfg = load()
W, H = cfg["width"], cfg["height"]
OUT = rel(cfg, "webvid"); shutil.rmtree(OUT, ignore_errors=True); os.makedirs(OUT)
cast = rel(cfg, cfg.get("cast_final", "final.cast"))
dur = json.loads(open(cast).read().splitlines()[-1])[0]
page_url = f"http://127.0.0.1:{cfg['port']}/{cfg.get('page','chrome/macos.html')}"
print(f"cast plays {dur:.1f}s -> {page_url}", flush=True)

with sync_playwright() as p:
    b = p.chromium.launch(args=["--force-device-scale-factor=1", "--hide-scrollbars",
                                "--autoplay-policy=no-user-gesture-required"])
    ctx = b.new_context(viewport={"width": W, "height": H}, device_scale_factor=1,
                        record_video_dir=OUT, record_video_size={"width": W, "height": H})
    pg = ctx.new_page()
    errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(page_url)
    pg.wait_for_selector("#term .ap-term", timeout=30000)
    pg.wait_for_timeout(2500)                    # fonts settled + recorder warm
    pg.evaluate("window.startDemo()")
    t0 = time.time()
    while time.time() - t0 < dur + 25:
        if pg.evaluate("window.__DONE__===true"):
            break
        time.sleep(0.3)
    print(f"playback {time.time()-t0:.1f}s done={pg.evaluate('window.__DONE__')} errs={errs[:2]}")
    pg.wait_for_timeout(1400)                    # hold the end marker in frame
    pg.close(); ctx.close(); b.close()

raw = max((os.path.join(OUT, f) for f in os.listdir(OUT) if f.endswith(".webm")),
          key=os.path.getmtime)
probe = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "default=nw=1:nk=1", raw], capture_output=True, text=True)
print("raw:", raw, probe.stdout.strip())
open(rel(cfg, "webraw.txt"), "w").write(raw + "\n")
