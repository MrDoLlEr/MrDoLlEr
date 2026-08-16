#!/usr/bin/env python3
"""Render two Instagram 4:5 interactive posts for Assala — أصالة."""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "exports"
PREVIEW = ROOT / "preview"

W, H = 1080, 1350  # Instagram portrait 4:5

FONTS = {
    "amiri": "/usr/share/fonts/opentype/fonts-hosny-amiri/Amiri-Regular.ttf",
    "amiri_b": "/usr/share/fonts/opentype/fonts-hosny-amiri/Amiri-Bold.ttf",
    "plex": "/usr/share/fonts/truetype/ibm-plex/IBMPlexSansArabic-Regular.ttf",
    "plex_m": "/usr/share/fonts/truetype/ibm-plex/IBMPlexSansArabic-Medium.ttf",
    "plex_sb": "/usr/share/fonts/truetype/ibm-plex/IBMPlexSansArabic-SemiBold.ttf",
    "kufi": "/usr/share/fonts/truetype/noto/NotoKufiArabic-Regular.ttf",
}

NIGHT = {
    "bg": (16, 10, 9),
    "ink": (246, 236, 218),
    "muted": (186, 156, 132),
    "gold": (201, 168, 112),
    "wine": (148, 40, 48),
}

DAY = {
    "bg": (239, 228, 208),
    "ink": (28, 16, 12),
    "muted": (104, 72, 54),
    "gold": (132, 92, 42),
    "wine": (122, 28, 36),
}


def font(key: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONTS[key], size)


def ar(draw: ImageDraw.ImageDraw, xy, text, **kwargs):
    kwargs.setdefault("language", "ar")
    kwargs.setdefault("direction", "rtl")
    draw.text(xy, text, **kwargs)


def grain(img: Image.Image, amount: float = 0.03) -> Image.Image:
    arr = np.asarray(img).astype(np.float32)
    noise = np.random.default_rng(11).normal(0, 255 * amount, arr.shape[:2])
    for c in range(3):
        arr[:, :, c] = np.clip(arr[:, :, c] + noise, 0, 255)
    return Image.fromarray(arr.astype(np.uint8))


def star(draw: ImageDraw.ImageDraw, cx: float, cy: float, r: float, fill) -> None:
    pts = []
    for i in range(16):
        ang = math.radians(-90 + i * 22.5)
        rad = r if i % 2 == 0 else r * 0.38
        pts.append((cx + rad * math.cos(ang), cy + rad * math.sin(ang)))
    draw.polygon(pts, fill=fill)


def plate(pal: dict) -> Image.Image:
    img = Image.new("RGB", (W, H), pal["bg"])
    draw = ImageDraw.Draw(img)
    gold = pal["gold"]
    m = 44
    draw.rectangle([m, m, W - m, H - m], outline=gold, width=1)
    draw.rectangle([m + 10, m + 10, W - m - 10, H - m - 10], outline=gold, width=1)
    for cx, cy in (
        (m + 10, m + 10),
        (W - m - 10, m + 10),
        (m + 10, H - m - 10),
        (W - m - 10, H - m - 10),
    ):
        star(draw, cx, cy, 9, gold)
    return img


def rule(draw: ImageDraw.ImageDraw, y: int, pal: dict) -> None:
    draw.line([(160, y), (500, y)], fill=pal["gold"], width=1)
    draw.line([(580, y), (920, y)], fill=pal["gold"], width=1)
    star(draw, 540, y, 8, pal["gold"])


def paste_mask(base: Image.Image, mask: Image.Image, color: tuple[int, int, int], xy=(0, 0)) -> None:
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    tint = Image.new("RGBA", mask.size, (*color, 255))
    layer.paste(tint, xy, mask)
    composed = Image.alpha_composite(base.convert("RGBA"), layer)
    base.paste(composed.convert("RGB"))


def crescent_mask(size: int = 96) -> Image.Image:
    m = Image.new("L", (size, size), 0)
    d = ImageDraw.Draw(m)
    pad = 4
    d.ellipse([pad, pad, size - pad, size - pad], fill=255)
    # Offset disc eats the right side → classic waxing crescent
    d.ellipse([int(size * 0.28), pad, size + 8, size - pad], fill=0)
    return m


def sun_mask(size: int = 96) -> Image.Image:
    m = Image.new("L", (size, size), 0)
    d = ImageDraw.Draw(m)
    c = size // 2
    r = 22
    d.ellipse([c - r, c - r, c + r, c + r], outline=255, width=2)
    d.ellipse([c - 3, c - 3, c + 3, c + 3], fill=255)
    for i in range(12):
        a = math.radians(-90 + i * 30)
        inner, outer = r + 8, r + 18
        d.line(
            [
                (c + math.cos(a) * inner, c + math.sin(a) * inner),
                (c + math.cos(a) * outer, c + math.sin(a) * outer),
            ],
            fill=255,
            width=2,
        )
    return m


