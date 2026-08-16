#!/usr/bin/env python3
"""Render Coca-Cola-Arena-style looping GIFs / MP4s for each entrance."""

from __future__ import annotations

import json
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
DATA = json.loads((ROOT / "data" / "osm-lite.json").read_text())
ROUTES = json.loads((ROOT / "data" / "routes.json").read_text())
LOGO = Image.open(ROOT / "assets" / "logo.png").convert("RGBA")

W, H = 1280, 720
FPS = 12
DRAW_FRAMES = 48
HOLD_FRAMES = 18
TOTAL = DRAW_FRAMES + HOLD_FRAMES

BG = (232, 233, 230, 255)
BLOCK = (214, 214, 210, 255)
BLOCK_SIDE = (196, 196, 191, 255)
BLOCK_TOP = (226, 226, 222, 255)
PARK = (196, 214, 186, 255)
AREA = (206, 208, 204, 255)
STREET = (255, 255, 255, 255)
MAIN = (186, 198, 208, 255)
SECONDARY = (205, 212, 218, 255)
PATH_GLOW = (255, 80, 80, 70)
PATH = (220, 20, 30, 255)
PATH_CORE = (255, 230, 230, 255)
PIN_RED = (196, 16, 28, 255)
INK = (42, 45, 52, 255)
MUTED = (90, 96, 104, 255)
THEATER_FILL = (48, 48, 48, 255)

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_AR = "/usr/share/fonts/truetype/noto/NotoNaskhArabic-Regular.ttf"
FONT_AR_B = "/usr/share/fonts/truetype/noto/NotoNaskhArabic-Bold.ttf"

THEATER = DATA["theater"]
LAT0 = THEATER["lat"]
LON0 = THEATER["lon"]
COS = math.cos(math.radians(LAT0))
ROT = math.radians(38)


def meters(lon, lat):
    x = (lon - LON0) * 111320 * COS
    y = (lat - LAT0) * 110540
    rx = x * math.cos(ROT) - y * math.sin(ROT)
    ry = x * math.sin(ROT) + y * math.cos(ROT)
    return rx, ry


def font(path, size):
    return ImageFont.truetype(path, size)


def reshape_ar(text):
    try:
        import arabic_reshaper
        from bidi.algorithm import get_display

        return get_display(arabic_reshaper.reshape(text))
    except Exception:
        return text


def frame_for(path_pts):
    xs, ys = zip(*(meters(p["lon"], p["lat"]) for p in path_pts))
    tx, ty = meters(THEATER["lon"], THEATER["lat"])
    minx, maxx = min(xs + (tx,)), max(xs + (tx,))
    miny, maxy = min(ys + (ty,)), max(ys + (ty,))
    pad = 380
    return minx - pad, maxx + pad, miny - pad, maxy + pad


def projector(bounds):
    minx, maxx, miny, maxy = bounds
    tilt = 0.58
    sx = (W - 80) / max(maxx - minx, 1)
    sy = (H - 90) / max((maxy - miny) * tilt, 1)
    scale = min(sx, sy)

    def proj(lon, lat, z=0):
        x, y = meters(lon, lat)
        px = 40 + (x - minx) * scale
        py = H - 50 - (y - miny) * scale * tilt - z
        return px, py

    return proj, scale


def polyline(draw, pts, fill, width, proj):
    if len(pts) < 2:
        return
    xy = [proj(p["lon"], p["lat"]) if isinstance(p, dict) else proj(*p[:2]) for p in pts]
    draw.line(xy, fill=fill, width=width, joint="curve")


def poly(draw, pts, fill, proj, z=0):
    if len(pts) < 3:
        return
    xy = [proj(p[0], p[1], z) for p in pts]
    draw.polygon(xy, fill=fill)


