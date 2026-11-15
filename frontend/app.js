/* Earth Analog Finder frontend: MapLibre + deck.gl + Plotly, talking to the FastAPI backend (same origin).
   Scores are Earth-relative (0-100 here, 0-1 in the API): a Moon score and a Mars score are never comparable. */
const API = location.protocol.startsWith("http") ? "" : "http://127.0.0.1:8000";
const LABEL = {
  relief_20km_m: "Relief (20 km)", slope_20km_deg: "Slope (20 km)", roughness_5km_m: "Roughness 5 km",
  roughness_10km_m: "Roughness 10 km", roughness_20km_m: "Roughness 20 km", hurst_2_32km: "Hurst exponent",
  temp_mean_c: "Mean temp.", temp_diurnal_range_c: "Diurnal range", temp_max_warmest_c: "Warmest-month max",
  temp_min_coldest_c: "Coldest-month min", temp_annual_range_c: "Annual range",
  precip_annual_mm: "Annual precip.", precip_driest_month_mm: "Driest-month precip.",
};
const GROUP = {
  relief: "Relief", slope: "Slope", roughness: "Roughness", scale_robust_roughness: "Hurst (scale-robust)",
  temperature: "Temperature (qualitative)", dryness: "Dryness",
};
const esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const $ = id => document.getElementById(id);
const num = (v, d = 3) => v == null || !isFinite(v) ? "—" : Math.abs(v) >= 100 ? Math.round(v).toLocaleString() : +v.toPrecision(d);
const pct = v => `${Math.round(v * 100)}`;
const dirLat = v => `${Math.abs(v).toFixed(1)}°${v < 0 ? "S" : "N"}`, dirLon = v => `${Math.abs(v).toFixed(1)}°${v < 0 ? "W" : "E"}`;

const state = { targets: [], target: null, preset: "balanced", weights: null, custom: false, hideFamous: false,
  sites: [], selected: null, pick: null, tick: 0, profile: null };

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
  const t = state.target, data = state.sites.map((s, i) => ({ ...s, rank: i + 1 }));
  const layers = [
    new deck.BitmapLayer({
      id: `score-${t.id}-${state.tick}`, image: `${API}/targets/${t.id}/score.png?${wq()}`,
      bounds: [-180, -90, 180, 90], _imageCoordinateSystem: deck.COORDINATE_SYSTEM.LNGLAT, opacity: 0.85,
    }),
    new deck.ScatterplotLayer({ id: "sites", data, getPosition: d => [d.lon, d.lat], getRadius: 7, radiusUnits: "pixels",
      getFillColor: d => d.famous ? [255, 181, 71] : [56, 213, 255], getLineColor: [255, 255, 255], lineWidthMinPixels: 1.5, stroked: true }),
    new deck.TextLayer({ id: "site-labels", data, getPosition: d => [d.lon, d.lat], getText: d => String(d.rank), getSize: 11,
      getColor: [6, 16, 26], fontWeight: 700, getTextAnchor: "middle", getAlignmentBaseline: "center" }),
  ];
  if (state.pick) layers.push(new deck.ScatterplotLayer({ id: "pick", data: [state.pick], getPosition: d => [d.lon, d.lat],
    getRadius: 11, radiusUnits: "pixels", filled: false, stroked: true, getLineColor: [255, 255, 255], lineWidthMinPixels: 2.5 }));
  overlay.setProps({ layers });
}

function renderTargets() {
  $("targets").innerHTML = state.targets.map(t =>
    `<button data-id="${t.id}" class="${t.id === state.target.id ? "on" : ""}">${t.id === "moon" ? "🌑 Lunar south pole" : "🔴 Jezero, Mars"}</button>`).join("");
  $("targets").querySelectorAll("button").forEach(b => b.onclick = () => setTarget(b.dataset.id));
}

