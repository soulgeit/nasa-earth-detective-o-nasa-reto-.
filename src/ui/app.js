(function() {
'use strict';
// SI-assisted: claude-omni-1 (Claude Sonnet 5.5)
// EarthTrend Detective — frontend interface logic.
// All scientific numbers, statistical analyses, and trend lines come exclusively
// from the real API endpoints (/api/analyze, /api/trendmap, /api/compare, etc.).
// No synthetic or placeholder data generators exist in this codebase.

const { t, applyTranslations, formatUnit = (u) => u } = window.__etdI18n;

const API_BASE = window.ETD_API_BASE || '';

const state = {
  mode: 'single', // 'single' | 'trendmap' | 'compare'
  health: null,
  catalog: [],
  regions: [],
  cases: [],
  analysis: null,
  trendmap: null,
  compare: null,
  view: 'monthly', // 'monthly' | 'anomalies' | 'annual'
  point: null,
  pointCompareB: null,
  locationName: null,
  locationNameB: null,
  placeLabel: null, // real place name (geocoder or frozen case); null for a bare map click
  bbox: null,
  lang: window.__etdLang || 'en',
};

let map = null;
let marker = null;
let markerB = null;
let rect = null;
let trendmapLayer = null;
let chart = null;
let chartCompareA = null;
let chartCompareB = null;
let mapReady = false;

const VERDICT_TIER = {
  INSUFFICIENT_DATA: 1,
  NOT_SIGNIFICANT: 2,
  SUGGESTIVE: 3,
  SIGNIFICANT: 4,
  SIGNIFICANT_STRONG: 5,
};

/* ---------------------------------------------------------------- helpers */

function $(sel) { return document.querySelector(sel); }

function el(tag, attrs, text) {
  const node = document.createElement(tag);
  if (attrs) for (const k of Object.keys(attrs)) node.setAttribute(k, attrs[k]);
  if (text !== undefined) node.textContent = text;
  return node;
}

function fmt(n, digits = 2) {
  if (n === null || n === undefined || Number.isNaN(n)) return '—';
  return Number(n).toLocaleString(state.lang === 'es' ? 'es-PE' : 'en-US', {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });
}

function signed(n, digits = 2) {
  if (n === null || n === undefined || Number.isNaN(n)) return '—';
  return (n > 0 ? '+' : '') + fmt(n, digits);
}

function fmtP(p) {
  if (p === null || p === undefined || Number.isNaN(p)) return '—';
  if (p < 0.001) return '< 0.001';
  return fmt(p, 3);
}

class ApiError extends Error {
  constructor(code, message, hint) {
    super(message);
    this.code = code;
    this.hint = hint;
  }
}

async function apiGet(path, params) {
  const url = new URL(`${API_BASE}${path}`, location.href);
  if (params) {
    for (const [k, v] of Object.entries(params)) {
      if (v !== null && v !== undefined) url.searchParams.set(k, v);
    }
  }
  let res;
  try {
    res = await fetch(url.toString(), { headers: { Accept: 'application/json' } });
  } catch (_) {
    throw new ApiError('API_UNAVAILABLE', t('error.body'));
  }
  let body = null;
  try { body = await res.json(); } catch (_) { /* not JSON */ }
  if (!res.ok) {
    const e = (body && body.error) || {};
    const msg = e.message && typeof e.message === 'object'
      ? (e.message[state.lang] || e.message.en || e.message.es)
      : (e.message || t('error.body'));
    throw new ApiError(e.code || 'UPSTREAM_ERROR', msg, e.hint);
  }
  return body;
}

async function apiPost(path, data) {
  const url = `${API_BASE}${path}`;
  let res;
  try {
    res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
      body: JSON.stringify(data),
    });
  } catch (_) {
    throw new ApiError('API_UNAVAILABLE', t('error.body'));
  }
  let body = null;
  try { body = await res.json(); } catch (_) { /* not JSON */ }
  if (!res.ok) {
    const e = (body && body.error) || {};
    const msg = e.message && typeof e.message === 'object'
      ? (e.message[state.lang] || e.message.en || e.message.es)
      : (e.message || t('error.body'));
    throw new ApiError(e.code || 'UPSTREAM_ERROR', msg, e.hint);
  }
  return body;
}

/* ---------------------------------------------------------------- errors */

function showError(err) {
  const box = $('#error-state');
  if (!box) return;
  box.hidden = false;
  $('#error-code').textContent = err.code ? `${t('error.code')}: ${err.code}` : '';
  const msg = err.message || String(err);
  const isGeneric = msg === t('error.body');
  $('#error-message').textContent = isGeneric ? '' : msg;
}

function clearError() {
  const box = $('#error-state');
  if (box) box.hidden = true;
}

/* ---------------------------------------------------------------- variable & region naming */

function getCleanVariableName(varId) {
  if (!varId) return '';
  const card = state.catalog.find(v => v.id === varId);
  if (card) {
    const name = card.names?.[state.lang] || card.names?.es || card.names?.en || card.power_longname;
    if (name) return name;
  }
  if (state.plannedCatalog) {
    const pCard = state.plannedCatalog.find(v => v.id === varId);
    if (pCard) {
      const name = pCard.names?.[state.lang] || pCard.names?.es || pCard.names?.en;
      if (name) return name;
    }
  }
  // QA D8: Map raw Giovanni parameter identifiers to clean names
  if (/T2M/i.test(varId)) {
    return state.lang === 'es' ? 'Temperatura del aire a 2 m' : 'Air temperature at 2 m';
  }
  if (/PREC/i.test(varId)) {
    return state.lang === 'es' ? 'Precipitación' : 'Precipitation';
  }
  if (/SOIL|GWET/i.test(varId)) {
    return state.lang === 'es' ? 'Humedad del suelo' : 'Soil moisture';
  }
  if (/NDVI/i.test(varId)) {
    return state.lang === 'es' ? 'Índice de vegetación NDVI' : 'NDVI vegetation index';
  }
  if (/AOD/i.test(varId)) {
    return state.lang === 'es' ? 'Espesor óptico de aerosoles' : 'Aerosol optical depth';
  }
  if (/O3|OZONE/i.test(varId)) {
    return state.lang === 'es' ? 'Ozono total en columna' : 'Total column ozone';
  }
  return varId;
}

function getCleanRegionName(analysis) {
  if (!analysis) return '';
  const r = analysis.region || {};
  if (r.name && r.name !== 'None' && r.name !== 'la región analizada' && r.name !== 'Ubicación' && r.name !== 'Location') {
    return r.name;
  }
  if (state.locationName && state.locationName !== 'None') {
    return state.locationName;
  }
  if (r.lat !== undefined && r.lat !== null && r.lon !== undefined && r.lon !== null) {
    return `${Number(r.lat).toFixed(2)}°, ${Number(r.lon).toFixed(2)}°`;
  }
  return state.lang === 'es' ? 'Región analizada' : 'Analyzed region';
}

function sanitizeText(txt, varId, regionName) {
  if (!txt) return '';
  let out = txt;
  if (varId) {
    const cleanVar = getCleanVariableName(varId);
    out = out.replace(new RegExp(`^${varId}\\s*se\\s*encuentra`, 'i'), `${cleanVar} se encuentra`);
    out = out.replace(new RegExp(`^${varId}\\s*presents`, 'i'), `${cleanVar} presents`);
    out = out.replace(new RegExp(`^${varId}:`, 'i'), `${cleanVar}:`);
    if (varId.includes('M2SMNXSLV')) {
      out = out.replaceAll(varId, cleanVar);
    }
  }
  out = out.replace(/Observado en None/gi, `Observado en ${regionName}`);
  out = out.replace(/Observed in None/gi, `Observed in ${regionName}`);
  out = out.replace(/\bNone\b/g, regionName);

  // Ronda 5: Spanish unit translations in all rendered text
  if (state.lang === 'es') {
    out = out.replace(/million km²/g, 'millones de km²')
             .replace(/million km2/g, 'millones de km²')
             .replace(/\bmillion\b/g, 'millones')
             .replace(/mm\/day/g, 'mm/día')
             .replace(/MJ\/m²\/day/g, 'MJ/m²/día')
             .replace(/MJ\/m2\/day/g, 'MJ/m²/día')
             .replace(/fraction \(0-1\)/g, 'fracción (0-1)')
             .replace(/\bdimensionless\b/g, 'adimensional')
             .replace(/°C \(anomaly vs 1951-1980\)/g, '°C (anomalía respecto a 1951-1980)');
  }
  return out;
}

/* ---------------------------------------------------------------- map */

