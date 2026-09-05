# X (Twitter) — the post composer

Drive X **only** through the owner's logged-in Chrome (`claude-in-chrome`), **never** `playwright-cli`
or any other headless automation — that traffic gets accounts suspended or muted. If the Chrome
tools are unavailable, stop and report it; do not improvise a substitute.

**Verify the account before doing anything else.** Confirm the profile name/handle in the bottom-left
account switcher matches the account this platform section names. A post published to the wrong
account is a real mess to undo — check every time, not just on the first run of the day.

## Text

Clipboard + paste, not synthesized keystrokes — typing long or non-Latin text character-by-character
is slow and lossy.

```bash
printf '%s' "$TEXT" | xclip -selection clipboard
```

**Verify the clipboard actually changed before pasting.** A clipboard write can hand off
asynchronously and lose to whatever last owned the selection — read it back before you paste:

```bash
printf '%s' "$TEXT" | xclip -selection clipboard; sleep 1; xclip -selection clipboard -o
```

**A clipboard selection goes stale in roughly a minute.** Re-set it **immediately** before every
paste, including before a second field (e.g. an ALT-text field right after the body) — a clipboard
set even a couple of steps earlier can paste nothing, and the field silently stays empty with no
error. **The first click after navigating to a page often does not register.** Click the target
field, paste, and check the result; if it's empty, click and paste again — a second attempt is
normal, not a sign something is broken.

**Length**: X counts non-Latin/CJK characters as 2 each toward the limit — a post that looks short
in the editor can still be over 280. A Premium/verified account raises the free-tier limit
substantially, so check whether the account has it; either way, confirm the counter ring near the
Post button is not red before publishing.

## Hashtags

- **`&` terminates a hashtag** — `#M&A` parses as the hashtag `#M` followed by literal `&A`. Looks
  fine in a draft doc, wrong in the feed. Only `\w` characters survive in a tag.
- After pasting, **look at the composer**: every intended tag must render blue. A tag sitting in
  plain (non-blue) text did not register.
- An autocomplete popover can open over the toolbar after the last tag — dismiss it by clicking blank
  space **inside** the composer (see the double-post trap below for why "inside" matters).

## Bare links auto-build the post's preview card

If the post has no attached media, X builds a link-preview card from the **last URL in the text** —
and that card becomes the post's visual, branding included. A post that merely *names* several
competing tools/sites as plain text can end up illustrated by one of them. **Attaching an image
suppresses the card**, so for any post naming outside domains/brands, an image is not optional —
check the composer's preview before sending.

## Images

- **Verify every candidate image URL actually resolves** before using it — a broken or 404 source is
  a common miss.
- **Always look at the image before attaching it.** A license/rights check is not a composition
  check — read the actual picture.
- **Sourcing from Wikimedia Commons:** one call gets you filenames, URLs, and license metadata
  together — use `generator=categorymembers` rather than a plain `list` query plus a second
  `imageinfo` round-trip:
  ```bash
  curl -sS -A "<YourTool>/1.0 (<contact-email-or-url>)" \
    "https://commons.wikimedia.org/w/api.php?action=query&format=json&generator=categorymembers&gcmtitle=Category:<Name>&gcmtype=file&gcmlimit=25&prop=imageinfo&iiprop=url|size|extmetadata&iiurlwidth=1600"
  ```
  Wikimedia's API etiquette expects a real contact-identifying User-Agent, not a generic client
  string — put this project's own tool name/contact in it. Grab the returned `thumburl` at
  ~1600-1920px, not the multi-thousand-pixel original. **Prefer CC BY over CC BY-SA** when both are
  available for the same subject — CC BY-SA's share-alike clause can complicate reuse in a post's
  context in ways a plain attribution license doesn't; when only CC BY-SA exists, it's still usable,
  just note the license (not only the author) in the ALT-text attribution.
- **Attribution goes in the ALT text**, not the post body — there's no room in the body, and it also
  makes the post accessible. Hover the attached image → **Add description**, paste, **Save**.
  Confirm the small **ALT** badge appears on the thumbnail afterward.
  ⚠️ **A coordinate click on the "Add description" link tends to land as a hover only** — the composer
  reflows as the image finishes rendering, so coordinates read a moment earlier are stale by the time
  the click lands. Call it directly instead and confirm the navigation actually happened:
  ```js
  document.querySelector('a[href*="compose/post/media"]').click();
  await new Promise(r=>setTimeout(r,1200));
  location.href   // must have changed to the media-edit URL
  ```
