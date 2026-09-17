# Rotana Music — "We're Hiring" promo

A 14-second recruitment promo for the Rotana Music website launch and the
LinkedIn vacancy announcement, built with [Remotion](https://remotion.dev).

Two compositions render from one source of truth, so copy and timing can never
drift between the two placements:

| Composition | Size | Placement |
| --- | --- | --- |
| `Promo-LinkedIn-1080x1350` | 1080 × 1350 (4:5) | LinkedIn feed |
| `Promo-Web-1920x1080` | 1920 × 1080 (16:9) | Website hero |

Both are 14.0 s at 30 fps, H.264.

## Beat sheet

| Time | Beat | Copy |
| --- | --- | --- |
| 0.0 – 2.6 s | Hook + logo lockup | READY FOR YOUR NEXT MOVE? |
| 2.6 – 5.0 s | Slam | WE'RE **HIRING!** |
| 5.0 – 8.6 s | The role | SENIOR SOCIAL MEDIA SPECIALIST & CREATIVE CONTENT WRITER |
| 8.6 – 11.2 s | The line | TURN IDEAS INTO IMPACT. JOIN ROTANA MUSIC. |
| 11.2 – 14.0 s | CTA | APPLY NOW · rotanamusic.com/careers |

Scene boundaries live in one place — `SCENES` in `src/theme.ts`. Change a
duration there and both formats follow.

## Render

```bash
npm install
node scripts-logoflag.cjs
npx remotion render Promo-LinkedIn-1080x1350 out/rotana-hiring-linkedin-1080x1350.mp4
npx remotion render Promo-Web-1920x1080      out/rotana-hiring-web-1920x1080.mp4
```

To preview and scrub interactively: `npm run studio`.

In a headless container, Chrome's old headless mode is gone, so point Remotion
at the headless shell:

```bash
export REMOTION_BROWSER_EXECUTABLE=/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell
```

## Two assets to drop in

Both are optional — the project renders without them — but the promo is not
finished until they are in.

**1. The official logo.** `rotanamusic.com` is unreachable from the build
container, so `src/Logo.tsx` currently draws a vector stand-in of the orb.
Drop the real file at `public/logo.png` (square, transparent background),
re-run `node scripts-logoflag.cjs`, and it is used instead — no code change.

**2. The music bed.** The MP4s are currently **silent**. Drop a licensed
track at `public/music.mp3`, re-run `node scripts-logoflag.cjs`, re-render, and
it is mixed in. The brief calls for an energetic instrumental with a modern
Arabic/electronic feel; the cut is built to a 14 s structure with hits at
2.6 s, 5.0 s, 8.6 s and 11.2 s, so pick a track whose accents land near those.

## Brand tokens

`src/theme.ts` holds the palette (greens sampled from the Rotana orb, plus the
cream used for the swoosh and the headline type). Type is Montserrat,
vendored under `public/fonts/` so renders never depend on the network.
