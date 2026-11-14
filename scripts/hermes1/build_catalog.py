# SI-assisted: hermes-1 (Claude Sonnet 5.5)
"""C1 - Build data/catalog/variables.json from the seed plus verified sources.

Verification policy (prompt 07):
- A field is only filled if the value was read on a page that answered HTTP 200.
- POWER parameter metadata comes from the official parameter dictionary API:
  https://power.larc.nasa.gov/api/website/metadata/parameters
- Source/splice information comes from the POWER methodology pages (cached).
- GISTEMP and NSIDC facts come from their own pages and DOIs (DataCite/Crossref).
- Anything not confirmed is written as null and listed in the report.
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hermes1.fetch_common import ROOT, fetch, write_jsonl  # noqa: E402

POWER_METADATA_URL = "https://power.larc.nasa.gov/api/website/metadata/parameters"
POWER_SOURCES_METEO = "https://power.larc.nasa.gov/docs/methodology/data/sources_meteorology/"
POWER_SOURCES_RADIATION = "https://power.larc.nasa.gov/docs/methodology/data/sources_fluxes/"
POWER_SOURCES_CLOUDS = "https://power.larc.nasa.gov/docs/methodology/data/sources_clds_aerosols/"
POWER_LIMITS_URL = "https://power.larc.nasa.gov/docs/services/api/"
GISTEMP_URL = "https://data.giss.nasa.gov/gistemp/"
GISTEMP_DOI = "10.1029/2023JD040179"
NSIDC_URL = "https://nsidc.org/data/g02135/versions/4"
NSIDC_DOI = "10.7265/a98x-0f50"

TODAY = "2026-11-14"

# ---------------------------------------------------------------------------
# Per-variable editorial content. Text is original (Hermes 1), based on the
# source documented in `source`. Definitions are <= 30 words, no jargon.
# ---------------------------------------------------------------------------

POWER_VARIABLES: dict[str, dict[str, Any]] = {
    "T2M": {
        "names": {"es": "Temperatura del aire a 2 m", "en": "Air temperature at 2 m"},
        "simple_definition": {
            "es": "Cuánto calor hace en el aire a la altura de nuestra cara, en promedio.",
            "en": "How warm the air is at the height of our face, on average.",
        },
        "what_up": {
            "es": "Puede indicar más calor acumulado, más olas de calor y noches menos frescas.",
            "en": "May point to more stored heat, more heat waves and less cool nights.",
        },
        "what_down": {
            "es": "Puede indicar enfriamiento local, más heladas o más nieve persistente.",
            "en": "May indicate local cooling, more frosts or longer-lasting snow.",
        },
        "drivers": {
            "es": ["Cambios en la radiación solar que llega", "El Niño y La Niña", "Ciudades y pérdida de vegetación", "Viento y nubosidad"],
            "en": ["Changes in incoming sunlight", "El Nino and La Nina", "Cities and loss of vegetation", "Wind and cloud cover"],
        },
        "caveats": {
            "es": [
                "Es un promedio de una rejilla de ~50 km: no distingue la cima de un cerro del valle.",
                "Los cambios en cómo se toman las observaciones pueden afectar la tendencia.",
            ],
            "en": [
                "It averages a ~50 km grid cell: it cannot tell a mountain top from the valley.",
                "Changes in how observations are made can affect the trend.",
            ],
        },
        "keywords": {
            "es": ["calor", "temperatura", "calentamiento", "bochorno", "frío", "grados", "termómetro", "verano", "invierno"],
            "en": ["heat", "temperature", "warming", "hot", "cold", "degrees", "thermometer", "summer", "winter"],
        },
    },
    "TS": {
        "names": {"es": "Temperatura de la piel terrestre", "en": "Earth skin temperature"},
        "simple_definition": {
            "es": "Cuánto calor tiene la superficie del suelo o del agua, en promedio.",
            "en": "How warm the ground or water surface is, on average.",
        },
        "what_up": {
            "es": "Puede indicar suelos más calientes, más evaporación y estrés para los cultivos.",
            "en": "May point to hotter soils, more evaporation and crop stress.",
        },
        "what_down": {
            "es": "Puede indicar suelos más fríos, más humedad retenida y heladas más probables.",
            "en": "May indicate cooler soils, more retained moisture and likelier frosts.",
        },
        "drivers": {
            "es": ["Radiación solar", "Humedad del suelo", "Tipo de cobertura del suelo", "Nubosidad"],
            "en": ["Solar radiation", "Soil moisture", "Land cover type", "Cloud cover"],
        },
        "caveats": {
            "es": ["No es la temperatura del aire: el suelo puede estar mucho más caliente al sol.", "La rejilla es de ~50 km y mezcla superficies distintas."],
            "en": ["It is not air temperature: bare soil can be much hotter in the sun.", "The ~50 km grid mixes different surfaces."],
        },
        "keywords": {
            "es": ["suelo", "superficie", "tierra caliente", "temperatura del suelo", "sequedad", "helada", "suelo desnudo", "asfalto caliente", "arena"],
            "en": ["soil", "surface", "ground heat", "skin temperature", "dryness", "frost", "bare ground", "hot asphalt", "sand"],
        },
    },
    "PRECTOTCORR": {
        "names": {"es": "Precipitación corregida", "en": "Precipitation (corrected)"},
        "simple_definition": {
            "es": "Cuánta lluvia o nieve cae al día, en promedio, con una corrección aplicada por los científicos.",
            "en": "How much rain or snow falls per day, on average, with a scientific correction applied.",
        },
        "what_up": {
            "es": "Puede indicar temporadas más lluviosas, más riesgo de inundaciones y recarga de acuíferos.",
            "en": "May point to wetter seasons, more flood risk and aquifer recharge.",
        },
        "what_down": {
            "es": "Puede indicar sequías más frecuentes, menos agua para cultivos y ciudades.",
            "en": "May indicate more frequent droughts and less water for farms and cities.",
        },
        "drivers": {
            "es": ["El Niño y La Niña", "Humedad que llega del océano", "Relieve de montañas", "Cambios en los vientos"],
            "en": ["El Nino and La Nina", "Moisture arriving from the ocean", "Mountain relief", "Changes in winds"],
        },
        "caveats": {
            "es": [
                "La lluvia es muy variable de un año a otro: hacen falta muchas décadas para ver una tendencia clara.",
                "En zonas de montaña la rejilla suaviza los máximos locales.",
            ],
            "en": [
                "Rain varies a lot from year to year: many decades are needed to see a clear trend.",
                "In mountains the grid smooths out local extremes.",
            ],
        },
        "keywords": {
            "es": ["lluvia", "llover", "precipitación", "sequía", "garúa", "aguacero", "inundación", "nieve", "temporada"],
            "en": ["rain", "rainfall", "precipitation", "drought", "shower", "flood", "snow", "wet season"],
        },
    },
    "GWETTOP": {
        "names": {"es": "Humedad de la capa superior del suelo", "en": "Surface soil wetness"},
        "simple_definition": {
            "es": "Qué tan mojada está la primera capa del suelo, de 0 (seco) a 1 (saturado).",
            "en": "How wet the top layer of soil is, from 0 (dry) to 1 (saturated).",
        },
        "what_up": {
            "es": "Puede indicar suelos más húmedos, mejor crecimiento de plantas y menos polvo.",
            "en": "May point to wetter soils, better plant growth and less dust.",
        },
        "what_down": {
            "es": "Puede indicar suelos más secos, más polvo en el aire y estrés hídrico.",
            "en": "May indicate drier soils, more airborne dust and water stress.",
        },
        "drivers": {
            "es": ["Lluvia", "Evaporación", "Tipo de suelo", "Riego y uso del territorio"],
            "en": ["Rainfall", "Evaporation", "Soil type", "Irrigation and land use"],
        },
        "caveats": {
            "es": ["Solo representa la capa más superficial, no toda la reserva de agua del suelo.", "Los suelos arenosos y arcillosos retienen el agua de forma distinta."],
            "en": ["It only represents the topmost layer, not all soil water storage.", "Sandy and clay soils hold water differently."],
        },
        "keywords": {
            "es": ["humedad", "suelo mojado", "sequedad", "polvo", "agricultura", "reserva de agua", "riego", "tierra seca", "barro"],
            "en": ["moisture", "wet soil", "dryness", "dust", "agriculture", "water storage", "irrigation", "dry earth", "mud"],
        },
    },
    "EVLAND": {
        "names": {"es": "Evaporación sobre la tierra", "en": "Evaporation over land"},
        "simple_definition": {
            "es": "Cuánta agua pasa del suelo y las plantas al aire al día, en promedio.",
            "en": "How much water moves from soil and plants into the air per day, on average.",
        },
        "what_up": {
            "es": "Puede indicar más calor o más vegetación activa, y suelos que se secan antes.",
            "en": "May point to more heat or more active vegetation, and soils that dry sooner.",
        },
        "what_down": {
            "es": "Puede indicar menos agua disponible o menos vegetación activa.",
            "en": "May indicate less available water or less active vegetation.",
        },
        "drivers": {
            "es": ["Temperatura", "Humedad del suelo", "Cobertura vegetal", "Viento"],
            "en": ["Temperature", "Soil moisture", "Vegetation cover", "Wind"],
        },
        "caveats": {
            "es": ["Incluye la evaporación del suelo y la transpiración de las plantas juntas.", "Difícil de medir directamente: es una estimación del modelo."],
            "en": ["It combines soil evaporation and plant transpiration.", "Hard to measure directly: it is a model estimate."],
        },
        "keywords": {
            "es": ["evaporación", "transpiración", "humedad del aire", "secado", "plantas", "bosque", "cultivo", "suelo que se seca", "riego"],
            "en": ["evaporation", "transpiration", "air humidity", "drying", "plants", "forest", "crop", "soil drying", "irrigation"],
        },
    },
    "SNODP": {
        "names": {"es": "Profundidad de la nieve", "en": "Snow depth"},
        "simple_definition": {
            "es": "Qué tan gruesa es la capa de nieve en el suelo, en centímetros.",
            "en": "How thick the snow layer on the ground is, in centimetres.",
        },
        "what_up": {
            "es": "Puede indicar más nieve acumulada, más agua disponible al derretirse y riesgo de avalanchas.",
            "en": "May point to more stored snow, more water at melt time and avalanche risk.",
        },
        "what_down": {
            "es": "Puede indicar inviernos con menos nieve y menos agua de deshielo para los ríos.",
            "en": "May indicate snow-poor winters and less meltwater for rivers.",
        },
        "drivers": {
            "es": ["Temperatura", "Precipitación", "Altura de la montaña", "Viento que arrastra la nieve"],
            "en": ["Temperature", "Precipitation", "Mountain elevation", "Wind that moves snow"],
        },
        "caveats": {
            "es": ["La nieve puede caer y derretirse en pocos días: mira también las medias anuales.", "El relieve abrupto se suaviza en la rejilla."],
            "en": ["Snow can fall and melt within days: also look at annual means.", "Steep relief gets smoothed in the grid."],
        },
        "keywords": {
            "es": ["nieve", "nevada", "glaciar", "montaña", "deshielo", "invierno", "andino", "copos", "ventisquero", "puna"],
            "en": ["snow", "snowfall", "glacier", "mountain", "melt", "winter", "Andes", "snowflakes", "snowpack", "highlands"],
        },
    },
    "RH2M": {
        "names": {"es": "Humedad relativa a 2 m", "en": "Relative humidity at 2 m"},
        "simple_definition": {
            "es": "Qué parte del aire está cargada de vapor de agua, en porcentaje.",
            "en": "How much of the air's capacity for water vapour is filled, as a percentage.",
        },
        "what_up": {
            "es": "Puede indicar aire más húmedo, más niebla y una sensación de bochorno mayor.",
            "en": "May point to more humid air, more fog and a stronger muggy feeling.",
        },
        "what_down": {
            "es": "Puede indicar aire más seco, más sed en plantas y más riesgo de incendios.",
            "en": "May indicate drier air, more plant water stress and higher fire risk.",
        },
        "drivers": {
            "es": ["Temperatura", "Evaporación del mar y del suelo", "Viento", "Lluvia"],
            "en": ["Temperature", "Evaporation from sea and soil", "Wind", "Rainfall"],
        },
        "caveats": {
            "es": ["Depende de la temperatura: el mismo vapor da humedad relativa distinta según el calor.", "No dice cuánta agua hay en toda la columna del aire."],
            "en": ["It depends on temperature: the same vapour gives different relative humidity with heat.", "It does not tell how much water is in the whole air column."],
        },
        "keywords": {
            "es": ["humedad", "bochorno", "niebla", "garúa", "aire húmedo", "sequedad", "vapor", "sudor", "sensación térmica"],
            "en": ["humidity", "muggy", "fog", "damp air", "dryness", "vapour", "mist", "sweat", "heat index"],
        },
    },
    "TQV": {
        "names": {"es": "Agua precipitable en la columna", "en": "Total column precipitable water"},
        "simple_definition": {
            "es": "Cuánta agua cabría en toda la columna de aire encima de un lugar, en kg/m².",
            "en": "How much water the whole air column above a place holds, in kg/m².",
        },
        "what_up": {
            "es": "Puede indicar más vapor disponible para lluvias intensas.",
            "en": "May point to more vapour available for heavy rainfall.",
        },
        "what_down": {
            "es": "Puede indicar aire más seco en toda la columna.",
            "en": "May indicate a drier air column overall.",
        },
        "drivers": {
            "es": ["Temperatura del mar", "Evaporación", "Vientos que traen humedad", "Frentes y tormentas"],
            "en": ["Sea temperature", "Evaporation", "Winds that bring moisture", "Fronts and storms"],
        },
        "caveats": {
            "es": ["Tener mucho vapor no garantiza lluvia: hace falta que el aire suba.", "Es una medida de la columna completa, no de lo que sientes en el suelo."],
            "en": ["Plenty of vapour does not guarantee rain: the air must rise.", "It measures the whole column, not what you feel at the ground."],
        },
        "keywords": {
            "es": ["vapor de agua", "humedad de la atmósfera", "agua precipitable", "lluvia intensa", "nubes", "columna de agua", "aire cargado", "tormenta"],
            "en": ["water vapour", "atmospheric moisture", "precipitable water", "heavy rain", "clouds", "water column", "loaded air", "storm"],
        },
    },
    "TO3": {
        "names": {"es": "Ozono total en la columna", "en": "Total column ozone"},
        "simple_definition": {
            "es": "Cuánto ozono hay en toda la columna de aire, en unidades Dobson.",
            "en": "How much ozone the whole air column holds, in Dobson units.",
        },
        "what_up": {
            "es": "Puede indicar mejor protección contra la radiación ultravioleta.",
            "en": "May point to better protection against ultraviolet radiation.",
        },
        "what_down": {
            "es": "Puede indicar menos protección ultravioleta y más riesgo para la piel.",
            "en": "May indicate less ultraviolet protection and more skin risk.",
        },
        "drivers": {
            "es": ["Circulación estratosférica", "Temperatura de la estratosfera", "Productos químicos que destruyen el ozono"],
            "en": ["Stratospheric circulation", "Stratospheric temperature", "Ozone-depleting chemicals"],
        },
        "caveats": {
            "es": ["El ozono sube y baja con las estaciones y con los vientos, no solo con la contaminación.", "Los satélites y el modelo pueden no coincidir en los polos."],
            "en": ["Ozone rises and falls with seasons and winds, not only with pollution.", "Satellites and the model may disagree near the poles."],
        },
        "keywords": {
            "es": ["ozono", "capa de ozono", "ultravioleta", "sol", "estratosfera", "agujero de ozono", "radiación UV", "protector solar"],
            "en": ["ozone", "ozone layer", "ultraviolet", "sun", "stratosphere", "ozone hole", "UV radiation", "sunscreen"],
        },
    },
    "AOD_55": {
        "names": {"es": "Espesor óptico de aerosoles (0,55 µm)", "en": "Aerosol optical depth (0.55 µm)"},
        "simple_definition": {
            "es": "Cuánta luz solar bloquean las partículas suspendidas en el aire.",
            "en": "How much sunlight is blocked by particles suspended in the air.",
        },
        "what_up": {
            "es": "Puede indicar más humo, polvo o contaminación y menos luz que llega al suelo.",
            "en": "May point to more smoke, dust or pollution and less light reaching the ground.",
        },
        "what_down": {
            "es": "Puede indicar aire más limpio y más luz solar directa.",
            "en": "May indicate cleaner air and more direct sunlight.",
        },
        "drivers": {
            "es": ["Incendios y humo", "Polvo levantado por el viento", "Emisiones urbanas e industriales", "Aerosoles marinos y volcánicos"],
            "en": ["Fires and smoke", "Wind-blown dust", "Urban and industrial emissions", "Sea-salt and volcanic aerosols"],
        },
        "caveats": {
            "es": [
                "Empieza en 2001-01 en POWER (CERES SYN1deg): antes de esa fecha no hay serie comparable.",
                "Un cielo nublado puede dificultar la lectura del aerosol desde el satélite.",
            ],
            "en": [
                "It starts in 2001-01 in POWER (CERES SYN1deg): there is no comparable record before that.",
                "A cloudy sky can make satellite aerosol retrievals harder.",
            ],
        },
        "keywords": {
            "es": ["aerosoles", "humo", "polvo", "contaminación", "smog", "bruma", "calima", "incendio", "partículas", "aire sucio"],
            "en": ["aerosols", "smoke", "dust", "pollution", "smog", "haze", "wildfire", "particles", "dirty air", "air quality"],
        },
    },
    "CLOUD_AMT": {
        "names": {"es": "Cantidad de nubes", "en": "Cloud amount"},
        "simple_definition": {
            "es": "Qué porcentaje del cielo está cubierto por nubes, en promedio.",
            "en": "What share of the sky is covered by clouds, on average.",
        },
        "what_up": {
            "es": "Puede indicar más días nublados, menos sol directo y temperaturas máximas más bajas.",
            "en": "May point to more cloudy days, less direct sun and lower daytime highs.",
        },
        "what_down": {
            "es": "Puede indicar cielos más despejados y más radiación solar en la superficie.",
            "en": "May indicate clearer skies and more solar radiation at the surface.",
        },
        "drivers": {
            "es": ["Humedad del aire", "Circulación atmosférica", "Temperatura del mar", "Aerosoles"],
            "en": ["Air humidity", "Atmospheric circulation", "Sea temperature", "Aerosols"],
        },
        "caveats": {
            "es": [
                "Empalme de fuentes: SRB hasta 2000 y CERES SYN1deg desde 2001; analiza en dos tramos.",
                "Una rejilla de ~100 km no capta la nubosidad de un valle concreto.",
            ],
            "en": [
                "Source splice: SRB up to 2000 and CERES SYN1deg from 2001; analyse in two stretches.",
                "A ~100 km grid cannot capture the cloudiness of a single valley.",
            ],
        },
        "keywords": {
            "es": ["nubes", "nubosidad", "cielo", "días nublados", "sol", "neblina", "cielo cubierto", "nublado"],
            "en": ["clouds", "cloud cover", "sky", "cloudy days", "sun", "overcast", "cloudiness", "grey sky"],
        },
    },
    "ALLSKY_SFC_SW_DWN": {
        "names": {"es": "Radiación solar de onda corta en superficie", "en": "Surface shortwave downward irradiance"},
        "simple_definition": {
            "es": "Cuánta energía del Sol llega a una superficie horizontal, al día.",
            "en": "How much solar energy reaches a horizontal surface per day.",
        },
        "what_up": {
            "es": "Puede indicar menos nubes o partículas, y más energía para plantas y paneles solares.",
            "en": "May point to fewer clouds or particles, and more energy for plants and solar panels.",
        },
        "what_down": {
            "es": "Puede indicar más nubes, más humo o más polvo bloqueando el sol.",
            "en": "May indicate more clouds, smoke or dust blocking the sun.",
        },
        "drivers": {
            "es": ["Nubosidad", "Aerosoles", "Temporada y latitud", "Bruma y humo"],
            "en": ["Cloudiness", "Aerosols", "Season and latitude", "Haze and smoke"],
        },
        "caveats": {
            "es": [
                "Empalme de fuentes: SRB 1984-2000 y CERES SYN1deg desde 2001; una tendencia a través del empalme puede ser artificial.",
                "Rejilla nativa de 1°: no sirve para diseñar un panel solar concreto.",
            ],
            "en": [
                "Source splice: SRB 1984-2000 and CERES SYN1deg from 2001; a trend across the splice may be artificial.",
                "Native 1° grid: it is not enough to design a single solar panel.",
            ],
        },
        "keywords": {
            "es": ["radiación", "sol", "energía solar", "insolación", "luz", "nublado", "panel solar", "irradiancia", "energía renovable"],
            "en": ["radiation", "sun", "solar energy", "insolation", "sunlight", "cloudy", "solar panel", "irradiance", "renewable energy"],
        },
    },
}

FIXED_VARIABLES: dict[str, dict[str, Any]] = {
    "GISTEMP_TANOM": {
        "names": {"es": "Anomalía de temperatura global (GISTEMP)", "en": "Global temperature anomaly (GISTEMP)"},
        "simple_definition": {
            "es": "Cuánto más caliente o frío está el planeta que el promedio de 1951 a 1980.",
            "en": "How much warmer or cooler the planet is than the 1951-1980 average.",
        },
        "what_up": {
            "es": "Puede indicar calentamiento global acumulado.",
            "en": "May indicate accumulated global warming.",
        },
        "what_down": {
            "es": "Puede indicar un año globalmente más frío, normalmente por erupciones o La Niña.",
            "en": "May indicate a globally cooler year, usually from eruptions or La Nina.",
        },
        "drivers": {
            "es": ["Gases de efecto invernadero", "El Niño y La Niña", "Erupciones volcánicas", "Variabilidad solar"],
            "en": ["Greenhouse gases", "El Nino and La Nina", "Volcanic eruptions", "Solar variability"],
        },
        "caveats": {
            "es": ["Es un promedio global: no dice nada de una ciudad concreta.", "Cambios en las estaciones de medición introducen incertidumbre."],
            "en": ["It is a global average: it says nothing about one city.", "Changes in station coverage introduce uncertainty."],
        },
        "keywords": {
            "es": ["calentamiento global", "anomalía", "temperatura media", "planeta", "cambio climático", "clima", "grados de calentamiento", "serie global"],
            "en": ["global warming", "anomaly", "mean temperature", "planet", "climate change", "climate", "warming degrees", "global series"],
        },
    },
    "SEAICE_EXTENT_N": {
        "names": {"es": "Extensión del hielo marino del Ártico", "en": "Arctic sea ice extent"},
        "simple_definition": {
            "es": "Cuánta superficie del océano Ártico está cubierta al menos en un 15 % por hielo.",
            "en": "How much of the Arctic Ocean is at least 15 % covered by ice.",
        },
        "what_up": {
            "es": "Puede indicar un año de hielo más extendido, típico de inviernos muy fríos.",
            "en": "May point to a more extensive ice year, typical of very cold winters.",
        },
        "what_down": {
            "es": "Puede indicar hielo en retroceso, más agua abierta y más absorción de calor.",
            "en": "May indicate retreating ice, more open water and more heat absorption.",
        },
        "drivers": {
            "es": ["Temperatura del aire y del mar", "Vientos y corrientes", "Cobertura de nieve", "Nubes de verano"],
            "en": ["Air and sea temperature", "Winds and currents", "Snow cover", "Summer clouds"],
        },
        "caveats": {
            "es": ["Septiembre marca el mínimo anual: compare siempre el mismo mes.", "La extensión no es el volumen del hielo."],
            "en": ["September is the yearly minimum: always compare the same month.", "Extent is not ice volume."],
        },
        "keywords": {
            "es": ["hielo marino", "ártico", "deshielo", "océano", "glaciación", "invierno polar", "casquete", "polo norte"],
            "en": ["sea ice", "Arctic", "melting", "ocean", "freezing", "polar winter", "ice cap", "north pole"],
        },
    },
    "SEAICE_EXTENT_S": {
        "names": {"es": "Extensión del hielo marino del Antártico", "en": "Antarctic sea ice extent"},
        "simple_definition": {
            "es": "Cuánta superficie del océano Antártico está cubierta al menos en un 15 % por hielo.",
            "en": "How much of the Southern Ocean is at least 15 % covered by ice.",
        },
        "what_up": {
            "es": "Puede indicar más hielo alrededor de la Antártida, típico de vientos y mares fríos.",
            "en": "May point to more ice around Antarctica, typical of cold winds and seas.",
        },
        "what_down": {
            "es": "Puede indicar pérdida de hielo antártico y más calor en el océano austral.",
            "en": "May indicate Antarctic ice loss and more heat in the Southern Ocean.",
        },
        "drivers": {
            "es": ["Vientos del oeste", "Temperatura del océano", "Circulación del mar de Weddell", "Nieve sobre el hielo"],
            "en": ["Westerly winds", "Ocean temperature", "Weddell Sea circulation", "Snow on the ice"],
        },
        "caveats": {
            "es": ["Febrero es el mínimo anual del Antártico, al revés que en el Ártico.", "Las tendencias antárticas han cambiado de signo en las últimas décadas."],
            "en": ["February is the Antarctic yearly minimum, the opposite of the Arctic.", "Antarctic trends have changed sign in recent decades."],
        },
        "keywords": {
            "es": ["hielo marino", "antártida", "polo sur", "deshielo", "océano austral", "pingüinos", "glaciar antártico", "invierno austral"],
            "en": ["sea ice", "Antarctica", "south pole", "melting", "Southern Ocean", "penguins", "antarctic glacier", "austral winter"],
        },
    },
}


def load_seed() -> dict[str, Any]:
    path = os.path.join(ROOT, "data", "catalog", "variables.seed.json")
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def load_power_metadata() -> tuple[dict[str, dict], str]:
    page = fetch(POWER_METADATA_URL, cache_key="power_parameter_dictionary")
    data = json.loads(page.text)
    by_id = {item["id"]: item for item in data if isinstance(item, dict) and item.get("id")}
    return by_id, page.final_url


def build_power_source(pid: str, seed: dict, power_meta: dict[str, dict], urls: dict[str, str]) -> dict[str, Any]:
    meta = power_meta.get(pid, {})
    sources = meta.get("sources") or []
    start = (meta.get("range") or {}).get("start")
    start_month = start[:7].replace("/", "-") if start else seed.get("start")

    if pid in ("CLOUD_AMT", "ALLSKY_SFC_SW_DWN"):
        model = "CERES SYN1deg (with GEWEX SRB for 1984-2000)"
        instrument = "CERES"
        homogeneous = "2001-01"
        url = urls["power_fluxes"]
    elif pid == "AOD_55":
        model = "CERES SYN1deg"
        instrument = "CERES"
        homogeneous = None
        url = urls["power_clouds"]
    else:
        model = "MERRA-2"
        instrument = None
        homogeneous = seed.get("homogeneous_since")
        url = urls["power_meteo"]

    return {
        "model_or_mission": model,
        "instrument": instrument,
        "via": "NASA POWER",
        "challenge_named_source": "MERRA-2" if model == "MERRA-2" else "other",
        "native_resolution": "0.5 x 0.625 degrees" if model == "MERRA-2" else "1 x 1 degree",
        "start": start_month,
        "homogeneous_since": homogeneous,
        "doi": None,
        "url": url,
        "_power_declared_sources": sources,
    }


def build_catalog() -> dict[str, Any]:
    seed = load_seed()
    power_meta, dictionary_url = load_power_metadata()

    # Verify the methodology pages we cite answer 200 in this same run.
    urls = {
        "power_meteo": fetch(POWER_SOURCES_METEO, cache_key="power_docs_meteorology").final_url,
        "power_fluxes": fetch(POWER_SOURCES_RADIATION, cache_key="power_docs_fluxes").final_url,
        "power_clouds": fetch(POWER_SOURCES_CLOUDS, cache_key="power_docs_clouds").final_url,
        "power_api": fetch(POWER_LIMITS_URL, cache_key="power_docs_api").final_url,
        "gistemp": fetch(GISTEMP_URL, cache_key="gistemp_home").final_url,
        "nsidc": fetch(NSIDC_URL, cache_key="nsidc_g02135_v4").final_url,
    }

    cards: list[dict[str, Any]] = []

    for entry in seed["live"]:
        pid = entry["id"]
        if entry["connector"] == "power":
            if pid not in POWER_VARIABLES:
                raise SystemExit(f"missing editorial content for POWER variable {pid}")
            content = POWER_VARIABLES[pid]
            source = build_power_source(pid, entry, power_meta, urls)
            card = {
                "id": pid,
                "connector": "power",
                "connector_param": entry["connector_param"],
                "names": content["names"],
                "simple_definition": content["simple_definition"],
                "unit": entry["unit"],
                "ratio_scale": entry["ratio_scale"],
                "sphere": entry["sphere"],
                "source": source,
                "what_up_means": content["what_up"],
                "what_down_means": content["what_down"],
                "typical_drivers": content["drivers"],
                "caveats": content["caveats"],
                "keywords": content["keywords"],
                "verified": {"by": "hermes-1", "at": TODAY, "evidence_url": dictionary_url},
            }
            cards.append(card)
        elif pid in FIXED_VARIABLES:
            content = FIXED_VARIABLES[pid]
            if pid == "GISTEMP_TANOM":
                source = {
                    "model_or_mission": "GISTEMP v4 (GHCN v4 stations + ERSST v5 ocean)",
                    "instrument": None,
                    "via": "NASA GISS",
                    "challenge_named_source": "other",
                    "native_resolution": "1200 km smoothing grid (netCDF GISTEMP1200)",
                    "start": "1880-01",
                    "homogeneous_since": None,
                    "doi": GISTEMP_DOI,
                    "url": urls["gistemp"],
                }
            else:
                north = pid == "SEAICE_EXTENT_N"
                source = {
                    "model_or_mission": "Sea Ice Index Version 4",
                    "instrument": "Nimbus-7 SMMR and DMSP SSM/I-SSMIS passive microwave",
                    "via": "NSIDC",
                    "challenge_named_source": "other",
                    "native_resolution": "25 km passive-microwave grid",
                    "start": "1978-11",
                    "homogeneous_since": None,
                    "doi": NSIDC_DOI,
                    "url": urls["nsidc"],
                }
            cards.append(
                {
                    "id": pid,
                    "connector": entry["connector"],
                    "connector_param": entry["connector_param"],
                    "names": content["names"],
                    "simple_definition": content["simple_definition"],
                    "unit": entry["unit"],
                    "ratio_scale": entry["ratio_scale"],
                    "sphere": entry["sphere"],
                    "source": source,
                    "what_up_means": content["what_up"],
                    "what_down_means": content["what_down"],
                    "typical_drivers": content["drivers"],
                    "caveats": content["caveats"],
                    "keywords": content["keywords"],
                    "verified": {"by": "hermes-1", "at": TODAY, "evidence_url": source["url"]},
                }
            )
        else:
            raise SystemExit(f"no content for live variable {pid}")

    return {"schema": "catalog/2", "generated_at": TODAY, "variables": cards}


def main() -> int:
    catalog = build_catalog()
    out = os.path.join(ROOT, "data", "catalog", "variables.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(catalog, fh, ensure_ascii=False, indent=2)
    print(f"wrote {out} with {len(catalog['variables'])} variables")
    for card in catalog["variables"]:
        src = card["source"]
        print(f"  {card['id']:22s} start={src['start']:8s} homo={str(src['homogeneous_since']):8s} doi={src['doi']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
