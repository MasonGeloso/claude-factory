# Factory Marketing — Platforms — <PROJECT NAME>

> Every platform this project posts to, and the mechanics of operating it. Read by
> `/factory-marketing-post` (the dispatcher) and any on-demand content skill before it touches a
> composer. Filled during onboarding via `factory-marketing-onboard`; one section per platform, no
> per-platform files/folders — keep it all in this one doc.

<!-- Repeat this section per platform. Delete/keep only the ones this project actually uses. -->

## <Platform name, e.g. "X (Twitter)">

- **Account / handle:** <@handle or account name>
- **Credentials:** <env var names only, e.g. nothing needed if it's a logged-in Chrome session —
  never put an actual secret in this file>
- **Account-switch check (MANDATORY, every single run, no exceptions):** <exactly how to confirm the
  right account is active before touching any composer on this platform — e.g. "confirm the handle
  in the bottom-left account switcher matches @handle">
- **Mechanics:** <either paste/adapt the built-in starter for this platform from
  `factory-marketing-onboard/starters/` (e.g. `x-post.md`, `x-article.md`, `youtube.md`), or, for a
  platform with no built-in starter, write the mechanics learned live during onboarding — composer
  quirks, upload traps, double-post/double-publish risks, anything that cost real time to discover>
- **Tone / formality default:** <e.g. casual and informal | formal, no contractions | matches the
  content type's own override if its file under content-types/ specifies one for this platform>
- **De-slop pass:** <run `factory-humanizer` in which language, if any, before anything on this
  platform goes out>
- **Publish authority default:** <draft-only (default) | this platform has standing autonomous
  publish authority for [which content types] — name them explicitly, don't leave it implicit>

<!-- Repeat the section above for each additional platform. -->
