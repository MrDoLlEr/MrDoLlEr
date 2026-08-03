"""The edit itself: shots, camera moves, transitions and on-screen type.

Every cut time is read out of `build/vo_timing.json`, so the picture is cut to
the voice-over rather than to a guessed rhythm. `SHOTS` is built at import time
and also exposes `cut_times()` for the music bed to hit.
"""

from __future__ import annotations

import json
import math
import random
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Callable

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

import artext
import fx
import ui
from config import (
    BUILD,
    CRIMSON,
    FONT_BODY,
    FONT_DISPLAY,
    FPS,
    GOLD,
    GOLD_BRIGHT,
    H,
    PLATES,
    W,
    WHITE,
)
from script_data import CTA_SUB, VO_LINES

TIMING = json.loads((BUILD / "vo_timing.json").read_text(encoding="utf-8"))
LINES = {l["id"]: l for l in TIMING["lines"]}


def word_t(line_id: str, index: int) -> float:
    return LINES[line_id]["words"][index]["start"]


def line_end(line_id: str) -> float:
    return LINES[line_id]["end"]


# --------------------------------------------------------------------------- #
# plates
# --------------------------------------------------------------------------- #


@lru_cache(maxsize=24)
def plate(name: str) -> Image.Image:
    return Image.open(PLATES / name).convert("RGB")


def shake(t: float, amp: float, seed: float = 0.0) -> tuple[float, float]:
    """Low-frequency handheld drift so no shot ever sits perfectly still."""
    x = math.sin(t * 2.1 + seed) * 0.62 + math.sin(t * 3.77 + seed * 2.3) * 0.38
    y = math.sin(t * 1.63 + seed * 3.1) * 0.58 + math.sin(t * 4.31 + seed * 1.7) * 0.42
    return x * amp, y * amp


# --------------------------------------------------------------------------- #
# shot model
# --------------------------------------------------------------------------- #

Renderer = Callable[[float], np.ndarray]


@dataclass
class Shot:
    name: str
    start: float
    dur: float
    fn: Renderer
    trans: str = "cut"        # how this shot enters
    trans_dur: float = 0.0
    exposure_pop: float = 0.0  # brief exposure lift on entry

    @property
    def end(self) -> float:
        return self.start + self.dur


def plate_shot(
    name: str,
    dur: float,
    z: tuple[float, float] = (1.06, 1.14),
    pan: tuple[tuple[float, float], tuple[float, float]] = ((0, 0), (0, 0)),
    rot: tuple[float, float] = (0.0, 0.0),
    ease=fx.ease_io,
    handheld: float = 3.2,
    seed: float = 0.0,
    ev: float = 0.0,
    overlay: Callable[[float, np.ndarray], np.ndarray] | None = None,
) -> Renderer:
    """A still plate given a virtual camera move, with real motion blur."""
    src = plate(name)

    def params(tl: float) -> dict:
        u = ease(max(0.0, min(1.0, tl / max(dur, 1e-3))))
        sx, sy = shake(tl, handheld, seed)
        return {
            "zoom": z[0] + (z[1] - z[0]) * u,
            "dx": pan[0][0] + (pan[1][0] - pan[0][0]) * u + sx,
            "dy": pan[0][1] + (pan[1][1] - pan[0][1]) * u + sy,
            "rot": rot[0] + (rot[1] - rot[0]) * u,
        }

    def fn(tl: float) -> np.ndarray:
        p1 = params(tl)
        p0 = params(max(0.0, tl - 1.0 / FPS))
        move = abs(p1["dx"] - p0["dx"]) + abs(p1["dy"] - p0["dy"]) + abs(p1["zoom"] - p0["zoom"]) * W
        if move > 6:
            steps = 3 if move < 26 else 5
            seq = [params(tl - (1 - i / (steps - 1)) / FPS) for i in range(steps)]
            img = fx.camera_blurred(src, seq)
        else:
            img = fx.camera(src, **p1)
        arr = fx.np_of(img)
        if ev:
            arr = fx.exposure(arr, ev)
        if overlay is not None:
            arr = overlay(tl, arr)
        return arr

    return fn


# --------------------------------------------------------------------------- #
# reusable overlay elements
# --------------------------------------------------------------------------- #


