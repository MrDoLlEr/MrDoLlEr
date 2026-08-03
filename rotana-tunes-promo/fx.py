"""Camera, transition and finishing effects.

Geometry runs through PIL's affine transform (bicubic, so sub-pixel camera
moves stay smooth); everything tonal runs on float32 numpy arrays in 0..1.
"""

from __future__ import annotations

import math

import numpy as np
from PIL import Image, ImageFilter

from config import H, W

# --------------------------------------------------------------------------- #
# conversions
# --------------------------------------------------------------------------- #


def np_of(img: Image.Image) -> np.ndarray:
    return np.asarray(img.convert("RGB"), dtype=np.float32) / 255.0


def pil_of(arr: np.ndarray) -> Image.Image:
    return Image.fromarray((np.clip(arr, 0, 1) * 255).astype(np.uint8), "RGB")


# --------------------------------------------------------------------------- #
# easing
# --------------------------------------------------------------------------- #


def clamp01(x: float) -> float:
    return 0.0 if x < 0 else 1.0 if x > 1 else x


def ease_out(x: float, p: float = 3.0) -> float:
    return 1 - (1 - clamp01(x)) ** p


def ease_in(x: float, p: float = 3.0) -> float:
    return clamp01(x) ** p


def ease_io(x: float) -> float:
    x = clamp01(x)
    return 4 * x * x * x if x < 0.5 else 1 - (-2 * x + 2) ** 3 / 2


def overshoot(x: float, amount: float = 1.25) -> float:
    """Ease-out-back: lands slightly past the target then settles."""
    x = clamp01(x)
    c1 = amount
    c3 = c1 + 1
    return 1 + c3 * (x - 1) ** 3 + c1 * (x - 1) ** 2


def spring(x: float, freq: float = 3.0, decay: float = 6.0) -> float:
    x = clamp01(x)
    if x >= 1:
        return 1.0
    return 1 - math.exp(-decay * x) * math.cos(freq * math.pi * x)


# --------------------------------------------------------------------------- #
# camera
# --------------------------------------------------------------------------- #


def camera(
    plate: Image.Image,
    zoom: float = 1.0,
    dx: float = 0.0,
    dy: float = 0.0,
    rot: float = 0.0,
    size: tuple[int, int] = (W, H),
    fit: str = "cover",
) -> Image.Image:
    """Frame `plate` into `size` with a virtual camera.

    zoom  1.0 = the plate exactly covers the frame; >1 pushes in.
    dx/dy pan in output pixels at the current zoom.
    rot   camera roll in degrees.
    """
    ow, oh = size
    pw, ph = plate.size
    base = max(ow / pw, oh / ph) if fit == "cover" else min(ow / pw, oh / ph)
    k = 1.0 / (base * zoom)  # output pixel -> source pixel

    th = math.radians(rot)
    cos_t, sin_t = math.cos(th) * k, math.sin(th) * k
    cx, cy = pw / 2 - dx * k, ph / 2 - dy * k

    a, b = cos_t, -sin_t
    d, e = sin_t, cos_t
    c = cx - (a * ow / 2 + b * oh / 2)
    f = cy - (d * ow / 2 + e * oh / 2)
    return plate.transform((ow, oh), Image.AFFINE, (a, b, c, d, e, f), resample=Image.BICUBIC)


def camera_blurred(plate: Image.Image, params: list[dict], size=(W, H)) -> Image.Image:
    """True motion blur: average the camera at several sub-frame positions."""
    if len(params) == 1:
        return camera(plate, size=size, **params[0])
    acc = None
    for p in params:
        f = np.asarray(camera(plate, size=size, **p).convert("RGB"), dtype=np.float32)
        acc = f if acc is None else acc + f
    return Image.fromarray((acc / len(params)).astype(np.uint8), "RGB")


# --------------------------------------------------------------------------- #
# tonal
# --------------------------------------------------------------------------- #


def bloom(arr: np.ndarray, threshold: float = 0.62, radius: int = 26, strength: float = 0.5,
          tint=(1.0, 0.86, 0.72)) -> np.ndarray:
    lum = arr @ np.array([0.299, 0.587, 0.114], dtype=np.float32)
    mask = np.clip((lum - threshold) / max(1e-3, 1 - threshold), 0, 1)[..., None]
    bright = arr * mask
    img = Image.fromarray((np.clip(bright, 0, 1) * 255).astype(np.uint8), "RGB")
    blurred = np.asarray(img.filter(ImageFilter.GaussianBlur(radius)), dtype=np.float32) / 255.0
    blurred *= np.array(tint, dtype=np.float32)
    return 1 - (1 - arr) * (1 - np.clip(blurred * strength, 0, 1))


