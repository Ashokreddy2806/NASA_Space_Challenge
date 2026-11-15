import Plotly from 'plotly.js-dist-min';
import { FEATURE_LABELS, PRESET_HELP, PRESET_LABELS, REASON_LABELS, TARGET_LABELS } from './labels.js';

const RING_RADIUS = 46;
const RING_LENGTH = 2 * Math.PI * RING_RADIUS;
const VERDICT = { match: 'Match', partial: 'Partial', mismatch: 'Mismatch' };
const FONT = 'Inter, "Segoe UI", system-ui, sans-serif';

const format = (value) => (Math.abs(value) >= 100 ? value.toFixed(0) : value.toFixed(2));

function formatCoord(lat, lon) {
  const ns = lat >= 0 ? 'N' : 'S';
  const ew = lon >= 0 ? 'E' : 'W';
  return `${Math.abs(lat).toFixed(2)}° ${ns}, ${Math.abs(lon).toFixed(2)}° ${ew}`;
}

function ring(score) {
  const offset = RING_LENGTH * (1 - score / 100);
  return `<div class="ring-wrap">
    <svg class="ring" viewBox="0 0 120 120" aria-hidden="true">
      <circle class="ring-track" cx="60" cy="60" r="${RING_RADIUS}"></circle>
      <circle class="ring-value" cx="60" cy="60" r="${RING_RADIUS}" stroke-dasharray="${RING_LENGTH}" stroke-dashoffset="${offset}"></circle>
    </svg>
    <div class="ring-text"><span>${Math.round(score)}</span><small>of 100</small></div>
  </div>`;
}

function featureRow(f) {
  return `<li class="feature ${f.verdict}">
    <div class="feature-head"><span>${FEATURE_LABELS[f.feature]}</span><span class="pill">${VERDICT[f.verdict]}</span></div>
    <div class="values"><span>Earth <b>${format(f.earth_value)}</b> ${f.units}</span><span>Target <b>${format(f.target_value)}</b> ${f.units}</span></div>
    <div class="bar" title="Sub-score ${Math.round(f.sub_score)} of 100"><span style="width:${f.sub_score}%"></span></div>
  </li>`;
}

function mismatchList(site) {
  if (site.does_not_match.length === 0) return '<p class="note">No scored feature falls in the mismatch band.</p>';
  const byKey = Object.fromEntries(site.features.map((f) => [f.feature, f]));
  const items = site.does_not_match.map((key) => {
    const f = byKey[key];
    return `<li><span>${FEATURE_LABELS[key]}</span><em>Earth ${format(f.earth_value)} · target ${format(f.target_value)} ${f.units}</em></li>`;
  });
  return `<ul class="plain">${items.join('')}</ul>`;
}

function body(site, preset) {
  const notScored = Object.entries(site.not_scored).map(
    ([key, reason]) => `<li><span>${FEATURE_LABELS[key]}</span><em>${REASON_LABELS[reason] ?? reason}</em></li>`,
  );
  const cannot = site.earth_cannot_replicate.map((text) => `<li>${text}</li>`);
  return `
    <section class="summary">
      ${ring(site.score)}
      <p>Overall similarity of this Earth location to the selected target, on a 0 to 100 scale.</p>
    </section>
    <section class="section">
      <span class="eyebrow">Per-feature sub-scores</span>
      <div class="radar" id="radar"></div>
    </section>
    <section class="section">
      <span class="eyebrow">Feature comparison</span>
      <ul class="features">${site.features.map(featureRow).join('')}</ul>
    </section>
    <section class="section alert">
      <span class="eyebrow">What does not match</span>
      ${mismatchList(site)}
    </section>
    <section class="section">
      <span class="eyebrow">Not scored</span>
      <ul class="plain muted">${notScored.join('')}</ul>
    </section>
    <section class="section callout">
      <span class="eyebrow">Earth cannot replicate</span>
      <ul class="bullets">${cannot.join('')}</ul>
    </section>
    <section class="section guide">
      <span class="eyebrow">How this helps exploration</span>
      <p>${PRESET_HELP[preset]}</p>
      <span class="tag">Guidance, not data</span>
    </section>`;
}

const radarLayout = {
  paper_bgcolor: 'rgba(0,0,0,0)',
  plot_bgcolor: 'rgba(0,0,0,0)',
  margin: { l: 56, r: 56, t: 28, b: 28 },
  height: 280,
  showlegend: false,
  font: { family: FONT, color: '#8a92a6', size: 10 },
  polar: {
    bgcolor: 'rgba(0,0,0,0)',
    radialaxis: {
      range: [0, 100],
      tickvals: [25, 50, 75, 100],
      gridcolor: 'rgba(255,255,255,0.08)',
      linecolor: 'rgba(255,255,255,0.0)',
      tickfont: { size: 9, color: '#6b7388' },
    },
    angularaxis: {
      gridcolor: 'rgba(255,255,255,0.08)',
      linecolor: 'rgba(255,255,255,0.12)',
      tickfont: { size: 10, color: '#c9d1e0' },
    },
  },
};

function drawRadar(features) {
  const theta = features.map((f) => FEATURE_LABELS[f.feature]);
  const r = features.map((f) => f.sub_score);
  Plotly.react(
    'radar',
    [
      {
        type: 'scatterpolar',
        r: [...r, r[0]],
        theta: [...theta, theta[0]],
        fill: 'toself',
        fillcolor: 'rgba(94,234,212,0.16)',
        line: { color: '#5eead4', width: 2 },
        marker: { size: 5, color: '#5eead4' },
        hovertemplate: '%{theta}: %{r:.0f} / 100<extra></extra>',
      },
    ],
    radarLayout,
    { displayModeBar: false, responsive: true },
  );
}

export function showSite(site, preset, custom) {
  document.getElementById('panel-coords').textContent = formatCoord(site.lat, site.lon);
  document.getElementById('panel-context').textContent =
    `${TARGET_LABELS[site.target]} · ${custom ? 'Custom weights' : PRESET_LABELS[preset]}`;
  document.getElementById('panel-body').innerHTML = body(site, preset);
  drawRadar(site.features);
  document.getElementById('panel').classList.add('open');
}

export function hidePanel() {
  document.getElementById('panel').classList.remove('open');
}