async function renderTargetInfo() {
  const p = state.profile = await get(`/targets/${state.target.id}`);
  const f = p.features, m = k => f[k] && f[k].median != null ? num(f[k].median) : "—";
  const ice = p.ice_proxy && p.ice_proxy.available ? `<br>Permanently shadowed: ${(p.ice_proxy.value * 100).toFixed(1)}% of the region (context only, Earth has no equivalent map).` : "";
  const unavailable = state.target.not_scored.filter(x => x.status === "unavailable").map(x => LABEL[x.feature]).filter(Boolean);
  $("target-info").innerHTML = `${esc(p.label)}, ${Math.round(p.extent.radius_km)} km radius.<br>
  Relief ${m("relief_20km_m")} m · slope ${m("slope_20km_deg")}° · roughness 10 km ${m("roughness_10km_m")} m.${ice}<br>
  <span style="color:var(--mid)">${state.target.id === "moon"
    ? "Temperature scored qualitatively from cited polar anchors."
    : "Temperature unavailable (thermal inertia only); unresolved at 3.7 km: " + esc(unavailable.slice(0, 3).join(", ")) + "."}</span>`;
}

function renderPresets() {
  const pr = state.target.presets;
  $("presets").innerHTML = Object.keys(pr).map(k => {
    const on = !state.custom && state.preset === k;
    return `<button data-k="${k}" class="${on ? "on" : ""}" ${pr[k].available ? "" : "disabled title=\"Unavailable for this target\""}>${esc(pr[k].label)}</button>`;
  }).join("") + (state.custom ? `<button class="on">Custom</button>` : "");
  $("presets").querySelectorAll("button[data-k]").forEach(b => b.onclick = () => setPreset(b.dataset.k));
  const groups = state.target.scored_groups, w = state.weights || {};
  $("weights").innerHTML = groups.map(g => `<div class="w"><label for="w-${g}">${GROUP[g]}</label>
    <input id="w-${g}" type="range" min="0" max="2" step="0.05" value="${w[g] ?? 0}" data-k="${g}"><span>${(w[g] ?? 0).toFixed(2)}</span></div>`).join("");
  $("weights").querySelectorAll("input").forEach(i => i.oninput = () => {
    state.weights = Object.fromEntries([...$("weights").querySelectorAll("input")].map(x => [x.dataset.k, +x.value]).filter(([, v]) => v > 0));
    i.nextElementSibling.textContent = (+i.value).toFixed(2);
    state.custom = Object.keys(state.weights).length > 0;
    $("custom-note").hidden = !state.custom;
    clearTimeout(state.deb); state.deb = setTimeout(() => { state.tick++; drawMap(); refreshSelected(); chip(); }, 250);
  });
}
const chip = () => {
  $("presets").querySelectorAll("button").forEach(b => b.classList.toggle("on", state.custom ? !b.dataset.k : b.dataset.k === state.preset));
  if (state.custom && !$("presets").querySelector("button:not([data-k])")) $("presets").insertAdjacentHTML("beforeend", `<button class="on">Custom</button>`);
};

