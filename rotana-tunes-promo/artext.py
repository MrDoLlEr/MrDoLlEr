"""Arabic typography helpers.

Pillow is built against Raqm here, so HarfBuzz does the shaping and FriBidi the
bidi reordering: passing direction="rtl" is enough to get correctly joined
Arabic glyphs. Every helper returns a transparent RGBA layer plus its metrics so
the animation stage can move words independently.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from PIL import Image, ImageDraw, ImageFilter, ImageFont

RTL_KW = dict(direction="rtl", language="ar", features=["liga", "calt", "kern", "mark"])


@lru_cache(maxsize=64)
def font(path: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(path), size)


def measure(text: str, f: ImageFont.FreeTypeFont, rtl: bool = True) -> tuple[int, int, int, int]:
    kw = RTL_KW if rtl else {}
    return f.getbbox(text, **kw)


def text_layer(
    text: str,
    f: ImageFont.FreeTypeFont,
    fill=(255, 255, 255, 255),
    rtl: bool = True,
    pad: int = 28,
    stroke: int = 0,
    stroke_fill=(0, 0, 0, 255),
) -> Image.Image:
    """Rasterise one run of text onto a tightly cropped transparent layer."""
    kw = RTL_KW if rtl else {}
    x0, y0, x1, y1 = f.getbbox(text, stroke_width=stroke, **kw)
    w, h = max(1, x1 - x0) + pad * 2, max(1, y1 - y0) + pad * 2
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.text(
        (pad - x0, pad - y0),
        text,
        font=f,
        fill=fill,
        stroke_width=stroke,
        stroke_fill=stroke_fill,
        **kw,
    )
    return img


def glow(layer: Image.Image, radius: int, strength: float, tint=None) -> Image.Image:
    """Additive bloom behind a text layer."""
    a = layer.split()[-1].filter(ImageFilter.GaussianBlur(radius))
    if tint is None:
        base = layer.copy()
        base.putalpha(a.point(lambda v: int(v * strength)))
        return base
    g = Image.new("RGBA", layer.size, tuple(tint) + (0,))
    g.putalpha(a.point(lambda v: int(min(255, v * strength))))
    return g


@dataclass
class Word:
    text: str
    layer: Image.Image
    x: int  # left edge inside the line box
    y: int
    w: int
    h: int


@dataclass
class Line:
    words: list[Word]
    width: int
    height: int


def layout_line(
    words: list[str],
    f: ImageFont.FreeTypeFont,
    fill=(255, 255, 255, 255),
    space: float = 0.34,
    stroke: int = 0,
    stroke_fill=(0, 0, 0, 220),
    pad: int = 30,
) -> Line:
    """Lay a list of words out right-to-left, each on its own layer.

    Words are shaped in isolation. Arabic letters never join across a space, so
    isolating them does not change any glyph forms.
    """
    layers = [text_layer(w, f, fill, pad=pad, stroke=stroke, stroke_fill=stroke_fill) for w in words]
    gap = int(f.size * space)
    widths = [lay.width - pad * 2 for lay in layers]
    height = max(lay.height for lay in layers)
    total = sum(widths) + gap * (len(words) - 1)

    out: list[Word] = []
    cursor = total  # start at the right edge
    for text, lay, w in zip(words, layers, widths):
        cursor -= w
        out.append(Word(text, lay, cursor - pad, 0, w, lay.height))
        cursor -= gap
    return Line(out, total, height)


def wrap_lines(
    words: list[str], f: ImageFont.FreeTypeFont, max_width: int, **kw
) -> list[Line]:
    """Greedy RTL wrap into lines that fit `max_width`."""
    lines, current = [], []
    for w in words:
        trial = current + [w]
        if current and layout_line(trial, f, **kw).width > max_width:
            lines.append(layout_line(current, f, **kw))
            current = [w]
        else:
            current = trial
    if current:
        lines.append(layout_line(current, f, **kw))
    return lines
