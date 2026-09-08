# X (Twitter) — the long-form Articles editor

A **different surface** from the post composer (`x-post.md`) — nothing there transfers here, and
nothing here transfers there. Requires the account to have Articles enabled (typically a paid tier).
Drive it **only** through the owner's logged-in Chrome (`claude-in-chrome`), never `playwright-cli`.
**Verify the account** in the profile switcher before starting, same as any other platform action.

Entry: the "Articles" nav item (its label follows the account's UI locale — e.g. 記事 on a
Japanese-locale account) → the compose URL → "Create article". A draft is created
immediately and autosaves continuously — there is no separate save button, and a full page reload
restores the draft intact (blocks, headings, images, cover), so reloading is a safe recovery if the
editor gets stuck.

## Coordinates: the trap that costs the most time

The rendered page is scaled from the actual viewport, **and the viewport's effective height changes
as the toolbar re-renders** — so a coordinate computed in one call is often stale by the next call.

- **`getBoundingClientRect()` on menu items can return wrong values** in an editor like this one —
  menus can sit inside a transformed container, so measured coordinates and visual coordinates
  diverge. **Read menu positions off a screenshot, not off JS**, when this happens.
- **A screenshot and the click that uses its coordinates must be adjacent tool calls.** Anything that
  can re-render the layout between them (including a `scrollIntoView`) invalidates the coordinates.

## Text

- Title: click it, then paste (clipboard write + paste, not synthesized keystrokes).
- Body paragraph breaks: **verify empirically which newline convention this editor wants** — some
  editors want a single `\n` between paragraphs and treat `\n\n` as an empty block (producing
  unwanted gaps); confirm before pasting a long body.
- **Read the clipboard back before every paste.** A paste can silently serve stale clipboard content
  written several calls earlier (e.g. a caption paste that actually inserts the title text).

## Headings — verify the working recipe empirically, then reuse it

Rich-text editors built on a contenteditable/Draft.js-style model often only honor a **programmatic
collapsed caret**, not a raw click, when applying a block-level style (heading, etc.). A recipe that
tends to work:

1. Set a collapsed caret at the start of the target block via JS, then focus it.
2. Open the block-type control (usually a toolbar label near the paragraph-style button).
3. Screenshot before clicking the target style — **a plain wait is not enough**, the toolbar can be
   mid-render.
4. Click the target style, then verify structurally — **by the block's CSS class, not by tag name.**
   X Articles renders every block as a `div[data-block="true"]` and carries the style in a class:
   `longform-unstyled` (body), `longform-header-one` (見出し), `longform-header-two` (小見出し).
   There is no `h1`/`h2` in the DOM at all, so a tag check reports failure on a click that worked.
   Pick ONE of the two heading levels for a whole article and hold to it — 見出し (header-one) is the
   section heading; 小見出し is a sub-level, and mixing them because two blocks were styled on
   different days is a real defect a reader sees.

**One heading per tool call.** Batching several in one call tends to fail after the first — the
previous menu's open/close state can swallow the next click. Verify each one and retry misses.

**Element refs for MENU ITEMS go stale; refs for toolbar buttons survive.** A `find`-issued ref for
an item inside a dropdown is dead the moment that dropdown closes, so a loop that re-uses it fails on
iteration 2 with "element may have been removed". Either re-`find` per heading (3 calls each), or —
much cheaper — dispatch a synthetic pointer sequence on the element:

```js
const fire = el => { const r = el.getBoundingClientRect();
  ['pointerdown','mousedown','pointerup','mouseup','click'].forEach(k =>
    el.dispatchEvent(new MouseEvent(k, {bubbles:true, cancelable:true, view:window,
      clientX:r.left+r.width/2, clientY:r.top+r.height/2, button:0}))); };
fire(toolbarBtn);                                  // opens the dropdown
// then POLL for [role="menuitem"] — it can take >1s to mount
fire([...document.querySelectorAll('[role="menuitem"]')].find(e => e.textContent.trim()==='見出し'));
```

This works on the **Articles** editor. It is NOT safe on the X **post composer**, where a JS click
destroys the draft — that ban is composer-scoped, don't generalise it to Articles.

**Do not click these by screenshot coordinate.** Coordinates read off a screenshot are scaled, and
the browser window can resize mid-session (observed: 674px → 604px viewport height between two
calls), so a coordinate that worked five calls ago silently misses now. Click by `ref` or by the
synthetic dispatch above. `getBoundingClientRect()` on a portalled menu item also disagrees with the
screenshot frame — don't convert one to the other.

**Order matters: paste first, THEN apply the heading style — never the reverse.** Opening the
block-type dropdown before pasting can blur the editor, and a paste queued against a blurred editor
silently vanishes. Paste the text, select it (e.g. a collapsed-caret-to-line-end selection), then
open the dropdown and apply the style.

**Pressing Enter after a heading block does NOT reset the next block back to body text** — the new
line inherits the heading style unless you explicitly switch it back. Check the block type after
every heading, not just its content.

**Clicking empty space below the last block does not focus the editor.** Click on real text first
(e.g. `ctrl+End` after clicking into existing content) rather than clicking blank space and assuming
focus landed.

## Cover image and body figures — two async traps that make working code look broken

**Trap 1 — the insert-toolbar re-renders after every image upload.** For several seconds the insert
button can be a shimmer placeholder that silently no-ops on click. **Poll until the button has
existed stably for several consecutive checks before clicking it**, and only *then* place the caret
— setting the caret before a long poll finishes can let the poll steal the selection back.

**Trap 2 — the file input for body media renders lazily.** Querying for it in the *same* batched
call as the click that should reveal it will often return nothing and look like failure. **Query for
it in a separate tool call**, or poll for it.

