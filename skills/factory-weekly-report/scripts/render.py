#!/usr/bin/env python3
"""Render a weekly-report data file to a PNG (and a standalone HTML).

  python3 render.py data.json -o report.png          # png + report.html beside it
  python3 render.py data.json -o report.png --open   # …and open it in the browser
  python3 render.py --sample -o sample.png           # render the bundled sample

The page is assembled by inlining every asset into one HTML string rather than
loading them over file:// — Chromium treats file:// as an opaque origin, so an
external SVG sprite (`<use href="icons.svg#…">`) silently renders nothing there.
Inlining also means the emitted .html is a genuine single-file artifact: it opens
anywhere, with no sibling files and no network.
"""
import argparse
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ASSETS = HERE.parent / "assets"


def build_html(data: dict) -> str:
    html = (ASSETS / "template.html").read_text()
    fonts = (ASSETS / "fonts.css").read_text()
    theme = (ASSETS / "theme.css").read_text()
    sprite = (ASSETS / "icons.svg").read_text()

    html = html.replace(
        '<!--@fonts--><link rel="stylesheet" href="fonts.css">',
        f"<style>\n{fonts}\n</style>",
    )
    html = html.replace(
        '<!--@theme--><link rel="stylesheet" href="theme.css">',
        f"<style>\n{theme}\n</style>",
    )
    html = html.replace("<!--@sprite-->", sprite)
    # json.dumps escapes nothing HTML-significant except `/` in `</script>`, which
    # would close the tag early if a title ever contained one.
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    html = re.sub(
        r"window\.REPORT_DATA = window\.REPORT_DATA \|\| null; //@data",
        f"window.REPORT_DATA = {payload};",
        html,
    )
    return html


def render(data: dict, out: Path, scale: int = 2) -> Path:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        sys.exit("playwright not installed — pip install playwright && playwright install chromium")

    html = build_html(data)
    html_out = out.with_suffix(".html")
    html_out.write_text(html)

    with sync_playwright() as p:
        browser = p.chromium.launch()
        # deviceScaleFactor=2 — these reports are read zoomed-in on the small
        # mono labels; a 1x screenshot turns 9px tracking-heavy text to mush.
        page = browser.new_page(viewport={"width": 1600, "height": 1200}, device_scale_factor=scale)
        crashes: list[str] = []
        page.on("pageerror", lambda e: crashes.append(str(e)))
        page.set_content(html, wait_until="load")
        # Either outcome resolves the wait, so bad data fails in a second with a
        # real message instead of timing out with none.
        page.wait_for_selector("body[data-ready='1'], body[data-error]", timeout=15000)
        err = page.get_attribute("body", "data-error")
        if err or crashes:
            browser.close()
            sys.exit("render failed:\n" + (err or "\n".join(crashes)))
        page.wait_for_function("document.fonts.ready.then(() => true)")
        report = page.locator("#report")
        # Screenshot the element, not the viewport: the report sizes itself to the
        # tree's content width, which varies with the number of tiers.
        report.screenshot(path=str(out))
        browser.close()

    return html_out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("data", nargs="?", help="path to the report JSON")
    ap.add_argument("-o", "--out", default="weekly-report.png", help="output PNG path")
    ap.add_argument("--sample", action="store_true", help="render assets/sample.json")
    ap.add_argument("--scale", type=int, default=2, help="device scale factor (default 2)")
    ap.add_argument("--open", action="store_true", help="open the HTML in the default browser")
    a = ap.parse_args()

    if a.sample:
        src = ASSETS / "sample.json"
    elif a.data:
        src = Path(a.data)
    else:
        ap.error("pass a data file or --sample")

    if not src.exists():
        sys.exit(f"no such data file: {src}")

    data = json.loads(src.read_text())
    out = Path(a.out).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    html_out = render(data, out, scale=a.scale)
    print(f"{out}\n{html_out}")

    if a.open:
        import subprocess
        subprocess.run(["xdg-open", str(html_out)], check=False)


if __name__ == "__main__":
    main()
