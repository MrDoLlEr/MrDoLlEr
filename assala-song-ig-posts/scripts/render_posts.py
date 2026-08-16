#!/usr/bin/env python3
"""Assala — أصالة. Instagram 4:5 stills.

Full-bleed official Rotana portrait. Type sits on the garment as
editorial ink — no boxes, no scrim, no fake studio panel.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFont

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "assets" / "source"
OUT = ROOT / "exports"
W, H = 1080, 1350

FONTS = {
    "amiri": "/usr/share/fonts/opentype/fonts-hosny-amiri/Amiri-Regular.ttf",
    "amiri_b": "/usr/share/fonts/opentype/fonts-hosny-amiri/Amiri-Bold.ttf",
    "plex_m": "/usr/share/fonts/truetype/ibm-plex/IBMPlexSansArabic-Medium.ttf",
    "kufi": "/usr/share/fonts/truetype/noto/NotoKufiArabic-Regular.ttf",
}

GOLD = (138, 98, 42)
INK = (36, 22, 16)
SOFT = (72, 48, 36)


def fnt(key: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONTS[key], size)


def ar(draw, xy, text, **kwargs):
    kwargs.setdefault("language", "ar")
    kwargs.setdefault("direction", "rtl")
    draw.text(xy, text, **kwargs)


def to_rgb(im: Image.Image) -> Image.Image:
    if im.mode == "P":
        im = im.convert("RGBA")
    if im.mode == "RGBA":
        bg = Image.new("RGB", im.size, (32, 28, 30))
        bg.paste(im, mask=im.split()[-1])
        return bg
    return im.convert("RGB")


def bleed(scale: float = 1.0, up: float = 0.08) -> Image.Image:
    im = to_rgb(Image.open(SRC / "rotana-portrait.png"))
    im = ImageEnhance.Contrast(im).enhance(1.05)
    im = ImageEnhance.Color(im).enhance(1.04)
    tw, th = im.size
    if scale > 1:
        nw, nh = int(tw / scale), int(th / scale)
        left = (tw - nw) // 2
        top = int((th - nh) * up)
        im = im.crop((left, top, left + nw, top + nh))
        tw, th = im.size
    nw = int(th * 4 / 5)
    left = (tw - nw) // 2
    im = im.crop((left, 0, left + nw, th))
    return im.resize((W, H), Image.Resampling.LANCZOS)


def post_one() -> Image.Image:
    img = bleed(1.02)
    d = ImageDraw.Draw(img)
    ar(d, (W // 2, 48), "أصالة", font=fnt("kufi", 20), fill=GOLD, anchor="mm")
    ar(d, (W // 2, 1168), "أي بيت أقوى؟", font=fnt("amiri_b", 56), fill=INK, anchor="mm")
    d.line([(430, 1216), (650, 1216)], fill=GOLD, width=1)
    ar(d, (W // 2, 1264), "١  ما أخون الوعد     ·     ٢  صفر بالمية", font=fnt("amiri", 28), fill=INK, anchor="mm")
    ar(d, (W // 2, 1310), "علّق بالرقم", font=fnt("plex_m", 16), fill=SOFT, anchor="mm")
    return img


def post_two() -> Image.Image:
    img = bleed(1.20, up=0.06)
    d = ImageDraw.Draw(img)
    ar(d, (W // 2, 48), "أصالة", font=fnt("kufi", 20), fill=GOLD, anchor="mm")
    ar(d, (W // 2, 1176), "كمّل البيت", font=fnt("amiri_b", 52), fill=INK, anchor="mm")
    ar(d, (W // 2, 1232), "وأنا من اسمي", font=fnt("amiri", 30), fill=INK, anchor="mm")
    d.line([(340, 1268), (740, 1268)], fill=GOLD, width=2)
    ar(d, (W // 2, 1312), "اكتب الكلمة  ·  منشن", font=fnt("plex_m", 16), fill=SOFT, anchor="mm")
    return img


def save(img: Image.Image, name: str) -> Path:
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / name
    img.save(path, "PNG", optimize=True)
    return path


def main() -> None:
    for p in (save(post_one(), "01-ayy-bayt-aqwa.png"), save(post_two(), "02-kammil-albayt.png")):
        print(p.name, Image.open(p).size)


if __name__ == "__main__":
    main()