function initMap() {
  if (typeof L === 'undefined') {
    const frame = document.querySelector('.map-frame');
    if (frame) frame.hidden = true;
    return;
  }
  map = L.map('map', { worldCopyJump: true, minZoom: 2 }).setView([-12.05, -77.03], 4);

  const gibs = L.tileLayer(
    'https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/BlueMarble_ShadedRelief_Bathymetry/default/2020-08-01/GoogleMapsCompatible_Level8/{z}/{y}/{x}.jpeg',
    { maxZoom: 8, attribution: 'Imagery: NASA GIBS (public domain)' }
  );
  const osm = L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
  });

  gibs.on('tileerror', () => {
    if (map.hasLayer(gibs)) { map.removeLayer(gibs); osm.addTo(map); }
  });
  gibs.addTo(map);

  trendmapLayer = L.layerGroup().addTo(map);
  mapReady = true;

  map.on('click', (ev) => {
    if (state.mode === 'compare') {
      if (!state.point) {
        setPointA(ev.latlng.lat, ev.latlng.lng);
      } else {
        setPointB(ev.latlng.lat, ev.latlng.lng);
      }
    } else {
      setPoint(ev.latlng.lat, ev.latlng.lng);
    }
  });

  let dragStart = null;
  map.on('mousedown', (ev) => {
    if (ev.originalEvent && ev.originalEvent.shiftKey) { dragStart = ev.latlng; map.dragging.disable(); }
  });
  map.on('mouseup', (ev) => {
    if (!dragStart) return;
    const a = dragStart, b = ev.latlng;
    dragStart = null;
    map.dragging.enable();
    const south = Math.min(a.lat, b.lat), north = Math.max(a.lat, b.lat);
    const west = Math.min(a.lng, b.lng), east = Math.max(a.lng, b.lng);
    if (Math.abs(north - south) < 0.05 || Math.abs(east - west) < 0.05) return;
    setBBox([west, south, east, north]);
  });
}

function setPoint(lat, lon, label) {
  state.point = { lat, lon };
  state.bbox = null;
  state.placeLabel = label || null;
  state.locationName = label || `${lat.toFixed(2)}°, ${lon.toFixed(2)}°`;
  if (map) {
    if (marker) marker.remove();
    if (rect) { rect.remove(); rect = null; }
    marker = L.circleMarker([lat, lon], {
      radius: 7, color: '#16272b', weight: 2, fillColor: '#125e5a', fillOpacity: 1,
    }).addTo(map);
  }
  $('#place-chosen').textContent = state.locationName;
  const sc = $('#scout-bar');
  if (sc) sc.hidden = false;
}

function setPointA(lat, lon, label) {
  state.point = { lat, lon };
  state.locationName = label || `A (${lat.toFixed(2)}°, ${lon.toFixed(2)}°)`;
  if (map) {
    if (marker) marker.remove();
    marker = L.circleMarker([lat, lon], {
      radius: 7, color: '#16272b', weight: 2, fillColor: '#125e5a', fillOpacity: 1,
    }).addTo(map).bindPopup('A');
  }
  $('#place-chosen').textContent = state.locationName;
}

function setPointB(lat, lon, label) {
  state.pointCompareB = { lat, lon };
  state.locationNameB = label || `B (${lat.toFixed(2)}°, ${lon.toFixed(2)}°)`;
  if (map) {
    if (markerB) markerB.remove();
    markerB = L.circleMarker([lat, lon], {
      radius: 7, color: '#16272b', weight: 2, fillColor: '#a2610f', fillOpacity: 1,
    }).addTo(map).bindPopup('B');
  }
  $('#place-chosen-b').textContent = state.locationNameB;
}

function setBBox(bbox) {
  state.bbox = bbox;
  state.point = null;
  state.placeLabel = null;
  state.locationName = `[${bbox.map(v => v.toFixed(2)).join(', ')}]`;
  if (map) {
    if (marker) { marker.remove(); marker = null; }
    if (rect) rect.remove();
    const [[w, s], [e, n]] = [[bbox[0], bbox[1]], [bbox[2], bbox[3]]];
    rect = L.rectangle([[s, w], [n, e]], { color: '#16272b', weight: 2, fillColor: '#125e5a', fillOpacity: 0.12 }).addTo(map);
  }
  $('#place-chosen').textContent = state.locationName;
  if (state.mode === 'trendmap') {
    $('#trendmap-bar').hidden = false;
  }
}

/* ---------------------------------------------------------------- search */

async function searchPlace(q, isB = false) {
  const list = $(isB ? '#place-results-b' : '#place-results');
  if (list) list.innerHTML = '';
  if (!q || q.length < 2) return;
  try {
    const data = await apiGet('/api/geocode', { q });
    const items = (data && (data.places || data.results)) || [];
    if (!items.length) {
      $(isB ? '#place-chosen-b' : '#place-chosen').textContent = t('panel.search.noResults');
      return;
    }
    for (const p of items) {
      const opt = el('option', { value: p.name });
      opt.dataset.lat = p.lat;
      opt.dataset.lon = p.lon;
      list.appendChild(opt);
    }
    const first = items[0];
    if (isB) setPointB(first.lat, first.lon, first.name);
    else setPoint(first.lat, first.lon, first.name);
    if (map) map.setView([first.lat, first.lon], 6);
  } catch (err) {
    showError(err);
  }
}

/* ---------------------------------------------------------------- catalog */

const PLANNED_FALLBACK = [
  { id: 'GPM_IMERG_PRECIP', names: { en: 'GPM IMERG precipitation', es: 'Precipitación GPM IMERG' } },
  { id: 'GLDAS_SOILM_0_10', names: { en: 'Soil moisture 0-10 cm (GLDAS)', es: 'Humedad del suelo 0-10 cm (GLDAS)' } },
  { id: 'GLDAS_EVAP', names: { en: 'Evapotranspiration (GLDAS)', es: 'Evapotranspiración (GLDAS)' } },
  { id: 'GLDAS_RUNOFF', names: { en: 'Runoff (GLDAS)', es: 'Escorrentía (GLDAS)' } },
  { id: 'AIRS_SURF_AIR_TEMP', names: { en: 'Surface air temperature (AIRS)', es: 'Temperatura superficial del aire (AIRS)' } },
  { id: 'OMI_NO2_TROP', names: { en: 'Tropospheric nitrogen dioxide (OMI)', es: 'Dióxido de nitrógeno troposférico (OMI)' } },
  { id: 'OMI_O3_TOTAL', names: { en: 'Total column ozone (OMI)', es: 'Ozono total en columna (OMI)' } },
  { id: 'MODIS_NDVI', names: { en: 'NDVI vegetation index (MODIS)', es: 'Índice de vegetación NDVI (MODIS)' } },
  { id: 'MODIS_LST_DAY', names: { en: 'Daytime land surface temperature (MODIS)', es: 'Temperatura diurna superficie terrestre (MODIS)' } },
  { id: 'MODIS_AOD', names: { en: 'Aerosol optical depth (MODIS)', es: 'Espesor óptico de aerosoles (MODIS)' } },
];

function isPlannedVariable(varId) {
  if (!varId) return false;
  if (state.plannedCatalog && state.plannedCatalog.some(p => p.id === varId)) return true;
  return PLANNED_FALLBACK.some(p => p.id === varId);
}

function renderCatalog() {
  const select = $('#variable-select');
  if (!select) return;
  select.innerHTML = '';

  // 1. Available variables (selectable)
  const available = state.catalog.filter(v => v.available !== false);
  const optgroupAvail = el('optgroup', { label: state.lang === 'es' ? 'Variables disponibles' : 'Available variables' });
  for (const v of available) {
    const optName = v.names?.[state.lang] || v.names?.es || v.names?.en || v.power_longname || v.id;
    const cleanU = formatUnit(v.unit || '', state.lang);
    const opt = el('option', { value: v.id }, `${optName} (${cleanU})`);
    optgroupAvail.appendChild(opt);
  }
  select.appendChild(optgroupAvail);

  // 2. Planned variables (Rule 19: cannot be chosen, disabled)
  const plannedList = (state.plannedCatalog && state.plannedCatalog.length)
    ? state.plannedCatalog
    : PLANNED_FALLBACK;
  const notLoadedLabel = t('detective.plan.not_loaded');
  const optgroupPlanned = el('optgroup', {
    label: state.lang === 'es' ? 'Planificadas (requieren CSV de Giovanni)' : 'Planned (require Giovanni CSV)'
  });
  for (const p of plannedList) {
    const pName = p.names?.[state.lang] || p.names?.es || p.names?.en || p.id;
    const opt = el('option', { value: p.id, disabled: true }, `${pName} — ${notLoadedLabel}`);
    opt.setAttribute('title', notLoadedLabel);
    optgroupPlanned.appendChild(opt);
  }
  select.appendChild(optgroupPlanned);

  onVariableChange();
}

function onVariableChange() {
  const select = $('#variable-select');
  if (!select) return;
  const id = select.value;
  const v = state.catalog.find(x => x.id === id);
  const def = v && v.simple_definition
    ? (v.simple_definition[state.lang] || v.simple_definition.es || v.simple_definition.en)
    : '';
  $('#variable-definition').textContent = def;
}

/* ---------------------------------------------------------------- cases */

