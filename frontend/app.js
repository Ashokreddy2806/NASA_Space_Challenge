/* Earth Analog Finder frontend: MapLibre + deck.gl + Plotly, talking to the FastAPI backend (same origin). */
const API = location.port === "8000" || location.protocol.startsWith("http") ? "" : "http://127.0.0.1:8000";
const LABEL = {
  relief_20km_m: "Relief (20 km)", slope_20km_deg: "Slope (20 km)", roughness_5km_m: "Roughness 5 km",
  roughness_10km_m: "Roughness 10 km", roughness_20km_m: "Roughness 20 km", hurst_2_32km: "Hurst exponent",
  precip_annual_mm: "Annual precip.", precip_driest_month_mm: "Driest-month precip.", ice_proxy: "Ice / cold proxy",
};
const PRESET_LABEL = { balanced: "Balanced", rover_mobility: "Rover mobility", cold_trap_ice: "Cold trap / ice", thermal_cycling: "Thermal cycling" };
const esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const $ = id => document.getElementById(id);
const fmt = (v, u) => v == null ? "—" : `${Math.abs(v) >= 100 ? Math.round(v) : +v.toFixed(2)}${u && u !== "unitless" ? " " + u : ""}`;

const state = { targets: [], target: null, preset: "balanced", weights: null, custom: false, hideFamous: false,
  sites: [], selected: null, pick: null, tick: 0 };

const map = new maplibregl.Map({
  container: "map", center: [-25, 12], zoom: 1.55, attributionControl: { compact: true },
  style: "https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json",
});
const overlay = new deck.MapboxOverlay({ interleaved: false, layers: [] });
map.addControl(overlay);
map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "bottom-right");

async function get(path) {
  const r = await fetch(API + path);
  if (!r.ok) throw new Error((await r.json().catch(() => ({}))).detail || r.statusText);
  return r.json();
}
const wq = () => state.custom ? `weights=${encodeURIComponent(JSON.stringify(state.weights))}` : `preset=${state.preset}`;

function drawMap() {
  const t = state.target;
  const layers = [
    new deck.BitmapLayer({
      id: `score-${t.id}-${state.tick}`, image: `${API}/targets/${t.id}/score.png?${wq()}`,
      bounds: [-180, -90, 180, 90], _imageCoordinateSystem: deck.COORDINATE_SYSTEM.LNGLAT, opacity: 0.85,
    }),
    new deck.ScatterplotLayer({
      id: "sites", data: state.sites.map((s, i) => ({ ...s, rank: i + 1 })), getPosition: d => [d.lon, d.lat],
      getRadius: 7, radiusUnits: "pixels", getFillColor: [56, 213, 255], getLineColor: [255, 255, 255], lineWidthMinPixels: 1.5, stroked: true,
    }),
    new deck.TextLayer({
      id: "site-labels", data: state.sites.map((s, i) => ({ ...s, rank: i + 1 })), getPosition: d => [d.lon, d.lat],
      getText: d => String(d.rank), getSize: 11, getColor: [6, 16, 26], fontWeight: 700, getTextAnchor: "middle", getAlignmentBaseline: "center",
    }),
  ];
  if (state.pick) layers.push(new deck.ScatterplotLayer({
    id: "pick", data: [state.pick], getPosition: d => [d.lon, d.lat], getRadius: 11, radiusUnits: "pixels",
    filled: false, stroked: true, getLineColor: [255, 255, 255], lineWidthMinPixels: 2.5,
  }));
  overlay.setProps({ layers });
}

function renderTargets() {
  $("targets").innerHTML = state.targets.map(t =>
    `<button data-id="${t.id}" class="${t.id === state.target.id ? "on" : ""}">${t.body === "Moon" ? "🌑 Lunar south pole" : "🔴 Jezero, Mars"}</button>`).join("");
  $("targets").querySelectorAll("button").forEach(b => b.onclick = () => setTarget(b.dataset.id));
}

async function renderTargetInfo() {
  const p = await get(`/targets/${state.target.id}`);
  const f = p.features, pc = k => f[k] && f[k].earth_percentile != null ? `${Math.round(f[k].earth_percentile)}th` : "—";
  $("target-info").innerHTML = `${esc(p.region)}.<br>Relief ${fmt(f.relief_20km_m.value, "m")} (Earth ${pc("relief_20km_m")} pct) · slope ${fmt(f.slope_20km_deg.value, "°")} (${pc("slope_20km_deg")}).<br>
  <span style="color:var(--mid)">Temperatures not scored: no site-specific literature values yet.</span>`;
}