If more than one file input exists on the page (e.g. one for the cover, one for body media), tell
them apart by a distinguishing attribute (commonly `accept`, since a video-capable input differs
from an image-only one) rather than by position/index, which can shift.

**Captions**: click the 「キャプションを入力（オプション）」 placeholder under the image → a
「キャプションを編集」 modal opens → click *into* the textarea (a second click, the first only opened
the modal) → type → click 保存. Nothing is written until 保存.

**Where a body image lands**: it is inserted *after* the block holding the caret/selection. So put
the caret on the placeholder paragraph that marks the spot, insert, then delete the placeholder.

**Clipboard paste does not insert images into X Articles.** `xclip -t image/png` + `ctrl+v` with a
valid selection in the editor is a silent no-op here (verified: 0 image nodes after, no error). The
挿入 → メディア modal and its lazily-rendered file input is the only route that works. The paragraph
below applies to editors where clipboard paste IS the insert path (note.com), not to this one.

**⚠️ If images go in via clipboard paste (`ctrl+v`) rather than a file input, read the clipboard back
before every image paste.** You're pasting whatever is on the *system* clipboard — if a human is
using the same machine/clipboard concurrently, or a previous image copy silently failed, the wrong
image (or someone else's) pastes with no error. Verify by dimension and checksum before trusting the
paste landed correctly:
```bash
xclip -selection clipboard -t image/png -i "$SOURCE_PNG"
xclip -selection clipboard -o -t image/png > /tmp/_clipcheck.png   # then diff size + md5 vs $SOURCE_PNG
```
After the paste, also confirm the inserted image's actual `naturalWidth`/`naturalHeight` in the DOM
match the source file — that's the only proof the editor actually took the image you verified, not
just that something got pasted.

## Links

Bare URLs are usually auto-linked by this kind of editor — prefer writing a URL as plain text over
manually wiring an inline link, it's far less error-prone.

**⚠️ This editor can also auto-link anything domain-shaped in plain prose, not just bare URLs** — a
competitor or third-party product named as a domain (e.g. writing out `example.com` in running text)
can silently become a live outbound hyperlink to that domain. This has shipped real outbound links to
competitors before. Before handover, count outbound links that don't point at your own domain:
```js
[...ed.querySelectorAll('a')].filter(a => !a.href.includes('<your-own-domain>')).length
```
Report the count and confirm with the project's own content-type guidance whether to strip them (a
harmless reference — e.g. a benchmark mention — is usually fine to leave; a real competitor mention
usually isn't).

## Verify structurally before considering the draft done

Query the editor's root contenteditable element and walk its children, checking for the expected
mix of heading/image/paragraph blocks in the expected order, rather than trusting that clicks landed
correctly by assumption:
```js
const ed=document.querySelector('[contenteditable="true"][role="textbox"]');
[...ed.children[0].children].map(b => (b.querySelector('h1')?'H: ':b.querySelector('img')?'IMG: ':'p: ')
  + b.innerText.replace(/\s+/g,' ').slice(0,34));
```

## Never

**Never click Publish/公開.** Publishing this kind of long-form article is the account owner's call,
unless the calling context has explicit standing authorization to publish autonomously (state that
clearly in the platform's own onboarded config if so — the default is draft-only).

## Editing text that is already in the editor (the one that corrupts drafts silently)

Setting a DOM `Range` from JS and pressing a key in the **same** `browser_batch` does not work: the
editor has not yet adopted the selection when the keystroke arrives, so the key applies at the *old*
caret. This does not error — it quietly eats the wrong characters. One real run turned
`example.app（https://example.app）でアカウントを作る` into
`example.app（https://example.aでアカウントを作る` in six keypresses before anyone noticed.

The loop that is safe:

1. JS: find the next target, set the range, return the current total character count **and the count
   you expect after the edit**.
2. `wait` 1 second (a real round trip; this is the part that makes it work).
3. Press the key.
4. Next JS call re-reads the character count **first** and aborts (blurring the editor, so a queued
   keystroke becomes a no-op) if it doesn't match what step 1 predicted.

Batched as `[js, wait, key] × N` this runs ~13 edits per tool call and every edit is verified. If a
step ever reports a mismatch, `ctrl+z` repeatedly until the character count returns to its
pre-batch value, then re-derive — undo is reliable here.

**Deleting a whole block** (a placeholder paragraph, a literal `---` left over from Markdown): select
from the **end of the previous block's last text node** to the **end of the target block**, then one
BackSpace. That removes the block break plus its content in a single, verifiable edit.

- Do NOT select only the text and press BackSpace twice — the second press acts on whatever is
  adjacent, and next to an atomic node (an image) that can select or delete the image.
- If the previous sibling IS an atomic node, merge *forwards* instead (select from the start of the
  target block to the start of the next block) — but only when that next block is a plain paragraph;
  merging a heading upward turns the heading into body text.
- A helper that resolves `'end'` must use the block's **last** `[data-text="true"]` node, not its
  first. Blocks containing a link have several text nodes, and taking the first one's length silently
  produces a selection that spans most of the paragraph.

**Regex scans over block text miss matches that straddle text nodes.** A link splits a paragraph into
several text nodes, so a pattern like `JP-space-JP` will not match when the space sits at the
boundary. Walk the text nodes as a list and additionally test the first/last character of each
against its neighbour's, or the scan will report "done" with hits still on the page.

## What this editor cannot do

`挿入 → コード` did not apply to either a range selection or a collapsed caret (two attempts, no DOM
change, no error). Fenced code blocks from a Markdown source therefore land as ordinary paragraphs.
Plan for it: the commands and prompts still read fine as plain paragraphs, but any content that
depends on monospace alignment (an ASCII pointer line under a URL, a hand-aligned table) must be
rewritten as prose or shipped as an image.
