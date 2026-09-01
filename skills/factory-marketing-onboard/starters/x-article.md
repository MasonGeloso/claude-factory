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
4. Click the target style, then verify structurally (query the DOM for the expected tag, e.g. `h1`).

**One heading per tool call.** Batching several in one call tends to fail after the first — the
previous menu's open/close state can swallow the next click. Verify each one and retry misses.

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

**Captions**: clicking a caption line can only *open* a modal on the first click — a second click
*into* the opened textarea is required before pasting; save explicitly afterward.

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
correctly by assumption.

## Never

**Never click Publish/公開.** Publishing this kind of long-form article is the account owner's call,
unless the calling context has explicit standing authorization to publish autonomously (state that
clearly in the platform's own onboarded config if so — the default is draft-only).
