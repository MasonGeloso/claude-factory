# note.com — long-form editor mechanics starter

Generic operating notes for note.com's editor — a different surface from X's post composer and
Articles editor (see `x-post.md` / `x-article.md`), with several rules **exactly
inverted** from X. Do not reuse X muscle memory here without checking the comparison table at the
bottom first.

Project-specific decisions (account, tone, which figures/prose to mirror from a source piece) belong
in this project's `factory/marketing/platforms.md`, not here.

---

## Entry and the two buttons that matter

Signed in → the "new post" action opens a fresh draft directly in the editor. No template picker.

| Button | What it does |
|---|---|
| **Save draft** | saves the draft. **This is the only one to click during drafting.** |
| **Publish / proceed to publish** | starts the publish flow. **Never click this** unless this content type's autonomy mode is explicitly `autonomous-publish` for note.com — publishing is otherwise the account owner's click. |

A left rail shows an auto-generated table of contents (every heading appears there — use it as free
verification that a heading actually landed). A character counter sits near the title. The icon above
the title is the cover image control.

---

## Text

Clipboard write + paste is the reliable input, same as X. Typing long or non-Latin text
character-by-character is slow and lossy.

**Paragraph separator is a double newline (`\n\n`) — the opposite of X's single-`\n` convention.**
This is the single easiest thing to get wrong when working both platforms in one session:
- `\n\n` → separate paragraph blocks, correct spacing.
- A single `\n` → a line break *inside* one block; paragraphs jam together with no gap and share one
  block marker.

---

## Use keyboard shortcuts, not the floating toolbar

Most editors of this kind expose an in-editor shortcuts guide — read it once at the start of a
session. Common shortcuts worth confirming: heading levels, link insertion, save draft, bold/quote.

### Do not drive the floating toolbar by coordinates

The floating toolbar re-anchors to the current selection, so its buttons move after **every**
conversion — and a dropdown-style control needs a second click at an offset that also moves. Half
the clicks land on nothing and fail silently, and a mis-click can scroll the document back to the
top, losing your place. Prefer a keyboard shortcut applied to a real selection over toolbar clicks
whenever one exists — it works reliably where the toolbar route needs several retries.

## Headings

**Select the header line, then apply the heading shortcut.** That's the whole procedure when a
shortcut exists.

Selection: a real triple-click on the line is reliable. Verify with the live selection's text
content before sending the shortcut.

### Enter with an active selection can split the block

After applying a heading via the floating toolbar, the selection can stay active — pressing End then
Return in that state can split the heading text into two separate heading blocks (and both then show
up as separate entries in the table of contents). Worse, a plain Backspace often does **not** merge
heading blocks back together — it only demotes the second block to body text, so recovery means
manually selecting the orphaned text, deleting the block, and re-pasting the missing characters onto
the heading.

**Rule:** after any floating-toolbar formatting, click once at the end of the text to collapse the
selection before pressing Enter — or use the keyboard-shortcut route and sidestep this entirely.

### Free verification

Every heading should appear in the table-of-contents rail, in order, none split in half. Dump the
document's actual heading elements and compare against what you intended, rather than trusting the
rail visually.

---

## Scrolling — the page may not respond to JS

