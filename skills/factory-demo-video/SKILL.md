---
name: factory-demo-video
description: 'Factory-suite copy of the demo-video skill. Create polished demo videos of web applications using playwright-cli with HTML overlay cards, code diffs, chapters, and banners. Records .webm video of a real browser session with composited overlays, and also captures numbered PNG screenshots of every key moment (desktop + mobile) plus an artifacts.md manifest, so the work can be reviewed without watching a video. Invoked by the factory-implement driver for `video` demo mode; also usable standalone. Use when user says "factory demo video", "make a demo video", "record a demo", "create a screencast", "demo recording", "video walkthrough", or wants to showcase a feature, bug fix, or product workflow as a video.'
---

# Demo Video Creator

Create polished demo videos using `playwright-cli` with HTML overlay cards, code diffs, chapters, and banners. Records `.webm` video of a real browser session with overlays composited on top in real time.

**Every demo produces two things: the video AND a set of still screenshots.** The video is for someone who wants the story; the screenshots are for someone who has 20 seconds and just wants to see that the thing works. Both are required — a demo run that produces only a `.webm` is incomplete.

**IMPORTANT:** This skill uses `/playwright-cli` for all browser automation. Do NOT use `/playwright-skill`.

## When to Use This Skill

- User wants to record a demo video of a web application or feature
- User wants to create a screencast walkthrough of a bug fix, new feature, or product
- User says "demo video", "record a demo", "screencast", "video walkthrough"
- User wants to showcase code changes with before/after overlays

## Prerequisites

- A running web application or target URL
- `playwright-cli` available (invoke via `/playwright-cli`)
- Output directory for `.webm` files (created automatically)

## Output contract — what a finished demo leaves on disk

Everything for one demo goes in **one directory per feature**, under the project's demo output dir
(`factory/deployment.md` → *Demo output dir*, usually `demos/`):

```
demos/<feature>/
  <feature>-demo.webm     the video
  01-<slug>.png           key moment 1   (numbered in the order they appear in the demo)
  02-<slug>.png           key moment 2
  03-<slug>-mobile.png    the same feature at 390px width
  artifacts.md            one line per file above, with a caption
```

Rules:

- **At least three screenshots**, and one per meaningful state the demo shows (empty, populated, error,
  the after-state of the fix). Shoot the **live UI**, never an overlay card — a screenshot of your own
  title slide tells the reader nothing.
- **Mobile is not optional** if the feature has a UI a person can reach on a phone: at least one shot at
  390×844.
- **Slug names describe what is on screen** (`02-filtered-results.png`), not what step it was
  (`02-step-two.png`).
- `artifacts.md` is what `factory-explain` and the handoff comment read to list the files. Write it.

## Reference

See `references/playwright-demo-videos.md` for the complete API reference, color palette, font stack, timing guidelines, advanced layouts, CSS animations, and troubleshooting.

## Workflow

### Step 1: Gather Requirements

Ask the user:
1. What URL/app to demo (e.g., `http://localhost:3000`)
2. What story to tell (bug fix, new feature, refactor, before/after)
3. Key scenes or interactions to capture
4. Any code changes to highlight (file paths, before/after snippets)

### Step 2: Choose a Narrative Arc

Pick the structure that fits the demo type:

| Type | Arc |
|------|-----|
| Bug Fix | Title → Problem (red) → Root Cause (blue) → Live UI: reproduce → Fix (green) → Code Diffs → Live UI: fixed → Summary |
| New Feature | Title → Motivation → Live UI: walkthrough → Architecture (blue) → Code Highlights → Live UI: edge cases → Summary |
| Refactor | Title → Problem (red) → Strategy (green) → Dashboard UI → Code Diffs (grouped) → Coverage Summary → Dashboard: healthy → Closing |
| Before/After | Title → Live UI: before → Banner("Before") → Changes (code cards) → Live UI: after → Banner("After") → Summary |

### Step 3: Write the Demo Script

Create a `.js` file with the demo script. The script MUST be a bare `async page => { ... }` arrow function.

**Required structure:**

```js
async page => {
    await page.setViewportSize({ width: 1280, height: 720 });

    // ─── Helper functions ───
    // Define showCard, showCodeCard, showBanner, etc.

    // ═══ Scenes ═══
    // Title → Context → Live UI → Code → Summary
}
```

**Include these helper functions** (copy from `references/playwright-demo-videos.md`):

- `showCard(title, body, bgColor, durationMs)` — full-screen overlay card
- `showCodeCard(filepath, before, after, durationMs)` — side-by-side code diff
- `showBanner(text, durationMs)` — floating pill annotation over live UI
- `showBadge(text, color)` — persistent corner badge (caller disposes)
- `shot(slug)` — **required.** Dispose any overlay, let the UI settle, then call
  `page.screenshot()` into the demo dir with a running counter, so the stills number themselves in
  demo order.

**Screenshot helper — copy this in:**

```js
    let shotN = 0;
    const SHOT_DIR = 'demos/<feature>';
    const shot = async (slug) => {
        shotN += 1;
        await page.waitForTimeout(400);   // let animations settle
        const nn = String(shotN).padStart(2, '0');
        await page.screenshot({ path: `${SHOT_DIR}/${nn}-${slug}.png` });
    };
```