def halation(arr: np.ndarray, strength: float = 0.22, radius: int = 40) -> np.ndarray:
    """Red-biased glow around highlights, the way film scatters in the emulsion."""
    lum = arr @ np.array([0.299, 0.587, 0.114], dtype=np.float32)
    mask = np.clip((lum - 0.75) * 4, 0, 1)
    img = Image.fromarray((mask * 255).astype(np.uint8), "L")
    blurred = np.asarray(img.filter(ImageFilter.GaussianBlur(radius)), dtype=np.float32) / 255.0
    tint = np.stack([blurred, blurred * 0.35, blurred * 0.22], axis=-1)
    return np.clip(arr + tint * strength, 0, 1)


def chroma_split(arr: np.ndarray, amount: float) -> np.ndarray:
    """Lens-style lateral chromatic aberration, scaled from the frame centre."""
    if amount <= 0.0005:
        return arr
    h, w = arr.shape[:2]
    out = arr.copy()
    for ch, s in ((0, 1 + amount), (2, 1 - amount)):
        img = Image.fromarray((np.clip(arr[..., ch], 0, 1) * 255).astype(np.uint8), "L")
        scaled = img.resize((max(2, int(w * s)), max(2, int(h * s))), Image.BICUBIC)
        ox, oy = (scaled.width - w) // 2, (scaled.height - h) // 2
        out[..., ch] = np.asarray(scaled.crop((ox, oy, ox + w, oy + h)), dtype=np.float32) / 255.0
    return out


_VIGNETTE_CACHE: dict[tuple, np.ndarray] = {}


def vignette(arr: np.ndarray, strength: float = 0.42, power: float = 1.6) -> np.ndarray:
    key = (arr.shape[0], arr.shape[1], round(strength, 3), round(power, 3))
    m = _VIGNETTE_CACHE.get(key)
    if m is None:
        h, w = arr.shape[:2]
        y, x = np.mgrid[0:h, 0:w].astype(np.float32)
        r = np.sqrt(((x - w / 2) / (w / 2)) ** 2 + ((y - h / 2) / (h / 2)) ** 2) / math.sqrt(2)
        m = (1 - strength * np.clip(r, 0, 1) ** power)[..., None].astype(np.float32)
        _VIGNETTE_CACHE[key] = m
    return arr * m


_GRAIN: np.ndarray | None = None


def grain(arr: np.ndarray, amount: float = 0.035, seed_frame: int = 0) -> np.ndarray:
    """Animated film grain, cycled from a small pre-baked noise stack."""
    global _GRAIN
    h, w = arr.shape[:2]
    if _GRAIN is None or _GRAIN.shape[1:3] != (h, w):
        rng = np.random.default_rng(7)
        _GRAIN = rng.normal(0, 1, size=(8, h, w)).astype(np.float32)
        for i in range(8):
            img = Image.fromarray(((_GRAIN[i] * 40) + 128).clip(0, 255).astype(np.uint8), "L")
            _GRAIN[i] = (np.asarray(img.filter(ImageFilter.GaussianBlur(0.6)), np.float32) - 128) / 40
    g = _GRAIN[seed_frame % 8][..., None]
    # Grain is most visible in the mid-tones, barely in the blacks.
    lum = (arr @ np.array([0.299, 0.587, 0.114], dtype=np.float32))[..., None]
    weight = np.clip(1.6 * lum * (1 - lum) + 0.12, 0, 1)
    return np.clip(arr + g * amount * weight, 0, 1)


def grade(arr: np.ndarray, lift=0.012, contrast=1.10, sat=1.06,
          shadow_tint=(0.98, 0.99, 1.06), high_tint=(1.05, 0.99, 0.94)) -> np.ndarray:
    """Cinematic grade: crushed cool shadows, warm highlights, gentle S-curve."""
    x = np.clip(arr, 0, 1)
    lum = (x @ np.array([0.299, 0.587, 0.114], dtype=np.float32))[..., None]
    x = x + (np.array(shadow_tint, np.float32) - 1) * (1 - lum) * 0.5
    x = x + (np.array(high_tint, np.float32) - 1) * lum * 0.5
    x = (x - 0.5) * contrast + 0.5 + lift
    lum2 = (x @ np.array([0.299, 0.587, 0.114], dtype=np.float32))[..., None]
    x = lum2 + (x - lum2) * sat
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x) * 0.22 + x * 0.78  # soft filmic shoulder


def exposure(arr: np.ndarray, ev: float) -> np.ndarray:
    return np.clip(arr * (2.0 ** ev), 0, 1)


# --------------------------------------------------------------------------- #
# transitions
# --------------------------------------------------------------------------- #


def radial_blur(arr: np.ndarray, amount: float, steps: int = 6) -> np.ndarray:
    """Zoom blur out of the frame centre."""
    if amount <= 0.001:
        return arr
    img = Image.fromarray((np.clip(arr, 0, 1) * 255).astype(np.uint8), "RGB")
    h, w = arr.shape[:2]
    acc = np.zeros_like(arr)
    for i in range(steps):
        s = 1 + amount * (i / max(1, steps - 1))
        sw, sh = int(w * s), int(h * s)
        z = img.resize((sw, sh), Image.BILINEAR)
        ox, oy = (sw - w) // 2, (sh - h) // 2
        acc += np.asarray(z.crop((ox, oy, ox + w, oy + h)), dtype=np.float32) / 255.0
    return acc / steps