`window.scrollTo()` and `element.scrollIntoView()` can be no-ops in an editor like this (they return
without moving anything, and the scroll position doesn't change). If that's the case here:

- Scroll with a real mouse-wheel action instead, then re-measure element positions afterward.
- Screenshot coordinates are not the same as CSS pixels — measure the ratio once
  (screenshot height ÷ window inner height) and convert, or just read the position directly off the
  image.
- Positions shift after every conversion or image insert — **re-measure before every click**, don't
  trust a coordinate computed even one step earlier.
- The floating toolbar can overlap whatever sits just above the current selection; if the next
  target lands under it, scroll a few ticks first.

---

## Images

### Check whether this editor triggers a native OS file picker

Unlike X (which just renders a file input on the page), an editor like this can genuinely open an
**OS-level file dialog** on an image-insert click — which a browser-automation tool cannot see or
dismiss, and which blocks the whole session if left open.

If that's the behavior here, swallow the native picker for the duration of the insert by patching
the file input's own click handler, then restore it immediately afterward:

```js
// 1. before triggering the image-insert control
window.__picker = {clicks: 0};
window.__origClick = HTMLInputElement.prototype.click;
HTMLInputElement.prototype.click = function () {
  if (this.type === 'file') { window.__picker.clicks++; return; }  // swallow
  return window.__origClick.apply(this, arguments);
};

// 2. trigger the image-insert control, then tag the input that appears
const e = document.querySelector('input[type=file]');
e.setAttribute('aria-label', 'IMAGE INPUT');

// 3. find the tagged input, then upload to it directly

// 4. ALWAYS restore, even on failure
HTMLInputElement.prototype.click = window.__origClick;
```

**Restoring matters** — leaving the prototype patched silently breaks every later file picker on the
page, including ones a human clicks by hand afterward.

If there's only ever one file input on the page (context-aware, not split cover-vs-body like X),
there's no risk of an inline figure clobbering the cover image the way there can be elsewhere.

### Cover image — pre-pad to the exact recommended aspect ratio BEFORE uploading

If the editor's crop dialog zooms in on any image whose aspect ratio doesn't match its recommended
size (commonly something like 1280×670, a ~1.91:1 hero shape) and the zoom slider's minimum is still
too far in, a source image with a different aspect can come out with its edges sliced off, with no
"fit" control to fix it after the fact.

**Fix it upstream**: pad the source image onto an exact-aspect canvas using the image's own
background color before uploading, so the crop box lands on the full image and saving is lossless:

```bash
convert source.png -format "%[pixel:p{2,2}]" info:      # sample the background color
convert source.png -resize <target_width - margin>x \
        -background 'rgb(r,g,b)' -gravity center -extent <target_width>x<target_height> cover.png
```

Replacing a bad cover afterward: hover it for a remove control (may need two clicks as the layout
reflows), then upload again.

### Captions

If the editor renders an inline caption field directly under the image (click and paste, no modal),
note that it may render centered rather than left-aligned like a different platform's modal-based
caption field — same text, different visual treatment, expected rather than a mistake.

### ⚠️ If images go in via clipboard paste, read the clipboard back before every image paste

You're pasting whatever is on the *system* clipboard — if a human is using the same machine
concurrently, or a previous copy silently failed, the wrong image (or someone else's) pastes with no
error and ships. This has actually put a stranger's image into a published draft before. Verify by
dimension and checksum before trusting the paste landed:
```bash
xclip -selection clipboard -t image/png -i "$SOURCE_PNG"
xclip -selection clipboard -o -t image/png > /tmp/_clipcheck.png   # diff size + md5 vs $SOURCE_PNG
```
Then confirm the inserted image's actual `naturalWidth`/`naturalHeight` in the DOM match the source
file — that's the only proof the editor took the one you verified, not just that something pasted.

---

## Links

Selecting an exact phrase mid-paragraph is the fiddly part in most rich-text editors — a triple-click
grabs the whole line, and non-Latin scripts often have no word boundaries to double-click select. A
reliable recipe:

1. Place a **collapsed** caret with a DOM Range at the start of the target phrase (a collapsed
   programmatic selection is generally honored by contenteditable editors; a non-collapsed one is
   often silently discarded).
2. Send one real "extend selection" keypress per character (e.g. shift+Right) to extend the
   selection through the phrase — real key events go through the editor's own selection handling, so
   the selection sticks, unlike a purely programmatic range. Verify the live selection's text
   afterward.
3. Trigger the link-insert control, type the URL into the popup, confirm.

### A link popup anchored to the selection needs the selection on-screen first

If the target text is off-screen, an anchored popup can be off-screen too, and unfillable. Scroll the
phrase into view before opening the link control. Scrolling can dismiss an already-open popup while
leaving the selection intact — in that case, just reopen the link control after scrolling. It may
also need a second attempt to appear at all; screenshot to confirm before typing into it.

Work on links in reverse document order (last one first), or re-locate each phrase after every
insert — wrapping text in a link element splits the surrounding text nodes and invalidates earlier
character offsets.

### Auto-linking bare domains

Many editors of this kind auto-link a bare domain written in prose. Decide per-project whether that's
acceptable (harmless for a non-competitor reference) or needs stripping (an actual competitor domain)
— this is a content decision, document it in that content type's file under `factory/marketing/content-types/`, not a mechanics
one.

---

## Additional traps (found operating a real long document, not in the basics above)

- **Screenshots can be permission-denied on the editor's own domain.** If so, a scroll action still
  returns a usable image — use a 1-tick scroll as a screenshot substitute when a plain screenshot is
  refused.
- **A JS `.focus()` call does not reliably make a ProseMirror-style editor accept key events.**
  Programmatic paste/shortcut dispatch can silently no-op. Place the caret with a **real click inside
  the body** instead.
- **Click targets near the very top of the viewport can fail** if a floating toolbar overlaps that
  region — scroll the target further down before clicking.
- **A synthetic paste event can fill the body fastest on an empty draft**, but it typically
  **appends rather than replaces**, even with the whole body notionally selected via a DOM Range:
  ```js
  const dt = new DataTransfer(); dt.setData('text/plain', text);
  body.dispatchEvent(new ClipboardEvent('paste', {clipboardData: dt, bubbles: true, cancelable: true}));
  ```
  Use it exactly once, on a genuinely empty draft — never as a way to replace existing content.
- **A "select all" shortcut can crash a large document in this kind of editor** (the editor's root
  node can go null and the page serve its own error state). **There is no safe select-all** in that
  case — never try to clear-and-refill an existing large draft this way.
- **This kind of editor often does not parse markdown on paste.** A `## ` heading prefix can get
  stripped as plain text while the block itself stays an ordinary paragraph — verify the actual
  block type, don't trust the visible character prefix.
- **Keys can stop reaching the editor after each image insert**, even after a real click that
  verifiably placed the caret in the right place. A fresh tab on the same draft URL typically
  restores key handling. Plan on **one editor session per image insert**, or better: create all the
  empty text blocks first in one session, then insert every image afterward in a separate pass
  (image insertion via file upload needs no keyboard input).
- **A stale, abandoned editor tab can poison the whole browser.** An editor tab with unsaved changes
  often holds a `beforeunload` dialog that a programmatic tab-close cannot dismiss. Two such tabs can
  be enough to stop key events reaching *any* tab and to make batched browser actions time out.
  **Never leave an editor tab open** at the end of a session — and if one is already stuck, its
  dialog must be dismissed by hand before automation will work reliably again. Work in exactly one
  tab at a time.
- **A corrupted draft is often unrecoverable in place.** Undo may not cover a synthetic paste, and a
  dirty-state "leave site?" dialog can block navigation away even after saving. If a draft gets into
  a bad state, **abandon it and start a new one** rather than trying to repair it — and note a fresh
  tab may lack whatever page-specific permissions the current one has, so free the current tab first.

**Consequence for sequencing: get this editor right on the first pass, in one session where possible.**
Set the title, click once into the body, paste once, then apply headings one at a time (scroll into
view → real click → select the line → apply the heading shortcut → verify the resulting tag).
Avoid re-pasting into an already-filled draft.

---

## Comparison with X (the inverted bits — check every one before reusing X habits)

| | note.com-style editor | X |
|---|---|---|
| Paragraph separator | double newline | single newline (double = extra gap) |
| Heading control | keyboard shortcut (toolbar unreliable) | toolbar block-type dropdown |
| Link control | shortcut + anchored popup | toolbar icon |
| JS scrolling | can be a no-op — real wheel only | generally works |
| Cover aspect | often must be pre-padded to an exact ratio or it crops | usually more tolerant |
| Block type after Enter | new block reverts to body | can stay in the same style — reset explicitly |
| Enter with an active selection | can split the block | collapses normally |
| Image insert | can fire a native OS picker — must be swallowed | usually just renders an input, no OS dialog |
| File inputs | often exactly one, context-aware | can be two — cover vs. body, distinguish by `accept` |
| Caption | often an inline field, centered | often a modal with its own Save, left-aligned |
| Save vs. publish | separate explicit "save draft" action | autosaves — just don't click Publish |
| Heading verification | table-of-contents rail | dump the block list directly |

## Finish

Save the draft, confirm the save succeeded, and hand back: the draft URL, the resulting
table-of-contents/heading list, figure count, and any auto-linked domains worth flagging. Never click
the publish control unless this content type's autonomy mode explicitly grants standing publish
authority for this platform.

---

## Observed on note.com specifically (2026-09-04, ProseMirror editor)

These are measured on note.com's own editor and take precedence over the hedged
"this kind of editor" wording above where they conflict.

**note.com DOES parse Markdown on paste, and parses it well.** One paste of a full article produced
`H2` headings (feeding the 目次 rail), `OL` lists, `HR` rules, and blockquotes as `FIGURE` nodes —
no manual heading pass needed at all. This is the opposite of X Articles, where everything arrives
as body text. Two consequences:

- **A `#` line INSIDE a fenced code block still becomes a real heading.** An example file whose
  first line is `# 7532 …` shows up in the 目次 as if it were a section of the article. Demote it:
  scroll it into view, real-select the line, floating toolbar → 見出し → **指定なし**. Verify by
  reading the 目次 rail, which should list exactly the article's own sections and nothing else.
- **Never hard-wrap paragraphs in the source Markdown.** Every wrap becomes a literal `<br>` inside
  the paragraph, so a sentence breaks mid-clause in the rendered article. One ~4,300-character
  article carried **33** of them. (The same source on X becomes 44 stray mid-sentence *spaces*
  instead.) Keep every paragraph, list item and blockquote line on one physical line in the `.md`.

**The cover-image file input exists — it just mounts late.** The earlier belief that note's cover
required a human click was a false negative from querying too early. What works:

1. Click the cover control → 「画像をアップロード」 in the menu.
2. **Wait ~2–3 seconds**, then query `input[type=file]` (a same-tick query returns nothing).
3. The input is `display:none`, so `find` cannot see it. Make it addressable, then upload by ref:
   ```js
   const i = document.querySelector('input[type=file]');
   i.setAttribute('aria-label','COVERUPLOADINPUT');
   i.style.cssText = 'position:fixed;top:200px;left:400px;width:300px;height:40px;opacity:1;z-index:99999;display:block';
   ```
   then `find` "COVERUPLOADINPUT" → `file_upload` with that ref.
4. The 「画像のサイズの変更」 crop modal opens; a pre-padded 1280×670 source needs no adjustment —
   click 保存.

**Captions are plain ProseMirror nodes, not a modal** (unlike X). Put a collapsed caret at
`setStart(figcaption, 0)` and type — the text lands directly.

**`scrollIntoView()` on an editor node does not reliably move note's viewport.** Use
`window.scrollTo(0, node.getBoundingClientRect().top + window.scrollY - 300)`. This matters because
the floating format toolbar only appears once the selected block is actually on screen — a JS-set
range alone does not summon it.

**The same select → wait → key discipline as X applies here.** A JS-set `Range` followed by a
keystroke in the same batch acts at the old caret. Use `[js-select, wait 1s, key] × N` and have each
JS step verify the character count moved by exactly the amount the previous step predicted.
