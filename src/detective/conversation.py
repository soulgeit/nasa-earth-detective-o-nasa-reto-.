# SI-assisted: cfable (Claude Fable 5.2)
"""Huiracocha IA — the conversational layer (RONDA_7).

    message + context ─► small talk?  ─► a fixed, honest answer
                      ─► planner      ─► plan + what I am going to do
                      ─► place only   ─► what the sources say about it + what to ask
                      ─► knowledge    ─► excerpt from the cited corpus
                      ─► nothing      ─► say so, and offer things that work

Before this module a greeting came back as ``intent: no_match`` with no text and
the UI turned it into "I will investigate air temperature in the selected place".

Nothing here is generative. Every reply is either a fixed sentence, a field of
the catalogue, or text retrieved from the cited corpus, and every number the
student later sees comes from the statistics engine. That is why the reply can
always say where it comes from (``sources``) and which path produced it (``kind``).
"""

from __future__ import annotations

import re
from typing import Any

from .lexicon import expand
from .text_norm import detect_language, fold

NAME = "Huiracocha IA"
NAME_EN = "Huiracocha AI"

# The five cities of the round first: they are the ones the corpus knows best.
FEATURED_PLACES = ("Lima", "Huancayo", "Andahuaylas", "Ica", "Ayacucho")

SUGGESTIONS = {
    "es": [
        "¿Llueve menos en Ica?",
        "¿Hace más calor en Lima?",
        "¿Hay menos heladas en Huancayo?",
        "¿Cambió la lluvia en Ayacucho?",
        "¿Sube la temperatura mínima en Andahuaylas?",
        "¿Qué está cambiando en Huancayo?",
    ],
    "en": [
        "Is it raining less in Ica?",
        "Is Lima getting hotter?",
        "Are there fewer frosts in Huancayo?",
        "Has rainfall changed in Ayacucho?",
        "Is the minimum temperature rising in Andahuaylas?",
        "What is changing in Huancayo?",
    ],
}

# What to offer once a place is known: (variable_id, es, es with article, en).
PLACE_TOPICS = (
    ("T2M", "temperatura", "la temperatura", "temperature"),
    ("PRECTOTCORR", "lluvia", "la lluvia", "rainfall"),
    ("FROST_DAYS", "heladas", "las heladas", "frost days"),
    ("GWETROOT", "humedad del suelo para los cultivos", "la humedad del suelo", "soil moisture for crops"),
    ("WS2M", "viento", "el viento", "wind"),
    ("ALLSKY_SFC_UV_INDEX", "radiación UV", "la radiación UV", "UV radiation"),
)


def _rx(*alternatives: str) -> re.Pattern[str]:
    return re.compile(r"(?<!\w)(?:" + "|".join(alternatives) + r")(?!\w)")


# Patterns run on accent-free lowercase text (``fold``).
_GREETING = _rx(
    r"hola+", r"holi+s?", r"buenas", r"buen(?:os)? dias?", r"buenas (?:tardes|noches)",
    r"saludos", r"que tal", r"que onda", r"hey+", r"hi+", r"hello+", r"good (?:morning|afternoon|evening)",
    r"greetings", r"howdy",
)
_HOW_ARE_YOU = _rx(r"como estas", r"como te va", r"como andas", r"todo bien", r"how are you", r"how is it going", r"how are things")
_IDENTITY = _rx(
    r"quien eres", r"que eres", r"como te llamas", r"cual es tu nombre", r"tu nombre", r"eres (?:una? )?(?:ia|robot|persona|humano|bot)",
    r"que es huiracocha", r"quien es huiracocha", r"por que (?:te llamas|huiracocha)", r"que significa huiracocha",
    r"who are you", r"what are you", r"what is your name", r"your name", r"are you (?:an? )?(?:ai|robot|human|bot)",
    r"who is huiracocha", r"what is huiracocha", r"why (?:are you called|huiracocha)",
)
_HELP = _rx(
    r"que puedes hacer", r"que sabes hacer", r"que haces", r"para que sirves", r"en que (?:me )?(?:puedes )?ayuda\w*",
    r"ayuda", r"ayudame", r"como funciona\w*", r"como te uso", r"como (?:se|lo) usa", r"instrucciones", r"no entiendo",
    r"que (?:te )?puedo preguntar\w*", r"por donde empiezo",
    r"what can you do", r"what do you do", r"help", r"how do(?:es)? (?:you|this|it) work", r"how do i use",
    r"what can i ask", r"where do i start", r"instructions",
)
_THANKS = _rx(r"(?:muchas |mil )?gracias", r"te agradezco", r"thank(?:s| you)", r"thx", r"genial", r"perfecto", r"excelente", r"great", r"awesome", r"nice")
_BYE = _rx(r"adios", r"chau+", r"chao", r"hasta (?:luego|pronto|manana)", r"nos vemos", r"bye+", r"goodbye", r"see you")
_VARIABLES = _rx(
    r"(?:que|cuales|cuantas) variables", r"variables (?:tienes|hay|disponibles|puedo)", r"lista de variables",
    r"que (?:datos|cosas) (?:tienes|puedes (?:medir|analizar|investigar))", r"que puedo (?:investigar|analizar|medir)",
    r"(?:what|which|how many) variables", r"list (?:of |the )?variables", r"variables (?:do you have|available)",
    r"what (?:data|things) (?:do you have|can you (?:measure|analy[sz]e))", r"what can i (?:investigate|analy[sz]e)",
)
_PLACES = _rx(
    r"(?:que|cuales) (?:ciudades|lugares|sitios|regiones|paises)", r"(?:en )?que lugares", r"de donde tienes datos",
    r"(?:what|which) (?:cities|places|regions|countries)", r"where do you have data",
)
_DATA_SOURCE = _rx(
    r"de donde (?:salen|vienen|sacas|obtienes)\w* (?:los |tus )?datos", r"fuentes? de (?:los |tus )?datos", r"que datos usas",
    r"(?:son|es) (?:datos )?(?:reales?|inventad\w+|simulad\w+)", r"(?:de|con) que satelite\w*", r"quien mide",
    r"where (?:does|do) (?:the |your )?data come from", r"data sources?", r"is (?:the |this |your )?data real",
    r"which satellites?",
)
_METHOD = _rx(
    r"mann[- ]?kendall", r"theil[- ]?sen", r"pendiente de sen", r"valor[- ]p", r"p[- ]?valor", r"p[- ]?value",
    r"significativ\w+", r"significan\w+", r"intervalos? de confianza", r"confidence intervals?", r"autocorrelacion",
    r"autocorrelation", r"estacionalidad", r"desestacionali\w+", r"seasonal\w*", r"como (?:sabes|calculas|decides|mides)",
    r"que metodo\w*", r"how do you (?:know|calculate|decide|measure)", r"what method\w*", r"t[- ]?test", r"prueba t",
)
_SCAN = _rx(
    r"que (?:esta|ha|han) (?:cambia\w+|pasa\w+)", r"que cambia", r"escanea\w*", r"escaneo", r"resumen de", r"panorama de",
    r"todas las variables", r"todo (?:sobre|de)", r"revisa\w* todo", r"analiza\w* todo",
    r"what(?: is|'s| has)? chang\w+", r"scan", r"overview of", r"summary of", r"all (?:the )?variables", r"everything about",
)
_CLIMATE_ONLY = _rx(r"clima", r"climate", r"tiempo", r"weather", r"hablame", r"cuentame", r"tell me about", r"como es")

