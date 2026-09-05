# OS chrome

`macos.html` is the page the recorder points at: an `asciinema-player` inside a CSS macOS window
(wallpaper, menu bar, dock, frosted glass). It is a template — swap it for your own chrome, or set
`chrome.theme: "plain"` in `demo.json` and use a bare terminal panel.

## What this directory does NOT ship

**Icons.** The dock expects `icons/*.svg`. Nothing is bundled, deliberately: the set this was built
against is **WhiteSur** (`github.com/vinceliuice/WhiteSur-icon-theme`), which is **GPL-3.0**, and
that is a licence decision for the consuming project, not for a skill.

Do not substitute hand-drawn approximations. They read as fake no matter how much they are tweaked,
mostly because macOS icons are **squircles** (superellipse, |x|ⁿ+|y|ⁿ=1, n≈5) rather than rounded
rectangles. If you must clip them yourself, note that `clip-path: path()` takes **absolute** units
and will not scale with the element — use an SVG `clipPath` with `clipPathUnits="objectBoundingBox"`.

Also: WhiteSur's `links/` entries are symlinks, so a raw fetch returns the link text rather than
the SVG. Always `file` what you downloaded.

**Wallpaper and fonts.** Point `chrome.wallpaper` at your own. For the UI font, Inter is the closest
free stand-in for SF Pro (fetch it from the Google Fonts CSS2 API — the `rsms/inter` raw GitHub path
returns HTML error pages). Inter has no CJK, so a Japanese face must sit behind it in the stack or
the menu bar renders as tofu.

## The two things most likely to bite

1. **Verify the theme actually applied.** A `<style>` block placed after `</html>` is ignored, so
   every render silently uses the player's default palette — and the symptom looks exactly like a
   content bug. Read it back:
   ```js
   getComputedStyle(document.querySelector('#term .ap-term'))
     .getPropertyValue('--term-color-7')
   ```
   Note the v3 DOM is `.ap-term` and the theme class is `.asciinema-player-theme-<name>` —
   *not* `.ap-terminal`.

2. **Contrast on the echoed prompt.** Many CLIs emit the echoed input on `--term-color-8`
   (bright-black background, SGR 100), not the body background. If that token is near the
   foreground colour the prompt block is unreadable while everything else looks fine. Measure it;
   do not eyeball it.

Two smaller ones: give `--term-color-background` a real translucent dark colour rather than
`transparent`, and use `width: max-content` on the window so it shrink-wraps the terminal instead of
leaving dead space. `backdrop-filter: blur()` is what makes the glass — keep the text fully opaque
and let the wallpaper show through the *background*; fading the whole terminal just dims the text.
Glass opacity is a readability trade (0.76 dropped body contrast to 4.8:1; 0.88 gives 14.3:1).

If you animate the window in, the keyframes must preserve the existing `translate(-50%,-50%)` or the
centring breaks mid-animation, and gate it with `animation-play-state` so the recorder catches it.
