"""Terminal-style demo recorder. Plays back captured CLI output in an
animated HTML "terminal" page and records it as a .webm via Playwright.

Setup:
    1. Capture each scene's real stdout to a text file (see CAPTURES_DIR).
    2. Edit the SCENES list below.
    3. Optionally tweak the :root CSS variables in HTML_TEMPLATE for branding.
    4. Run:  python <this-file>

Requires:
    pip install playwright && playwright install chromium
"""

import asyncio
import json
import shutil
from pathlib import Path

from playwright.async_api import async_playwright

# ─── Paths — adjust per project ───────────────────────────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent
CAPTURES_DIR = Path("/tmp/demo-captures")              # where you saved CLI stdout
OUTPUT_WEBM = SCRIPT_DIR / "demo.webm"                 # final video output


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8").rstrip()


# ─── Scenes — edit me ─────────────────────────────────────────────────────
# Two shapes:
#   Splash:  {title, subtitle, duration_ms}
#   Command: {command, narration, output, type_delay_ms, hold_ms}
SCENES = [
    {
        "title": "My Feature",
        "subtitle": "One-line pitch describing what this demo shows",
        "duration_ms": 3500,
    },
    {
        "command": "my-cli stats",
        "narration": "Inspect the new collection",
        "output": _read(CAPTURES_DIR / "01-stats.txt"),
        "type_delay_ms": 35,
        "hold_ms": 2800,
    },
    {
        "command": 'my-cli query "example"',
        "narration": "Run a real query",
        "output": _read(CAPTURES_DIR / "02-query.txt"),
        "type_delay_ms": 25,
        "hold_ms": 4500,
    },
    {
        "title": "Closing line",
        "subtitle": "Optional pithy summary",
        "duration_ms": 3000,
    },
]


# ─── Branding — edit :root CSS vars + .titlebar text to match the project ─
HTML_TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<title>Terminal Demo</title>
<style>
  :root {
    --bg: #0B0D0E;
    --panel: #0A0C0D;
    --border: rgba(237, 231, 218, 0.10);
    --ink: #EDE7DA;
    --muted: rgba(237, 231, 218, 0.55);
    --gold: #D8B36A;
    --sage: #A8C9A0;
    --rose: #C99090;
    --prompt: #A8C9A0;
  }
  * { box-sizing: border-box; }
  html, body {
    margin: 0; padding: 0; height: 100%; width: 100%;
    background: var(--bg);
    color: var(--ink);
    font-family: "JetBrains Mono", "SF Mono", "Fira Code", ui-monospace, Menlo, monospace;
    overflow: hidden;
  }
  body { display: flex; align-items: center; justify-content: center; }
  .frame {
    width: 1280px; height: 720px;
    background: var(--panel);
    border: 1px solid var(--border);
    position: relative;
    display: flex; flex-direction: column;
  }
  .titlebar {
    height: 36px;
    border-bottom: 1px solid var(--border);
    display: flex; align-items: center; padding: 0 14px;
    color: var(--muted); font-size: 12px; letter-spacing: 0.08em;
    text-transform: uppercase;
  }
  .titlebar .dots { display: flex; gap: 6px; margin-right: 14px; }
  .titlebar .dot { width: 10px; height: 10px; border-radius: 50%; background: rgba(237,231,218,0.15); }
  .titlebar .label { flex: 1; }
  .titlebar .meta { color: var(--gold); font-size: 11px; }
  .terminal {
    flex: 1; overflow: hidden;
    padding: 18px 22px;
    font-size: 13px; line-height: 1.45;
    white-space: pre;
  }
  .line { display: block; }
  .prompt { color: var(--prompt); }
  .cmd { color: var(--ink); }
  .narration { color: var(--muted); font-style: italic; }
  .cursor {
    display: inline-block; width: 8px; height: 14px;
    background: var(--gold); vertical-align: -3px;
    animation: blink 1s steps(2) infinite;
  }
  @keyframes blink { 50% { opacity: 0; } }

  .splash {
    position: absolute; inset: 0;
    background: var(--bg);
    display: flex; flex-direction: column; align-items: center; justify-content: center;
    z-index: 10;
    opacity: 0; transition: opacity 360ms ease;
  }
  .splash.visible { opacity: 1; }
  .splash .title {
    font-family: "Fraunces", "Times New Roman", serif;
    font-size: 56px; letter-spacing: -0.02em;
    color: var(--ink);
    margin-bottom: 18px;
  }
  .splash .subtitle {
    color: var(--muted); font-size: 16px; max-width: 800px; text-align: center;
    line-height: 1.6;
  }
  .splash .accent { color: var(--gold); }

  .chapter {
    position: absolute; top: 50px; right: 22px;
    color: var(--gold); font-size: 10px; letter-spacing: 0.22em;
    text-transform: uppercase;
    border: 1px solid rgba(216,179,106,0.35);
    padding: 4px 10px;
    background: rgba(216,179,106,0.06);
    opacity: 0; transition: opacity 300ms ease;
  }
  .chapter.visible { opacity: 1; }
</style>
</head>
<body>
  <div class="frame">
    <div class="titlebar">
      <div class="dots"><div class="dot"></div><div class="dot"></div><div class="dot"></div></div>
      <div class="label">~/project — terminal demo</div>
      <div class="meta">DEMO</div>
    </div>
    <div class="chapter" id="chapter"></div>
    <div class="terminal" id="terminal"></div>
    <div class="splash" id="splash">
      <div class="title" id="splash-title"></div>
      <div class="subtitle" id="splash-subtitle"></div>
    </div>
  </div>
