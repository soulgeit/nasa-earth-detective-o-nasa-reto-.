# SI-assisted: claude-omni-2 (Claude Opus 5.5)
"""Colloquial-term -> variable_id bridge used only to *expand the query*.

Why this file exists
--------------------
Hermes 1 owns ``data/catalog/variables.json`` and writes the ``keywords`` field for
each card (prompt C1: "≥ 8 per idiom, including colloquial words"). Until that file
lands, the corpus only has the seed (ids + POWER long names), so a student's
"¿está lloviendo menos?" finds nothing.

This module is a linguistic resource, not a catalogue: it never states a fact about
a variable, it only says "when the student types *lluvia*, also search *rain,
precipitation, PRECTOTCORR*". Every alias below is a plain-language paraphrase of a
POWER parameter long name that is already in the verified seed/fixture
(``tests/fixtures/real/power_monthly_point_lima.json``). No definition, unit,
date or number is produced here.

When Hermes 1's ``variables.json`` arrives the expansion is still valid, just
redundant; ``retrieve`` merges everything through the same BM25 index.
"""

from __future__ import annotations

from typing import Iterable

from .text_norm import normalize_terms

# alias (es/en, accent-free, lowercase) -> variable_id from data/catalog/variables.seed.json
ALIASES: dict[str, tuple[str, ...]] = {
    "T2M": (
        "temperatura", "calor", "bochorno", "caliente", "frio", "fria", "grados", "termometro",
        "temperature", "heat", "hot", "cold", "warm", "air temperature", "ita est",
    ),
    "TS": (
        "temperatura de la superficie", "superficie", "suelo caliente", "tierra caliente",
        "skin temperature", "surface temperature", "land temperature",
    ),
    "PRECTOTCORR": (
        "lluvia", "llueve", "llover", "lloviendo", "precipitacion", "sequia", "seco", "seca",
        "garua", "llovizna", "pluviosidad", "chubasco",
        "rain", "raining", "precipitation", "rainfall", "drought", "dry", "wetter", "rainy season",
    ),
    "GWETTOP": (
        "humedad del suelo", "suelo humedo", "tierra humeda", "agua en el suelo",
        "turning into desert", "turning to desert",
        "desertificacion", "el suelo se esta desertificando",
        "secando el suelo", "suelo seco", "tierra seca", "se seca",
        "soil moisture", "soil wetness", "wet soil", "dry soil", "drying soil",
        "land drying", "desertification", "desertificacion", "soil is drying",
        "el suelo se seca", "se seca el suelo",
    ),
    "EVLAND": (
        "evaporacion", "evapotranspiracion", "se evapora",
        "evaporation", "evapotranspiration", "moisture loss",
    ),
    "SNODP": (
        "nieve", "nevada", "capa de nieve", "glaciar", "deshielo", "nevando",
        "snow", "snowfall", "snow depth", "glacier", "melting snow", "snowpack",
    ),
    "RH2M": (
        "humedad", "humedad relativa", "humedad del aire", "humedo", "humeda",
        "bochorno", "vapor", "aire humedo", "aire húmedo",
        "humidity", "relative humidity", "air humidity", "muggy", "damp", "moist air",
    ),
    "TQV": (
        "vapor de agua", "agua precipitable", "columna de agua", "humedad total",
        "water vapor", "precipitable water", "atmospheric moisture",
    ),
    "TO3": (
        "ozono", "capa de ozono", "agujero de ozono", "ozone", "ozone hole", "ozone column",
    ),
    "AOD_55": (
        "aerosoles", "aerosol", "polvo", "bruma", "neblina", "calima", "humo", "humo en el cielo",
        "smoke", "wildfire smoke", "incendios",
        "contaminacion del aire", "aire contaminado", "calidad del aire",
        "dust", "haze", "smoke", "particulate", "air pollution", "air quality", "polluted air",
    ),
    "CLOUD_AMT": (
        "nubes", "nubosidad", "cielo cubierto", "nublado", "garua", "garúa",
        "llovizna", "cielo", "clouds", "cloud cover", "overcast", "cloudiness", "drizzle",
    ),
    "ALLSKY_SFC_SW_DWN": (
        "radiacion solar", "sol", "energia solar", "luz del sol", "irradiancia",
        "solar radiation", "sunlight", "sunshine", "solar energy", "irradiance",
    ),
    "GISTEMP_TANOM": (
        "calentamiento global", "anomalia de temperatura", "cambio climatico", "temperatura global",
        "global warming", "temperature anomaly", "global temperature", "climate change",
    ),
    "SEAICE_EXTENT_N": (
        "hielo marino", "hielo del artico", "deshielo del artico", "mar congelado",
        "sea ice", "arctic ice", "ice extent", "melting ice", "arctic",
    ),
    "SEAICE_EXTENT_S": (
        "hielo marino", "hielo de la antartida", "antartida", "mar congelado",
        "sea ice", "antarctic ice", "ice extent", "antarctica",
    ),
    "GPM_IMERG_PRECIP": (
        "lluvia", "precipitacion", "lluvias intensas", "inundacion",
        "rain", "precipitation", "heavy rain", "flooding",
    ),
    "GLDAS_SOILM_0_10": (
        "humedad del suelo", "suelo seco", "agricultura", "cultivos",
        "soil moisture", "soil water", "crops", "farmland",
    ),
    "GLDAS_EVAP": ("evaporacion", "evaporation", "evapotranspiration"),
    "GLDAS_RUNOFF": (
        "escorrentia", "desague", "caudal del rio", "agua de rio",
        "runoff", "river flow", "streamflow", "drainage",
    ),
    "AIRS_SURF_AIR_TEMP": (
        "temperatura del aire", "calor", "frio", "temperature", "air temperature", "heat", "cold",
    ),
    "OMI_NO2_TROP": (
        "no2", "dioxido de nitrogeno", "contaminacion", "trafico", "smog",
        "nitrogen dioxide", "air quality", "pollution", "traffic",
    ),
    "OMI_O3_TOTAL": ("ozono", "ozone", "ozone column", "capa de ozono"),
    "MODIS_NDVI": (
        "vegetacion", "deforestacion", "bosque", "selva", "plantas", "verde", "verdor",
        "vegetation", "deforestation", "forest", "greenness", "ndvi", "vegetation index",
    ),
    "MODIS_LST_DAY": (
        "temperatura del suelo", "superficie", "calor urbano", "isla de calor",
        "land surface temperature", "surface heat", "urban heat",
    ),
    "MODIS_AOD": ("aerosoles", "polvo", "smog", "aerosol", "dust", "haze", "fine particles"),
    # --- RONDA_7: the 20 POWER variables added to the catalogue --------------
    # Single distinctive words on purpose. A multi-word alias also lends its words
    # as loose aliases, so "temperatura maxima" would make every "temperatura"
    # question hesitate between T2M and T2M_MAX.
    "T2M_MAX": ("maxima", "maximas", "maximum", "highs"),
    "T2M_MIN": ("minima", "minimas", "minimum", "lows", "friaje", "friajes"),
    "T2M_RANGE": ("amplitud", "oscilacion", "diurnal"),
    "T2MDEW": ("rocio", "dew", "dewpoint"),
    "QV2M": ("especifica", "specific"),
    "PS": ("presion", "barometro", "pressure", "barometer", "barometric"),
    "WS2M": (
        "viento", "vientos", "ventoso", "brisa", "rafagas", "vendaval", "ventarron",
        "wind", "winds", "windy", "windier", "windiest", "breeze", "gusts", "gale",
    ),
    "WS10M": ("anemometro", "anemometer", "stilling"),
    "WS50M": ("eolica", "eolico", "aerogenerador", "aerogeneradores", "turbina", "turbine", "turbines"),
    "GWETROOT": ("raices", "raiz", "roots", "rootzone"),
    "GWETPROF": ("perfil", "profile"),
    "PRECSNOLAND": ("nevazon", "snowstorm"),
    "FROST_DAYS": ("helada", "heladas", "hiela", "escarcha", "frost", "frosts", "freezing", "hoarfrost"),
    "TSOIL1": ("germinacion", "germination", "subsuelo", "seedbed"),
    "ALLSKY_SFC_LW_DWN": ("infrarroja", "infrarrojo", "invernadero", "longwave", "infrared", "greenhouse"),
    "CLRSKY_SFC_SW_DWN": ("despejado", "dimming", "brightening", "cloudless"),
    "ALLSKY_KT": ("claridad", "clearness"),
    "ALLSKY_SFC_UV_INDEX": ("ultravioleta", "uv", "quemadura", "bloqueador", "ultraviolet", "sunburn", "sunscreen"),
    "ALLSKY_SFC_PAR_TOT": ("fotosintesis", "fotosintetica", "photosynthesis", "photosynthetic"),
    "ALLSKY_SRF_ALB": ("albedo", "reflectividad", "reflectancia", "reflectivity", "reflectance"),
}

