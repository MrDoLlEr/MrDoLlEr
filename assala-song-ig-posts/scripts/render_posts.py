#!/usr/bin/env python3
"""Photo-led Instagram 4:5 posts for Assala — أصالة. Official portraits, not empty type."""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFont

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "assets" / "source"
OUT = ROOT / "exports"

W, H = 1080, 1350

FONTS = {
    "amiri": "/usr/share/fonts/opentype/fonts-hosny-amiri/Amiri-Regular.ttf",
    "amiri_b": "/usr/share/fonts/opentype/fonts-hosny-amiri/Amiri-Bold.ttf",
    "plex": "/usr/share/fonts/truetype/ibm-plex/IBMPlexSansArabic-Regular.ttf",
    "plex_m": "/usr/share/fonts/truetype/ibm-plex/IBMPlexSansArabic-Medium.ttf",
    "plex_sb": "/usr/share/fonts/truetype/ibm-plex/IBMPlexSansArabic-SemiBold.ttf",
    "kufi": "/usr/share/fonts/truetype/noto/NotoKufiArabic-Regular.ttf",
}

GOLD = (212, 178, 118)
CREAM = (250, 242, 228)
WINE = (150, 36, 44)
MUTED = (210, 190, 168)


def font(key: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONTS[key], size)


def ar(draw: ImageDraw.ImageDraw, xy, text, **kwargs):
    kwargs.setdefault("language", "ar")
    kwargs.setdefault("direction", "rtl")
    draw.text(xy, text, **kwargs)


def to_rgb(im: Image.Image, bg=(24, 20, 22)) -> Image.Image:
    if im.mode == "P":
        im = im.convert("RGBA")
    if im.mode == "RGBA":
        base = Image.new("RGB", im.size, bg)
        base.paste(im, mask=im.split()[-1])
        return base
    return im.convert("RGB")


def crop_to_45(im: Image.Image, focus: str = "center", tight: float = 1.0) -> Image.Image:
    """Crop any image to 4:5, then scale to Instagram size."""
    im = to_rgb(im)
    tw, th = im.size
    if tight < 1.0:
        nw, nh = int(tw * tight), int(th * tight)
        left = (tw - nw) // 2
        top = int((th - nh) * 0.18)
        im = im.crop((left, top, left + nw, top + nh))
        tw, th = im.size
    target = 4 / 5
    if tw / th > target:
        nw = int(th * target)
        if focus == "right":
            left = tw - nw
        elif focus == "left":
            left = 0
        else:
            left = (tw - nw) // 2
        im = im.crop((left, 0, left + nw, th))
    else:
        nh = int(tw / target)
        top = max(0, int((th - nh) * 0.12))
        if top + nh > th:
            top = th - nh
        im = im.crop((0, top, tw, top + nh))
    return im.resize((W, H), Image.Resampling.LANCZOS)


def cover_album_type(im: Image.Image) -> Image.Image:
    """Paint out leftover Rotana single title so only Assala remains."""
    im = to_rgb(im)
    red = im.getpixel((24, 24))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 470, 820], fill=red)
    return im


def grade(im: Image.Image, contrast=1.12, color=1.06, brightness=0.97) -> Image.Image:
    im = ImageEnhance.Contrast(im).enhance(contrast)
    im = ImageEnhance.Color(im).enhance(color)
    im = ImageEnhance.Brightness(im).enhance(brightness)
    return im


def vignette(im: Image.Image, strength=0.55) -> Image.Image:
    arr = np.asarray(im).astype(np.float32)
    y, x = np.ogrid[:H, :W]
    cy, cx = H * 0.38, W * 0.5
    r = np.sqrt(((x - cx) / (W * 0.72)) ** 2 + ((y - cy) / (H * 0.70)) ** 2)
    shade = np.clip(1 - strength * np.clip(r - 0.55, 0, 1) ** 1.4, 0.35, 1)
    arr *= shade[..., None]
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


def bottom_scrim(im: Image.Image, start=0.42, end=0.98) -> Image.Image:
    arr = np.asarray(im).astype(np.float32)
    y = np.linspace(0, 1, H)[:, None, None]
    t = np.clip((y - start) / (end - start), 0, 1)
    t = t ** 1.35
    dark = np.array([8, 6, 6], dtype=np.float32)
    arr = arr * (1 - t) + dark * t
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


def shadow_text(draw, xy, text, font_obj, fill, anchor="mm", shadow=(0, 0, 0, 180)):
    x, y = xy
    # soft shadow
    for dx, dy in ((2, 2), (0, 3), (-1, 2)):
        ar(draw, (x + dx, y + dy), text, font=font_obj, fill=(0, 0, 0), anchor=anchor)
    ar(draw, xy, text, font=font_obj, fill=fill, anchor=anchor)