async function loadCases() {
  try {
    const data = await apiGet('/api/cases');
    state.cases = (data && data.cases) || [];
  } catch (_) {
    state.cases = [];
  }
  const list = $('#cases-list');
  if (!list) return;
  list.innerHTML = '';
  if (!state.cases.length) {
    list.appendChild(el('p', { class: 'help' }, t('cases.none')));
    return;
  }
  for (const c of state.cases) {
    const btn = el('button', { type: 'button', class: 'btn case-btn' });
    btn.appendChild(el('span', null, caseTitle(c)));
    const sub = caseVerdictLabel(c) || c.description;
    if (sub) btn.appendChild(el('small', null, sub));
    btn.addEventListener('click', () => openCase(c));
    list.appendChild(btn);
  }
}

/* The index publishes bilingual `title`, `names` and `finding`; older builds had `region_name`. */
function caseTitle(c) {
  const L = state.lang;
  return c.title?.[L] || c.title?.en || c.names?.[L] || c.names?.en || c.region_name || c.id || c.region_id;
}

function casePlace(c) {
  const L = state.lang;
  return c.names?.[L] || c.names?.en || c.region?.name || c.region_name || c.id;
}

function caseVerdictLabel(c) {
  if (!c.verdict_code) return '';
  const key = `verdict.${c.verdict_code}`;
  const label = t(key);
  return label && label !== key ? label : '';
}

function caseFinding(c) {
  const L = state.lang;
  return c.finding?.[L] || c.finding?.en || c.description || '';
}

async function openCase(c) {
  clearError();
  const select = $('#variable-select');
  if (select && c.variable_id) {
    select.value = c.variable_id;
    onVariableChange();
  }
  // The position lives under `region` in /api/cases; the static backup also copies it to the root.
  const r = c.region || {};
  const lat = c.lat ?? r.lat;
  const lon = c.lon ?? r.lon;
  const bbox = c.bbox || r.bbox;
  const hasPoint = lat !== undefined && lat !== null && lon !== undefined && lon !== null;
  if (bbox && (r.kind === 'bbox' || !hasPoint)) {
    setBBox(bbox);
    if (map) map.fitBounds([[bbox[1], bbox[0]], [bbox[3], bbox[2]]]);
  } else if (hasPoint) {
    setPoint(Number(lat), Number(lon), casePlace(c));
    if (map) map.setView([Number(lat), Number(lon)], 5);
  } else {
    // Hemispheric or global case: it has no place, so forget the one chosen before.
    state.point = null;
    state.bbox = null;
    state.placeLabel = null;
    state.locationName = casePlace(c);
    if (marker) { marker.remove(); marker = null; }
    if (rect) { rect.remove(); rect = null; }
    const chosen = $('#place-chosen');
    if (chosen) chosen.textContent = state.locationName;
  }
  // A frozen case is shown exactly as it was frozen: same series, same numbers, same provenance.
  if (c.id) {
    try {
      const frozen = await apiGet(`/api/cases/${encodeURIComponent(c.id)}`);
      if (frozen && frozen.analysis && frozen.analysis.schema === 'analysis/2') {
        renderAnalysis(frozen.analysis);
        return;
      }
    } catch (_) { /* a build without this route: fall through to the live analysis */ }
  }
  investigate();
}

/* ---------------------------------------------------------------- investigate */

async function investigate() {
  clearError();
  if (state.mode === 'compare') {
    return runCompare();
  }
  if (state.mode === 'trendmap') {
    return runTrendMap();
  }

  const variableId = $('#variable-select')?.value || 'T2M';
  const FIXED_GLOBAL_VARS = ['GISTEMP_TANOM', 'SEAICE_EXTENT_N', 'SEAICE_EXTENT_S'];
  const isGlobal = FIXED_GLOBAL_VARS.includes(variableId);

  if (!isGlobal && !state.point && !state.bbox) {
    showError(new ApiError('NO_LOCATION', state.lang === 'es'
      ? 'Elige primero un lugar en el mapa o búscalo por nombre.'
      : 'Pick a place on the map or search for it by name first.'));
    return;
  }

  const btn = $('#investigate-btn');
  btn.disabled = true;
  const label = btn.textContent;
  btn.textContent = t('panel.investigating');

  try {
    const params = {
      variable_id: variableId,
      start: `${$('#period-start').value}-01`,
      end: `${$('#period-end').value}-12`,
      lang: state.lang,
    };
    if (state.bbox) {
      params.bbox = state.bbox.join(',');
    } else if (state.point) {
      params.lat = Number(state.point.lat).toFixed(4);
      params.lon = Number(state.point.lon).toFixed(4);
      // The API writes this name into region.name, so the text says "Lima, Peru" and not coordinates.
      if (state.placeLabel && !isGlobal) params.place = state.placeLabel;
    }

    state.analysis = await apiGet('/api/analyze', params);
    renderAnalysis(state.analysis);
  } catch (err) {
    state.analysis = null;
    $('#result-root').hidden = true;
    $('#empty-state').hidden = true;
    showError(err);
  } finally {
    btn.disabled = false;
    btn.textContent = label;
  }
}

/* ---------------------------------------------------------------- render single */

function renderAnalysis(a) {
  state.analysis = a;
  $('#empty-state').hidden = true;
  $('#result-root').hidden = false;
  $('#compare-root').hidden = true;
  $('#trendmap-root').hidden = true;
  clearError();

  const code = a.significance?.verdict_code || 'INSUFFICIENT_DATA';
  const tier = VERDICT_TIER[code] || 1;

  const cleanVar = getCleanVariableName(a.variable?.id || $('#variable-select')?.value);
  const cleanLoc = getCleanRegionName(a);

  $('#verdict-title').textContent = t(`verdict.${code}`);
  const rawWhat = a.answers?.what?.[state.lang] || a.answers?.what?.es || a.answers?.what?.en || '';
  $('#verdict-plain').textContent = sanitizeText(rawWhat, a.variable?.id, cleanLoc);

  // evidence ladder — 5 states
  const ticks = document.querySelectorAll('#ladder li');
  ticks.forEach((li) => {
    const n = Number(li.dataset.tier);
    li.classList.toggle('is-active', n === tier);
    li.style.opacity = n <= tier ? '1' : '0.45';
  });
  const ladder = $('#ladder');
  ladder.classList.remove('is-fresh');
  void ladder.offsetWidth;
  ladder.classList.add('is-fresh');

  $('#verdict-state').textContent = t(`ladder.${tier}`);
  $('#verdict-step').textContent = `${tier}/5`;

  // provenance warning
  const kind = a.provenance?.kind;
  const warn = $('#provenance-warning');
  if (kind === 'fixture') {
    warn.hidden = false;
    warn.textContent = t('provenance.warning.fixture');
  } else if (kind === 'user_upload') {
    warn.hidden = false;
    warn.textContent = t('provenance.warning.upload');
  } else {
    warn.hidden = true;
  }

  renderChart();
  renderFindings(a, cleanVar, cleanLoc);
  renderMethod(a);
  // tests disagree breakdown (Ronda 3, Task 3)
  const disagreePanel = $('#tests-disagree-panel');
  const hasDisagree = (a.warnings && a.warnings.includes('TESTS_DISAGREE')) || (a.significance && a.significance.tests_agree === false);
  if (disagreePanel) {
    disagreePanel.hidden = !hasDisagree;
    if (hasDisagree) {
      const list = $('#test-agreement-list');
      if (list) {
        list.innerHTML = '';
        const mkMonthly = a.tests?.mann_kendall?.p_value_autocorr ?? a.tests?.mann_kendall?.p_value;
        const mkAnnual = a.tests?.mann_kendall_annual?.p_value;
        const tOls = a.tests?.t_test_ols?.p_value;
        const ci = a.trend?.sen_ci95_per_decade;
        const ciExclZero = Array.isArray(ci) && (ci[0] * ci[1] > 0);

        const items = [
          { name: state.lang === 'es' ? 'Mann–Kendall mensual' : 'Mann–Kendall (monthly)', sig: mkMonthly !== undefined && mkMonthly < 0.05, p: mkMonthly },
          { name: state.lang === 'es' ? 'Mann–Kendall anual' : 'Mann–Kendall (annual)', sig: mkAnnual !== undefined && mkAnnual < 0.05, p: mkAnnual },
          { name: state.lang === 'es' ? 'Prueba t de MCO ajustada' : 'OLS t-test (autocorr. adj.)', sig: tOls !== undefined && tOls < 0.05, p: tOls },
          { name: state.lang === 'es' ? 'Intervalo de confianza 95%' : '95% Confidence Interval', sig: ciExclZero, p: null },
        ];

        for (const it of items) {
          const li = el('li');
          const badge = el('span', { class: `badge-agree ${it.sig ? 'yes' : 'no'}` }, it.sig ? '✓ Sig' : '✗ Not sig');
          li.appendChild(badge);
          li.appendChild(document.createTextNode(` ${it.name}${it.p !== null && it.p !== undefined ? ` (p = ${fmtP(it.p)})` : ''}`));
          list.appendChild(li);
        }

        const moreY = a.detectability?.more_years_needed;
        if (moreY && Number(moreY) > 0) {
          const needLi = el('li');
          needLi.style.marginTop = '0.3rem';
          needLi.appendChild(el('strong', null, `⏱ ${t('years.more', { n: fmt(moreY, 1) })}`));
          list.appendChild(needLi);
        }
      }
    }
  }

  renderProvenance(a);
  loadExplanation(a, currentExplainLevel);

  // Update Period fields (From / To) to reflect actual analysis period (§2.14)
  if (a.period?.start) {
    const sYr = parseInt(String(a.period.start).slice(0, 4), 10);
    if (!isNaN(sYr) && $('#period-start')) $('#period-start').value = sYr;
  }
  if (a.period?.end) {
    const eYr = parseInt(String(a.period.end).slice(0, 4), 10);
    if (!isNaN(eYr) && $('#period-end')) $('#period-end').value = eYr;
  }

  $('#results').focus({ preventScroll: true });
}

