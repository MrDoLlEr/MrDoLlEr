---
name: creative-brief
description: Intake and execute a multimedia or design brief on this workstation. Use when the user asks for a design, animation, video, poster, social visual, brand system, or interactive experience.
---

# Creative brief

## 1. Name the actual brief

The user’s first message may be direction, not the job. Confirm the deliverable in one line before building: poster, motion, site, video, identity, or tool setup.

Do not attach the work to `mohammed-abdo-arena-map/` unless they asked for that project.

## 2. Direction before pixels

Write (short, internal):

- Audience and use (print, 9:16, 16:9, web, still)
- Language (Arabic, English, mixed) and direction (RTL/LTR)
- Visual language (references from their work if relevant)
- What must be preserved (logo, type, footage)

## 3. Use this machine

| Need | Tool |
| --- | --- |
| Encode / cut / overlay video | `ffmpeg`, `ffprobe` |
| Still processing | ImageMagick `convert` / `identify` |
| Audio | `sox` |
| SVG → PNG | `rsvg-convert` |
| GIF | `gifsicle` |
| Arabic on images | Pillow + raqm, fonts listed in `AGENTS.md` |
| Interactive web | HTML/CSS/JS; GSAP from CDN or project npm |
| Generative image/video | Higgsfield MCP, only if they asked |

Run `bash scripts/check-creative-env.sh` if a tool is missing.

## 4. Arabic

- `dir="rtl"` and `lang="ar"` on Arabic surfaces
- Shape with raqm (`language="ar"`, `direction="rtl"`) or `arabic-reshaper` + `python-bidi`
- Prefer IBM Plex Sans Arabic (UI), Amiri or Noto Naskh Arabic (display/editorial)
- Mixed lines: keep Latin LTR inside RTL layout; do not reverse Latin

## 5. Quality loop

Build → run → look → fix the weakest visual thing → run again.

For UI, use the computer-use agent and save a short recording. For video/image, inspect frames with `ffprobe` / `identify` and open the file.

Do not declare done on a first technically-working version.
