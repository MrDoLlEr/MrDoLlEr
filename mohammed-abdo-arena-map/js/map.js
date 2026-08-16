const canvas = document.getElementById("map");
const ctx = canvas.getContext("2d");
const tabs = document.getElementById("tabs");
const legend = document.getElementById("legend");

const THEATER = { lon: 46.60650686, lat: 24.77232198 };
const ROT = (38 * Math.PI) / 180;
const COS = Math.cos((THEATER.lat * Math.PI) / 180);
let osm, routes, logo, active = 0, t = 0, last = 0, proj;

function meters(lon, lat) {
  const x = (lon - THEATER.lon) * 111320 * COS;
  const y = (lat - THEATER.lat) * 110540;
  return [
    x * Math.cos(ROT) - y * Math.sin(ROT),
    x * Math.sin(ROT) + y * Math.cos(ROT),
  ];
}

function makeProj(path) {
  const pts = path.map((p) => meters(p.lon, p.lat));
  const th = meters(THEATER.lon, THEATER.lat);
  const xs = pts.map((p) => p[0]).concat(th[0]);
  const ys = pts.map((p) => p[1]).concat(th[1]);
  const pad = 380;
  const minx = Math.min(...xs) - pad, maxx = Math.max(...xs) + pad;
  const miny = Math.min(...ys) - pad, maxy = Math.max(...ys) + pad;
  const tilt = 0.58;
  const scale = Math.min((canvas.width - 80) / (maxx - minx), (canvas.height - 90) / ((maxy - miny) * tilt));
  return (lon, lat, z = 0) => {
    const [x, y] = meters(lon, lat);
    return [
      40 + (x - minx) * scale,
      canvas.height - 50 - (y - miny) * scale * tilt - z,
    ];
  };
}

function strokeRoad(pts, color, width) {
  if (pts.length < 2) return;
  ctx.beginPath();
  pts.forEach((p, i) => {
    const [x, y] = proj(p[0], p[1]);
    i ? ctx.lineTo(x, y) : ctx.moveTo(x, y);
  });
  ctx.strokeStyle = color;
  ctx.lineWidth = width;
  ctx.lineJoin = "round";
  ctx.lineCap = "round";
  ctx.stroke();
}

function fillPoly(pts, color, z = 0) {
  if (pts.length < 3) return;
  ctx.beginPath();
  pts.forEach((p, i) => {
    const [x, y] = proj(p[0], p[1], z);
    i ? ctx.lineTo(x, y) : ctx.moveTo(x, y);
  });
  ctx.closePath();
  ctx.fillStyle = color;
  ctx.fill();
}

function drawBuilding(b) {
  const h = b.kind === "theatre" ? 34 : b.kind === "stadium" ? 26 : Math.min(28, 5 + (b.levels || 2) * 3.2);
  const top = b.kind === "theatre" ? "#242424" : b.kind === "stadium" ? "#a8c4a4" : "#e2e2de";
  const side = b.kind === "theatre" ? "#181818" : "#c4c4bf";
  const n = b.pts.length;
  for (let i = 0; i < n; i++) {
    const a = proj(b.pts[i][0], b.pts[i][1], 0);
    const c = proj(b.pts[(i + 1) % n][0], b.pts[(i + 1) % n][1], 0);
    const d = proj(b.pts[(i + 1) % n][0], b.pts[(i + 1) % n][1], h);
    const e = proj(b.pts[i][0], b.pts[i][1], h);
    if ((a[1] + c[1]) / 2 > (d[1] + e[1]) / 2) {
      ctx.beginPath();
      ctx.moveTo(...a); ctx.lineTo(...c); ctx.lineTo(...d); ctx.lineTo(...e);
      ctx.closePath();
      ctx.fillStyle = side;
      ctx.fill();
    }
  }
  fillPoly(b.pts, top, h);
}

function pointAt(path, tt) {
  tt = Math.max(0, Math.min(1, tt));
  let total = 0;
  const segs = [];
  for (let i = 0; i < path.length - 1; i++) {
    const a = path[i], b = path[i + 1];
    const l = Math.hypot(b.lon - a.lon, b.lat - a.lat) || 1e-12;
    segs.push([a, b, l]);
    total += l;
  }
  let target = total * tt, acc = 0;
  for (const [a, b, l] of segs) {
    if (acc + l >= target) {
      const u = (target - acc) / l;
      return {
        lon: a.lon + (b.lon - a.lon) * u,
        lat: a.lat + (b.lat - a.lat) * u,
        a, b,
      };
    }
    acc += l;
  }
  return { ...path.at(-1), a: path.at(-2), b: path.at(-1) };
}

function drawPin() {
  const [x, y] = proj(THEATER.lon, THEATER.lat);
  const pulse = 0.5 + 0.5 * Math.sin(performance.now() / 250);
  const r = 46 + pulse * 3;
  ctx.save();
  ctx.beginPath();
  ctx.arc(x, y - 8, r, 0, Math.PI * 2);
  ctx.fillStyle = "#c4101c";
  ctx.shadowColor = "rgba(0,0,0,.28)";
  ctx.shadowBlur = 16;
  ctx.fill();
  ctx.shadowBlur = 0;
  ctx.beginPath();
  ctx.arc(x, y - 8, r - 8, 0, Math.PI * 2);
  ctx.fillStyle = "#fff";
  ctx.fill();
  if (logo) {
    const s = (r - 10) * 2;
    ctx.drawImage(logo, x - s / 2, y - 8 - s / 2, s, s);
  }
  ctx.beginPath();
  ctx.moveTo(x - 8, y + r - 14);
  ctx.lineTo(x + 8, y + r - 14);
  ctx.lineTo(x, y + r + 10);
  ctx.closePath();
  ctx.fillStyle = "#c4101c";
  ctx.fill();
  ctx.restore();
}

