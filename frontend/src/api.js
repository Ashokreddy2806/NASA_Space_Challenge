const API = '/api';

function assertOk(res) {
  if (!res.ok) throw new Error(`${res.status} ${res.url}`);
  return res;
}

function scoringQuery({ preset, weights }) {
  const query = new URLSearchParams();
  if (weights) query.set('weights', JSON.stringify(weights));
  else query.set('preset', preset);
  return query.toString();
}

export async function fetchTargets() {
  return assertOk(await fetch(`${API}/targets`)).json();
}

export async function fetchTopSites(target, preset, excludeFamous) {
  const query = new URLSearchParams({ preset, exclude_famous: excludeFamous, format: 'geojson' });
  return assertOk(await fetch(`${API}/targets/${target}/top-sites?${query}`)).json();
}

export async function fetchSite(target, lat, lon, scoring) {
  const res = await fetch(`${API}/targets/${target}/site?lat=${lat}&lon=${lon}&${scoringQuery(scoring)}`);
  if (res.status === 404) return null;
  return assertOk(res).json();
}

export async function fetchScoreImage(target, scoring) {
  const res = await fetch(`${API}/targets/${target}/score.png?${scoringQuery(scoring)}&step=2`);
  return assertOk(res).blob();
}