function renderFindings(a, cleanVar, cleanLoc) {
  const rawWhere = a.answers?.where?.[state.lang] || a.answers?.where?.es || a.answers?.where?.en || '';
  $('#f-where').textContent = sanitizeText(rawWhere, a.variable?.id, cleanLoc) || cleanLoc;

  const slope = a.trend?.sen_slope_per_decade;
  const ci = a.trend?.sen_ci95_per_decade;

  // Harmonize exact last digit between large number and explanation text (§2.16):
  const rawHow = a.answers?.how_much?.[state.lang] || a.answers?.how_much?.es || a.answers?.how_much?.en || '';
  const m = /([+-]\d+\.\d+)/.exec(rawHow);
  let slopeStr = signed(slope, 3);
  if (m) {
    const rawVal = m[1];
    slopeStr = rawVal.startsWith('-') ? '−' + rawVal.slice(1) : rawVal;
  }
  $('#f-slope').textContent = slopeStr;

  const unitText = formatUnit(a.variable?.unit || '', state.lang);
  $('#f-unit').textContent = `${unitText} ${t('measure.perDecade')}`.trim();
  $('#f-ci').textContent = Array.isArray(ci)
    ? `${t('measure.ci')}: ${signed(ci[0], 3)} … ${signed(ci[1], 3)}`
    : '';

  const rawSig = a.answers?.significant?.[state.lang] || a.answers?.significant?.es || a.answers?.significant?.en || '';
  $('#f-significant').textContent = sanitizeText(rawSig, a.variable?.id, cleanLoc);

  // detectability bar
  const d = a.detectability || {};
  const avail = Number(d.years_available) || 0;
  const need = Number(d.years_needed) || 0;
  const span = Math.max(avail, need, 1);
  const availPct = Math.min(100, (avail / span) * 100);
  const needPct = Math.min(100, (need / span) * 100);
  $('#years-available').style.width = `${availPct}%`;
  $('#years-needed').style.left = `calc(${needPct}% - 1px)`;
  $('#years-avail-label').textContent = `${t('years.available')}: ${fmt(avail, 1)}`;
  $('#years-need-label').textContent = need > 0
    ? `${t('years.needed')}: ${fmt(need, 1)}`
    : t('years.needed');
  const more = Number(d.more_years_needed) || 0;
  $('#years-statement').textContent = more > 0
    ? t('years.more', { n: fmt(more, 1) })
    : t('years.enough');
  $('#years-scale').setAttribute('aria-label',
    `${t('years.available')}: ${fmt(avail, 1)}. ${t('years.needed')}: ${fmt(need, 1)}.`);
}

function renderMethod(a) {
  const tbody = $('#tests-table tbody');
  tbody.innerHTML = '';
  const mk = a.tests?.mann_kendall;
  const mka = a.tests?.mann_kendall_annual;
  const tt = a.tests?.t_test_ols;
  const rows = [];
  if (mk) rows.push(['Mann–Kendall (monthly)', `τ = ${fmt(mk.tau, 3)}${mk.z !== undefined ? `, z = ${fmt(mk.z, 2)}` : ''}`, fmtP(mk.p_value_autocorr ?? mk.p_value)]);
  if (mka) rows.push([`Mann–Kendall (annual, n=${mka.n})`, `τ = ${fmt(mka.tau, 3)}`, fmtP(mka.p_value)]);
  if (tt) rows.push([`t-test on OLS${tt.adjusted_for_autocorrelation ? ' (autocorr. adj.)' : ''}`, `t = ${fmt(tt.t, 2)}, df = ${fmt(tt.df, 0)}`, fmtP(tt.p_value)]);
  for (const r of rows) {
    const tr = el('tr');
    tr.appendChild(el('td', null, r[0]));
    tr.appendChild(el('td', { class: 'num' }, r[1]));
    tr.appendChild(el('td', { class: 'num' }, r[2]));
    tbody.appendChild(tr);
  }

  const ac = a.method?.autocorrelation;
  $('#method-autocorr').textContent = ac
    ? `${t('method.autocorr')}: ${fmt(ac.lag1, 2)} · ${t('method.neff')}: ${fmt(ac.n_eff, 0)}`
    : '';

  const warnList = $('#warn-list');
  warnList.innerHTML = '';
  for (const w of a.warnings || []) {
    warnList.appendChild(el('li', null, t(`warn.${w}`)));
  }

  $('#method-references').textContent = a.method?.references?.length
    ? `${t('method.references')}: ${a.method.references.join('; ')}`
    : '';
}

function renderProvenance(a) {
  const p = a.provenance || {};
  $('#prov-source').textContent = p.source || '—';
  $('#prov-underlying').textContent = p.underlying || '—';
  $('#prov-resolution').textContent = p.native_resolution || '—';
  $('#prov-retrieved').textContent = p.retrieved_at
    ? new Date(p.retrieved_at).toLocaleString(state.lang === 'es' ? 'es-PE' : 'en-US')
    : '—';
  const link = $('#prov-url');
  link.textContent = p.request_url || '—';
  if (p.request_url) link.href = p.request_url; else link.removeAttribute('href');
  $('#prov-citation').textContent = p.citation || '—';
}

/* ---------------------------------------------------------------- Tarea 1: Chart Engine with Corrected Sen & Confidence Fan */

function renderChart() {
  const a = state.analysis;
  if (!a || typeof Chart === 'undefined') return;
  const ctx = $('#trend-chart').getContext('2d');
  if (chart) chart.destroy();

  const s = a.series || {};
  const unit = formatUnit(a.variable?.unit || '', state.lang);
  const colors = {
    ink: '#16272b', teal: '#125e5a', tealWash: 'rgba(18, 94, 90, 0.15)',
    ochre: '#a2610f', grid: '#e3eae8', muted: '#566967',
  };
  const fonts = { family: 'Schibsted Grotesk, system-ui, sans-serif' };

  let labels, values, labelKey;
  let isAnnual = (state.view === 'annual');

  if (isAnnual) {
    const annual = s.annual || [];
    labels = annual.map((r) => String(r.year));
    values = annual.map((r) => r.value);
    labelKey = 'chart.annual';
  } else if (state.view === 'anomalies') {
    labels = s.dates || [];
    values = s.anomalies || [];
    labelKey = 'chart.anomalies';
  } else {
    labels = s.dates || [];
    values = s.raw || [];
    labelKey = 'chart.monthly';
  }

  // Calculate centered Sen trendline and confidence fan at the exact altitude of current data view
  const valid = [];
  for (let i = 0; i < values.length; i++) {
    if (values[i] !== null && Number.isFinite(values[i])) {
      valid.push({ v: values[i], i });
    }
  }

  let trendLine = null;
  let ciLow = null;
  let ciHigh = null;

  if (valid.length >= 2 && a.trend) {
    const meanY = valid.reduce((acc, e) => acc + e.v, 0) / valid.length;
    const meanIdx = valid.reduce((acc, e) => acc + e.i, 0) / valid.length;

    const slopeDecade = Number(a.trend.sen_slope_per_decade) || 0;
    const slopeYear = slopeDecade / 10.0;

    const ciDecade = Array.isArray(a.trend.sen_ci95_per_decade) && a.trend.sen_ci95_per_decade.length >= 2
      ? a.trend.sen_ci95_per_decade
      : [slopeDecade, slopeDecade];
    const ciLowSlopeYear = Number(ciDecade[0]) / 10.0;
    const ciHighSlopeYear = Number(ciDecade[1]) / 10.0;

    trendLine = new Array(values.length);
    ciLow = new Array(values.length);
    ciHigh = new Array(values.length);

    for (let i = 0; i < values.length; i++) {
      const dtYears = isAnnual ? (i - meanIdx) : ((i - meanIdx) / 12.0);
      const trendVal = meanY + slopeYear * dtYears;
      const fan1 = meanY + ciLowSlopeYear * dtYears;
      const fan2 = meanY + ciHighSlopeYear * dtYears;

      trendLine[i] = Number(trendVal.toFixed(4));
      ciLow[i] = Number(Math.min(fan1, fan2).toFixed(4));
      ciHigh[i] = Number(Math.max(fan1, fan2).toFixed(4));
    }
  }

  const datasets = [{
    label: t(labelKey),
    data: values,
    borderColor: colors.muted,
    backgroundColor: 'transparent',
    borderWidth: 1.2,
    pointRadius: 0,
    tension: 0,
    spanGaps: false,
  }];

  // Confidence fan as stacked fill
  if (ciHigh && ciLow) {
    datasets.push({
      label: 'CI 95% High',
      data: ciHigh,
      borderWidth: 0,
      pointRadius: 0,
      backgroundColor: colors.tealWash,
      fill: '+1',
      spanGaps: false,
    });
    datasets.push({
      label: 'CI 95% Low',
      data: ciLow,
      borderWidth: 0,
      pointRadius: 0,
      backgroundColor: colors.tealWash,
      fill: false,
      spanGaps: false,
    });
  }

  if (trendLine) {
    datasets.push({
      label: 'Theil–Sen Trend',
      data: trendLine,
      borderColor: colors.teal,
      borderWidth: 2.2,
      borderDash: [6, 4],
      pointRadius: 0,
      fill: false,
      spanGaps: false,
    });
  }

  const verticals = [];
  if (a.homogeneous_since && labels.length) {
    const target = a.homogeneous_since;
    const idx = labels.findIndex((l) => String(l).startsWith(target.slice(0, 7)) || String(l).slice(0, 4) >= target.slice(0, 4));
    if (idx >= 0) verticals.push(idx);
  }

  chart = new Chart(ctx, {
    type: 'line',
    data: { labels, datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      animation: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? false : { duration: 250 },
      plugins: {
        legend: { display: false },
        tooltip: {
          filter: (item) => item.datasetIndex === 0 || item.datasetIndex === datasets.length - 1,
          callbacks: {
            label: (c) => `${c.dataset.label}: ${fmt(c.raw, 2)} ${unit}`.trim(),
          },
        },
      },
      scales: {
        x: {
          grid: { color: colors.grid, drawTicks: false },
          ticks: { maxTicksLimit: 10, color: colors.muted, font: { ...fonts, size: 11 } },
        },
        y: {
          grid: { color: colors.grid, drawTicks: false },
          ticks: { color: colors.muted, font: { ...fonts, size: 11 } },
          title: { display: true, text: `${t('chart.axis.value')} (${unit})`, color: colors.muted, font: { ...fonts, size: 12 } },
        },
      },
    },
    plugins: verticals.length ? [{
      id: 'spliceLine',
      afterDraw(c) {
        const { ctx: c2, chartArea, scales } = c;
        c2.save();
        c2.strokeStyle = colors.ochre;
        c2.setLineDash([3, 3]);
        for (const i of verticals) {
          const x = scales.x.getPixelForValue(i);
          if (x >= chartArea.left && x <= chartArea.right) {
            c2.beginPath(); c2.moveTo(x, chartArea.top); c2.lineTo(x, chartArea.bottom); c2.stroke();
          }
        }
        c2.restore();
      },
    }] : [],
  });
}

