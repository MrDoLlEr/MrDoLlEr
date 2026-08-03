"""Brand mark, store badges and the in-app screens shown on the phone.

The phone UI is drawn rather than generated so the Arabic reads correctly and
the pixels stay crisp when the camera pushes in.
"""

from __future__ import annotations

import math
from functools import lru_cache

from PIL import Image, ImageDraw, ImageFilter

import artext
from config import (
    BLACK,
    CRIMSON,
    CRIMSON_DEEP,
    FONT_BODY,
    FONT_BODY_LIGHT,
    FONT_DISPLAY,
    FONT_LATIN,
    GOLD,
    GOLD_BRIGHT,
    MUTED,
    PLATES,
    WHITE,
)

SS = 2  # draw at 2x then downsample


def _squircle_mask(size: int, radius_ratio: float = 0.30) -> Image.Image:
    m = Image.new("L", (size, size), 0)
    ImageDraw.Draw(m).rounded_rectangle(
        (0, 0, size - 1, size - 1), radius=int(size * radius_ratio), fill=255
    )
    return m


def _linear_gradient(size: tuple[int, int], c0, c1, angle: float = 55.0) -> Image.Image:
    w, h = size
    grad = Image.new("RGB", (w, h))
    px = grad.load()
    th = math.radians(angle)
    dx, dy = math.cos(th), math.sin(th)
    norm = abs(dx) * w + abs(dy) * h
    for y in range(h):
        for x in range(w):
            t = ((x * dx + y * dy) + (w if dx < 0 else 0) + (h if dy < 0 else 0)) / norm
            t = min(1.0, max(0.0, t))
            px[x, y] = (
                int(c0[0] + (c1[0] - c0[0]) * t),
                int(c0[1] + (c1[1] - c0[1]) * t),
                int(c0[2] + (c1[2] - c0[2]) * t),
            )
    return grad


@lru_cache(maxsize=8)
def app_icon(size: int = 320) -> Image.Image:
    """Crimson-to-gold squircle holding an equaliser glyph."""
    s = size * SS
    icon = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    grad = _linear_gradient((s, s), CRIMSON_DEEP, CRIMSON, 60).convert("RGBA")
    grad.putalpha(_squircle_mask(s))
    icon.alpha_composite(grad)

    sheen = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    ImageDraw.Draw(sheen).ellipse(
        (-s * 0.35, -s * 0.75, s * 1.05, s * 0.42), fill=(255, 255, 255, 46)
    )
    sheen = sheen.filter(ImageFilter.GaussianBlur(s * 0.05))
    sheen.putalpha(Image.composite(sheen.split()[-1], Image.new("L", (s, s), 0), _squircle_mask(s)))
    icon.alpha_composite(sheen)

    bars = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(bars)
    heights = [0.30, 0.56, 0.86, 0.62, 0.38]
    bw = s * 0.072
    gap = s * 0.052
    total = len(heights) * bw + (len(heights) - 1) * gap
    x = (s - total) / 2
    cy = s * 0.53
    for i, hh in enumerate(heights):
        bh = s * 0.52 * hh
        t = i / (len(heights) - 1)
        col = tuple(int(GOLD_BRIGHT[j] + (WHITE[j] - GOLD_BRIGHT[j]) * abs(t - 0.5) * 2) for j in range(3))
        d.rounded_rectangle(
            (x, cy - bh / 2, x + bw, cy + bh / 2), radius=bw / 2, fill=col + (255,)
        )
        x += bw + gap
    glow = bars.filter(ImageFilter.GaussianBlur(s * 0.03))
    icon.alpha_composite(glow)
    icon.alpha_composite(bars)

    ring = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    ImageDraw.Draw(ring).rounded_rectangle(
        (s * 0.012, s * 0.012, s * 0.988, s * 0.988),
        radius=int(s * 0.30),
        outline=GOLD + (150,),
        width=max(2, int(s * 0.008)),
    )
    icon.alpha_composite(ring)
    return icon.resize((size, size), Image.LANCZOS)


