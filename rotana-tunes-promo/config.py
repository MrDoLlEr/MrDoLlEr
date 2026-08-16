"""Global render settings, brand palette and font resolution."""

from pathlib import Path

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"
PLATES = ASSETS / "plates"
BUILD = ROOT / "build"
OUT = ROOT / "out"

for _d in (ASSETS, PLATES, BUILD, OUT):
    _d.mkdir(parents=True, exist_ok=True)

# Vertical master. The 16:9 variant is derived by re-framing at encode time.
W, H = 1080, 1920
FPS = 30
SAMPLE_RATE = 48000

# Supersampling factor used when rasterising type and vector art, so that
# rotation / scaling in the camera stage never shows stair-stepped edges.
SS = 2

# Brand palette: Rotana crimson over near-black, with a warm gold accent.
BLACK = (6, 5, 8)
INK = (12, 10, 14)
CRIMSON = (214, 26, 46)
CRIMSON_DEEP = (126, 12, 28)
GOLD = (232, 184, 96)
GOLD_BRIGHT = (255, 221, 154)
WHITE = (250, 248, 245)
MUTED = (168, 160, 170)

FONT_DIR = Path("/usr/share/fonts/truetype/noto")
FONT_DISPLAY = FONT_DIR / "NotoKufiArabic-Bold.ttf"
FONT_DISPLAY_LIGHT = FONT_DIR / "NotoKufiArabic-Regular.ttf"
FONT_BODY = FONT_DIR / "NotoSansArabic-Bold.ttf"
FONT_BODY_LIGHT = FONT_DIR / "NotoSansArabic-Regular.ttf"
FONT_LATIN = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")

VOICE_MODEL = Path.home() / "piper_voices" / "ar_JO-kareem-medium.onnx"
