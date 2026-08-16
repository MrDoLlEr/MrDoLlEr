"""Synthesised score.

An oriental-flavoured electronic bed in D Hijaz at 96 BPM, arranged in sections
that change on the same beats the picture cuts on, plus impacts and whooshes
placed exactly on the cut list the storyboard hands over. Everything is
generated from scratch, so there is no third-party audio to license.
"""

from __future__ import annotations

import numpy as np
from scipy.signal import butter, fftconvolve, sosfilt

from config import SAMPLE_RATE as SR

BPM = 96.0
BEAT = 60.0 / BPM
BAR = BEAT * 4

# D Hijaz: the flat second and augmented third give the Arabic colour.
ROOT = 146.83  # D3
HIJAZ = [0, 1, 4, 5, 7, 8, 10]


def note(degree: int, octave: int = 0) -> float:
    semis = HIJAZ[degree % 7] + 12 * (octave + degree // 7)
    return ROOT * 2 ** (semis / 12)


def _n(seconds: float) -> int:
    return int(seconds * SR)


def env(length: int, a: float, d: float, s: float, r: float, sustain: float = 0.7) -> np.ndarray:
    """Sample-accurate ADSR."""
    e = np.zeros(length, dtype=np.float32)
    ai, di, ri = _n(a), _n(d), _n(r)
    si = max(0, length - ai - di - ri)
    i = 0
    if ai:
        e[i : i + ai] = np.linspace(0, 1, ai, dtype=np.float32)
        i += ai
    if di:
        e[i : i + di] = np.linspace(1, sustain, di, dtype=np.float32)
        i += di
    if si:
        e[i : i + si] = sustain
        i += si
    if ri and i < length:
        e[i:] = np.linspace(sustain, 0, length - i, dtype=np.float32)
    return e


def exp_env(length: int, decay: float, attack: float = 0.002) -> np.ndarray:
    t = np.arange(length, dtype=np.float32) / SR
    a = np.clip(t / max(attack, 1e-4), 0, 1)
    return (a * np.exp(-t / max(decay, 1e-4))).astype(np.float32)


def saw(freq, length: int, phase: float = 0.0) -> np.ndarray:
    t = np.arange(length, dtype=np.float32) / SR
    f = np.full(length, freq, dtype=np.float32) if np.isscalar(freq) else freq
    ph = np.cumsum(f) / SR + phase
    return (2 * (ph % 1.0) - 1).astype(np.float32)


def sine(freq, length: int, phase: float = 0.0) -> np.ndarray:
    f = np.full(length, freq, dtype=np.float32) if np.isscalar(freq) else freq
    ph = np.cumsum(f) / SR + phase
    return np.sin(2 * np.pi * ph).astype(np.float32)


def noise(length: int, seed: int = 0) -> np.ndarray:
    return np.random.default_rng(seed).normal(0, 1, length).astype(np.float32)


def lp(x: np.ndarray, cutoff: float, order: int = 4) -> np.ndarray:
    sos = butter(order, min(cutoff, SR * 0.49) / (SR / 2), btype="low", output="sos")
    return sosfilt(sos, x).astype(np.float32)


def hp(x: np.ndarray, cutoff: float, order: int = 4) -> np.ndarray:
    sos = butter(order, max(20.0, min(cutoff, SR * 0.49)) / (SR / 2), btype="high", output="sos")
    return sosfilt(sos, x).astype(np.float32)


def bp(x: np.ndarray, lo: float, hi: float, order: int = 2) -> np.ndarray:
    sos = butter(order, [max(20, lo) / (SR / 2), min(hi, SR * 0.49) / (SR / 2)],
                 btype="band", output="sos")
    return sosfilt(sos, x).astype(np.float32)


def reverb(x: np.ndarray, seconds: float = 1.6, mix: float = 0.22, seed: int = 5) -> np.ndarray:
    """Convolution reverb against a decaying noise impulse."""
    n = _n(seconds)
    rng = np.random.default_rng(seed)
    ir = rng.normal(0, 1, n).astype(np.float32) * np.exp(-np.arange(n, dtype=np.float32) / (SR * seconds / 4.5))
    ir = lp(ir, 6500)
    ir /= np.abs(ir).sum() / 12
    wet = fftconvolve(x, ir, mode="full")[: len(x)].astype(np.float32)
    return (x * (1 - mix) + wet * mix).astype(np.float32)


# --------------------------------------------------------------------------- #
# instruments
# --------------------------------------------------------------------------- #


def kick(length: int = None) -> np.ndarray:
    n = length or _n(0.45)
    t = np.arange(n, dtype=np.float32) / SR
    f = 118 * np.exp(-t * 34) + 46
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * exp_env(n, 0.20, 0.0008)
    click = lp(noise(n, 4), 4200) * exp_env(n, 0.012, 0.0002) * 0.35
    return np.tanh((body + click) * 1.5).astype(np.float32) * 0.95


def darbuka_dum() -> np.ndarray:
    n = _n(0.30)
    t = np.arange(n, dtype=np.float32) / SR
    f = 190 * np.exp(-t * 26) + 78
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * exp_env(n, 0.10, 0.001)
    skin = bp(noise(n, 9), 220, 1800) * exp_env(n, 0.05, 0.0005) * 0.5
    return ((body + skin) * 0.75).astype(np.float32)


def darbuka_tak() -> np.ndarray:
    n = _n(0.14)
    body = bp(noise(n, 12), 900, 6500) * exp_env(n, 0.028, 0.0004)
    ring = sine(760, n) * exp_env(n, 0.02, 0.0003) * 0.3
    return ((body + ring) * 0.55).astype(np.float32)


def hat(open_: bool = False) -> np.ndarray:
    n = _n(0.22 if open_ else 0.06)
    return (hp(noise(n, 21 if open_ else 22), 8600) *
            exp_env(n, 0.09 if open_ else 0.020, 0.0003) * 0.17).astype(np.float32)


def sub(freq: float, seconds: float) -> np.ndarray:
    n = _n(seconds)
    e = env(n, 0.02, 0.06, 0.0, 0.10, 0.85)
    return (sine(freq, n) * e * 0.85 + sine(freq * 2, n) * e * 0.10).astype(np.float32)


def pluck(freq: float, seconds: float, bright: float = 1.0) -> np.ndarray:
    n = _n(seconds)
    e = exp_env(n, seconds * 0.42, 0.004)
    raw = saw(freq, n) * 0.6 + saw(freq * 1.005, n) * 0.4
    cut = 900 + 4200 * bright
    return (lp(raw * e, cut) * 0.72).astype(np.float32)


def pad(freqs: list[float], seconds: float, level: float = 0.24) -> np.ndarray:
    n = _n(seconds)
    e = env(n, seconds * 0.30, seconds * 0.15, 0.0, seconds * 0.42, 0.8)
    out = np.zeros(n, dtype=np.float32)
    for i, f in enumerate(freqs):
        for det in (-0.006, 0.0, 0.007):
            out += saw(f * (1 + det), n, phase=0.13 * i) * 0.33
    out = lp(out / max(1, len(freqs)), 2600)
    return (out * e * level).astype(np.float32)


def lead(freq: float, seconds: float, level: float = 0.30) -> np.ndarray:
    n = _n(seconds)
    e = env(n, 0.03, 0.10, 0.0, seconds * 0.5, 0.75)
    vib = 1 + 0.006 * np.sin(2 * np.pi * 5.2 * np.arange(n, dtype=np.float32) / SR)
    tone = saw(freq * vib, n) * 0.5 + sine(freq * vib, n) * 0.5
    return (lp(tone, 3200) * e * level).astype(np.float32)


def riser(seconds: float, seed: int = 33) -> np.ndarray:
    n = _n(seconds)
    t = np.linspace(0, 1, n, dtype=np.float32)
    swept = noise(n, seed)
    out = np.zeros(n, dtype=np.float32)
    block = _n(0.05)
    for i in range(0, n, block):
        j = min(n, i + block)
        cut = 260 * (1 + 26 * (i / n) ** 2)
        out[i:j] = bp(swept[max(0, i - 600):j], cut * 0.7, min(cut * 1.6, SR * 0.45))[-(j - i):]
    tone = sine(np.linspace(180, 900, n).astype(np.float32), n) * 0.22
    return ((out * 0.34 + tone * 1.4) * (t ** 2.2) * 0.5).astype(np.float32)


def impact(level: float = 1.0) -> np.ndarray:
    n = _n(2.2)
    t = np.arange(n, dtype=np.float32) / SR
    boom = np.sin(2 * np.pi * np.cumsum(70 * np.exp(-t * 6) + 38) / SR) * exp_env(n, 0.55, 0.001)
    crash = hp(noise(n, 41), 2600) * exp_env(n, 0.85, 0.002) * 0.18
    low = lp(noise(n, 42), 180) * exp_env(n, 0.7, 0.002) * 0.5
    return (np.tanh((boom + crash + low) * 1.2) * 0.55 * level).astype(np.float32)


def whoosh(seconds: float = 0.6, seed: int = 55) -> np.ndarray:
    n = _n(seconds)
    t = np.linspace(0, 1, n, dtype=np.float32)
    src = noise(n, seed)
    out = np.zeros(n, dtype=np.float32)
    block = _n(0.03)
    for i in range(0, n, block):
        j = min(n, i + block)
        u = i / n
        cut = 400 + 5200 * np.sin(u * np.pi) ** 1.4
        out[i:j] = bp(src[max(0, i - 400):j], cut * 0.6, min(cut * 2.2, SR * 0.45))[-(j - i):]
    shape = np.clip(np.sin(t * np.pi), 0.0, None) ** 1.6
    return (out * shape * 0.17).astype(np.float32)


def reverse_cymbal(seconds: float = 1.0, seed: int = 61) -> np.ndarray:
    n = _n(seconds)
    s = hp(noise(n, seed), 3000) * np.linspace(0, 1, n, dtype=np.float32) ** 2.6
    return (s * 0.11).astype(np.float32)


# --------------------------------------------------------------------------- #
# arrangement
# --------------------------------------------------------------------------- #


def _add(track: np.ndarray, sample: np.ndarray, at: float, gain: float = 1.0) -> None:
    i = _n(at)
    if i < 0:
        sample = sample[-i:]
        i = 0
    j = min(len(track), i + len(sample))
    if j > i:
        track[i:j] += sample[: j - i] * gain


def compose(duration: float, cuts: list[float], sections: dict) -> np.ndarray:
    """Build the full bed. `sections` marks where the energy changes."""
    n = _n(duration + 1.0)
    drums = np.zeros(n, dtype=np.float32)
    bass = np.zeros(n, dtype=np.float32)
    harmony = np.zeros(n, dtype=np.float32)
    top = np.zeros(n, dtype=np.float32)
    fxbus = np.zeros(n, dtype=np.float32)

    t_open = sections["open"]
    t_groove = sections["groove"]
    t_full = sections["full"]
    t_peak = sections["peak"]
    t_break = sections["break"]
    t_cta = sections["cta"]

    # ---- chords: i - VI - v - i, one bar each, looping
    chords = [
        [note(0, -1), note(2, -1), note(4, -1)],
        [note(5, -2), note(0, -1), note(2, -1)],
        [note(4, -2), note(6, -2), note(1, -1)],
        [note(0, -1), note(3, -1), note(4, -1)],
    ]

    t = t_open
    ci = 0
    while t < duration:
        level = 0.16 if t < t_groove else (0.30 if t < t_break else 0.24)
        if t >= t_cta:
            level = 0.38
        _add(harmony, pad(chords[ci % 4], BAR * 1.02, level), t)
        ci += 1
        t += BAR

    # ---- sub bass on the root of each bar, with an off-beat push
    t = t_groove - BAR
    ci = 0
    while t < duration:
        root = chords[ci % 4][0] * 0.5
        _add(bass, sub(root, BEAT * 1.6), t, 0.85)
        _add(bass, sub(root, BEAT * 0.6), t + BEAT * 2.5, 0.55)
        _add(bass, sub(root * 1.5, BEAT * 0.5), t + BEAT * 3.5, 0.35)
        ci += 1
        t += BAR

    # ---- percussion
    k, dum, tak, h_c, h_o = kick(), darbuka_dum(), darbuka_tak(), hat(False), hat(True)
    t = t_groove
    step = BEAT / 2
    i = 0
    while t < duration - 0.2:
        energetic = t_full <= t < t_break or t >= t_cta
        beat_in_bar = (i % 8) / 2.0
        if beat_in_bar in (0.0, 2.0):
            _add(drums, k, t, 1.0 if energetic else 0.72)
        if energetic and beat_in_bar in (1.5, 3.5):
            _add(drums, k, t, 0.45)
        if beat_in_bar in (1.0, 3.0):
            _add(drums, dum, t, 0.6 if energetic else 0.4)
        if i % 2 == 1 and (energetic or i % 4 == 1):
            _add(drums, tak, t, 0.5 if energetic else 0.3)
        _add(drums, h_o if i % 8 == 6 else h_c, t, (0.9 if energetic else 0.55))
        if t_break <= t < t_cta:  # sparser under the offline beat
            drums[_n(t) : _n(t + step)] *= 0.55
        i += 1
        t += step

    # ---- hijaz motif
    motif = [0, 1, 0, 4, 3, 2, 1, 0]
    t = t_full
    i = 0
    while t < t_break:
        deg = motif[i % len(motif)]
        _add(top, pluck(note(deg, 1), BEAT * 0.9, 0.85), t, 0.78)
        i += 1
        t += BEAT / 2
    t = t_peak
    i = 0
    while t < t_break:
        _add(top, lead(note(motif[i % len(motif)], 0), BEAT * 1.1, 0.34), t, 1.0)
        i += 1
        t += BEAT

    t = t_cta
    i = 0
    while t < duration - 0.6:
        _add(top, pluck(note(motif[i % len(motif)], 1), BEAT * 0.9, 1.0), t, 0.85)
        _add(top, lead(note(motif[i % len(motif)], 0), BEAT * 1.0, 0.36), t, 1.0)
        i += 1
        t += BEAT / 2

    # ---- transitions: a whoosh into every cut, impacts on the section changes
    marked = {t_open, t_groove, t_full, t_peak, t_break, t_cta}
    for i, c in enumerate(cuts):
        if c in marked or i % 4 == 2:
            _add(fxbus, whoosh(0.55, seed=int(c * 100) % 9999), c - 0.42, 0.8)
    for s, lvl in ((t_open, 0.7), (t_full, 0.9), (t_peak, 0.85), (t_cta, 1.15)):
        _add(fxbus, impact(lvl), s)
    _add(fxbus, riser(1.05), t_open - 1.05, 0.9)
    _add(fxbus, riser(1.6), t_cta - 1.6, 1.0)
    _add(fxbus, reverse_cymbal(1.2), t_full - 1.2, 1.0)
    _add(fxbus, reverse_cymbal(1.4), t_cta - 1.4, 1.0)

    harmony = reverb(harmony, 2.2, 0.30, 7)
    top = reverb(top, 1.5, 0.26, 8)
    fxbus = reverb(fxbus, 1.5, 0.16, 9)
    drums = reverb(drums, 0.7, 0.10, 10)

    mono = (drums * 0.82 + bass * 1.05 + harmony * 1.15 + top * 1.05 + fxbus * 0.62)
    mono = np.tanh(mono * 1.05) * 0.9
    mono = np.nan_to_num(mono, nan=0.0, posinf=0.0, neginf=0.0)

    # gentle stereo width: delay and tilt the non-percussive buses
    d = _n(0.010)
    wide = np.concatenate([np.zeros(d, dtype=np.float32), (harmony + top)[:-d]])
    left = mono + wide * 0.16
    right = mono - wide * 0.16
    stereo = np.stack([left, right], axis=1)
    stereo /= max(1e-6, np.abs(stereo).max()) / 0.92
    return stereo[: _n(duration)].astype(np.float32)