_EN_SHORT = frozenset(
    "hi hello hey thanks thx bye goodbye help great awesome nice greetings howdy scan".split()
)
_EN_MARKERS = _EN_SHORT | frozenset(
    "good morning afternoon evening there what which where how who why is are the you your can do does "
    "please thank and in rain wind frost temperature snow".split()
)
_ES_SHORT = frozenset(
    "hola holi ola alo buenas gracias adios chau chao ayuda genial perfecto excelente saludos".split()
)


def _language(message: str, lang: str | None) -> str:
    """Answer in the language of the message; fall back to the UI language."""
    folded = fold(message).strip(" ¿?¡!.,")
    words = folded.split()
    if len(words) <= 1:
        if folded in _EN_SHORT:
            return "en"
        if folded in _ES_SHORT:
            return "es"
        return lang if lang in ("es", "en") else "es"
    # A short message has too few words for the detector, which then says
    # Spanish: "Good morning" must still be answered in English.
    if len(words) <= 4 and any(w in _EN_MARKERS for w in words) and not any(w in _ES_SHORT for w in words):
        return "en"
    detected = detect_language(message)
    if detected in ("es", "en"):
        return detected
    return lang if lang in ("es", "en") else "es"


def _t(lang: str, es: str, en: str) -> str:
    return es if lang == "es" else en


# --- catalogue helpers -------------------------------------------------------

def _cards() -> list[tuple[dict[str, Any], bool]]:
    from .corpus import load_catalog_cards

    return load_catalog_cards()


def _card(variable_id: str | None) -> dict[str, Any] | None:
    if not variable_id:
        return None
    for card, _available in _cards():
        if str(card.get("id")) == variable_id:
            return card
    return None


def _name(variable_id: str | None, lang: str) -> str:
    card = _card(variable_id)
    names = (card or {}).get("names") or {}
    return str(names.get(lang) or names.get("en") or variable_id or "")


def _pick(value: Any, lang: str) -> str:
    if isinstance(value, dict):
        value = value.get(lang) or value.get("en") or value.get("es")
    if isinstance(value, list):
        return str(value[0]) if value else ""
    return str(value or "")


def _names_variable(folded_question: str, variable_id: str, named: list[str]) -> bool:
    """True when the student's own words point at this variable.

    The planner retrieves on every word of the card, so "¿qué es El Niño?" reached
    surface pressure because "El Niño" is listed among its typical drivers. A
    variable is only accepted when the lexicon maps a word of the question to it,
    or when the question contains one of the card's names or keywords.
    """
    if variable_id in named:
        return True
    card = _card(variable_id) or {}
    phrases: list[str] = []
    for key in ("names", "keywords"):
        value = card.get(key) or {}
        for item in (value.values() if isinstance(value, dict) else [value]):
            phrases.extend(item if isinstance(item, list) else [item])
    padded = f" {folded_question} "
    for phrase in phrases:
        needle = " ".join(fold(str(phrase)).split())
        if len(needle) >= 5 and f" {needle} " in padded:
            return True
    return False


def _is_point_variable(variable_id: str) -> bool:
    card = _card(variable_id) or {}
    return str(card.get("connector") or "power") in ("power", "giovanni_csv")


