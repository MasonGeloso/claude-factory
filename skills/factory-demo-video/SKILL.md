---
name: factory-demo-video
description: 'Factory-suite copy of the demo-video skill. Create polished demo videos of web applications using playwright-cli with HTML overlay cards, code diffs, chapters, and banners. Records .webm video of a real browser session with composited overlays. Invoked by the factory-implement driver for `video` demo mode; also usable standalone. Use when user says "factory demo video", "make a demo video", "record a demo", "create a screencast", "demo recording", "video walkthrough", or wants to showcase a feature, bug fix, or product workflow as a video.'
---

# Demo Video Creator

Create polished demo videos using `playwright-cli` with HTML overlay cards, code diffs, chapters, and banners. Records `.webm` video of a real browser session with overlays composited on top in real time.

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

### Step 4: Record

Use `/playwright-cli` commands in sequence:

```bash
# 1. Open browser to target URL
playwright-cli open http://localhost:3000

# 2. Start recording
playwright-cli video-start demos/my-demo.webm

# 3. Run the demo script
playwright-cli run-code --filename=demos/my-demo.js

# 4. Stop recording
playwright-cli video-stop

# 5. Close browser
playwright-cli close
```

### Step 5: Convert (Optional)

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
- [ ] Output directory exists for `.webm` file
- [ ] App state is clean (seed data loaded, no stale errors)
