# Project Brief — Mohammed Abdo Arena Direction Map
# بريف المشروع — خريطة اتجاهات مسرح محمد عبده

## 1. Overview / نظرة عامة

**EN:** An interactive, isometric entrance-direction map for **Mohammed Abdo Arena** (مسرح محمد عبده) in Riyadh, Saudi Arabia. It shows looping driving-route animations to each entrance in the same visual style as the Coca‑Cola Arena driving-direction graphics (isometric city map, animated red route, moving car, and a logo pin locked to the venue).

**AR:** خريطة تفاعلية ثلاثية الأبعاد (آيزومترك) توضّح اتجاهات القيادة إلى مداخل **مسرح محمد عبده** في الرياض، بنفس أسلوب أنيميشن اتجاهات Coca‑Cola Arena: خريطة مدينة آيزومترك، مسار أحمر متحرك، سيارة تتحرك على الطريق، وبِن (دبوس) للشعار مثبّت على موقع المسرح.

Reference / المرجع: [Coca‑Cola Arena — From_AUH.gif](https://about.coca-cola-arena.com/getattachment/plan-your-visit/From_AUH.gif)

## 2. Objective / الهدف

- **EN:** Give visitors a clear, animated, bilingual (Arabic/English) guide from a nearby main road to each specific gate/entrance of the venue, delivered both as an interactive web map and as ready-to-share GIF/MP4 loops.
- **AR:** تقديم دليل واضح ومتحرك وثنائي اللغة (عربي/إنجليزي) من أقرب طريق رئيسي إلى كل بوابة/مدخل بالمسرح، على شكل خريطة ويب تفاعلية وكذلك مقاطع GIF/MP4 جاهزة للمشاركة.

## 3. Brand & logo lock / العلامة وتثبيت الشعار

- The Mohammed Abdo Arena logo pin is **locked to the theatre building** in OpenStreetMap — not to the end of the red route line.
- Coordinates: `24.772322°N, 46.606507°E`
- OSM way `1218902216` — مسرح محمد عبده / Mohammed Abdu Arena
- Address: شارع سويد بن حارثة, حطين، الرياض

## 4. Locations / المواقع (5 routes)

| # | File ID | Destination (EN) | الوجهة (AR) | Roads / الطرق |
|---|---------|------------------|-------------|----------------|
| 1 | `01-blvd-city-square-2` | BLVD City Square 2 | ساحة البوليفارد ٢ | Prince Mohammed Bin Salman → Souwaid Ibn Harithah |
| 2 | `02-arena-general-gate` | Arena General Gate | البوابة العامة | Prince Mohammed Bin Salman → Souwaid Ibn Harithah → Al Hawiy |
| 3 | `03-arena-general-gate-north` | Arena General Gate (north approach) | البوابة العامة (من الشمال) | Al Imam Saud Bin Faysal → Prince Muhammad Ibn Saad → Al Hawiy |
| 4 | `04-blvd-city-square-1` | BLVD City Square 1 | ساحة البوليفارد ١ | Prince Turki Bin Abdulaziz Al Awal |
| 5 | `05-arena-vip-gate` | Arena VIP Gate | بوابة كبار الشخصيات | Prince Mohammed Bin Salman → Souwaid Ibn Harithah |

Nearby landmarks referenced on the map / معالم قريبة تظهر على الخريطة: Kingdom Arena (المملكة أرينا)، Boulevard City (بوليفارد سيتي)، Boulevard World (عالم البوليفارد)، Riyadh Park (الرياض بارك).

## 5. Deliverables / المُخرجات

- **Interactive web map** — `index.html` + `js/map.js` (HTML5 Canvas), 5 tabbed routes with looping animation.
- **5 GIF loops** — `gifs/*.gif` (one per route).
- **5 MP4 loops** — `videos/*.mp4` (one per route).
- **5 preview stills** — `previews/*.png` (final frame of each route).
- **Bilingual UI** — Arabic (RTL) + English.

## 6. Design / المواصفات البصرية

- Isometric ("2.5D") city map with extruded buildings; the theatre and stadium are visually emphasized.
- Animated red driving path drawn progressively, with a moving car following the route and a pulsing logo pin at the venue.
- Arabic street-name labels drawn on the roads — large, legible, kept fully on-canvas and non-overlapping.
- The logo marker is a gold square frame around the logo (no on-map step numbers; numbered steps live in the side legend).
- Rendered media canvas: `1280×720`, `12 fps`, ~48 draw frames + ~18 hold frames per loop.

## 7. Tech stack / التقنيات

| Layer | Technology |
|-------|------------|
| Frontend | Vanilla HTML5, CSS3, JavaScript (Canvas 2D) |
| Build/render | Python 3 (`Pillow`, `arabic-reshaper`, `python-bidi`) |
| Media encoding | `ffmpeg` (GIF palette + H.264 MP4) |
| Map data | OpenStreetMap (Overpass export → `data/osm.json`) |
| Fonts | DejaVu Sans (Latin) + Noto Naskh Arabic (Arabic) |
| Backend / DB | None — fully static |

## 8. How to run / التشغيل

The map loads JSON via `fetch()`, so it must be served over HTTP (not opened as a `file://`):

```bash
cd mohammed-abdo-arena-map
python3 -m http.server 8080
# open http://localhost:8080/
```

Regenerate data and media (optional) / إعادة توليد البيانات والوسائط (اختياري):

```bash
python3 scripts/build_data.py    # OSM → data/osm-lite.json + data/routes.json
python3 scripts/render_gifs.py   # → gifs/ , videos/ , previews/
```

## 9. Data pipeline / خط معالجة البيانات

1. `data/osm.json` — raw Overpass export for the area.
2. `scripts/build_data.py` — filters roads, builds a routing graph, runs shortest-path per route, and writes `data/osm-lite.json` (map features) and `data/routes.json` (5 computed paths + markers).
3. `scripts/render_gifs.py` — renders each route to GIF, MP4, and a preview PNG.

## 10. Notes / ملاحظات

- The interactive map and the rendered GIF/MP4 are generated from the same route data, so they stay consistent.
- Route geometry is computed from OSM; individual route shapes can be tuned per destination in `scripts/build_data.py` (start hints, allowed roads, destination points).
