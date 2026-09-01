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
- **Sourcing from Wikimedia Commons:** query the category API directly rather than guessing a file
  URL — it returns the real filenames and their license metadata in one call:
  ```bash
  curl -s "https://commons.wikimedia.org/w/api.php?action=query&list=categorymembers&cmtitle=Category:<Name>&cmtype=file&format=json"
  ```
  Then resolve each candidate's actual license via `imageinfo` (`iiprop=extmetadata`) before using it
  — don't assume from the category alone. **Prefer CC BY over CC BY-SA** when both are available for
  the same subject — CC BY-SA's share-alike clause can complicate reuse in a post's context in ways
  a plain attribution license doesn't; when only CC BY-SA exists, it's still usable, just note the
  license (not only the author) in the ALT-text attribution.
- **Attribution goes in the ALT text**, not the post body — there's no room in the body, and it also
  makes the post accessible. Hover the attached image → **Add description**, paste, **Save**.
  Confirm the small **ALT** badge appears on the thumbnail afterward.
- X does not fire a native OS file picker for uploads — the file input is just rendered on the page;
  tag inputs by a distinguishing attribute (`accept`, position) if more than one exists, then upload.
  The input can render lazily — query for it in its own tool call if a batched query returns nothing.

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
is the one just published — open it to confirm it's the right one before quoting or replying to it.
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