/* ---------------------------------------------------------------- U3: TrendMap */

function getDivergingColor(slope, maxAbs) {
  if (slope === null || slope === undefined || Number.isNaN(slope)) return '#c8d3d1';
  const clamped = Math.max(-maxAbs, Math.min(maxAbs, slope));
  const ratio = clamped / maxAbs; // -1 to +1
  if (ratio > 0) {
    return `rgba(162, 97, 15, ${0.15 + 0.85 * ratio})`;
  } else {
    return `rgba(18, 94, 90, ${0.15 + 0.85 * Math.abs(ratio)})`;
  }
}


async function loadGlobalAtlas() {
  clearError();
  const select = $('#variable-select');
  const varId = (select && select.value) || 'T2M';
  const targetAtlas = (varId === 'GISTEMP_TANOM') ? 'GISTEMP_TANOM' : 'T2M';

  const btn = $('#btn-load-atlas');
  if (btn) {
    btn.disabled = true;
    btn.textContent = t('atlas.loading');
  }

  try {
    const data = await apiGet(`/api/atlas/${targetAtlas}`);
    setMode('trendmap');
    renderTrendMap(data);
    if (map) map.setView([10, 0], 2);
  } catch (err) {
    showError(err);
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.textContent = t('atlas.load.btn');
    }
  }
}

async function runTrendMap() {
  clearError();
  if (!state.bbox) {
    showError(new ApiError('NO_BBOX', state.lang === 'es'
      ? 'Selecciona una caja en el mapa con Mayús + arrastrar para generar el mapa de tendencias.'
      : 'Select a box on the map holding Shift and dragging to generate the trend map.'));
    return;
  }
  const variableId = $('#variable-select').value;
  const btn = $('#btn-calc-trendmap');
  btn.disabled = true;

  try {
    const data = await apiGet('/api/trendmap', {
      variable_id: variableId,
      bbox: state.bbox.join(','),
    });
    renderTrendMap(data);
  } catch (err) {
    showError(err);
  } finally {
    btn.disabled = false;
  }
}

function renderTrendMap(tm) {
  state.trendmap = tm;
  $('#empty-state').hidden = true;
  $('#result-root').hidden = true;
  $('#compare-root').hidden = true;
  $('#trendmap-root').hidden = false;

  if (trendmapLayer) trendmapLayer.clearLayers();

  const lats = tm.lats || [];
  const lons = tm.lons || [];
  const slopes = tm.slope_per_decade || [];
  const sigFdr = tm.significant_fdr || [];

  let maxAbs = 0.05;
  for (const row of slopes) {
    for (const v of row) {
      if (v !== null && Number.isFinite(v)) maxAbs = Math.max(maxAbs, Math.abs(v));
    }
  }

  $('#legend-min').textContent = signed(-maxAbs, 2);
  $('#legend-max').textContent = signed(maxAbs, 2);

  const dLat = lats.length > 1 ? Math.abs(lats[1] - lats[0]) : 0.5;
  const dLon = lons.length > 1 ? Math.abs(lons[1] - lons[0]) : 0.625;

  let totalCells = 0, sigCount = 0;

  for (let r = 0; r < lats.length; r++) {
    const lat = lats[r];
    for (let c = 0; c < lons.length; c++) {
      const lon = lons[c];
      const slope = slopes[r] ? slopes[r][c] : null;
      const isSig = sigFdr[r] ? sigFdr[r][c] : false;
      totalCells++;
      if (isSig) sigCount++;

      const s = lat - dLat / 2;
      const n = lat + dLat / 2;
      const w = lon - dLon / 2;
      const e = lon + dLon / 2;

      const fill = getDivergingColor(slope, maxAbs);

      const cellRect = L.rectangle([[s, w], [n, e]], {
        color: '#33484c',
        weight: 1,
        fillColor: fill,
        fillOpacity: 0.85,
      });

      cellRect.bindTooltip(`
        <strong>${lat.toFixed(2)}°, ${lon.toFixed(2)}°</strong><br>
        ${t('verdict.howmuch')}: ${signed(slope, 3)} ${tm.unit_per_decade || ''}<br>
        ${isSig ? `✓ <strong>${t('trendmap.legend.sig')}</strong>` : ''}
      `);

      cellRect.on('click', () => {
        setPoint(lat, lon);
        setMode('single');
        investigate();
      });

      trendmapLayer.addLayer(cellRect);

      if (isSig) {
        const dot = L.circleMarker([lat, lon], {
          radius: 3,
          color: '#16272b',
          weight: 1.5,
          fillColor: '#16272b',
          fillOpacity: 1,
        });
        trendmapLayer.addLayer(dot);
      }
    }
  }

  const sharePct = tm.n_cells ? ((tm.n_significant / tm.n_cells) * 100).toFixed(0) : ((sigCount / totalCells) * 100).toFixed(0);
  const requestedVarId = $('#variable-select')?.value || 'T2M';
  const targetVarId = (tm.variable_id && tm.variable_id !== 'VAR') ? tm.variable_id : requestedVarId;
  const cleanVar = getCleanVariableName(targetVarId);
  $('#trendmap-heading').textContent = `${cleanVar} — ${t('trendmap.legend.share', { pct: sharePct })}`;
  $('#trendmap-summary').textContent = `${t('trendmap.cells')}: ${tm.n_cells || totalCells} | ${t('trendmap.legend.sig')}: ${tm.n_significant || sigCount} (FDR q=${tm.fdr_q || 0.10})`;
}

/* ---------------------------------------------------------------- U3: Compare */

async function runCompare() {
  clearError();
  if (!state.point || !state.pointCompareB) {
    showError(new ApiError('NO_COMPARE_LOCATIONS', state.lang === 'es'
      ? 'Selecciona dos lugares en el mapa (A y B) para compararlos.'
      : 'Select two places on the map (A and B) to compare them.'));
    return;
  }
  const variableId = $('#variable-select').value;
  const btn = $('#investigate-btn');
  btn.disabled = true;

  try {
    const compData = await apiGet('/api/compare', {
      variable_id: variableId,
      a: `${state.point.lat.toFixed(4)},${state.point.lon.toFixed(4)}`,
      b: `${state.pointCompareB.lat.toFixed(4)},${state.pointCompareB.lon.toFixed(4)}`,
    });
    renderCompare(compData);
  } catch (err) {
    showError(err);
  } finally {
    btn.disabled = false;
  }
}

