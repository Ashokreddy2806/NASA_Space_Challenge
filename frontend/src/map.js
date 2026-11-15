import { MapLibreMap, setWorkerUrl } from 'maplibre-gl';
import maplibreWorkerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?url';
import { MapboxOverlay } from '@deck.gl/mapbox';
import { ScatterplotLayer, TextLayer } from '@deck.gl/layers';
import { MERCATOR_LAT_LIMIT } from './reproject.js';

const STYLE_URL = 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json';
const SCORE_SOURCE = 'score';
const SCORE_LAYER = 'score';
const SITE_LAYER = 'top-sites';
const INK = [5, 7, 14, 255];
const ACCENT = [94, 234, 212];
const FONT = 'Inter, "Segoe UI", system-ui, sans-serif';
const COORDINATES = [
  [-180, MERCATOR_LAT_LIMIT],
  [180, MERCATOR_LAT_LIMIT],
  [180, -MERCATOR_LAT_LIMIT],
  [-180, -MERCATOR_LAT_LIMIT],
];

const position = (feature) => feature.geometry.coordinates;

function firstSymbolLayer(map) {
  return map.getStyle().layers.find((layer) => layer.type === 'symbol')?.id;
}

export function createMap(container, onSelect) {
  setWorkerUrl(maplibreWorkerUrl);
  const map = new MapLibreMap({
    container,
    style: STYLE_URL,
    center: [0, 15],
    zoom: 1.8,
    minZoom: 1.2,
    renderWorldCopies: false,
  });
  const overlay = new MapboxOverlay({ layers: [] });
  const tooltip = document.createElement('div');
  tooltip.className = 'tooltip';
  tooltip.hidden = true;
  container.append(tooltip);

  let sites = [];
  let selected = null;

  function pickSite(point) {
    return overlay.pickObject({ x: point.x, y: point.y, radius: 12, layerIds: [SITE_LAYER] })?.object ?? null;
  }

  function render() {
    overlay.setProps({
      layers: [
        new ScatterplotLayer({
          id: 'site-glow',
          data: sites,
          getPosition: position,
          getRadius: 24,
          radiusUnits: 'pixels',
          getFillColor: [...ACCENT, 46],
        }),
        new ScatterplotLayer({
          id: SITE_LAYER,
          data: sites,
          pickable: true,
          getPosition: position,
          getRadius: 11,
          radiusUnits: 'pixels',
          getFillColor: [...ACCENT, 255],
          stroked: true,
          getLineColor: INK,
          getLineWidth: 2,
          lineWidthUnits: 'pixels',
        }),
        new TextLayer({
          id: 'site-rank',
          data: sites,
          getPosition: position,
          getText: (feature) => String(feature.properties.rank),
          getColor: INK,
          getSize: 12,
          sizeUnits: 'pixels',
          fontFamily: FONT,
          fontWeight: 700,
          getTextAnchor: 'middle',
          getAlignmentBaseline: 'center',
        }),
        new ScatterplotLayer({
          id: 'selected',
          data: selected ? [selected] : [],
          getPosition: (site) => [site.lon, site.lat],
          getRadius: 17,
          radiusUnits: 'pixels',
          filled: false,
          stroked: true,
          getLineColor: [255, 255, 255, 235],
          getLineWidth: 2,
          lineWidthUnits: 'pixels',
        }),
      ],
    });
  }

  map.addControl(overlay);

  map.on('mousemove', (event) => {
    const site = pickSite(event.point);
    map.getCanvas().style.cursor = site ? 'pointer' : '';
    tooltip.hidden = !site;
    if (!site) return;
    const { rank, score } = site.properties;
    tooltip.innerHTML = `<b>Rank ${rank}</b> score ${score.toFixed(1)}<span>Click to inspect</span>`;
    tooltip.style.transform = `translate(${event.point.x + 16}px, ${event.point.y + 16}px)`;
  });

  map.on('mouseout', () => {
    tooltip.hidden = true;
  });

  map.on('click', (event) => {
    const site = pickSite(event.point);
    if (site) return onSelect(site.geometry.coordinates[1], site.geometry.coordinates[0]);
    const { lat, lng } = event.lngLat.wrap();
    onSelect(lat, lng);
  });

  return new Promise((resolve) => {
    map.on('load', () => {
      map.addSource(SCORE_SOURCE, { type: 'image', coordinates: COORDINATES });
      map.addLayer(
        {
          id: SCORE_LAYER,
          type: 'raster',
          source: SCORE_SOURCE,
          paint: { 'raster-opacity': 0.92, 'raster-fade-duration': 0 },
        },
        firstSymbolLayer(map),
      );
      render();
      resolve({
        setScore(canvas) {
          map.getSource(SCORE_SOURCE).updateImage({ image: canvas });
        },
        setSites(features) {
          sites = features;
          render();
        },
        setSelected(lat, lon) {
          selected = { lat, lon };
          render();
        },
      });
    });
  });
}
