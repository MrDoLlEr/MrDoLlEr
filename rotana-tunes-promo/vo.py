"""Synthesise the Arabic voice-over and recover word-level timings from it.

The voice model exports no alignment tensor, so boundaries are estimated from
the phoneme string (espeak keeps a space between words, which gives an exact
phoneme-count per word) and then snapped onto the quietest point of the audio
inside a small search window. That lands captions on the word being spoken
without hand-tuning a single frame.
"""

from __future__ import annotations

import json
import wave

import numpy as np
from piper import PiperVoice
from piper.config import SynthesisConfig

from config import BUILD, SAMPLE_RATE, VOICE_MODEL
from script_data import VO_LINES

# Slightly faster than default: an ad read, not an audiobook.
LENGTH_SCALE = 0.94

# Relative duration of a phoneme when spreading a line's audio over its words.
STRESS_MARKS = {"ˈ", "ˌ", "ˑ"}
PAUSE_MARKS = {",", ".", "،", "؛", ":", "!", "?", "؟"}
VOWELS = set("aeiouɑɐɒæɛɜɪɔʊʌyøœɯɤə")


def _phoneme_weight(ph: str, prev: str) -> float:
    if ph in STRESS_MARKS:
        return 0.0
    if ph == "ː":
        return 0.75
    if ph in PAUSE_MARKS:
        return 2.2
    if ph in VOWELS:
        return 1.15
    return 1.0


def _word_weights(phonemes: list[str]) -> list[float]:
    """Total phonetic weight of every space-separated phoneme group."""
    groups, current = [], []
    for ph in phonemes:
        if ph == " ":
            groups.append(current)
            current = []
        else:
            current.append(ph)
    groups.append(current)

    weights = []
    for g in groups:
        total, prev = 0.0, ""
        for ph in g:
            total += _phoneme_weight(ph, prev)
            prev = ph
        weights.append(max(total, 0.6))
    return weights


def _envelope(audio: np.ndarray, sr: int, hop: int = 128) -> tuple[np.ndarray, int]:
    """Smoothed short-time energy, used to find the gaps between words."""
    win = hop * 4
    padded = np.pad(np.abs(audio), (win // 2, win // 2))
    kernel = np.hanning(win)
    kernel /= kernel.sum()
    smooth = np.convolve(padded, kernel, mode="same")[win // 2 : win // 2 + len(audio)]
    return smooth[::hop], hop


def _trim_bounds(env: np.ndarray, hop: int, sr: int) -> tuple[int, int]:
    peak = env.max()
    thresh = peak * 0.035
    above = np.where(env > thresh)[0]
    if len(above) == 0:
        return 0, len(env) * hop
    pad = int(0.012 * sr / hop)
    lo = max(0, above[0] - pad)
    hi = min(len(env) - 1, above[-1] + pad)
    return lo * hop, hi * hop


def _snap(boundary: int, env: np.ndarray, hop: int, sr: int, window_s: float = 0.075) -> int:
    """Move a boundary to the quietest frame within +/- window_s."""
    w = max(1, int(window_s * sr / hop))
    c = boundary // hop
    lo, hi = max(0, c - w), min(len(env), c + w + 1)
    if hi <= lo:
        return boundary
    return int((lo + int(np.argmin(env[lo:hi]))) * hop)


def synthesize() -> dict:
    voice = PiperVoice.load(str(VOICE_MODEL))
    syn = SynthesisConfig(length_scale=LENGTH_SCALE, noise_scale=0.62, noise_w_scale=0.75)

    track: list[np.ndarray] = []
    lines_out = []
    cursor = 0.0
    lead_in = 1.15
    track.append(np.zeros(int(lead_in * SAMPLE_RATE), dtype=np.float32))
    cursor += lead_in

    for spec in VO_LINES:
        chunks = list(voice.synthesize(spec["vo"], syn_config=syn))
        sr = chunks[0].sample_rate
        audio = np.concatenate([c.audio_float_array for c in chunks]).astype(np.float32)
        phonemes: list[str] = []
        for i, c in enumerate(chunks):
            if i:
                phonemes.append(" ")
            phonemes.extend(c.phonemes)

        env, hop = _envelope(audio, sr)
        start, end = _trim_bounds(env, hop, sr)
        audio = audio[start:end]
        env, hop = _envelope(audio, sr)

        words = spec["vo"].split()
        weights = _word_weights(phonemes)
        if len(weights) != len(words):  # espeak split differently; fall back to length
            weights = [max(len(w), 2) for w in words]

        total = sum(weights)
        span = len(audio) / sr
        bounds, acc = [0.0], 0.0
        for w in weights[:-1]:
            acc += w
            raw = int(acc / total * len(audio))
            bounds.append(_snap(raw, env, hop, sr) / sr)
        bounds.append(span)
        bounds = list(np.maximum.accumulate(bounds))

        if sr != SAMPLE_RATE:
            n = int(round(len(audio) * SAMPLE_RATE / sr))
            audio = np.interp(
                np.linspace(0, len(audio) - 1, n), np.arange(len(audio)), audio
            ).astype(np.float32)

        line_start = cursor
        track.append(audio)
        cursor += len(audio) / SAMPLE_RATE
        pause = float(spec["pause"])
        track.append(np.zeros(int(pause * SAMPLE_RATE), dtype=np.float32))
        cursor += pause

        lines_out.append(
            {
                "id": spec["id"],
                "text": spec["vo"],
                "start": round(line_start, 4),
                "end": round(line_start + span, 4),
                "pause_end": round(cursor, 4),
                "words": [
                    {
                        "text": words[i],
                        "start": round(line_start + bounds[i], 4),
                        "end": round(line_start + bounds[i + 1], 4),
                    }
                    for i in range(len(words))
                ],
            }
        )

    full = np.concatenate(track)
    peak = float(np.abs(full).max()) or 1.0
    full = full / peak * 0.89

    path = BUILD / "vo_raw.wav"
    with wave.open(str(path), "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(SAMPLE_RATE)
        f.writeframes((full * 32767).astype(np.int16).tobytes())

    timing = {"duration": round(len(full) / SAMPLE_RATE, 4), "lines": lines_out}
    (BUILD / "vo_timing.json").write_text(
        json.dumps(timing, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return timing


if __name__ == "__main__":
    t = synthesize()
    print(f"voice-over: {t['duration']:.2f}s")
    for line in t["lines"]:
        print(f"  [{line['start']:6.2f} -> {line['end']:6.2f}] {line['id']}")
        print("    " + "  ".join(f"{w['text']}@{w['start']:.2f}" for w in line["words"]))