async function loadSites() {
  const r = await get(`/targets/${state.target.id}/top-sites?preset=${state.preset}&exclude_famous=${state.hideFamous}&n=10`);
  state.sites = r.sites;
  $("sites").innerHTML = state.sites.map((s, i) => {
    const worst = Object.entries(s.group_scores || {}).sort((a, b) => a[1] - b[1])[0];
    return `<li data-i="${i}"><span class="rank" style="${s.famous ? "background:var(--mid)" : ""}">${i + 1}</span>
    <div><div>${dirLat(s.lat)}, ${dirLon(s.lon)}${s.famous ? ` <span class="muted">near ${esc(s.famous_name)}</span>` : ""}</div>
    <div class="sub">weakest group: ${worst ? GROUP[worst[0]] + " " + pct(worst[1]) : "—"}</div></div><span class="sc">${pct(s.site_score)}</span></li>`;
  }).join("");
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

function featureRow(f) {
  const name = LABEL[f.feature] || f.feature;
  if (f.qualitative) {
    const c = f.band_similarity >= 0.8 ? "match" : f.band_similarity >= 0.5 ? "partial" : "mismatch";
    return `<tr title="${esc(f.absolute_gap_note)}"><td>${name} <span class="muted">(qual.)</span></td><td class="n">${num(f.value)} °C</td>
      <td class="n">cold band ${f.target_band}</td><td class="n">band ${f.band}</td><td><span class="v ${c}">${pct(f.band_similarity)}</span></td></tr>`;
  }
  const sim = f.absolute_similarity, cls = sim >= 0.8 ? "match" : sim >= 0.5 ? "partial" : "mismatch";
  return `<tr title="${esc(f.note)}"><td>${name}${f.hidden_real_unit_gap ? " ⚠" : ""}</td><td class="n">${num(f.value)} ${f.units === "unitless" ? "" : esc(f.units)}</td>
    <td class="n">${num(f.target_median)}</td><td class="n">${f.absolute_gap > 0 ? "+" : ""}${num(f.absolute_gap)}</td>
    <td><span class="v ${cls}">${pct(sim)}</span></td></tr>`;
}

function showDetail(d) {
  $("empty").hidden = true; $("detail").hidden = false;
  $("d-title").textContent = `Similarity to ${state.target.name}`;
  $("d-coord").textContent = `${d.lat.toFixed(2)}°, ${d.lon.toFixed(2)}° · ${state.custom ? "custom weights" : state.target.presets[state.preset].label}${d.famous_near ? " · near " + d.famous_near : ""}`;
  $("d-score").textContent = pct(d.score);
  const g = Object.entries(d.group_scores).filter(([k]) => d.weights_used[k] != null);
  const names = g.map(([k]) => GROUP[k].replace(" (qualitative)", "").replace(" (scale-robust)", "")), vals = g.map(([, v]) => v * 100);
  Plotly.react("radar", [{ type: "scatterpolar", r: [...vals, vals[0]], theta: [...names, names[0]], fill: "toself",
    line: { color: "#38d5ff", width: 2 }, fillcolor: "rgba(56,213,255,.22)", hovertemplate: "%{theta}: %{r:.0f}<extra></extra>" }],
    { polar: { bgcolor: "rgba(0,0,0,0)", radialaxis: { range: [0, 100], gridcolor: "rgba(255,255,255,.12)", tickfont: { size: 9, color: "#8b94a7" } },
      angularaxis: { gridcolor: "rgba(255,255,255,.12)", tickfont: { size: 10, color: "#c9d0de" } } },
      paper_bgcolor: "rgba(0,0,0,0)", margin: { t: 24, b: 24, l: 64, r: 64 }, showlegend: false }, { displayModeBar: false, responsive: true });
  $("d-table").innerHTML = `<tr><th>Feature</th><th class="n">Earth</th><th class="n">Target</th><th class="n">Gap</th><th>Match</th></tr>` + d.features.map(featureRow).join("");
  const weak = d.features.filter(f => !f.qualitative && f.absolute_similarity < 0.5);
  const items = [];
  d.hidden_gaps.forEach(k => items.push(`<li><b>${LABEL[k]}</b>: ranks alike on Earth's scale but the real-unit gap is large (⚠)</li>`));
  weak.filter(f => !f.hidden_real_unit_gap).forEach(f => items.push(`<li><b>${LABEL[f.feature]}</b> is far from the target in real units (match ${pct(f.absolute_similarity)}/100)</li>`));
  if (!items.length) items.push("<li>No scored feature has a large real-unit gap here.</li>");
  items.push(`<li>Not scored: ${d.not_scored.filter(x => x.status === "unavailable").map(x => esc(LABEL[x.feature] || x.feature)).join(", ")} (reasons in the API)</li>`);
  if (state.target.id === "moon") items.push("<li>Earth temperature is air temperature; the lunar side is a cited surface anchor, so temperature is a qualitative band match only.</li>");
  $("d-break").innerHTML = items.join("");
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
});
