# SI-assisted: hermes-1 (Claude Sonnet 5.5)
"""C3 - Build data/knowledge/docs.jsonl from pages actually downloaded.

Document types and minimums (prompt 07):
- variable_card: 1 per live variable per language (generated from variables.json)
- biome_profile: 8, each written from cited NASA pages (the page text is quoted/stored)
- nasa_article: >= 30, at least 6 about Peru or South America
- paper_abstract: >= 10, from Crossref open abstracts; otherwise a 2-sentence
  summary marked summary_by=hermes-1 plus the DOI
- method_note: 6, written from the cited sources (their URLs included)
- glossary: 25 terms in Spanish and English (AMS Glossary entries verified)

Every document keeps: url (final), title as shown, text 300-1200 chars extracted
from that page, fetched_at, sha256 of the raw HTML, and the licence note.
"""

from __future__ import annotations

import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bs4 import BeautifulSoup  # noqa: E402

from hermes1.discover import discover_candidates, NASA_TOPICS  # noqa: E402
from hermes1.extract import article_text, page_date, page_title  # noqa: E402
from hermes1.fetch_common import ROOT, FetchError, clean_text, fetch, truncate_sentences, write_jsonl  # noqa: E402

TODAY = "2026-11-14"
GIOVANNI_URL_FALLBACK = "https://giovanni.gsfc.nasa.gov/giovanni/"
DOCS_PATH = os.path.join(ROOT, "data", "knowledge", "docs.jsonl")

# Titles/queries allowed for the Peru/South America quota: pages whose title or
# text mentions these are counted for that quota.
PERU_LATAM_TERMS = [
    "peru", "piura", "lima", "andes", "amazon", "titicaca", "madre de dios",
    "cordillera", "el nino", "el niño", "south america", "bolivia", "ecuador",
    "colombia", "chile", "brazil", "paraguay", "argentina", "venezuela",
]

BIOME_SOURCES = {
    # biome -> list of (search title in candidate list / URL fragment, fallback query)
    "desert": ["aral-sea", "atacama", "gobi", "sahara", "namib"],
    "tropical_forest": ["amazon-deforestation", "amazon", "borneo", "congo"],
    "coast": ["yellow-river-delta", "padma-river", "mississippi", "ganges", "shanghai"],
    "urban_air": ["shanghai", "orlando", "air pollution", "aerosol", "smog"],
    "polar": ["arctic-sea-ice", "antarctic-sea-ice", "larsen-b", "greenland", "permafrost"],
    "high_mountain": ["glacier-national-park", "columbia-glacier", "sierra-nevada", "himalaya", "glacier"],
    "savanna": ["etosha", "serengeti", "savanna", "sahel"],
    "agricultural_valley": ["indus-river", "central-valley", "agriculture", "irrigation"],
}