def draw_building(draw, pts, levels, proj, scale, kind="building"):
    h = min(28, 5 + levels * 3.2)
    if kind == "theatre":
        top, side, body = (36, 36, 36, 255), (24, 24, 24, 255), (28, 28, 28, 255)
        h = 34
    elif kind == "stadium":
        top, side, body = (168, 196, 164, 255), (140, 170, 138, 255), (152, 182, 148, 255)
        h = 26
    else:
        top, side, body = BLOCK_TOP, BLOCK_SIDE, BLOCK
    base = [proj(p[0], p[1], 0) for p in pts]
    lifted = [proj(p[0], p[1], h) for p in pts]
    # simple south-east extrusion faces
    for i in range(len(pts)):
        a, b = base[i], base[(i + 1) % len(pts)]
        c, d = lifted[(i + 1) % len(pts)], lifted[i]
        # only draw faces that go downward on screen
        if (a[1] + b[1]) / 2 > (c[1] + d[1]) / 2:
            draw.polygon([a, b, c, d], fill=side if a[0] < b[0] else body)
    draw.polygon(lifted, fill=top)


def make_pin(pulse=0.0):
    size = int(118 + pulse * 8)
    pin = Image.new("RGBA", (size, size + 22), (0, 0, 0, 0))
    d = ImageDraw.Draw(pin)
    r = size // 2
    d.ellipse((6, 8, size - 6, size - 4), fill=(0, 0, 0, 45))
    d.ellipse((4, 2, size - 4, size - 6), fill=PIN_RED)
    d.ellipse((14, 12, size - 14, size - 16), fill=(255, 255, 255, 255))
    logo = LOGO.copy()
    inner = size - 36
    logo.thumbnail((inner, inner), Image.Resampling.LANCZOS)
    lx = (size - logo.width) // 2
    ly = (size - 8 - logo.height) // 2
    pin.alpha_composite(logo, (lx, ly))
    # pointer
    d.polygon([(r - 10, size - 18), (r + 10, size - 18), (r, size + 16)], fill=PIN_RED)
    return pin


