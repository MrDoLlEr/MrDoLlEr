#!/usr/bin/env python3
"""Build a compact OSM dataset and five driving routes to Mohammed Abdo Arena."""

from __future__ import annotations

import json
import math
import os
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = Path("/tmp/maa-data/osm.json")
if not SRC.exists():
    SRC = ROOT / "data" / "osm.json"
OUT = ROOT / "data"

THEATER = {
    "id": "mohammed-abdo-arena",
    "name_en": "Mohammed Abdo Arena",
    "name_ar": "مسرح محمد عبده",
    "lon": 46.60650686,
    "lat": 24.77232198,
}

POIS = [
    THEATER,
    {
        "id": "kingdom-arena",
        "name_en": "Kingdom Arena",
        "name_ar": "المملكة أرينا",
        "lon": 46.60643394,
        "lat": 24.77873859,
    },
    {
        "id": "blvd-city",
        "name_en": "Boulevard City",
        "name_ar": "بوليفارد سيتي",
        "lon": 46.60426449,
        "lat": 24.76793913,
    },
    {
        "id": "blvd-world",
        "name_en": "Boulevard World",
        "name_ar": "عالم البوليفارد",
        "lon": 46.60124378,
        "lat": 24.77664117,
    },
    {
        "id": "riyadh-park",
        "name_en": "Riyadh Park",
        "name_ar": "الرياض بارك",
        "lon": 46.6300962,
        "lat": 24.7569124,
    },
]

ROAD_ALIASES = {
    "pmbs": [
        "طريق الأمير محمد بن سلمان بن عبدالعزيز",
        "Prince Mohammed Bin Salman",
    ],
    "souwaid": [
        "شارع سويد بن حارثة",
        "Souwaid",
        "Suwaid",
    ],
    "hawiy": [
        "شارع الحوي",
        "Al Hawiy",
        "الحوي",
    ],
    "turki": [
        "طريق الأمير تركي بن عبدالعزيز الأول",
        "Prince Turki",
    ],
    "imam": [
        "طريق الإمام سعود بن فيصل",
        "Al Imam Saud",
    ],
    "saad": [
        "طريق الأمير محمد بن سعد بن عبدالعزيز",
        "Prince Muhammad Ibn Saad",
        "Prince Mohammed Ibn Saad",
    ],
}

DESTINATIONS = {
    "square2": {"lon": 46.60755, "lat": 24.77085},  # BLVD City Square 2
    "general": {"lon": 46.60672, "lat": 24.77385},  # Arena General Gate on Al Hawiy
    "square1": {"lon": 46.60535, "lat": 24.77015},  # BLVD City Square 1
    "vip": {"lon": 46.60655, "lat": 24.77225},  # Arena VIP Gate at the theater
}

ROUTES = [
    {
        "id": "01-blvd-city-square-2",
        "title_en": "BLVD City Square 2",
        "title_ar": "ساحة البوليفارد ٢",
        "roads": [
            {"key": "pmbs", "en": "Prince Mohammed Bin Salman Road", "ar": "طريق الأمير محمد بن سلمان"},
            {"key": "souwaid", "en": "Souwaid Ibn Harithah Road", "ar": "شارع سويد بن حارثة"},
        ],
        "destination": "square2",
        "start_hint": {"lon": 46.6285, "lat": 24.7728},
    },
    {
        "id": "02-arena-general-gate",
        "title_en": "Arena General Gate",
        "title_ar": "البوابة العامة",
        "roads": [
            {"key": "pmbs", "en": "Prince Mohammed Bin Salman Road", "ar": "طريق الأمير محمد بن سلمان"},
            {"key": "souwaid", "en": "Souwaid Ibn Harithah Road", "ar": "شارع سويد بن حارثة"},
            {"key": "hawiy", "en": "Al Hawiy Road", "ar": "شارع الحوي"},
        ],
        "destination": "general",
        "start_hint": {"lon": 46.6288, "lat": 24.7732},
    },
    {
        "id": "03-arena-general-gate-north",
        "title_en": "Arena General Gate",
        "title_ar": "البوابة العامة",
        "roads": [
            {"key": "imam", "en": "Al Imam Saud Bin Faysal Road", "ar": "طريق الإمام سعود بن فيصل"},
            {"key": "saad", "en": "Prince Muhammad Ibn Saad Ibn Abdulaziz Road", "ar": "طريق الأمير محمد بن سعد"},
            {"key": "hawiy", "en": "Al Hawiy Road", "ar": "شارع الحوي"},
        ],
        "destination": "general",
        "start_hint": {"lon": 46.6125, "lat": 24.7864},
    },
    {
        "id": "04-blvd-city-square-1",
        "title_en": "BLVD City Square 1",
        "title_ar": "ساحة البوليفارد ١",
        "roads": [
            {"key": "turki", "en": "Prince Turki Bin Abdulaziz Al Awal Road", "ar": "طريق الأمير تركي بن عبدالعزيز الأول"},
        ],
        "destination": "square1",
        "start_hint": {"lon": 46.60945, "lat": 24.75469},
        "dest_radius_m": 480,
    },
    {
        "id": "05-arena-vip-gate",
        "title_en": "Arena VIP Gate",
        "title_ar": "بوابة كبار الشخصيات",
        "roads": [
            {"key": "pmbs", "en": "Prince Mohammed Bin Salman Road", "ar": "طريق الأمير محمد بن سلمان"},
            {"key": "souwaid", "en": "Souwaid Ibn Harithah Road", "ar": "شارع سويد بن حارثة"},
        ],
        "destination": "vip",
        "start_hint": {"lon": 46.6272, "lat": 24.7722},
    },
]