- X does not fire a native OS file picker for uploads — the file input is just rendered on the page;
  tag inputs by a distinguishing attribute (`accept`, position) if more than one exists, then upload.
  The input can render lazily — query for it in its own tool call if a batched query returns nothing.
  **The same duplication trap as the text area applies to file inputs**: a compose page can carry two
  (and a quote-tweet composer its own), so confirm the one you're uploading to actually sits inside
  the active modal (`el.closest('[aria-modal="true"]')`) rather than trusting a raw index.

## ⚠️ The composer stacks — this causes real double-posts

**Clicking outside the modal closes the composer silently, with no save prompt.** The draft stays
mounted in the background. Open a second composer later and press Post, and **both submit** — this
has caused a real double-post (once with media, once without) in production use.

Rules that prevent it:

- **Never click outside the modal** to dismiss anything. Click blank space **inside** the composer
  instead.
- Before pressing Post, confirm exactly **one** composer is mounted **inside the modal specifically**
  — a normal compose page also renders the home timeline behind the modal, which mounts its own
  inline text area, so a bare count of "2 text areas total" across the whole page is the *healthy*
  baseline, not a warning sign. Check which elements are inside the modal, and check their *text*
  (are two different composers carrying different drafts?), not just a raw count:
  ```js
  [...document.querySelectorAll('[data-testid="tweetTextarea_0"]')]
    .map(e=>({inModal:!!e.closest('[aria-modal="true"],[role="dialog"]'), text:e.innerText.trim().slice(0,30)}));
  ```
- **A DOM query can return zeros during a re-render** — `composers: 0, media: 0` right after a Save
  is usually a lie, not an empty composer. Screenshot before believing it, and note the screenshot can
  be stale too. The reliable liveness signal is the browser's own **"Leave site?" dialog**: if
  navigating away triggers it, the composer still holds unsaved content regardless of what the DOM
  query just reported.