def _source_line(variable_id: str, lang: str) -> str:
    source = (_card(variable_id) or {}).get("source") or {}
    mission = source.get("model_or_mission")
    via = source.get("via")
    start = str(source.get("start") or "")[:4]
    if not mission:
        return ""
    origin = f"{mission} ({via})" if via and via not in str(mission) else str(mission)
    if start:
        return _t(lang, f"datos reales de {origin}, desde {start}", f"real data from {origin}, since {start}")
    return _t(lang, f"datos reales de {origin}", f"real data from {origin}")


# --- replies -----------------------------------------------------------------

def _base(kind: str, lang: str, reply: str, **extra: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "schema": "chat/1",
        "kind": kind,
        "lang": lang,
        "reply": reply.strip(),
        "plan": None,
        "action": None,
        "suggestions": [],
        "sources": [],
        "context": {},
        "mode": "rules",
        "assistant": NAME if lang == "es" else NAME_EN,
    }
    payload.update(extra)
    return payload


def _counts() -> tuple[int, int]:
    cards = _cards()
    return sum(1 for _c, ok in cards if ok), sum(1 for _c, ok in cards if not ok)


def _greeting(lang: str, *, asked_how: bool = False) -> dict[str, Any]:
    ready, _planned = _counts()
    how = _t(lang, "Muy bien, gracias por preguntar. ", "Doing well, thanks for asking. ") if asked_how else ""
    reply = _t(
        lang,
        f"¡Hola! {how}Soy **{NAME}**, tu detective de tendencias de la Tierra. "
        f"Dime un lugar y qué te preocupa, y lo compruebo con datos reales de la NASA: "
        f"qué cambia, dónde, cuánto y si el cambio es significativo. "
        f"Tengo {ready} variables listas, desde la lluvia y las heladas hasta el viento y la radiación UV. "
        f"Puedes empezar con una de estas preguntas:",
        f"Hello! {how}I am **{NAME_EN}**, your Earth-trend detective. "
        f"Tell me a place and what worries you, and I will check it against real NASA data: "
        f"what is changing, where, how much, and whether the change is significant. "
        f"I have {ready} variables ready, from rainfall and frost to wind and UV radiation. "
        f"You can start with one of these questions:",
    )
    return _base("greeting", lang, reply, suggestions=SUGGESTIONS[lang][:5])


def _identity(lang: str) -> dict[str, Any]:
    reply = _t(
        lang,
        f"Soy **{NAME}**. Mi nombre viene de Huiracocha (Wiracocha), la deidad creadora de la tradición andina. "
        "No improviso respuestas: elijo la variable con reglas verificadas y un buscador sobre fuentes citadas, "
        "descargo la serie real (NASA POWER, GISTEMP, NSIDC) y dejo que la estadística decida: pendiente de "
        "Theil-Sen, prueba de Mann-Kendall e intervalo de confianza. Si no tengo un dato, te lo digo.",
        f"I am **{NAME_EN}**. My name comes from Huiracocha (Wiracocha), the creator deity of Andean tradition. "
        "I do not improvise answers: I pick the variable with verified rules and a search over cited sources, "
        "download the real series (NASA POWER, GISTEMP, NSIDC) and let statistics decide: Theil-Sen slope, "
        "Mann-Kendall test and confidence interval. If I do not have something, I say so.",
    )
    return _base("identity", lang, reply, suggestions=SUGGESTIONS[lang][:3])


def _help(lang: str) -> dict[str, Any]:
    ready, planned = _counts()
    reply = _t(
        lang,
        "Esto es lo que puedo hacer por ti:\n"
        "1. **Investigar una variable en un lugar** — «¿Llueve menos en Ica?»\n"
        "2. **Revisar todas las variables de un lugar** — «¿Qué está cambiando en Huancayo?»\n"
        "3. **Comparar dos lugares** — «Compara la temperatura de Lima y Ayacucho»\n"
        "4. **Explicar una variable o un método** — «¿Qué es la humedad del suelo?», «¿Qué es Mann-Kendall?»\n"
        "5. **Seguir el hilo** — después de una respuesta, pregunta «¿y en Andahuaylas?» o «¿y la lluvia?»\n"
        f"Trabajo con {ready} variables listas y conozco {planned} más que necesitan un archivo de Giovanni. "
        "Cada respuesta dice de dónde sale el dato.",
        "Here is what I can do for you:\n"
        "1. **Investigate a variable in a place** — \"Is it raining less in Ica?\"\n"
        "2. **Check every variable for a place** — \"What is changing in Huancayo?\"\n"
        "3. **Compare two places** — \"Compare temperature in Lima and Ayacucho\"\n"
        "4. **Explain a variable or a method** — \"What is soil moisture?\", \"What is Mann-Kendall?\"\n"
        "5. **Follow up** — after an answer, ask \"and in Andahuaylas?\" or \"and rainfall?\"\n"
        f"I work with {ready} ready variables and know {planned} more that need a Giovanni file. "
        "Every answer says where the data comes from.",
    )
    return _base("help", lang, reply, suggestions=SUGGESTIONS[lang])