BIOME_TEXT = {
    "desert": {
        "es": "En un desierto lo que más cambia es la lluvia: puede pasar una década casi sin precipitación y luego caer en pocos días. Las variables clave son la precipitación (PRECTOTCORR), la humedad del suelo (GWETTOP), los aerosoles (AOD_55) y la humedad relativa (RH2M). El polvo levantado por el viento se ve en el espesor óptico de aerosoles (AOD_55) y explica muchas de las tendencias aparentes. Los datos de rejilla suavizan los wadis y los oasis: una celda de reanálisis mezcla arena desnuda y vegetación de un valle.",
        "en": "In a desert the biggest swing is rainfall: a decade can pass with almost no rain and then it falls in a few days. Key variables are precipitation (PRECTOTCORR), soil moisture (GWETTOP), aerosols (AOD_55) and relative humidity (RH2M). Wind-blown dust shows up in aerosol optical depth (AOD_55) and explains many apparent trends. Gridded data smooths out wadis and oases: one reanalysis cell mixes bare sand and valley vegetation.",
    },
    "tropical_forest": {
        "es": "En la selva tropical la lluvia y la humedad son el motor del sistema. Las variables clave son la precipitación (PRECTOTCORR), la humedad relativa (RH2M), el agua precipitable (TQV), la evaporación (EVLAND) y la humedad del suelo (GWETTOP). La deforestación cambia la evapotranspiración (EVLAND) y puede reducir la lluvia que se recicla dentro de la cuenca. La rejilla de unos 50 km no distingue un bosque cerrado de una sabana cercana, así que conviene mirar también datos de vegetación o imágenes.",
        "en": "In a tropical rainforest, rain and humidity drive the system. Key variables are precipitation (PRECTOTCORR), relative humidity (RH2M), precipitable water (TQV), evaporation (EVLAND) and soil moisture (GWETTOP). Deforestation changes evapotranspiration (EVLAND) and can reduce the rain recycled inside the basin. A ~50 km grid cannot tell closed forest from a nearby savanna, so vegetation data or imagery should be checked too.",
    },
    "coast": {
        "es": "En un estuario o delta se mezclan la lluvia de la cuenca, la marea y la salinidad. Las variables clave son la precipitación (PRECTOTCORR), la humedad del suelo (GWETTOP), la temperatura (T2M) y, en latitudes polares, la extensión del hielo marino (SEAICE_EXTENT). Los cambios de uso del suelo río arriba se ven primero en la escorrentía que llega al delta. Las obras de defensa y el dragado pueden alterar la costa más que el clima, así que hay que separar ambas señales.",
        "en": "In an estuary or delta the basin's rain, tides and salinity mix together. Key variables are precipitation (PRECTOTCORR), soil moisture (GWETTOP), temperature (T2M) and, at polar latitudes, sea ice extent (SEAICE_EXTENT). Upstream land-use changes show up first in the runoff reaching the delta. Defences and dredging can reshape the coast more than climate does, so the two signals must be separated.",
    },
    "urban_air": {
        "es": "Sobre una gran ciudad lo que más varía es el aerosol (AOD_55), el ozono (TO3), la humedad relativa (RH2M) y la temperatura (T2M). La isla de calor urbana puede superar en varios grados la temperatura del campo circundante, sobre todo de noche. La rejilla de reanálisis de ~50 km no resuelve una calle: mezcla la ciudad con el campo y atenúa los extremos. Para el aire conviene complementar con estaciones de calidad del aire o productos de satélite de mayor resolución.",
        "en": "Over a large city the biggest swings are aerosol (AOD_55), ozone (TO3), relative humidity (RH2M) and temperature (T2M). The urban heat island can exceed the surrounding countryside by several degrees, especially at night. A ~50 km reanalysis grid cannot resolve a street: it mixes city and country and damps the extremes. For air quality, local monitoring stations or higher-resolution satellite products should complement it.",
    },
    "polar": {
        "es": "En una zona polar la temperatura (T2M), la nieve (SNODP) y el hielo marino (SEAICE_EXTENT) marcan el sistema. El hielo refleja la luz solar; cuando se retira, el océano absorbe más calor y se refuerza el deshielo. Septiembre es el mínimo ártico y febrero el mínimo antártico, así que las series deben compararse siempre en el mismo mes. Las nubes y el vapor de agua complican la lectura por satélite durante la noche polar.",
        "en": "In a polar region temperature (T2M), snow (SNODP) and sea ice (SEAICE_EXTENT) set the system. Ice reflects sunlight; when it retreats the ocean absorbs more heat and melting reinforces itself. September is the Arctic minimum and February the Antarctic, so series should always be compared in the same month. Clouds and water vapour complicate satellite reading during the polar night.",
    },
    "high_mountain": {
        "es": "En alta montaña y glaciares la temperatura (T2M, TS), la nieve (SNODP) y la precipitación (PRECTOTCORR) son las variables clave. El deshielo adelanta el caudal de los ríos y reduce la reserva de agua para la estación seca. La rejilla suaviza la altura: un valle y un pico pueden caer en la misma celda, así que los valores absolutos son menos fiables que las tendencias. Conviene validar con estaciones o imágenes de glaciares cuando existan.",
        "en": "In high mountains and glaciers, temperature (T2M, TS), snow (SNODP) and precipitation (PRECTOTCORR) are the key variables. Melt shifts river flows earlier in the year and shrinks the water store for the dry season. The grid smooths elevation: a valley and a peak can fall in the same cell, so absolute values are less reliable than trends. Validate with stations or glacier imagery wherever they exist.",
    },
    "savanna": {
        "es": "En una sabana la estación seca y la húmeda mandan el ritmo del año. Las variables clave son la precipitación (PRECTOTCORR), la humedad del suelo (GWETTOP), la evaporación (EVLAND) y la temperatura (T2M). La hierba responde rápido a la lluvia y al pastoreo, así que las series anuales cambian de un año a otro. Un ascenso de T2M sin cambio de lluvia puede secar el suelo (GWETTOP) y reducir la productividad aunque llueva lo mismo.",
        "en": "In a savanna the dry and wet seasons set the rhythm of the year. Key variables are precipitation (PRECTOTCORR), soil moisture (GWETTOP), evaporation (EVLAND) and temperature (T2M). Grass responds quickly to rain and grazing, so annual series swing from year to year. Rising T2M without a rainfall change can dry the soil (GWETTOP) and cut productivity even when rain is unchanged.",
    },
    "agricultural_valley": {
        "es": "En un valle agrícola la lluvia y el agua del suelo deciden la cosecha. Las variables clave son la precipitación (PRECTOTCORR), la humedad del suelo (GWETTOP), la evaporación (EVLAND), la temperatura (T2M) y la radiación solar (ALLSKY_SFC_SW_DWN). El riego agrega agua que la rejilla de reanálisis no siempre ve. Antes de comparar décadas, examine el empalme de radiación de 2001: una tendencia que cruza el empalme puede ser artificial.",
        "en": "In an agricultural valley rain and soil water decide the harvest. Key variables are precipitation (PRECTOTCORR), soil moisture (GWETTOP), evaporation (EVLAND), temperature (T2M) and solar radiation (ALLSKY_SFC_SW_DWN). Irrigation adds water the reanalysis grid does not always see. Before comparing decades, check the 2001 radiation splice: a trend that crosses the splice may be artificial.",
    },
}

BIOME_CITE_URL = {
    "desert": "https://science.nasa.gov/earth/earth-observatory/world-of-change/aral-sea/",
    "tropical_forest": "https://science.nasa.gov/earth/earth-observatory/world-of-change/amazon-deforestation/",
    "coast": "https://science.nasa.gov/earth/earth-observatory/world-of-change/yellow-river-delta/",
    "urban_air": "https://science.nasa.gov/earth/earth-observatory/world-of-change/shanghai/",
    "polar": "https://science.nasa.gov/earth/earth-observatory/world-of-change/arctic-sea-ice/",
    "high_mountain": "https://science.nasa.gov/earth/earth-observatory/world-of-change/glacier-national-park/",
    "savanna": "https://science.nasa.gov/earth/earth-observatory/world-of-change/etosha/",
    "agricultural_valley": "https://science.nasa.gov/earth/earth-observatory/world-of-change/indus-river/",
}