- **Click Send via JS matched on `data-testid`, never on button text.** Chrome can auto-translate the
  page, and a text-matching regex throws the moment it renders in a different language (this broke a
  live send once). A status/reply page carries **two** send buttons — `tweetButton` (the modal's own)
  and `tweetButtonInline` (the page's inline reply box) — always target the one contained within the
  modal, explicitly:
  ```js
  const modal=document.querySelector('[aria-modal="true"],[role="dialog"]');
  const withText=[...document.querySelectorAll('[data-testid="tweetTextarea_0"]')]
    .filter(e=>e.innerText.trim());
  if(withText.length!==1) throw new Error('ABORT composers='+withText.length);
  const btn=document.querySelector('[data-testid="tweetButton"]');
  if(!modal || !modal.contains(btn)) throw new Error('ABORT: send button not in modal');
  btn.click();
  ```
  Confirm success on the toast, which is also language-dependent:
  `/(ポストを送信しました|返信を送信しました|Your post was sent)/` (adapt the phrases to the account's
  actual UI language).
- After posting, list the account's most recent posts and check for an accidental duplicate (same
  text / same media) before moving on.
- **You cannot delete a stray post from an automated run** — deleting published content is the
  account owner's call. Hand them the exact post URL and let them decide.

## Drafts vs. publishing

The composer has a **Drafts** save option, distinct from posting. Use it whenever the run's authority
is "build it, don't send it" — **default to drafting** and only publish on an explicit go-ahead for
that specific piece of content, unless the calling context (e.g. a scheduled/autonomous lane) has
standing authorization to publish directly, which overrides the interactive default.

## Reading back a post's own URL (needed for quote-tweets / self-replies)

After a post confirms as sent, the newest post in the account's own timeline (skip the pinned one)
is the one just published — open it to confirm it's the right one before quoting or replying to it:
```js
[...document.querySelectorAll('a[href*="/<handle>/status/"]')]
  .map(a=>a.getAttribute('href')).filter(h=>new RegExp(`^/<handle>/status/\\d+$`).test(h));
// the pinned post is always in this list — skip it, take the newest remaining one
```
A quote-tweet needs a published parent; you cannot quote a draft, so publish first, read the URL
back, then build anything that references it.

## Checklist before every Post

- [ ] Body matches the approved draft verbatim
- [ ] Every hashtag rendered **blue**
- [ ] Character counter not over limit
- [ ] Any image attached, verified by eye, ALT text present with attribution if required
- [ ] Exactly one composer mounted **inside the modal** — confirmed, not assumed
- [ ] Correct account confirmed (see the top of this doc)
- [ ] Publish authority confirmed: standing autonomous authorization, or an explicit human go-ahead

## Video attachments: the browser must be able to DECODE the file, and this one can't (2026-09-05)

Images attach to the X composer through a file input in one call and upload immediately. **Video
does not** — in a Chrome instance whose media pipeline can't decode a local file.

What it looks like: a grey placeholder with a spinner that never resolves, **no request to any
`upload` endpoint**, no console error. X eventually shows a small toast: 「一部の画像/動画を読み込め
ません。」 ("some images/videos could not be loaded").

**Root cause, confirmed directly.** X reads the video's metadata locally to build the preview before
it uploads anything. That read never finishes here:

```js
const url = URL.createObjectURL(new File([bytes],'x.mp4',{type:'video/mp4'}));
const v = document.createElement('video'); v.preload='auto'; v.src = url;
// after 9s:  readyState 0  ·  networkState 2 (NETWORK_LOADING)  ·  no error  ·  no CSP violation
```

The video element sits in NETWORK_LOADING forever and never fires `loadedmetadata`. No upload can
start because X never gets past validation.

**Rule out these first — all were measured and none is the cause:**

| checked | result |
|---|---|
| the encode | 640×360 baseline, no B-frames, 3 s, **67 KB** fails identically to 720p/4.2 MB/55 s. Not size, duration, profile, or container. |
| codec support | `canPlayType` says "probably" for avc1 baseline *and* main; `MediaSource.isTypeSupported` true for both. H.264 is nominally supported. |
| CSP | no `securitypolicyviolation` event fires during the load; `blob:` is not blocked. |
| connectivity | `upload.twitter.com` answers a preflight 202 from the page; both upload hosts resolve and connect from the shell. |

**Do not spend rounds re-encoding.** Run the four-line video-element probe above first: if
`readyState` stays 0, the browser is the problem and no file will work.

**Workarounds that do NOT work** (all measured): synthetic `DragEvent` drop with a `File` (swept all
334 elements in the composer subtree — X checks `isTrusted`); synthetic `ClipboardEvent` paste with a
`File`; a real `ctrl+v` with `text/uri-list` on the X11 clipboard. Getting bytes *into* the page does
work — `navigator.clipboard.readText()` on base64 set with `xclip`, which needs the document focused,
so click into the page first and never let a shell call steal focus in between — but there is nothing
useful to do with them once X refuses untrusted events.

**What to do:** build the post properly, **save it as an X draft**, and have a human attach the video
and send. Two clicks for them, and the draft keeps the exact wording and the quoted post.

## Quote posts: use the 引用 menu, not a URL in the text

Pasting a status URL into the composer leaves a **bare blue link**. It does not render the quoted
post as a card in the composer, and it is not the same object as a quote post. Use the post's repost
button → 引用する, which opens a composer with the quoted post embedded; the comment goes in
「コメントを追加」 above it. Verify before saving: the composer's text should contain 引用 followed by
the quoted author and post.


### When a step genuinely needs the human, hand it off *inside the composer*

Owner's instruction, 2026-09-05, after a video had to be attached by hand:

> "leave the quote tweet open and put the path in the tweet so I see it, know the path to upload and
> know you are asking me to do it and then I'll delete the path text once I am done."

So for any manual step in a post, do **not** just save a draft and describe the gap in chat. Instead:

1. Build the post completely — text, quote card, everything that can be automated.
2. **Append the ask and the absolute file path as a line in the post body itself**, phrased so it is
   unmistakably a note and not content, e.g.
   `⚠ ATTACH THIS THEN DELETE THIS LINE: /abs/path/to/file.mp4`
3. **Leave the composer open on screen.** Don't save-and-close; the open composer is the handoff.
4. Say in chat that it's open and waiting, in one line.

The owner deletes that line after attaching. This puts the ask, the path, and the place to act in a
single screen instead of three, and it makes the remaining work obvious rather than something they
have to reconstruct from a chat message.

**Corollary:** always give an absolute path, never "the file I sent" or a repo-relative path.

### Before concluding a browser can't do video, check chrome://media-internals

The instance that failed above was **real Google Chrome 149** (`/opt/google/chrome`, Widevine
present), not a codec-less Chromium — so H.264 should have decoded and the stall is probably
configuration, not a missing codec. If this recurs, load `chrome://media-internals` in a second tab,
reproduce the attach, and read the pipeline error there before declaring it unfixable. Launch flags
worth suspecting: `--disable-dev-shm-usage`, and anything touching the GPU process.
