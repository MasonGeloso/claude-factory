# -*- coding: utf-8 -*-
"""Piecewise time-warp a real cast. Bytes are never touched — only how fast the
recording plays back in each phase, the way any screencast is edited.

SEGMENTS: (start_s, end_s, speed). Anything past the last segment's end is cut.
"""
import json, sys

src, dst = sys.argv[1], sys.argv[2]
SEGMENTS = json.loads(sys.argv[3])
# Optional freeze-frames: [[real_time, seconds], ...]. Everything after `real_time` is
# pushed later by `seconds`, which holds the last rendered frame on screen. The payoff
# table scrolls out of view on its own, so it has to be held deliberately.
DWELLS = json.loads(sys.argv[4]) if len(sys.argv) > 4 else []

lines = open(src, encoding="utf-8").read().splitlines()
hdr = json.loads(lines[0])
ev = [json.loads(l) for l in lines[1:] if l.strip()]

def warp(ts):
    """Map an original timestamp onto the edited timeline."""
    out = 0.0
    for a, b, sp in SEGMENTS:
        if ts <= a:
            break
        out += (min(ts, b) - a) / sp
        if ts <= b:
            break
    for at, hold in DWELLS:
        if ts > at:
            out += hold
    return out

end = SEGMENTS[-1][1]
# Claude Code pads its input line with U+00A0 (no-break space), which agg has no glyph
# for and draws as a tofu box next to the prompt. Substitute a plain space: identical
# whitespace on screen, no missing-glyph artefact.
kept = [[round(warp(t), 6), k, d.replace("\u00a0", " ")] for t, k, d in ev if t <= end]

with open(dst, "w", encoding="utf-8") as f:
    f.write(json.dumps(hdr) + "\n")
    for e in kept:
        f.write(json.dumps(e, ensure_ascii=False) + "\n")

print(f"{src}: {ev[-1][0]:.1f}s -> {kept[-1][0]:.1f}s  ({len(kept)}/{len(ev)} events kept)")
for a, b, sp in SEGMENTS:
    print(f"   {a:6.1f}-{b:6.1f}s  x{sp:<5g} -> {warp(a):6.1f}-{warp(b):6.1f}s")