function renderCompare(data) {
  state.compare = data;
  $('#empty-state').hidden = true;
  $('#result-root').hidden = true;
  $('#trendmap-root').hidden = true;
  $('#compare-root').hidden = false;

  const a = data.a || {};
  const b = data.b || {};
  const cmp = data.comparison || {};

  const nameA = a.region?.name || state.locationName || 'A';
  const nameB = b.region?.name || state.locationNameB || 'B';

  $('#compare-title').textContent = `${nameA} vs. ${nameB}`;

  const statement = cmp.statement?.[state.lang] || cmp.statement?.en || (cmp.opposite ? t('compare.opposite.yes') : t('compare.opposite.no'));
  $('#compare-statement').textContent = statement;

  const badge = $('#compare-badge');
  badge.className = `compare-badge ${cmp.opposite ? 'opposite' : 'similar'}`;
  badge.textContent = cmp.opposite ? t('compare.opposite.yes') : t('compare.opposite.no');

  $('#chart-heading-a').textContent = nameA;
  $('#chart-heading-b').textContent = nameB;

  renderCompareCharts(a, b);
}

function renderCompareCharts(a, b) {
  const ctxA = $('#chart-compare-a').getContext('2d');
  const ctxB = $('#chart-compare-b').getContext('2d');

  if (chartCompareA) chartCompareA.destroy();
  if (chartCompareB) chartCompareB.destroy();

  const sA = a.series || {};
  const sB = b.series || {};

  const allVals = [...(sA.raw || []), ...(sB.raw || [])].filter(v => v !== null && Number.isFinite(v));
  const sharedMin = allVals.length ? Math.floor(Math.min(...allVals) - 1) : 0;
  const sharedMax = allVals.length ? Math.ceil(Math.max(...allVals) + 1) : 30;

  const unit = a.variable?.unit || '';

  const chartOpts = {
    responsive: true,
    maintainAspectRatio: false,
    scales: {
      y: { min: sharedMin, max: sharedMax, title: { display: true, text: unit } },
      x: { ticks: { maxTicksLimit: 8 } },
    },
    plugins: { legend: { display: false } },
  };

  function calcCenteredTrend(series, analysis) {
    const raw = series.raw || [];
    const valid = raw.filter(v => v !== null && Number.isFinite(v));
    if (valid.length < 2) return [];
    const meanY = valid.reduce((a, b) => a + b, 0) / valid.length;
    const slopeYear = (Number(analysis.trend?.sen_slope_per_decade) || 0) / 10.0;
    const mid = raw.length / 2;
    return raw.map((_, i) => Number((meanY + slopeYear * ((i - mid) / 12.0)).toFixed(4)));
  }

  const trendA = calcCenteredTrend(sA, a);
  const trendB = calcCenteredTrend(sB, b);

  chartCompareA = new Chart(ctxA, {
    type: 'line',
    data: {
      labels: sA.dates || [],
      datasets: [
        { data: sA.raw || [], borderColor: '#125e5a', borderWidth: 1.2, pointRadius: 0 },
        { data: trendA.length ? trendA : (sA.trend_line || []), borderColor: '#16272b', borderWidth: 2, borderDash: [4, 4], pointRadius: 0 }
      ],
    },
    options: chartOpts,
  });

  chartCompareB = new Chart(ctxB, {
    type: 'line',
    data: {
      labels: sB.dates || [],
      datasets: [
        { data: sB.raw || [], borderColor: '#a2610f', borderWidth: 1.2, pointRadius: 0 },
        { data: trendB.length ? trendB : (sB.trend_line || []), borderColor: '#16272b', borderWidth: 2, borderDash: [4, 4], pointRadius: 0 }
      ],
    },
    options: chartOpts,
  });
}

/* ---------------------------------------------------------------- U4: AI Detective */

let currentPlan = null;
let currentExplainLevel = 'school';
let currentChatContext = {};

function formatMarkdownMini(text) {
  if (!text) return '';
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/\n\n/g, '<br><br>')
    .replace(/\n• /g, '<br>• ')
    .replace(/\n/g, '<br>');
}

function renderChatReply(data) {
  const card = $('#detective-plan-card');
  card.hidden = false;

  const badge = $('#plan-meta-badge');
  if (badge) {
    badge.textContent = 'Huiracocha IA (LoRA & Chat)';
    badge.className = 'plan-badge plan-badge-lora';
  }

  const intentText = $('#plan-intent-text');
  if (intentText) {
    intentText.innerHTML = formatMarkdownMini(data.reply);
  }

  // Sources
  const sourcesEl = $('#plan-sources-list');
  if (sourcesEl) {
    if (data.sources && data.sources.length > 0) {
      sourcesEl.hidden = false;
      const title = state.lang === 'es' ? 'Fuentes oficiales consultadas:' : 'Official sources consulted:';
      const items = data.sources.map(s => `<li><a href="${s.url}" target="_blank" rel="noopener">${s.title} (${s.publisher || 'Fuente'})</a></li>`).join('');
      sourcesEl.innerHTML = `<strong>${title}</strong><ul style="margin:0.25rem 0 0 1.1rem;padding:0;">${items}</ul>`;
    } else {
      sourcesEl.hidden = true;
      sourcesEl.innerHTML = '';
    }
  }

  // Suggestions
  const suggsEl = $('#plan-suggestions');
  if (suggsEl) {
    if (data.suggestions && data.suggestions.length > 0) {
      suggsEl.hidden = false;
      const title = state.lang === 'es' ? 'Sugerencias para continuar:' : 'Suggestions to continue:';
      const btns = data.suggestions.map(sg => `<button type="button" class="plan-suggestion-chip">${sg}</button>`).join('');
      suggsEl.innerHTML = `<span style="font-size:0.75rem;font-weight:600;color:var(--ink-2);">${title}</span><div style="display:flex;flex-direction:column;gap:0.3rem;margin-top:0.25rem;">${btns}</div>`;
      suggsEl.querySelectorAll('.plan-suggestion-chip').forEach(btn => {
        btn.addEventListener('click', () => {
          $('#detective-input').value = btn.textContent;
          askDetective(btn.textContent);
        });
      });
    } else {
      suggsEl.hidden = true;
      suggsEl.innerHTML = '';
    }
  }

  // Confirm plan button
  const confirmBtn = $('#plan-confirm-btn');
  if (confirmBtn) {
    if (data.plan && (data.action === 'analyze' || (data.plan.variable_ids && data.plan.variable_ids.length > 0))) {
      currentPlan = data.plan;
      confirmBtn.hidden = false;
      confirmBtn.disabled = false;
      confirmBtn.textContent = state.lang === 'es' ? 'Investigar en el mapa con NASA' : 'Investigate on map with NASA';
    } else {
      confirmBtn.hidden = true;
    }
  }
}