<script>
  const SCENES = __SCENES_JSON__;
  const term = document.getElementById('terminal');
  const splash = document.getElementById('splash');
  const splashTitle = document.getElementById('splash-title');
  const splashSubtitle = document.getElementById('splash-subtitle');
  const chapter = document.getElementById('chapter');

  const sleep = (ms) => new Promise(r => setTimeout(r, ms));

  function appendLine(html = '') {
    const div = document.createElement('div');
    div.className = 'line';
    div.innerHTML = html;
    term.appendChild(div);
    return div;
  }

  function escapeHtml(s) {
    return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }

  async function showSplash(title, subtitle, ms) {
    // Highlight a brand word in gold if it appears in the title — edit me.
    splashTitle.innerHTML = title;
    splashSubtitle.innerHTML = subtitle;
    splash.classList.add('visible');
    await sleep(ms);
    splash.classList.remove('visible');
    await sleep(420);
  }

  async function showChapter(text, ms) {
    chapter.textContent = text;
    chapter.classList.add('visible');
    await sleep(ms);
    chapter.classList.remove('visible');
  }

  async function typeCommand(cmd, narration, typeDelay) {
    if (narration) {
      appendLine('<span class="narration"># ' + escapeHtml(narration) + '</span>');
      await sleep(700);
    }
    const line = appendLine('<span class="prompt">$ </span><span class="cmd"></span><span class="cursor"></span>');
    const cmdSpan = line.querySelector('.cmd');
    const cursor = line.querySelector('.cursor');
    for (let i = 0; i < cmd.length; i++) {
      cmdSpan.textContent += cmd[i];
      await sleep(typeDelay);
    }
    cursor.remove();
    await sleep(260);
  }

  async function showOutput(output, holdMs) {
    const lines = output.split('\n');
    for (const l of lines) {
      appendLine(colorize(l));
      await sleep(8);
    }
    appendLine('');
    await sleep(holdMs);
  }

  // Output highlighting — adapt regex to your CLI's output shape.
  function colorize(line) {
    const safe = escapeHtml(line);
    if (/^RANK\s+/.test(line) || /^[A-Z][A-Z0-9 _-]{2,}$/.test(line.trim())) {
      return '<span style="color: var(--gold)">' + safe + '</span>';
    }
    if (/^-{5,}/.test(line) || /^={5,}/.test(line)) {
      return '<span style="color: var(--border)">' + safe + '</span>';
    }
    if (/TOTAL|SUMMARY/i.test(line)) {
      return '<span style="color: var(--gold)">' + safe + '</span>';
    }
    if (/^\s*(query|input|prompt):/i.test(line)) {
      return '<span style="color: var(--muted)">' + safe + '</span>';
    }
    return safe;
  }

  async function clearTerm() { term.innerHTML = ''; }

  async function run() {
    let cmdIdx = 0;
    for (const scene of SCENES) {
      if (scene.title && scene.subtitle && !scene.command) {
        await showSplash(scene.title, scene.subtitle, scene.duration_ms);
        await clearTerm();
        continue;
      }
      cmdIdx += 1;
      showChapter('Scene ' + String(cmdIdx).padStart(2, '0'), 2200);
      await typeCommand(scene.command, scene.narration, scene.type_delay_ms);
      await showOutput(scene.output, scene.hold_ms);
      // Clear every 2 scenes so the terminal doesn't run off the bottom.
      // Set to `cmdIdx >= 1` for every scene, or remove for none.
      if (cmdIdx % 2 === 0) {
        await sleep(400);
        await clearTerm();
      }
    }
    window.__DEMO_DONE__ = true;
  }

  run();
</script>
</body>
</html>
"""


async def record() -> None:
    OUTPUT_WEBM.parent.mkdir(parents=True, exist_ok=True)

    html = HTML_TEMPLATE.replace("__SCENES_JSON__", json.dumps(SCENES))
    html_path = OUTPUT_WEBM.parent / f"_{OUTPUT_WEBM.stem}.html"
    html_path.write_text(html, encoding="utf-8")

    # Estimate total duration from scene timings so we don't time out.
    total_ms = 0
    for s in SCENES:
        if "duration_ms" in s:
            total_ms += s["duration_ms"] + 500
        else:
            type_ms = s.get("type_delay_ms", 35) * len(s.get("command", ""))
            line_ms = len(s["output"].splitlines()) * 8
            total_ms += 1100 + type_ms + 260 + line_ms + s.get("hold_ms", 3500) + 700
    total_ms += 1500
    print(f"Estimated demo duration: {total_ms/1000:.1f}s")

    record_dir = OUTPUT_WEBM.parent / "_rec"
    if record_dir.exists():
        shutil.rmtree(record_dir)
    record_dir.mkdir()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 720},
            record_video_dir=str(record_dir),
            record_video_size={"width": 1280, "height": 720},
        )
        page = await context.new_page()
        await page.goto(html_path.as_uri())
        try:
            await page.wait_for_function("window.__DEMO_DONE__ === true", timeout=total_ms + 30000)
        except Exception as e:
            print(f"wait_for_function errored ({e}); finalizing anyway.")
        await page.wait_for_timeout(800)
        await context.close()
        await browser.close()

    webms = list(record_dir.glob("*.webm"))
    if not webms:
        raise RuntimeError("No webm produced by Playwright.")
    src = webms[0]
    if OUTPUT_WEBM.exists():
        OUTPUT_WEBM.unlink()
    shutil.move(str(src), str(OUTPUT_WEBM))
    shutil.rmtree(record_dir, ignore_errors=True)
    html_path.unlink(missing_ok=True)
    size_kb = OUTPUT_WEBM.stat().st_size // 1024
    print(f"Wrote {OUTPUT_WEBM} ({size_kb} KB)")


if __name__ == "__main__":
    asyncio.run(record())
