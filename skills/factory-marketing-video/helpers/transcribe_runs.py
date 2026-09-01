"""Silence-segmented batch transcription: exact timing from audio, text from a hosted model.

Why this exists
---------------
Word-level ASR timestamps are the usual way to place cuts, but they drift badly
around long pauses -- Whisper in particular absorbs a 2.5s silence into the
duration of the adjacent word, which makes "cut in the middle of the pause"
impossible to compute from the transcript alone.

This helper inverts the dependency. `ffmpeg silencedetect` finds the pauses in
the waveform, which is ground truth and needs no model. That partitions the
timeline into speech RUNS with exact boundaries. Each run is then transcribed as
its own batch request, in parallel, so every run carries accurate text AND exact
timing. Cut points come from the silence between runs, never from the model.

This is the right transcriber for take-structured recordings (verbal slates and
"restart" markers), where what matters is which runs to keep and where the pauses
are -- not sub-word precision inside a run.

Cost note: one request per speech run. A 100s recording is ~15 requests.

Usage:
    python helpers/transcribe_runs.py <video>
    python helpers/transcribe_runs.py <video> --edit-dir /custom/edit
    python helpers/transcribe_runs.py <video> --noise -32dB --min-silence 0.30
    python helpers/transcribe_runs.py <video> --model gpt-4o-transcribe --workers 8
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

# Nudges the model toward verbatim disfluencies and keeps slate words intact.
CONTEXT_PROMPT = (
    "Spoken-word video recording. Transcribe verbatim, including fillers like "
    "um and uh. The speaker announces sections out loud (\"intro\", \"section one\", "
    "\"section two\") and says \"restart\" when redoing a section."
)


def run_cmd(cmd: list[str]) -> str:
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    return p.stdout


def extract_audio(video: Path, dest: Path) -> None:
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(video), "-vn", "-ac", "1", "-ar", "16000",
         "-c:a", "pcm_s16le", str(dest)],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )


def media_duration(path: Path) -> float:
    out = run_cmd(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                   "-of", "default=nw=1:nk=1", str(path)])
    return float(out.strip().splitlines()[0])


def detect_silences(audio: Path, noise: str, min_silence: float) -> list[tuple[float, float]]:
    """Return [(silence_start, silence_end)] from ffmpeg silencedetect."""
    out = run_cmd(["ffmpeg", "-hide_banner", "-nostats", "-i", str(audio),
                   "-af", f"silencedetect=noise={noise}:d={min_silence}", "-f", "null", "-"])
    starts = [float(m) for m in re.findall(r"silence_start:\s*(-?[\d.]+)", out)]
    ends = [float(m) for m in re.findall(r"silence_end:\s*(-?[\d.]+)", out)]
    return list(zip(starts, ends))


def speech_runs(silences: list[tuple[float, float]], duration: float,
                min_run: float) -> list[tuple[float, float]]:
    """Invert the silence list into speech runs, dropping sub-threshold blips."""
    runs: list[tuple[float, float]] = []
    cursor = 0.0
    for s_start, s_end in silences:
        if s_start > cursor:
            runs.append((cursor, min(s_start, duration)))
        cursor = max(cursor, s_end)
    if cursor < duration:
        runs.append((cursor, duration))
    return [(a, b) for a, b in runs if (b - a) >= min_run]


def transcribe_run(args: tuple) -> tuple[int, str]:
    idx, audio_path, start, end, pad, model, api_key = args
    from openai import OpenAI

    client = OpenAI(api_key=api_key)
    a = max(0.0, start - pad)
    dur = (end - start) + 2 * pad
    with tempfile.TemporaryDirectory() as tmp:
        slice_path = Path(tmp) / f"run_{idx:03d}.wav"
        subprocess.run(
            ["ffmpeg", "-y", "-ss", f"{a:.3f}", "-i", str(audio_path), "-t", f"{dur:.3f}",
             "-c:a", "pcm_s16le", str(slice_path)],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        try:
            with open(slice_path, "rb") as f:
                resp = client.audio.transcriptions.create(
                    model=model, file=f, response_format="text", prompt=CONTEXT_PROMPT,
                )
            text = (resp if isinstance(resp, str) else getattr(resp, "text", "")).strip()
        except Exception as e:                       # one bad run must not kill the batch
            text = f"[transcription failed: {type(e).__name__}]"
    return idx, text


def main() -> None:
    ap = argparse.ArgumentParser(description="Silence-segmented batch transcription")
    ap.add_argument("video", type=Path)
    ap.add_argument("--edit-dir", type=Path, default=None)
    ap.add_argument("--model", default="gpt-4o-transcribe")
    ap.add_argument("--noise", default="-32dB", help="silencedetect noise floor")
    ap.add_argument("--min-silence", type=float, default=0.30,
                    help="shortest pause that splits two runs (s)")
    ap.add_argument("--min-run", type=float, default=0.20,
                    help="drop speech runs shorter than this (s)")
    ap.add_argument("--pad", type=float, default=0.15,
                    help="audio padding each side when slicing a run for ASR (s)")
    ap.add_argument("--workers", type=int, default=8)
    args = ap.parse_args()

    video = args.video.resolve()
    if not video.exists():
        sys.exit(f"video not found: {video}")
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        sys.exit("OPENAI_API_KEY not set")

    edit_dir = (args.edit_dir or (video.parent / "edit")).resolve()
    out_path = edit_dir / "transcripts" / f"{video.stem}.runs.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if out_path.exists():                            # Hard Rule 9
        print(f"cached: {out_path.name}")
        return

    with tempfile.TemporaryDirectory() as tmp:
        audio = Path(tmp) / "a.wav"
        extract_audio(video, audio)
        duration = media_duration(audio)
        silences = detect_silences(audio, args.noise, args.min_silence)
        runs = speech_runs(silences, duration, args.min_run)
        print(f"{len(silences)} silences -> {len(runs)} speech runs over {duration:.2f}s", flush=True)
        print(f"transcribing with {args.model} ({args.workers} workers)", flush=True)

        jobs = [(i, audio, a, b, args.pad, args.model, api_key)
                for i, (a, b) in enumerate(runs)]
        texts: dict[int, str] = {}
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            for idx, text in pool.map(transcribe_run, jobs):
                texts[idx] = text

    payload = {
        "source": str(video),
        "duration": round(duration, 3),
        "model": args.model,
        "silence_params": {"noise": args.noise, "min_silence": args.min_silence},
        "runs": [
            {
                "index": i,
                "start": round(a, 3),
                "end": round(b, 3),
                "duration": round(b - a, 3),
                # Pause AFTER this run -- the splice window (None on the last run).
                "gap_after": (round(runs[i + 1][0] - b, 3) if i + 1 < len(runs) else None),
                "text": texts.get(i, ""),
            }
            for i, (a, b) in enumerate(runs)
        ],
    }
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
    print(f"saved: {out_path}")
    print()
    for r in payload["runs"]:
        gap = f"{r['gap_after']:.2f}s" if r["gap_after"] is not None else "  -- "
        print(f"  [{r['index']:02d}] {r['start']:7.2f}-{r['end']:7.2f}  gap {gap}  {r['text'][:88]}")


if __name__ == "__main__":
    main()
