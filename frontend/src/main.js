import './style.css';
import 'maplibre-gl/dist/maplibre-gl.css';
import { fetchScoreImage, fetchSite, fetchTargets, fetchTopSites } from './api.js';
import { createMap } from './map.js';
import { reprojectToMercator } from './reproject.js';
import { renderPresets, renderSliders, renderTargets } from './controls.js';
import { hidePanel, showSite } from './panel.js';

const MAP_TEXTURE_SIZE = 2048;
const WEIGHT_DEBOUNCE_MS = 300;
const TOAST_MS = 2400;

const state = {
  targets: [],
  target: null,
  preset: 'balanced',
  excludeFamous: false,
  weights: null,
  selected: null,
};
let view;
let scoreRequest = 0;
let siteListRequest = 0;
let selectRequest = 0;
let toastTimer;

const currentTarget = () => state.targets.find((t) => t.id === state.target);
const scoring = () => (state.weights ? { weights: state.weights } : { preset: state.preset });

function presetWeights(target, preset) {
  const weights = target.presets[preset].weights;
  return Object.fromEntries(target.features_scored.map((f) => [f, weights[f] ?? 0]));
}

const scoredWeights = () => state.weights ?? presetWeights(currentTarget(), state.preset);

function debounce(fn, ms) {
  let timer;
  return () => {
    clearTimeout(timer);
    timer = setTimeout(fn, ms);
  };
}

function showToast(text) {
  const toast = document.getElementById('toast');
  toast.textContent = text;
  toast.classList.add('show');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove('show'), TOAST_MS);
}

function renderControls() {
  const target = currentTarget();
  renderTargets(state.targets, state.target, setTarget);
  renderPresets(target, state.preset, setPreset);
  renderSliders(target, scoredWeights(), setWeight);
  document.getElementById('custom-badge').hidden = !state.weights;
}

async function refreshScore() {
  const id = ++scoreRequest;
  const image = await fetchScoreImage(state.target, scoring());
  const bitmap = await createImageBitmap(image);
  if (id === scoreRequest) view.setScore(reprojectToMercator(bitmap, MAP_TEXTURE_SIZE));
}

async function refreshSiteList() {
  const id = ++siteListRequest;
  const geojson = await fetchTopSites(state.target, state.preset, state.excludeFamous);
  if (id === siteListRequest) view.setSites(geojson.features);
}

async function selectPoint(lat, lon) {
  const id = ++selectRequest;
  const site = await fetchSite(state.target, lat, lon, scoring());
  if (id !== selectRequest) return;
  if (!site) return showToast('Ocean: no data at this point');
  state.selected = { lat: site.lat, lon: site.lon };
  view.setSelected(site.lat, site.lon);
  showSite(site, state.preset, Boolean(state.weights));
}

function refreshSelected() {
  if (state.selected) selectPoint(state.selected.lat, state.selected.lon);
}

function refreshAll() {
  refreshScore();
  refreshSiteList();
  refreshSelected();
}

const scheduleWeightRefresh = debounce(() => {
  refreshScore();
  refreshSelected();
}, WEIGHT_DEBOUNCE_MS);

function setTarget(id) {
  state.target = id;
  state.weights = null;
  if (!currentTarget().presets[state.preset].available) state.preset = 'balanced';
  renderControls();
  refreshAll();
}

function setPreset(key) {
  state.preset = key;
  state.weights = null;
  renderControls();
  refreshAll();
}

function setWeight(feature, value) {
  state.weights = { ...scoredWeights(), [feature]: value };
  document.getElementById('custom-badge').hidden = false;
  scheduleWeightRefresh();
}

function resetWeights() {
  state.weights = null;
  renderControls();
  refreshAll();
}

function bindControls() {
  document.getElementById('exclude-famous').addEventListener('change', (event) => {
    state.excludeFamous = event.target.checked;
    refreshSiteList();
  });
  document.getElementById('reset-weights').addEventListener('click', resetWeights);
  document.getElementById('close-panel').addEventListener('click', hidePanel);
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') hidePanel();
  });
}

async function init() {
  state.targets = await fetchTargets();
  state.target = state.targets[0].id;
  bindControls();
  renderControls();
  view = await createMap(document.getElementById('map'), selectPoint);
  refreshAll();
}

init();