@lru_cache(maxsize=2)
def _cover_columns() -> list[Image.Image]:
    """Three tall strips of album art, scrolled at different speeds."""
    names = [
        "bg_01_stage.png", "bg_03_listener.png", "bg_07_oud.png", "bg_08_studio.png",
        "bg_09_crowd.png", "bg_06_car.png", "bg_10_headphones.png", "bg_02_waves.png",
    ]
    tile = 300
    gap = 26
    cols = []
    rng = random.Random(11)
    for c in range(3):
        order = names[:]
        rng.shuffle(order)
        strip = Image.new("RGBA", (tile, (tile + gap) * len(order)), (0, 0, 0, 0))
        for i, n in enumerate(order):
            strip.alpha_composite(ui._cover(n, tile, 0.085), (0, i * (tile + gap)))
        cols.append(strip)
    return cols


def cover_wall(t: float, arr: np.ndarray, intro: float = 0.0) -> np.ndarray:
    """Parallax wall of album art, tilted back in perspective."""
    cols = _cover_columns()
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    speeds = (180, -240, 205)
    xs = (-40, 350, 740)
    for strip, sp, x in zip(cols, speeds, xs):
        loop = strip.height // 2
        off = int((t * sp) % loop)
        canvas.alpha_composite(strip, (x, -off))
        canvas.alpha_composite(strip, (x, -off + loop))
    canvas = canvas.rotate(-6, resample=Image.BICUBIC, center=(W // 2, H // 2))
    layer = np.asarray(canvas, dtype=np.float32) / 255.0
    rgb, alpha = layer[..., :3], layer[..., 3:4]
    fade = np.clip(intro, 0, 1)
    y = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
    edge = np.clip(np.minimum(y / 0.22, (1 - y) / 0.22), 0, 1)
    a = alpha * fade * edge * 0.97
    out = arr * (1 - a) + rgb * a
    return out


@lru_cache(maxsize=1)
def _particle_field() -> np.ndarray:
    rng = np.random.default_rng(3)
    return np.stack(
        [rng.uniform(0, 1, 90), rng.uniform(0, 1, 90), rng.uniform(0.4, 1.6, 90),
         rng.uniform(0, 6.28, 90)], axis=1
    ).astype(np.float32)


def dust(t: float, arr: np.ndarray, strength: float = 0.55) -> np.ndarray:
    """Slow gold motes, screened over the frame."""
    p = _particle_field()
    layer = Image.new("L", (W // 2, H // 2), 0)
    d = ImageDraw.Draw(layer)
    for x0, y0, sp, ph in p:
        x = (x0 + 0.02 * math.sin(t * 0.5 * sp + ph)) * (W // 2)
        y = ((y0 - t * 0.012 * sp) % 1.0) * (H // 2)
        r = 1.0 + 1.8 * sp
        v = int(120 + 110 * (0.5 + 0.5 * math.sin(t * 2.2 * sp + ph)))
        d.ellipse((x - r, y - r, x + r, y + r), fill=v)
    layer = layer.filter(ImageFilter.GaussianBlur(1.6)).resize((W, H), Image.BILINEAR)
    m = (np.asarray(layer, dtype=np.float32) / 255.0)[..., None] * strength
    tint = np.array([1.0, 0.84, 0.55], dtype=np.float32)
    return fx.screen(arr, m * tint)


def eq_bar_overlay(t: float, arr: np.ndarray, gain: float = 1.0, opacity: float = 0.85) -> np.ndarray:
    """Full-width spectrum across the bottom of the frame."""
    bars = 46
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    bw = W * 0.86 / (bars * 1.6)
    x = W * 0.07
    base_y = H * 0.90
    for i in range(bars):
        a = math.sin(t * 6.2 + i * 0.72) * 0.5 + 0.5
        b = math.sin(t * 3.1 + i * 0.27) * 0.5 + 0.5
        amp = (0.16 + 0.84 * (a * 0.6 + b * 0.4)) * (0.45 + 0.55 * math.sin(i / bars * math.pi))
        bh = max(6, amp * H * 0.085 * gain)
        u = i / bars
        col = tuple(int(CRIMSON[j] + (GOLD_BRIGHT[j] - CRIMSON[j]) * u) for j in range(3))
        d.rounded_rectangle((x, base_y - bh, x + bw, base_y), radius=bw / 2, fill=col + (235,))
        x += bw * 1.6
    glow = layer.filter(ImageFilter.GaussianBlur(16))
    out = fx.composite(arr, glow, opacity * 0.75, blend="screen")
    return fx.composite(out, layer, opacity, blend="screen")


def scanline_sweep(t: float, arr: np.ndarray, speed: float = 0.55) -> np.ndarray:
    """A soft band of light travelling down the frame."""
    y = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
    pos = (t * speed) % 1.4 - 0.2
    band = np.exp(-((y - pos) ** 2) / 0.0016).astype(np.float32)
    return fx.screen(arr, band * np.array([0.55, 0.42, 0.30], dtype=np.float32))


# --------------------------------------------------------------------------- #
# phone shots
# --------------------------------------------------------------------------- #

SCREEN = (620, 1342)


@lru_cache(maxsize=1)
def _phone_plate() -> tuple[Image.Image, tuple[int, int, int, int]]:
    """Background plate for the phone shots plus the on-screen rectangle."""
    src = plate("bg_11_phone_hand.png")
    return src, (0, 0, 0, 0)


def phone_shot(
    dur: float,
    screen_fn: Callable[[float], Image.Image],
    z: tuple[float, float] = (1.02, 1.10),
    pan: tuple[tuple[float, float], tuple[float, float]] = ((0, 0), (0, 0)),
    rot: tuple[float, float] = (0.0, 0.0),
    entry: float = 0.0,
    seed: float = 5.0,
) -> Renderer:
    """The rendered app UI, composited into the real phone-in-hand plate.

    The plate was shot dead-on with a blank screen, so a plain scale-and-place
    is enough; no corner-pinning needed.
    """
    src = plate("bg_11_phone_hand.png")
    # Screen rectangle measured on the 1024x1536 plate.
    SX0, SY0, SX1, SY1 = 296, 172, 743, 1188

    def fn(tl: float) -> np.ndarray:
        u = fx.ease_io(max(0.0, min(1.0, tl / max(dur, 1e-3))))
        sx, sy = shake(tl, 2.4, seed)
        cam = {
            "zoom": z[0] + (z[1] - z[0]) * u,
            "dx": pan[0][0] + (pan[1][0] - pan[0][0]) * u + sx,
            "dy": pan[0][1] + (pan[1][1] - pan[0][1]) * u + sy,
            "rot": rot[0] + (rot[1] - rot[0]) * u,
        }

        composited = src.copy()
        screen = screen_fn(tl).resize((SX1 - SX0, SY1 - SY0), Image.LANCZOS)
        mask = Image.new("L", screen.size, 0)
        ImageDraw.Draw(mask).rounded_rectangle(
            (0, 0, screen.width - 1, screen.height - 1), radius=34, fill=255
        )
        if entry > 0:
            k = fx.clamp01(tl / entry)
            mask = mask.point(lambda v, k=k: int(v * k))
            screen = Image.blend(Image.new("RGB", screen.size, (0, 0, 0)), screen, 0.25 + 0.75 * k)
        composited.paste(screen, (SX0, SY0), mask)

        glass = Image.new("RGBA", composited.size, (0, 0, 0, 0))
        gd = ImageDraw.Draw(glass)
        gd.polygon(
            [(SX0 + 40, SY0), (SX0 + 250, SY0), (SX0 + 60, SY1), (SX0, SY1 - 260)],
            fill=(255, 255, 255, 16),
        )
        composited = Image.alpha_composite(composited.convert("RGBA"), glass).convert("RGB")

        arr = fx.np_of(fx.camera(composited, **cam))
        return arr

    return fn


# --------------------------------------------------------------------------- #
# titles
# --------------------------------------------------------------------------- #


@lru_cache(maxsize=64)
def _caption_line(words: tuple[str, ...], size: int, stroke: int):
    f = artext.font(FONT_DISPLAY, size)
    return artext.layout_line(list(words), f, WHITE + (255,), stroke=stroke,
                              stroke_fill=(0, 0, 0, 190))


def draw_caption(
    arr: np.ndarray,
    words: tuple[str, ...],
    t_since: float,
    size: int = 96,
    cy: float = H * 0.735,
    accent_last: bool = False,
    hold: float = 10.0,
) -> np.ndarray:
    """Word-by-word kinetic type: each word springs up with a gold underline."""
    line = _caption_line(words, size, 0)
    if t_since < -0.05 or t_since > hold + 0.26:
        return arr

    out_u = fx.clamp01((t_since - hold) / 0.24)
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    x0 = (W - line.width) / 2

    for i, wd in enumerate(line.words):
        tw = t_since - i * 0.085
        if tw < 0:
            continue
        u = fx.overshoot(fx.clamp01(tw / 0.42), 1.6)
        rise = (1 - u) * size * 0.55
        op = fx.clamp01(tw / 0.16) * (1 - out_u)
        scale = 0.86 + 0.14 * u
        colour = GOLD_BRIGHT if (accent_last and i == len(line.words) - 1) else WHITE
        lay = artext.text_layer(
            wd.text, artext.font(FONT_DISPLAY, size), colour + (255,), pad=30,
            stroke=0,
        )
        cx = x0 + wd.x + lay.width / 2
        cyy = cy + rise + out_u * -size * 0.3
        shadow = artext.glow(lay, 26, 0.85, tint=(0, 0, 0))
        canvas.alpha_composite(fx.place((W, H), shadow, cx, cyy + 6, scale, 0, op * 0.9))
        if colour is GOLD_BRIGHT:
            canvas.alpha_composite(
                fx.place((W, H), artext.glow(lay, 22, 0.8, tint=GOLD), cx, cyy, scale, 0, op * 0.85)
            )
        canvas.alpha_composite(fx.place((W, H), lay, cx, cyy, scale, 0, op))

    # gold rule that wipes in under the line
    ru = fx.ease_out(fx.clamp01((t_since - 0.12) / 0.5))
    if ru > 0.01:
        rule = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        rd = ImageDraw.Draw(rule)
        half = line.width * 0.5 * ru
        yy = cy + size * 0.72
        rd.rounded_rectangle((W / 2 - half, yy, W / 2 + half, yy + 6), radius=3,
                             fill=GOLD + (int(220 * (1 - out_u)),))
        canvas.alpha_composite(rule)

    return fx.composite(arr, canvas, 1.0)


def logo_bug(arr: np.ndarray, opacity: float) -> np.ndarray:
    """Small corner lockup that rides the middle of the film."""
    if opacity <= 0.01:
        return arr
    icon = ui.app_icon(76)
    mark = ui.wordmark(38, latin=False)
    pad = 44
    canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    canvas.alpha_composite(icon, (W - pad - icon.width, pad + 8))
    canvas.alpha_composite(mark, (W - pad - icon.width - mark.width - 6, pad + 20))
    return fx.composite(arr, canvas, opacity * 0.92)


# --------------------------------------------------------------------------- #
# bespoke shots
# --------------------------------------------------------------------------- #


def cold_open(dur: float) -> Renderer:
    """Black frame, a single line of light that snaps open into the film."""
    src = plate("bg_02_waves.png")

    def fn(tl: float) -> np.ndarray:
        u = fx.clamp01(tl / dur)
        arr = fx.np_of(fx.camera(src, zoom=1.34 - 0.10 * u, dx=0, dy=0, rot=-1.5 + u))
        arr = fx.exposure(arr, -1.9 + 2.2 * fx.ease_in(u, 2.2))
        y = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
        slit = np.exp(-((y - 0.5) ** 2) / (0.00035 + 0.06 * fx.ease_out(u, 2.0)))
        arr = arr * (0.18 + 0.82 * slit)
        arr = fx.screen(arr, slit.astype(np.float32) * np.array([0.9, 0.5, 0.28], np.float32)
                        * (1 - fx.ease_out(u, 1.6)))
        return arr

    return fn


def logo_reveal(dur: float) -> Renderer:
    """Icon slams in over the empty stage, wordmark wipes out from behind it."""
    src = plate("bg_04_pedestal.png")
    icon_px = 420

    def fn(tl: float) -> np.ndarray:
        u = fx.clamp01(tl / dur)
        arr = fx.np_of(fx.camera(src, zoom=1.20 - 0.10 * fx.ease_io(u), dy=60 - 80 * u, rot=0.6 - 1.0 * u))
        arr = fx.exposure(arr, -0.25 + 0.25 * u)

        s = fx.spring(fx.clamp01(tl / 0.62), freq=1.6, decay=7.0)
        icon = ui.app_icon(icon_px)
        scale = 1.9 - 0.9 * s
        op = fx.clamp01(tl / 0.14)
        cy = H * 0.44
        canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        halo = artext.glow(icon, 60, 1.5, tint=CRIMSON)
        canvas.alpha_composite(fx.place((W, H), halo, W / 2, cy, scale * 1.15, 0, op * 0.8))
        canvas.alpha_composite(fx.place((W, H), icon, W / 2, cy, scale, 0, op))
        arr = fx.composite(arr, canvas, 1.0)

        # impact flash and ring on the landing frame
        arr = fx.flash(arr, max(0.0, 0.55 - abs(tl - 0.30) * 3.4), (1.0, 0.86, 0.72))
        ring_u = fx.clamp01((tl - 0.26) / 0.55)
        if 0 < ring_u < 1:
            ring = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            r = 120 + 620 * fx.ease_out(ring_u, 2.4)
            ImageDraw.Draw(ring).ellipse(
                (W / 2 - r, cy - r, W / 2 + r, cy + r),
                outline=GOLD + (int(200 * (1 - ring_u) ** 1.4),), width=max(1, int(9 * (1 - ring_u))),
            )
            arr = fx.composite(arr, ring.filter(ImageFilter.GaussianBlur(3)), 1.0, blend="screen")

        wu = fx.ease_out(fx.clamp01((tl - 0.46) / 0.6), 2.6)
        if wu > 0.01:
            mark = ui.wordmark(112)
            reveal = mark.crop((int(mark.width * (1 - wu)), 0, mark.width, mark.height))
            lay = Image.new("RGBA", mark.size, (0, 0, 0, 0))
            lay.alpha_composite(reveal, (int(mark.width * (1 - wu)), 0))
            arr = fx.composite(
                arr, fx.place((W, H), lay, W / 2, cy + icon_px * 0.72, 1.0, 0, 1.0), 1.0
            )
        arr = dust(tl, arr, 0.5)
        return arr

    return fn


@lru_cache(maxsize=1)
def _cta_scrim() -> np.ndarray:
    """Soft dark oval so the crimson lockup keeps contrast against the plate."""
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.sqrt(((x - W / 2) / (W * 0.62)) ** 2 + ((y - H * 0.46) / (H * 0.42)) ** 2)
    return (0.34 + 0.66 * np.clip(r, 0, 1) ** 1.1)[..., None].astype(np.float32) * 0.0 + (
        1 - 0.55 * np.exp(-(r ** 2) * 1.5)
    )[..., None].astype(np.float32)


def end_card(dur: float) -> Renderer:
    """Locked-off end card: lockup, headline, badges, gold sweep."""
    src = plate("bg_05_cta.png")

    def fn(tl: float) -> np.ndarray:
        u = fx.clamp01(tl / dur)
        arr = fx.np_of(fx.camera(src, zoom=1.16 - 0.07 * fx.ease_io(u), rot=-0.4 + 0.8 * u))
        arr = fx.exposure(arr, -0.55)
        arr = arr * 0.66 + np.array([0.02, 0.008, 0.012], dtype=np.float32) * 0.34
        arr = arr * _cta_scrim()

        canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        s = fx.spring(fx.clamp01(tl / 0.75), 1.5, 6.5)
        lock = ui.logo_lockup(282)
        canvas.alpha_composite(
            fx.place((W, H), artext.glow(lock, 46, 0.9, tint=CRIMSON), W / 2, H * 0.335,
                     0.9 + 0.1 * s, 0, fx.clamp01(tl / 0.25) * 0.8)
        )
        canvas.alpha_composite(
            fx.place((W, H), lock, W / 2, H * 0.335, 0.9 + 0.1 * s, 0, fx.clamp01(tl / 0.2))
        )

        bu = fx.ease_out(fx.clamp01((tl - 2.45) / 0.6), 2.6)
        if bu > 0.01:
            b1 = ui.store_badge("Download on the", "App Store", 372)
            b2 = ui.store_badge("GET IT ON", "Google Play", 372)
            gap = 36
            total = b1.width + b2.width + gap
            y = H * 0.762 + (1 - bu) * 60
            canvas.alpha_composite(
                fx.place((W, H), b1, W / 2 - total / 2 + b1.width / 2, y, 1.0, 0, bu)
            )
            canvas.alpha_composite(
                fx.place((W, H), b2, W / 2 + total / 2 - b2.width / 2, y, 1.0, 0, bu)
            )
            sub = artext.text_layer(CTA_SUB, artext.font(FONT_BODY, 38), (205, 198, 208, 255))
            canvas.alpha_composite(fx.place((W, H), sub, W / 2, H * 0.836, 1.0, 0, bu * 0.92))

        arr = fx.composite(arr, canvas, 1.0)

        # gold sweep across the lockup
        sw = (tl - 1.0) / 1.15
        if 0 < sw < 1:
            x = np.linspace(0, 1, W, dtype=np.float32)[None, :, None]
            y = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
            band = np.exp(-((x - y * 0.45 - (sw * 1.7 - 0.35)) ** 2) / 0.0022)
            arr = fx.screen(arr, band * np.array([0.55, 0.44, 0.24], np.float32) * 0.9)

        arr = dust(tl, arr, 0.75)
        return arr

    return fn


def bass_pulse(t: float, arr: np.ndarray, bpm: float, strength: float = 0.05) -> np.ndarray:
    """Frame-wide breathing locked to the music tempo."""
    beat = t * bpm / 60.0
    p = (beat % 1.0)
    k = math.exp(-p * 5.5)
    if k < 0.02:
        return arr
    z = 1 + strength * k
    img = Image.fromarray((np.clip(arr, 0, 1) * 255).astype(np.uint8), "RGB")
    zw, zh = int(W * z), int(H * z)
    z_img = img.resize((zw, zh), Image.BILINEAR)
    ox, oy = (zw - W) // 2, (zh - H) // 2
    out = np.asarray(z_img.crop((ox, oy, ox + W, oy + H)), dtype=np.float32) / 255.0
    return np.clip(out * (1 + 0.05 * k), 0, 1)


BPM = 96.0

# --------------------------------------------------------------------------- #
# the edit
# --------------------------------------------------------------------------- #


def _library_screen(tl: float) -> Image.Image:
    hi = 1.0 if tl < 0.9 else (2.0 if tl < 1.8 else 3.0)
    return ui.screen_library(SCREEN, hi)


def _now_playing(tl: float, progress0: float = 0.18) -> Image.Image:
    return ui.now_playing_frame(SCREEN, eq_phase=tl * 3.1, progress=progress0 + tl * 0.055)


def build_shots() -> list[Shot]:
    t_hook = LINES["hook"]["words"]
    t_brand = LINES["brand"]["words"]
    t_lib = LINES["library"]["words"]
    t_taste = LINES["taste"]["words"]
    t_off = LINES["offline"]["words"]
    t_cta = LINES["cta"]["words"]

    marks = [
        0.0,
        t_hook[0]["start"],
        t_hook[3]["start"],
        t_hook[5]["start"],
        t_brand[0]["start"],
        t_brand[2]["start"],
        t_brand[5]["start"],
        t_lib[0]["start"],
        t_lib[2]["start"],
        t_lib[5]["start"],
        t_taste[0]["start"],
        t_taste[2]["start"],
        t_taste[4]["start"],
        t_taste[7]["start"],
        t_off[0]["start"],
        t_off[3]["start"],
        t_off[5]["start"],
        t_cta[0]["start"],
        TIMING["duration"],
    ]
    d = [marks[i + 1] - marks[i] for i in range(len(marks) - 1)]

    spec = [
        ("cold_open", cold_open(d[0]), "cut", 0.0),
        ("listener", plate_shot("bg_03_listener.png", d[1], z=(1.20, 1.05),
                                pan=((30, 40), (-10, -10)), rot=(1.1, -0.2), seed=1.0,
                                ev=-0.12), "dissolve", 0.42),
        ("headphones", plate_shot("bg_10_headphones.png", d[2], z=(1.28, 1.10),
                                  pan=((-60, 30), (40, -20)), rot=(-1.6, 0.6), seed=2.0),
         "whip", 0.24),
        ("waves", plate_shot("bg_02_waves.png", d[3], z=(1.04, 1.24),
                             rot=(0.4, -1.2), seed=3.0,
                             overlay=lambda tl, a: scanline_sweep(tl, a, 0.7)), "flash", 0.16),
        ("logo", logo_reveal(d[4]), "zoomblur", 0.34),
        ("stage", plate_shot("bg_01_stage.png", d[5], z=(1.06, 1.22),
                             pan=((0, 60), (0, -40)), rot=(-0.5, 0.5), seed=4.0), "flash", 0.14),
        ("crowd", plate_shot("bg_09_crowd.png", d[6], z=(1.24, 1.06),
                             pan=((-40, -50), (30, 30)), rot=(1.4, -0.4), seed=6.0), "whip", 0.22),
        ("wall", plate_shot("bg_04_pedestal.png", d[7], z=(1.10, 1.20), seed=7.0, ev=-0.6,
                            overlay=lambda tl, a: dust(tl, cover_wall(tl, a, tl / 0.35), 0.4)),
         "glitch", 0.22),
        ("oud", plate_shot("bg_07_oud.png", d[8], z=(1.22, 1.06), pan=((50, -30), (-30, 20)),
                           rot=(0.9, -0.6), seed=8.0, ev=0.05,
                           overlay=lambda tl, a: dust(tl, a, 0.6)), "dissolve", 0.34),
        ("studio", plate_shot("bg_08_studio.png", d[9], z=(1.05, 1.22),
                              pan=((-20, 30), (20, -30)), rot=(-1.0, 0.4), seed=9.0),
         "glitch", 0.24),
        ("phone_lib", phone_shot(d[10], _library_screen, z=(1.34, 1.12),
                                 pan=((80, 120), (0, 10)), rot=(-3.2, 0.2), entry=0.42),
         "zoomblur", 0.32),
        ("phone_lib2", phone_shot(d[11], lambda tl: _library_screen(tl + 1.0), z=(1.12, 1.46),
                                  pan=((0, 10), (-30, -120)), rot=(0.2, 1.1), seed=11.0),
         "push", 0.28),
        ("crowd2", plate_shot("bg_09_crowd.png", d[12], z=(1.30, 1.10),
                              pan=((60, 60), (-40, -30)), rot=(-1.8, 0.8), seed=12.0,
                              overlay=lambda tl, a: eq_bar_overlay(tl, a, 1.0, 0.8)),
         "whip", 0.24),
        ("stage2", plate_shot("bg_01_stage.png", d[13], z=(1.30, 1.08), pan=((0, -60), (0, 40)),
                              rot=(0.8, -0.3), seed=13.0, ev=0.08), "flash", 0.16),
        ("phone_play", phone_shot(d[14], _now_playing, z=(1.40, 1.14),
                                  pan=((-90, -60), (10, 20)), rot=(3.0, -0.3), entry=0.40,
                                  seed=14.0), "zoomblur", 0.30),
        ("car", plate_shot("bg_06_car.png", d[15], z=(1.08, 1.26), pan=((0, 20), (0, -30)),
                           rot=(-0.7, 0.9), seed=15.0, ev=0.12), "whip", 0.24),
        ("headphones2", plate_shot("bg_10_headphones.png", d[16], z=(1.24, 1.08),
                                   pan=((40, -40), (-40, 30)), rot=(1.2, -0.5), seed=16.0,
                                   overlay=lambda tl, a: dust(tl, a, 0.5)), "dissolve", 0.30),
        ("end_card", end_card(d[17]), "leak", 0.44),
    ]

    shots, cursor = [], 0.0
    for i, (name, fn, trans, tdur) in enumerate(spec):
        shots.append(Shot(name, marks[i], d[i], fn, trans, tdur))
        cursor = marks[i + 1]
    return shots


SHOTS = build_shots()


def cut_times() -> list[float]:
    """Cut points, for the music bed to place impacts and whooshes on."""
    return [s.start for s in SHOTS[1:]]


# --------------------------------------------------------------------------- #
# transitions
# --------------------------------------------------------------------------- #


def blend(kind: str, u: float, prev: np.ndarray, nxt: np.ndarray, seed: int) -> np.ndarray:
    u = fx.clamp01(u)
    if kind == "dissolve":
        k = fx.ease_io(u)
        out = prev * (1 - k) + nxt * k
        return fx.flash(out, math.sin(u * math.pi) * 0.10)

    if kind == "flash":
        k = 1.0 if u > 0.5 else 0.0
        out = prev * (1 - k) + nxt * k
        return fx.flash(out, math.sin(u * math.pi) ** 0.6 * 0.92, (1.0, 0.92, 0.80))

    if kind == "whip":
        d = W * 1.15
        if u < 0.5:
            k = fx.ease_in(u * 2, 2.0)
            out = fx.directional_blur(prev, d * k * 0.55, 0, 9)
            out = np.roll(out, -int(d * k * 0.42), axis=1)
        else:
            k = 1 - fx.ease_out((u - 0.5) * 2, 2.0)
            out = fx.directional_blur(nxt, d * k * 0.55, 0, 9)
            out = np.roll(out, int(d * k * 0.42), axis=1)
        return fx.flash(out, math.sin(u * math.pi) * 0.16)

    if kind == "zoomblur":
        k = fx.ease_io(u)
        a = fx.radial_blur(prev, 0.20 * math.sin(u * math.pi))
        b = fx.radial_blur(nxt, 0.26 * math.sin(u * math.pi))
        out = a * (1 - k) + b * k
        return fx.flash(out, math.sin(u * math.pi) * 0.22)

    if kind == "glitch":
        k = 1.0 if u > 0.45 else 0.0
        out = prev * (1 - k) + nxt * k
        g = math.sin(u * math.pi) ** 0.5
        out = fx.glitch(out, g * 0.95, seed)
        return fx.chroma_split(out, g * 0.012)

    if kind == "push":
        k = fx.ease_io(u)
        off = max(0, min(W - 1, int(W * k)))
        out = np.empty_like(prev)
        if off:
            out[:, : W - off] = prev[:, off:]
            out[:, W - off :] = nxt[:, :off]
        else:
            out[:] = prev
        return fx.directional_blur(out, W * 0.09 * math.sin(u * math.pi), 0, 5)

    if kind == "leak":
        k = fx.ease_io(u)
        out = prev * (1 - k) + nxt * k
        wash = fx.light_leak((H, W), u * 2.4, (1.0, 0.62, 0.28), seed)
        return fx.screen(out, wash * math.sin(u * math.pi) * 1.5)

    k = 1.0 if u > 0.5 else 0.0
    return prev * (1 - k) + nxt * k


# --------------------------------------------------------------------------- #
# caption schedule
# --------------------------------------------------------------------------- #

CAPTION_STYLE = {
    "hook": {"size": 104, "cy": H * 0.735},
    "brand": {"size": 96, "cy": H * 0.755},
    "library": {"size": 96, "cy": H * 0.745},
    "taste": {"size": 92, "cy": H * 0.745},
    "offline": {"size": 100, "cy": H * 0.735},
    "cta": {"size": 90, "cy": H * 0.628},
}


def _caption_schedule() -> list[dict]:
    out = []
    for spec in VO_LINES:
        line = LINES[spec["id"]]
        beats = spec["caption"]
        for i, beat in enumerate(beats):
            start = line["words"][beat["on"]]["start"]
            if i + 1 < len(beats):
                stop = line["words"][beats[i + 1]["on"]]["start"] - 0.22
            elif spec["id"] == "cta":
                stop = TIMING["duration"]  # the end-card headline stays up
            else:
                stop = min(line["pause_end"] + 0.05, start + 2.35)
            style = CAPTION_STYLE[spec["id"]]
            out.append(
                {
                    "words": tuple(beat["words"]),
                    "start": start,
                    "hold": max(0.5, stop - start),
                    "size": style["size"],
                    "cy": style["cy"],
                    "accent": i == len(beats) - 1,
                }
            )
    return out


CAPTIONS = _caption_schedule()

# Feature chips that punctuate the offline beat.
CHIPS = [
    {"text": "تحميل للاستماع بدون إنترنت", "start": LINES["offline"]["words"][3]["start"] + 0.10,
     "hold": 1.05, "cy": H * 0.30},
    {"text": "بدون إعلانات تقطع الأغنية", "start": LINES["offline"]["words"][5]["start"] + 0.10,
     "hold": 1.25, "cy": H * 0.30},
]


# --------------------------------------------------------------------------- #
# master frame
# --------------------------------------------------------------------------- #


def _shot_at(t: float) -> tuple[int, Shot]:
    for i, s in enumerate(SHOTS):
        if t < s.end or i == len(SHOTS) - 1:
            return i, s
    return len(SHOTS) - 1, SHOTS[-1]


def frame(t: float, index: int = 0) -> np.ndarray:
    i, shot = _shot_at(t)
    arr = shot.fn(t - shot.start)

    if shot.trans_dur > 0 and i > 0 and t - shot.start < shot.trans_dur:
        prev = SHOTS[i - 1]
        u = (t - shot.start) / shot.trans_dur
        arr = blend(shot.trans, u, prev.fn(t - prev.start), arr, seed=i * 977)

    motion = 0.0
    if shot.trans_dur > 0 and t - shot.start < shot.trans_dur:
        motion = math.sin((t - shot.start) / shot.trans_dur * math.pi)

    if 7.0 < t < 27.4:
        arr = bass_pulse(t, arr, BPM, 0.028)

    for cap in CAPTIONS:
        ts = t - cap["start"]
        if -0.05 <= ts <= cap["hold"] + 0.26:
            arr = draw_caption(arr, cap["words"], ts, cap["size"], cap["cy"],
                               accent_last=cap["accent"], hold=cap["hold"])

    for chip in CHIPS:
        ts = t - chip["start"]
        if -0.05 <= ts <= chip["hold"] + 0.4:
            u_in = fx.overshoot(fx.clamp01(ts / 0.34), 1.5)
            u_out = fx.clamp01((ts - chip["hold"]) / 0.3)
            pill = ui.feature_pill(chip["text"], 46)
            arr = fx.composite(
                arr,
                fx.place((W, H), pill, W / 2, chip["cy"] - (1 - u_in) * 40 - u_out * 30,
                         0.9 + 0.1 * u_in, 0, (1 - u_out)),
                1.0,
            )

    bug = fx.clamp01((t - 6.2) / 0.6) * (1 - fx.clamp01((t - 26.6) / 0.5))
    if shot.name.startswith("phone"):  # the app's own header owns that corner
        bug *= 1 - fx.clamp01((t - shot.start + 0.25) / 0.3)
    elif SHOTS[i - 1].name.startswith("phone") and t - shot.start < 0.45:
        bug *= fx.clamp01((t - shot.start) / 0.45)
    arr = logo_bug(arr, bug * 0.85)

    arr = fx.grade(arr)
    arr = fx.bloom(arr, 0.66, 24, 0.44)
    arr = fx.halation(arr, 0.20, 44)
    arr = fx.chroma_split(arr, 0.0016 + motion * 0.006)
    arr = fx.vignette(arr, 0.40, 1.7)
    arr = fx.grain(arr, 0.030, index)

    fade_in = fx.clamp01(t / 0.45)
    fade_out = 1 - fx.clamp01((t - (TIMING["duration"] - 0.55)) / 0.55)
    k = min(fade_in, fade_out)
    if k < 0.999:
        arr = arr * k
    return arr
