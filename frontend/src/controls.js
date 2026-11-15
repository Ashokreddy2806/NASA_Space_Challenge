import { FEATURE_LABELS, PRESET_LABELS, PRESET_ORDER, REASON_LABELS, TARGET_LABELS } from './labels.js';

function toggle(label, pressed, onClick) {
  const button = document.createElement('button');
  button.type = 'button';
  button.textContent = label;
  button.setAttribute('aria-pressed', String(pressed));
  button.addEventListener('click', onClick);
  return button;
}

function unscoredReason(target, key) {
  const missing = Object.keys(target.presets[key].weights).filter((f) => !target.features_scored.includes(f));
  const details = missing.map((f) => `${FEATURE_LABELS[f]} (${REASON_LABELS[target.not_scored[f]] ?? target.not_scored[f]})`);
  return `needs ${details.join(', ')}`;
}

function slider(feature, value, onChange) {
  const row = document.createElement('div');
  row.className = 'slider';
  row.innerHTML = `<div class="slider-head"><label for="w-${feature}">${FEATURE_LABELS[feature]}</label><output>${value.toFixed(2)}</output></div><input type="range" id="w-${feature}" min="0" max="4" step="0.05" value="${value}" />`;
  const input = row.querySelector('input');
  const output = row.querySelector('output');
  const paint = () => input.style.setProperty('--fill', `${(input.value / input.max) * 100}%`);
  input.addEventListener('input', () => {
    output.textContent = Number(input.value).toFixed(2);
    paint();
    onChange(feature, Number(input.value));
  });
  paint();
  return row;
}

export function renderTargets(targets, current, onPick) {
  document.getElementById('targets').replaceChildren(
    ...targets.map((t) => toggle(TARGET_LABELS[t.id], t.id === current, () => onPick(t.id))),
  );
}

export function renderPresets(target, current, onPick) {
  const notes = [];
  const buttons = PRESET_ORDER.map((key) => {
    const { available } = target.presets[key];
    const button = toggle(PRESET_LABELS[key], key === current, () => available && onPick(key));
    button.setAttribute('aria-disabled', String(!available));
    if (!available) {
      const reason = unscoredReason(target, key);
      button.title = `${PRESET_LABELS[key]} ${reason}`;
      notes.push(`${PRESET_LABELS[key]} unavailable: ${reason}.`);
    }
    return button;
  });
  document.getElementById('presets').replaceChildren(...buttons);
  document.getElementById('preset-note').textContent = notes.join(' ');
}

export function renderSliders(target, weights, onChange) {
  document.getElementById('sliders').replaceChildren(
    ...target.features_scored.map((f) => slider(f, weights[f], onChange)),
  );
}
