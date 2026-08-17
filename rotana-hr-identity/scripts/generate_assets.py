#!/usr/bin/env python3
"""Generate icons, photo-mask placeholders, and textures for the Rotana HR kit."""
from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
ICON_DIR = ROOT / "assets" / "icons"
MASK_DIR = ROOT / "assets" / "masks"
PH_DIR = ROOT / "assets" / "placeholders"

FOREST = (0, 81, 47)
GROVE = (0, 108, 60)
LEAF = (43, 168, 108)
INK = (12, 16, 14)
MIST = (232, 232, 228)
PAPER = (247, 246, 243)
STONE = (197, 199, 194)
WHITE = (255, 255, 255)
SAGE = (184, 192, 176)

AR_FONT = "/usr/share/fonts/truetype/ibm-plex/IBMPlexSansArabic-Medium.ttf"
AR_REG = "/usr/share/fonts/truetype/ibm-plex/IBMPlexSansArabic-Regular.ttf"


def font(path: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(path, size)


# --- Icons: rounded monoline, matching the Rotana wordmark terminals --------
ICONS = {
    "people": "M8 19v-1.2A4.2 4.2 0 0 1 12.2 13.6h7.6A4.2 4.2 0 0 1 24 18V19 M16 13.4a3.4 3.4 0 1 0 0-6.8 3.4 3.4 0 0 0 0 6.8 M6.2 19v-1A3.4 3.4 0 0 1 9.6 14.6h.4 M9.2 13.2a2.7 2.7 0 1 0-2.2-4.8",
    "hire": "M16 7.5v5.2 M13.4 10.1h5.2 M8 21.2V9.4A1.6 1.6 0 0 1 9.6 7.8h12.8A1.6 1.6 0 0 1 24 9.4v11.8 M8 21.2H6.2A1.6 1.6 0 0 1 4.6 19.6V11",
    "onboard": "M7 16.5l4.2 4.2L21.5 10.4 M16 6.5h6.2v6.2",
    "train": "M5 12.5 L16 7.2 27 12.5 16 17.8Z M9.2 14.6v4.2c0 0 3 2.4 6.8 2.4s6.8-2.4 6.8-2.4v-4.2",
    "performance": "M6.5 22V10.5 M13 22V7.5 M19.5 22v-8.2 M26 22V5.8",
    "benefits": "M16 7.2c-2.8-3.2-8.2-1.4-8.2 2.8 0 5.6 8.2 10.6 8.2 10.6s8.2-5 8.2-10.6c0-4.2-5.4-6-8.2-2.8z",
    "relations": "M8.5 12.5h6.2v7.4H8.2A2.4 2.4 0 0 1 5.8 17.5v-2.6A2.4 2.4 0 0 1 8.2 12.5Z M17.3 12.5h6.2A2.4 2.4 0 0 1 25.9 14.9v2.6a2.4 2.4 0 0 1-2.4 2.4h-.3 M11.6 12.5V10.2a4.4 4.4 0 0 1 8.8 0v2.3",
    "culture": "M16 26.2c5.6-4.4 8.4-8.2 8.4-12.2A8.4 8.4 0 0 0 7.6 14c0 4 2.8 7.8 8.4 12.2z M16 15.6a2.2 2.2 0 1 0 0-4.4 2.2 2.2 0 0 0 0 4.4",
    "wellness": "M8.4 16.2c0-4 3.2-6.4 7.6-3.6 4.4-2.8 7.6-.4 7.6 3.6 0 4.8-7.6 9.2-7.6 9.2s-7.6-4.4-7.6-9.2z",
    "payroll": "M8 8.4h16v15.2H8z M8 13.2h16 M12.4 8.4V6.8 M19.6 8.4V6.8 M13.2 18.2h5.6",
    "policy": "M10.2 6.8h9.2l4.4 4.4v14H10.2z M19.4 6.8v4.4h4.4 M13.2 16.2h7.6 M13.2 19.8h5.2",
    "talent": "M16 6.4l1.8 5.4h5.6l-4.5 3.3 1.7 5.5L16 17.4l-4.6 3.2 1.7-5.5-4.5-3.3h5.6z",
    "org": "M16 7.2h0 M16 7.2a2.6 2.6 0 1 0 .01 0 M16 9.8v4.4 M9.2 16.8a2.4 2.4 0 1 0 .01 0 M16 16.8a2.4 2.4 0 1 0 .01 0 M22.8 16.8a2.4 2.4 0 1 0 .01 0 M9.2 14.4h13.6",
    "calendar": "M8.4 9.2h15.2v14.4H8.4z M8.4 13.6h15.2 M12 9.2V6.8 M20 9.2V6.8 M12.4 17.2h2.2 M17.4 17.2h2.2",
    "chart": "M6.8 22.2h18.4 M9.6 22.2V14 M16 22.2V8.6 M22.4 22.2v-9.4",
    "target": "M16 16m-8.4 0a8.4 8.4 0 1 0 16.8 0a8.4 8.4 0 1 0 -16.8 0 M16 16m-4.4 0a4.4 4.4 0 1 0 8.8 0a4.4 4.4 0 1 0 -8.8 0 M16 16m-1.4 0a1.4 1.4 0 1 0 2.8 0a1.4 1.4 0 1 0 -2.8 0",
    "handshake": "M8 16.4l4.4-4.4 3.2 3.2 3.2-3.2 4.4 4.4 M11 19.6h10",
    "shield": "M16 6.8l9.2 3.2v6.4c0 5.2-4 8.8-9.2 10.4C10.8 25.2 6.8 21.6 6.8 16.4V10z",
    "globe": "M16 16m-9 0a9 9 0 1 0 18 0a9 9 0 1 0 -18 0 M7.2 16h17.6 M16 7.2c2.6 2.4 3.8 5.4 3.8 8.8s-1.2 6.4-3.8 8.8c-2.6-2.4-3.8-5.4-3.8-8.8s1.2-6.4 3.8-8.8z",
    "music": "M12.2 24.2a3.2 3.2 0 1 0 .01 0 M22.2 21.2a3.2 3.2 0 1 0 .01 0 M15.4 24.2V9.2l10-2.2v14.2",
    "film": "M7.2 9.2h17.6v13.6H7.2z M10.4 9.2v13.6 M21.6 9.2v13.6 M7.2 13.2h3.2 M7.2 18.8h3.2 M21.6 13.2h3.2 M21.6 18.8h3.2",
    "tv": "M6.8 8.8h18.4v12.4H6.8z M12.4 21.2h7.2 M16 21.2v2.2",
    "megaphone": "M8.4 13.2h4.2l10.2-4.6v14.8L12.6 18.8H8.4z M8.4 13.2v5.6 M20.6 16.4c1.4 0 2.4 1 2.4 2.4",
    "building": "M8.4 24.2V9.2h15.2v15 M12 12.4h2 M16 12.4h2 M20 12.4h2 M12 16.8h2 M16 16.8h2 M20 16.8h2 M14.8 24.2v-4.2h2.4v4.2",
    "document": "M10.4 6.8h8.4l4.4 4.4v14H10.4z M18.8 6.8v4.4h4.4 M13.4 15.6h7.2 M13.4 19.2h5.2",
    "clock": "M16 16m-9 0a9 9 0 1 0 18 0a9 9 0 1 0 -18 0 M16 10.4V16l4 2.4",
    "pin": "M16 7.4a6.2 6.2 0 0 1 6.2 6.2c0 4.6-6.2 11.2-6.2 11.2S9.8 18.2 9.8 13.6A6.2 6.2 0 0 1 16 7.4z M16 15.8a2.2 2.2 0 1 0 0-4.4 2.2 2.2 0 0 0 0 4.4",
    "message": "M7.2 9.2h17.6v12.4l-5.2-3.2H7.2z",
    "heart": "M16 24.2s-8.4-5.2-8.4-10.6c0-3.2 2.4-5.2 5.2-5.2 1.8 0 3.2.8 3.2 2.4 0-1.6 1.4-2.4 3.2-2.4 2.8 0 5.2 2 5.2 5.2 0 5.4-8.4 10.6-8.4 10.6z",
    "spark": "M16 6.4v4.4 M16 21.2v4.4 M6.4 16h4.4 M21.2 16h4.4 M9.2 9.2l3 3 M19.8 19.8l3 3 M22.8 9.2l-3 3 M12.2 19.8l-3 3",
    "arrow": "M8.4 16h15.2 M18.4 10.8L23.6 16 18.4 21.2",
}


def icon_svg(name: str, d: str, color: str = "#00512F") -> str:
    extra = ""
    if name == "target":
        extra = (
            '<circle cx="16" cy="16" r="8.4"/><circle cx="16" cy="16" r="4.4"/>'
            '<circle cx="16" cy="16" r="1.2" fill="{c}" stroke="none"/>'
        ).format(c=color)
        d = ""
    if name == "globe":
        extra = (
            '<circle cx="16" cy="16" r="9"/>'
            '<path d="M7.2 16h17.6"/>'
            '<path d="M16 7.2c2.6 2.4 3.8 5.4 3.8 8.8s-1.2 6.4-3.8 8.8c-2.6-2.4-3.8-5.4-3.8-8.8s1.2-6.4 3.8-8.8z"/>'
        )
        d = ""
    body = extra if extra else f'<path d="{d}"/>'
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" fill="none"
  stroke="{color}" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
  {body}
</svg>
'''


def write_icons() -> None:
    ICON_DIR.mkdir(parents=True, exist_ok=True)
    for name, d in ICONS.items():
        (ICON_DIR / f"{name}.svg").write_text(icon_svg(name, d), encoding="utf-8")
        (ICON_DIR / f"{name}-white.svg").write_text(
            icon_svg(name, d, "#FFFFFF"), encoding="utf-8"
        )


def noise_field(w: int, h: int, seed: int = 3) -> Image.Image:
    import numpy as np

    rng = np.random.default_rng(seed)
    arr = rng.random((h, w))
    img = Image.fromarray((arr * 255).astype("uint8"), "L")
    img = img.filter(ImageFilter.GaussianBlur(radius=7))
    return img


def grade_texture(seed: int, tint: tuple[int, int, int]) -> Image.Image:
    import numpy as np

    w, h = 1200, 1500
    n = noise_field(w, h, seed)
    na = np.array(n, dtype="float32") / 255.0
    yy = np.linspace(0, 1, h)[:, None]
    xx = np.linspace(0, 1, w)[None, :]
    vignette = 1 - 0.28 * ((xx - 0.5) ** 2 + (yy - 0.38) ** 2) * 4
    wash = 0.22 + 0.55 * yy + 0.23 * na
    wash *= vignette
    paper = np.array([232, 232, 228], dtype="float32")
    rgb = np.zeros((h, w, 3), dtype="float32")
    for i, c in enumerate(tint):
        rgb[:, :, i] = wash * c + (1 - wash) * paper[i]
    return Image.fromarray(rgb.clip(0, 255).astype("uint8"), "RGB")


def silhouette_portrait(w: int, h: int, seed: int = 1) -> Image.Image:
    """Editorial bust placeholder — replace this layer with a photo."""
    img = Image.new("RGB", (w, h), MIST)
    d = ImageDraw.Draw(img)
    d.rectangle((0, 0, w, h), fill=(226, 227, 222))
    # studio ground
    d.ellipse((-w * 0.1, int(h * 0.72), w * 1.1, int(h * 1.35)), fill=(210, 212, 206))
    cx, cy = w // 2, int(h * 0.42)
    head_r = int(w * 0.16)
    d.ellipse((cx - head_r, cy - head_r - 20, cx + head_r, cy + head_r - 20), fill=FOREST)
    # shoulders
    d.ellipse((cx - int(w * 0.32), int(h * 0.52), cx + int(w * 0.32), int(h * 1.15)), fill=FOREST)
    # neck
    d.rectangle((cx - int(w * 0.06), cy + head_r - 40, cx + int(w * 0.06), int(h * 0.62)), fill=FOREST)
    # quiet leaf glint on shoulder
    d.ellipse((cx + int(w * 0.08), int(h * 0.58), cx + int(w * 0.18), int(h * 0.66)), fill=GROVE)
    return img.resize((w, h))


def wave_mask(size: int) -> Image.Image:
    """S-curve window inspired by the Rotana sphere ribbon."""
    m = Image.new("L", (size, size), 0)
    d = ImageDraw.Draw(m)
    # outer circle
    d.ellipse((2, 2, size - 3, size - 3), fill=255)
    return m


def ribbon_overlay(img: Image.Image) -> Image.Image:
    w, h = img.size
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    # white ribbon S
    pts = []
    for i in range(80):
        t = i / 79
        x = int(w * (0.08 + 0.84 * t))
        y = int(h * (0.62 - 0.28 * math.sin(t * math.pi) + 0.08 * math.sin(t * math.pi * 2)))
        pts.append((x, y))
    d.line(pts, fill=(255, 255, 255, 42), width=max(18, w // 28))
    return Image.alpha_composite(img.convert("RGBA"), overlay)


def label_replace(img: Image.Image, text: str = "استبدال الصورة") -> Image.Image:
    canvas = img.convert("RGBA")
    d = ImageDraw.Draw(canvas)
    f = font(AR_FONT, max(22, canvas.size[0] // 18))
    # dark bar at bottom
    h = canvas.size[1]
    w = canvas.size[0]
    d.rectangle((0, int(h * 0.86), w, h), fill=(12, 16, 14, 200))
    d.text(
        (w // 2, int(h * 0.93)),
        text,
        font=f,
        fill=WHITE + (255,),
        anchor="mm",
        language="ar",
        direction="rtl",
    )
    return canvas


def circle_crop(img: Image.Image) -> Image.Image:
    img = img.convert("RGBA")
    s = min(img.size)
    img = img.crop(((img.width - s) // 2, (img.height - s) // 2, (img.width + s) // 2, (img.height + s) // 2))
    m = Image.new("L", img.size, 0)
    ImageDraw.Draw(m).ellipse((1, 1, s - 2, s - 2), fill=255)
    img.putalpha(m)
    return img


def round_rect_crop(img: Image.Image, radius: int = 36) -> Image.Image:
    img = img.convert("RGBA")
    m = Image.new("L", img.size, 0)
    ImageDraw.Draw(m).rounded_rectangle((0, 0, img.width - 1, img.height - 1), radius=radius, fill=255)
    img.putalpha(m)
    return img


def arch_crop(img: Image.Image) -> Image.Image:
    img = img.convert("RGBA")
    m = Image.new("L", img.size, 0)
    d = ImageDraw.Draw(m)
    r = img.width // 2
    d.pieslice((0, 0, img.width - 1, img.width - 1), 180, 0, fill=255)
    d.rectangle((0, r, img.width, img.height), fill=255)
    img.putalpha(m)
    return img


def wave_window(img: Image.Image) -> Image.Image:
    """Vertical panel with a Rotana-like S-curve on the left edge."""
    img = img.convert("RGBA")
    w, h = img.size
    m = Image.new("L", (w, h), 0)
    px = m.load()
    for y in range(h):
        t = y / max(h - 1, 1)
        inset = int((0.18 + 0.10 * math.sin(t * math.pi * 1.15)) * w)
        for x in range(inset, w):
            px[x, y] = 255
    img.putalpha(m)
    return img


def write_placeholders() -> None:
    PH_DIR.mkdir(parents=True, exist_ok=True)
    MASK_DIR.mkdir(parents=True, exist_ok=True)
    tints = [
        (48, 92, 68),
        (36, 64, 50),
        (88, 94, 88),
        (22, 70, 48),
        (110, 112, 106),
        (18, 44, 32),
    ]
    textures = []
    for i, tint in enumerate(tints, 1):
        tex = grade_texture(10 + i * 7, tint)
        path = PH_DIR / f"texture-{i:02d}.jpg"
        tex.save(path, quality=90)
        textures.append(tex)

    portraits = [silhouette_portrait(900, 1120, i) for i in range(1, 5)]
    for i, p in enumerate(portraits, 1):
        p.save(PH_DIR / f"portrait-{i:02d}.jpg", quality=92)

    # circular portraits
    for i, tex in enumerate(portraits[:4], 1):
        c = circle_crop(tex.resize((720, 900)))
        c = label_replace(c)
        c.save(MASK_DIR / f"circle-{i:02d}.png")

    # rounded editorial
    for i, tex in enumerate(portraits[:3], 1):
        r = round_rect_crop(tex.resize((900, 1120)), 28)
        r = label_replace(r)
        r.save(MASK_DIR / f"rounded-{i:02d}.png")

    # arch
    a = arch_crop(portraits[0].resize((800, 1100)))
    a = label_replace(a)
    a.save(MASK_DIR / "arch-01.png")

    # wave window over a quieter texture
    w = wave_window(textures[2].resize((1000, 1200)))
    w = label_replace(w)
    w.save(MASK_DIR / "wave-01.png")

    # wide banner
    banner = textures[0].resize((1600, 640))
    banner = round_rect_crop(banner, 8)
    banner = label_replace(banner.convert("RGBA"))
    banner.save(MASK_DIR / "banner-01.png")

    sq = label_replace(textures[4].resize((900, 900)))
    sq.save(MASK_DIR / "square-01.png")


def write_wave_svg() -> None:
    svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 160" fill="none">
  <path d="M8 118 C 80 118, 110 28, 200 42 C 290 56, 310 128, 392 92"
        stroke="#00512F" stroke-width="14" stroke-linecap="round"/>
</svg>
"""
    (ROOT / "assets" / "logo" / "wave-motif.svg").write_text(svg, encoding="utf-8")


if __name__ == "__main__":
    write_icons()
    write_placeholders()
    write_wave_svg()
    print("assets ready", len(list(ICON_DIR.glob("*.svg"))), "icons")