def post_one() -> Image.Image:
    photo = crop_to_45(Image.open(SRC / "rotana-portrait.png"), "center", tight=0.88)
    photo = grade(photo, contrast=1.14, color=1.04, brightness=0.96)
    photo = vignette(photo, 0.5)
    photo = bottom_scrim(photo, start=0.46, end=1.0)

    layer = photo.convert("RGBA")
    ui = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ui)

    shadow_text(d, (W // 2, 58), "أصالة  ·  إصدار جديد", font("kufi", 22), GOLD)

    # Interactive stack sits on the dress, not the face
    shadow_text(d, (W // 2, 790), "أي بيت أقوى؟", font("amiri_b", 62), CREAM)
    shadow_text(d, (W // 2, 846), "علّق بالرقم في الكومنت", font("plex", 24), MUTED)

    options = [
        ("١", "وأنا من اسمي أصالة", "يعني ما أخون الوعد"),
        ("٢", "إني أنسى الحب؟ لا لا", "صفر بالمية احتمالا"),
    ]
    y = 882
    for num, l1, l2 in options:
        x0, x1 = 70, 1010
        y1 = y + 118
        d.rectangle([x0, y, x1, y1], fill=(8, 6, 6, 210), outline=GOLD, width=1)
        d.rectangle([x1 - 92, y, x1, y1], fill=(*WINE, 230))
        ar(d, (x1 - 46, y + 59), num, font=font("amiri_b", 52), fill=CREAM, anchor="mm")
        ar(d, (x1 - 118, y + 40), l1, font=font("amiri", 30), fill=CREAM, anchor="rm")
        ar(d, (x1 - 118, y + 84), l2, font=font("amiri_b", 28), fill=GOLD, anchor="rm")
        y += 132

    d.rectangle([70, 1230, 1010, 1298], fill=(8, 6, 6, 220), outline=GOLD, width=1)
    ar(d, (W // 2, 1264), "اكتب ١     أو     ٢", font=font("plex_sb", 28), fill=CREAM, anchor="mm")

    out = Image.alpha_composite(layer, ui).convert("RGB")
    return out


def post_two() -> Image.Image:
    raw = cover_album_type(Image.open(SRC / "album-leheqt.jpg"))
    photo = crop_to_45(raw, "right", tight=0.92)
    photo = grade(photo, contrast=1.10, color=1.08, brightness=0.95)
    photo = vignette(photo, 0.42)
    photo = bottom_scrim(photo, start=0.50, end=1.0)

    layer = photo.convert("RGBA")
    ui = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(ui)

    shadow_text(d, (W // 2, 58), "أصالة  ·  إصدار جديد", font("kufi", 22), GOLD)
    shadow_text(d, (W // 2, 720), "كمّل البيت", font("amiri_b", 68), CREAM)
    shadow_text(d, (W // 2, 786), "الكلمة الناقصة في التعليق", font("plex", 24), MUTED)

    ar(d, (W // 2, 860), "وأنا من اسمي", font=font("amiri", 40), fill=CREAM, anchor="mm")

    d.rectangle([140, 892, 940, 1028], fill=(8, 6, 6, 200), outline=WINE, width=2)
    x = 210
    while x < 870:
        d.line([(x, 980), (min(x + 16, 870), 980)], fill=GOLD, width=2)
        x += 28

    ar(d, (W // 2, 1088), "يعني ما أخون الوعد", font=font("amiri_b", 38), fill=GOLD, anchor="mm")
    ar(d, (W // 2, 1154), "ومنشن شخص ما يخون الوعد", font=font("plex_m", 24), fill=MUTED, anchor="mm")

    d.rectangle([70, 1230, 1010, 1298], fill=(8, 6, 6, 220), outline=GOLD, width=1)
    ar(d, (W // 2, 1264), "اكتب الكلمة  +  منشن", font=font("plex_sb", 28), fill=CREAM, anchor="mm")

    return Image.alpha_composite(layer, ui).convert("RGB")


def save(img: Image.Image, name: str) -> Path:
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / name
    img.save(path, "PNG", optimize=True)
    return path


def main() -> None:
    p1 = save(post_one(), "01-ayy-bayt-aqwa.png")
    p2 = save(post_two(), "02-kammil-albayt.png")
    for p in (p1, p2):
        im = Image.open(p)
        print(p.name, im.size, im.mode)


if __name__ == "__main__":
    main()