def haversine_m(a, b):
    lon1, lat1 = a
    lon2, lat2 = b
    r = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    h = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(h))


def name_matches(name: str, keys: list[str]) -> bool:
    if not name:
        return False
    return any(k in name for k in keys)


def way_points(el):
    return [(p["lon"], p["lat"]) for p in el.get("geometry") or []]


def road_key_for(name: str) -> str | None:
    for key, aliases in ROAD_ALIASES.items():
        if name_matches(name, aliases):
            return key
    return None


def simplify(points, min_m=18):
    if len(points) < 2:
        return points
    out = [points[0]]
    for p in points[1:]:
        if haversine_m(out[-1], p) >= min_m:
            out.append(p)
    if out[-1] != points[-1]:
        out.append(points[-1])
    return out


def snap_key(pt):
    return (round(pt[0], 6), round(pt[1], 6))


def build_graph(ways, allowed_keys: set[str], dest=None, dest_radius_m=220):
    adj = defaultdict(list)
    all_nodes = []

    def add_edge(a, b):
        a, b = snap_key(a), snap_key(b)
        d = haversine_m(a, b)
        if d <= 0:
            return
        adj[a].append((b, d))
        adj[b].append((a, d))

    for el in ways:
        tags = el.get("tags") or {}
        name = tags.get("name") or ""
        key = road_key_for(name)
        include = key in allowed_keys
        if not include and dest is not None and tags.get("highway"):
            pts0 = way_points(el)
            if pts0 and min(haversine_m(p, (dest["lon"], dest["lat"])) for p in pts0) < dest_radius_m:
                include = True
        if not include:
            continue
        pts = [snap_key(p) for p in way_points(el)]
        pts = [p for i, p in enumerate(pts) if i == 0 or p != pts[i - 1]]
        for a, b in zip(pts, pts[1:]):
            add_edge(a, b)
        all_nodes.extend(pts)

    # stitch nearby nodes so intersections connect even if OSM IDs differ
    uniq = list(dict.fromkeys(all_nodes))
    bins = defaultdict(list)
    cell = 0.0008  # ~80m
    for p in uniq:
        bins[(int(p[0] / cell), int(p[1] / cell))].append(p)
    for (gx, gy), bucket in bins.items():
        neighbors = []
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                neighbors.extend(bins.get((gx + dx, gy + dy), []))
        for a in bucket:
            for b in neighbors:
                if b <= a:
                    continue
                d = haversine_m(a, b)
                if 0 < d < 90:
                    add_edge(a, b)

    # connect leftover nearby components (overpasses / missing OSM links)
    def components():
        seen = set()
        comps = []
        for n in list(adj.keys()):
            if n in seen:
                continue
            stack = [n]
            seen.add(n)
            c = []
            while stack:
                u = stack.pop()
                c.append(u)
                for v, _ in adj[u]:
                    if v not in seen:
                        seen.add(v)
                        stack.append(v)
            comps.append(c)
        return comps

    for _ in range(12):
        comps = components()
        if len(comps) <= 1:
            break
        best = None
        for i, a in enumerate(comps):
            for b in comps[i + 1 :]:
                for p in a:
                    for q in b:
                        d = haversine_m(p, q)
                        if best is None or d < best[0]:
                            best = (d, p, q)
        if best and best[0] < 150:
            add_edge(best[1], best[2])
        else:
            break
    return adj


def nearest_node(adj, target):
    best, best_d = None, 1e18
    for n in adj:
        d = haversine_m(n, (target["lon"], target["lat"]))
        if d < best_d:
            best, best_d = n, d
    return best, best_d