def car_icon(angle):
    img = Image.new("RGBA", (44, 24), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((1, 5, 42, 21), radius=6, fill=(200, 18, 28, 255))
    d.rounded_rectangle((10, 2, 30, 12), radius=4, fill=(255, 210, 210, 255))
    d.ellipse((6, 16, 16, 24), fill=(40, 40, 40, 255))
    d.ellipse((28, 16, 38, 24), fill=(40, 40, 40, 255))
    return img.rotate(-math.degrees(angle), expand=True, resample=Image.Resampling.BICUBIC)


def draw_base(proj, scale):
    im = Image.new("RGBA", (W, H), BG)
    d = ImageDraw.Draw(im, "RGBA")
    # subtle vignette grid
    for g in DATA["greens"]:
        poly(d, g["pts"], PARK, proj)
    for a in DATA["areas"]:
        poly(d, a["pts"], AREA, proj)

    # roads under buildings
    order = {
        "motorway": 0,
        "trunk": 1,
        "primary": 2,
        "secondary": 3,
        "tertiary": 4,
        "unclassified": 5,
        "residential": 6,
        "service": 7,
        "footway": 9,
    }
    roads = sorted(DATA["highways"], key=lambda r: -order.get(r.get("highway"), 8))
    for r in roads:
        hw = r.get("highway") or ""
        if hw in ("footway", "path", "steps"):
            continue
        pts = [{"lon": p[0], "lat": p[1]} for p in r["pts"]]
        if hw in ("primary", "trunk", "motorway"):
            polyline(d, pts, MAIN, 11, proj)
            polyline(d, pts, (232, 236, 240, 255), 3, proj)
        elif hw == "secondary":
            polyline(d, pts, SECONDARY, 8, proj)
        elif hw in ("tertiary", "tertiary_link"):
            polyline(d, pts, STREET, 6, proj)
        else:
            polyline(d, pts, STREET, 4, proj)

    buildings = sorted(DATA["buildings"], key=lambda b: meters(b["pts"][0][0], b["pts"][0][1])[1])
    for b in buildings:
        if len(b["pts"]) < 3:
            continue
        draw_building(d, b["pts"], b.get("levels") or 2, proj, scale, b.get("kind") or "building")

    # landmark labels
    f = font(FONT_B, 15)
    fa = font(FONT_AR, 16)
    for poi in DATA["pois"]:
        if poi["id"] == "mohammed-abdo-arena":
            continue
        x, y = proj(poi["lon"], poi["lat"])
        if not (-40 <= x <= W + 40 and -40 <= y <= H + 40):
            continue
        label = poi["name_en"]
        d.text((x + 1, y + 1), label, font=f, fill=(255, 255, 255, 200))
        d.text((x, y), label, font=f, fill=INK)
        d.text((x, y + 16), reshape_ar(poi["name_ar"]), font=fa, fill=MUTED)
    return im


def point_at(path, t):
    t = max(0.0, min(1.0, t))
    if t <= 0:
        return path[0], 0.0
    segs = []
    total = 0.0
    for a, b in zip(path, path[1:]):
        dx, dy = b["lon"] - a["lon"], b["lat"] - a["lat"]
        l = math.hypot(dx, dy) or 1e-12
        segs.append((a, b, l))
        total += l
    target = total * t
    acc = 0.0
    for a, b, l in segs:
        if acc + l >= target:
            u = (target - acc) / l
            lon = a["lon"] + (b["lon"] - a["lon"]) * u
            lat = a["lat"] + (b["lat"] - a["lat"]) * u
            ang = math.atan2(b["lat"] - a["lat"], b["lon"] - a["lon"])
            return {"lon": lon, "lat": lat}, ang
        acc += l
    a, b, _ = segs[-1]
    return path[-1], math.atan2(b["lat"] - a["lat"], b["lon"] - a["lon"])


def draw_hud(im, route, frame_i):
    d = ImageDraw.Draw(im, "RGBA")
    d.rounded_rectangle((24, 18, 520, 100), radius=16, fill=(255, 255, 255, 235))
    d.text((44, 32), "Mohammed Abdo Arena", font=font(FONT_B, 20), fill=INK)
    d.text((44, 62), route["title_en"], font=font(FONT_B, 16), fill=PIN_RED)

    d.rounded_rectangle((W - 430, 18, W - 24, 100), radius=16, fill=(255, 255, 255, 235))
    ar_title = reshape_ar("مسرح محمد عبده")
    ar_sub = reshape_ar(route["title_ar"])
    d.text((W - 50, 32), ar_title, font=font(FONT_AR_B, 22), fill=INK, anchor="ra")
    d.text((W - 50, 64), ar_sub, font=font(FONT_AR_B, 18), fill=PIN_RED, anchor="ra")

    y = H - 92
    d.rounded_rectangle((24, y, W - 24, H - 18), radius=14, fill=(255, 255, 255, 235))
    x = 44
    slot = min(400, (W - 80) // max(1, len(route["markers"])))
    for m in route["markers"]:
        d.ellipse((x, y + 16, x + 28, y + 44), fill=(70, 140, 210, 255))
        d.text((x + 14, y + 30), str(m["n"]), font=font(FONT_B, 14), fill=(255, 255, 255, 255), anchor="mm")
        d.text((x + 36, y + 16), m["en"], font=font(FONT, 13), fill=INK)
        d.text((x + 36, y + 36), reshape_ar(m["ar"]), font=font(FONT_AR, 15), fill=MUTED)
        x += slot


def render_route(route):
    path = route["path"]
    bounds = frame_for(path)
    proj, scale = projector(bounds)
    base = draw_base(proj, scale)
    frames = []
    for i in range(TOTAL):
        if i < DRAW_FRAMES:
            t = (i / (DRAW_FRAMES - 1)) ** 0.85
        else:
            t = 1.0
        im = base.copy()
        d = ImageDraw.Draw(im, "RGBA")
        n = max(2, int(round((len(path) - 1) * t)) + 1)
        drawn = path[:n]
        polyline(d, drawn, PATH_GLOW, 18, proj)
        polyline(d, drawn, PATH, 8, proj)
        polyline(d, drawn, PATH_CORE, 2, proj)

        for m in route["markers"]:
            mx, my = proj(m["lon"], m["lat"])
            d.ellipse((mx - 13, my - 13, mx + 13, my + 13), fill=(70, 140, 210, 255), outline=(255, 255, 255, 255), width=3)
            d.text((mx - 4, my - 8), str(m["n"]), font=font(FONT_B, 14), fill=(255, 255, 255, 255))

        pos, ang = point_at(path, t)
        cx, cy = proj(pos["lon"], pos["lat"])
        # convert lon/lat angle into screen angle
        p2, _ = point_at(path, min(1.0, t + 0.01))
        sx2, sy2 = proj(p2["lon"], p2["lat"])
        screen_ang = math.atan2(sy2 - cy, sx2 - cx)
        car = car_icon(screen_ang)
        im.alpha_composite(car, (int(cx - car.width / 2), int(cy - car.height / 2)))

        pulse = 0.5 + 0.5 * math.sin((i / FPS) * 4)
        pin = make_pin(pulse if t > 0.92 else 0)
        px, py = proj(THEATER["lon"], THEATER["lat"])
        im.alpha_composite(pin, (int(px - pin.width / 2), int(py - pin.height + 8)))

        draw_hud(im, route, i)
        frames.append(im.convert("RGB"))
    return frames


def save_gif(frames, path: Path):
    tmp = path.parent / f".frames-{path.stem}"
    if tmp.exists():
        for f in tmp.glob("*"):
            f.unlink()
        tmp.rmdir()
    tmp.mkdir()
    for i, fr in enumerate(frames):
        fr.save(tmp / f"{i:03d}.png")
    import subprocess

    palette = tmp / "palette.png"
    subprocess.run(
        ["ffmpeg", "-y", "-framerate", str(FPS), "-i", str(tmp / "%03d.png"), "-vf", "palettegen=stats_mode=full", str(palette)],
        check=True,
        capture_output=True,
    )
    subprocess.run(
        [
            "ffmpeg", "-y", "-framerate", str(FPS), "-i", str(tmp / "%03d.png"), "-i", str(palette),
            "-lavfi", "paletteuse=dither=bayer:bayer_scale=3",
            "-loop", "0", str(path),
        ],
        check=True,
        capture_output=True,
    )
    for f in tmp.glob("*"):
        f.unlink()
    tmp.rmdir()


def save_mp4(frames, mp4_path: Path):
    import subprocess, tempfile, os

    tmp = mp4_path.parent / f".mp4-{mp4_path.stem}"
    tmp.mkdir(exist_ok=True)
    for i, fr in enumerate(frames):
        fr.save(tmp / f"{i:03d}.png")
    subprocess.run(
        [
            "ffmpeg", "-y", "-framerate", str(FPS), "-i", str(tmp / "%03d.png"),
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
            str(mp4_path),
        ],
        check=True,
        capture_output=True,
    )
    for f in tmp.glob("*"):
        f.unlink()
    tmp.rmdir()


def main():
    out_gif = ROOT / "gifs"
    out_mp4 = ROOT / "videos"
    out_gif.mkdir(exist_ok=True)
    out_mp4.mkdir(exist_ok=True)
    try:
        import arabic_reshaper  # noqa: F401
        from bidi.algorithm import get_display  # noqa: F401
    except Exception:
        import subprocess, sys

        subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "arabic-reshaper", "python-bidi"])

    for route in ROUTES["routes"]:
        print("rendering", route["id"])
        frames = render_route(route)
        still = ROOT / "previews" / f"{route['id']}.png"
        still.parent.mkdir(exist_ok=True)
        frames[-1].save(still)
        gif = out_gif / f"{route['id']}.gif"
        save_gif(frames, gif)
        print("  gif", gif, gif.stat().st_size)
        mp4 = out_mp4 / f"{route['id']}.mp4"
        save_mp4(frames, mp4)
        print("  mp4", mp4, mp4.stat().st_size)


if __name__ == "__main__":
    main()