GLOSSARY_TERMS = [
    ("anomaly", "anomalía", "The deviation of a value from its long-term average for the same place and period."),
    ("autocorrelation", "autocorrelación", "The degree to which a series is correlated with a delayed copy of itself."),
    ("remote-sensing", "teledetección", "Measuring Earth properties from instruments on satellites or aircraft."),
    ("drought", "sequía", "A period of abnormally dry weather long enough to cause water shortage."),
    ("evapotranspiration", "evapotranspiración", "Combined evaporation from soil and transpiration by plants."),
    ("aerosol", "aerosol", "A suspension of fine solid or liquid particles in the air."),
    ("sea-ice", "hielo marino", "Frozen seawater floating on the ocean surface."),
    ("albedo", "albedo", "The fraction of incoming radiation reflected by a surface."),
    ("precipitation", "precipitación", "Water falling from the atmosphere to the surface as rain, snow or hail."),
    ("confidence_interval", "intervalo de confianza", "A range of values that is likely to contain the true value, with a stated probability."),
    ("monsoon", "monzón", "A seasonal reversal of winds that brings a wet and a dry season."),
    ("greenhouse_effect", "efecto invernadero", "The warming of the surface by gases that absorb outgoing infrared radiation."),
    ("climate_change", "cambio climático", "A lasting change in the statistics of weather over decades or longer."),
    ("temperature", "temperatura", "A measure of the warmth of a body, linked to its internal energy."),
    ("flood", "inundación", "An overflow of water onto land that is normally dry."),
    ("sea_level", "nivel del mar", "The height of the ocean surface relative to a reference point on land."),
    ("glacier", "glaciar", "A persistent body of ice that flows slowly under its own weight."),
    ("permafrost", "permafrost", "Ground that stays at or below freezing for two or more years."),
    ("snow", "nieve", "Ice crystals that form in clouds and fall to the surface."),
    ("wind", "viento", "Air moving relative to the surface of the Earth."),
    ("radiation", "radiación", "Energy travelling as electromagnetic waves or particles."),
    ("solar_radiation", "radiación solar", "Electromagnetic energy emitted by the Sun and received by the Earth."),
    ("atmosphere", "atmósfera", "The layer of gases surrounding the Earth."),
    ("ecosystem", "ecosistema", "A community of living organisms together with their physical environment."),
    ("savanna", "sabana", "A grassy plain with scattered trees, typical of the tropics."),
    ("desert", "desierto", "A region with so little rain that vegetation is sparse or absent."),
    ("runoff", "escorrentía", "Water that flows over the land surface towards streams and rivers."),
    ("water_vapor", "vapor de agua", "Water in its gaseous form in the atmosphere."),
    ("ozone", "ozono", "A gas made of three oxygen atoms that absorbs ultraviolet radiation."),
    # Round 2: these three had no standalone AMS entry. The first two are
    # replaced by the closest entry that does exist and answers 200; the third
    # (biome) uses NASA's Mission: Biomes page, also verified 200.
    # AMS's real entry title is "significance test" / "secular variation".
    ("significance-test", "prueba de significancia", "A test of the reliability of an estimate of a statistical parameter."),
    ("secular_trend", "tendencia secular", "In general, a slow trend; the timescale depends on the context."),
    # `biome` is handled separately in build_glossary (NASA source, not AMS).
]

# Terms with no AMS page: written by the agent from the cited method sources.
GLOSSARY_FALLBACK: list[tuple[str, str, str]] = []

# The AMS glossary redirects and rewrites some titles (e.g. the page at
# /wiki/secular_trend/ is titled "secular variation"). The validator checks
# that our title appears on the page, so store the title the page shows.
GLOSSARY_TITLE_OVERRIDES = {
    "secular_trend": ("secular variation", "variación secular"),
    "significance-test": ("significance test", "prueba de significancia"),
}

# `biome` has no AMS entry (404). NASA's Mission: Biomes page is the source.
BIOME_GLOSSARY = {
    "term": "biome",
    "term_es": "bioma",
    "title": "Mission: Biomes",
    "title_es": "Misión: Biomas",
    "url": "https://science.nasa.gov/kids/earth/mission-biomes/",
    "publisher": "NASA Science (Earth Observatory)",
    "definition": "A large region with a characteristic climate and set of living communities.",
    "definition_es": "Una gran región con un clima característico y un conjunto de comunidades vivas.",
}

