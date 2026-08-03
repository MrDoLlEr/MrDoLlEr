"""Audio post: voice-over sweetening, music bed, sidechain ducking, limiter."""

from __future__ import annotations

import wave

import numpy as np
from scipy.signal import butter, sosfilt

import music
from config import BUILD, SAMPLE_RATE as SR


def _read_wav(path) -> np.ndarray:
    with wave.open(str(path), "rb") as f:
        n = f.getnframes()
        raw = np.frombuffer(f.readframes(n), dtype=np.int16).astype(np.float32) / 32768.0
        if f.getnchannels() == 2:
            raw = raw.reshape(-1, 2).mean(axis=1)
        assert f.getframerate() == SR, f"expected {SR} Hz, got {f.getframerate()}"
    return raw


def _write_wav(path, stereo: np.ndarray) -> None:
    stereo = np.nan_to_num(stereo, nan=0.0, posinf=0.0, neginf=0.0)
    data = (np.clip(stereo, -1, 1) * 32767).astype(np.int16)
    with wave.open(str(path), "wb") as f:
        f.setnchannels(2)
        f.setsampwidth(2)
        f.setframerate(SR)
        f.writeframes(data.tobytes())


def _sos(kind: str, cutoff, order=2):
    if isinstance(cutoff, (list, tuple)):
        wn = [c / (SR / 2) for c in cutoff]
    else:
        wn = cutoff / (SR / 2)
    return butter(order, wn, btype=kind, output="sos")


def compress(x: np.ndarray, thresh_db=-20.0, ratio=4.0, attack=0.006, release=0.16,
             makeup_db=0.0) -> np.ndarray:
    """Feed-forward compressor with a smoothed level detector."""
    eps = 1e-7
    level = np.abs(x)
    a_a = np.exp(-1.0 / (attack * SR))
    a_r = np.exp(-1.0 / (release * SR))
    env = np.empty_like(level)
    prev = 0.0
    # single-pole detector; vectorising this would need a different topology
    for i in range(0, len(level), 1024):
        chunk = level[i : i + 1024]
        peak = chunk.max() if len(chunk) else 0.0
        coeff = a_a if peak > prev else a_r
        prev = peak + (prev - peak) * coeff
        env[i : i + 1024] = prev
    env_db = 20 * np.log10(env + eps)
    over = np.maximum(0.0, env_db - thresh_db)
    gain_db = -over * (1 - 1 / ratio) + makeup_db
    return (x * 10 ** (gain_db / 20)).astype(np.float32)


def sweeten_vo(vo: np.ndarray) -> np.ndarray:
    """Broadcast-style voice chain: clean the bottom, add presence, control it."""
    x = sosfilt(_sos("high", 95.0, 4), vo).astype(np.float32)
    presence = sosfilt(_sos("band", (2600.0, 6200.0), 2), x).astype(np.float32)
    body = sosfilt(_sos("band", (140.0, 320.0), 2), x).astype(np.float32)
    x = x + presence * 0.34 + body * 0.16
    x = compress(x, thresh_db=-22.0, ratio=3.6, makeup_db=5.0)
    x = compress(x, thresh_db=-10.0, ratio=8.0, attack=0.002, release=0.09, makeup_db=1.0)
    wet = music.reverb(x, 0.9, 0.10, seed=17)
    x = x * 0.90 + wet * 0.10
    peak = np.abs(x).max() or 1.0
    return (x / peak * 0.92).astype(np.float32)


def duck_envelope(vo: np.ndarray, depth_db: float = -9.5, attack=0.05, release=0.34) -> np.ndarray:
    """Gain curve that pulls the music down whenever the voice is present."""
    level = np.abs(sosfilt(_sos("low", 30.0, 2), np.abs(vo))).astype(np.float32)
    level /= max(1e-6, level.max())
    key = np.clip(level * 6.0, 0, 1)

    a_a = np.exp(-1.0 / (attack * SR))
    a_r = np.exp(-1.0 / (release * SR))
    out = np.empty_like(key)
    prev = 0.0
    block = 512
    for i in range(0, len(key), block):
        chunk = key[i : i + block]
        target = chunk.max() if len(chunk) else 0.0
        coeff = a_a if target > prev else a_r
        prev = target + (prev - target) * coeff
        out[i : i + block] = prev
    gain = 10 ** ((depth_db * out) / 20)
    return gain.astype(np.float32)


def limiter(stereo: np.ndarray, ceiling: float = 0.95) -> np.ndarray:
    """Normalise to the ceiling, then soft-clip the last couple of dB."""
    peak = np.abs(stereo).max()
    if peak > 1e-6:
        stereo = stereo * (ceiling / peak)
    return (np.tanh(stereo * 1.12) * 0.96).astype(np.float32)


def build_mix(duration: float, cuts: list[float], sections: dict):
    vo_raw = _read_wav(BUILD / "vo_raw.wav")
    total = int(duration * SR)
    if len(vo_raw) < total:
        vo_raw = np.pad(vo_raw, (0, total - len(vo_raw)))
    vo_raw = vo_raw[:total]

    vo = sweeten_vo(vo_raw)
    bed = music.compose(duration, cuts, sections)
    if len(bed) < total:
        bed = np.pad(bed, ((0, total - len(bed)), (0, 0)))
    bed = bed[:total]

    # Broadband duck, plus a deeper duck of the band the voice lives in, so the
    # bed keeps its weight and sparkle while the words stay legible.
    wide = duck_envelope(vo_raw, depth_db=-11.0)[:, None]
    speech_band = duck_envelope(vo_raw, depth_db=-7.5, release=0.28)[:, None]
    mids = np.stack([sosfilt(_sos("band", (850.0, 5200.0), 2), bed[:, c]) for c in range(2)], 1)
    bed = bed - mids.astype(np.float32) * (1.0 - speech_band)
    mix = bed * wide * 0.56 + np.stack([vo, vo], axis=1) * 1.0

    fade = int(0.5 * SR)
    ramp = np.linspace(0, 1, fade, dtype=np.float32)[:, None]
    mix[:fade] *= ramp
    mix[-fade:] *= ramp[::-1]

    out = limiter(mix)
    _write_wav(BUILD / "mix.wav", out)
    _write_wav(BUILD / "music_only.wav", limiter(bed))
    return BUILD / "mix.wav"
