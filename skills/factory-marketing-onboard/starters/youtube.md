# YouTube — publishing

Drive it only through the owner's logged-in Chrome (`claude-in-chrome`). Publishing here is
**human-gated by design**, not an oversight — treat every rule below as load-bearing.

**Switch channel before anything else.** Avatar → Switch account. Confirm the channel name in the
sidebar. A video published to the wrong channel is a real mess to undo — this is the one platform
where an account-switch check has already been battle-tested; every other platform's starter in this
suite copies this same rule for the same reason.

**The browser bridge caps file uploads at a few MB** — thumbnails and caption files go through fine,
but a full-size video file does not. **Hand the video off to the human to select** via the native
picker, then take over the metadata fields. Do not build a workaround for this unless explicitly
asked to.

`127.0.0.1` and `localhost` can be treated as different entries in Chrome's site-permission list —
if a local URL is refused, try the other spelling before concluding it's actually blocked.

**Typing long text into form fields is error-prone** — synthesized keystrokes can silently drop a
character in a figure that was already carefully verified. Read the field back and diff it against
the source before moving on, or paste instead of typing.

**Defaults that are usually wrong:** category tends to default to something generic; video language
is usually unset. Set both explicitly.

**Chapter rules** (if used): first chapter must be `00:00`, at least three chapters, each at least
10s apart, and the last at least 10s before the video ends. Derive chapters from real content-section
boundaries, not round numbers.

**Auto-translate needs *published* captions in the original language** — YouTube's own
auto-generated captions do not satisfy this requirement, and the option stays greyed out with an
unhelpful tooltip if you rely on them. Upload a real caption track to the "(video language)" row and
publish it explicitly.

**Publishing is irreversible and outward-facing.** Walk the whole flow, stop at the visibility step,
and get explicit human confirmation before clicking Publish. Any legal/audience declaration (e.g.
"made for kids") is the account owner's answer to give, not something to infer or answer on their
behalf.
