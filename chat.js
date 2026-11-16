(function () {
'use strict';
// SI-assisted: cfable (Claude Sonnet 5.5)
// Huiracocha IA — conversation console, "how it works" note and all-variables scan.
//
// This file only formats and sequences. Every number it shows comes from the API
// (/api/ai/chat, /api/ai/about, /api/scan and the analysis endpoints); the
// "thinking" line names the real step that is running, with a real clock, and
// there is no artificial delay anywhere.

const I18N = window.__etdI18n;
if (!I18N) return;

/* ------------------------------------------------------------------ strings */

const EN = {
  'chat.title': 'Huiracocha AI',
  'chat.subtitle': 'Ask in plain language. Every number comes from real NASA data and every statement cites its source.',
  'chat.label': 'Your question',
  'chat.placeholder': 'Tell me a place and what worries you: “Is it raining less in Ica?”, “Frost days in Huancayo”, “What is changing in Ayacucho?”, “Compare rainfall in Andahuaylas and Lima”…',
  'chat.ask': 'Ask',
  'chat.ask.busy': 'Thinking with Huiracocha AI…',
  'chat.count': '{n}/500',
  'chat.hint': 'Enter to send · Shift+Enter for a new line',
  'chat.places': 'Places',
  'chat.topics': 'Topics',
  'chat.you': 'You',
  'chat.ai': 'Huiracocha AI',
  'chat.welcome': 'Hello, I am **Huiracocha AI**, your Earth-trend detective. Tell me a place and what worries you, and I will check it against real NASA data: what is changing, where, how much, and whether the change is significant. Try one of these questions or write your own.',
  'chat.ex.1': 'Is it raining less in Ica?',
  'chat.ex.2': 'Is Lima getting hotter?',
  'chat.ex.3': 'Are there fewer frosts in Huancayo?',
  'chat.ex.4': 'What is changing in Ayacucho?',
  'chat.ex.5': 'Compare rainfall in Andahuaylas and Lima',
  'chat.place.q': 'What is changing in {place}?',
  'chat.topic.rain': 'Rainfall in ',
  'chat.topic.temp': 'Temperature in ',
  'chat.topic.frost': 'Frost days in ',
  'chat.topic.wind': 'Wind in ',
  'chat.topic.uv': 'UV radiation in ',
  'chat.topic.soil': 'Soil moisture in ',
  'chat.topic.rain.l': 'Rainfall',
  'chat.topic.temp.l': 'Temperature',
  'chat.topic.frost.l': 'Frost',
  'chat.topic.wind.l': 'Wind',
  'chat.topic.uv.l': 'UV',
  'chat.topic.soil.l': 'Soil moisture',
  'chat.sources': 'Sources',
  'chat.followups': 'Continue with',
  'chat.elapsed': '{s} s',
  'chat.stage.understand': 'Reading your question and searching the cited sources (RAG)…',
  'chat.stage.geocode': 'Locating {place} on the map…',
  'chat.stage.fetch': 'Downloading the real NASA series for {place} and testing the trend (Theil–Sen, Mann–Kendall)…',
  'chat.stage.fetch.global': 'Downloading the real series and testing the trend (Theil–Sen, Mann–Kendall)…',
  'chat.stage.compare': 'Downloading both series and comparing their trends…',
  'chat.stage.scan': 'Testing every variable for {place} and correcting for multiple tests (Benjamini–Hochberg)…',
  'chat.result.title': 'Result · {place} · {variable}',
  'chat.result.period': 'Period {start}–{end}',
  'chat.result.see': 'The chart, the statistical tests and the provenance are below ↓',
  'chat.result.compare': 'Comparison ready. The two charts are below ↓',
  'chat.scan.done': 'I tested {n} variables for **{place}**. After correcting for {n} simultaneous tests, **{c}** show a confirmed change. The table is below ↓',
  'chat.scan.top': 'Clearest: {top}.',
  'chat.scan.none': 'I tested {n} variables for **{place}** and none shows a confirmed change after correcting for multiple tests. The table is below ↓',
  'chat.error.generic': 'Something went wrong while answering. Please try again.',
  'chat.error.offline': 'The conversation needs the live server. This static copy only includes the frozen cases; open the live app to chat: {url}',
  'chat.error.place': 'I could not locate “{place}” on the map. Try another spelling or click the map.',
  'chat.error.analysis': 'I could not complete the analysis; the details are shown below.',
  'engine.rules': 'Verified rules + RAG',
  'engine.lora': 'LoRA planner + RAG',
  'engine.title.rules': 'This server answers with verified rules over a retrieval index (RAG). The LoRA planner is used when its model is loaded.',
  'engine.title.lora': 'This server uses the LoRA planner (SmolLM2-1.7B adapter); every plan is verified by rules.',
  'engine.unknown': 'Connecting…',
  'engine.offline': 'Static copy · no live server',
  'about.open': 'How it works',
  'footer.ai': 'Built with AI assistance; the AI-use log is in the repository (docs/AI_USE_LOG.md).',
  'intro.note.static': 'Huiracocha AI is made in Peru and named after Wiracocha, the Andean creator deity. It works from the memory of its own server, with no third-party AI service: a retrieval index (RAG) over cited sources and a statistics engine that downloads the real NASA series. Its planner is a LoRA adapter on SmolLM2-1.7B trained on a single NVIDIA RTX 4070 SUPER GPU. It is built to be precise and traceable, not fast.',
  'intro.note': 'Huiracocha AI is made in Peru and named after Wiracocha, the Andean creator deity. It works from the memory of its own server, with no third-party AI service: a retrieval index (RAG) over {docs} cited documents and a statistics engine that downloads the real NASA series. Its planner is a LoRA adapter on SmolLM2-1.7B trained on a single NVIDIA RTX 4070 SUPER GPU. It is built to be precise and traceable, not fast.',
  'intro.mode': 'Mode of this server',
  'intro.mode.rules': 'verified rules + RAG (the LoRA planner is not loaded here)',
  'intro.mode.lora': 'LoRA planner + RAG, every plan verified by rules',
  'intro.mode.loading': 'verified rules + RAG while the LoRA planner finishes loading into memory',
  'intro.how.title': 'Before you start: how Huiracocha AI works',
  'intro.how.toggle': 'open / close',
  'intro.pipeline': 'From question to answer',
  'intro.step.1': 'Question',
  'intro.step.2': 'Retrieve sources (RAG)',
  'intro.step.3': 'Plan (rules + LoRA)',
  'intro.step.4': 'Real NASA data',
  'intro.step.5': 'Statistics',
  'intro.step.6': 'Cited explanation',
  'intro.rag.title': 'RAG: what it knows',
  'intro.rag.body': 'A search index over cited documents from NASA, NOAA, SENAMHI, ANA, IGP, INAIGEM and peer-reviewed papers. It ranks with BM25 plus a lexicon of everyday words (“llueve”, “heladas”), so a question reaches the right variable and the right local note.',
  'intro.rag.docs': 'documents',
  'intro.rag.pubs': 'institutions',
  'intro.rag.srcs': 'source pages',
  'intro.rag.cities': 'Documents per city',
  'intro.rag.facts': '{n} of them are trends computed by our own engine, not quotations.',
  'intro.lora.title': 'LoRA: how it plans',
  'intro.lora.body': 'The planner turns a question into a plan (variable, place, period). It is {base} with a LoRA adapter ({params} trainable parameters, {examples} examples, {steps} steps in {minutes} min) trained on one {hardware}.',
  'intro.lora.eval': 'On 50 hand-written reference questions the verified rules answer {rules}/{total} and the LoRA {lora}/{total} on GPU ({cpu}/{total} on CPU). That is why a plan is always checked by the rules before it is used.',
  'intro.lora.here': 'In this server: {engine}.',
  'intro.res.title': 'Resources obtained',
  'intro.res.body': '{vars} real variables from NASA POWER (MERRA-2 and CERES), GISTEMP and the NSIDC Sea Ice Index, plus the platforms named in the challenge:',
  'intro.res.prov': 'Every result shows its exact request URL, date and SHA-256 fingerprint.',
  'scan.eyebrow': 'All variables · {place}',
  'scan.title': '{c} of {n} changes confirmed',
  'scan.lead': 'Every variable was tested at the same point and period. “Confirmed” means the engine’s verdict is significant and the change also survives the Benjamini–Hochberg correction for {n} simultaneous tests (q < 0.05).',
  'scan.col.var': 'Variable',
  'scan.col.dir': 'Trend',
  'scan.col.slope': 'Per decade',
  'scan.col.period': 'Period',
  'scan.col.p': 'p',
  'scan.col.q': 'q',
  'scan.col.verdict': 'Verdict',
  'scan.filter.all': 'All',
  'scan.filter.confirmed': 'Confirmed only',
  'scan.verdict.confirmed': 'Confirmed',
  'scan.verdict.unconfirmed': 'Significant, not confirmed',
  'scan.verdict.suggestive': 'Suggestive',
  'scan.verdict.none': 'Not significant',
  'scan.verdict.insufficient': 'Insufficient data',
  'scan.verdict.error': 'Unavailable',
  'scan.up': 'rising',
  'scan.down': 'falling',
  'scan.flat': 'flat',
  'scan.hint': 'Select a row to open its full analysis.',
  'scan.method': 'Method: Theil–Sen slope; Mann–Kendall test corrected for autocorrelation (Hamed & Rao 1998); Benjamini–Hochberg (1995) correction across all variables.',
};

const ES = {
  'chat.title': 'Huiracocha IA',
  'chat.subtitle': 'Pregunta en lenguaje natural. Cada cifra viene de datos reales de la NASA y cada afirmación cita su fuente.',
  'chat.label': 'Tu pregunta',
  'chat.placeholder': 'Dime un lugar y qué te preocupa: «¿Llueve menos en Ica?», «Heladas en Huancayo», «¿Qué está cambiando en Ayacucho?», «Compara la lluvia de Andahuaylas y Lima»…',
  'chat.ask': 'Preguntar',
  'chat.ask.busy': 'Pensando con Huiracocha IA…',
  'chat.count': '{n}/500',
  'chat.hint': 'Enter para enviar · Shift+Enter para otra línea',
  'chat.places': 'Lugares',
  'chat.topics': 'Temas',
  'chat.you': 'Tú',
  'chat.ai': 'Huiracocha IA',
  'chat.welcome': 'Hola, soy **Huiracocha IA**, tu detective de tendencias de la Tierra. Dime un lugar y qué te preocupa, y lo compruebo con datos reales de la NASA: qué cambia, dónde, cuánto y si el cambio es significativo. Prueba una de estas preguntas o escribe la tuya.',
  'chat.ex.1': '¿Llueve menos en Ica?',
  'chat.ex.2': '¿Hace más calor en Lima?',
  'chat.ex.3': '¿Hay menos heladas en Huancayo?',
  'chat.ex.4': '¿Qué está cambiando en Ayacucho?',
  'chat.ex.5': 'Compara la lluvia de Andahuaylas y Lima',
  'chat.place.q': '¿Qué está cambiando en {place}?',
  'chat.topic.rain': 'Lluvia en ',
  'chat.topic.temp': 'Temperatura en ',
  'chat.topic.frost': 'Heladas en ',
  'chat.topic.wind': 'Viento en ',
  'chat.topic.uv': 'Radiación UV en ',
  'chat.topic.soil': 'Humedad del suelo en ',
  'chat.topic.rain.l': 'Lluvia',
  'chat.topic.temp.l': 'Temperatura',
  'chat.topic.frost.l': 'Heladas',
  'chat.topic.wind.l': 'Viento',
  'chat.topic.uv.l': 'UV',
  'chat.topic.soil.l': 'Humedad del suelo',
  'chat.sources': 'Fuentes',
  'chat.followups': 'Continuar con',
  'chat.elapsed': '{s} s',
  'chat.stage.understand': 'Leyendo tu pregunta y buscando en las fuentes citadas (RAG)…',
  'chat.stage.geocode': 'Ubicando {place} en el mapa…',
  'chat.stage.fetch': 'Descargando la serie real de la NASA para {place} y probando la tendencia (Theil–Sen, Mann–Kendall)…',
  'chat.stage.fetch.global': 'Descargando la serie real y probando la tendencia (Theil–Sen, Mann–Kendall)…',
  'chat.stage.compare': 'Descargando ambas series y comparando sus tendencias…',
  'chat.stage.scan': 'Probando todas las variables de {place} y corrigiendo por pruebas múltiples (Benjamini–Hochberg)…',
  'chat.result.title': 'Resultado · {place} · {variable}',
  'chat.result.period': 'Periodo {start}–{end}',
  'chat.result.see': 'El gráfico, las pruebas estadísticas y la procedencia están abajo ↓',
  'chat.result.compare': 'Comparación lista. Los dos gráficos están abajo ↓',
  'chat.scan.done': 'Probé {n} variables para **{place}**. Tras corregir por {n} pruebas simultáneas, **{c}** muestran un cambio confirmado. La tabla está abajo ↓',
  'chat.scan.top': 'Lo más claro: {top}.',
  'chat.scan.none': 'Probé {n} variables para **{place}** y ninguna muestra un cambio confirmado tras corregir por pruebas múltiples. La tabla está abajo ↓',
  'chat.error.generic': 'Algo falló al responder. Inténtalo de nuevo.',
  'chat.error.offline': 'La conversación necesita el servidor en vivo. Esta copia estática solo incluye los casos congelados; abre la app en vivo para conversar: {url}',
  'chat.error.place': 'No pude ubicar «{place}» en el mapa. Prueba otra grafía o haz clic en el mapa.',
  'chat.error.analysis': 'No pude completar el análisis; el detalle se muestra abajo.',
  'engine.rules': 'Reglas verificadas + RAG',
  'engine.lora': 'Planificador LoRA + RAG',
  'engine.title.rules': 'Este servidor responde con reglas verificadas sobre un índice de recuperación (RAG). El planificador LoRA se usa cuando su modelo está cargado.',
  'engine.title.lora': 'Este servidor usa el planificador LoRA (adaptador de SmolLM2-1.7B); cada plan lo verifican las reglas.',
  'engine.unknown': 'Conectando…',
  'engine.offline': 'Copia estática · sin servidor',
  'about.open': 'Cómo funciona',
  'footer.ai': 'Construida con asistencia de IA; el registro de uso de IA está en el repositorio (docs/AI_USE_LOG.md).',
  'intro.note.static': 'Huiracocha IA nace en el Perú y lleva el nombre de Wiracocha, la deidad creadora andina. Trabaja desde la memoria de su propio servidor, sin servicios de IA de terceros: un índice de recuperación (RAG) sobre fuentes citadas y un motor estadístico que descarga las series reales de la NASA. Su planificador es un adaptador LoRA sobre SmolLM2-1.7B entrenado en una sola GPU NVIDIA RTX 4070 SUPER. Está hecha para ser precisa y trazable, no rápida.',
  'intro.note': 'Huiracocha IA nace en el Perú y lleva el nombre de Wiracocha, la deidad creadora andina. Trabaja desde la memoria de su propio servidor, sin servicios de IA de terceros: un índice de recuperación (RAG) sobre {docs} documentos citados y un motor estadístico que descarga las series reales de la NASA. Su planificador es un adaptador LoRA sobre SmolLM2-1.7B entrenado en una sola GPU NVIDIA RTX 4070 SUPER. Está hecha para ser precisa y trazable, no rápida.',
  'intro.mode': 'Modo de este servidor',
  'intro.mode.rules': 'reglas verificadas + RAG (aquí no está cargado el planificador LoRA)',
  'intro.mode.lora': 'planificador LoRA + RAG, cada plan verificado por reglas',
  'intro.mode.loading': 'reglas verificadas + RAG mientras el planificador LoRA termina de cargarse en memoria',
  'intro.how.title': 'Antes de empezar: cómo funciona Huiracocha IA',
  'intro.how.toggle': 'abrir / cerrar',
  'intro.pipeline': 'De la pregunta a la respuesta',
  'intro.step.1': 'Pregunta',
  'intro.step.2': 'Recupera fuentes (RAG)',
  'intro.step.3': 'Plan (reglas + LoRA)',
  'intro.step.4': 'Datos reales de la NASA',
  'intro.step.5': 'Estadística',
  'intro.step.6': 'Explicación con citas',
  'intro.rag.title': 'RAG: lo que sabe',
  'intro.rag.body': 'Un índice de búsqueda sobre documentos citados de NASA, NOAA, SENAMHI, ANA, IGP, INAIGEM y artículos revisados por pares. Ordena con BM25 más un léxico de palabras cotidianas («llueve», «heladas»), de modo que una pregunta llega a la variable correcta y a la nota local correcta.',
  'intro.rag.docs': 'documentos',
  'intro.rag.pubs': 'instituciones',
  'intro.rag.srcs': 'páginas fuente',
  'intro.rag.cities': 'Documentos por ciudad',
  'intro.rag.facts': '{n} de ellos son tendencias calculadas por nuestro propio motor, no citas.',
  'intro.lora.title': 'LoRA: cómo planifica',
  'intro.lora.body': 'El planificador convierte una pregunta en un plan (variable, lugar, periodo). Es {base} con un adaptador LoRA ({params} parámetros entrenables, {examples} ejemplos, {steps} pasos en {minutes} min) entrenado en una {hardware}.',
  'intro.lora.eval': 'En 50 preguntas de referencia escritas a mano, las reglas verificadas aciertan {rules}/{total} y el LoRA {lora}/{total} en GPU ({cpu}/{total} en CPU). Por eso un plan siempre lo comprueban las reglas antes de usarse.',
  'intro.lora.here': 'En este servidor: {engine}.',
  'intro.res.title': 'Recursos obtenidos',
  'intro.res.body': '{vars} variables reales de NASA POWER (MERRA-2 y CERES), GISTEMP y el índice de hielo marino del NSIDC, más las plataformas que nombra el reto:',
  'intro.res.prov': 'Cada resultado muestra la URL exacta de la petición, la fecha y una huella SHA-256.',
  'scan.eyebrow': 'Todas las variables · {place}',
  'scan.title': '{c} de {n} cambios confirmados',
  'scan.lead': 'Cada variable se probó en el mismo punto y periodo. «Confirmado» significa que el veredicto del motor es significativo y que el cambio además resiste la corrección de Benjamini–Hochberg por {n} pruebas simultáneas (q < 0,05).',
  'scan.col.var': 'Variable',
  'scan.col.dir': 'Tendencia',
  'scan.col.slope': 'Por década',
  'scan.col.period': 'Periodo',
  'scan.col.p': 'p',
  'scan.col.q': 'q',
  'scan.col.verdict': 'Veredicto',
  'scan.filter.all': 'Todas',
  'scan.filter.confirmed': 'Solo confirmadas',
  'scan.verdict.confirmed': 'Confirmado',
  'scan.verdict.unconfirmed': 'Significativo, sin confirmar',
  'scan.verdict.suggestive': 'Sugerente',
  'scan.verdict.none': 'No significativo',
  'scan.verdict.insufficient': 'Datos insuficientes',
  'scan.verdict.error': 'No disponible',
  'scan.up': 'sube',
  'scan.down': 'baja',
  'scan.flat': 'estable',
  'scan.hint': 'Selecciona una fila para abrir su análisis completo.',
  'scan.method': 'Método: pendiente de Theil–Sen; prueba de Mann–Kendall corregida por autocorrelación (Hamed y Rao 1998); corrección de Benjamini–Hochberg (1995) entre todas las variables.',
};

Object.assign(I18N.STRINGS.en, EN);
Object.assign(I18N.STRINGS.es, ES);

/* ------------------------------------------------------------------ helpers */

const GLOBAL_VARS = ['GISTEMP_TANOM', 'SEAICE_EXTENT_N', 'SEAICE_EXTENT_S'];
const MAX_LEN = 500;
const LIVE_URL = 'https://huiracochaia.soulgeit.com/';
const PLACES = ['Lima', 'Huancayo', 'Andahuaylas', 'Ica', 'Ayacucho'];
const TOPICS = ['rain', 'temp', 'frost', 'wind', 'uv', 'soil'];

let api = null;
let ctx = {};
let busy = false;
let about = null;
let aboutFailed = false;
let aboutPolls = 0;
let els = {};

const $ = (sel) => document.querySelector(sel);
const t = (key, vars) => I18N.t(key, vars);
const lang = () => (api && api.state && api.state.lang) || window.__etdLang || 'en';

function el(tag, cls, text) {
  const node = document.createElement(tag);
  if (cls) node.className = cls;
  if (text !== undefined && text !== null) node.textContent = text;
  return node;
}

function esc(value) {
  return String(value === undefined || value === null ? '' : value)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

// **bold** and line breaks only; everything else is escaped first.
function md(text) {
  return esc(text).replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>').replace(/\n/g, '<br>');
}

function num(n) {
  if (n === undefined || n === null || Number.isNaN(Number(n))) return '—';
  return Number(n).toLocaleString(lang() === 'es' ? 'es-PE' : 'en-US');
}

function catalogCard(id) {
  const cat = (api && api.state && api.state.catalog) || [];
  return cat.find((v) => v.id === id) || null;
}

function varName(id, fallbackNames, L) {
  const card = catalogCard(id);
  const names = (card && card.names) || fallbackNames || {};
  const k = L || lang();
  return names[k] || names.en || names.es || id;
}

function pick(obj, L) {
  if (!obj) return '';
  if (typeof obj === 'string') return obj;
  const k = L || lang();
  return obj[k] || obj.en || obj.es || '';
}

// The conversation answers in the language of the user's last message (the UI
// language only decides the page itself): "¿Llueve menos en Ica?" in an English
// page still gets a Spanish thread.
let convLang = null;
const cl = () => convLang || lang();

function tc(key, vars) {
  const table = I18N.STRINGS[cl()] || I18N.STRINGS.en;
  let s = table[key];
  if (s === undefined) s = I18N.STRINGS.en[key];
  if (s === undefined) return key;
  if (vars) for (const k of Object.keys(vars)) s = s.replaceAll(`{${k}}`, String(vars[k]));
  return s;
}

/* ------------------------------------------------------------------ thread */

function scrollThread() {
  if (els.thread) els.thread.scrollTop = els.thread.scrollHeight;
}

function addMessage(role, build) {
  const wrap = el('div', `msg msg-${role}`);
  const body = el('div', 'msg-body');
  wrap.append(el('div', 'msg-who', role === 'user' ? t('chat.you') : t('chat.ai')), body);
  build(body, wrap);
  els.thread.appendChild(wrap);
  scrollThread();
  return wrap;
}

function renderSources(body, sources) {
  if (!sources || !sources.length) return;
  const box = el('div', 'msg-sources');
  box.append(el('span', 'msg-sources-label', t('chat.sources')));
  const ul = el('ul');
  for (const s of sources.slice(0, 5)) {
    const li = el('li');
    if (s.url && /^https?:\/\//.test(s.url)) {
      const a = el('a', null, s.title || s.publisher || s.url);
      a.href = s.url;
      a.target = '_blank';
      a.rel = 'noopener noreferrer';
      li.append(a);
    } else {
      li.textContent = s.title || s.publisher || '';
    }
    if (s.publisher && s.title) li.append(el('span', 'msg-pub', ` — ${s.publisher}`));
    ul.append(li);
  }
  box.append(ul);
  body.append(box);
}

function renderChips(body, list) {
  if (!list || !list.length) return;
  const box = el('div', 'msg-chips');
  box.setAttribute('aria-label', t('chat.followups'));
  for (const q of list.slice(0, 5)) {
    const b = el('button', 'chip-btn', q);
    b.type = 'button';
    b.addEventListener('click', () => send(q));
    box.append(b);
  }
  body.append(box);
}

function say(text, extra) {
  return addMessage('ai', (body) => {
    body.innerHTML = md(text);
    if (extra) extra(body);
  });
}

// A live "thinking" bubble: the label always names the real step in progress.
function thinking(label) {
  const wrap = el('div', 'msg msg-ai msg-thinking');
  wrap.setAttribute('role', 'status');
  const body = el('div', 'msg-body');
  const dots = el('span', 'dots');
  dots.setAttribute('aria-hidden', 'true');
  dots.innerHTML = '<i></i><i></i><i></i>';
  const text = el('span', 'think-text', label);
  const clock = el('span', 'think-clock', '');
  body.append(dots, text, clock);
  wrap.append(el('div', 'msg-who', t('chat.ai')), body);
  els.thread.appendChild(wrap);
  scrollThread();
  const t0 = performance.now();
  const tick = setInterval(() => {
    clock.textContent = t('chat.elapsed', { s: Math.floor((performance.now() - t0) / 1000) });
  }, 1000);
  return {
    set(next) { text.textContent = next; },
    done() { clearInterval(tick); wrap.remove(); },
  };
}

function setBusy(on) {
  busy = on;
  if (!els.ask) return;
  els.ask.disabled = on;
  els.ask.classList.toggle('is-busy', on);
  els.ask.setAttribute('aria-busy', String(on));
  if (els.askLabel) els.askLabel.textContent = on ? t('chat.ask.busy') : t('chat.ask');
}

function updateCount() {
  if (els.count && els.input) els.count.textContent = t('chat.count', { n: els.input.value.length });
}

function errorText(err) {
  const code = err && err.code;
  if (code === 'API_UNAVAILABLE' || code === 'DATA_UNAVAILABLE') return tc('chat.error.offline', { url: LIVE_URL });
  return (err && err.message) ? err.message : tc('chat.error.generic');
}

function mergeContext(next) {
  if (!next || typeof next !== 'object') return;
  for (const key of ['place', 'place_b', 'variable_id']) {
    if (typeof next[key] === 'string' && next[key]) ctx[key] = next[key];
    else if (key === 'place_b') delete ctx.place_b;
  }
}

/* ------------------------------------------------------------------ actions */

function selectVariable(id) {
  const sel = $('#variable-select');
  if (!sel) return;
  sel.value = id;
  api.onVariableChange();
}

// A variable that starts later (aerosols 2001, clouds 1984) must not be asked from 1981:
// the series would be 55 % empty and the engine would answer "insufficient data".
function applyPeriod(plan, variableId) {
  const startEl = $('#period-start');
  const endEl = $('#period-end');
  if (!startEl || !endEl) return;
  const card = catalogCard(variableId);
  const first = parseInt(String((card && card.source && card.source.start) || '1981').slice(0, 4), 10) || 1981;
  const floor = Math.max(1981, first);
  let start = floor;
  let end = 2025;
  if (plan && plan.start_year && plan.end_year) {
    start = Math.max(plan.start_year, first);
    end = plan.end_year;
  } else if (plan && plan.last_n_years) {
    end = 2025;
    start = Math.max(end - plan.last_n_years + 1, first);
  }
  startEl.value = start;
  endEl.value = end;
}

async function geocode(name) {
  const data = await api.apiGet('/api/geocode', { q: name });
  const items = (data && (data.places || data.results)) || [];
  return items[0] || null;
}

async function locate(name, isB) {
  const first = await geocode(name);
  if (!first) return null;
  if (isB) api.setPointB(first.lat, first.lon, first.name);
  else api.setPoint(first.lat, first.lon, first.name);
  api.panMap(first.lat, first.lon);
  return first;
}

function scrollToResults() {
  const results = $('#results');
  if (!results) return;
  const r = results.getBoundingClientRect();
  if (r.top > window.innerHeight * 0.7 || r.top < 0) results.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function summarizeAnalysis(variableId) {
  const a = api.state.analysis;
  if (!a) {
    say(tc('chat.error.analysis'));
    return;
  }
  const answers = a.answers || {};
  const lines = ['what', 'how_much', 'significant', 'detectability'].map((k) => pick(answers[k], cl())).filter(Boolean);
  const place = (a.region && a.region.name) || '';
  const period = a.period ? tc('chat.result.period', { start: String(a.period.start).slice(0, 4), end: String(a.period.end).slice(0, 4) }) : '';
  addMessage('ai', (body) => {
    body.classList.add('msg-result');
    const head = tc('chat.result.title', { place, variable: varName(variableId, null, cl()) });
    body.innerHTML = `<strong>${esc(head)}</strong><br><span class="msg-period">${esc(period)}</span>`
      + `<ul>${lines.map((l) => `<li>${esc(l)}</li>`).join('')}</ul>`
      + `<span class="msg-see">${esc(tc('chat.result.see'))}</span>`;
  });
  scrollToResults();
}

async function goAnalyze(plan) {
  const variableId = (plan.variable_ids || [])[0];
  if (!variableId) return;
  const isGlobal = GLOBAL_VARS.includes(variableId);
  const th = thinking(isGlobal ? tc('chat.stage.fetch.global') : tc('chat.stage.geocode', { place: plan.place || '' }));
  try {
    api.setMode('single');
    selectVariable(variableId);
    applyPeriod(plan, variableId);
    if (!isGlobal && plan.place) {
      const found = await locate(plan.place, false);
      if (!found) {
        th.done();
        say(tc('chat.error.place', { place: plan.place }));
        return;
      }
    }
    th.set(isGlobal ? tc('chat.stage.fetch.global') : tc('chat.stage.fetch', { place: plan.place || '' }));
    await api.investigate();
    th.done();
    summarizeAnalysis(variableId);
  } catch (err) {
    th.done();
    say(errorText(err));
  }
}

async function goCompare(plan) {
  const variableId = (plan.variable_ids || [])[0];
  if (!variableId || !plan.place || !plan.place_b) return;
  const th = thinking(tc('chat.stage.geocode', { place: `${plan.place} / ${plan.place_b}` }));
  try {
    api.setMode('compare');
    selectVariable(variableId);
    const a = await locate(plan.place, false);
    const b = await locate(plan.place_b, true);
    if (!a || !b) {
      th.done();
      say(tc('chat.error.place', { place: !a ? plan.place : plan.place_b }));
      return;
    }
    th.set(tc('chat.stage.compare'));
    await api.runCompare();
    th.done();
    const statement = ($('#compare-statement') || {}).textContent || '';
    say(`${tc('chat.result.compare')}${statement ? `\n${statement}` : ''}`);
    scrollToResults();
  } catch (err) {
    th.done();
    say(errorText(err));
  }
}

async function goScan(place) {
  if (!place) return;
  const th = thinking(tc('chat.stage.geocode', { place }));
  try {
    const first = await geocode(place);
    if (!first) {
      th.done();
      say(tc('chat.error.place', { place }));
      return;
    }
    api.setMode('single');
    api.setPoint(first.lat, first.lon, first.name);
    api.panMap(first.lat, first.lon);
    th.set(tc('chat.stage.scan', { place: first.name }));
    const data = await api.apiGet('/api/scan', {
      lat: Number(first.lat).toFixed(4),
      lon: Number(first.lon).toFixed(4),
      place: first.name,
    });
    th.done();
    renderScan(data, first.name);
    const confirmed = (data.rows || []).filter((r) => r.confirmed).slice(0, 3).map((r) => varName(r.variable_id, r.names, cl()));
    const head = confirmed.length
      ? tc('chat.scan.done', { n: data.n_tested, c: data.n_confirmed, place: first.name }) + (data.n_confirmed ? ` ${tc('chat.scan.top', { top: confirmed.join(', ') })}` : '')
      : tc('chat.scan.none', { n: data.n_tested, place: first.name });
    say(head);
    scrollToResults();
  } catch (err) {
    th.done();
    say(errorText(err));
  }
}

async function runAction(reply) {
  const plan = reply.plan || {};
  if (reply.action === 'analyze') return goAnalyze(plan);
  if (reply.action === 'compare') return goCompare(plan);
  if (reply.action === 'scan') return goScan(plan.place);
  return undefined;
}

async function send(raw) {
  const text = String(raw === undefined || raw === null ? els.input.value : raw).trim();
  if (!text || busy) return;
  setBusy(true);
  els.input.value = '';
  updateCount();
  addMessage('user', (body) => { body.textContent = text; });
  let th = thinking(tc('chat.stage.understand'));
  try {
    const reply = await api.apiPost('/api/ai/chat', { message: text.slice(0, MAX_LEN), lang: lang(), context: ctx });
    th.done();
    th = null;
    convLang = reply.lang === 'es' || reply.lang === 'en' ? reply.lang : lang();
    mergeContext(reply.context);
    addMessage('ai', (body) => {
      body.innerHTML = md(reply.reply);
      renderSources(body, reply.sources);
      renderChips(body, reply.suggestions);
    });
    await runAction(reply);
  } catch (err) {
    if (th) th.done();
    addMessage('ai', (body) => { body.classList.add('msg-error'); body.textContent = errorText(err); });
  } finally {
    setBusy(false);
    if (els.input) els.input.focus({ preventScroll: true });
  }
}

/* ------------------------------------------------------------------ scan table */

function verdictOf(row) {
  if (row.status === 'error') return { cls: 'na', key: 'scan.verdict.error' };
  if (row.status !== 'ok') return { cls: 'na', key: 'scan.verdict.insufficient' };
  if (row.confirmed) return { cls: 'confirmed', key: 'scan.verdict.confirmed' };
  if (row.is_significant) return { cls: 'unconfirmed', key: 'scan.verdict.unconfirmed' };
  if (row.verdict_code === 'SUGGESTIVE') return { cls: 'suggestive', key: 'scan.verdict.suggestive' };
  return { cls: 'none', key: 'scan.verdict.none' };
}

function scanRow(row) {
  const verdict = verdictOf(row);
  const tr = el('tr', `scan-row scan-${verdict.cls}`);
  tr.dataset.confirmed = row.confirmed ? '1' : '0';
  tr.tabIndex = 0;
  const unit = I18N.formatUnit ? I18N.formatUnit(row.unit || '', lang()) : (row.unit || '');

  const name = el('td', 'scan-var');
  name.append(el('span', 'scan-name', varName(row.variable_id, row.names)), el('span', 'scan-unit', unit));

  const dir = el('td', 'scan-dir');
  if (row.status === 'ok') {
    const glyph = row.direction === 'up' ? '▲' : row.direction === 'down' ? '▼' : '●';
    const word = t(row.direction === 'up' ? 'scan.up' : row.direction === 'down' ? 'scan.down' : 'scan.flat');
    const g = el('span', `dir dir-${row.direction || 'flat'}`, glyph);
    g.setAttribute('role', 'img');
    g.setAttribute('aria-label', word);
    dir.append(g);
  } else {
    dir.textContent = '—';
  }

  const slope = el('td', 'scan-num', row.status === 'ok' ? api.signed(row.slope_per_decade, 3) : '—');
  const period = el('td', 'scan-num scan-period', row.period && row.period.start ? `${String(row.period.start).slice(0, 4)}–${String(row.period.end).slice(0, 4)}` : '—');
  const p = el('td', 'scan-num', row.status === 'ok' ? api.fmtP(row.p_value) : '—');
  const q = el('td', 'scan-num', row.status === 'ok' ? api.fmtP(row.q_value) : '—');
  const verdictCell = el('td', 'scan-verdict');
  verdictCell.append(el('span', `badge badge-${verdict.cls}`, t(verdict.key)));

  tr.append(name, dir, slope, period, p, q, verdictCell);
  if (row.status === 'ok') {
    const open = () => openVariable(row.variable_id);
    tr.addEventListener('click', open);
    tr.addEventListener('keydown', (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); open(); } });
    tr.classList.add('is-link');
  }
  return tr;
}

async function openVariable(variableId) {
  api.setMode('single');
  selectVariable(variableId);
  applyPeriod(null, variableId);
  await api.investigate();
  scrollToResults();
}

function renderScan(data, place) {
  const root = els.scan;
  if (!root) return;
  for (const id of ['empty-state', 'result-root', 'compare-root', 'trendmap-root', 'error-state']) {
    const node = document.getElementById(id);
    if (node) node.hidden = true;
  }
  root.replaceChildren();
  root.dataset.filter = 'all';

  const head = el('div', 'scan-head');
  head.append(el('p', 'verdict-eyebrow', t('scan.eyebrow', { place })));
  head.append(el('h2', null, t('scan.title', { c: data.n_confirmed, n: data.n_tested })));
  head.append(el('p', 'plain serif', t('scan.lead', { n: data.n_tested })));

  const seg = el('div', 'seg');
  seg.setAttribute('role', 'group');
  const mk = (id, key, pressed) => {
    const b = el('button', null, t(key));
    b.type = 'button';
    b.dataset.filter = id;
    b.setAttribute('aria-pressed', String(pressed));
    b.addEventListener('click', () => {
      root.dataset.filter = id;
      seg.querySelectorAll('button').forEach((x) => x.setAttribute('aria-pressed', String(x.dataset.filter === id)));
    });
    return b;
  };
  seg.append(mk('all', 'scan.filter.all', true), mk('confirmed', 'scan.filter.confirmed', false));
  head.append(seg);

  const wrap = el('div', 'scan-table-wrap');
  const table = el('table', 'scan-table');
  const thead = el('thead');
  const hr = el('tr');
  for (const [key, cls] of [['scan.col.var', ''], ['scan.col.dir', ''], ['scan.col.slope', 'scan-num'], ['scan.col.period', 'scan-num'], ['scan.col.p', 'scan-num'], ['scan.col.q', 'scan-num'], ['scan.col.verdict', '']]) {
    hr.append(el('th', cls, t(key)));
  }
  thead.append(hr);
  const tbody = el('tbody');
  for (const row of data.rows || []) tbody.append(scanRow(row));
  table.append(thead, tbody);
  wrap.append(table);

  root.append(head, wrap, el('p', 'help', `${t('scan.hint')} ${t('scan.method')}`));
  root.hidden = false;
}

// Showing any other result hides the scan table (the other renderers do not know it).
function watchResults() {
  const ids = ['result-root', 'compare-root', 'trendmap-root'];
  const observer = new MutationObserver(() => {
    if (ids.some((id) => { const n = document.getElementById(id); return n && !n.hidden; })) els.scan.hidden = true;
  });
  for (const id of ids) {
    const node = document.getElementById(id);
    if (node) observer.observe(node, { attributes: true, attributeFilter: ['hidden'] });
  }
}

/* ------------------------------------------------------------------ composer */

function renderComposerChips() {
  if (!els.chips) return;
  els.chips.replaceChildren();
  const group = (label, items) => {
    const row = el('div', 'chip-row');
    row.append(el('span', 'chip-label', label));
    for (const item of items) row.append(item);
    els.chips.append(row);
  };
  const places = PLACES.map((p) => {
    const b = el('button', 'chip-btn', p);
    b.type = 'button';
    b.addEventListener('click', () => send(t('chat.place.q', { place: p })));
    return b;
  });
  const topics = TOPICS.map((k) => {
    const b = el('button', 'chip-btn chip-topic', t(`chat.topic.${k}.l`));
    b.type = 'button';
    b.addEventListener('click', () => {
      els.input.value = t(`chat.topic.${k}`);
      updateCount();
      els.input.focus();
    });
    return b;
  });
  group(t('chat.places'), places);
  group(t('chat.topics'), topics);
}

function welcome() {
  addMessage('ai', (body) => {
    body.innerHTML = md(t('chat.welcome'));
    renderChips(body, [1, 2, 3, 4, 5].map((i) => t(`chat.ex.${i}`)));
  });
}

/* ------------------------------------------------------------------ how it works */

function engineLabel(engine) {
  return t(engine === 'lora+rag' ? 'engine.lora' : 'engine.rules');
}

function renderBadge() {
  if (!els.badge) return;
  if (!about) {
    els.badge.textContent = t(aboutFailed ? 'engine.offline' : 'engine.unknown');
    els.badge.dataset.engine = aboutFailed ? 'offline' : 'unknown';
    els.badge.removeAttribute('title');
    return;
  }
  const engine = about.deployment.engine;
  els.badge.textContent = engineLabel(engine);
  els.badge.dataset.engine = engine === 'lora+rag' ? 'lora' : 'rules';
  els.badge.title = t(engine === 'lora+rag' ? 'engine.title.lora' : 'engine.title.rules');
}

function renderNote() {
  if (!els.note) return;
  els.note.replaceChildren();
  if (!about) {
    els.note.append(document.createTextNode(t('intro.note.static')));
    return;
  }
  els.note.append(document.createTextNode(`${t('intro.note', { docs: num(about.corpus.documents) })} `));
  const mode = el('span', 'mode-line');
  const loading = about.deployment.lora && about.deployment.lora.state === 'loading';
  const modeKey = about.deployment.engine === 'lora+rag' ? 'intro.mode.lora' : (loading ? 'intro.mode.loading' : 'intro.mode.rules');
  mode.append(el('strong', null, `${t('intro.mode')}: `), document.createTextNode(t(modeKey)));
  els.note.append(mode);
}

// "NASA AppEEARS: Application for Extracting..." -> "NASA AppEEARS"; an agency name alone
// ("Canadian Space Agency: Monitoring...") would repeat, so the descriptive part is used.
function resourceLabel(title) {
  const parts = String(title).split(':');
  let label = parts[0].trim();
  if (parts.length > 1 && /agency|agencia/i.test(label)) label = parts.slice(1).join(':').trim();
  return label.length > 58 ? `${label.slice(0, 56)}…` : label;
}

function card(title) {
  const c = el('article', 'intro-card');
  c.append(el('h3', null, title));
  return c;
}

function statRow(items) {
  const dl = el('dl', 'stat-row');
  for (const [label, value] of items) {
    const box = el('div');
    box.append(el('dd', null, value), el('dt', null, label));
    dl.append(box);
  }
  return dl;
}

function renderIntro() {
  if (!els.grid) return;
  els.grid.replaceChildren();
  if (!about) {
    els.how.hidden = true;
    return;
  }
  els.how.hidden = false;
  const { corpus, lora, catalog, resources } = about;

  const flow = el('ol', 'pipeline');
  flow.setAttribute('aria-label', t('intro.pipeline'));
  for (let i = 1; i <= 6; i += 1) flow.append(el('li', null, t(`intro.step.${i}`)));

  const rag = card(t('intro.rag.title'));
  rag.append(el('p', null, t('intro.rag.body')));
  rag.append(statRow([[t('intro.rag.docs'), num(corpus.documents)], [t('intro.rag.pubs'), num(corpus.publishers)], [t('intro.rag.srcs'), num(corpus.sources)]]));
  rag.append(el('h4', null, t('intro.rag.cities')));
  const top = Math.max(...corpus.cities.map((c) => c.docs), 1);
  const bars = el('ul', 'city-bars');
  for (const c of corpus.cities) {
    const li = el('li');
    const bar = el('b');
    bar.style.width = `${Math.round((c.docs / top) * 100)}%`;
    li.append(el('span', null, c.name), el('span', 'bar-track'), el('i', null, num(c.docs)));
    li.children[1].append(bar);
    bars.append(li);
  }
  rag.append(bars);
  const facts = corpus.cities.reduce((sum, c) => sum + (c.computed_facts || 0), 0);
  if (facts) rag.append(el('p', 'help', t('intro.rag.facts', { n: num(facts) })));

  const lo = card(t('intro.lora.title'));
  lo.append(el('p', null, t('intro.lora.body', {
    base: String(lora.base_model).split('/').pop(),
    params: `${(lora.trainable_params / 1e6).toFixed(1)}M`,
    examples: num(lora.train_examples),
    steps: num(lora.train_steps),
    minutes: (lora.train_seconds / 60).toFixed(1),
    hardware: lora.hardware,
  })));
  const rq = lora.reference_questions;
  lo.append(statRow([['rules', `${rq.rules}/${rq.total}`], ['LoRA GPU', `${rq.lora_gpu}/${rq.total}`], ['LoRA CPU', `${rq.lora_cpu}/${rq.total}`]]));
  lo.append(el('p', null, t('intro.lora.eval', { rules: rq.rules, lora: rq.lora_gpu, cpu: rq.lora_cpu, total: rq.total })));
  lo.append(el('p', 'help', t('intro.lora.here', { engine: engineLabel(about.deployment.engine) })));

  const rs = card(t('intro.res.title'));
  rs.append(el('p', null, t('intro.res.body', { vars: num(catalog.available) })));
  const ul = el('ul', 'res-list');
  for (const r of resources) {
    const li = el('li');
    if (r.url && /^https?:\/\//.test(r.url)) {
      const a = el('a', null, resourceLabel(r.title || r.url));
      a.href = r.url;
      a.target = '_blank';
      a.rel = 'noopener noreferrer';
      li.append(a);
      try { li.append(el('span', 'res-host', new URL(r.url).hostname.replace(/^www\./, ''))); } catch (_) { /* bad URL */ }
    } else {
      li.textContent = r.title;
    }
    ul.append(li);
  }
  rs.append(ul, el('p', 'help', t('intro.res.prov')));

  els.grid.append(flow, rag, lo, rs);
}

async function loadAbout() {
  try {
    about = await api.apiGet('/api/ai/about', { lang: lang() });
    aboutFailed = false;
  } catch (_) {
    about = null;
    aboutFailed = true;
  }
  const aboutBtn = $('#btn-about');
  if (aboutBtn) aboutBtn.hidden = !about;
  renderBadge();
  renderNote();
  renderIntro();
  if (about && about.deployment.lora && about.deployment.lora.state === 'loading' && aboutPolls < 12) {
    aboutPolls += 1;
    setTimeout(loadAbout, 8000);
  }
}

function openIntro() {
  if (!els.how || els.how.hidden) return;
  els.how.open = true;
  els.how.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function restoreIntroState() {
  if (!els.how) return;
  try {
    if (localStorage.getItem('etd.intro') === 'closed') els.how.open = false;
  } catch (_) { /* private mode */ }
  els.how.addEventListener('toggle', () => {
    try { localStorage.setItem('etd.intro', els.how.open ? 'open' : 'closed'); } catch (_) { /* private mode */ }
  });
}

/* ------------------------------------------------------------------ init */

function init(hooks) {
  api = hooks;
  els = {
    thread: $('#chat-thread'),
    input: $('#detective-input'),
    ask: $('#detective-ask-btn'),
    askLabel: $('#ask-label'),
    count: $('#chat-count'),
    chips: $('#detective-chips'),
    badge: $('#engine-badge'),
    note: $('#intro-note'),
    grid: $('#intro-grid'),
    how: $('#intro-how'),
    scan: $('#scan-root'),
  };
  if (!els.thread || !els.input) return;
  els.input.setAttribute('maxlength', String(MAX_LEN));
  els.input.addEventListener('input', updateCount);
  const aboutBtn = $('#btn-about');
  if (aboutBtn) aboutBtn.addEventListener('click', openIntro);
  renderComposerChips();
  welcome();
  watchResults();
  restoreIntroState();
  renderBadge();
  renderNote();
  updateCount();
  loadAbout();
  window.addEventListener('etd:lang', () => {
    renderComposerChips();
    updateCount();
    renderBadge();
    renderNote();
    loadAbout();
    if (!busy && els.askLabel) els.askLabel.textContent = t('chat.ask');
  });
}

window.HuiracochaChat = { init, send };

})();