async function askDetective(question) {
  if (!question || question.trim().length < 2) return;
  const btn = $('#detective-ask-btn');
  btn.disabled = true;
  btn.textContent = '…';

  try {
    let chatData = null;
    try {
      const res = await fetch(`${API_BASE}/api/ai/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
        body: JSON.stringify({ message: question.trim(), lang: state.lang, context: currentChatContext })
      });
      if (res.ok) {
        chatData = await res.json();
      }
    } catch (_) {}

    if (chatData && chatData.reply) {
      if (chatData.context) currentChatContext = Object.assign(currentChatContext, chatData.context);
      renderChatReply(chatData);
    } else {
      const qUrl = `${API_BASE}/api/ai/plan?question=${encodeURIComponent(question)}&lang=${state.lang}`;
      const res = await fetch(qUrl, { method: 'POST', headers: { Accept: 'application/json' } });
      if (!res.ok) throw new Error('Planner error');
      const planData = await res.json();
      renderPlan(planData);
    }
  } catch (err) {
    showError(new ApiError('AI_UNAVAILABLE', state.lang === 'es'
      ? 'Huiracocha IA no está disponible en este momento. Selecciona lugar y variable manualmente.'
      : 'Huiracocha AI is not available right now. Please select location and variable manually.'));
  } finally {
    btn.disabled = false;
    btn.textContent = state.lang === 'es' ? 'Preguntar' : 'Ask';
  }
}

function renderPlan(plan) {
  currentPlan = plan;
  const card = $('#detective-plan-card');
  card.hidden = false;

  const confirmBtn = $('#plan-confirm-btn');

  // Handle greetings or no-match queries friendly
  if (plan.intent === 'no_match' || (!plan.place && (!plan.variable_ids || plan.variable_ids.length === 0))) {
    const rawQ = ($('#detective-input')?.value || '').toLowerCase().trim();
    const isGreeting = /^(hola|ola|buenos|buenas|hello|hi|hey|saludos|que tal|quÃ© tal|qué tal)/i.test(rawQ);
    if (isGreeting) {
      $('#plan-intent-text').textContent = state.lang === 'es'
        ? '¡Hola! Soy Huiracocha IA. Puedo analizar tendencias climáticas con datos de la NASA. Prueba preguntando: "¿Llueve menos en Piura?" o "¿Sube la temperatura en Lima?".'
        : 'Hello! I am Huiracocha AI. I can investigate climate trends with NASA Earth science data. Try asking: "Is it raining less in Piura?" or "Is temperature rising in Lima?".';
    } else {
      $('#plan-intent-text').textContent = state.lang === 'es'
        ? 'No identifiqué una variable climática o lugar específico. Pregúntame sobre temperatura, lluvia o vegetación de una ciudad (ej. "¿Llueve menos en Piura?").'
        : 'Could not match a climate variable or location. Ask me about temperature, rainfall or vegetation in a place (e.g. "Is it raining less in Piura?").';
    }
    const badge = $('#plan-meta-badge');
    if (badge) {
      badge.textContent = state.lang === 'es' ? 'Huiracocha IA' : 'Huiracocha AI';
      badge.className = 'plan-badge plan-badge-rules';
    }
    const noteEl = $('#plan-note-text');
    if (noteEl) noteEl.hidden = true;
    if (confirmBtn) confirmBtn.hidden = true;
    return;
  }

  if (confirmBtn) confirmBtn.hidden = false;

  const varId = plan.variable_ids && plan.variable_ids[0] ? plan.variable_ids[0] : 'T2M';
  const cleanVar = getCleanVariableName(varId);
  const placeName = plan.place || (state.lang === 'es' ? 'el lugar seleccionado' : 'the selected place');

  $('#plan-intent-text').textContent = t('detective.plan.intent', { var: cleanVar, place: placeName });

  // Planner attribution badge (LoRA fine-tuned model vs rules)
  const isLora = plan.planner === 'lora' || plan.mode === 'lora';
  const badge = $('#plan-meta-badge');
  if (badge) {
    badge.textContent = isLora ? t('detective.plan.by_lora') : t('detective.plan.by_rules');
    badge.className = `plan-badge ${isLora ? 'plan-badge-lora' : 'plan-badge-rules'}`;
  }

  // Fallback note if any
  const noteEl = $('#plan-note-text');
  if (noteEl) {
    if (plan.note) {
      noteEl.textContent = plan.note;
      noteEl.hidden = false;
    } else {
      noteEl.textContent = '';
      noteEl.hidden = true;
    }
  }

  // Rule 19: If plan picked a planned variable, it cannot be run directly
  if (confirmBtn) {
    if (isPlannedVariable(varId)) {
      confirmBtn.disabled = true;
      confirmBtn.textContent = t('detective.plan.not_loaded');
      confirmBtn.setAttribute('title', 'This variable requires uploading its Giovanni CSV');
    } else {
      confirmBtn.disabled = false;
      confirmBtn.textContent = t('detective.plan.run');
      confirmBtn.removeAttribute('title');
    }
  }
}

async function confirmPlan() {
  if (!currentPlan) return;
  $('#detective-plan-card').hidden = true;

  const varId = currentPlan.variable_ids && currentPlan.variable_ids[0] ? currentPlan.variable_ids[0] : 'T2M';
  const select = $('#variable-select');
  if (select) {
    select.value = varId;
    onVariableChange();
  }

  if (currentPlan.place) {
    await searchPlace(currentPlan.place, false);
  }

  investigate();
}

async function scoutLocation() {
  if (!state.point) return;
  const btn = $('#btn-scout');
  btn.disabled = true;

  try {
    const qUrl = `${API_BASE}/api/ai/scout?lat=${state.point.lat}&lon=${state.point.lon}&lang=${state.lang}`;
    const res = await fetch(qUrl, { method: 'POST', headers: { Accept: 'application/json' } });
    if (!res.ok) throw new Error('Scout error');
    const scoutData = await res.json();
    renderScout(scoutData);
  } catch (err) {
    showError(new ApiError('AI_SCOUT_ERROR', state.lang === 'es'
      ? 'No se pudieron recuperar recomendaciones para esta zona.'
      : 'Could not retrieve recommendations for this area.'));
  } finally {
    btn.disabled = false;
  }
}

function renderScout(data) {
  const drawer = $('#scout-drawer');
  const list = $('#scout-list');
  list.innerHTML = '';
  drawer.hidden = false;

  const candidates = data.candidates || [];
  for (const c of candidates) {
    const cleanVar = getCleanVariableName(c.variable_id);
    const item = el('div', { class: 'scout-item' });
    item.appendChild(el('h4', null, `${c.variable_id} — ${cleanVar}`));
    item.appendChild(el('p', null, c.why?.[state.lang] || c.why?.es || c.why?.en || ''));

    const srcDiv = el('div', { class: 'scout-sources' });
    for (const src of c.sources || []) {
      const a = el('a', { href: src.url, target: '_blank', rel: 'noopener noreferrer' }, src.title || 'NASA EO');
      srcDiv.appendChild(a);
    }
    item.appendChild(srcDiv);

    const pickBtn = el('button', { type: 'button', class: 'btn btn-ghost btn-small' },
      state.lang === 'es' ? 'Investigar esta variable' : 'Investigate this variable');
    pickBtn.addEventListener('click', () => {
      $('#variable-select').value = c.variable_id;
      onVariableChange();
      drawer.hidden = true;
      investigate();
    });
    item.appendChild(pickBtn);

    list.appendChild(item);
  }
}

async function loadExplanation(analysis, level = 'school') {
  currentExplainLevel = level;
  const isSchool = (level === 'school');
  const isUni = (level === 'uni' || level === 'university');
  $('#lvl-school').classList.toggle('is-active', isSchool);
  $('#lvl-uni').classList.toggle('is-active', isUni);
  $('#lvl-school').setAttribute('aria-pressed', String(isSchool));
  $('#lvl-uni').setAttribute('aria-pressed', String(isUni));

  const textEl = $('#explain-text');
  const sourcesBox = $('#explain-sources-box');
  const listEl = $('#explain-citations-list');

  textEl.textContent = t('detective.explain.loading');
  sourcesBox.hidden = true;

  try {
    const exp = await apiPost('/api/ai/explain', { analysis, level, lang: state.lang });
    const cleanLoc = getCleanRegionName(analysis);
    textEl.textContent = sanitizeText(exp.text || '', analysis.variable?.id, cleanLoc);

    // Update label strictly based on mode (Ronda 3, Task 1)
    const badgeEl = document.querySelector('.ai-badge');
    if (badgeEl) {
      const isFull = (exp.mode === 'full');
      badgeEl.textContent = isFull
        ? t('detective.explain.badge.full')
        : t('detective.explain.badge.extractive');
    }

    if (exp.citations && exp.citations.length) {
      sourcesBox.hidden = false;
      listEl.innerHTML = '';
      for (const cit of exp.citations) {
        const citNum = (cit.n !== undefined && cit.n !== null) ? cit.n : (cit.id || 1);
        const li = el('li');
        li.appendChild(el('strong', null, `[${citNum}] `));

        if (cit.url) {
          const a = el('a', { href: cit.url, target: '_blank', rel: 'noopener noreferrer' }, cit.title || 'Source');
          li.appendChild(a);
        } else {
          li.appendChild(document.createTextNode(cit.title || 'Source'));
        }

        if (cit.publisher) {
          li.appendChild(el('span', { class: 'citation-publisher' }, ` — ${cit.publisher}`));
        }
        listEl.appendChild(li);
      }
    }
  } catch (err) {
    textEl.textContent = state.lang === 'es'
      ? 'La explicación con IA está en modo extractivo. Revisa las 4 tarjetas del veredicto y las pruebas estadísticas comprobadas arriba.'
      : 'AI explanation is in extractive mode. Please review the 4 verdict cards and statistical tests above.';
  }
}

/* ---------------------------------------------------------------- U5: Guided Demo with Real Data */

let demoIndex = 0;
let demoTimer = null;
let demoPaused = false;
const DEMO_DURATION = 12000;

function startDemo() {
  demoIndex = 0;
  demoPaused = false;
  $('#demo-banner').hidden = false;
  $('#btn-demo-pause').textContent = t('demo.btn.pause');
  loadDemoCase(demoIndex);
}

function stopDemo() {
  if (demoTimer) clearTimeout(demoTimer);
  demoTimer = null;
  $('#demo-banner').hidden = true;
  const fill = $('#demo-progress-fill');
  if (fill) fill.style.width = '0%';
}

function pauseResumeDemo() {
  if (demoPaused) {
    demoPaused = false;
    $('#btn-demo-pause').textContent = t('demo.btn.pause');
    scheduleNextDemo(DEMO_DURATION / 2);
  } else {
    demoPaused = true;
    if (demoTimer) clearTimeout(demoTimer);
    demoTimer = null;
    $('#btn-demo-pause').textContent = t('demo.btn.resume');
    const fill = $('#demo-progress-fill');
    if (fill) fill.style.width = fill.offsetWidth + 'px';
  }
}

function nextDemoCase() {
  if (demoTimer) clearTimeout(demoTimer);
  demoIndex = (demoIndex + 1) % (state.cases.length || 1);
  loadDemoCase(demoIndex);
}

async function loadDemoCase(idx) {
  if (!state.cases.length) {
    await loadCases();
  }
  if (!state.cases.length) return;

  const c = state.cases[idx % state.cases.length];
  $('#demo-counter').textContent = t('demo.step', { curr: (idx % state.cases.length) + 1, total: state.cases.length });
  $('#demo-case-title').textContent = caseTitle(c);
  $('#demo-case-text').textContent = caseFinding(c) || (state.lang === 'es' ? 'Caso emblemático con datos satelitales reales.' : 'Real satellite observation case.');

  const fill = $('#demo-progress-fill');
  if (fill) {
    fill.style.transition = 'none';
    fill.style.width = '0%';
    setTimeout(() => {
      fill.style.transition = `width ${DEMO_DURATION}ms linear`;
      fill.style.width = '100%';
    }, 50);
  }

  await openCase(c);

  if (!demoPaused) {
    scheduleNextDemo(DEMO_DURATION);
  }
}

function scheduleNextDemo(delay) {
  if (demoTimer) clearTimeout(demoTimer);
  demoTimer = setTimeout(() => {
    if (!demoPaused) {
      demoIndex = (demoIndex + 1) % (state.cases.length || 1);
      loadDemoCase(demoIndex);
    }
  }, delay);
}

/* ---------------------------------------------------------------- U6: Report */

function printReport() {
  if (!state.analysis) {
    showError(new ApiError('NO_REPORT_DATA', state.lang === 'es'
      ? 'Primero realiza una investigación para poder generar y descargar el informe.'
      : 'Please run an investigation first before downloading the report.'));
    return;
  }
  window.print();
}

/* ---------------------------------------------------------------- modes */

function setMode(mode) {
  state.mode = mode;
  $('#mode-single').classList.toggle('is-active', mode === 'single');
  $('#mode-trendmap').classList.toggle('is-active', mode === 'trendmap');
  $('#mode-compare').classList.toggle('is-active', mode === 'compare');

  $('#field-compare-b').hidden = mode !== 'compare';
  $('#trendmap-bar').hidden = mode !== 'trendmap';

  if (mode !== 'trendmap' && trendmapLayer) {
    trendmapLayer.clearLayers();
  }

  const btn = $('#investigate-btn');
  if (mode === 'compare') {
    btn.textContent = t('compare.btn');
  } else if (mode === 'trendmap') {
    btn.textContent = t('trendmap.btn');
  } else {
    btn.textContent = t('panel.investigate');
  }
}

/* ---------------------------------------------------------------- glossary */

function initGlossary() {
  document.querySelectorAll('.term').forEach(btn => {
    btn.addEventListener('click', (ev) => {
      ev.stopPropagation();
      const pop = $('#glossary-pop');
      if (!pop) return;
      const key = btn.dataset.termKey;
      pop.hidden = false;
      pop.textContent = t(key);
      const r = btn.getBoundingClientRect();
      pop.style.left = `${Math.min(r.left + window.scrollX, window.innerWidth - 320)}px`;
      pop.style.top = `${r.bottom + window.scrollY + 6}px`;
    });
  });
  document.addEventListener('click', () => { const pop = $('#glossary-pop'); if (pop) pop.hidden = true; });
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape') { const pop = $('#glossary-pop'); if (pop) pop.hidden = true; } });
}

/* ---------------------------------------------------------------- lang */

function setLang(lang) {
  state.lang = lang;
  window.__etdLang = lang;
  $('#lang-en').setAttribute('aria-pressed', String(lang === 'en'));
  $('#lang-es').setAttribute('aria-pressed', String(lang === 'es'));
  applyTranslations(document);
  renderCatalog();
  loadCases();
  if (state.analysis && state.mode === 'single') renderAnalysis(state.analysis);
  else if (state.trendmap && state.mode === 'trendmap') renderTrendMap(state.trendmap);
  else if (state.compare && state.mode === 'compare') renderCompare(state.compare);
  try { localStorage.setItem('etd.lang', lang); } catch (_) { /* private mode */ }
}

/* ---------------------------------------------------------------- CSV Upload */

async function handleCsvUpload(file) {
  if (!file) return;
  const formData = new FormData();
  formData.append('file', file);

  const btn = $('#btn-upload-csv');
  if (btn) btn.disabled = true;

  try {
    const res = await fetch(`${API_BASE}/api/analyze/upload`, {
      method: 'POST',
      headers: { Accept: 'application/json' },
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Error uploading Giovanni CSV');
    }
    const data = await res.json();
    setMode('single');
    renderAnalysis(data);
  } catch (err) {
    showError(new ApiError('UPLOAD_ERROR', err.message || String(err)));
  } finally {
    if (btn) btn.disabled = false;
  }
}

/* ---------------------------------------------------------------- boot */

function boot() {
  try {
    const saved = localStorage.getItem('etd.lang');
    if (saved === 'es' || saved === 'en') state.lang = saved;
  } catch (_) { /* private mode */ }
  window.__etdLang = state.lang;
  applyTranslations(document);
  $('#lang-en').setAttribute('aria-pressed', String(state.lang === 'en'));
  $('#lang-es').setAttribute('aria-pressed', String(state.lang === 'es'));

  $('#lang-en').addEventListener('click', () => setLang('en'));
  $('#lang-es').addEventListener('click', () => setLang('es'));

  $('#mode-single').addEventListener('click', () => setMode('single'));
  $('#mode-trendmap').addEventListener('click', () => setMode('trendmap'));
  $('#mode-compare').addEventListener('click', () => setMode('compare'));

  initMap();
  initGlossary();

  $('#investigate-form').addEventListener('submit', (ev) => { ev.preventDefault(); investigate(); });
  $('#variable-select').addEventListener('change', onVariableChange);
  $('#place-search-btn').addEventListener('click', () => searchPlace($('#place-search').value, false));
  $('#place-search-btn-b').addEventListener('click', () => searchPlace($('#place-search-b').value, true));
  $('#btn-calc-trendmap').addEventListener('click', runTrendMap);
  $('#btn-load-atlas')?.addEventListener('click', loadGlobalAtlas);
  
  // Quick question chips for Huiracocha IA
  document.querySelectorAll('.chip-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const q = btn.dataset.q || btn.textContent;
      const inp = $('#detective-input');
      if (inp) inp.value = q;
      askDetective(q);
    });
  });

  $('#detective-ask-btn')?.addEventListener('click', () => askDetective($('#detective-input').value));
  $('#detective-input')?.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      askDetective($('#detective-input').value);
    }
  });
  $('#plan-confirm-btn')?.addEventListener('click', confirmPlan);
  $('#btn-scout')?.addEventListener('click', scoutLocation);
  $('#btn-scout-close')?.addEventListener('click', () => { $('#scout-drawer').hidden = true; });
  $('#lvl-school')?.addEventListener('click', () => { if (state.analysis) loadExplanation(state.analysis, 'school'); });
  $('#lvl-uni')?.addEventListener('click', () => { if (state.analysis) loadExplanation(state.analysis, 'university'); });
  $('#btn-start-demo')?.addEventListener('click', startDemo);
  $('#btn-demo-pause')?.addEventListener('click', pauseResumeDemo);
  $('#btn-demo-next')?.addEventListener('click', nextDemoCase);
  $('#btn-demo-stop')?.addEventListener('click', stopDemo);
  $('#btn-print-report')?.addEventListener('click', printReport);

  const csvInput = $('#csv-file-input');
  if (csvInput) {
    csvInput.addEventListener('change', (ev) => {
      const file = ev.target.files?.[0];
      if (file) handleCsvUpload(file);
    });
  }
  $('#btn-upload-csv')?.addEventListener('click', () => csvInput?.click());

  for (const [id, view] of [['view-monthly', 'monthly'], ['view-anomalies', 'anomalies'], ['view-annual', 'annual']]) {
    $(`#${id}`).addEventListener('click', () => {
      state.view = view;
      for (const other of ['view-monthly', 'view-anomalies', 'view-annual']) {
        $(`#${other}`).setAttribute('aria-pressed', String(other === id));
      }
      renderChart();
    });
  }

  $('#error-retry').addEventListener('click', () => {
    clearError();
    if (state.analysis) renderAnalysis(state.analysis);
    else boot();
  });

  apiGet('/api/health')
    .then((h) => { state.health = h; })
    .catch((err) => showError(err))
    .finally(() => {
      apiGet(`/api/catalog/variables?lang=${state.lang}`)
        .then((d) => {
          state.catalog = (d && d.variables) || [];
          if (d && Array.isArray(d.planned)) state.plannedCatalog = d.planned;
          renderCatalog();
        })
        .catch((err) => showError(err));
      loadCases();
    });
}

document.addEventListener('DOMContentLoaded', boot);

window.__etd = { state, investigate, renderAnalysis, renderTrendMap, renderCompare, setLang, setMode, setPoint, setPointA, setPointB, setBBox, onVariableChange, fmt, fmtP, signed, t, openCase };

})();
