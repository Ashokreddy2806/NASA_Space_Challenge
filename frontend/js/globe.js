/* Horizon globe: MapLibre globe + API score heat layer + ranked pins. Talks to the FastAPI backend (same origin).
   Contract with js/panel.js: window.Panel.show({target, preset, site}) on select, window.Panel.hide() on deselect. */
(() => {
const API = location.protocol.startsWith("http") ? "" : "http://127.0.0.1:8000";
const BODY = { moon: { name: "the Moon", target: "the lunar south pole" }, mars: { name: "Mars", target: "Jezero crater" } };
const $ = id => document.getElementById(id);
const state = { target: "moon", preset: "balanced", hideFamous: false, sites: [], sel: -1, presets: null, rotate: true, flying: false, req: 0 };

/* Static mode: window.STATIC_DATA_BASE (js/config.js) points at pre-exported files (Vercel Blob); empty = live FastAPI. */
const STATIC = (window.STATIC_DATA_BASE || "").replace(/\/$/, "");
const staticUrl = path => {
  const [p, q = ""] = path.split("?"), a = new URLSearchParams(q);
  if (p === "/score-map-info") return `${STATIC}/score-map-info.json`;
  if (p === "/presets") return `${STATIC}/presets.json`;
  const m = p.match(/^\/targets\/(\w+)\/(top-sites|score\.png)$/);
  const preset = a.get("preset") || "balanced";
  if (m && m[2] === "score.png") return `${STATIC}/score/${m[1]}_${preset}.png`;
  if (m) return `${STATIC}/top-sites/${m[1]}_${preset}_${a.get("exclude_famous") === "true" ? "nofamous" : "all"}.json`;
  throw new Error("no static export for " + path);
};
const endpoint = path => STATIC ? staticUrl(path) : API + path;

const get = async path => {
  const r = await fetch(endpoint(path));
  if (!r.ok) throw new Error((await r.json().catch(() => ({}))).detail || r.statusText);
  return r.json();
};
const fmtLat = v => `${Math.abs(v).toFixed(1)}°${v < 0 ? "S" : "N"}`, fmtLon = v => `${Math.abs(v).toFixed(1)}°${v < 0 ? "W" : "E"}`;
const siteName = s => (s.famous && s.famous_name) || `${Math.abs(Math.round(s.lat))}°${s.lat < 0 ? "S" : "N"} ${Math.abs(Math.round(s.lon))}°${s.lon < 0 ? "W" : "E"}`;
const pct = s => Math.round(s.site_score * 100);
const status = msg => { $("status").textContent = msg || ""; };

/* ---------- stars ---------- */
function drawStars() {
  const c = document.createElement("canvas"), w = c.width = innerWidth, h = c.height = innerHeight, x = c.getContext("2d");
  let seed = 7; const rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647;
  for (let i = 0; i < Math.round(w * h / 9000); i++) {
    x.globalAlpha = .25 + .6 * rnd(); x.fillStyle = "#FFFFFF";
    const s = rnd() < .08 ? 2 : 1; x.fillRect(Math.floor(rnd() * w), Math.floor(rnd() * h), s, s);
  }
  $("stars").style.background = `#02040A url(${c.toDataURL()})`;
}
drawStars(); addEventListener("resize", drawStars);

/* ---------- map ---------- */
const DEM = { type: "raster-dem", encoding: "terrarium", tileSize: 256, maxzoom: 12,
  tiles: ["https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png"],
  attribution: "Terrain: Mapzen / AWS Terrain Tiles" };
const EXAG = 1.6;
const map = new maplibregl.Map({
  container: "map", center: [-60, 18], zoom: 2.15, attributionControl: { compact: true }, maxPitch: 70, dragRotate: false,
  style: { version: 8, sources: {
      img: { type: "raster", tileSize: 256, maxzoom: 12, tiles: ["https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"], attribution: "Imagery: Esri, Maxar, Earthstar Geographics" },
      dem: DEM, demshade: DEM },
    layers: [{ id: "bg", type: "background", paint: { "background-color": "#0B2A4A" } },
      { id: "img", type: "raster", source: "img", paint: { "raster-saturation": -0.05, "raster-contrast": 0.05 } },
      { id: "shade", type: "hillshade", source: "demshade", paint: { "hillshade-exaggeration": 0.35, "hillshade-shadow-color": "#1a1410", "hillshade-highlight-color": "#ffffff", "hillshade-accent-color": "#3a3226" } }] },
});
map.on("style.load", () => {
  map.setProjection({ type: "globe" });
  try { map.setSky({ "sky-color": "#1c4f8f", "horizon-color": "#8CC4F2", "fog-color": "#0a1c33", "sky-horizon-blend": 0.6, "horizon-fog-blend": 0.8, "fog-ground-blend": 0.3, "atmosphere-blend": ["interpolate", ["linear"], ["zoom"], 0, 1, 6, 0.4, 9, 0] }); } catch (e) { console.error("SKY", e.stack); }
  try { map.setTerrain({ source: "dem", exaggeration: EXAG }); } catch (e) { console.error("TERRAIN", e.stack); }
});
map.on("error", e => console.error("MAPERR", e.error && e.error.message, e.sourceId || ""));
const shift = () => ({ left: innerWidth > 900 ? Math.round(innerWidth * 0.2) : 0, right: 0, top: 0, bottom: 0 });
const layerOpacity = (z0, a0, z1, a1, z2, a2) => ["interpolate", ["linear"], ["zoom"], z0, a0, z1, a1, z2, a2];

/* Score PNG (equirectangular) -> soft glow Mercator canvas, visible only for top-scoring cells. */
const GLOW = [255, 190, 92];
async function buildHeat(url, bounds) {
  const img = new Image(); img.crossOrigin = "anonymous"; img.src = url; await img.decode();
  const W = img.width, H = img.height, src = document.createElement("canvas"); src.width = W; src.height = H;
  const sx = src.getContext("2d", { willReadFrequently: true }); sx.drawImage(img, 0, 0);
  const px = sx.getImageData(0, 0, W, H).data;
  const [west, south, east, north] = bounds, lonSpan = east - west, latSpan = north - south;
  const heatAt = (lat, lon) => {
    const x = Math.min(W - 1, Math.max(0, Math.floor((lon - west) / lonSpan * W))), y = Math.min(H - 1, Math.max(0, Math.floor((north - lat) / latSpan * H)));
    const i = (y * W + x) * 4; if (px[i + 3] < 128) return null;
    return Math.min(1, Math.max(0, ((.299 * px[i] + .587 * px[i + 1] + .114 * px[i + 2]) / 255 - .04) / .8));
  };
  const M = 1024, out = document.createElement("canvas"); out.width = 1440; out.height = M * 1.4 | 0;
  const ox = out.getContext("2d"), id = ox.createImageData(out.width, out.height), LIM = 85.0511, yMax = Math.log(Math.tan(Math.PI / 4 + LIM * Math.PI / 360));
  for (let y = 0; y < out.height; y++) {
    const my = yMax * (1 - 2 * y / (out.height - 1)), lat = (2 * Math.atan(Math.exp(my)) - Math.PI / 2) * 180 / Math.PI;
    for (let x = 0; x < out.width; x++) {
      const h = heatAt(lat, west + (x + .5) / out.width * lonSpan); if (h == null) continue;
      const k = Math.min(1, Math.max(0, (h - .6) / .4)), o = (y * out.width + x) * 4;
      if (k <= 0) continue;
      id.data[o] = GLOW[0]; id.data[o + 1] = GLOW[1] - 50 * k; id.data[o + 2] = GLOW[2] - 40 * k; id.data[o + 3] = 255 * k * k * (3 - 2 * k);
    }
  }
  const raw = document.createElement("canvas"); raw.width = out.width; raw.height = out.height; raw.getContext("2d").putImageData(id, 0, 0);
  ox.filter = "blur(7px)"; ox.drawImage(raw, 0, 0);
  return out.toDataURL();
}

let bounds = [-180, -90, 180, 90], loadingHeat = 0;
async function refreshHeat() {
  const id = ++loadingHeat;
  try {
    const url = await buildHeat(endpoint(`/targets/${state.target}/score.png?preset=${state.preset}&step=5`), bounds);
    if (id !== loadingHeat) return;
    const src = map.getSource("heat"); src.updateImage({ url, coordinates: [[-180, 85.0511], [180, 85.0511], [180, -85.0511], [-180, -85.0511]] });
    status("");
  } catch (e) { status("Score map failed: " + e.message); }
}

map.on("load", async () => { try {
  map.setPadding?.(shift());
  const BLANK = "data:image/gif;base64,R0lGODlhAQABAAAAACH5BAEKAAEALAAAAAABAAEAAAICTAEAOw==";
  map.addSource("heat", { type: "image", url: BLANK, coordinates: [[-180, 85.0511], [180, 85.0511], [180, -85.0511], [-180, -85.0511]] });
  map.addSource("pins", { type: "geojson", data: { type: "FeatureCollection", features: [] } });
  map.addLayer({ id: "heat", type: "raster", source: "heat", paint: { "raster-opacity": layerOpacity(0, .6, 4, .45, 8, .12), "raster-resampling": "linear", "raster-fade-duration": 0 } });
  map.addLayer({ id: "pins-halo", type: "circle", source: "pins", paint: { "circle-radius": 10, "circle-color": "#000000", "circle-opacity": .35, "circle-blur": .6 } });
  map.addLayer({ id: "pins", type: "circle", source: "pins", paint: { "circle-radius": 5.5, "circle-color": "#FF7A59", "circle-stroke-color": "#ffffff", "circle-stroke-width": 1.5 } });
  try { bounds = (await get("/score-map-info")).bounds_west_south_east_north; } catch (e) {}
  await loadPresets();
  await loadSites();
  refreshHeat();
  spin();
} catch (e) { console.error("INIT", e.stack); } });

map.on("click", e => {
  const hit = map.queryRenderedFeatures([[e.point.x - 12, e.point.y - 12], [e.point.x + 12, e.point.y + 12]], { layers: ["pins"] })[0];
  if (hit) select(hit.properties.i); else if (state.sel >= 0) deselect();
});
map.on("mousemove", e => {
  const over = map.queryRenderedFeatures([[e.point.x - 8, e.point.y - 8], [e.point.x + 8, e.point.y + 8]], { layers: ["pins"] }).length;
  map.getCanvas().style.cursor = over ? "pointer" : "";
});
for (const ev of ["mousedown", "touchstart", "wheel"]) map.getCanvas().addEventListener(ev, () => { state.rotate = false; }, { passive: true });

function spin() {
  const tick = () => {
    requestAnimationFrame(tick);
    if (!state.rotate || state.sel >= 0 || state.flying || document.hidden) return;
    const c = map.getCenter(); map.jumpTo({ center: [c.lng + .045, c.lat] });
  };
  tick();
}

/* ---------- data ---------- */
async function loadPresets() {
  try { state.presets = (await get("/presets")).presets; } catch (e) { state.presets = null; }
  renderPresets();
}
function renderPresets() {
  const p = state.presets && state.presets[state.target] || { balanced: { label: "Balanced", available: true } };
  $("preset").innerHTML = Object.entries(p).map(([k, v]) =>
    `<option value="${k}" ${v.available === false ? "disabled" : ""}>${v.label}</option>`).join("");
  $("preset").value = state.preset;
}

async function loadSites() {
  const id = ++state.req;
  try {
    const r = await get(`/targets/${state.target}/top-sites?preset=${state.preset}&exclude_famous=${state.hideFamous}&n=8`);
    if (id !== state.req) return;
    state.sites = r.sites;
    status("");
  } catch (e) { status(e.message); state.sites = []; }
  map.getSource("pins") && map.getSource("pins").setData({ type: "FeatureCollection", features: state.sites.map((s, i) => ({
    type: "Feature", geometry: { type: "Point", coordinates: [s.lon, s.lat] }, properties: { i } })) });
  renderChips();
}
function renderChips() {
  $("chips").innerHTML = state.sites.slice(0, 6).map((s, i) =>
    `<button data-i="${i}" class="${i === state.sel ? "on" : ""}">${siteName(s)}</button>`).join("");
  $("chips").querySelectorAll("button").forEach(b => b.onclick = () => select(+b.dataset.i));
}

/* ---------- elevation: decode the AWS Terrarium DEM tile under the site (same data the 3D terrain uses) ---------- */
const tileCache = {};
async function elevAt(lat, lon) {
  const z = 9, n = 2 ** z, r = lat * Math.PI / 180;
  const fx = (lon + 180) / 360 * n, fy = (1 - Math.asinh(Math.tan(r)) / Math.PI) / 2 * n, tx = Math.floor(fx), ty = Math.floor(fy);
  const key = `${z}/${tx}/${ty}`;
  tileCache[key] = tileCache[key] || (async () => {
    const img = new Image(); img.crossOrigin = "anonymous"; img.src = `https://s3.amazonaws.com/elevation-tiles-prod/terrarium/${key}.png`; await img.decode();
    const c = document.createElement("canvas"); c.width = img.width; c.height = img.height;
    const x = c.getContext("2d", { willReadFrequently: true }); x.drawImage(img, 0, 0); return x.getImageData(0, 0, c.width, c.height);
  })();
  const d = await tileCache[key], px = Math.min(d.width - 1, Math.floor((fx - tx) * d.width)), py = Math.min(d.height - 1, Math.floor((fy - ty) * d.height)), i = (py * d.width + px) * 4;
  return d.data[i] * 256 + d.data[i + 1] + d.data[i + 2] / 256 - 32768;
}

/* ---------- selection ---------- */
let marker = null;
function clearMarker() { if (marker) { marker.remove(); marker = null; } }
function select(i) {
  const s = state.sites[i]; if (!s) return;
  state.sel = i; state.rotate = false; clearMarker();
  map.setFilter("pins", ["!=", ["get", "i"], i]); map.setFilter("pins-halo", ["!=", ["get", "i"], i]);
  renderChips();
  const el = document.createElement("div"); el.className = "pin";
  el.innerHTML = `<span class="ring"></span><span class="ring b"></span><span class="stem"></span><span class="base"></span><span class="pill"></span>`;
  el.querySelector(".pill").textContent = `${pct(s)}%`;
  marker = new maplibregl.Marker({ element: el, anchor: "center" }).setLngLat([s.lon, s.lat]).addTo(map);
  state.flying = true;
  map.once("moveend", () => { state.flying = false; el.classList.add("up"); });
  map.flyTo({ center: [s.lon, s.lat], zoom: 5.6, pitch: 55, duration: 2400, essential: true, padding: shift() });
  setTimeout(() => el.classList.add("up"), 2600);
  window.Panel && window.Panel.show({ target: state.target, preset: state.preset, site: s });
  elevAt(s.lat, s.lon).then(m => { if (state.sel === i && window.Panel) window.Panel.setElevation(m); }).catch(e => console.error("ELEV", e.message));
}
function deselect() {
  state.sel = -1; clearMarker();
  if (!map.getLayer("pins")) { window.Panel && window.Panel.hide(); return; }
  map.setFilter("pins", null); map.setFilter("pins-halo", null);
  renderChips();
  if (map.getPitch() > 0) map.easeTo({ pitch: 0, zoom: Math.min(map.getZoom(), 3.2), duration: 900, padding: shift() });
  window.Panel && window.Panel.hide();
}

/* ---------- controls ---------- */
async function reload() {
  deselect(); state.req++;
  renderPresets();
  $("body-name").textContent = BODY[state.target].name;
  document.querySelectorAll(".pills button").forEach(b => b.classList.toggle("on", b.dataset.target === state.target));
  await loadSites(); refreshHeat();
  if (!state.sites.length) return;
  map.flyTo({ zoom: 2.15, pitch: 0, duration: 1200, padding: shift() });
}
document.querySelectorAll(".pills button").forEach(b => b.onclick = () => { if (!map.getSource("pins")) return; if (state.target !== b.dataset.target) { state.target = b.dataset.target; reload(); } });
$("preset").onchange = async e => {
  const prev = state.preset; state.preset = e.target.value;
  try { await get(`/targets/${state.target}/top-sites?preset=${state.preset}&n=8`); } catch (err) { state.preset = prev; $("preset").value = prev; status(err.message); setTimeout(status, 3500); return; }
  reload();
};
$("famous").onchange = e => { state.hideFamous = e.target.checked; deselect(); loadSites(); };
addEventListener("keydown", e => { if (e.key === "Escape" && state.sel >= 0) deselect(); });
})();
