"""Local word-level ASR fallback, emitting Scribe-compatible transcript JSON.

Drop-in alternative to `transcribe.py` for machines with no ELEVENLABS_API_KEY.
Uses faster-whisper with `word_timestamps=True` and a disfluency-biased
initial_prompt so fillers and false starts survive into the transcript -- they
are the editorial signal, so a clean-reading transcript is a broken one here.

Scribe remains the better transcriber (tighter timestamps, real diarization,
audio-event tags). Reach for this when there is no key, or when the material is
a single-speaker screen recording where diarization buys nothing.

Output schema matches what pack_transcripts.py and tighten.py expect:
    {"language_code":..., "text":..., "words":[{text,start,end,type,speaker_id}]}
with 'spacing' entries between words carrying the silence gaps.

Usage:
    python helpers/transcribe_local.py <video>
    python helpers/transcribe_local.py <video> --edit-dir /custom/edit
    python helpers/transcribe_local.py <video> --model large-v3 --language en
"""

from __future__ import annotations

import argparse
import ctypes
import json
import subprocess
import sys
import tempfile
from pathlib import Path

# Biases the decoder toward verbatim disfluencies instead of tidying them away.
FILLER_PROMPT = {
    "en": "Um, uh, so, like, you know, I mean, uhh, hmm, er, well...",
    "ja": "えーと、あの、その、まあ、うーん、えっと、なんか、ええ。",
}


def preload_cuda_libs() -> None:
    """Preload pip-installed cuDNN/cuBLAS so ctranslate2's dlopen finds them.

    faster-whisper links cuDNN at runtime. When CUDA came from pip wheels rather
    than a system install, the loader has no path to them and CUDA init dies with
    'Unable to load libcudnn_ops.so.9'. Preloading with RTLD_GLOBAL fixes it
    without the caller having to export LD_LIBRARY_PATH.
    """
    try:
        import nvidia  # noqa: F401
    except ImportError:
        return
    root = Path(sys.prefix) / "lib"
    for pattern in ("nvidia/cudnn/lib/lib*.so*", "nvidia/cublas/lib/lib*.so*"):
        for so in sorted(Path(root).glob(f"python*/site-packages/{pattern}")):
            try:
                ctypes.CDLL(str(so), mode=ctypes.RTLD_GLOBAL)
            except OSError:
                pass


def extract_audio(video: Path, dest: Path) -> None:
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(video), "-vn", "-ac", "1", "-ar", "16000",
         "-c:a", "pcm_s16le", str(dest)],
        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )


def load_model(model_name: str):
    from faster_whisper import WhisperModel

    preload_cuda_libs()
    try:
        m = WhisperModel(model_name, device="cuda", compute_type="float16")
        # Force CUDA init now so we can fall back before burning time on audio.
        m.transcribe(__probe_silence(), beam_size=1, without_timestamps=True)
        print(f"  model: {model_name} on cuda/float16", flush=True)
        return m
    except Exception as e:
        print(f"  cuda unavailable ({type(e).__name__}); falling back to cpu/int8", flush=True)
        return WhisperModel(model_name, device="cpu", compute_type="int8")


_PROBE: Path | None = None


def __probe_silence() -> str:
    """0.2s of silence used only to force CUDA initialization."""
    global _PROBE
    if _PROBE is None:
        tmp = Path(tempfile.mkdtemp()) / "probe.wav"
        subprocess.run(
            ["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=16000:cl=mono",
             "-t", "0.2", "-c:a", "pcm_s16le", str(tmp)],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        _PROBE = tmp
    return str(_PROBE)


def transcribe_one(video: Path, edit_dir: Path, model_name: str,
                   language: str | None = None, verbose: bool = True) -> Path:
    out_path = edit_dir / "transcripts" / f"{video.stem}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if out_path.exists():                      # Hard Rule 9: never re-transcribe
        if verbose:
            print(f"cached: {out_path.name}")
        return out_path

    with tempfile.TemporaryDirectory() as tmp:
        audio = Path(tmp) / "a.wav"
        extract_audio(video, audio)
        model = load_model(model_name)

        lang = language
        if lang is None:
            _, info = model.transcribe(str(audio), beam_size=1, without_timestamps=True)
            lang = info.language
            if verbose:
                print(f"  language: {lang} (p={info.language_probability:.2f})", flush=True)

        segments, _ = model.transcribe(
            str(audio),
            language=lang,
            beam_size=5,
            word_timestamps=True,
            condition_on_previous_text=False,  # stops it smoothing over disfluencies
            initial_prompt=FILLER_PROMPT.get(lang),
            vad_filter=False,                  # keep real silence gaps in the timeline
        )

        words: list[dict] = []
        full_text: list[str] = []
        prev_end: float | None = None
        for seg in segments:
            for w in seg.words or []:
                txt = w.word.strip()
                if not txt:
                    continue
                if prev_end is not None and w.start > prev_end:
                    words.append({"text": " ", "start": round(prev_end, 3),
                                  "end": round(w.start, 3), "type": "spacing",
                                  "speaker_id": "speaker_0"})
                words.append({"text": txt, "start": round(w.start, 3),
                              "end": round(w.end, 3), "type": "word",
                              "speaker_id": "speaker_0"})
                full_text.append(txt)
                prev_end = w.end

    payload = {
        "language_code": lang,
        "text": " ".join(full_text),
        "words": words,
        "_asr": f"faster-whisper/{model_name} (local fallback, verbatim-biased)",
    }
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
    if verbose:
        n = sum(1 for w in words if w["type"] == "word")
        print(f"saved: {out_path}  words={n}")
    return out_path


def main() -> None:
    ap = argparse.ArgumentParser(description="Local word-level ASR (faster-whisper)")
    ap.add_argument("video", type=Path)
    ap.add_argument("--edit-dir", type=Path, default=None)
    ap.add_argument("--model", default="large-v3")
    ap.add_argument("--language", default=None, help="ISO code; omit to auto-detect")
    args = ap.parse_args()

    video = args.video.resolve()
    if not video.exists():
        sys.exit(f"video not found: {video}")
    edit_dir = (args.edit_dir or (video.parent / "edit")).resolve()
    transcribe_one(video, edit_dir, args.model, args.language)


if __name__ == "__main__":
    main()
