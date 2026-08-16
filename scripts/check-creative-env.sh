#!/usr/bin/env bash
# Smoke-test the multimedia workstation. Exit 1 if a required tool is missing.
set -euo pipefail

fail=0
need_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "MISSING command: $1" >&2
    fail=1
  else
    echo "ok  $1  $($1 ${2:---version} 2>&1 | head -1)"
  fi
}

need_cmd ffmpeg -version
need_cmd ffprobe -version
need_cmd convert -version
need_cmd identify -version
need_cmd sox --version
need_cmd gifsicle --version
need_cmd optipng -v
need_cmd pngquant --version
need_cmd potrace --version
need_cmd rsvg-convert --version
need_cmd mediainfo --version
need_cmd python3 -V
need_cmd node -v

python3 - <<'PY' || fail=1
from PIL import Image, ImageDraw, ImageFont, features
import arabic_reshaper
from bidi.algorithm import get_display

assert features.check("raqm"), "Pillow raqm (HarfBuzz/FriBidi) is required for Arabic"
font_paths = [
    "/usr/share/fonts/truetype/ibm-plex/IBMPlexSansArabic-Regular.ttf",
    "/usr/share/fonts/opentype/fonts-hosny-amiri/Amiri-Regular.ttf",
    "/usr/share/fonts/truetype/noto/NotoNaskhArabic-Regular.ttf",
    "/usr/share/fonts/truetype/scheherazade/Scheherazade-Regular.ttf",
]
missing = [p for p in font_paths if __import__("os").path.exists(p) is False]
if missing:
    raise SystemExit("MISSING fonts:\n" + "\n".join(missing))

text = "تصميم عربي"
font = ImageFont.truetype(font_paths[0], 48)
img = Image.new("RGB", (400, 120), "#0a0a0a")
draw = ImageDraw.Draw(img)
draw.text((24, 32), text, font=font, fill="#e8d5a3", language="ar", direction="rtl", anchor="lt")
shaped = arabic_reshaper.reshape("تصميم")
print("ok  pillow raqm + arabic fonts")
print("ok  arabic-reshaper", shaped)
print("ok  python-bidi", get_display(shaped))
PY

echo "---- fonts ----"
fc-list :lang=ar family | sort -u | head -20

if [ "$fail" -ne 0 ]; then
  echo "creative environment check FAILED" >&2
  exit 1
fi
echo "creative environment check PASSED"