function renderPresets() {
  const pr = state.target.presets;
  $("presets").innerHTML = Object.keys(pr).map(k => {
    const on = !state.custom && state.preset === k;
    return `<button data-k="${k}" class="${on ? "on" : ""}" ${pr[k].available ? "" : "disabled title=\"Unavailable: no site-specific target temperatures yet\""}>${PRESET_LABEL[k]}</button>`;
  }).join("") + (state.custom ? `<button class="on">Custom</button>` : "");
  $("presets").querySelectorAll("button[data-k]").forEach(b => b.onclick = () => setPreset(b.dataset.k));
  const feats = state.target.features_scored;
  const w = state.weights || {};
  $("weights").innerHTML = feats.map(k => `<div class="w"><label for="w-${k}">${LABEL[k]}</label>
    <input id="w-${k}" type="range" min="0" max="3" step="0.1" value="${w[k] ?? 0}" data-k="${k}"><span>${(w[k] ?? 0).toFixed(1)}</span></div>`).join("");
  $("weights").querySelectorAll("input").forEach(i => i.oninput = () => {
    state.weights = Object.fromEntries([...$("weights").querySelectorAll("input")].map(x => [x.dataset.k, +x.value]).filter(([, v]) => v > 0));
    i.nextElementSibling.textContent = (+i.value).toFixed(1);
    state.custom = Object.keys(state.weights).length > 0;
    $("custom-note").hidden = !state.custom;
    clearTimeout(state.deb); state.deb = setTimeout(() => { state.tick++; drawMap(); refreshSelected(); renderPresetsChip(); }, 250);
  });
}
const renderPresetsChip = () => {
  $("presets").querySelectorAll("button").forEach(b => b.classList.toggle("on", state.custom ? !b.dataset.k : b.dataset.k === state.preset));
  if (state.custom && !$("presets").querySelector("button:not([data-k])")) $("presets").insertAdjacentHTML("beforeend", `<button class="on">Custom</button>`);
};

async function loadSites() {
  const q = `preset=${state.preset}&exclude_famous=${state.hideFamous}&n=10`;
  state.sites = (await get(`/targets/${state.target.id}/top-sites?${q}`)).sites;
  $("sites").innerHTML = state.sites.map((s, i) => `<li data-i="${i}"><span class="rank">${i + 1}</span>
    <div><div>${Math.abs(s.lat).toFixed(1)}°${s.lat < 0 ? "S" : "N"}, ${Math.abs(s.lon).toFixed(1)}°${s.lon < 0 ? "W" : "E"}</div>
    <div class="sub">weakest: ${s.weakest_matches.slice(0, 2).map(k => LABEL[k]).join(", ")}</div></div><span class="sc">${s.score.toFixed(1)}</span></li>`).join("");
  $("sites").querySelectorAll("li").forEach(li => li.onclick = () => {
    const s = state.sites[+li.dataset.i];
    map.flyTo({ center: [s.lon, s.lat], zoom: 4.5, duration: 1400 });
    selectSite(s.lat, s.lon, +li.dataset.i);
  });
  drawMap();
}

async function selectSite(lat, lon, idx = null) {
  state.pick = { lat, lon };
  document.querySelectorAll("#sites li").forEach((li, i) => li.classList.toggle("on", i === idx));
  drawMap();
  try {
    const d = await get(`/targets/${state.target.id}/site?lat=${lat}&lon=${lon}&${wq()}`);
    state.selected = { lat, lon, idx };
    showDetail(d);
  } catch (e) {
    $("detail").hidden = true; $("empty").hidden = false;
    $("empty").innerHTML = `<b>${esc(e.message)}</b><br>Pick a land location.`;
  }
}
const refreshSelected = () => state.selected && selectSite(state.selected.lat, state.selected.lon, state.selected.idx);