def _thanks(lang: str) -> dict[str, Any]:
    reply = _t(
        lang,
        "¡Con gusto! Si quieres seguir investigando, cambia de lugar o de variable: por ejemplo «¿y en Ayacucho?».",
        "You are welcome! To keep investigating, switch place or variable: for example \"and in Ayacucho?\".",
    )
    return _base("thanks", lang, reply, suggestions=SUGGESTIONS[lang][2:5])


def _bye(lang: str) -> dict[str, Any]:
    reply = _t(
        lang,
        "¡Hasta pronto! Recuerda: una tendencia que aún no es significativa a veces solo necesita más años de datos.",
        "See you soon! Remember: a trend that is not yet significant sometimes just needs more years of data.",
    )
    return _base("farewell", lang, reply)


SPHERES = (
    ("atmosphere", "Atmósfera", "Atmosphere"),
    ("land", "Tierra y suelo", "Land and soil"),
    ("cryosphere", "Hielo y nieve", "Ice and snow"),
    ("ocean", "Océano", "Ocean"),
)


def _variables(lang: str) -> dict[str, Any]:
    ready, planned = _counts()
    groups: dict[str, list[str]] = {}
    for card, available in _cards():
        if available:
            groups.setdefault(str(card.get("sphere") or "atmosphere"), []).append(_name(str(card["id"]), lang))
    lines = []
    for key, es, en in SPHERES:
        if groups.get(key):
            lines.append(f"**{_t(lang, es, en)}:** " + ", ".join(groups[key]) + ".")
    reply = _t(
        lang,
        f"Tengo **{ready} variables listas** para analizar en cualquier punto del mapa:\n" + "\n".join(lines)
        + f"\nAdemás conozco {planned} productos de misión (GPM, GLDAS, MODIS, OMI, AIRS) que se cargan subiendo su CSV de Giovanni. "
        "Pregúntame «¿qué es…?» sobre cualquiera, o nómbrala junto a un lugar.",
        f"I have **{ready} variables ready** to analyse at any point on the map:\n" + "\n".join(lines)
        + f"\nI also know {planned} mission products (GPM, GLDAS, MODIS, OMI, AIRS) that load from their Giovanni CSV. "
        "Ask me \"what is…?\" about any of them, or name one together with a place.",
    )
    suggestions = _t(
        lang,
        ["¿Qué es la humedad del suelo en la zona de raíces?", "Viento en Ica", "Radiación UV en Ayacucho", "Heladas en Huancayo"],
        ["What is root zone soil wetness?", "Wind in Ica", "UV radiation in Ayacucho", "Frost in Huancayo"],
    )
    return _base("variables", lang, reply, suggestions=suggestions)


def _places_reply(lang: str) -> dict[str, Any]:
    cities = ", ".join(FEATURED_PLACES)
    reply = _t(
        lang,
        f"Puedo analizar **cualquier punto del planeta**: escribe una ciudad (conozco más de 8 000) o haz clic en el mapa. "
        f"Las que mejor documentadas tengo, con fuentes locales, son **{cities}**. "
        "También conozco regiones con nombre propio, como la Amazonía, el Ártico o el Altiplano.",
        f"I can analyse **any point on the planet**: type a city (I know more than 8,000) or click the map. "
        f"The best documented ones, with local sources, are **{cities}**. "
        "I also know named regions such as the Amazon, the Arctic or the Altiplano.",
    )
    return _base("places", lang, reply, suggestions=SUGGESTIONS[lang][:5])


def _data_source(lang: str) -> dict[str, Any]:
    reply = _t(
        lang,
        "Todos los datos son reales y se descargan en el momento, sin cuenta ni clave: **NASA POWER** (reanálisis "
        "MERRA-2 y radiación de CERES, mensual desde 1981), **GISTEMP** de NASA GISS (anomalía global desde 1880) y "
        "el **Sea Ice Index** del NSIDC (hielo marino desde 1978). Cada resultado muestra su procedencia: la URL "
        "exacta de la petición, la fecha y una huella sha256. Nada se simula: si la fuente no responde, verás un "
        "código de error y no un número inventado.",
        "All data is real and downloaded on the spot, with no account or key: **NASA POWER** (MERRA-2 reanalysis "
        "and CERES radiation, monthly since 1981), NASA GISS **GISTEMP** (global anomaly since 1880) and the NSIDC "
        "**Sea Ice Index** (sea ice since 1978). Every result shows its provenance: the exact request URL, the date "
        "and a sha256 fingerprint. Nothing is simulated: if a source does not answer you get an error code, never "
        "an invented number.",
    )
    sources = [
        {"title": "NASA POWER — Data Methodology", "url": "https://power.larc.nasa.gov/docs/methodology/", "publisher": "NASA LaRC"},
        {"title": "GISS Surface Temperature Analysis (GISTEMP v4)", "url": "https://data.giss.nasa.gov/gistemp/", "publisher": "NASA GISS"},
        {"title": "Sea Ice Index", "url": "https://nsidc.org/data/seaice_index", "publisher": "NSIDC"},
    ]
    return _base("data_source", lang, reply, sources=sources, suggestions=SUGGESTIONS[lang][:3])


def _sentences(text: str, *, limit: int = 420) -> str:
    """The first sentences of a passage, never cut in the middle of a word."""
    text = " ".join(str(text).split())
    if len(text) <= limit:
        return text
    cut = text[:limit]
    stop = max(cut.rfind(". "), cut.rfind("; "))
    if stop >= limit * 0.5:
        return cut[: stop + 1]
    return cut[: cut.rfind(" ")].rstrip(",;:") + "…"


