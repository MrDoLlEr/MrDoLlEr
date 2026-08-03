# روتانا تيونز — فيديو برومو | Rotana Tunes promo

A ~34 second promo film for the Rotana Tunes music app, generated end to end from
this repository: Arabic voice-over, cinematic plates, in-app screens, the edit,
the score and the final master. No editing timeline app and no licensed stock.

> **Concept work.** Rotana did not supply brand assets, so the logo mark, the app
> screens and the copy here are an original interpretation. Swap `assets/plates`,
> `ui.app_icon` and `ui.wordmark` for the official kit and re-run the build.

## Output

| File | Use |
| --- | --- |
| `out/rotana_tunes_promo_9x16.mp4` | 1080×1920 master — Reels, TikTok, Shorts, Snap |
| `out/rotana_tunes_promo_16x9.mp4` | 1920×1080 re-frame with a blurred fill — YouTube, pre-roll |

## The idea behind the cut

Every cut, caption and musical hit is derived from the voice-over rather than
placed by hand. `vo.py` synthesises the read, then recovers where each word lands
by combining the phoneme string espeak produces (which gives an exact
phoneme-count per word) with the quietest point of the audio inside a small
search window. `storyboard.py` reads those word times and builds the shot list
from them, so the picture changes on the word that earns the change:

| Voice-over | On screen |
| --- | --- |
| في كل لحظة… في داخلك أغنية | rooftop listener → headphones → waveform |
| روتانا تيونز… كل الموسيقى العربية في مكان واحد | logo slam, stage, festival crowd |
| ملايين الأغاني… من الطرب الأصيل إلى أحدث الإصدارات | parallax wall of covers → oud → studio |
| قوائم تشغيل على مزاجك… وجودة صوت تضعك في قلب الحفلة | the app in hand → crowd with a live spectrum |
| حمّل أغانيك واستمع بدون إنترنت… وبدون إعلانات | now-playing screen → night drive → headphones |
| روتانا تيونز… حمّل التطبيق الآن | end card, badges, gold sweep |

Re-word a line in `script_data.py` and the film re-times itself.

## Craft notes

- **Camera.** Each still plate is flown with a virtual camera (`fx.camera`) —
  push, drift, roll — plus a low-frequency handheld drift so nothing sits still.
  When a move is fast enough to strobe, the frame is accumulated from several
  sub-frame camera positions, which is real motion blur rather than a smear.
- **Transitions.** Whip pan, flash cut, zoom-blur dissolve, digital tear with an
  RGB split, a slide, and a light-leak wash into the end card.
- **Typography.** Pillow is built against Raqm here, so HarfBuzz shapes the
  Arabic and FriBidi orders it. Words spring in one at a time on the syllable
  that says them, over a gold rule that wipes in underneath.
- **App screens.** Drawn, not generated, so the Arabic is real text and the
  pixels stay sharp when the camera pushes into the phone. The screen is
  composited into a plate that was shot dead-on with the display switched off.
- **Score.** `music.py` synthesises the whole bed from oscillators and noise: D
  Hijaz at 96 BPM, kick and darbuka, sub bass, a plucked motif, pads, risers and
  impacts placed on the cut list the storyboard exports.
- **Mix.** The voice runs through a high-pass, a presence lift and two
  compressors. The bed is ducked broadband and ducked harder across 850–5200 Hz,
  the band the voice occupies, so it keeps weight without covering the words.
- **Finish.** Filmic grade, bloom, red-biased halation, chromatic aberration that
  opens up during transitions, vignette and luminance-weighted grain.

## Build

```bash
pip install -r requirements.txt
python3 -m piper.download_voices ar_JO-kareem-medium   # into ~/piper_voices
python3 build.py                # full build
python3 build.py --revoice      # re-synthesise the voice-over first
python3 build.py --preview      # every 3rd frame at half size, for a fast look
```

Rendering is spread across all cores; on a 4-core machine a full pass is a few
minutes. Intermediates land in `build/`, finals in `out/`.

## Verifying the result

`verify.py` re-transcribes the finished mix with Whisper and compares it word by
word against the script. It is how the voice/music balance was set: if the
transcript degrades against the dry voice-over, the bed is too loud.

```bash
python3 verify.py
```

## Layout

```
config.py        canvas, palette, fonts, paths
script_data.py   the copy: voice-over lines and caption beats
vo.py            speech synthesis and word-level timing recovery
artext.py        Arabic shaping, per-word layout, glow
ui.py            logo, store badges, the two in-app screens
fx.py            camera, grade, bloom, grain, transitions
storyboard.py    the edit: shots, cuts, kinetic type, master frame()
music.py         the synthesised score
mix.py           voice sweetening, ducking, limiter
build.py         orchestrates everything and encodes both masters
verify.py        transcription check on the final mix
```