def dijkstra(adj, start, goal):
    import heapq

    dist = {start: 0.0}
    prev = {}
    heap = [(0.0, start)]
    seen = set()
    while heap:
        d, u = heapq.heappop(heap)
        if u in seen:
            continue
        seen.add(u)
        if u == goal:
            break
        for v, w in adj[u]:
            nd = d + w
            if nd < dist.get(v, 1e18):
                dist[v] = nd
                prev[v] = u
                heapq.heappush(heap, (nd, v))
    if goal not in prev and start != goal:
        return None
    path = [goal]
    while path[-1] != start:
        path.append(prev[path[-1]])
    path.reverse()
    return path


def densify(path, step_m=14):
    out = []
    for a, b in zip(path, path[1:]):
        d = haversine_m(a, b)
        n = max(1, int(d / step_m))
        for i in range(n):
            t = i / n
            out.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
    out.append(path[-1])
    return out


def lite_features(raw):
    highways, buildings, greens, areas = [], [], [], []
    for el in raw["elements"]:
        tags = el.get("tags") or {}
        pts = way_points(el)
        if len(pts) < 2:
            continue
        rec = {
            "id": el["id"],
            "pts": pts,
            "name": tags.get("name"),
            "name_en": tags.get("name:en"),
            "highway": tags.get("highway"),
            "road_key": road_key_for(tags.get("name") or ""),
        }
        if tags.get("highway"):
            rec["pts"] = simplify(pts, 12 if tags.get("highway") in ("primary", "secondary", "trunk", "motorway") else 22)
            highways.append(rec)
        elif tags.get("building") or tags.get("amenity") == "theatre" or tags.get("leisure") == "stadium":
            rec["kind"] = (
                "theatre"
                if tags.get("amenity") == "theatre"
                else "stadium"
                if tags.get("leisure") == "stadium"
                else "building"
            )
            rec["levels"] = float(tags.get("building:levels") or (6 if rec["kind"] != "building" else 2))
            buildings.append(rec)
        elif tags.get("leisure") in ("park", "garden") or tags.get("landuse") in ("grass", "recreation_ground"):
            greens.append(rec)
        elif tags.get("tourism") in ("attraction", "theme_park"):
            rec["kind"] = tags.get("tourism")
            areas.append(rec)
    return {
        "highways": highways,
        "buildings": buildings,
        "greens": greens,
        "areas": areas,
        "pois": POIS,
        "theater": THEATER,
    }


def main():
    raw = json.loads(SRC.read_text())
    OUT.mkdir(parents=True, exist_ok=True)
    lite = lite_features(raw)
    (OUT / "osm-lite.json").write_text(json.dumps(lite))

    routes_out = []
    for spec in ROUTES:
        allowed = {r["key"] for r in spec["roads"]}
        dest = DESTINATIONS[spec["destination"]]
        adj = build_graph(
            raw["elements"],
            allowed,
            dest=dest,
            dest_radius_m=spec.get("dest_radius_m", 220),
        )
        start, sd = nearest_node(adj, spec["start_hint"])
        goal, gd = nearest_node(adj, dest)
        if goal:
            dest_node = snap_key((dest["lon"], dest["lat"]))
            if dest_node not in adj:
                d = haversine_m(goal, dest_node)
                adj[dest_node].append((goal, d))
                adj[goal].append((dest_node, d))
            goal = dest_node
        path = dijkstra(adj, start, goal) if start and goal else None
        if not path:
            raise SystemExit(f"no path for {spec['id']} nodes={len(adj)} start_d={sd} goal_d={gd}")
        theater = (THEATER["lon"], THEATER["lat"])
        if spec["destination"] in ("vip", "general") and haversine_m(path[-1], theater) > 8:
            path.append(theater)
        pts = densify(simplify(path, 10), 16)
        length = sum(haversine_m(a, b) for a, b in zip(pts, pts[1:]))
        n = len(spec["roads"])
        markers = []
        for i in range(n):
            idx = 0 if i == 0 else min(len(pts) - 1, int(len(pts) * (i / n)))
            markers.append({"n": i + 1, "lon": pts[idx][0], "lat": pts[idx][1], **spec["roads"][i]})
        routes_out.append(
            {
                **spec,
                "start_d_m": round(sd, 1),
                "goal_d_m": round(gd, 1),
                "length_m": round(length, 1),
                "path": [{"lon": p[0], "lat": p[1]} for p in pts],
                "markers": markers,
            }
        )
        print(f"{spec['id']}: {len(pts)} pts, {length:.0f} m, start {sd:.0f}m, goal {gd:.0f}m, nodes={len(adj)}")

    (OUT / "routes.json").write_text(json.dumps({"theater": THEATER, "routes": routes_out}, indent=2))
    print("wrote", OUT / "osm-lite.json", os.path.getsize(OUT / "osm-lite.json"))
    print("wrote", OUT / "routes.json")


if __name__ == "__main__":
    main()