def _public_source(doc: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": doc.get("id"),
        "title": doc.get("title"),
        "url": doc.get("url"),
        "publisher": doc.get("publisher"),
        "is_quotation": bool(doc.get("is_quotation", True)),
    }


def _content_words(text: str) -> set[str]:
    from .text_norm import tokenize

    return {w for w in tokenize(text) if len(w) >= 4}


def _knowledge(question: str, lang: str, *, types: list[str], place: str | None = None, k: int = 2) -> list[dict[str, Any]]:
    """Documents that really talk about the question (never a loose match)."""
    from .rag import retrieve

    wanted = _content_words(question)
    place_key = fold(place).strip() if place else None
    pattern = re.compile(r"(?<!\w)" + re.escape(place_key) + r"(?!\w)") if place_key else None
    found: list[dict[str, Any]] = []
    seen_urls: set[str] = set()
    candidates = retrieve(question, lang=lang, k=24, types=types)
    candidates.sort(key=lambda d: 0 if d.get("lang") == lang else 1)
    for doc in candidates:
        haystack = fold(f"{doc.get('title') or ''} {doc.get('text') or ''}")
        if pattern is not None:
            if not (pattern.search(fold(doc.get("title") or "")) or place_key in (doc.get("places") or [])):
                continue
        else:
            overlap = sum(1 for w in wanted if w in haystack)
            if overlap < min(2, len(wanted)) or not wanted:
                continue
        url = str(doc.get("url") or "")
        if url in seen_urls:
            continue
        seen_urls.add(url)
        found.append(doc)
        if len(found) >= k:
            break
    return found


def _quote(doc: dict[str, Any], lang: str) -> str:
    excerpt = _sentences(doc.get("text") or "")
    publisher = doc.get("publisher") or doc.get("title") or ""
    if doc.get("is_quotation", True):
        return f"«{excerpt}» — {publisher}"
    return _t(lang, f"{excerpt} (resumen de {publisher})", f"{excerpt} (summary of {publisher})")


def _method(question: str, lang: str) -> dict[str, Any]:
    docs = _knowledge(question, lang, types=["method_note", "glossary"], k=2)
    intro = _t(
        lang,
        "Así decido si un cambio es real: quito el ciclo estacional, mido la pendiente con Theil-Sen (resiste los "
        "valores raros), pruebo la dirección con Mann-Kendall corregido por autocorrelación y calculo un intervalo "
        "de confianza del 95 %. Llamo «significativa» a una tendencia cuando es muy improbable que salga del azar "
        "(valor p menor que 0,05).",
        "This is how I decide whether a change is real: I remove the seasonal cycle, measure the slope with "
        "Theil-Sen (robust to odd values), test the direction with Mann-Kendall corrected for autocorrelation and "
        "compute a 95% confidence interval. I call a trend \"significant\" when it is very unlikely to come from "
        "chance (p-value below 0.05).",
    )
    extra = ""
    if docs:
        extra = "\n" + _t(lang, "De mis fuentes: ", "From my sources: ") + _quote(docs[0], lang)
    return _base(
        "method", lang, intro + extra,
        sources=[_public_source(d) for d in docs],
        suggestions=_t(lang, ["¿Qué es el valor p?", "¿Qué es Mann-Kendall?", "¿Llueve menos en Ica?"],
                       ["What is a p-value?", "What is Mann-Kendall?", "Is it raining less in Ica?"]),
    )


def _define(variable_id: str, lang: str) -> dict[str, Any]:
    card = _card(variable_id) or {}
    name = _name(variable_id, lang)
    unit = card.get("unit") or ""
    parts = [f"**{name}** ({variable_id}{', ' + str(unit) if unit else ''}). {_pick(card.get('simple_definition'), lang)}"]
    up, down = _pick(card.get("what_up_means"), lang), _pick(card.get("what_down_means"), lang)
    if up:
        parts.append(_t(lang, f"Si sube: {up}", f"If it rises: {up}"))
    if down:
        parts.append(_t(lang, f"Si baja: {down}", f"If it falls: {down}"))
    caveat = _pick(card.get("caveats"), lang)
    if caveat:
        parts.append(_t(lang, f"Ojo: {caveat}", f"Mind: {caveat}"))
    origin = _source_line(variable_id, lang)
    if origin:
        parts.append(_t(lang, f"La analizo con {origin}.", f"I analyse it with {origin}."))
    source = card.get("source") or {}
    sources = [{"title": name, "url": source.get("url"), "publisher": source.get("via") or source.get("model_or_mission")}] if source.get("url") else []
    place = FEATURED_PLACES[len(variable_id) % len(FEATURED_PLACES)]
    suggestions = _t(
        lang,
        [f"{name} en {place}", "¿Qué variables tienes?"],
        [f"{name} in {place}", "Which variables do you have?"],
    )
    return _base("define", lang, " ".join(parts), sources=sources, suggestions=suggestions,
                 context={"variable_id": variable_id})


