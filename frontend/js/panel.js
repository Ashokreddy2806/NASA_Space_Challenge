(function () {
  const GROUP = { relief: "Relief", slope: "Slope", roughness: "Roughness", scale_robust_roughness: "Multi-scale",
    temperature: "Temperature", dryness: "Dryness", ice_proxy: "Ice proxy" };
  const FEAT = { relief_20km_m: "relief (20 km)", slope_20km_deg: "slope (20 km)", roughness_5km_m: "roughness at 5 km",
    roughness_10km_m: "roughness at 10 km", roughness_20km_m: "roughness at 20 km", hurst_2_32km: "Hurst exponent",
    temp_mean_c: "mean temperature", temp_diurnal_range_c: "day-night range", temp_max_warmest_c: "warmest-month high",
    temp_min_coldest_c: "coldest-month low", temp_annual_range_c: "annual range", precip_annual_mm: "annual precipitation",
    precip_driest_month_mm: "driest-month precipitation" };
  const TARGET = { moon: "Moon (south pole)", mars: "Mars (Jezero)", moon_south_pole: "Moon (south pole)", mars_jezero: "Mars (Jezero)" };
  const CANNOT = {
    common: ["Gravity: Earth is 6x (Moon) or 2.6x (Mars) the target's surface gravity, so slope stability and regolith flow differ.",
      "Radiation: no Earth site has the target's unshielded cosmic and solar particle flux."],
    moon: ["Vacuum: the Moon has none. Earth always has an atmosphere, so wind, convection and weathering act here but not there, and heat transfer differs.",
      "Temperature is only a weak qualitative anchor: Earth air temperature is compared against a lunar surface value."],
    mars: ["Thin atmosphere: Earth has about 100x the surface pressure of Mars, which changes dust, wind and heat transfer.",
      "Score covers terrain and dryness only. It includes no temperature comparison."] };
  const esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  const root = () => document.getElementById("panel");
  let cur = null, opener = null, plotlyP = null;

  function tkey(t) { return String(t || "").startsWith("mars") ? "mars" : "moon"; }
  function fmt(v) { const a = Math.abs(v); return a >= 100 ? v.toFixed(0) : a >= 10 ? v.toFixed(1) : v.toFixed(2); }
  function coords(s) { return `${Math.abs(s.lat).toFixed(2)}°${s.lat < 0 ? "S" : "N"}, ${Math.abs(s.lon).toFixed(2)}°${s.lon < 0 ? "W" : "E"}`; }

  function gapLine(f) {
    const n = FEAT[f.feature] || f.feature, u = f.units || "";
    const dir = f.absolute_gap > 0 ? "higher" : "lower";
    return `<b>${esc(n)}</b>: Earth ${fmt(f.value)} ${esc(u)} vs target ${fmt(f.target_median)} ${esc(u)}`
      + ` (${fmt(Math.abs(f.absolute_gap))} ${esc(u)} ${dir})`;
  }

  function build(c) {
    const s = c.site, t = tkey(c.target), g = s.group_scores || {};
    const pct = Math.round((s.site_score || 0) * 100);
    const entries = Object.entries(g).sort((a, b) => b[1] - a[1]);
    const weakest = entries.length ? entries[entries.length - 1][0] : null;
    const name = s.famous_name || coords(s);
    const rel = (s.features || []).find(f => f.feature === "relief_20km_m");
    return `<div class="pn" role="dialog" aria-label="Site detail: ${esc(name)}" tabindex="-1">
<button class="pn-x" aria-label="Close site panel">&times;</button>
<h2>${esc(name)}</h2>
<div class="pn-coord">${s.famous_name ? esc(coords(s)) : "&nbsp;"}</div>
<div class="pn-hero"><div class="pn-pct" aria-label="${pct} percent match">${pct}<sup>%</sup></div></div>
<section>
${entries.map(([k, v]) => `<div class="pn-bar${k === weakest && entries.length > 1 ? " weak" : ""}"><span>${esc(GROUP[k] || k)}</span>
<div class="pn-trk" role="img" aria-label="${esc(GROUP[k] || k)} ${Math.round(v * 100)} percent"><div class="pn-fill" style="width:${(v * 100).toFixed(0)}%"></div></div><b>${Math.round(v * 100)}</b></div>`).join("")}
</section>
<div class="pn-elev"><span>Elevation <b id="pn-elev">&hellip;</b></span>${rel ? `<span>Relief <b>${Math.round(rel.value).toLocaleString()} m</b></span>` : ""}</div>
<p class="pn-cant">Not replicable on Earth: ${t === "mars" ? "gravity &middot; thin air &middot; radiation" : "gravity &middot; vacuum &middot; radiation"}</p>
<button class="pn-cmp" type="button">Compare</button>
</div>`;
  }

  function loadPlotly() {
    if (window.Plotly) return Promise.resolve(window.Plotly);
    return plotlyP || (plotlyP = new Promise((res, rej) => {
      const el = document.createElement("script");
      el.src = "https://cdn.plot.ly/plotly-2.35.2.min.js";
      el.onload = () => res(window.Plotly); el.onerror = () => { plotlyP = null; rej(); };
      document.head.appendChild(el);
    }));
  }

  function groupMeans(c, key) {
    const out = {};
    (c.site.features || []).forEach(f => { if (f.qualitative || f[key] == null) return; (out[f.group] = out[f.group] || []).push(f[key]); });
    return Object.fromEntries(Object.entries(out).map(([k, a]) => [k, a.reduce((x, y) => x + y, 0) / a.length]));
  }

  function openModal() {
    const c = cur; if (!c) return;
    closeModal();
    const m = document.createElement("div"); m.id = "pn-modal";
    m.innerHTML = `<div class="pm" role="dialog" aria-modal="true" aria-labelledby="pn-mt"><button class="pn-x" aria-label="Close comparison">&times;</button>
<h2 id="pn-mt">Earth site vs ${esc(TARGET[c.target] || TARGET[tkey(c.target)])}</h2>
<p>Match by group, 0 to 100. The outer ring is a perfect match to the target.</p><div id="pn-radar"><p style="padding:150px 0;text-align:center">Loading chart</p></div></div>`;
    document.body.appendChild(m);
    m.addEventListener("mousedown", e => { if (e.target === m) closeModal(); });
    m.querySelector(".pn-x").addEventListener("click", closeModal);
    m.querySelector(".pn-x").focus();
    const g = c.site.group_scores || {}, keys = Object.keys(g), lab = keys.map(k => GROUP[k] || k);
    const abs = groupMeans(c, "absolute_similarity");
    const close = a => a.concat(a[0]);
    loadPlotly().then(P => {
      if (!document.getElementById("pn-radar")) return;
      const tr = (name, r, line, extra) => Object.assign({ type: "scatterpolar", name, r: close(r), theta: close(lab), line, hovertemplate: "%{theta}: %{r:.0f}<extra>" + name + "</extra>" }, extra);
      P.newPlot("pn-radar", [
        tr("Target (perfect match)", keys.map(() => 100), { color: "#0C2526", width: 1.5, dash: "dash" }),
        tr("Earth site: rank match", keys.map(k => g[k] * 100), { color: "#D9532F", width: 2.5 }, { fill: "toself", fillcolor: "rgba(217,83,47,.25)" }),
        tr("Earth site: real-unit closeness", keys.map(k => (abs[k] == null ? g[k] : abs[k]) * 100), { color: "#0C2526", width: 2 }, { fill: "none" })
      ], { polar: { bgcolor: "rgba(0,0,0,0)", radialaxis: { range: [0, 100], tickfont: { size: 10 }, gridcolor: "rgba(12,37,38,.18)" }, angularaxis: { tickfont: { size: 11, color: "#0C2526" } } },
        paper_bgcolor: "rgba(0,0,0,0)", font: { family: "DM Sans, sans-serif", color: "#0C2526" }, margin: { t: 20, b: 50, l: 70, r: 70 },
        legend: { orientation: "h", y: -0.08, font: { size: 11 } } }, { displayModeBar: false, responsive: true });
    }).catch(() => { const r = document.getElementById("pn-radar"); if (r) r.innerHTML = `<p style="padding:150px 0;text-align:center">Chart library could not load (network).</p>`; });
  }
  function closeModal() { const m = document.getElementById("pn-modal"); if (m) { m.remove(); const b = root() && root().querySelector(".pn-cmp"); if (b) b.focus(); return true; } return false; }

  function show(c) {
    if (!c || !c.site) return;
    opener = document.activeElement; cur = c;
    root().innerHTML = build(c);
    const p = root().querySelector(".pn");
    p.querySelector(".pn-x").addEventListener("click", hide);
    p.querySelector(".pn-cmp").addEventListener("click", openModal);
    p.focus({ preventScroll: true });
  }
  function hide() {
    closeModal(); cur = null; root().innerHTML = "";
    if (opener && opener.focus && document.contains(opener)) opener.focus();
  }
  document.addEventListener("keydown", e => {
    if (e.key !== "Escape") return;
    if (closeModal()) return;
    if (cur) hide();
  });
  function setElevation(m) { const el = document.getElementById("pn-elev"); if (el) el.textContent = Math.round(m).toLocaleString() + " m"; }
  window.Panel = { show, hide, setElevation };
})();