@lru_cache(maxsize=8)
def wordmark(height: int = 150, latin: bool = True) -> Image.Image:
    """Arabic logotype with a letterspaced Latin lockup underneath."""
    f_ar = artext.font(FONT_DISPLAY, height)
    ar = artext.text_layer("روتانا تيونز", f_ar, WHITE + (255,), pad=int(height * 0.25))
    if not latin:
        return ar
    f_lat = artext.font(FONT_LATIN, max(12, int(height * 0.235)))
    lat = artext.text_layer(
        " ".join("ROTANA TUNES"), f_lat, GOLD + (232,), rtl=False, pad=int(height * 0.18)
    )
    w = max(ar.width, lat.width)
    out = Image.new("RGBA", (w, ar.height + lat.height - int(height * 0.16)), (0, 0, 0, 0))
    out.alpha_composite(ar, ((w - ar.width) // 2, 0))
    out.alpha_composite(lat, ((w - lat.width) // 2, ar.height - int(height * 0.16)))
    return out


@lru_cache(maxsize=4)
def logo_lockup(icon_size: int = 190) -> Image.Image:
    """Icon above the wordmark: the end-card lockup."""
    icon = app_icon(icon_size)
    mark = wordmark(int(icon_size * 0.62))
    gap = int(icon_size * 0.30)
    w = max(icon.width, mark.width)
    out = Image.new("RGBA", (w, icon.height + gap + mark.height), (0, 0, 0, 0))
    out.alpha_composite(icon, ((w - icon.width) // 2, 0))
    out.alpha_composite(mark, ((w - mark.width) // 2, icon.height + gap))
    return out


@lru_cache(maxsize=32)
def _cover(name: str, size: int, radius: float = 0.10) -> Image.Image:
    """Square album art cut from one of the cinematic plates."""
    src = Image.open(PLATES / name).convert("RGB")
    side = min(src.size)
    left = (src.width - side) // 2
    top = int((src.height - side) * 0.32)
    art = src.crop((left, top, left + side, top + side)).resize((size, size), Image.LANCZOS)
    art = art.convert("RGBA")
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, size - 1, size - 1), radius=int(size * radius), fill=255)
    art.putalpha(mask)
    return art


TRACKS = [
    ("ليلة العمر", "أصالة نصري", "bg_01_stage.png"),
    ("على مزاجي", "محمد عبده", "bg_07_oud.png"),
    ("نبض المدينة", "بلقيس", "bg_08_studio.png"),
    ("سهرة الخليج", "راشد الماجد", "bg_09_crowd.png"),
]

PLAYLISTS = [
    ("طرب زمان", "٨٤ أغنية", "bg_07_oud.png"),
    ("خليجي اليوم", "١٢٠ أغنية", "bg_09_crowd.png"),
    ("مزاجك الليلة", "٦٢ أغنية", "bg_03_listener.png"),
    ("أحدث الإصدارات", "يُحدَّث يومياً", "bg_08_studio.png"),
]


@lru_cache(maxsize=4)
def _now_playing_base(size: tuple[int, int] = (720, 1560)) -> tuple[Image.Image, dict]:
    """Everything on the now-playing screen that never moves.

    The progress head and the equaliser are drawn per frame on a copy of this,
    so a 26 s render does not rebuild album art a thousand times.
    """
    w, h = size
    img = Image.new("RGB", (w, h), (10, 9, 12))

    art = _cover(TRACKS[0][2], int(w * 0.78), 0.09)
    glow = art.resize((int(w * 1.5), int(w * 1.5)), Image.LANCZOS).filter(
        ImageFilter.GaussianBlur(int(w * 0.10))
    )
    img.paste(
        Image.blend(Image.new("RGB", glow.size, (10, 9, 12)), glow.convert("RGB"), 0.42),
        (int(-w * 0.25), int(h * 0.02)),
    )
    top = Image.new("RGB", (w, h), (10, 9, 12))
    grad = Image.new("L", (1, h))
    for y in range(h):
        t = y / h
        grad.putpixel((0, y), int(255 * min(1.0, max(0.0, (t - 0.42) * 2.2))))
    img = Image.composite(top, img, grad.resize((w, h)))

    d = ImageDraw.Draw(img)
    f_small = artext.font(FONT_BODY_LIGHT, int(w * 0.036))
    f_title = artext.font(FONT_DISPLAY, int(w * 0.062))
    f_artist = artext.font(FONT_BODY_LIGHT, int(w * 0.042))

    header = artext.text_layer("تشغيل الآن", f_small, MUTED + (255,), pad=6)
    img.paste(header, (w // 2 - header.width // 2, int(h * 0.052)), header)

    ax, ay = int(w * 0.11), int(h * 0.115)
    shadow = Image.new("RGBA", (art.width + 60, art.height + 60), (0, 0, 0, 0))
    shadow.paste((0, 0, 0, 190), (30, 44, 30 + art.width, 44 + art.height), art.split()[-1])
    shadow = shadow.filter(ImageFilter.GaussianBlur(22))
    img.paste(Image.new("RGB", shadow.size, (0, 0, 0)), (ax - 30, ay - 30), shadow.split()[-1])
    img.paste(art, (ax, ay), art)

    ty = ay + art.height + int(h * 0.045)
    title = artext.text_layer(TRACKS[0][0], f_title, WHITE + (255,), pad=8)
    artist = artext.text_layer(TRACKS[0][1], f_artist, MUTED + (255,), pad=8)
    img.paste(title, (w - art.width - ax + art.width - title.width - int(w * 0.02), ty), title)
    img.paste(artist, (w - ax - artist.width + 8, ty + title.height + int(h * 0.004)), artist)

    by = ty + title.height + artist.height + int(h * 0.055)
    bx0, bx1 = int(w * 0.11), int(w * 0.89)
    f_t = artext.font(FONT_LATIN, int(w * 0.030))
    d.text((bx0, by + 22), "0:00", font=f_t, fill=MUTED)
    d.text((bx1 - 44, by + 22), "3:52", font=f_t, fill=MUTED)

    # transport controls
    cy = by + int(h * 0.075)
    d.ellipse((w / 2 - 46, cy - 46, w / 2 + 46, cy + 46), fill=CRIMSON)
    d.polygon([(w / 2 - 13, cy - 20), (w / 2 - 13, cy + 20), (w / 2 + 21, cy)], fill=WHITE)
    for sx in (w / 2 - 130, w / 2 + 130):
        for k in (-1, 1):
            ox = sx + k * 11
            sgn = 1 if sx < w / 2 else -1
            d.polygon(
                [(ox + sgn * 13, cy - 15), (ox + sgn * 13, cy + 15), (ox - sgn * 9, cy)],
                fill=(215, 210, 218),
            )

    eqy = cy + int(h * 0.062)

    # up next
    ny = eqy + int(h * 0.055)
    nx_label = artext.text_layer("التالي في القائمة", artext.font(FONT_BODY, int(w * 0.036)),
                                 WHITE + (235,), pad=6)
    img.paste(nx_label, (w - int(w * 0.11) - nx_label.width + 6, ny), nx_label)
    ny += int(h * 0.036)
    for name, artist_name, plate in TRACKS[1:4]:
        thumb = _cover(plate, int(w * 0.115), 0.22)
        img.paste(thumb, (int(w * 0.11), ny), thumb)
        t_lay = artext.text_layer(name, artext.font(FONT_BODY, int(w * 0.038)), WHITE + (245,), pad=6)
        a_lay = artext.text_layer(artist_name, artext.font(FONT_BODY_LIGHT, int(w * 0.030)),
                                  MUTED + (235,), pad=6)
        img.paste(t_lay, (w - int(w * 0.11) - t_lay.width + 6, ny + 2), t_lay)
        img.paste(a_lay, (w - int(w * 0.11) - a_lay.width + 6, ny + t_lay.height - 6), a_lay)
        ny += int(w * 0.155)

    layout = {"bar_y": by, "bar_x0": bx0, "bar_x1": bx1, "eq_y": eqy, "w": w, "h": h}
    return img, layout


def now_playing_frame(size: tuple[int, int] = (720, 1560), eq_phase: float = 0.0,
                      progress: float = 0.36, eq_gain: float = 1.0) -> Image.Image:
    """One live frame of the now-playing screen."""
    base, L = _now_playing_base(size)
    img = base.copy()
    d = ImageDraw.Draw(img)
    w, h = L["w"], L["h"]

    by, bx0, bx1 = L["bar_y"], L["bar_x0"], L["bar_x1"]
    d.rounded_rectangle((bx0, by, bx1, by + 7), radius=4, fill=(58, 54, 62))
    px = bx0 + (bx1 - bx0) * max(0.0, min(1.0, progress))
    d.rounded_rectangle((bx0, by, px, by + 7), radius=4, fill=CRIMSON)
    d.ellipse((px - 11, by - 7, px + 11, by + 15), fill=WHITE)

    eqy = L["eq_y"]
    bars = 34
    bw = (w * 0.78) / (bars * 1.75)
    x = w * 0.11
    for i in range(bars):
        a = math.sin(eq_phase * 2.4 + i * 0.55) * 0.5 + 0.5
        b = math.sin(eq_phase * 1.3 + i * 0.21) * 0.5 + 0.5
        amp = (0.22 + 0.78 * (a * 0.65 + b * 0.35)) * (0.55 + 0.45 * math.sin(i / bars * math.pi))
        bh = max(4, amp * h * 0.055 * eq_gain)
        t = i / bars
        col = tuple(int(CRIMSON[j] + (GOLD[j] - CRIMSON[j]) * t) for j in range(3))
        d.rounded_rectangle((x, eqy - bh, x + bw, eqy + bh), radius=bw / 2, fill=col)
        x += bw * 1.75
    return img


def screen_now_playing(size: tuple[int, int] = (720, 1560), eq_phase: float = 0.0,
                       progress: float = 0.36) -> Image.Image:
    return now_playing_frame(size, eq_phase, progress)


@lru_cache(maxsize=8)
def screen_library(size: tuple[int, int] = (720, 1560), highlight: float = 0.0) -> Image.Image:
    w, h = size
    img = Image.new("RGB", (w, h), (10, 9, 12))
    d = ImageDraw.Draw(img)

    d.rectangle((0, 0, w, int(h * 0.30)), fill=(18, 10, 14))
    band = Image.new("RGB", (w, int(h * 0.30)), (0, 0, 0))
    bd = ImageDraw.Draw(band)
    for y in range(band.height):
        t = 1 - y / band.height
        bd.line((0, y, w, y), fill=(int(46 * t + 10), int(10 * t + 9), int(18 * t + 12)))
    img.paste(band, (0, 0))

    head = artext.text_layer("مكتبتك", artext.font(FONT_DISPLAY, int(w * 0.070)), WHITE + (255,), pad=8)
    img.paste(head, (w - int(w * 0.10) - head.width + 8, int(h * 0.055)), head)
    sub = artext.text_layer("قوائم مختارة على مزاجك", artext.font(FONT_BODY_LIGHT, int(w * 0.038)),
                            MUTED + (255,), pad=8)
    img.paste(sub, (w - int(w * 0.10) - sub.width + 8, int(h * 0.055) + head.height - 4), sub)

    y = int(h * 0.163)
    for i, (name, count, plate) in enumerate(PLAYLISTS):
        active = abs(highlight - i) < 0.5
        card_h = int(h * 0.115)
        pad = int(w * 0.055)
        if active:
            d.rounded_rectangle((pad - 14, y - 12, w - pad + 14, y + card_h + 12),
                                radius=26, fill=(28, 18, 24))
        thumb = _cover(plate, card_h, 0.20)
        img.paste(thumb, (pad, y), thumb)
        t_lay = artext.text_layer(name, artext.font(FONT_BODY, int(w * 0.044)), WHITE + (250,), pad=6)
        c_lay = artext.text_layer(count, artext.font(FONT_BODY_LIGHT, int(w * 0.032)),
                                  MUTED + (240,), pad=6)
        img.paste(t_lay, (w - pad - t_lay.width + 6, y + int(card_h * 0.10)), t_lay)
        img.paste(c_lay, (w - pad - c_lay.width + 6, y + int(card_h * 0.10) + t_lay.height - 8), c_lay)
        y += card_h + int(h * 0.023)

    # download row, ties into the offline beat
    dy = y + int(h * 0.010)
    pad = int(w * 0.055)
    d.rounded_rectangle((pad - 14, dy - 12, w - pad + 14, dy + int(h * 0.064)),
                        radius=26, fill=(20, 16, 22))
    lab = artext.text_layer("متاح بدون إنترنت", artext.font(FONT_BODY, int(w * 0.040)),
                            GOLD_BRIGHT + (255,), pad=6)
    img.paste(lab, (w - pad - lab.width + 6, dy + int(h * 0.011)), lab)
    cx, cy = pad + int(w * 0.035), dy + int(h * 0.032)
    d.ellipse((cx - 24, cy - 24, cx + 24, cy + 24), outline=GOLD, width=3)
    d.polygon([(cx - 10, cy - 4), (cx + 10, cy - 4), (cx, cy + 11)], fill=GOLD)
    d.line((cx - 11, cy - 12, cx + 11, cy - 12), fill=GOLD, width=3)

    _mini_player(img, d, w, h)
    _tab_bar(img, d, w, h)
    return img


def _mini_player(img: Image.Image, d: ImageDraw.ImageDraw, w: int, h: int) -> None:
    bar_h = int(h * 0.070)
    top = int(h * 0.885) - bar_h - int(h * 0.012)
    pad = int(w * 0.045)
    d.rounded_rectangle((pad, top, w - pad, top + bar_h), radius=int(bar_h * 0.28),
                        fill=(26, 18, 22))
    thumb = _cover(TRACKS[0][2], int(bar_h * 0.74), 0.22)
    img.paste(thumb, (pad + int(bar_h * 0.14), top + int(bar_h * 0.13)), thumb)
    t_lay = artext.text_layer(TRACKS[0][0], artext.font(FONT_BODY, int(w * 0.036)),
                             WHITE + (250,), pad=6)
    a_lay = artext.text_layer(TRACKS[0][1], artext.font(FONT_BODY_LIGHT, int(w * 0.029)),
                             MUTED + (240,), pad=6)
    img.paste(t_lay, (w - pad - int(bar_h * 0.9) - t_lay.width, top + int(bar_h * 0.10)), t_lay)
    img.paste(a_lay, (w - pad - int(bar_h * 0.9) - a_lay.width,
                      top + int(bar_h * 0.10) + t_lay.height - 8), a_lay)
    px, py = w - pad - int(bar_h * 0.45), top + bar_h // 2
    d.ellipse((px - bar_h * 0.28, py - bar_h * 0.28, px + bar_h * 0.28, py + bar_h * 0.28),
              fill=CRIMSON)
    d.polygon([(px - bar_h * 0.08, py - bar_h * 0.12), (px - bar_h * 0.08, py + bar_h * 0.12),
               (px + bar_h * 0.13, py)], fill=WHITE)


def _tab_bar(img: Image.Image, d: ImageDraw.ImageDraw, w: int, h: int) -> None:
    top = int(h * 0.885)
    d.rectangle((0, top, w, h), fill=(13, 11, 15))
    d.line((0, top, w, top), fill=(38, 34, 40), width=2)
    tabs = [("مكتبتي", True), ("بحث", False), ("الرئيسية", False)]
    slot = w / len(tabs)
    for i, (name, active) in enumerate(tabs):
        cx = slot * (i + 0.5)
        col = CRIMSON if active else (110, 104, 116)
        cy = top + int(h * 0.030)
        if i == 0:
            d.rounded_rectangle((cx - 15, cy - 14, cx - 5, cy + 14), radius=4, fill=col)
            d.rounded_rectangle((cx - 1, cy - 14, cx + 15, cy + 14), radius=4, outline=col, width=3)
        elif i == 1:
            d.ellipse((cx - 15, cy - 15, cx + 7, cy + 7), outline=col, width=3)
            d.line((cx + 5, cy + 5, cx + 15, cy + 15), fill=col, width=3)
        else:
            d.polygon([(cx, cy - 16), (cx + 16, cy - 1), (cx - 16, cy - 1)], fill=col)
            d.rectangle((cx - 11, cy - 2, cx + 11, cy + 14), fill=col)
        lab = artext.text_layer(name, artext.font(FONT_BODY_LIGHT, int(w * 0.028)),
                                (col if active else (140, 134, 146)) + (255,), pad=4)
        img.paste(lab, (int(cx - lab.width / 2), top + int(h * 0.048)), lab)


def phone(screen: Image.Image, corner: float = 0.055, bezel: int = 16) -> Image.Image:
    """Wrap a screen render in a bezel with a rounded glass edge."""
    sw, sh = screen.size
    w, h = sw + bezel * 2, sh + bezel * 2
    body = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(body)
    r = int(w * corner)
    d.rounded_rectangle((0, 0, w - 1, h - 1), radius=r, fill=(16, 15, 18, 255))
    d.rounded_rectangle((0, 0, w - 1, h - 1), radius=r, outline=(96, 88, 78, 255), width=3)
    scr = screen.convert("RGBA")
    mask = Image.new("L", (sw, sh), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, sw - 1, sh - 1), radius=int(r * 0.86), fill=255)
    scr.putalpha(mask)
    body.alpha_composite(scr, (bezel, bezel))
    d.rounded_rectangle(
        (bezel, bezel, w - bezel - 1, h - bezel - 1), radius=int(r * 0.86),
        outline=(255, 255, 255, 26), width=2,
    )
    nw = int(sw * 0.30)
    d.rounded_rectangle(
        (w // 2 - nw // 2, bezel + 10, w // 2 + nw // 2, bezel + 10 + int(sh * 0.022)),
        radius=40, fill=(8, 8, 10, 255),
    )
    return body


def store_badge(label_top: str, label_main: str, width: int = 300) -> Image.Image:
    h = int(width * 0.30)
    img = Image.new("RGBA", (width, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 0, width - 1, h - 1), radius=int(h * 0.24),
                        fill=(18, 17, 20, 235), outline=(120, 112, 100, 220), width=2)
    f_top = artext.font(FONT_LATIN, int(h * 0.19))
    f_main = artext.font(FONT_LATIN, int(h * 0.33))
    tx = int(h * 0.78)
    d.text((tx, h * 0.20), label_top, font=f_top, fill=MUTED)
    d.text((tx, h * 0.44), label_main, font=f_main, fill=WHITE)
    cx, cy = int(h * 0.44), h // 2
    d.ellipse((cx - h * 0.24, cy - h * 0.24, cx + h * 0.24, cy + h * 0.24),
              outline=GOLD, width=2)
    d.polygon([(cx - h * 0.10, cy - h * 0.05), (cx + h * 0.10, cy - h * 0.05), (cx, cy + h * 0.12)],
              fill=GOLD)
    d.line((cx - h * 0.11, cy - h * 0.13, cx + h * 0.11, cy - h * 0.13), fill=GOLD, width=2)
    return img


def feature_pill(text: str, size: int = 46, accent=GOLD) -> Image.Image:
    """Small outlined chip used for the feature call-outs."""
    f = artext.font(FONT_BODY, size)
    lab = artext.text_layer(text, f, WHITE + (255,), pad=4)
    pad_x, pad_y = int(size * 0.95), int(size * 0.50)
    w, h = lab.width + pad_x * 2, lab.height + pad_y * 2
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 0, w - 1, h - 1), radius=h // 2, fill=(10, 8, 12, 168),
                        outline=accent + (210,), width=3)
    img.alpha_composite(lab, (pad_x, pad_y))
    return img