def _missing(plan: dict[str, Any], lang: str) -> dict[str, Any]:
    names = ", ".join(plan.get("missing") or [])
    how = " ".join(plan.get("how_to_load") or [])
    alternatives = [a for a in (plan.get("alternatives") or []) if a.get("variable_id")]
    reply = _t(
        lang,
        f"Eso corresponde a **{names}**, un dato que conozco pero que todavía no tengo cargado, y prefiero decírtelo "
        f"antes que darte otra cosa parecida. {how}",
        f"That is **{names}**, something I know about but do not have loaded yet, and I would rather tell you than "
        f"hand you something merely similar. {how}",
    )
    suggestions: list[str] = []
    if alternatives:
        listed = ", ".join(_name(a["variable_id"], lang) for a in alternatives)
        reply += " " + _t(lang, f"Lo más cercano que sí puedo analizar ahora: {listed}.",
                          f"The closest things I can analyse right now: {listed}.")
        place = plan.get("place") or FEATURED_PLACES[0]
        for alt in alternatives[:3]:
            label = _name(alt["variable_id"], lang)
            suggestions.append(_t(lang, f"{label} en {place}", f"{label} in {place}"))
    return _base("missing_variable", lang, reply, suggestions=suggestions)


def _out_of_scope(lang: str) -> dict[str, Any]:
    reply = _t(
        lang,
        "Eso se sale de lo mío: solo sé de variables de la Tierra (clima, agua, suelo, hielo, aire) y de cómo "
        "cambian con el tiempo. Pero si te interesa algún lugar, pregúntame qué está cambiando ahí.",
        "That is outside my field: I only know about Earth variables (climate, water, soil, ice, air) and how "
        "they change over time. But if a place interests you, ask me what is changing there.",
    )
    return _base("out_of_scope", lang, reply, suggestions=SUGGESTIONS[lang][:4])


def _fallback(lang: str) -> dict[str, Any]:
    reply = _t(
        lang,
        "No estoy seguro de haberte entendido, y prefiero no adivinar. Dime **un lugar** y **qué quieres saber**, "
        "por ejemplo «temperatura en Huancayo» o «¿llueve menos en Ica?». También puedes escribir «ayuda».",
        "I am not sure I understood, and I would rather not guess. Tell me **a place** and **what you want to "
        "know**, for example \"temperature in Huancayo\" or \"is it raining less in Ica?\". You can also type \"help\".",
    )
    return _base("fallback", lang, reply, suggestions=SUGGESTIONS[lang][:4])


def _ask_place(variable_id: str, lang: str) -> dict[str, Any]:
    name = _name(variable_id, lang)
    reply = _t(
        lang,
        f"Puedo investigar **{name}**. ¿En qué lugar? Escribe una ciudad o elige una:",
        f"I can investigate **{name}**. Where? Type a city or pick one:",
    )
    label = name[0].upper() + name[1:]
    suggestions = [_t(lang, f"{label} en {p}", f"{label} in {p}") for p in FEATURED_PLACES]
    return _base("ask_place", lang, reply, suggestions=suggestions, context={"variable_id": variable_id})


def _place_briefing(place: str, lang: str, question: str) -> dict[str, Any]:
    """A place with no variable: what the sources say, and what could be asked."""
    docs = _knowledge(f"{place} {question}", lang, types=["region_note", "nasa_article", "paper_abstract"], place=place, k=2)
    if docs:
        body = _t(lang, f"Esto dicen mis fuentes sobre **{place}**:\n", f"This is what my sources say about **{place}**:\n")
        body += "\n".join("• " + _quote(d, lang) for d in docs)
    else:
        body = _t(
            lang,
            f"Tengo los datos de la NASA para **{place}**, aunque todavía no notas locales que citar.",
            f"I have the NASA data for **{place}**, though no local notes to cite yet.",
        )
    body += "\n" + _t(lang, "¿Qué quieres que compruebe ahí?", "What would you like me to check there?")
    suggestions = [_t(lang, f"{es[0].upper() + es[1:]} en {place}", f"{en[0].upper() + en[1:]} in {place}") for _vid, es, _art, en in PLACE_TOPICS[:5]]
    suggestions.append(_t(lang, f"¿Qué está cambiando en {place}?", f"What is changing in {place}?"))
    return _base("place_briefing", lang, body, sources=[_public_source(d) for d in docs],
                 suggestions=suggestions, context={"place": place})


def _scan(place: str, lang: str) -> dict[str, Any]:
    reply = _t(
        lang,
        f"Voy a revisar **todas las variables** que tengo para **{place}** y a ordenarlas por lo claro que es su "
        "cambio. Como son muchas pruebas a la vez, corrijo el umbral para no confundir casualidades con tendencias.",
        f"I will check **every variable** I have for **{place}** and rank them by how clear their change is. "
        "Because that is many tests at once, I correct the threshold so chance is not mistaken for a trend.",
    )
    return _base("scan", lang, reply, action="scan", context={"place": place},
                 plan={"intent": "scan", "place": place, "variable_ids": [], "lang": lang})