# RONDA_7: the catalogue grew from 15 to 35 variables. The additions are
# specialised views of something the catalogue already had (the monthly maximum,
# the wind at 50 m, the root zone...). They are proposed when the student names
# them; otherwise the general variable stays the default, so "is it getting
# hotter?" keeps meaning air temperature and not "the hottest hour of the month".
SPECIALISED: frozenset[str] = frozenset({
    "T2M_MAX", "T2M_MIN", "T2M_RANGE", "T2MDEW", "QV2M", "PS", "WS2M", "WS10M", "WS50M",
    "GWETROOT", "GWETPROF", "PRECSNOLAND", "FROST_DAYS", "TSOIL1", "ALLSKY_SFC_LW_DWN",
    "CLRSKY_SFC_SW_DWN", "ALLSKY_KT", "ALLSKY_SFC_UV_INDEX", "ALLSKY_SFC_PAR_TOT", "ALLSKY_SRF_ALB",
})

# Reverse map built once: normalised alias -> ids
# Words that must not become loose aliases even though they appear inside a
# multi-word alias. They are too generic on their own: "desert" is a place in
# "Sechura Desert", not a request for soil moisture data.
_PHRASE_ONLY_WORDS = frozenset({"desert", "turning", "turn", "into"})

_ALIAS_TO_IDS: dict[str, set[str]] = {}
# term -> ids for which the term IS the alias (not a word lent by a phrase).
# "temperatura" is T2M's own alias; TS only lends it through "temperatura de la
# superficie". The prior must tell the two apart (RONDA_7).
_DIRECT_ALIAS: dict[str, set[str]] = {}
for _vid, _aliases in ALIASES.items():
    for _alias in _aliases:
        _terms = normalize_terms(_alias)
        if len(_terms) == 1:
            _ALIAS_TO_IDS.setdefault(_terms[0], set()).add(_vid)
            _DIRECT_ALIAS.setdefault(_terms[0], set()).add(_vid)
        else:
            # A multi-word alias contributes its words ("soil", "drying") so a
            # question that separates them still matches — "Is the soil in Ica
            # drying out?" must reach GWETTOP. Words listed in _PHRASE_ONLY_WORDS
            # are excluded, and the phrase itself is matched separately below.
            for _term in _terms:
                if _term not in _PHRASE_ONLY_WORDS:
                    _ALIAS_TO_IDS.setdefault(_term, set()).add(_vid)

