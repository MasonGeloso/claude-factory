# Playwright Demo Video System

Create polished demo videos using `playwright-cli` with HTML overlay cards, code diffs, chapters, and banners. Records `.webm` video of a real browser session with overlays composited on top in real time.

---

## Table of Contents

- [Quick Start](#quick-start)
- [Script Format](#script-format)
- [Core Overlay API](#core-overlay-api)
- [Reusable Helper Functions](#reusable-helper-functions)
- [Color Palette](#color-palette)
- [Font Stack](#font-stack)
- [Demo Structure Template](#demo-structure-template)
- [Narrative Arc Patterns](#narrative-arc-patterns)
- [Timing Guidelines](#timing-guidelines)
- [Interacting with the Live Page](#interacting-with-the-live-page)
- [Running the Demo](#running-the-demo)
- [Advanced: Persistent Overlays](#advanced-persistent-overlays)
- [Advanced: Custom Overlay Layouts](#advanced-custom-overlay-layouts)
- [Advanced: CSS Animations](#advanced-css-animations)
- [Gotchas and Pitfalls](#gotchas-and-pitfalls)
- [Troubleshooting](#troubleshooting)
- [Checklist Before Recording](#checklist-before-recording)

---

## Quick Start

```bash
# 1. Open browser (any URL — your app, a static page, even about:blank)
playwright-cli open http://localhost:3000

# 2. Start recording
playwright-cli video-start demos/my-demo.webm

# 3. Run script
playwright-cli run-code --filename=demos/my-demo.js

# 4. Stop recording
playwright-cli video-stop

# 5. Close browser
playwright-cli close
```

That's it. You get a `.webm` file with everything — page navigation, clicks, overlays, chapters — baked into the video.

---

## Script Format

Scripts are **async arrow functions** that receive `page` (a Playwright Page object). The function body is the entire demo sequence.

```js
async page => {
    await page.setViewportSize({ width: 1280, height: 720 });

    // your demo logic here
}
```

**Important:** The outer wrapper must be `async page => { ... }` — not `async (page) => { ... }`, not `module.exports`, not `function`. Just a bare async arrow. The CLI wraps it in `(yourFunction)(page)` internally.

### Available APIs on `page`

**Navigation and interaction (standard Playwright):**
- `page.goto(url)` — navigate to a URL
- `page.waitForTimeout(ms)` — pause for a duration
- `page.waitForLoadState('networkidle')` — wait until network settles
- `page.click(selector)` — click an element
- `page.fill(selector, text)` — fill a form input
- `page.locator(selector)` — get a Playwright locator for complex interactions
- `page.evaluate(fn)` — execute arbitrary JS in the browser context
- `page.setViewportSize({ width, height })` — set viewport dimensions
- `page.getByRole(role, { name })` — accessible element lookup
- `page.getByText(text)` — find element by visible text

**Screencast overlay system (the demo magic):**
- `page.screencast.showOverlay(htmlString)` — inject HTML overlay, returns disposable handle
- `page.screencast.showChapter(title, { description, duration })` — built-in section divider card

---

## Core Overlay API

### `page.screencast.showOverlay(htmlString)`

Injects arbitrary HTML into the page DOM as an overlay layer. Returns a handle object with a `.dispose()` method to remove it.

```js
const overlay = await page.screencast.showOverlay(`
    <div style="position:fixed; ...">Content here</div>
`);
await page.waitForTimeout(3000);  // show for 3 seconds
await overlay.dispose();          // remove it
```

**How it works under the hood:**
- The HTML string is injected into the page's DOM (not a separate layer)
- It's rendered by Chromium like any other HTML — full CSS support
- The video encoder captures whatever is on screen, overlays included
- Because it's real DOM, you get: flexbox, grid, gradients, backdrop-filter, transforms, @keyframes animations, SVG, canvas — anything the browser supports
- `position: fixed` + `z-index: 99999` ensures it sits above the app's UI

**The overlay does NOT auto-dispose.** You must call `.dispose()` or it stays on screen forever (or until the page navigates, which clears DOM). The pattern is always: show → wait → dispose.

### `page.screencast.showChapter(title, options)`

Built-in chapter card. This is a pre-styled section divider that auto-disposes after the specified duration. You cannot customize its appearance — it uses the system's built-in card style.

```js
await page.screencast.showChapter('Section Title', {
    description: 'What this section covers',
    duration: 2000,   // milliseconds — auto-disposes after this
});
```

Use chapters to separate logical sections of the demo. Use custom `showOverlay` for everything else where you need control over styling.

---

## Reusable Helper Functions

Define these at the top of your script. They close over `page` from the outer scope.

### Full-Screen Card (titles, explanations, summaries)

Covers the entire viewport with a centered title + body. The workhorse of any demo — use for title cards, problem statements, explanations, summaries, anything text-heavy.

```js
async function showCard(title, body, bgColor, durationMs) {
    const overlay = await page.screencast.showOverlay(`
        <div style="
            position: fixed;
            inset: 0;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            background: ${bgColor || 'rgba(0,0,0,0.92)'};
            font-family: 'SF Mono', 'Fira Code', monospace;
            color: white;
            padding: 60px;
            text-align: center;
            z-index: 99999;
        ">
            <div style="
                font-size: 36px;
                font-weight: 700;
                margin-bottom: 24px;
                letter-spacing: -0.5px;
            ">${title}</div>
            <div style="
                font-size: 18px;
                line-height: 1.7;
                opacity: 0.85;
                white-space: pre-line;
                max-width: 900px;
            ">${body}</div>
        </div>
    `);
    await page.waitForTimeout(durationMs);
    await overlay.dispose();
}
```

**Usage:**

```js
// Title card — black bg, large centered text
await showCard('My Feature Demo', 'Subtitle text here', 'rgba(0,0,0,0.95)', 3500);

// Problem statement — dark red bg signals danger/issue
await showCard('The Problem', 'Users see a 500 error\nwhen submitting forms with special chars.', 'rgba(139,20,0,0.90)', 5000);

// Solution — dark green bg signals resolution
await showCard('The Fix', 'Input sanitization at the API boundary.\nAll 3 affected endpoints patched.', 'rgba(0,60,30,0.90)', 5000);

// Neutral explanation — dark blue bg for technical detail
await showCard('How It Works', 'Technical implementation details...', 'rgba(20,20,60,0.93)', 4000);
```

**Why this works visually:**
- `position: fixed; inset: 0;` — covers full viewport regardless of scroll position
- `display: flex; justify-content: center; align-items: center;` — perfect centering
- `white-space: pre-line` — `\n` in your body string becomes actual line breaks
- `max-width: 900px` — prevents text from stretching edge-to-edge on wide viewports
- `opacity: 0.85` on body — slightly muted body text creates visual hierarchy vs title
- `letter-spacing: -0.5px` on title — tightens large text for a polished look
- `padding: 60px` — generous breathing room prevents cramped feel

### Side-by-Side Code Diff Card

Shows a filepath header with two panels: red (before) and green (after). Mimics a GitHub diff view.

```js
async function showCodeCard(filepath, before, after, durationMs) {
    const overlay = await page.screencast.showOverlay(`
        <div style="
            position: fixed;
            inset: 0;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            background: rgba(8, 8, 24, 0.96);
            font-family: 'SF Mono', 'Fira Code', monospace;
            color: white;
            padding: 40px;
            z-index: 99999;
        ">
            <div style="
                font-size: 16px;
                color: #8b949e;
                margin-bottom: 20px;
                letter-spacing: 1px;
            ">${filepath}</div>
            <div style="display: flex; gap: 32px; max-width: 1100px; width: 100%;">
                <!-- BEFORE panel (red) -->
                <div style="
                    flex: 1;
                    background: rgba(139, 0, 0, 0.15);
                    border: 1px solid rgba(248, 81, 73, 0.3);
                    border-radius: 8px;
                    padding: 20px;
                    text-align: left;
                ">
                    <div style="
                        font-size: 12px;
                        color: #f85149;
                        margin-bottom: 12px;
                        font-weight: 600;
                    ">BEFORE</div>
                    <pre style="
                        font-size: 14px;
                        line-height: 1.6;
                        color: #ffa198;
                        margin: 0;
                        white-space: pre-wrap;
                    ">${before}</pre>
                </div>
                <!-- AFTER panel (green) -->
                <div style="
                    flex: 1;
                    background: rgba(0, 100, 0, 0.15);
                    border: 1px solid rgba(63, 185, 80, 0.3);
                    border-radius: 8px;
                    padding: 20px;
                    text-align: left;
                ">
                    <div style="
                        font-size: 12px;
                        color: #3fb950;
                        margin-bottom: 12px;
                        font-weight: 600;
                    ">AFTER</div>
                    <pre style="
                        font-size: 14px;
                        line-height: 1.6;
                        color: #7ee787;
                        margin: 0;
                        white-space: pre-wrap;
                    ">${after}</pre>
                </div>
            </div>
        </div>
    `);
    await page.waitForTimeout(durationMs);
    await overlay.dispose();
}
```

**Usage:**

```js
// Simple one-line change
await showCodeCard(
    'src/api/handler.py :42',
    'result = fetch(url)',
    'result = fetch(url, timeout=30)',
    4500
);

// Multi-line with highlighted additions (gold spans)
await showCodeCard(
    'src/worker.py :80, :102',
    'job.wait_for_completion(\n    timeout=120\n)\n\nresult = api.generate(\n    prompt=prompt\n)',
    'job.wait_for_completion(\n    timeout=120,\n    <span style="color:#ffd700;">caller_job=parent</span>\n)\n\n<span style="color:#ffd700;">with keep_alive(job):</span>\n    result = api.generate(\n        prompt=prompt\n    )',
    5000
);
```

**Why this works visually:**
- `background: rgba(8, 8, 24, 0.96)` — near-black with a hint of blue, like a code editor
- `display: flex; gap: 32px;` — side-by-side panels with breathing room
- Red panel uses three shades: `rgba(139,0,0,0.15)` background, `rgba(248,81,73,0.3)` border, `#ffa198` text
- Green panel uses three shades: `rgba(0,100,0,0.15)` background, `rgba(63,185,80,0.3)` border, `#7ee787` text
- These exact colors come from GitHub's dark mode diff — viewers instinctively read red=removed, green=added
- `<span style="color:#ffd700;">` inside before/after highlights the specific changed tokens in gold
- `<pre>` with `white-space: pre-wrap` preserves code indentation and wraps long lines
- `flex: 1` on both panels — equal width regardless of content length
- `max-width: 1100px` on the container — prevents panels from stretching too wide

### Bottom Banner (contextual callout over live UI)

A floating pill at the bottom center of the viewport. Shows a one-liner annotation while the real page is visible behind it. Use to narrate what the viewer should notice on the live page.

```js
async function showBanner(text, durationMs) {
    const overlay = await page.screencast.showOverlay(`
        <div style="
            position: fixed;
            bottom: 24px;
            left: 50%;
            transform: translateX(-50%);
            padding: 14px 32px;
            background: rgba(0, 0, 0, 0.85);
            border: 1px solid rgba(255, 255, 255, 0.15);
            border-radius: 12px;
            font-family: 'SF Mono', 'Fira Code', monospace;
            font-size: 16px;
            color: white;
            z-index: 99999;
            backdrop-filter: blur(8px);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
        ">${text}</div>
    `);
    await page.waitForTimeout(durationMs);
    await overlay.dispose();
}
```

**Usage:**

```js
// Navigate to page, let it render, then annotate
await page.goto('http://localhost:3000/dashboard');
await page.waitForTimeout(2000);
await showBanner('All tests passing — zero regressions', 3000);

// After performing an action
await page.click('#submit-btn');
await page.waitForTimeout(1500);
await showBanner('Form submitted successfully — check the network tab', 2500);
```

**Why this works visually:**
- `left: 50%; transform: translateX(-50%)` — perfectly centered horizontally
- `bottom: 24px` — floats above the bottom edge, clears most app navigation bars
- `backdrop-filter: blur(8px)` — frosted glass effect, page content is visible but blurred behind it
- `border: 1px solid rgba(255,255,255,0.15)` — subtle border makes it pop without being heavy
- `box-shadow: 0 8px 32px rgba(0,0,0,0.4)` — floating depth effect
- Does NOT cover the page — this is the key difference from `showCard`

### Top Banner (alternative position)

Same concept as bottom banner but pinned to the top. Useful when bottom content matters.

```js
async function showTopBanner(text, durationMs) {
    const overlay = await page.screencast.showOverlay(`
        <div style="
            position: fixed;
            top: 24px;
            left: 50%;
            transform: translateX(-50%);
            padding: 14px 32px;
            background: rgba(0, 0, 0, 0.85);
            border: 1px solid rgba(255, 255, 255, 0.15);
            border-radius: 12px;
            font-family: 'SF Mono', 'Fira Code', monospace;
            font-size: 16px;
            color: white;
            z-index: 99999;
            backdrop-filter: blur(8px);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
        ">${text}</div>
    `);
    await page.waitForTimeout(durationMs);
    await overlay.dispose();
}
```

### Corner Badge (persistent status indicator)

Small persistent label in a corner. Stays visible across multiple scenes until you `.dispose()` it.

```js
async function showBadge(text, color) {
    return await page.screencast.showOverlay(`
        <div style="
            position: fixed;
            top: 12px;
            right: 12px;
            padding: 8px 16px;
            background: ${color || 'rgba(34,197,94,0.9)'};
            border-radius: 8px;
            font-size: 14px;
            color: white;
            font-family: 'SF Mono', 'Fira Code', monospace;
            z-index: 99999;
        ">${text}</div>
    `);
    // Caller is responsible for .dispose() — this intentionally persists
}
```

**Usage:**

```js
const badge = await showBadge('Authenticated', 'rgba(34,197,94,0.9)');

// Navigate around with the badge visible
await page.goto('/dashboard');
await page.waitForTimeout(3000);
await page.goto('/settings');
await page.waitForTimeout(2000);

badge.dispose();  // Remove when done with this section
```

---

## Color Palette

All colors based on GitHub's dark theme for instant developer familiarity.

### Background Colors for `showCard`

| Purpose | Color | When to use |
|---------|-------|-------------|
| Title/neutral | `rgba(0,0,0,0.95)` | Opening card, closing card, neutral summaries |
| Problem/error | `rgba(139,20,0,0.90)` | Problem statements, bug descriptions, failure states |
| Solution/success | `rgba(0,60,30,0.90)` | Fix descriptions, success summaries, feature complete |
| Warning/caution | `rgba(120,80,0,0.90)` | Trade-offs, caveats, things to watch out for |
| Explanation | `rgba(20,20,60,0.93)` | Technical details, architecture explanations |
| Code background | `rgba(8,8,24,0.96)` | Code diff cards, terminal output |

### Text Colors

| Element | Color | Hex | Usage |
|---------|-------|-----|-------|
| Title text | white | `#ffffff` | Card titles, headings |
| Body text | white 85% | `opacity: 0.85` | Card body text (slightly muted) |
| Muted/secondary | GitHub secondary | `#8b949e` | Filepaths, labels, metadata |
| Red (before/deleted) | GitHub diff red | `#ffa198` | Code in BEFORE panels |
| Red label | GitHub danger | `#f85149` | "BEFORE" label, error text |
| Green (after/added) | GitHub diff green | `#7ee787` | Code in AFTER panels |
| Green label | GitHub success | `#3fb950` | "AFTER" label, success text |
| Blue (info) | GitHub blue | `#58a6ff` | Informational highlights, links |
| Gold (highlight) | Gold | `#ffd700` | Changed tokens in code diffs |
| Purple (accent) | GitHub purple | `#bc8cff` | Alternative accent color |
| Orange (warn) | GitHub orange | `#f0883e` | Warnings, deprecations |

### Inline Color Highlights in Body Text

Use `<span>` tags inside the body string for colored inline text. Since the body is raw HTML, anything goes:

```js
await showCard('Coverage Summary',
    '<span style="color:#3fb950;">Fix 1 (caller_job)</span>  →  40+ tasks covered\n' +
    '<span style="color:#58a6ff;">Fix 2 (keep_alive)</span>  →  6 tasks with API calls\n' +
    '<span style="color:#8b949e;">Already handled</span>     →  3 tasks\n' +
    '<span style="color:#f85149;">At risk</span>             →  0 tasks',
    'rgba(0,0,0,0.93)',
    5000
);
```

### Diff Panel Colors (for code cards)

| Panel | Background | Border | Text |
|-------|-----------|--------|------|
| BEFORE (red) | `rgba(139,0,0,0.15)` | `rgba(248,81,73,0.3)` | `#ffa198` |
| AFTER (green) | `rgba(0,100,0,0.15)` | `rgba(63,185,80,0.3)` | `#7ee787` |

These are subtle tinted backgrounds with matching borders — the same layering GitHub uses in dark mode diffs.

---

## Font Stack

### Primary (code/technical demos)

```css
font-family: 'SF Mono', 'Fira Code', monospace;
```

- **SF Mono** — macOS system monospace font, available on all Macs without install
- **Fira Code** — popular open-source dev font, common on Linux systems
- **monospace** — generic fallback (usually Courier New or Liberation Mono)

This gives everything a clean terminal/editor aesthetic. Used for all overlay types in the helpers above.

### Alternative (product/marketing demos)

```css
font-family: -apple-system, 'Segoe UI', 'Inter', sans-serif;
```

Use this for demos targeting non-developer audiences. Swap it into the `showCard` helper's font-family.

### Mixing fonts in a single overlay

```js
await page.screencast.showOverlay(`
    <div style="position:fixed;inset:0;display:flex;flex-direction:column;
        justify-content:center;align-items:center;background:rgba(0,0,0,0.95);
        z-index:99999;">
        <div style="font-family:-apple-system,sans-serif;font-size:42px;
            color:white;font-weight:700;">Product Feature Name</div>
        <pre style="font-family:'SF Mono',monospace;font-size:14px;
            color:#7ee787;margin-top:24px;">const result = newApi.call()</pre>
    </div>
`);
```

---

## Demo Structure Template

A complete starting point. Copy this, replace the content, define your helpers, and you have a demo.

```js
async page => {
    await page.setViewportSize({ width: 1280, height: 720 });

    const APP_URL = 'http://localhost:3000';

    // ─── Helper functions ───
    // (paste showCard, showCodeCard, showBanner from above)

    // ═══ Scene 1: Title ═══
    await showCard('Feature Name', 'One-line description of what was done', 'rgba(0,0,0,0.95)', 3500);

    // ═══ Scene 2: Context / Problem ═══
    await showCard('The Problem', 'What was broken or missing.\nWhy it matters.', 'rgba(139,20,0,0.90)', 5000);

    // ═══ Scene 3: Solution Overview ═══
    await showCard('The Approach', 'High-level description of the fix.\nKey decisions made.', 'rgba(0,60,30,0.90)', 5000);

    // ═══ Scene 4: Live UI Demo ═══
    await page.screencast.showChapter('Live Demo', {
        description: 'Showing the feature in action',
        duration: 2000,
    });
    await page.goto(`${APP_URL}/feature-page`);
    await page.waitForTimeout(2500);
    await showBanner('Notice the new behavior here', 3000);

    // Interact with the page
    await page.click('#some-button');
    await page.waitForTimeout(1500);
    await showBanner('Action completed successfully', 2500);

    // ═══ Scene 5: Code Changes ═══
    await page.screencast.showChapter('Code Changes', {
        description: 'What was modified',
        duration: 2000,
    });

    // Pattern: context card → code diff, repeated per change
    await showCard('Change 1: Auth Module', 'src/auth.py — Added timeout parameter', 'rgba(20,20,60,0.93)', 3500);
    await showCodeCard('src/auth.py :42', 'old_code()', 'new_code()', 4500);

    await showCard('Change 2: Worker', 'src/worker.py — Wrapped blocking call', 'rgba(20,20,60,0.93)', 3500);
    await showCodeCard('src/worker.py :88', 'blocking_call()', 'with keepalive():\n    blocking_call()', 4500);

    // ═══ Scene 6: Summary / Closing ═══
    await showCard('Done', 'Summary of all changes\nKey metrics or impact', 'rgba(0,0,0,0.95)', 4000);
}
```

---

## Narrative Arc Patterns

Different demo types call for different structures. Choose the one that fits.

### Bug Fix Demo

```
Title → Problem (red) → Root Cause (blue) → [Live UI: reproduce bug] →
Fix (green) → Code Diffs → [Live UI: bug gone] → Summary
```

### New Feature Demo

```
Title → Motivation (neutral) → [Live UI: walkthrough] →
Architecture (blue) → Code Highlights → [Live UI: edge cases] → Summary
```

### Refactor/Infrastructure Demo

```
Title → Problem (red) → Strategy (green) → [Dashboard/monitoring UI] →
Code Diffs (grouped by fix type) → Coverage Summary → [Dashboard: healthy] → Closing
```

### Before/After Demo

```
Title → [Live UI: before state] → Banner("Before") →
Changes (code cards) → [Live UI: after state] → Banner("After") → Summary
```

### General Pattern

Every demo benefits from this rhythm:
1. **Tell** them what you'll show (title + context cards)
2. **Show** them (live UI + banners)
3. **Explain** the code (context card + diff card, repeated)
4. **Summarize** (closing card with metrics/impact)

Alternate between full-screen overlays (cards) and live page (with banners). This creates visual rhythm — solid color → real UI → solid color → real UI. The viewer's brain gets explanation then evidence, explanation then evidence.

---

## Timing Guidelines

| Card Type | Duration | Rule of Thumb |
|-----------|----------|---------------|
| Title card | 3000-3500ms | Just title + subtitle, quick read |
| Problem/solution card | 4000-5000ms | 3-5 lines of body text |
| Context card (before code) | 3000-4000ms | Brief intro to what's coming |
| Code diff card | 4000-5500ms | Code reads slower — give extra time |
| Dense code diff (10+ lines) | 5500-7000ms | Complex diffs need more |
| Chapter divider | 1500-2000ms | Just a section label, fast |
| Banner over UI | 2500-3000ms | One-liner, quick read |
| `waitForTimeout` after `goto` | 2000-2500ms | Let the page render and settle |
| `waitForTimeout` after `click` | 1000-1500ms | Let the UI respond |
| Card with inline colored spans | +500-1000ms | Color draws the eye, takes longer to parse |

**General rule:** ~200-250ms per word in card body text. Code takes ~300ms per line. When in doubt, err slightly longer — viewers can rewatch, but a too-fast card is frustrating.

**Pacing tip:** After 3-4 full-screen cards in a row, cut to live UI or a chapter to break the visual monotony. The chapter card is a natural "breath" between dense sections.

---

## Interacting with the Live Page

The real power is mixing overlays with actual page interaction. The video captures everything.

### Basic navigation and clicks

```js
await page.goto('http://localhost:3000/settings');
await page.waitForTimeout(2000);  // Let the page render

// Click a button
await page.click('button:has-text("Save")');
await page.waitForTimeout(1000);

// Annotate what happened
await showBanner('Settings saved — changes take effect immediately', 2500);
```

### Filling forms

```js
await page.fill('#email-input', 'user@example.com');
await page.waitForTimeout(500);
await page.fill('#password-input', 'securepassword123');
await page.waitForTimeout(500);
await page.click('button[type="submit"]');
await page.waitForTimeout(1500);
```

### Using Playwright locators (more robust)

```js
const submitBtn = page.getByRole('button', { name: 'Submit' });
await submitBtn.click();

const heading = page.getByRole('heading', { name: 'Dashboard' });
await heading.waitFor();  // Wait for element to appear
```

### Executing JavaScript in the page

```js
// Read a value from the page
const count = await page.evaluate(() => {
    return document.querySelectorAll('.item').length;
});

// Use it in an overlay
await showBanner(`Found ${count} items in the list`, 2500);
```

### WebSocket interaction (for real-time apps)

```js
const result = await page.evaluate(async () => {
    return new Promise((resolve, reject) => {
        const ws = new WebSocket('ws://localhost:8080/ws');
        ws.onopen = () => {
            ws.send(JSON.stringify({ type: 'auth', token: 'test-key' }));
        };
        ws.onmessage = (event) => {
            const msg = JSON.parse(event.data);
            if (msg.type === 'auth_success') {
                resolve(msg);
            }
        };
        setTimeout(() => reject(new Error('Timeout')), 5000);
    });
});

await showBanner(`Authenticated as ${result.user_id}`, 2500);
```

### Scrolling

```js
// Scroll to bottom
await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
await page.waitForTimeout(1000);

// Scroll to specific element
await page.evaluate(() => {
    document.querySelector('#target-section').scrollIntoView({ behavior: 'smooth' });
});
await page.waitForTimeout(1500);
```

---

## Running the Demo

### Full workflow

```bash
# 1. Start your dev server / app (separate terminal)
npm run dev  # or docker compose up, etc.

# 2. Record the demo
playwright-cli open http://localhost:3000
playwright-cli video-start demos/feature-demo.webm
playwright-cli run-code --filename=demos/feature-demo.js
playwright-cli video-stop
playwright-cli close
```

### Viewing the output

```bash
# Open in browser
google-chrome demos/feature-demo.webm

# Or on macOS
open demos/feature-demo.webm
```

### Converting to other formats

```bash
# WebM to MP4 (widely compatible, good for sharing)
ffmpeg -i demos/feature-demo.webm -c:v libx264 -crf 23 demos/feature-demo.mp4

# WebM to GIF (for README/docs, large file warning)
ffmpeg -i demos/feature-demo.webm -vf "fps=10,scale=800:-1" demos/feature-demo.gif

# Extract a still frame (e.g. for thumbnail)
ffmpeg -i demos/feature-demo.webm -ss 00:00:03 -frames:v 1 demos/thumbnail.png
```

### Re-recording

Just run the same commands again. `video-start` overwrites the file if it already exists. No need to delete first.

---

## Advanced: Persistent Overlays

Overlays persist until `.dispose()` is called. Use this for badges, labels, or annotations that should stay visible across multiple actions.

```js
// Show a status badge while navigating around
const badge = await page.screencast.showOverlay(`
    <div style="position:fixed; top:12px; right:12px;
        padding:8px 16px; background:rgba(34,197,94,0.9);
        border-radius:8px; font-size:14px; color:white;
        font-family:monospace; z-index:99999;">
        Authenticated as test user
    </div>
`);

// Do stuff with the badge visible
await page.goto('/dashboard');
await page.waitForTimeout(3000);
await page.goto('/settings');
await page.waitForTimeout(2000);

// Remove when done
await badge.dispose();
```

### Multiple simultaneous overlays

```js
const topLabel = await page.screencast.showOverlay(`
    <div style="position:fixed;top:12px;left:12px;padding:6px 12px;
        background:rgba(88,166,255,0.9);border-radius:6px;
        font-size:12px;color:white;font-family:monospace;z-index:99999;">
        Environment: staging
    </div>
`);

const bottomLabel = await page.screencast.showOverlay(`
    <div style="position:fixed;bottom:12px;right:12px;padding:6px 12px;
        background:rgba(248,81,73,0.9);border-radius:6px;
        font-size:12px;color:white;font-family:monospace;z-index:99999;">
        Recording in progress
    </div>
`);

// ... do stuff ...

topLabel.dispose();
bottomLabel.dispose();
```

---

## Advanced: Custom Overlay Layouts

Since overlays are raw HTML, any layout the browser can render is possible.

### Three-column comparison

```js
const overlay = await page.screencast.showOverlay(`
    <div style="position:fixed;inset:0;display:flex;
        justify-content:center;align-items:center;
        background:rgba(0,0,0,0.95);padding:40px;z-index:99999;">
        <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:24px;
            max-width:1200px;width:100%;font-family:monospace;color:white;">
            <div style="background:rgba(255,0,0,0.1);border-radius:8px;padding:20px;">
                <h3 style="color:#f85149;margin:0 0 12px 0;">Option A</h3>
                <pre style="margin:0;color:#ffa198;">sync_call()\nblocks for 90s</pre>
            </div>
            <div style="background:rgba(0,100,255,0.1);border-radius:8px;padding:20px;">
                <h3 style="color:#58a6ff;margin:0 0 12px 0;">Option B</h3>
                <pre style="margin:0;color:#a5d6ff;">async_call()\ncallback based</pre>
            </div>
            <div style="background:rgba(0,255,0,0.1);border-radius:8px;padding:20px;">
                <h3 style="color:#3fb950;margin:0 0 12px 0;">Option C (chosen)</h3>
                <pre style="margin:0;color:#7ee787;">with keep_alive():\n    sync_call()</pre>
            </div>
        </div>
    </div>
`);
await page.waitForTimeout(6000);
await overlay.dispose();
```

### Big number stats / metrics card

```js
const overlay = await page.screencast.showOverlay(`
    <div style="position:fixed;inset:0;display:flex;
        justify-content:center;align-items:center;
        background:rgba(0,0,0,0.93);z-index:99999;">
        <div style="display:flex;gap:48px;font-family:monospace;color:white;">
            <div style="text-align:center;">
                <div style="font-size:64px;font-weight:700;color:#3fb950;">8</div>
                <div style="font-size:16px;opacity:0.7;">files modified</div>
            </div>
            <div style="text-align:center;">
                <div style="font-size:64px;font-weight:700;color:#58a6ff;">62</div>
                <div style="font-size:16px;opacity:0.7;">tasks covered</div>
            </div>
            <div style="text-align:center;">
                <div style="font-size:64px;font-weight:700;color:#f85149;">0</div>
                <div style="font-size:16px;opacity:0.7;">at risk</div>
            </div>
        </div>
    </div>
`);
await page.waitForTimeout(4000);
await overlay.dispose();
```

### Numbered step list

```js
const overlay = await page.screencast.showOverlay(`
    <div style="position:fixed;inset:0;display:flex;flex-direction:column;
        justify-content:center;align-items:center;
        background:rgba(0,0,0,0.93);z-index:99999;
        font-family:'SF Mono',monospace;color:white;">
        <div style="font-size:32px;font-weight:700;margin-bottom:32px;">How It Works</div>
        <div style="max-width:700px;width:100%;text-align:left;">
            <div style="display:flex;gap:16px;margin-bottom:20px;align-items:flex-start;">
                <div style="background:#3fb950;color:black;border-radius:50%;
                    width:32px;height:32px;display:flex;align-items:center;
                    justify-content:center;font-weight:700;flex-shrink:0;">1</div>
                <div style="font-size:18px;line-height:1.5;opacity:0.85;">
                    Task calls llm() which creates a child job</div>
            </div>
            <div style="display:flex;gap:16px;margin-bottom:20px;align-items:flex-start;">
                <div style="background:#58a6ff;color:black;border-radius:50%;
                    width:32px;height:32px;display:flex;align-items:center;
                    justify-content:center;font-weight:700;flex-shrink:0;">2</div>
                <div style="font-size:18px;line-height:1.5;opacity:0.85;">
                    wait_for_completion() polls the child job status</div>
            </div>
            <div style="display:flex;gap:16px;align-items:flex-start;">
                <div style="background:#ffd700;color:black;border-radius:50%;
                    width:32px;height:32px;display:flex;align-items:center;
                    justify-content:center;font-weight:700;flex-shrink:0;">3</div>
                <div style="font-size:18px;line-height:1.5;opacity:0.85;">
                    caller_job.heartbeat() fires every 30s during the poll loop</div>
            </div>
        </div>
    </div>
`);
await page.waitForTimeout(6000);
await overlay.dispose();
```

### Table / matrix layout

```js
const overlay = await page.screencast.showOverlay(`
    <div style="position:fixed;inset:0;display:flex;flex-direction:column;
        justify-content:center;align-items:center;
        background:rgba(0,0,0,0.93);z-index:99999;
        font-family:'SF Mono',monospace;color:white;">
        <div style="font-size:28px;font-weight:700;margin-bottom:24px;">Coverage Matrix</div>
        <table style="border-collapse:collapse;font-size:15px;">
            <tr style="border-bottom:1px solid rgba(255,255,255,0.2);">
                <th style="padding:10px 20px;text-align:left;color:#8b949e;">Task</th>
                <th style="padding:10px 20px;text-align:left;color:#8b949e;">Fix</th>
                <th style="padding:10px 20px;text-align:left;color:#8b949e;">Status</th>
            </tr>
            <tr>
                <td style="padding:10px 20px;">llm()</td>
                <td style="padding:10px 20px;color:#ffd700;">caller_job</td>
                <td style="padding:10px 20px;color:#3fb950;">covered</td>
            </tr>
            <tr>
                <td style="padding:10px 20px;">generate_image</td>
                <td style="padding:10px 20px;color:#ffd700;">keep_alive</td>
                <td style="padding:10px 20px;color:#3fb950;">covered</td>
            </tr>
            <tr>
                <td style="padding:10px 20px;">generate_video</td>
                <td style="padding:10px 20px;color:#ffd700;">both</td>
                <td style="padding:10px 20px;color:#3fb950;">covered</td>
            </tr>
        </table>
    </div>
`);
await page.waitForTimeout(5000);
await overlay.dispose();
```

---

## Advanced: CSS Animations

Since overlays are real DOM, CSS animations work. Use sparingly — they're effective for drawing attention but distracting if overused.

### Fade-in card

```js
const overlay = await page.screencast.showOverlay(`
    <style>
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
    </style>
    <div style="position:fixed;inset:0;display:flex;
        justify-content:center;align-items:center;
        background:rgba(0,0,0,0.93);z-index:99999;
        animation: fadeIn 0.5s ease-out;">
        <div style="font-family:monospace;color:white;font-size:36px;
            font-weight:700;">Animated Title</div>
    </div>
`);
await page.waitForTimeout(3500);
await overlay.dispose();
```

### Pulsing attention indicator

```js
const pulse = await page.screencast.showOverlay(`
    <style>
        @keyframes pulse {
            0%, 100% { box-shadow: 0 0 0 0 rgba(248,81,73,0.7); }
            50% { box-shadow: 0 0 0 12px rgba(248,81,73,0); }
        }
    </style>
    <div style="position:fixed;top:120px;left:240px;
        width:16px;height:16px;border-radius:50%;
        background:#f85149;z-index:99999;
        animation: pulse 1.5s infinite;">
    </div>
`);
// Use to draw attention to a specific area of the UI
await page.waitForTimeout(4000);
await pulse.dispose();
```

### Typewriter text effect

```js
const overlay = await page.screencast.showOverlay(`
    <style>
        @keyframes typing {
            from { width: 0; }
            to { width: 100%; }
        }
    </style>
    <div style="position:fixed;bottom:80px;left:50%;transform:translateX(-50%);
        z-index:99999;">
        <div style="font-family:monospace;font-size:18px;color:#3fb950;
            overflow:hidden;white-space:nowrap;border-right:2px solid #3fb950;
            animation: typing 2s steps(40) forwards;">
            $ deploy --production --no-downtime
        </div>
    </div>
`);
await page.waitForTimeout(3500);
await overlay.dispose();
```

---

## Gotchas and Pitfalls

### HTML escaping in template literals

Your overlay content is injected as raw HTML. Watch out for:

```js
// BAD — angle brackets in code will be parsed as HTML tags
await showCodeCard('file.py', 'if x < 10:', 'if x < 10 and y > 5:', 4000);

// GOOD — escape angle brackets
await showCodeCard('file.py', 'if x &lt; 10:', 'if x &lt; 10 and y &gt; 5:', 4000);
```

Backticks in content need escaping too since you're inside a template literal:

```js
// BAD — breaks the template literal
`code with \`backticks\``

// GOOD — escape them
`code with \`backticks\``
// Or use a variable
const code = "code with `backticks`";
```

### Overlay doesn't show

- Make sure you have `position: fixed` (not `absolute` — that's relative to the scroll position)
- Make sure `z-index: 99999` is high enough (some UI frameworks use 10000+)
- Check that your HTML is valid — unclosed tags can cause silent failures

### Page navigation clears overlays

When you `page.goto()`, all overlays are destroyed (they're DOM elements on the old page). If you need an overlay to persist across navigation, re-create it after the `goto`:

```js
await page.goto('/page2');
await page.waitForTimeout(1000);
// Re-create the badge on the new page
const badge = await showBadge('Still authenticated');
```

### Script format matters

The script MUST be `async page => { ... }` — a bare async arrow function. Common mistakes:

```js
// WRONG — module.exports
module.exports = async (page) => { ... }

// WRONG — named function
async function demo(page) { ... }

// WRONG — parens around param (sometimes works, sometimes doesn't)
async (page) => { ... }

// RIGHT
async page => { ... }
```

### Long-running scripts

If your script takes more than ~5 minutes, consider whether the video file will be too large. At 1280x720, `.webm` typically produces 0.5-1 MB per minute. A 5-minute demo is about 3-5 MB.

### Overlay z-index conflicts

If your app uses portals, modals, or toasts with high z-index values, your overlay might appear behind them. Bump to `z-index: 2147483647` (max 32-bit int) if needed:

```js
`<div style="position:fixed;inset:0;z-index:2147483647;">...`
```

---

## Troubleshooting

| Problem | Cause | Fix |
|---------|-------|-----|
| `SyntaxError: Unexpected token` | Wrong script format | Use `async page => { }` (bare arrow) |
| `showOverlay: html: expected string, got object` | Passing object instead of HTML string | Use template literal string, not `{ title, body }` object |
| Overlay appears behind app UI | z-index too low | Use `z-index: 99999` or higher |
| Overlay disappears on navigation | `page.goto()` clears DOM | Re-create overlay after navigation |
| Video is blank | Recording started before navigating | Call `page.goto()` after `video-start` |
| `TypeError: __fn__ is not a function` | Empty or malformed script | Check script is a valid async arrow function |
| Text overflows card | Body text too long for `max-width` | Use `word-break: break-word` or reduce text |
| Code diff panels uneven height | One side has more lines | `align-items: flex-start` on the flex container (default stretch equalizes) |

---

## Checklist Before Recording

- [ ] Dev server / app is running and accessible
- [ ] Browser opened with `playwright-cli open <url>`
- [ ] Viewport set in script: `page.setViewportSize({ width: 1280, height: 720 })`
- [ ] All URLs in script point to correct host/port
- [ ] No real credentials or secrets visible in overlays or on page
- [ ] Timing feels right (mentally walk through the script)
- [ ] HTML entities escaped in code examples (`<` → `&lt;`, `>` → `&gt;`)
- [ ] Output path exists (or will be created): `demos/my-demo.webm`
- [ ] App state is clean (seed data loaded, no stale errors on screen)
