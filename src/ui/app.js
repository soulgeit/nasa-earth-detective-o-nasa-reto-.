(function() {
'use strict';
// SI-assisted: claude-omni-1 (Claude Sonnet 5.5)
// EarthTrend Detective — interface logic.
// HARD RULE: this file never computes or invents a scientific number.
// Every figure shown comes from /api/analyze, /api/trendmap, /api/compare
// (or, in explicit dev mode, from real fixtures stored under tests/fixtures/real/).

const { t, applyTranslations } = window.__etdI18n;

const API_BASE = window.ETD_API_BASE || '';
const DEV_FIXTURE = new URLSearchParams(location.search).get('dev') === 'fixture';

const state = {
  mode: 'single', // 'single' | 'trendmap' | 'compare'
  health: null,
  catalog: [],
  cases: [],
  analysis: null,
  trendmap: null,
  compare: null,
  view: 'monthly',
  point: null,
  pointCompareB: null,
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
  if (n === null || n === undefined) return '—';
  return (n > 0 ? '+' : '') + fmt(n, digits);
}

function fmtP(p) {
  if (p === null || p === undefined) return '—';
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
  if (params) for (const [k, v] of Object.entries(params)) if (v !== null && v !== undefined) url.searchParams.set(k, v);
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

/* ---------------------------------------------------------------- map */

function initMap() {
  if (typeof L === 'undefined') {
    const frame = document.querySelector('.map-frame');
    if (frame) frame.hidden = true;
    return;
  }
  map = L.map('map', { worldCopyJump: true, minZoom: 2 }).setView([-12.05, -77.03], 3);

  // Basemap: NASA GIBS Blue Marble
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

  // Shift+drag selects a box
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

function setPoint(lat, lon) {
  state.point = { lat, lon };
  state.bbox = null;
  if (map) {
    if (marker) marker.remove();
    if (rect) { rect.remove(); rect = null; }
    marker = L.circleMarker([lat, lon], {
      radius: 7, color: '#16272b', weight: 2, fillColor: '#125e5a', fillOpacity: 1,
    }).addTo(map);
  }
  $('#place-chosen').textContent = `${lat.toFixed(2)}, ${lon.toFixed(2)}`;
}

function setPointA(lat, lon) {
  state.point = { lat, lon };
  if (map) {
    if (marker) marker.remove();
    marker = L.circleMarker([lat, lon], {
      radius: 7, color: '#16272b', weight: 2, fillColor: '#125e5a', fillOpacity: 1,
    }).addTo(map).bindPopup('A');
  }
  $('#place-chosen').textContent = `A: ${lat.toFixed(2)}, ${lon.toFixed(2)}`;
}

function setPointB(lat, lon) {
  state.pointCompareB = { lat, lon };
  if (map) {
    if (markerB) markerB.remove();
    markerB = L.circleMarker([lat, lon], {
      radius: 7, color: '#16272b', weight: 2, fillColor: '#a2610f', fillOpacity: 1,
    }).addTo(map).bindPopup('B');
  }
  $('#place-chosen-b').textContent = `B: ${lat.toFixed(2)}, ${lon.toFixed(2)}`;
}

function setBBox(bbox) {
  state.bbox = bbox;
  state.point = null;
  if (map) {
    if (marker) { marker.remove(); marker = null; }
    if (rect) rect.remove();
    const [[w, s], [e, n]] = [[bbox[0], bbox[1]], [bbox[2], bbox[3]]];
    rect = L.rectangle([[s, w], [n, e]], { color: '#16272b', weight: 2, fillColor: '#125e5a', fillOpacity: 0.12 }).addTo(map);
  }
  $('#place-chosen').textContent = `[${bbox.map((v) => v.toFixed(2)).join(', ')}]`;
  if (state.mode === 'trendmap') {
    $('#trendmap-bar').hidden = false;
  }
}

/* ---------------------------------------------------------------- search */

async function searchPlace(q, isB = false) {
  const list = $(isB ? '#place-results-b' : '#place-results');
  list.innerHTML = '';
  if (!q || q.length < 2) return;
  try {
    const data = await apiGet('/api/geocode', { q });
    const items = (data && data.results) || [];
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
    if (isB) setPointB(first.lat, first.lon);
    else setPoint(first.lat, first.lon);
    if (map) map.setView([first.lat, first.lon], 6);
  } catch (err) {
    showError(err);
  }
}

/* ---------------------------------------------------------------- catalog */

function renderCatalog() {
  const select = $('#variable-select');
  select.innerHTML = '';
  for (const v of state.catalog) {
    const opt = el('option', { value: v.id }, `${v.names?.[state.lang] || v.id} (${v.unit})`);
    select.appendChild(opt);
  }
  onVariableChange();
}

function onVariableChange() {
  const id = $('#variable-select').value;
  const v = state.catalog.find((x) => x.id === id);
  $('#variable-definition').textContent = v && v.simple_definition
    ? (v.simple_definition[state.lang] || v.simple_definition.en)
    : '';
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
    btn.appendChild(el('span', null, c.region_name || c.region_id));
    if (c.description) btn.appendChild(el('small', null, c.description));
    btn.addEventListener('click', () => openCase(c));
    list.appendChild(btn);
  }
}

async function openCase(c) {
  if (c.analysis) { renderAnalysis(c.analysis); return; }
  try {
    const data = await apiGet('/api/analyze', {
      variable_id: c.variable_id,
      lat: c.lat, lon: c.lon,
      bbox: c.bbox ? c.bbox.join(',') : null,
    });
    renderAnalysis(data);
  } catch (err) {
    showError(err);
  }
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

  if (!state.point && !state.bbox) {
    showError(new ApiError('NO_LOCATION', state.lang === 'es'
      ? 'Elige primero un lugar en el mapa o búscalo por nombre.'
      : 'Pick a place on the map or search for it by name first.'));
    return;
  }
  const variableId = $('#variable-select').value;
  if (!variableId) return;

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
    if (state.bbox) params.bbox = state.bbox.join(',');
    else { params.lat = state.point.lat.toFixed(4); params.lon = state.point.lon.toFixed(4); }

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

  $('#verdict-title').textContent = t(`verdict.${code}`);
  $('#verdict-plain').textContent = a.answers?.['what']?.[state.lang] || '';

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
  renderFindings(a);
  renderMethod(a);
  renderProvenance(a);
  $('#results').focus({ preventScroll: true });
}

function renderFindings(a) {
  $('#f-where').textContent = a.answers?.['where']?.[state.lang] || a.region?.name || '';

  const slope = a.trend?.sen_slope_per_decade;
  const ci = a.trend?.sen_ci95_per_decade;
  $('#f-slope').textContent = signed(slope, 3);
  $('#f-unit').textContent = `${a.variable?.unit || ''} ${t('measure.perDecade')}`.trim();
  $('#f-ci').textContent = Array.isArray(ci)
    ? `${t('measure.ci')}: ${signed(ci[0], 3)} … ${signed(ci[1], 3)}`
    : '';

  $('#f-significant').textContent = a.answers?.significant?.[state.lang] || '';

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

/* ---------------------------------------------------------------- chart */

function renderChart() {
  const a = state.analysis;
  if (!a || typeof Chart === 'undefined') return;
  const ctx = $('#trend-chart').getContext('2d');
  if (chart) chart.destroy();

  const s = a.series || {};
  const unit = a.variable?.unit || '';
  const colors = {
    ink: '#16272b', teal: '#125e5a', tealWash: 'rgba(18, 94, 90, 0.14)',
    ochre: '#a2610f', grid: '#e3eae8', muted: '#566967',
  };
  const fonts = { family: 'Schibsted Grotesk, system-ui, sans-serif' };

  let labels, values, trendLine, ciLow, ciHigh, labelKey;

  if (state.view === 'annual') {
    const annual = s.annual || [];
    labels = annual.map((r) => String(r.year));
    values = annual.map((r) => r.value);
    trendLine = s.trend_line_annual || null;
    ciLow = s.trend_ci_low_annual || null;
    ciHigh = s.trend_ci_high_annual || null;
    labelKey = 'chart.annual';
  } else {
    labels = s.dates || [];
    values = state.view === 'anomalies' ? (s.anomalies || []) : (s.raw || []);
    trendLine = state.view === 'anomalies' ? (s.trend_line_anomalies || null) : (s.trend_line || null);
    ciLow = state.view === 'anomalies' ? (s.trend_ci_low_anomalies || null) : (s.trend_ci_low || null);
    ciHigh = state.view === 'anomalies' ? (s.trend_ci_high_anomalies || null) : (s.trend_ci_high || null);
    labelKey = state.view === 'anomalies' ? 'chart.anomalies' : 'chart.monthly';
  }

  const datasets = [{
    label: t(labelKey),
    data: values,
    borderColor: colors.muted,
    backgroundColor: 'transparent',
    borderWidth: 1,
    pointRadius: 0,
    tension: 0,
    spanGaps: false,
  }];

  if (ciHigh && ciHigh.length) {
    datasets.push({
      label: 'CI high', data: ciHigh, borderWidth: 0, pointRadius: 0,
      backgroundColor: colors.tealWash, fill: '+1', spanGaps: false,
    });
    datasets.push({
      label: 'CI low', data: ciLow, borderWidth: 0, pointRadius: 0,
      backgroundColor: colors.tealWash, fill: false, spanGaps: false,
    });
  }
  if (trendLine && trendLine.length) {
    datasets.push({
      label: 'Sen', data: trendLine, borderColor: colors.teal, borderWidth: 2.5,
      borderDash: [6, 4], pointRadius: 0, fill: false, spanGaps: false,
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
      animation: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? false : { duration: 300 },
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
    let data;
    if (DEV_FIXTURE) {
      data = await devFixtureTrendMap(variableId);
    } else {
      data = await apiGet('/api/trendmap', {
        variable_id: variableId,
        bbox: state.bbox.join(','),
      });
    }
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
        <strong>${lat.toFixed(2)}, ${lon.toFixed(2)}</strong><br>
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
  $('#trendmap-heading').textContent = `${tm.variable_id || ''} — ${t('trendmap.legend.share', { pct: sharePct })}`;
  $('#trendmap-summary').textContent = `${t('trendmap.cells')}: ${tm.n_cells || totalCells} | ${t('trendmap.legend.sig')}: ${tm.n_significant || sigCount} (FDR q=${tm.fdr_q || 0.10})`;
}

async function devFixtureTrendMap(varId) {
  const res = await fetch('/tests/fixtures/real/power_monthly_regional_piura_T2M.json');
  const d = await res.json();
  const coords = d.features.map(f => f.geometry.coordinates);
  const lons = sortedUnique(coords.map(c => c[0]));
  const lats = sortedUnique(coords.map(c => c[1]));

  const slope_per_decade = [];
  const significant_fdr = [];
  let nSig = 0;

  for (let r = 0; r < lats.length; r++) {
    const rowSlope = [];
    const rowSig = [];
    for (let c = 0; c < lons.length; c++) {
      const slope = Number((0.15 + (r - 4) * 0.04 - (c - 3) * 0.02).toFixed(3));
      const isSig = Math.abs(slope) > 0.16;
      if (isSig) nSig++;
      rowSlope.push(slope);
      rowSig.push(isSig);
    }
    slope_per_decade.push(rowSlope);
    significant_fdr.push(rowSig);
  }

  return {
    schema: 'trendmap/2',
    variable_id: varId,
    unit_per_decade: '°C/década',
    bbox: [-82, -7, -78, -3],
    lats,
    lons,
    slope_per_decade,
    p_value: [],
    significant_fdr,
    fdr_q: 0.10,
    n_cells: lats.length * lons.length,
    n_significant: nSig,
    period: { start: '1981-01', end: '2025-12' },
    summary: { share_up_significant: nSig / (lats.length * lons.length), share_down_significant: 0.0 },
    provenance: { kind: 'fixture', source: 'NASA POWER Regional' },
  };
}

function sortedUnique(arr) {
  return [...new Set(arr)].sort((a, b) => a - b);
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
    let compData;
    if (DEV_FIXTURE) {
      compData = await devFixtureCompare(variableId);
    } else {
      compData = await apiGet('/api/compare', {
        variable_id: variableId,
        a: `${state.point.lat.toFixed(4)},${state.point.lon.toFixed(4)}`,
        b: `${state.pointCompareB.lat.toFixed(4)},${state.pointCompareB.lon.toFixed(4)}`,
      });
    }
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

  const a = data.a;
  const b = data.b;
  const cmp = data.comparison || {};

  $('#compare-title').textContent = `${a.region?.name || 'A'} vs. ${b.region?.name || 'B'}`;

  const statement = cmp.statement?.[state.lang] || cmp.statement?.en || (cmp.opposite ? t('compare.opposite.yes') : t('compare.opposite.no'));
  $('#compare-statement').textContent = statement;

  const badge = $('#compare-badge');
  badge.className = `compare-badge ${cmp.opposite ? 'opposite' : 'similar'}`;
  badge.textContent = cmp.opposite ? t('compare.opposite.yes') : t('compare.opposite.no');

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

  chartCompareA = new Chart(ctxA, {
    type: 'line',
    data: {
      labels: sA.dates || [],
      datasets: [
        { data: sA.raw || [], borderColor: '#125e5a', borderWidth: 1, pointRadius: 0 },
        { data: sA.trend_line || [], borderColor: '#16272b', borderWidth: 2, borderDash: [4, 4], pointRadius: 0 }
      ],
    },
    options: chartOpts,
  });

  chartCompareB = new Chart(ctxB, {
    type: 'line',
    data: {
      labels: sB.dates || [],
      datasets: [
        { data: sB.raw || [], borderColor: '#a2610f', borderWidth: 1, pointRadius: 0 },
        { data: sB.trend_line || [], borderColor: '#16272b', borderWidth: 2, borderDash: [4, 4], pointRadius: 0 }
      ],
    },
    options: chartOpts,
  });
}

async function devFixtureCompare(varId) {
  const a = await devFixtureAnalysis();
  const b = JSON.parse(JSON.stringify(a));
  b.region.name = 'Arctic, Svalbard';
  b.series.raw = a.series.raw.map(v => v !== null ? v - 24 : null);
  b.series.trend_line = a.series.raw.map((_, i) => -5 + i * 0.015);
  a.series.trend_line = a.series.raw.map((_, i) => 18 + i * 0.005);

  return {
    a,
    b,
    comparison: {
      opposite: false,
      difference_significant: true,
      z: 3.42,
      statement: {
        en: 'Both regions show warming trends, but the Arctic warms at 3.2x the rate of the equatorial region.',
        es: 'Ambas regiones presentan calentamiento, pero el Ártico se calienta a una tasa 3.2x mayor que la región ecuatorial.',
      },
    },
  };
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

const GLOSSARY = {
  'glossary.trend': ['verdict.howmuch', '#f-slope'],
  'glossary.anomaly': ['chart.anomalies', '#chart-heading'],
  'glossary.pvalue': ['method.p', '#tests-table'],
  'glossary.significance': ['verdict.significant', '#f-significant'],
  'glossary.ci': ['measure.ci', '#f-ci'],
  'glossary.autocorrelation': ['method.autocorr', '#method-autocorr'],
};

function initGlossary() {
  const pop = $('#glossary-pop');
  for (const [key, [, targetSel]] of Object.entries(GLOSSARY)) {
    const target = document.querySelector(targetSel);
    if (!target) continue;
    const btn = el('button', { type: 'button', class: 'term', 'aria-describedby': 'glossary-pop' }, '?');
    btn.setAttribute('aria-label', t(key));
    btn.addEventListener('click', (ev) => {
      ev.stopPropagation();
      const r = btn.getBoundingClientRect();
      pop.hidden = false;
      pop.textContent = t(key);
      pop.style.left = `${Math.min(r.left + window.scrollX, window.innerWidth - 320)}px`;
      pop.style.top = `${r.bottom + window.scrollY + 6}px`;
    });
    target.parentNode.insertBefore(btn, target.nextSibling);
  }
  document.addEventListener('click', () => { if (pop) pop.hidden = true; });
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape' && pop) pop.hidden = true; });
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

/* ---------------------------------------------------------------- dev */

async function devFixtureAnalysis() {
  const res = await fetch('/tests/fixtures/real/power_monthly_point_lima.json');
  const raw = await res.json();
  const param = raw.properties?.parameter || {};
  const varId = $('#variable-select')?.value in param ? $('#variable-select').value : 'T2M';
  const series = param[varId] || {};
  const dates = [], values = [];
  for (const k of Object.keys(series)) {
    if (k.endsWith('13')) continue;
    dates.push(`${k.slice(0, 4)}-${k.slice(4, 6)}`);
    values.push(series[k] === -999 ? null : series[k]);
  }
  const meta = raw.parameters?.[varId] || {};
  return {
    schema: 'analysis/2',
    variable: { id: varId, names: { en: meta.longname, es: meta.longname }, unit: meta.units },
    region: { kind: 'point', name: 'Lima, Peru', lat: -12.05, lon: -77.03, bbox: null },
    trend: null, tests: null, significance: { verdict_code: 'INSUFFICIENT_DATA' },
    detectability: null, answers: {},
    series: { dates, raw: values, anomalies: [], annual: [] },
    warnings: ['REANALYSIS_CAVEAT'],
    provenance: {
      kind: 'fixture', source: raw.header?.api?.name || 'NASA POWER',
      underlying: (raw.header?.sources || []).join(', '),
      request_url: 'https://power.larc.nasa.gov/api/temporal/monthly/point?parameters=T2M&community=AG&longitude=-77.03&latitude=-12.05&start=1981&end=2025&format=JSON',
      retrieved_at: '2026-11-14T17:22:00Z',
      native_resolution: '0.5° x 0.625°',
      citation: 'NASA POWER (NASA Langley Research Center)',
    },
  };
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
        .then((d) => { state.catalog = (d && d.variables) || []; renderCatalog(); })
        .catch((err) => showError(err));
      loadCases();
    });

  if (DEV_FIXTURE) {
    devFixtureAnalysis().then(renderAnalysis).catch((e) => showError(e));
  }
}

document.addEventListener('DOMContentLoaded', boot);

window.__etd = { state, investigate, renderAnalysis, renderTrendMap, renderCompare, setLang, setMode, fmt, fmtP, signed, t };

})();
