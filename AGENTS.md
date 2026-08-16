# AGENTS.md

## Cursor Cloud specific instructions

This repo contains a single real product in `mohammed-abdo-arena-map/`: a static, client-side web app (vanilla HTML/CSS/JS + Canvas) that shows an interactive isometric direction map for Mohammed Abdo Arena. The root `README.md` is just a GitHub profile stub. There is no backend, database, or Node/npm — only an optional Python asset pipeline.

### Running the app (required to test)

`js/map.js` loads `data/osm-lite.json` and `data/routes.json` via `fetch()`, so opening `index.html` over `file://` fails on CORS. You must serve the directory over HTTP:

```bash
cd mohammed-abdo-arena-map
python3 -m http.server 8080
```

Then open `http://localhost:8080/`. Committed JSON/GIF/MP4 assets are enough to run the map — no Python deps or asset regeneration required just to view it.

### Optional Python asset pipeline

Dependencies (`Pillow`, `arabic-reshaper`, `python-bidi`) are installed by the startup update script via `mohammed-abdo-arena-map/requirements.txt`. They are only needed to regenerate map data or media:

- `python3 scripts/build_data.py` — rebuilds `data/osm-lite.json` and `data/routes.json` from `data/osm.json` (committed). It prefers `/tmp/maa-data/osm.json` (a fresh Overpass export) and falls back to the committed `data/osm.json`, so it runs offline with no arguments.
- `python3 scripts/render_gifs.py` — re-renders `gifs/`, `videos/`, and `previews/`. Requires `ffmpeg` (preinstalled) plus the DejaVu Sans and Noto Naskh Arabic fonts at the hardcoded paths in the script (both preinstalled in this environment; needed for Arabic labels).

Both scripts regenerate the committed assets in place and are reproducible (output is byte-identical to what is committed), so running them leaves the working tree clean. There is no lint or automated test setup in this repo.
