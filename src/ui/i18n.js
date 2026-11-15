(function() {
'use strict';
// SI-assisted: claude-omni-1 (Claude Sonnet 5.5)
// Every visible string lives here. `en` is the default (the submission is judged in English).


const STRINGS = {
  en: {
    'app.title': 'EarthTrend Detective',
    'app.tagline': 'Investigate a place on Earth with real NASA Earth science data.',
    'lang.label': 'Language',
    'nav.skip': 'Skip to results',

    'panel.location': 'Place',
    'panel.search.label': 'Search a place',
    'panel.search.placeholder': 'e.g. Piura, Peru',
    'panel.search.button': 'Find',
    'panel.search.noResults': 'No place matched that name. Try a city or region name.',
    'panel.map.hint': 'Click the map to pick a point. Hold Shift and drag to pick a box.',
    'panel.map.attribution': 'Basemap',

    'panel.variable': 'Variable',
    'panel.variable.learn': 'What this measures',
    'panel.period': 'Period',
    'panel.period.from': 'From',
    'panel.period.to': 'To',
    'panel.investigate': 'Investigate',
    'panel.investigating': 'Fetching real data…',
    'panel.report': 'Download report',
    'panel.upload.csv': '📁 Upload Giovanni CSV',

    'results.empty.title': 'Pick a place to begin',
    'results.empty.body': 'Click anywhere on the map or search for a place, choose a variable, and press Investigate. Every number you will see comes from NASA data fetched for that exact point.',

    'verdict.eyebrow': 'Verdict',
    'verdict.what': 'What is changing',
    'verdict.where': 'Where',
    'verdict.howmuch': 'How much per decade',
    'verdict.significant': 'Is it significant?',
    'verdict.years': 'How many years until we can be sure?',
    'verdict.method': 'How we know',
    'verdict.provenance': 'Where this comes from',

    'verdict.SIGNIFICANT_STRONG': 'Clear, strong trend',
    'verdict.SIGNIFICANT': 'Significant trend',
    'verdict.SUGGESTIVE': 'Suggestive, not yet certain',
    'verdict.NOT_SIGNIFICANT': 'No trend detectable so far',
    'verdict.INSUFFICIENT_DATA': 'Not enough data to answer',

    'ladder.1': 'Not enough data',
    'ladder.2': 'No trend detectable',
    'ladder.3': 'Suggestive',
    'ladder.4': 'Significant',
    'ladder.5': 'Clear, strong',

    'measure.ci': '95% confidence interval',
    'measure.perDecade': 'per decade',
    'measure.total': 'over the record',

    'years.available': 'Years of data available',
    'years.needed': 'Years needed for certainty',
    'years.enough': 'The record is long enough to detect this trend.',
    'years.more': 'About {n} more years of data would be needed.',

    'chart.monthly': 'Monthly values',
    'chart.anomalies': 'Anomalies',
    'chart.annual': 'Annual means',
    'chart.note': 'The dashed line is the Sen slope with its confidence band. The seasonal cycle is removed in the anomaly view so the underlying change is visible.',
    'chart.axis.value': 'Value',

    'method.tests': 'Statistical tests',
    'method.test': 'Test',
    'method.statistic': 'Statistic',
    'method.p': 'p-value',
    'method.autocorr': 'Autocorrelation (lag 1)',
    'method.neff': 'Effective sample size',
    'method.references': 'References',
    'method.warnings': 'Caveats',

    'warn.SHORT_RECORD': 'The record is short; trends are hard to separate from natural swings.',
    'warn.LOW_COVERAGE': 'Some months have no data.',
    'warn.HIGH_AUTOCORRELATION': 'Months are correlated with each other; the tests correct for it.',
    'warn.SOURCE_SPLICE': 'The series joins two different products; part of the change may come from the switch.',
    'warn.TESTS_DISAGREE': 'The tests do not fully agree, so the answer is cautious.',
    'warn.REANALYSIS_CAVEAT': 'This is a reanalysis or model product, not a direct satellite measurement.',

    'provenance.source': 'Source',
    'provenance.underlying': 'Based on',
    'provenance.resolution': 'Native resolution',
    'provenance.retrieved': 'Retrieved',
    'provenance.query': 'Exact query',
    'provenance.citation': 'Citation',
    'provenance.warning.fixture': 'This result does not come straight from a NASA service. Do not quote it.',
    'provenance.warning.upload': 'Result computed from a CSV you uploaded.',

    'error.title': 'Data unavailable',
    'error.body': 'The interface never invents data. When the analysis service is down you can still open a frozen, real case.',
    'error.retry': 'Try again',
    'error.code': 'Code',

    'cases.title': 'Frozen cases',
    'cases.body': 'Real analyses stored with their provenance.',
    'cases.none': 'No frozen cases are available right now.',

    'glossary.trend': 'A trend is a steady change over time, measured as slope per decade. It says nothing about the cause.',
    'glossary.anomaly': 'An anomaly is the difference between a month and the average of that same month across the record. It removes the seasonal cycle.',
    'glossary.pvalue': 'The p-value is the chance of seeing a pattern this strong if nothing were changing. Small p-values make a real trend more likely.',
    'glossary.significance': 'Significant means the pattern is unlikely to be chance at the chosen threshold (5% by default). It is not the same as large or important.',
    'glossary.ci': 'A 95% confidence interval is the range that would contain the true slope in 95 out of 100 repeats of the same measurement.',
    'glossary.autocorrelation': 'Autocorrelation means one month resembles the previous one. It makes records look more informative than they are, so the tests correct for it.',

    'footer.data': 'Data: NASA POWER, GISTEMP, NSIDC. Every figure shown comes from the analysis service with its provenance.',
    'footer.disclaimer': 'Not affiliated with or endorsed by NASA.',

    'unit.perDecade': 'per decade',
    'nav.mode.single': 'Single point',
    'nav.mode.trendmap': 'Trend map (regional)',
    'nav.mode.compare': 'Compare two places',
    'trendmap.title': 'Spatial Trend Map',
    'trendmap.legend.sig': 'Significant cell (FDR q=0.10)',
    'trendmap.legend.share': '{pct}% of cells show significant trends',
    'trendmap.cells': 'Grid cells',
    'trendmap.btn': 'Show trend map for box',
    'trendmap.hint': 'Drag with Shift on map to select a regional box, then load trend map.',
    'compare.title': 'Compare Two Places',
    'compare.placeA': 'Place A',
    'compare.placeB': 'Place B',
    'compare.btn': 'Compare places',
    'compare.opposite': 'Opposite trends',
    'compare.opposite.yes': '⚡ Opposite trends detected between both locations',
    'compare.opposite.no': 'Similar trend direction in both locations',
    'compare.diffSig': 'The difference between both trends is statistically significant (z = {z}).',
    'detective.title': 'Ask the Detective',
    'detective.placeholder': 'e.g. Is it raining less in Piura? or Is Arctic ice shrinking?',
    'detective.ask': 'Ask',
    'detective.planning': 'Detective is planning your investigation…',
    'detective.plan.heading': 'Investigation Plan',
    'detective.plan.intent': 'I plan to investigate {var} in {place}.',
    'detective.plan.run': 'Confirm & Investigate',
    'detective.scout.btn': 'What should I investigate here?',
    'detective.scout.heading': 'Suggested Variables for this Area',
    'detective.scout.why': 'Why this matters here',
    'detective.scout.sources': 'Sources',
    'detective.explain.title': 'Detective Explanation',
        'detective.explain.badge.extractive': 'Excerpts from cited sources (no generative AI)',
    'detective.explain.badge.full': 'AI-assisted synthesis from cited sources',
    'verdict.tests_disagree.title': 'Why the statistical tests disagree',
    'verdict.tests_disagree.body': 'The Mann-Kendall test detects persistent direction, but the autocorrelation-adjusted OLS t-test and confidence interval indicate the slope magnitude requires more observation time to achieve definitive certainty.',
    'atlas.load.btn': '🌐 Load Global Atlas (T2M)',
    'atlas.loading': 'Loading global grid atlas…',
    'variable.global_series': 'Fixed global or polar series (no point selection required)',

    'detective.explain.level.school': 'School level',
    'detective.explain.level.uni': 'University level',
    'detective.explain.loading': 'Generating explanation with cited evidence…',
    'detective.explain.sources': 'Cited evidence',
    'demo.btn.start': '▶ Guided Demo',
    'demo.btn.pause': '⏸ Pause',
    'demo.btn.resume': '▶ Resume',
    'demo.btn.next': 'Next case ❯',
    'demo.btn.stop': '✕ Exit demo',
    'demo.label': 'Guided Demonstration',
    'demo.step': 'Case {curr} of {total}',
    'demo.case1.title': 'Piura, Peru — Extreme El Niño Fluctuations',
    'demo.case1.text': 'Notice the immense spikes in precipitation and temperature during the 1982-83 and 1997-98 Super El Niño events. Trend detection requires separating these periodic spikes from the underlying warming signal.',
    'demo.case2.title': 'Arctic (Svalbard) — Accelerated Polar Amplification',
    'demo.case2.text': 'The Arctic is warming at over three times the global rate. The Sen slope shows a decisive upward trajectory, confirmed as statistically significant with p < 0.001.',
    'demo.case3.title': 'Aral Sea (Central Asia) — Historic Inland Lake Desiccation',
    'demo.case3.text': 'Once one of the four largest lakes in the world, the Aral Sea shows marked loss in surface water elevation and soil moisture across decades of environmental transformation.',
    'demo.case4.title': 'Cordillera Blanca, Peru — High-Altitude Tropical Glaciers',
    'demo.case4.text': 'High-altitude tropical glaciers are natural climate sentinels. Warming at 4,000+ meters accelerates ice mass loss even when annual precipitation remains highly variable.',



  },

  es: {
    'app.title': 'EarthTrend Detective',
    'app.tagline': 'Investiga un lugar del planeta con datos reales de ciencias de la Tierra de la NASA.',
    'lang.label': 'Idioma',
    'nav.skip': 'Ir a los resultados',

    'panel.location': 'Lugar',
    'panel.search.label': 'Buscar un lugar',
    'panel.search.placeholder': 'p. ej. Piura, Perú',
    'panel.search.button': 'Buscar',
    'panel.search.noResults': 'Ningún lugar coincide con ese nombre. Prueba con una ciudad o una región.',
    'panel.map.hint': 'Haz clic en el mapa para elegir un punto. Mantén Mayús y arrastra para elegir una caja.',
    'panel.map.attribution': 'Mapa base',

    'panel.variable': 'Variable',
    'panel.variable.learn': 'Qué mide',
    'panel.period': 'Periodo',
    'panel.period.from': 'Desde',
    'panel.period.to': 'Hasta',
    'panel.investigate': 'Investigar',
    'panel.investigating': 'Trayendo datos reales…',
    'panel.report': 'Descargar informe',
    'panel.upload.csv': '📁 Subir CSV de Giovanni',

    'results.empty.title': 'Elige un lugar para empezar',
    'results.empty.body': 'Haz clic en el mapa o busca un lugar, elige una variable y pulsa Investigar. Cada número que veas sale de datos de la NASA pedidos para ese punto exacto.',

    'verdict.eyebrow': 'Veredicto',
    'verdict.what': 'Qué cambia',
    'verdict.where': 'Dónde',
    'verdict.howmuch': 'Cuánto por década',
    'verdict.significant': '¿Es significativo?',
    'verdict.years': '¿Cuántos años faltan para estar seguros?',
    'verdict.method': 'Cómo lo sabemos',
    'verdict.provenance': 'De dónde sale esto',

    'verdict.SIGNIFICANT_STRONG': 'Tendencia clara y fuerte',
    'verdict.SIGNIFICANT': 'Tendencia significativa',
    'verdict.SUGGESTIVE': 'Sugerente, aún sin certeza',
    'verdict.NOT_SIGNIFICANT': 'Todavía no se detecta tendencia',
    'verdict.INSUFFICIENT_DATA': 'Faltan datos para responder',

    'ladder.1': 'Faltan datos',
    'ladder.2': 'Sin tendencia detectable',
    'ladder.3': 'Sugerente',
    'ladder.4': 'Significativa',
    'ladder.5': 'Clara y fuerte',

    'measure.ci': 'intervalo de confianza del 95 %',
    'measure.perDecade': 'por década',
    'measure.total': 'en todo el registro',

    'years.available': 'Años de datos disponibles',
    'years.needed': 'Años necesarios para estar seguros',
    'years.enough': 'El registro es lo bastante largo para detectar esta tendencia.',
    'years.more': 'Harían falta unos {n} años más de datos.',

    'chart.monthly': 'Valores mensuales',
    'chart.anomalies': 'Anomalías',
    'chart.annual': 'Medias anuales',
    'chart.note': 'La línea punteada es la pendiente de Sen con su banda de confianza. En la vista de anomalías se quita el ciclo estacional para ver el cambio de fondo.',
    'chart.axis.value': 'Valor',

    'method.tests': 'Pruebas estadísticas',
    'method.test': 'Prueba',
    'method.statistic': 'Estadístico',
    'method.p': 'valor p',
    'method.autocorr': 'Autocorrelación (retardo 1)',
    'method.neff': 'Tamaño de muestra efectivo',
    'method.references': 'Referencias',
    'method.warnings': 'Advertencias',

    'warn.SHORT_RECORD': 'El registro es corto; cuesta separar la tendencia de las oscilaciones naturales.',
    'warn.LOW_COVERAGE': 'Hay meses sin dato.',
    'warn.HIGH_AUTOCORRELATION': 'Los meses están correlacionados entre sí; las pruebas lo corrigen.',
    'warn.SOURCE_SPLICE': 'La serie une dos productos distintos; parte del cambio puede venir del empalme.',
    'warn.TESTS_DISAGREE': 'Las pruebas no coinciden del todo, así que la respuesta es prudente.',
    'warn.REANALYSIS_CAVEAT': 'Es un producto de reanálisis o de modelo, no una medición directa de satélite.',

    'provenance.source': 'Fuente',
    'provenance.underlying': 'Basado en',
    'provenance.resolution': 'Resolución nativa',
    'provenance.retrieved': 'Descargado',
    'provenance.query': 'Consulta exacta',
    'provenance.citation': 'Cita',
    'provenance.warning.fixture': 'Este resultado no viene directamente de un servicio de la NASA. No lo cites.',
    'provenance.warning.upload': 'Resultado calculado a partir de un CSV que subiste.',

    'error.title': 'Datos no disponibles',
    'error.body': 'La interfaz nunca inventa datos. Si el servicio de análisis está caído, aún puedes abrir un caso real congelado.',
    'error.retry': 'Reintentar',
    'error.code': 'Código',

    'cases.title': 'Casos congelados',
    'cases.body': 'Análisis reales guardados con su procedencia.',
    'cases.none': 'Ahora mismo no hay casos congelados disponibles.',

    'glossary.trend': 'Una tendencia es un cambio sostenido en el tiempo, medido como pendiente por década. No dice nada sobre la causa.',
    'glossary.anomaly': 'Una anomalía es la diferencia entre un mes y el promedio de ese mismo mes en todo el registro. Quita el ciclo estacional.',
    'glossary.pvalue': 'El valor p es la probabilidad de ver un patrón así de fuerte si nada estuviera cambiando. Cuanto más pequeño, más probable es que la tendencia sea real.',
    'glossary.significance': 'Significativo significa que el patrón difícilmente sea azar al umbral elegido (5 % por defecto). No equivale a grande ni a importante.',
    'glossary.ci': 'Un intervalo de confianza del 95 % es el rango que contendría la pendiente verdadera en 95 de cada 100 repeticiones de la misma medición.',
    'glossary.autocorrelation': 'La autocorrelación significa que un mes se parece al anterior. Hace que el registro parezca más informativo de lo que es, así que las pruebas lo corrigen.',

    'footer.data': 'Datos: NASA POWER, GISTEMP, NSIDC. Cada cifra mostrada sale del servicio de análisis con su procedencia.',
    'footer.disclaimer': 'No está afiliado ni respaldado por la NASA.',

    'unit.perDecade': 'por década',
    'nav.mode.single': 'Punto individual',
    'nav.mode.trendmap': 'Mapa de tendencias (regional)',
    'nav.mode.compare': 'Comparar dos lugares',
    'trendmap.title': 'Mapa de Tendencias Espaciales',
    'trendmap.legend.sig': 'Celda significativa (FDR q=0.10)',
    'trendmap.legend.share': '{pct} % de celdas muestran tendencia significativa',
    'trendmap.cells': 'Celdas analizadas',
    'trendmap.btn': 'Ver mapa de tendencias de la caja',
    'trendmap.hint': 'Mantén Mayús y arrastra en el mapa para elegir una caja regional, luego pulsa ver mapa.',
    'compare.title': 'Comparar Dos Lugares',
    'compare.placeA': 'Lugar A',
    'compare.placeB': 'Lugar B',
    'compare.btn': 'Comparar lugares',
    'compare.opposite': 'Tendencias opuestas',
    'compare.opposite.yes': '⚡ Se detectan tendencias opuestas entre ambas regiones',
    'compare.opposite.no': 'Dirección de tendencia similar en ambas regiones',
    'compare.diffSig': 'La diferencia entre ambas tendencias es estadísticamente significativa (z = {z}).',
    'detective.title': 'Pregúntale al Detective',
    'detective.placeholder': 'p. ej. ¿Llueve menos en Piura? o ¿Se reduce el hielo del Ártico?',
    'detective.ask': 'Preguntar',
    'detective.planning': 'El detective está planificando tu investigación…',
    'detective.plan.heading': 'Plan de Investigación',
    'detective.plan.intent': 'Voy a investigar {var} en {place}.',
    'detective.plan.run': 'Confirmar e Investigar',
    'detective.scout.btn': '¿Qué investigo aquí?',
    'detective.scout.heading': 'Variables Sugeridas para esta Zona',
    'detective.scout.why': 'Por qué importa aquí',
    'detective.scout.sources': 'Fuentes',
    'detective.explain.title': 'Explicación del Detective',
        'detective.explain.badge.extractive': 'Fragmentos de las fuentes citadas (sin IA generativa)',
    'detective.explain.badge.full': 'Síntesis asistida por IA a partir de las fuentes citadas',
    'verdict.tests_disagree.title': 'Por qué discrepan las pruebas estadísticas',
    'verdict.tests_disagree.body': 'La prueba de Mann-Kendall detecta una dirección persistente, pero el test t de MCO ajustado por autocorrelación y el intervalo de confianza indican que la magnitud de la pendiente aún requiere más tiempo de observación para alcanzar certeza definitiva.',
    'atlas.load.btn': '🌐 Cargar Atlas Global (T2M)',
    'atlas.loading': 'Cargando atlas de cuadrícula global…',
    'variable.global_series': 'Serie global o polar fija (no requiere selección de punto)',

    'detective.explain.level.school': 'Nivel escolar',
    'detective.explain.level.uni': 'Nivel universitario',
    'detective.explain.loading': 'Generando explicación con evidencia citada…',
    'detective.explain.sources': 'Evidencias citadas',
    'demo.btn.start': '▶ Modo Demostración',
    'demo.btn.pause': '⏸ Pausa',
    'demo.btn.resume': '▶ Reanudar',
    'demo.btn.next': 'Siguiente caso ❯',
    'demo.btn.stop': '✕ Salir de demo',
    'demo.label': 'Demostración Guiada',
    'demo.step': 'Caso {curr} de {total}',
    'demo.case1.title': 'Piura, Perú — Fluctuaciones Extremas de El Niño',
    'demo.case1.text': 'Observa los picos masivos de precipitación y temperatura durante los eventos de El Niño 1982-83 y 1997-98. La detección de tendencias requiere aislar estas oscilaciones periódicas de la señal de fondo.',
    'demo.case2.title': 'Ártico (Svalbard) — Amplificación Polar Acelerada',
    'demo.case2.text': 'El Ártico se calienta a más de tres veces el promedio global. La pendiente de Sen confirma una trayectoria ascendente decidida y estadísticamente significativa (p < 0.001).',
    'demo.case3.title': 'Mar de Aral (Asia Central) — Desecación de un Gran Lago',
    'demo.case3.text': 'El Mar de Aral muestra una pérdida continua y persistente de elevación de agua y humedad de suelo a lo largo de cuatro décadas de transformación ambiental.',
    'demo.case4.title': 'Cordillera Blanca, Perú — Glaciares Tropicales de Alta Montaña',
    'demo.case4.text': 'Los glaciares tropicales de altura son centinelas climáticos. El calentamiento sostenido a más de 4.000 metros acelera el retroceso glaciar incluso con alta variabilidad estacional.',



  },
};

function detectLang() {
  // English is strictly the default for the judged submission (Ronda 3, Rule 16).
  try {
    const saved = localStorage.getItem('etd.lang');
    if (saved === 'es') return 'es';
  } catch (_) {}
  return 'en';
}

function translate(key, vars) {
  const table = STRINGS[window.__etdLang] || STRINGS.en;
  let s = table[key];
  if (s === undefined) s = STRINGS.en[key];
  if (s === undefined) return key;
  if (vars) {
    for (const k of Object.keys(vars)) s = s.replaceAll(`{${k}}`, String(vars[k]));
  }
  return s;
}

function applyTranslations(root) {
  const scope = root || document;
  scope.querySelectorAll('[data-i18n]').forEach((el) => {
    el.textContent = translate(el.getAttribute('data-i18n'));
  });
  scope.querySelectorAll('[data-i18n-placeholder]').forEach((el) => {
    el.setAttribute('placeholder', translate(el.getAttribute('data-i18n-placeholder')));
  });
  scope.querySelectorAll('[data-i18n-aria]').forEach((el) => {
    el.setAttribute('aria-label', translate(el.getAttribute('data-i18n-aria')));
  });
  scope.querySelectorAll('[data-i18n-title]').forEach((el) => {
    el.setAttribute('title', translate(el.getAttribute('data-i18n-title')));
  });
  document.documentElement.lang = window.__etdLang || 'en';
}

window.__etdLang = detectLang();
window.__etdI18n = { STRINGS, t: translate, applyTranslations, detectLang };

})();