def _plan_reply(plan: dict[str, Any], lang: str, *, inherited: list[str]) -> dict[str, Any]:
    variable_id = plan["variable_ids"][0]
    name = _name(variable_id, lang)
    place, place_b = plan.get("place"), plan.get("place_b")
    compare = plan.get("intent") == "compare" and place and place_b
    origin = _source_line(variable_id, lang)
    if compare:
        text = _t(lang, f"Voy a comparar **{name}** entre **{place}** y **{place_b}**",
                  f"I will compare **{name}** between **{place}** and **{place_b}**")
    else:
        text = _t(lang, f"Voy a investigar **{name}** en **{place}**", f"I will investigate **{name}** in **{place}**")
    text += f" {_t(lang, 'con', 'with')} {origin}." if origin else "."
    if plan.get("start_year") and plan.get("end_year"):
        text += " " + _t(lang, f"Periodo: {plan['start_year']}–{plan['end_year']}.", f"Period: {plan['start_year']}–{plan['end_year']}.")
    elif plan.get("last_n_years"):
        text += " " + _t(lang, f"Periodo: los últimos {plan['last_n_years']} años.", f"Period: the last {plan['last_n_years']} years.")
    if plan.get("hypothesis") == "up":
        text += " " + _t(lang, "Tu sospecha es que está subiendo; lo compruebo.", "Your hunch is that it is rising; I will check.")
    elif plan.get("hypothesis") == "down":
        text += " " + _t(lang, "Tu sospecha es que está bajando; lo compruebo.", "Your hunch is that it is falling; I will check.")
    if "place" in inherited:
        text += " " + _t(lang, f"(Sigo en {place}, el lugar de antes.)", f"(Staying in {place}, the previous place.)")
    if "variable" in inherited:
        text += " " + _t(lang, "(Mantengo la variable de antes.)", "(Keeping the previous variable.)")
    if plan.get("mode") == "lora":
        text += " " + _t(lang, "(Plan propuesto por el planificador LoRA y verificado por reglas.)",
                         "(Plan proposed by the LoRA planner and checked by rules.)")
    if plan.get("mode") == "llm":
        text += " " + _t(lang, "(Plan propuesto por el modelo de lenguaje y verificado por reglas.)",
                         "(Plan proposed by the language model and checked by rules.)")
    definition = _pick((_card(variable_id) or {}).get("simple_definition"), lang)
    if definition:
        text += "\n" + _t(lang, f"Qué mide: {definition}", f"What it measures: {definition}")

    # What is already known about this place and this variable, with its source.
    sources: list[dict[str, Any]] = []
    if place and not compare:
        local = [d for d in _knowledge(f"{place} {name}", lang, types=["region_note", "nasa_article", "paper_abstract"], place=place, k=4)
                 if variable_id in (d.get("variables") or [])][:1]
        if local:
            text += "\n" + _t(lang, "Contexto local: ", "Local context: ") + _quote(local[0], lang)
            sources = [_public_source(local[0])]

    others = [p for p in FEATURED_PLACES if fold(p) not in (fold(place or ""), fold(place_b or ""))]
    suggestions = [_t(lang, f"¿Y en {others[0]}?", f"And in {others[0]}?")]
    for vid, _es, with_article, en in PLACE_TOPICS:
        if vid != variable_id and len(suggestions) < 3:
            suggestions.append(_t(lang, f"¿Y {with_article}?", f"And {en}?"))
    if place and not compare:
        suggestions.append(_t(lang, f"¿Qué está cambiando en {place}?", f"What is changing in {place}?"))
    return _base(
        "plan", lang, text, plan=plan, action="compare" if compare else "analyze",
        suggestions=suggestions, sources=sources,
        context={"place": place, "place_b": place_b, "variable_id": variable_id},
    )


# --- entry point -------------------------------------------------------------

def _clean_context(context: Any) -> dict[str, Any]:
    if not isinstance(context, dict):
        return {}
    out: dict[str, Any] = {}
    for key in ("place", "place_b", "variable_id"):
        value = context.get(key)
        if isinstance(value, str) and 0 < len(value.strip()) <= 80:
            out[key] = value.strip()
    if out.get("variable_id") and not _card(out["variable_id"]):
        out.pop("variable_id")
    return out


def _small_talk(folded: str, lang: str, *, has_topic: bool) -> dict[str, Any] | None:
    """Fixed answers. A message that also carries a real question skips them."""
    if _IDENTITY.search(folded):
        return _identity(lang)
    if _VARIABLES.search(folded):
        return _variables(lang)
    if _DATA_SOURCE.search(folded):
        return _data_source(lang)
    if _PLACES.search(folded) and not has_topic:
        return _places_reply(lang)
    if has_topic:
        return None
    if folded.strip(" ?!.,") in ("ola", "alo", "holaa", "wenas", "buenass"):
        return _greeting(lang)
    if _HELP.search(folded):
        return _help(lang)
    if _HOW_ARE_YOU.search(folded):
        return _greeting(lang, asked_how=True)
    if _GREETING.search(folded) and len(folded.split()) <= 6:
        return _greeting(lang)
    if _BYE.search(folded) and len(folded.split()) <= 5:
        return _bye(lang)
    if _THANKS.search(folded) and len(folded.split()) <= 6:
        return _thanks(lang)
    return None