def directional_blur(arr: np.ndarray, dx: float, dy: float, steps: int = 7) -> np.ndarray:
    """Linear smear, used for whip pans."""
    if abs(dx) < 0.5 and abs(dy) < 0.5:
        return arr
    img = Image.fromarray((np.clip(arr, 0, 1) * 255).astype(np.uint8), "RGB")
    acc = np.zeros_like(arr)
    for i in range(steps):
        t = i / (steps - 1) - 0.5
        shifted = img.transform(
            img.size, Image.AFFINE, (1, 0, dx * t, 0, 1, dy * t), resample=Image.BILINEAR
        )
        acc += np.asarray(shifted, dtype=np.float32) / 255.0
    return acc / steps


def glitch(arr: np.ndarray, amount: float, seed: int) -> np.ndarray:
    """Digital tear: horizontal band displacement plus a hard RGB split."""
    if amount <= 0.01:
        return arr
    rng = np.random.default_rng(seed)
    out = arr.copy()
    h, w = arr.shape[:2]
    for _ in range(int(3 + amount * 9)):
        y0 = rng.integers(0, h - 8)
        band = int(rng.integers(6, 90))
        y1 = min(h, y0 + band)
        shift = int(rng.integers(-1, 2) * rng.integers(8, 90) * amount)
        out[y0:y1] = np.roll(arr[y0:y1], shift, axis=1)
    out[..., 0] = np.roll(out[..., 0], int(9 * amount), axis=1)
    out[..., 2] = np.roll(out[..., 2], -int(9 * amount), axis=1)
    return out


def screen(base: np.ndarray, top: np.ndarray, opacity: float = 1.0) -> np.ndarray:
    return base + (1 - (1 - base) * (1 - top) - base) * opacity


def flash(arr: np.ndarray, amount: float, colour=(1.0, 0.93, 0.82)) -> np.ndarray:
    if amount <= 0.001:
        return arr
    c = np.array(colour, dtype=np.float32)
    return np.clip(arr + (c - arr) * amount, 0, 1)


_LEAK_CACHE: dict[tuple, np.ndarray] = {}


def light_leak(shape: tuple[int, int], t: float, colour=(1.0, 0.45, 0.25), seed: int = 0) -> np.ndarray:
    """A drifting soft blob of light, screened over the frame."""
    h, w = shape
    key = (h, w, seed)
    grid = _LEAK_CACHE.get(key)
    if grid is None:
        y, x = np.mgrid[0:h, 0:w].astype(np.float32)
        grid = (x / w, y / h)
        _LEAK_CACHE[key] = grid
    gx, gy = grid
    rng = np.random.default_rng(seed)
    cx = 0.5 + 0.9 * math.sin(t * 1.7 + rng.random() * 6)
    cy = 0.5 + 0.7 * math.cos(t * 1.1 + rng.random() * 6)
    r = np.sqrt(((gx - cx) * 1.1) ** 2 + ((gy - cy) * 0.7) ** 2)
    blob = np.exp(-(r ** 2) * 5.0).astype(np.float32)
    return blob[..., None] * np.array(colour, dtype=np.float32)


def composite(base: np.ndarray, layer: Image.Image, opacity: float = 1.0,
              blend: str = "normal") -> np.ndarray:
    """Alpha-composite an RGBA PIL layer over a float array."""
    la = np.asarray(layer, dtype=np.float32) / 255.0
    rgb, alpha = la[..., :3], la[..., 3:4] * opacity
    if blend == "screen":
        mixed = 1 - (1 - base) * (1 - rgb)
        return base + (mixed - base) * alpha
    if blend == "add":
        return np.clip(base + rgb * alpha, 0, 1)
    return base * (1 - alpha) + rgb * alpha


def place(canvas_size: tuple[int, int], layer: Image.Image, cx: float, cy: float,
          scale: float = 1.0, rot: float = 0.0, opacity: float = 1.0) -> Image.Image:
    """Put an RGBA layer on a transparent canvas, centred on (cx, cy)."""
    out = Image.new("RGBA", canvas_size, (0, 0, 0, 0))
    if opacity <= 0.002 or scale <= 0.001:
        return out
    lw, lh = layer.size
    if abs(scale - 1) > 0.002:
        layer = layer.resize((max(1, int(lw * scale)), max(1, int(lh * scale))), Image.LANCZOS)
    if abs(rot) > 0.05:
        layer = layer.rotate(rot, resample=Image.BICUBIC, expand=True)
    if opacity < 0.998:
        a = layer.split()[-1].point(lambda v: int(v * opacity))
        layer = layer.copy()
        layer.putalpha(a)
    out.alpha_composite(layer, (int(cx - layer.width / 2), int(cy - layer.height / 2)))
    return out