# Multi-word aliases ("humedad del aire", "air pollution") are only evidence when
# they appear as a phrase: their individual words are too common on their own.
_PHRASES: list[tuple[str, str, float]] = []
for _vid, _aliases in ALIASES.items():
    for _alias in _aliases:
        _terms = normalize_terms(_alias)
        if len(_terms) >= 2:
            _PHRASES.append((" ".join(_terms), _vid, 1.5))
_PHRASES.sort(key=lambda item: -len(item[0]))


def _normalized_text(query: str) -> str:
    return " ".join(normalize_terms(query))


def expand(query: str) -> dict[str, list[str]]:
    """variable_id -> the student's words that pointed at it (for the 'why' text).

    Single-word aliases match per word; multi-word aliases match as a phrase, so
    "turning into desert" still reaches GWETTOP without "desert" alone doing so.
    """
    hits: dict[str, list[str]] = {}
    text = _normalized_text(query)
    for term in text.split():
        for vid in _ALIAS_TO_IDS.get(term, ()):
            bucket = hits.setdefault(vid, [])
            if term not in bucket:
                bucket.append(term)
    padded = f" {text} "
    for phrase, vid, _weight in _PHRASES:
        if f" {phrase} " in padded:
            bucket = hits.setdefault(vid, [])
            if phrase not in bucket:
                bucket.append(phrase)
    return hits


def expansion_terms(query: str, *, exclude: Iterable[str] = ()) -> str:
    """Text to append to the BM25 query: variable ids and their seed long names."""
    from .corpus import load_catalog_cards

    wanted = {vid for vid in expand(query) if vid not in set(exclude)}
    if not wanted:
        return ""
    extra: list[str] = []
    for card, _available in load_catalog_cards():
        if card.get("id") in wanted:
            for key in ("power_longname", "names"):
                value = card.get(key)
                if isinstance(value, dict):
                    extra.extend(str(v) for v in value.values())
                elif value:
                    extra.append(str(value))
    extra.extend(sorted(wanted))
    return " ".join(extra)


def variables_for_terms(text: str) -> list[str]:
    return sorted(expand(text))


LOOSE_WORD_WEIGHT = 0.35


def specificity_prior(query: str) -> dict[str, float]:
    """variable_id -> bonus in [0, 1].

    A term that points at exactly one variable ("lluvia" -> PRECTOTCORR) is worth
    more than a term that points at six ("calor"). A multi-word phrase
    ("humedad del aire") is worth more still, because it is a deliberate match.
    Used only as a tie-breaker on top of BM25.
    """
    prior: dict[str, float] = {}
    text = _normalized_text(query)
    words = text.split()
    for term in words:
        ids = _ALIAS_TO_IDS.get(term)
        if not ids:
            continue
        direct = _DIRECT_ALIAS.get(term, set())
        for vid in ids:
            # The variable whose own alias this word is gets the full share; one
            # that only lends the word from a longer phrase gets a small one.
            weight = (1.0 / len(direct)) if vid in direct else (LOOSE_WORD_WEIGHT / len(ids))
            prior[vid] = prior.get(vid, 0.0) + weight
    for phrase, vid, weight in _PHRASES:
        if f" {phrase} " in f" {text} ":
            prior[vid] = prior.get(vid, 0.0) + weight
    peak = max(prior.values()) if prior else 1.0
    return {vid: value / peak for vid, value in prior.items()}