def header(draw, pal, kicker: str) -> None:
    ar(draw, (W // 2, 88), kicker, font=font("kufi", 22), fill=pal["gold"], anchor="mm")


def footer(draw, pal, cta: str) -> None:
    rule(draw, 1188, pal)
    ar(draw, (W // 2, 1240), cta, font=font("plex_sb", 30), fill=pal["ink"], anchor="mm")
    ar(
        draw,
        (W // 2, 1294),
        "كلمات وألحان أمجد جمعة   ·   توزيع فؤاد جنيد",
        font=font("plex", 17),
        fill=pal["muted"],
        anchor="mm",
    )


def post_one() -> Image.Image:
    pal = NIGHT
    img = plate(pal)
    paste_mask(img, crescent_mask(110), pal["gold"], (485, 118))
    draw = ImageDraw.Draw(img)
    header(draw, pal, "أصالة   ·   إصدار جديد")

    ar(draw, (W // 2, 292), "أي بيت أقوى؟", font=font("amiri_b", 82), fill=pal["ink"], anchor="mm")
    ar(
        draw,
        (W // 2, 368),
        "علّق بالرقم في الكومنت",
        font=font("plex", 26),
        fill=pal["muted"],
        anchor="mm",
    )
    rule(draw, 422, pal)

    verses = [
        ("١", "وأنا من اسمي أصالة", "يعني ما أخون الوعد"),
        ("٢", "إني أنسى الحب؟ لا لا", "صفر بالمية احتمالا"),
    ]
    y = 478
    for i, (num, line1, line2) in enumerate(verses):
        # Number leads from the right; verse sits in the optical center.
        ar(draw, (918, y + 72), num, font=font("amiri_b", 118), fill=pal["wine"], anchor="mm")
        draw.line([(800, y + 16), (800, y + 128)], fill=pal["gold"], width=1)
        ar(draw, (430, y + 36), line1, font=font("amiri", 46), fill=pal["ink"], anchor="mm")
        ar(draw, (430, y + 108), line2, font=font("amiri_b", 42), fill=pal["gold"], anchor="mm")
        if i == 0:
            draw.line([(160, y + 196), (920, y + 196)], fill=pal["gold"], width=1)
        y += 268

    footer(draw, pal, "اكتب ١     أو     ٢")
    return grain(img, 0.026)


def post_two() -> Image.Image:
    pal = DAY
    img = plate(pal)
    paste_mask(img, sun_mask(120), pal["gold"], (480, 112))
    draw = ImageDraw.Draw(img)
    header(draw, pal, "أصالة   ·   إصدار جديد")

    ar(draw, (W // 2, 292), "كمّل البيت", font=font("amiri_b", 82), fill=pal["ink"], anchor="mm")
    ar(
        draw,
        (W // 2, 368),
        "اكتب الكلمة الناقصة في التعليق",
        font=font("plex", 26),
        fill=pal["muted"],
        anchor="mm",
    )
    rule(draw, 424, pal)

    ar(draw, (W // 2, 530), "وأنا من اسمي", font=font("amiri", 54), fill=pal["ink"], anchor="mm")

    # Empty manuscript field — the interaction
    draw.rectangle([200, 600, 880, 742], outline=pal["wine"], width=2)
    x = 260
    while x < 820:
        draw.line([(x, 688), (min(x + 18, 820), 688)], fill=pal["gold"], width=2)
        x += 30

    ar(draw, (W // 2, 860), "يعني ما أخون الوعد", font=font("amiri_b", 48), fill=pal["ink"], anchor="mm")
    ar(
        draw,
        (W // 2, 980),
        "ومنشن شخص ما يخون الوعد",
        font=font("plex_m", 28),
        fill=pal["muted"],
        anchor="mm",
    )

    footer(draw, pal, "الكلمة  +  منشن")
    return grain(img, 0.02)


def save(img: Image.Image, name: str) -> Path:
    OUT.mkdir(parents=True, exist_ok=True)
    PREVIEW.mkdir(parents=True, exist_ok=True)
    path = OUT / name
    img.save(path, "PNG", optimize=True)
    return path


def main() -> None:
    p1 = save(post_one(), "01-ayy-bayt-aqwa.png")
    p2 = save(post_two(), "02-kammil-albayt.png")
    print(p1)
    print(p2)
    for p in (p1, p2):
        im = Image.open(p)
        print(p.name, im.size, im.mode)


if __name__ == "__main__":
    main()