function showDetail(d) {
  $("empty").hidden = true; $("detail").hidden = false;
  $("d-title").textContent = `Similarity to ${state.target.name}`;
  $("d-coord").textContent = `${d.lat.toFixed(2)}°, ${d.lon.toFixed(2)}° · ${state.custom ? "custom weights" : PRESET_LABEL[state.preset]}`;
  $("d-score").textContent = d.score.toFixed(0);
  const names = d.features.map(f => LABEL[f.feature].replace("Roughness", "Rough.").replace("precip.", "precip"));
  const vals = d.features.map(f => f.sub_score);
  Plotly.react("radar", [{ type: "scatterpolar", r: [...vals, vals[0]], theta: [...names, names[0]], fill: "toself",
    line: { color: "#38d5ff", width: 2 }, fillcolor: "rgba(56,213,255,.22)", hovertemplate: "%{theta}: %{r:.0f}<extra></extra>" }],
    { polar: { bgcolor: "rgba(0,0,0,0)", radialaxis: { range: [0, 100], gridcolor: "rgba(255,255,255,.12)", tickfont: { size: 9, color: "#8b94a7" } },
      angularaxis: { gridcolor: "rgba(255,255,255,.12)", tickfont: { size: 9, color: "#c9d0de" } } },
      paper_bgcolor: "rgba(0,0,0,0)", margin: { t: 24, b: 24, l: 64, r: 64 }, showlegend: false },
    { displayModeBar: false, responsive: true });
  $("d-table").innerHTML = `<tr><th>Feature</th><th class="n">Earth</th><th class="n">Target</th><th>Match</th></tr>` +
    d.features.map(f => `<tr title="${esc(f.note)}"><td>${LABEL[f.feature]}</td><td class="n">${fmt(f.earth_value, f.units)}</td>
    <td class="n">${f.target_value == null ? (f.feature === "ice_proxy" || f.feature.startsWith("precip") ? "beyond Earth" : "—") : fmt(f.target_value, f.units)}</td>
    <td><span class="v ${f.verdict}">${Math.round(f.sub_score)}</span></td></tr>`).join("");
  const bad = d.features.filter(f => f.verdict !== "match");
  $("d-break").innerHTML =
    (bad.length ? bad.map(f => `<li><b>${LABEL[f.feature]}</b> ${f.verdict === "mismatch" ? "does not match" : "only partly matches"} (${Math.round(f.sub_score)}/100)</li>`).join("") : "<li>All scored features match.</li>") +
    `<li>Not scored: ${Object.keys(d.not_scored).map(k => esc(k.replace(/_c$/, "").replace(/_/g, " "))).join(", ")} (no site-specific values)</li>` +
    (state.target.body === "Mars" ? `<li>Mars 5 km roughness is resolution-limited (weight 0) and its Hurst exponent uses reduced lags (half weight).</li>` : "") +
    `<li>Dryness${state.target.body === "Moon" ? " and ice rows compare" : " row compares"} against a target beyond Earth's range (${state.target.body === "Moon" ? "airless / permanently shadowed" : "hyper-arid"}).</li>`;
  $("d-cannot").innerHTML = d.earth_cannot_replicate.map(x => `<li>${esc(x)}</li>`).join("");
}

async function setPreset(k) {
  state.preset = k; state.custom = false; state.weights = { ...state.target.presets[k].weights };
  $("custom-note").hidden = true; state.tick++;
  renderPresets(); await loadSites(); refreshSelected();
}

async function setTarget(id) {
  state.target = state.targets.find(t => t.id === id);
  state.preset = "balanced"; state.custom = false; state.selected = null; state.pick = null;
  state.weights = { ...state.target.presets.balanced.weights };
  renderTargets(); renderPresets(); renderTargetInfo();
  $("detail").hidden = true; $("empty").hidden = false;
  $("empty").innerHTML = "<b>Click anywhere on land</b> to see what matches and what doesn't.";
  await loadSites();
  if (state.sites.length) { const s = state.sites[0]; selectSite(s.lat, s.lon, 0); }
}

map.on("click", e => selectSite(+e.lngLat.lat.toFixed(3), +(((e.lngLat.lng + 540) % 360) - 180).toFixed(3)));
$("famous").onchange = e => { state.hideFamous = e.target.checked; loadSites(); };
map.on("load", async () => {
  state.targets = await get("/targets");
  const want = new URLSearchParams(location.search).get("target");
  await setTarget(state.targets.some(t => t.id === want) ? want : state.targets[0].id);
  $("targets").addEventListener("click", () => {});
});