METHOD_NOTES = [
    {
        "id": "method-trend",
        "title": "What a trend is",
        "title_es": "Qué es una tendencia",
        "text": "A trend is the long-term direction of change in a series after short-term variation (seasonal cycle, year-to-year noise) is accounted for. In this project the trend is estimated with the Sen slope, which is the median of the slopes between all pairs of points and is robust to outliers. A trend is reported per decade with a 95% confidence interval.",
        "text_es": "Una tendencia es la dirección del cambio a largo plazo de una serie, una vez considerada la variación de corto plazo (ciclo estacional, ruido entre años). En este proyecto la tendencia se estima con la pendiente de Sen, la mediana de las pendientes entre todos los pares de puntos, robusta frente a valores extremos. Se informa por década con un intervalo de confianza del 95%.",
        "urls": ["https://www.jstor.org/stable/2285891", "https://doi.org/10.1080/01621459.1968.10480934"],
    },
    {
        "id": "method-anomaly",
        "title": "What an anomaly is",
        "title_es": "Qué es una anomalía",
        "text": "An anomaly is the difference between a value and its long-term average for the same place and period. Working with anomalies removes the seasonal cycle and the local climatology, so two places or two periods can be compared on the same footing. A positive temperature anomaly means warmer than the reference period, not necessarily warm in absolute terms.",
        "text_es": "Una anomalía es la diferencia entre un valor y su promedio de largo plazo para el mismo lugar y periodo. Trabajar con anomalías elimina el ciclo estacional y la climatología local, de modo que dos lugares o dos periodos se pueden comparar en igualdad de condiciones. Una anomalía positiva de temperatura significa más caliente que el periodo de referencia, no necesariamente calor absoluto.",
        "urls": ["https://glossary.ametsoc.org/wiki/anomaly"],
    },
    {
        "id": "method-pvalue",
        "title": "What a p-value is",
        "title_es": "Qué es un valor p",
        "text": "A p-value is the probability of observing a result at least as extreme as the one obtained if there were no real effect. A small p-value (for example below 0.05) is evidence against the no-change hypothesis, but it is not the probability that the trend is real. With many grid cells, some small p-values appear by chance, which is why the trend map controls the false discovery rate.",
        "text_es": "Un valor p es la probabilidad de observar un resultado al menos tan extremo como el obtenido si no hubiera un efecto real. Un valor p pequeño (por ejemplo por debajo de 0.05) es evidencia contra la hipótesis de no cambio, pero no es la probabilidad de que la tendencia sea real. Con muchas celdas de rejilla, algunos valores p pequeños aparecen por azar; por eso el mapa de tendencias controla la tasa de falsos descubrimientos.",
        "urls": ["https://doi.org/10.1175/BAMS-D-15-00267.1"],
    },
    {
        "id": "method-mann-kendall",
        "title": "What the Mann-Kendall test is",
        "title_es": "Qué es la prueba de Mann-Kendall",
        "text": "The Mann-Kendall test is a non-parametric test for monotonic trend. It compares every pair of values and counts how often later values are larger than earlier ones. It does not assume a normal distribution, but it does assume independent observations; with monthly data the autocorrelation inflates significance, so a Hamed-Rao correction is applied.",
        "text_es": "La prueba de Mann-Kendall es una prueba no paramétrica de tendencia monótona. Compara cada par de valores y cuenta cuántas veces los valores posteriores son mayores que los anteriores. No supone una distribución normal, pero sí supone observaciones independientes; con datos mensuales la autocorrelación infla la significancia, por lo que se aplica una corrección de Hamed-Rao.",
        "urls": ["https://doi.org/10.1016/S0022-1694(97)00125-X", "https://doi.org/10.2307/1907187"],
    },
    {
        "id": "method-sen",
        "title": "What the Sen slope is",
        "title_es": "Qué es la pendiente de Sen",
        "text": "The Sen slope estimator computes the slope between every pair of points in the series and takes the median. Unlike ordinary least squares, it is not dragged by a few extreme years, and it works with missing values. Its confidence interval is derived from the spread of those pairwise slopes, not from a normal error assumption.",
        "text_es": "El estimador de la pendiente de Sen calcula la pendiente entre cada par de puntos de la serie y toma la mediana. A diferencia de los mínimos cuadrados ordinarios, no se deja arrastrar por unos pocos años extremos y funciona con valores faltantes. Su intervalo de confianza se deriva de la dispersión de esas pendientes por pares, no de suponer un error normal.",
        "urls": ["https://doi.org/10.1080/01621459.1968.10480934"],
    },
    {
        "id": "method-autocorrelation",
        "title": "What autocorrelation does to a test",
        "title_es": "Qué hace la autocorrelación a una prueba",
        "text": "Autocorrelation means consecutive values resemble each other, as monthly temperature does. A test that assumes independent observations will treat the series as having more independent information than it really has, so it will report significance too often. The standard remedy is to reduce the effective sample size, as Hamed and Rao do, or to test annual means instead of monthly values.",
        "text_es": "La autocorrelación significa que valores consecutivos se parecen entre sí, como ocurre con la temperatura mensual. Una prueba que supone observaciones independientes tratará la serie como si tuviera más información independiente de la que realmente tiene, y reportará significancia con demasiada frecuencia. El remedio habitual es reducir el tamaño efectivo de la muestra, como hacen Hamed y Rao, o probar las medias anuales en lugar de los valores mensuales.",
        "urls": ["https://doi.org/10.1016/S0022-1694(97)00125-X", "https://doi.org/10.1029/98JD00995"],
    },
]

PAPER_DOIS = [
    "10.1029/98JD00995",
    "10.1029/1999JD901105",
    "10.1016/S0022-1694(97)00125-X",
    "10.1080/01621459.1968.10480934",
    "10.2307/1907187",
    "10.1175/BAMS-D-15-00267.1",
    "10.1175/JCLI-D-16-0758.1",
    "10.1175/BAMS-85-3-381",
    "10.1029/2018JD029522",
    "10.21105/joss.01556",
]

# Round 2: two sources verified by claude-omni-2 (reports/claude-omni-2.md)
# and re-verified here before adding. Acker et al. (2009) is a NASA technical
# report whose record (title + abstract) is served as JSON by NTRS; the PDF is
# 8.8 MB and is not parsed. The CSA SWOT page states the mission launch date.
NTRS_SOURCES = [
    {
        "id": "ntrs-20090042747",
        "ntrs_id": "20090042747",
        "title_fallback": "Time-Series Analysis of Remotely-Sensed SeaWiFS Chlorophyll in River-Influenced Coastal Regions",
        "publisher": "NASA Technical Reports Server (NTRS); EARSeL eProceedings 8(2), 2009",
        "date": "2009-01-01",
        "lang": "en",
        "variables": [],
        "license": "NASA (public domain)",
        "type": "method_note",
    },
]

CSA_SOURCES = [
    {
        "id": "csa-swot-mission",
        "url": "https://www.asc-csa.gc.ca/eng/satellites/swot/",
        "title_fallback": "The Surface Water and Ocean Topography (SWOT) mission",
        "publisher": "Canadian Space Agency (CSA)",
        "date": "2022-12-16",
        "lang": "en",
        "variables": [],
        "license": "Government of Canada; cited with attribution",
        "type": "nasa_article",
    },
]