Call `shot('...')` at every live-UI beat of the script — right after the state you just demonstrated
is on screen and **after** the overlay covering it has been disposed. At the end of the script, switch
to mobile and shoot it too:

```js
    await page.setViewportSize({ width: 390, height: 844 });
    await page.waitForTimeout(800);
    await shot('mobile');
    await page.setViewportSize({ width: 1280, height: 720 });
```

### Step 4: Record

Use `/playwright-cli` commands in sequence:

```bash
# 0. Make the per-feature demo dir (the script writes screenshots into it)
mkdir -p demos/<feature>

# 1. Open browser to target URL
playwright-cli open http://localhost:3000

# 2. Start recording
playwright-cli video-start demos/<feature>/<feature>-demo.webm

# 3. Run the demo script — this also writes the screenshots
playwright-cli run-code --filename=demos/<feature>/<feature>-demo.js

# 4. Stop recording
playwright-cli video-stop

# 5. Close browser
playwright-cli close

# 6. Verify BOTH outputs exist before you call the demo done
ls -1 demos/<feature>/
```

`page.screenshot()` paths are resolved relative to the process cwd, so run these from the repo root
(or make `SHOT_DIR` an absolute path in the script). If `ls` shows a `.webm` and no `.png` files, the
demo is not finished — the `shot()` calls did not run, and you need to fix the script and re-record.

### Step 5: Write `artifacts.md`

The reviewer will not go spelunking through a folder of PNGs. Write
`demos/<feature>/artifacts.md` listing every file you produced with a caption saying **what is on
screen and why it matters** — not the scene number:

```markdown
# <Feature> — demo artifacts

- `<feature>-demo.webm` — full walkthrough, 1m10s
- `01-empty-state.png` — the report page with no data; this used to render blank
- `02-filtered.png` — filtered to the last 7 days, 12 rows
- `03-error.png` — what the user sees when the upstream API times out
- `04-mobile.png` — the same page at 390px
```

`factory-explain` and the handoff comment read this file to list artifacts for the reviewer. Captions
here are the difference between "here are five screenshots" and "here is proof it works".

### Step 6: Verify what you produced

Actually look at them. `Read` two or three of the PNGs and confirm the feature is visible and the
overlay isn't covering it, and check the `.webm` size is non-trivial. A blank or overlay-covered
screenshot is worse than none — it looks like evidence and isn't.

### Step 7: Convert (Optional)

```bash
# WebM → MP4
ffmpeg -i demos/my-demo.webm -c:v libx264 -crf 23 demos/my-demo.mp4

# WebM → GIF
ffmpeg -i demos/my-demo.webm -vf "fps=10,scale=800:-1" demos/my-demo.gif
```

## Script Format Rules

- Outer wrapper MUST be `async page => { ... }` — no parens, no `module.exports`, no named function
- Helper functions defined inside the arrow, closing over `page`
- All overlays use `position: fixed` + `z-index: 99999`
- Overlays do NOT auto-dispose — always call `.dispose()` (except `showChapter` which auto-disposes)
- `page.goto()` clears all overlays — re-create any persistent ones after navigation

## Core Overlay API

### `page.screencast.showOverlay(htmlString)`
Injects HTML into page DOM. Returns handle with `.dispose()`. Must manually dispose.

### `page.screencast.showChapter(title, { description, duration })`
Built-in chapter card. Auto-disposes after `duration` ms.

## Color Palette

| Purpose | Background Color |
|---------|-----------------|
| Title/neutral | `rgba(0,0,0,0.95)` |
| Problem/error | `rgba(139,20,0,0.90)` |
| Solution/success | `rgba(0,60,30,0.90)` |
| Warning | `rgba(120,80,0,0.90)` |
| Explanation | `rgba(20,20,60,0.93)` |
| Code background | `rgba(8,8,24,0.96)` |

## Timing Guidelines

| Card Type | Duration |
|-----------|----------|
| Title card | 3000-3500ms |
| Problem/solution card | 4000-5000ms |
| Context card | 3000-4000ms |
| Code diff card | 4000-5500ms |
| Dense code diff | 5500-7000ms |
| Chapter divider | 1500-2000ms |
| Banner over UI | 2500-3000ms |
| Wait after goto | 2000-2500ms |
| Wait after click | 1000-1500ms |

Rule of thumb: ~200-250ms per word in body text. Code: ~300ms per line.

## Gotchas

- Escape `<` and `>` in code overlays as `&lt;` and `&gt;`
- Escape backticks in template literals
- `page.goto()` destroys all overlays — re-create after navigation
- Script format must be bare `async page => { }` — no parens around param
- Use `z-index: 2147483647` if app has high z-index modals/portals

## Checklist Before Recording

- [ ] Dev server / app is running and accessible
- [ ] Browser opened with `playwright-cli open <url>`
- [ ] Viewport set: `page.setViewportSize({ width: 1280, height: 720 })`
- [ ] URLs in script point to correct host/port
- [ ] No real credentials or secrets in overlays or on page
- [ ] HTML entities escaped in code examples
- [ ] Output directory `demos/<feature>/` exists for the `.webm` **and the screenshots**
- [ ] App state is clean (seed data loaded, no stale errors)
- [ ] `shot()` helper defined and called at every live-UI beat, including one mobile shot
- [ ] After recording: `.webm` **and** ≥3 `.png` files on disk, and you have looked at them
- [ ] `artifacts.md` written, one captioned line per file