function drawCar(pos) {
  const [x, y] = proj(pos.lon, pos.lat);
  const [x2, y2] = proj(pos.b.lon, pos.b.lat);
  const ang = Math.atan2(y2 - y, x2 - x);
  ctx.save();
  ctx.translate(x, y);
  ctx.rotate(ang);
  ctx.fillStyle = "#c4101c";
  roundRect(-18, -8, 36, 16, 5);
  ctx.fill();
  ctx.fillStyle = "#ffd2d2";
  roundRect(-6, -10, 16, 8, 3);
  ctx.fill();
  ctx.restore();
}

function roundRect(x, y, w, h, r) {
  ctx.beginPath();
  ctx.roundRect(x, y, w, h, r);
}

function drawFrame() {
  const route = routes.routes[active];
  proj = makeProj(route.path);
  ctx.fillStyle = "#e8e9e6";
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  osm.greens.forEach((g) => fillPoly(g.pts, "#c4d6ba"));
  osm.areas.forEach((a) => fillPoly(a.pts, "#cecfcb"));
  const rank = { primary: 1, trunk: 1, motorway: 1, secondary: 2, tertiary: 3 };
  [...osm.highways].sort((a, b) => (rank[b.highway] || 4) - (rank[a.highway] || 4)).forEach((r) => {
    if (["footway", "path", "steps"].includes(r.highway)) return;
    const w = r.highway === "primary" || r.highway === "motorway" ? 11 : r.highway === "secondary" ? 8 : r.highway === "tertiary" ? 6 : 4;
    const c = r.highway === "primary" || r.highway === "motorway" ? "#bac6d0" : r.highway === "secondary" ? "#cdd4da" : "#fff";
    strokeRoad(r.pts, c, w);
  });
  [...osm.buildings].sort((a, b) => meters(a.pts[0][0], a.pts[0][1])[1] - meters(b.pts[0][0], b.pts[0][1])[1])
    .forEach(drawBuilding);

  ctx.font = "700 14px DejaVu Sans, sans-serif";
  ctx.fillStyle = "#2a2d34";
  osm.pois.forEach((p) => {
    if (p.id === "mohammed-abdo-arena") return;
    const [x, y] = proj(p.lon, p.lat);
    ctx.fillText(p.name_en, x, y);
  });

  const n = Math.max(2, Math.round((route.path.length - 1) * t) + 1);
  const drawn = route.path.slice(0, n).map((p) => [p.lon, p.lat]);
  strokeRoad(drawn, "rgba(220,20,30,.28)", 18);
  strokeRoad(drawn, "#dc141e", 8);
  route.markers.forEach((m) => {
    const [x, y] = proj(m.lon, m.lat);
    ctx.beginPath(); ctx.arc(x, y, 12, 0, Math.PI * 2);
    ctx.fillStyle = "#468cd2"; ctx.fill();
    ctx.fillStyle = "#fff"; ctx.font = "700 13px sans-serif";
    ctx.textAlign = "center"; ctx.textBaseline = "middle";
    ctx.fillText(String(m.n), x, y);
    ctx.textAlign = "start"; ctx.textBaseline = "alphabetic";
  });
  drawCar(pointAt(route.path, t));
  drawPin();
}

function loop(ts) {
  if (!last) last = ts;
  const dt = (ts - last) / 1000;
  last = ts;
  t += dt / 6.5;
  if (t > 1.25) t = 0;
  const drawT = Math.min(1, t / 1);
  const prev = t;
  t = drawT;
  drawFrame();
  t = prev;
  requestAnimationFrame(loop);
}

function setRoute(i) {
  active = i;
  t = 0;
  document.querySelectorAll(".tabs button").forEach((b, idx) => b.classList.toggle("active", idx === i));
  const r = routes.routes[i];
  legend.innerHTML = `<h2>${r.title_ar}<br><small>${r.title_en}</small></h2>` +
    r.markers.map((m) => `<div class="item"><div class="num">${m.n}</div><div><b>${m.ar}</b><br><span dir="ltr">${m.en}</span></div></div>`).join("");
  document.getElementById("gifLink").href = `gifs/${r.id}.gif`;
  document.getElementById("mp4Link").href = `videos/${r.id}.mp4`;
}

async function boot() {
  const [osmJ, routeJ] = await Promise.all([
    fetch("data/osm-lite.json").then((r) => r.json()),
    fetch("data/routes.json").then((r) => r.json()),
  ]);
  osm = osmJ; routes = routeJ;
  logo = new Image();
  logo.src = "assets/logo.png";
  routes.routes.forEach((r, i) => {
    const b = document.createElement("button");
    b.textContent = `${i + 1}. ${r.title_ar}`;
    b.onclick = () => setRoute(i);
    tabs.appendChild(b);
  });
  setRoute(0);
  requestAnimationFrame(loop);
}
boot();