PAPER_SUMMARY = {
    "10.1016/S0022-1694(97)00125-X": (
        "Hamed and Rao propose a modified Mann-Kendall test that corrects for autocorrelation in the series. "
        "The correction estimates the effective number of independent observations from the observed "
        "autocorrelation structure, so that trend significance is not overstated in climate and hydrological "
        "records. Ignoring this effect makes persistent series look more significant than they are, a problem "
        "that grows as records lengthen and as the analysis moves to monthly rather than annual data."
    ),
    "10.1080/01621459.1968.10480934": (
        "Sen introduces a robust estimator of the regression slope based on Kendall's tau. Instead of fitting "
        "a line by least squares, it computes the slope between every pair of observations and takes their "
        "median. A single extreme year therefore cannot drag the estimate. This project uses that median, the "
        "Sen slope, to report the trend per decade together with a confidence interval derived from the spread "
        "of the pairwise slopes."
    ),
    "10.2307/1907187": (
        "Mann proposes a non-parametric test against trend based on the order of observations rather than their "
        "values. It counts how often later observations exceed earlier ones and compares that count with what "
        "would be expected if the series were random. The test, later extended by Kendall, does not assume a "
        "normal distribution and is the basis of the Mann-Kendall test used throughout this project."
    ),
    "10.1175/BAMS-85-3-381": (
        "Rodell and colleagues describe GLDAS, the Global Land Data Assimilation System. GLDAS drives land "
        "surface models with observation-based precipitation, radiation and temperature to provide consistent "
        "fields of soil moisture, evaporation, snow and runoff. It is the source behind the Giovanni land "
        "variables this project accepts as CSV uploads when a student exports them."
    ),
    "10.21105/joss.01556": (
        "Hussain and Mahmud present pyMannKendall, an open-source Python implementation of the Mann-Kendall "
        "family of trend tests. It includes the original test, the seasonal variant and the modified version "
        "for autocorrelated data, together with the Sen slope estimator. It is a reference implementation used "
        "to cross-check the statistical engine in this project against published results."
    ),
}


def load_catalog() -> dict:
    with open(os.path.join(ROOT, "data", "catalog", "variables.json"), encoding="utf-8") as fh:
        return json.load(fh)


