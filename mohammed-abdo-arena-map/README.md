# Mohammed Abdo Arena — direction map

Looping entrance animations in the Coca-Cola Arena style (isometric map, red driving path, logo pin). Each location from the brief is a separate GIF / MP4.

The **Mohammed Abdo Arena logo is locked to the theatre building** in OpenStreetMap, not to the end of the red line:

- `24.772322°N, 46.606507°E`
- OSM way `1218902216` — مسرح محمد عبده / Mohammed Abdu Arena
- Address: شارع سويد بن حارثة, حطين

## Locations

| # | File | Destination | Roads |
|---|------|-------------|-------|
| 1 | `01-blvd-city-square-2` | BLVD City Square 2 | Prince Mohammed Bin Salman → Souwaid Ibn Harithah |
| 2 | `02-arena-general-gate` | Arena General Gate | Prince Mohammed Bin Salman → Souwaid Ibn Harithah → Al Hawiy |
| 3 | `03-arena-general-gate-north` | Arena General Gate | Al Imam Saud Bin Faysal → Prince Muhammad Ibn Saad → Al Hawiy |
| 4 | `04-blvd-city-square-1` | BLVD City Square 1 | Prince Turki Bin Abdulaziz Al Awal |
| 5 | `05-arena-vip-gate` | Arena VIP Gate | Prince Mohammed Bin Salman → Souwaid Ibn Harithah |

Open `index.html` (local static server) to play the interactive map. GIFs are in `gifs/`, MP4 loops in `videos/`.

## Regenerate

```bash
python3 scripts/build_data.py    # needs /tmp/maa-data/osm.json from Overpass
python3 scripts/render_gifs.py
```

Reference requested in the brief: [Coca-Cola Arena From_AUH.gif](https://about.coca-cola-arena.com/getattachment/plan-your-visit/From_AUH.gif)
