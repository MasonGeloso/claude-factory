"""Filler removal + silence tightening -> EDL, with cuts snapped to energy minima.

Builds a keep-list by subtracting unwanted intervals from the timeline:

  1. filler words ("um", "uh", ...) located from a word-level transcript
  2. explicit --drop ranges (spoken asides, interruptions, dead sections)
  3. the excess of any pause longer than --gap-threshold
  4. everything after --keep-until

Cut placement
-------------
The failure mode this is built to avoid is clipping the end of a word. Three
rules, in order of importance:

1. **Measure the noise floor; never assume a threshold.** A voice recording's
   floor varies by 40dB between setups. Picking a fixed `silencedetect` value
   like -35dB against a floor of -87dB classifies ordinary speech decay as
   silence, and every cut then lands inside a word. The floor is measured here
   and the threshold derived from it.

2. **Snap every cut edge to the local energy minimum**, not to a threshold
   crossing. Threshold crossings sit on the slope of a decaying vowel; the
   minimum sits in the actual gap. Searching +/-`--snap` for the quietest point
   is what makes a cut inaudible.

3. **Veto any cut with no quiet point near it.** If the snapped minimum is still
   louder than the speech floor, there is no pause there to hide a cut in, so the
   cut is abandoned. Leaving a filler in is always better than clipping a word.

Word endings get more padding than word beginnings (`--tail-pad` > `--lead-pad`):
a clipped final consonant is far more audible than a tight entry.

The tool self-reports how many boundaries still land in speech. That number
should be ~0; if it is not, raise --tail-pad or --snap and re-run.

Usage:
    python helpers/tighten.py <video> --edit-dir <dir> --edl <out.json>
    python helpers/tighten.py <video> ... --keep-until 739.9 --drop 317.8-325.2
    python helpers/tighten.py <video> ... --gap-threshold 0.55 --tail-pad 0.18
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import soundfile as sf

DEFAULT_FILLERS = r"^(um+|uh+|uhh+|erm|er|hmm+|mm+|ah+)[,.!?]*$"
HOP = 0.005          # 5ms envelope resolution
WIN = 0.020          # 20ms RMS window


def extract_audio(video: Path, dest: Path) -> None:
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(video), "-vn", "-ac", "1", "-ar", "16000",
         "-c:a", "pcm_s16le", str(dest)],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )


class Envelope:
    """Short-time RMS in dB, with helpers for snapping cuts to quiet points."""

    def __init__(self, wav: Path):
        x, sr = sf.read(str(wav))
        if x.ndim > 1:
            x = x.mean(axis=1)
        self.sr = sr
        self.duration = len(x) / sr
        hop_n, win_n = int(HOP * sr), int(WIN * sr)
        n = max(1, (len(x) - win_n) // hop_n)
        # Vectorised framing: one row per hop, then RMS across each row.
        idx = np.arange(n)[:, None] * hop_n + np.arange(win_n)[None, :]
        frames = x[np.clip(idx, 0, len(x) - 1)]
        rms = np.sqrt(np.mean(frames.astype(np.float64) ** 2, axis=1))
        self.db = 20 * np.log10(np.maximum(rms, 1e-10))
        self.t = np.arange(n) * HOP + WIN / 2

        self.floor = float(np.percentile(self.db, 5))
        self.speech = float(np.percentile(self.db, 75))
        # Both thresholds are relative to THIS recording's speech level, not
        # absolute dB. 22dB down is a real inter-word pause; a fixed value like
        # -35dB was 52dB above this recording's floor and ate word tails.
        self.pause = self.speech - 22.0        # quiet enough to place a cut in
        self.clip_th = self.speech - 15.0      # louder than this at a boundary = clipped
        self.quiet_cut = self.pause
        self.silence_th = self.pause

    def i(self, t: float) -> int:
        return int(np.clip(t / HOP, 0, len(self.db) - 1))

    def level(self, t: float) -> float:
        return float(self.db[self.i(t)])

    def snap(self, t: float, back: float, fwd: float,
             lo: float | None = None, hi: float | None = None) -> tuple[float, float] | None:
        """Move t to the quietest point in [t-back, t+fwd], clamped to [lo, hi].

        The window is asymmetric and the clamps are hard because a symmetric
        search will happily walk a cut edge backwards into the previous word --
        it is quieter in there than in the pause. `lo`/`hi` are the neighbouring
        word boundaries: a cut edge may move within the pause, never across a
        word. This is what stops "...the regular stock market" becoming
        "...the regular stock".
        """
        t0, t1 = t - back, t + fwd
        if lo is not None:
            t0 = max(t0, lo)
        if hi is not None:
            t1 = min(t1, hi)
        a, b = self.i(t0), self.i(t1)
        if b <= a:
            return None
        seg = self.db[a:b + 1]
        k = int(np.argmin(seg))
        lvl = float(seg[k])
        if lvl > self.quiet_cut:
            return None
        return (float((a + k) * HOP + WIN / 2), lvl)

    def expand_quiet(self, t: float, direction: int, reach: float) -> float:
        """Walk outward from t through contiguous quiet, stopping at the first loud frame.

        This is the safe way to widen a cut. A windowed search for the local
        minimum can land on the far side of a neighbouring word -- that point is
        genuinely silent, so the cut is inaudible, but everything between is
        deleted and the word vanishes. Expanding frame by frame cannot jump a
        word: the word's own energy halts the walk.
        """
        step = direction * HOP
        limit = t + direction * reach
        cur = t
        while (direction > 0 and cur + step <= limit) or (direction < 0 and cur + step >= limit):
            nxt = cur + step
            if self.level(nxt) > self.quiet_cut:
                break
            cur = nxt
        return cur

    def next_quiet(self, t: float, direction: int, reach: float) -> float | None:
        """First quiet frame at or beyond t in `direction`. None if none within reach."""
        n = int(reach / HOP)
        for k in range(n + 1):
            cand = t + direction * k * HOP
            if self.level(cand) <= self.pause:
                return cand
        return None

    def safe_edge(self, t: float, side: str, reach: float) -> float:
        """Place a cut edge at t without ever landing in speech.

        `side="start"` is the beginning of a removed region, `side="end"` its end.
        First try expanding outward through silence (removes adjacent dead air).
        If t is inside speech -- ASR word boundaries are routinely 300ms out, so
        this happens -- retreat *inward* to the next quiet frame instead. Both
        moves keep more audio; neither can truncate a word.
        """
        inward = +1 if side == "start" else -1
        if self.level(t) <= self.pause:
            return self.expand_quiet(t, -inward, reach)
        found = self.next_quiet(t, inward, reach)
        return found if found is not None else t

    def silences(self, min_dur: float) -> list[tuple[float, float]]:
        """Contiguous stretches below the derived silence threshold."""
        below = self.db < self.silence_th
        out: list[tuple[float, float]] = []
        start = None
        for i, v in enumerate(below):
            if v and start is None:
                start = i
            elif not v and start is not None:
                a, b = start * HOP, i * HOP
                if b - a >= min_dur:
                    out.append((a, b))
                start = None
        if start is not None:
            a, b = start * HOP, len(below) * HOP
            if b - a >= min_dur:
                out.append((a, b))
        return out


def subtract(keep: list[list[float]], cuts: list[tuple[float, float]]) -> list[list[float]]:
    for c0, c1 in sorted(cuts):
        out: list[list[float]] = []
        for k0, k1 in keep:
            if c1 <= k0 or c0 >= k1:
                out.append([k0, k1])
                continue
            if c0 > k0:
                out.append([k0, min(c0, k1)])
            if c1 < k1:
                out.append([max(c1, k0), k1])
        keep = out
    return keep


def parse_range(text: str) -> tuple[float, float]:
    m = re.match(r"^\s*([\d.]+)\s*-\s*([\d.]+)\s*$", text)
    if not m:
        raise argparse.ArgumentTypeError(f"expected START-END, got {text!r}")
    return (float(m.group(1)), float(m.group(2)))


def main() -> None:
    ap = argparse.ArgumentParser(description="Filler removal + silence tightening")
    ap.add_argument("video", type=Path)
    ap.add_argument("--edit-dir", type=Path, default=None)
    ap.add_argument("--edl", type=Path, required=True)
    ap.add_argument("--keep-until", type=float, default=None)
    ap.add_argument("--keep-from", type=float, default=0.0)
    ap.add_argument("--drop", type=parse_range, action="append", default=[])
    ap.add_argument("--fillers", default=DEFAULT_FILLERS)
    ap.add_argument("--gap-threshold", type=float, default=0.55,
                    help="pauses longer than this get trimmed")
    ap.add_argument("--tail-pad", type=float, default=0.18,
                    help="audio kept after a word before a cut (s)")
    ap.add_argument("--lead-pad", type=float, default=0.12,
                    help="audio kept before the next word after a cut (s)")
    ap.add_argument("--snap", type=float, default=0.12,
                    help="search radius for the local energy minimum (s)")
    ap.add_argument("--min-segment", type=float, default=0.12)
    ap.add_argument("--no-fillers", action="store_true", help="only trim silence")
    ap.add_argument("--filler-pause", type=float, default=18.0,
                    help="dB below speech that counts as a pause when excising a "
                         "filler. Lower = more fillers cut, more splice artefacts.")
    args = ap.parse_args()

    video = args.video.resolve()
    if not video.exists():
        sys.exit(f"video not found: {video}")
    edit_dir = (args.edit_dir or (video.parent / "edit")).resolve()
    tpath = edit_dir / "transcripts" / f"{video.stem}.json"
    if not tpath.exists():
        sys.exit(f"word transcript not found: {tpath}")
    words = [w for w in json.loads(tpath.read_text())["words"]
             if w.get("type", "word") == "word"]

    with tempfile.TemporaryDirectory() as tmp:
        wav = Path(tmp) / "a.wav"
        extract_audio(video, wav)
        env = Envelope(wav)

    print(f"{video.name}")
    print(f"  noise floor {env.floor:.1f} dB | speech {env.speech:.1f} dB | "
          f"pause level {env.pause:.1f} dB | clipping above {env.clip_th:.1f} dB")

    duration = env.duration
    end = args.keep_until if args.keep_until is not None else duration
    if args.keep_until is not None:
        snapped = env.snap(end, back=args.snap, fwd=args.snap)
        if snapped:
            end = snapped[0]
    keep: list[list[float]] = [[args.keep_from, min(end, duration)]]

    cuts: list[tuple[float, float]] = []
    n_fill = n_fill_veto = n_gap = 0

    if not args.no_fillers:
        fill_re = re.compile(args.fillers, re.I)
        for i, w in enumerate(words):
            if not fill_re.match((w.get("text") or "").strip()):
                continue
            ws, we = float(w["start"]), float(w["end"])
            # The filler pass gets its own, looser notion of "pause". A cut here
            # is masked by the 30ms fades render.py puts at every segment edge,
            # whereas the silence pass must stay strict to protect word tails.
            strict, env.quiet_cut = env.quiet_cut, env.speech - args.filler_pause
            a = env.expand_quiet(ws, -1, args.snap)
            b = env.expand_quiet(we, +1, args.snap)
            env.quiet_cut = strict
            # Require real silence on at least one side, and leave a sliver of it
            # behind so the join keeps a breath instead of butting two words.
            sil_left, sil_right = ws - a, b - we
            if sil_left + sil_right < 0.05:
                n_fill_veto += 1          # embedded mid-phrase; leave the filler in
                continue
            a += min(0.03, sil_left / 2)
            b -= min(0.03, sil_right / 2)
            if b - a < 0.05:
                n_fill_veto += 1
                continue
            # Final guard, applied to every cut regardless of how it was derived:
            # an edge sitting in speech means a truncated word. Drop the cut.
            if env.level(a) > env.clip_th or env.level(b) > env.clip_th:
                n_fill_veto += 1
                continue
            cuts.append((a, b))
            n_fill += 1

    for s0, s1 in env.silences(0.20):
        if (s1 - s0) <= args.gap_threshold:
            continue
        c0, c1 = s0 + args.tail_pad, s1 - args.lead_pad
        if c1 - c0 > 0.05:
            cuts.append((c0, c1))
            n_gap += 1

    # Hand-specified boundaries get snapped too. A range typed from a transcript
    # is an eyeball estimate and lands mid-word as easily as an ASR timestamp does.
    def word_gap(t: float) -> tuple[float, float]:
        """The (prev word end, next word start) surrounding time t."""
        prev = max((float(w["end"]) for w in words if float(w["end"]) <= t), default=0.0)
        nxt = min((float(w["start"]) for w in words if float(w["start"]) >= t), default=duration)
        return prev, nxt

    for d0, d1 in args.drop:
        # A typed range is an estimate. Resolve it to whole words -- those whose
        # midpoint falls inside -- then expand outward through silence only.
        inside = [w for w in words if d0 <= (float(w["start"]) + float(w["end"])) / 2 <= d1]
        if not inside:
            cuts.append((d0, d1))
            print(f"  warning: --drop {d0}-{d1} covers no words; used verbatim")
            continue
        # Retreat is bounded by the first/last removed word's own span. Letting it
        # run further lets the edge skip over whole words, which leaves them
        # dangling in the output ("...stock market, let me, there's a bit...").
        # If no quiet frame exists inside that bound, take the word boundary and
        # accept a faint edge -- a click beats a stranded half-phrase.
        a0, b0 = float(inside[0]["start"]), float(inside[-1]["end"])
        if env.level(a0) <= env.pause:
            a = env.expand_quiet(a0, -1, 0.40)
        else:
            a = env.next_quiet(a0, +1, min(0.40, float(inside[0]["end"]) - a0)) or a0
        if env.level(b0) <= env.pause:
            b = env.expand_quiet(b0, +1, 0.40)
        else:
            b = env.next_quiet(b0, -1, min(0.40, b0 - float(inside[-1]["start"]))) or b0
        cuts.append((a, b))
        print(f"  drop {d0}-{d1} -> {a:.2f}-{b:.2f}  "
              f"({len(inside)} words: {' '.join(x['text'] for x in inside[:6])}...)")

    keep = subtract(keep, cuts)
    keep = [k for k in keep if (k[1] - k[0]) >= args.min_segment]
    merged: list[list[float]] = []
    for k in keep:
        if merged and k[0] - merged[-1][1] < 0.02:
            merged[-1][1] = k[1]
        else:
            merged.append(list(k))

    # Self-check: how loud is the audio right at each boundary?
    bad_end = [k for k in merged if env.level(k[1] - 0.015) > env.clip_th]
    bad_start = [k for k in merged if env.level(k[0] + 0.010) > env.clip_th]

    total = sum(b - a for a, b in merged)
    stem = video.stem
    args.edl.parent.mkdir(parents=True, exist_ok=True)
    args.edl.write_text(json.dumps({
        "version": 1,
        "sources": {stem: str(video)},
        "ranges": [{"source": stem, "start": round(a, 3), "end": round(b, 3),
                    "beat": f"seg_{i}"} for i, (a, b) in enumerate(merged)],
        "grade": "none",
        "total_duration_s": round(total, 2),
    }, indent=2))

    print(f"  {duration:.1f}s -> {total:.1f}s ({100*total/duration:.0f}%), {len(merged)} segments")
    print(f"  fillers cut {n_fill}, left in place {n_fill_veto} (no pause to cut into)")
    print(f"  pauses trimmed {n_gap} (>{args.gap_threshold}s)")
    if args.keep_until is not None:
        print(f"  tail dropped from {args.keep_until:.2f}s ({duration - args.keep_until:.1f}s)")
    print(f"  CUT-QUALITY: {len(bad_end)} ends and {len(bad_start)} starts land in speech "
          f"(want 0 of {len(merged)})")
    for k in sorted(bad_end, key=lambda k: -env.level(k[1] - 0.015))[:5]:
        print(f"     end {k[1]:8.2f}s at {env.level(k[1]-0.015):6.1f} dB")
    print(f"  wrote {args.edl}")


if __name__ == "__main__":
    main()