def _verify_lora_plan(plan: dict[str, Any], text: str, language: str, named: list[str], make_plan: Any, cue_intent: Any) -> dict[str, Any]:
    """The adapter proposes, the verified rules decide (RONDA_4 §5.2).

    Measured on the 50 reference questions the rules answer 50/50 and the adapter 40/50, and
    in the live product test it dropped "heladas en Huancayo" and a two-city comparison. A
    LoRA plan is kept only when its variable is one the student's own words point at and it
    agrees with the comparison cue; otherwise the rules plan the question, and the note says so.
    """
    if plan.get("mode") not in ("lora", "llm") or plan.get("intent") not in ("investigate", "compare"):
        return plan
    padded = " ".join(fold(text).replace("?", " ").replace("!", " ").replace(",", " ").replace(".", " ").split())
    verified = [v for v in (plan.get("variable_ids") or []) if _card(v) and _names_variable(padded, v, named)]
    wants_compare = cue_intent(text) == "compare"
    if verified and (plan.get("intent") == "compare" or not wants_compare):
        return plan
    rules = dict(make_plan(text, lang=language, use_lora=False))
    rules["note"] = (f"{plan['mode']}_overruled: it proposed {plan.get('variable_ids') or []} ({plan.get('intent')}); "
                     "the verified rules planned instead")[:160]
    return rules


def chat(message: str, *, lang: str | None = None, context: dict[str, Any] | None = None) -> dict[str, Any]:
    """One conversational turn. Stateless: the client sends the context back."""
    from .planner import _intent as cue_intent
    from .planner import _resolved_places
    from .planner import plan as make_plan

    text = (message or "").strip()
    ui_lang = lang if lang in ("es", "en") else "es"
    if not text:
        return _greeting(ui_lang)
    language = _language(text, ui_lang)
    folded = " ".join(fold(text).replace("¿", " ").replace("¡", " ").split())
    ctx = _clean_context(context)

    places = _resolved_places(text, limit=2)
    named_variables = [v for v in expand(text) if _card(v)]
    has_topic = bool(places or named_variables)

    quick = _small_talk(folded, language, has_topic=has_topic)
    if quick is not None:
        return quick

    # "What is changing in Huancayo?" — every variable, one place.
    if _SCAN.search(folded) and not named_variables:
        place = places[0] if places else ctx.get("place")
        if place:
            return _scan(place, language)

    # A method question is about statistics, not about a variable ("Kendall" is
    # also a town in Florida, so the places found do not count here).
    if _METHOD.search(folded) and not named_variables:
        return _method(text, language)

    plan = make_plan(text, lang=language)
    plan = _verify_lora_plan(plan, text, language, named_variables, make_plan, cue_intent)
    intent = plan.get("intent")

    if intent == "out_of_scope":
        return _out_of_scope(language)
    if plan.get("missing"):
        return _missing(plan, language)
    padded_question = " ".join(folded.replace("?", " ").replace("!", " ").replace(",", " ").replace(".", " ").split())
    variable_ids = [
        v for v in (plan.get("variable_ids") or [])
        if _card(v) and _names_variable(padded_question, v, named_variables)
    ]
    if intent == "define" and variable_ids:
        return _define(variable_ids[0], language)
    inherited: list[str] = []

    # The planner needs *some* word to retrieve on. "¿Y en Huancayo?" has none:
    # the variable is the one we were already talking about.
    if not named_variables and places and ctx.get("variable_id"):
        if not _CLIMATE_ONLY.search(folded):
            variable_ids = [ctx["variable_id"]]
            inherited.append("variable")
            intent = "compare" if cue_intent(text) == "compare" else "investigate"
            plan = dict(plan, intent=intent, note=None)

    if places and not variable_ids:
        return _place_briefing(places[0], language, text)

    if intent in ("investigate", "compare") and variable_ids:
        place = places[0] if places else plan.get("place")
        place_b = places[1] if len(places) > 1 else plan.get("place_b")
        if not place and ctx.get("place"):
            place = ctx["place"]
            inherited.append("place")
        if intent == "compare" and place and not place_b and ctx.get("place") and fold(ctx["place"]) != fold(place):
            place, place_b = ctx["place"], place
        variable_id = variable_ids[0]
        if not place:
            if not _is_point_variable(variable_id):
                # A global or hemispheric series needs no place at all.
                final = dict(plan, variable_ids=[variable_id], place=None, place_b=None, intent="investigate")
                reply = _t(
                    language,
                    f"Voy a investigar **{_name(variable_id, language)}**, una serie que no depende de un punto del mapa, con {_source_line(variable_id, language)}.",
                    f"I will investigate **{_name(variable_id, language)}**, a series that does not depend on a map point, with {_source_line(variable_id, language)}.",
                )
                return _base("plan", language, reply, plan=final, action="analyze",
                             context={"variable_id": variable_id}, suggestions=SUGGESTIONS[language][:3])
            return _ask_place(variable_id, language)
        final = dict(plan, variable_ids=[variable_id], place=place, place_b=place_b if intent == "compare" else None)
        if intent == "compare" and not place_b:
            final["intent"] = "investigate"
        return _plan_reply(final, language, inherited=inherited)

    # No variable and no place: maybe the corpus can still answer the question.
    docs = _knowledge(text, language, types=["glossary", "method_note", "nasa_article", "biome_profile", "paper_abstract", "region_note"], k=2)
    if docs and len(_content_words(text)) >= 1:
        body = _t(language, "Esto encontré en mis fuentes:\n", "This is what I found in my sources:\n")
        body += "\n".join("• " + _quote(d, language) for d in docs)
        body += "\n" + _t(language, "Si quieres comprobarlo con datos, dime un lugar.", "To check it against data, tell me a place.")
        return _base("knowledge", language, body, sources=[_public_source(d) for d in docs],
                     suggestions=SUGGESTIONS[language][:3])
    return _fallback(language)