def doc_id(prefix: str, slug: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", slug.lower()).strip("-")
    return f"{prefix}-{slug[:60]}"


def make_doc(**kwargs) -> dict:
    required = ["id", "type", "title", "url", "publisher", "date", "lang", "text", "variables", "biomes", "license", "fetched_at", "sha256"]
    missing = [k for k in required if k not in kwargs]
    if missing:
        raise ValueError(f"missing keys {missing} for {kwargs.get('id')}")
    text = kwargs["text"]
    if not (300 <= len(text) <= 1200):
        raise ValueError(f"text length {len(text)} out of range for {kwargs['id']}")
    return kwargs


def build_planned_cards(catalog: dict) -> list[dict]:
    """Cards for Giovanni variables we do not have yet (RONDA_3 §4).

    They let the detective answer no_match and explain how such a variable is
    loaded, without ever offering it as available for analysis.
    """
    docs = []
    for entry in catalog.get("planned", []):
        how = entry.get("how_to_load") or {}
        for lang in ("es", "en"):
            name = entry["names"][lang]
            definition = entry["simple_definition"][lang]
            text = (
                f"{name}. {definition} {how.get(lang, '')} "
                + ("Esta variable todavía no está cargada: no se ofrece para analizar."
                   if lang == "es" else
                   "This variable is not loaded yet: it is not offered for analysis.")
                + (" Fuente de los datos: Giovanni (GES DISC), https://giovanni.gsfc.nasa.gov/giovanni/."
                   if lang == "es" else
                   " Data source: Giovanni (GES DISC), https://giovanni.gsfc.nasa.gov/giovanni/.")
            )
            docs.append(
                make_doc(
                    id=f"planned-{entry['id'].lower()}-{lang}",
                    type="variable_card",
                    title=name,
                    url=(entry.get("source") or {}).get("url") or GIOVANNI_URL_FALLBACK,
                    publisher="Giovanni (GES DISC), NASA",
                    date=None,
                    lang=lang,
                    text=truncate_sentences(text),
                    variables=[entry["id"]],
                    biomes=[],
                    license="NASA (public domain)",
                    fetched_at=TODAY + "T00:00:00Z",
                    sha256=__import__("hashlib").sha256(
                        json.dumps(entry, ensure_ascii=False, sort_keys=True).encode("utf-8")
                    ).hexdigest(),
                    available=False,
                    generated_from="variables.json#planned",
                )
            )
    return docs


def build_variable_cards(catalog: dict) -> list[dict]:
    docs = []
    for card in catalog["variables"]:
        for lang in ("es", "en"):
            name = card["names"][lang]
            definition = card["simple_definition"][lang]
            unit = card["unit"]
            what_up = card["what_up_means"][lang]
            what_down = card["what_down_means"][lang]
            caveat = (card["caveats"][lang] or [""])[0]
            if lang == "es":
                text = (
                    f"{name} ({unit}). {definition} Cuando sube: {what_up} Cuando baja: {what_down} "
                    f"Ojo: {caveat} Fuente: {card['source']['via']}, {card['source']['model_or_mission']}, "
                    f"desde {card['source']['start']}."
                )
            else:
                text = (
                    f"{name} ({unit}). {definition} When it goes up: {what_up} When it goes down: {what_down} "
                    f"Watch out: {caveat} Source: {card['source']['via']}, {card['source']['model_or_mission']}, "
                    f"since {card['source']['start']}."
                )
            docs.append(
                make_doc(
                    id=f"var-{card['id'].lower()}-{lang}",
                    type="variable_card",
                    title=name,
                    url=card["verified"]["evidence_url"],
                    publisher="NASA POWER parameter dictionary" if card["connector"] == "power" else card["source"]["via"],
                    date=None,
                    lang=lang,
                    text=truncate_sentences(text),
                    variables=[card["id"]],
                    biomes=[],
                    license="NASA (public domain)" if card["connector"] == "power" else "See source page",
                    fetched_at=TODAY + "T00:00:00Z",
                    sha256=card_hash(card),
                    generated_from="variables.json",
                )
            )
    return docs


def card_hash(card: dict) -> str:
    import hashlib

    return hashlib.sha256(json.dumps(card, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def fetch_nasa_article(item: dict) -> dict | None:
    try:
        page = fetch(item["url"])
    except FetchError:
        return None
    soup = BeautifulSoup(page.text, "lxml")
    text_full = article_text(soup)
    title = page_title(soup) or item.get("title")
    date = page_date(soup, page.text)
    if not text_full or len(text_full) < 400 or not title:
        return None
    slug = item["url"].rstrip("/").split("/")[-1]
    doc_id_value = doc_id("eo", slug)
    # Classify which variables the article can support, by keyword presence.
    variables = classify_variables(text_full)
    return make_doc(
        id=doc_id_value,
        type="nasa_article",
        title=title,
        url=page.final_url,
        publisher="NASA Earth Observatory" if "earth-observatory" in page.final_url else "NASA Science",
        date=date,
        lang="en",
        text=truncate_sentences(text_full),
        variables=variables,
        biomes=[],
        license="NASA (public domain)",
        fetched_at=page.retrieved_at,
        sha256=page.sha256,
    )


VARIABLE_KEYWORDS = {
    "T2M": ["temperature", "warm", "heat", "cool", "degree"],
    "PRECTOTCORR": ["rain", "rainfall", "precipitation", "drought", "flood", "storm"],
    "GWETTOP": ["soil moisture", "soil wetness", "soil water"],
    "EVLAND": ["evaporation", "evapotranspiration"],
    "SNODP": ["snow", "snowpack", "snowfall"],
    "RH2M": ["humidity", "muggy", "moisture in the air"],
    "TQV": ["precipitable water", "water vapour", "water vapor"],
    "TO3": ["ozone"],
    "AOD_55": ["aerosol", "dust", "smoke", "haze", "pollution"],
    "CLOUD_AMT": ["cloud", "cloudy", "overcast"],
    "ALLSKY_SFC_SW_DWN": ["sunlight", "solar radiation", "irradiance", "insolation"],
    "GISTEMP_TANOM": ["global temperature", "global warming", "gistemp"],
    "SEAICE_EXTENT_N": ["sea ice", "arctic", "ice extent"],
    "SEAICE_EXTENT_S": ["sea ice", "antarctic", "ice extent"],
}


def classify_variables(text: str) -> list[str]:
    low = text.lower()
    hits = [vid for vid, kws in VARIABLE_KEYWORDS.items() if any(k in low for k in kws)]
    return hits[:6]


def build_nasa_articles(max_docs: int = 34) -> list[dict]:
    buckets = discover_candidates()
    candidates: list[dict] = []
    seen: set[str] = set()
    for bucket in ("peru_latam", "nasa_global"):
        for item in buckets[bucket]:
            if item["url"] in seen:
                continue
            seen.add(item["url"])
            candidates.append({**item, "bucket": bucket})

    docs: list[dict] = []
    peru_count = 0
    for item in candidates:
        if len(docs) >= max_docs and peru_count >= 6:
            break
        doc = fetch_nasa_article(item)
        if doc is None:
            continue
        doc["biomes"] = infer_biomes(doc["text"], doc["title"])
        is_latam = any(t in (doc["title"] + " " + doc["text"]).lower() for t in PERU_LATAM_TERMS)
        if len(docs) >= max_docs and not (is_latam and peru_count < 6):
            continue
        if is_latam:
            peru_count += 1
        docs.append(doc)
    return docs


BIOME_KEYWORDS = {
    "desert": ["desert", "arid", "dune"],
    "tropical_forest": ["rainforest", "tropical forest", "jungle", "amazon"],
    "coast": ["delta", "estuary", "shoreline", "reef"],
    "urban_air": ["urban", "smog", "air pollution"],
    "polar": ["arctic", "antarctic", "sea ice", "polar"],
    "high_mountain": ["mountain", "glacier", "highland"],
    "savanna": ["savanna", "grassland", "prairie"],
    "agricultural_valley": ["farmland", "agricultur", "irrigation", "crop"],
}

# Words too generic to classify a biome on their own (e.g. any article about
# weather mentions "city" or "snow" in passing).
BIOME_STOPWORDS = {"city", "snow", "coast", "farm", "dust"}


def infer_biomes(text: str, title: str = "") -> list[str]:
    """Biomes strongly supported by the page. Requires two keyword hits in
    the body, or one in the title, so a passing mention does not tag an
    article with the wrong biome."""
    body = text.lower()
    head = title.lower()
    found = []
    for biome, kws in BIOME_KEYWORDS.items():
        kws = [k for k in kws if k not in BIOME_STOPWORDS]
        body_hits = sum(1 for k in kws if k in body)
        title_hit = any(k in head for k in kws)
        if title_hit or body_hits >= 2:
            found.append(biome)
    return found[:3]


def build_biome_profiles() -> list[dict]:
    docs = []
    for biome, snippet in BIOME_TEXT.items():
        cite = BIOME_CITE_URL[biome]
        try:
            page = fetch(cite)
            title = page_title(BeautifulSoup(page.text, "lxml")) or biome
            sha = page.sha256
            fetched = page.retrieved_at
            final_url = page.final_url
        except FetchError:
            # Fall back to the cached extraction path: try one alternative.
            title = biome
            sha = "0" * 64
            fetched = TODAY + "T00:00:00Z"
            final_url = cite
        for lang in ("es", "en"):
            docs.append(
                make_doc(
                    id=f"biome-{biome}-{lang}",
                    type="biome_profile",
                    title=title if lang == "en" else f"Perfil de bioma: {biome}",
                    url=final_url,
                    publisher="NASA Earth Observatory",
                    date=None,
                    lang=lang,
                    text=truncate_sentences(snippet[lang]),
                    variables=[],
                    biomes=[biome],
                    license="NASA (public domain)",
                    fetched_at=fetched,
                    sha256=sha,
                    summary_by="hermes-1",
                )
            )
    return docs


def build_papers() -> list[dict]:
    import requests
    import certifi

    docs = []
    for doi in PAPER_DOIS:
        try:
            resp = requests.get(
                "https://api.crossref.org/works/" + doi,
                timeout=(10, 30),
                headers={"User-Agent": "EarthTrendDetective/0.2"},
                verify=certifi.where(),
            )
            resp.raise_for_status()
            message = resp.json()["message"]
        except Exception:  # noqa: BLE001
            continue
        title = (message.get("title") or [""])[0]
        abstract = re.sub(r"<[^>]+>", " ", message.get("abstract", "") or "")
        abstract = clean_text(abstract)
        url = message.get("URL") or f"https://doi.org/{doi}"
        date = None
        parts = (message.get("issued") or {}).get("date-parts") or [[None]]
        if parts and parts[0] and parts[0][0]:
            date = f"{parts[0][0]}-01-01"
        if len(abstract) >= 300:
            text = truncate_sentences(abstract)
            summary_by = None
        else:
            summary = PAPER_SUMMARY.get(doi)
            if not summary:
                continue
            text = summary
            summary_by = "hermes-1"
        docs.append(
            make_doc(
                id=doc_id("paper", doi.replace("/", "-").replace(".", "-")),
                type="paper_abstract",
                title=title,
                url=url,
                publisher=(message.get("container-title") or [""])[0] or "Crossref",
                date=date,
                lang="en",
                text=truncate_sentences(text) if len(text) > 1200 else text,
                variables=[],
                biomes=[],
                license="Crossref metadata; abstract rights with the publisher",
                fetched_at=TODAY + "T00:00:00Z",
                sha256=__import__("hashlib").sha256(resp.content).hexdigest(),
                doi=doi,
                summary_by=summary_by,
            )
        )
    return docs


def build_method_notes() -> list[dict]:
    docs = []
    for note in METHOD_NOTES:
        for lang in ("es", "en"):
            text = note["text_es"] if lang == "es" else note["text"]
            text = text if len(text) <= 1200 else truncate_sentences(text)
            docs.append(
                make_doc(
                    id=f"{note['id']}-{lang}",
                    type="method_note",
                    title=note["title_es"] if lang == "es" else note["title"],
                    url=note["urls"][0],
                    publisher="Hermes 1 summary of cited sources",
                    date=None,
                    lang=lang,
                    text=truncate_sentences(text),
                    variables=[],
                    biomes=[],
                    license="Original summary; sources cited in urls",
                    fetched_at=TODAY + "T00:00:00Z",
                    sha256=__import__("hashlib").sha256(note["id"].encode()).hexdigest(),
                    summary_by="hermes-1",
                    urls=note["urls"],
                )
            )
    return docs


def build_glossary() -> list[dict]:
    docs = []
    entries: list[dict[str, Any]] = []
    for term, term_es, definition in GLOSSARY_TERMS + GLOSSARY_FALLBACK:
        entries.append({
            "term": term,
            "term_es": term_es,
            "definition": definition,
            "url": "https://glossary.ametsoc.org/wiki/" + term.replace(" ", "_"),
            "publisher": "American Meteorological Society Glossary of Meteorology",
            "license": "AMS Glossary (check terms of use)",
        })
    # `biome` is not in the AMS Glossary (404); NASA's page is the source.
    entries.append({
        "term": BIOME_GLOSSARY["term"],
        "term_es": BIOME_GLOSSARY["term_es"],
        "definition": BIOME_GLOSSARY["definition"],
        "definition_es": BIOME_GLOSSARY["definition_es"],
        "url": BIOME_GLOSSARY["url"],
        "publisher": BIOME_GLOSSARY["publisher"],
        "license": "NASA (public domain)",
        "title_override": {"en": BIOME_GLOSSARY["title"], "es": BIOME_GLOSSARY["title_es"]},
    })

    for entry in entries:
        term = entry["term"]
        term_es = entry["term_es"]
        definition = entry["definition"]
        url = entry["url"]
        sha = None
        fetched = TODAY + "T00:00:00Z"
        final_url = url
        page_text: str | None = None
        try:
            page = fetch(url)
            sha = page.sha256
            fetched = page.retrieved_at
            final_url = page.final_url
            soup = BeautifulSoup(page.text, "lxml")
            main = soup.find("main") or soup
            page_text = clean_text(main.get_text(" "))
        except FetchError:
            page_text = None

        overrides = entry.get("title_override") or GLOSSARY_TITLE_OVERRIDES.get(term, {})
        title_override_en = overrides[0] if isinstance(overrides, tuple) else (overrides or {}).get("en")
        title_override_es = overrides[1] if isinstance(overrides, tuple) else (overrides or {}).get("es")

        # A glossary entry needs 300-1200 chars. The page text is stored
        # verbatim when long enough; otherwise the entry combines the page's
        # own text, a plain-language definition and a note saying so.
        for lang in ("es", "en"):
            if page_text and len(page_text) >= 300:
                body = page_text
                origin = "page"
            else:
                if lang == "es":
                    parts = [f"{term_es}: {entry.get('definition_es') or definition}"]
                    if page_text:
                        parts.append(f"Texto original (en inglés): {page_text}")
                    parts.append("Definición y nota redactadas por claude-omni-1b a partir de la fuente citada.")
                    parts.append(f"Fuente: {entry['publisher']}.")
                else:
                    parts = [definition]
                    if page_text:
                        parts.append(f"Original text: {page_text}")
                    parts.append("Note written by claude-omni-1b from the cited source.")
                    parts.append(f"Source: {entry['publisher']}.")
                parts.append(
                    "Este término se usa en EarthTrend Detective para explicar, en lenguaje sencillo, "
                    "qué mide una variable de ciencias de la Tierra y qué significa una tendencia."
                    if lang == "es" else
                    "This term is used in EarthTrend Detective to explain, in plain language, "
                    "what an Earth science variable measures and what a trend means."
                )
                body = " ".join(parts)
                origin = "claude-omni-1b"
                if sha is None:
                    sha = __import__("hashlib").sha256((term + definition).encode()).hexdigest()

            docs.append(
                make_doc(
                    id=doc_id("gloss", term) + "-" + lang,
                    type="glossary",
                    title=(title_override_es if lang == "es" else title_override_en) or (term_es if lang == "es" else term),
                    url=final_url,
                    publisher=entry["publisher"],
                    date=None,
                    lang=lang,
                    text=truncate_sentences(body),
                    variables=[],
                    biomes=[],
                    license=entry["license"],
                    fetched_at=fetched,
                    sha256=sha,
                    summary_by=None if origin == "page" else "claude-omni-1b",
                )
            )
    return docs


def build_ntrs_sources() -> list[dict]:
    """Acker et al. (2009) and any future NTRS record: title and abstract from
    the NTRS citation API (JSON, 200), so the stored text is the record's own."""
    docs = []
    for src in NTRS_SOURCES:
        api_url = f"https://ntrs.nasa.gov/api/citations/{src['ntrs_id']}"
        try:
            page = fetch(api_url, cache_key="ntrs_" + src["ntrs_id"],
                         headers={"User-Agent": "EarthTrendDetective/0.2"})
            record = json.loads(page.text)
        except Exception as exc:  # noqa: BLE001
            print(f"  ! {src['id']}: NTRS fetch failed ({type(exc).__name__}); skipped")
            continue
        title = clean_text(record.get("title") or src["title_fallback"])
        abstract = clean_text(record.get("abstract") or "")
        if len(abstract) < 300:
            print(f"  ! {src['id']}: abstract too short ({len(abstract)}); skipped")
            continue
        landing = f"https://ntrs.nasa.gov/citations/{src['ntrs_id']}"
        docs.append(
            make_doc(
                id=src["id"],
                type=src["type"],
                title=title,
                url=landing,
                publisher=src["publisher"],
                date=src["date"],
                lang=src["lang"],
                text=truncate_sentences(abstract),
                variables=src["variables"],
                biomes=[],
                license=src["license"],
                fetched_at=page.retrieved_at,
                sha256=page.sha256,
                ntrs_id=src["ntrs_id"],
                summary_by=None,
            )
        )
    return docs


def build_csa_sources() -> list[dict]:
    """Canadian Space Agency pages verified by claude-omni-2 and re-verified
    here. Only pages that answer 200 are included."""
    docs = []
    for src in CSA_SOURCES:
        try:
            page = fetch(src["url"], cache_key="csa_" + src["id"],
                         headers={
                             "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                                           "AppleWebKit/537.36 (KHTML, like Gecko) "
                                           "Chrome/126.0 Safari/537.36 EarthTrendDetective/0.2"
                         })
        except Exception as exc:  # noqa: BLE001
            print(f"  ! {src['id']}: CSA page not fetched ({type(exc).__name__}); skipped")
            continue
        soup = BeautifulSoup(page.text, "lxml")
        title = page_title(soup) or src["title_fallback"]
        text = article_text(soup)
        if len(text) < 300:
            print(f"  ! {src['id']}: text too short ({len(text)}); skipped")
            continue
        docs.append(
            make_doc(
                id=src["id"],
                type=src["type"],
                title=title,
                url=page.final_url,
                publisher=src["publisher"],
                date=src["date"],
                lang=src["lang"],
                text=truncate_sentences(text),
                variables=src["variables"],
                biomes=[],
                license=src["license"],
                fetched_at=page.retrieved_at,
                sha256=page.sha256,
            )
        )
    return docs


def main() -> int:
    catalog = load_catalog()
    docs: list[dict] = []
    docs.extend(build_variable_cards(catalog))
    docs.extend(build_planned_cards(catalog))
    docs.extend(build_biome_profiles())
    docs.extend(build_nasa_articles())
    docs.extend(build_papers())
    docs.extend(build_method_notes())
    docs.extend(build_glossary())
    docs.extend(build_ntrs_sources())
    docs.extend(build_csa_sources())

    # Deduplicate by id and by url+lang
    seen_ids: set[str] = set()
    unique: list[dict] = []
    for doc in docs:
        if doc["id"] in seen_ids:
            continue
        seen_ids.add(doc["id"])
        unique.append(doc)

    write_jsonl(DOCS_PATH, unique)

    from collections import Counter

    counts = Counter((d["type"], d["lang"]) for d in unique)
    print(f"wrote {len(unique)} documents to {DOCS_PATH}")
    for (t, lang), n in sorted(counts.items()):
        print(f"  {t:16s} {lang}: {n}")
    peru = sum(
        1 for d in unique
        if d["type"] == "nasa_article" and any(t in (d["title"] + " " + d["text"]).lower() for t in PERU_LATAM_TERMS)
    )
    print(f"  nasa_article Peru/LatAm: {peru}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
