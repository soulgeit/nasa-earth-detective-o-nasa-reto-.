#!/usr/bin/env python3
"""Genera documentos JSON para regions/ica.jsonl — carril rag-ica, Ronda 7."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data" / "knowledge" / "regions" / "ica.jsonl"

ts = "2026-11-15T15:00:00Z"
now = ts

def doc(id_suffix, title, text, publisher, url, variables=None, date=None, lang="es",
        is_quotation=False, summary_by="rag-ica", license_text="Gobierno del Perú — información pública",
        supersedes=None):
    text = text.strip()
    return {
        "id": f"region-ica-{id_suffix}",
        "type": "region_note" if is_quotation is False else "region_note",
        "title": title,
        "url": url,
        "publisher": publisher,
        "date": date,
        "lang": lang,
        "text": text,
        "places": ["ica"],
        "variables": variables or [],
        "license": license_text,
        "fetched_at": ts,
        "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
        "is_quotation": is_quotation,
        "summary_by": summary_by,
    }

docs = []

# ============================================================
# TEMA 1: Ubicación, altitud, relieve, cuenca (3 docs)
# ============================================================

docs.append(doc(
    "ubicacion-region",
    "Ubicación geográfica y población de la región Ica, Perú",
    "La región Ica se ubica en la costa sur del Perú, entre los 12°30' y 15°30' de latitud sur y los 74°50' y 76°30' de longitud oeste. Limita al norte con la región Lima, al este con Huancavelica y Ayacucho, al sur con Arequipa y al oeste con el océano Pacífico. Su superficie es de 21 328 km², equivalente al 1,76 % del territorio nacional (OECD, 2023). Según el censo 2017 del INEI, la región tiene 893 292 habitantes; la capital, ciudad de Ica, concentra 155 247 habitantes. Está dividida en cinco provincias: Ica, Chincha, Nasca, Palpa y Pisco. La altitud de la capital es de 406 m.s.n.m., mientras que los Andes sobrepasan los 4 500 m en la cuenca alta del río Ica (citypopulation.de; INEI 2017; OECD 2023).",
    "INEI / OECD / citypopulation.de",
    "https://citypopulation.de/en/peru/admin/11__ica",
    date="2017",
    variables=[]
))

docs.append(doc(
    "cuenca-rio-ica",
    "Cuenca del río Ica: extensión, cauce y desembocadura",
    "El río Ica tiene una longitud de 220 km y una cuenca de 7 711 km² que se extiende entre los 13°28' y 14°53' S y los 74°58' y 75°54' O, desde el nivel del mar hasta los 4 503 m en el cerro Huayhuano. Nace de la confluencia de los ríos Tambo y Jatunchaca en Huancavelica y desemboca en el Mar de Grau, distrito de Santiago. Su cuenca propia abarca 7 711 km², de los cuales 2 234 km² están por encima de los 2 500 m. La pendiente promedio es de 5 %, con sectores de hasta 10 % en las quebradas Capillas y Huacceyoc. Recibe aportes de las quebradas Huacceyoc, Tombillos, Trapiche, Cansas, Yauca del Rosario y Tingue (Wikipedia; UNALM repositorio; OECD).",
    "OECD / Wikipedia / UNALM",
    "https://es.wikipedia.org/wiki/R%C3%ADo_Ica",
    variables=[],
    date="2024"
))

docs.append(doc(
    "sistema-choclococha",
    "Sistema Choclococha: trasvase de aguas entre vertientes",
    "El sistema Choclococha constituye la segunda fuente de agua del valle de Ica. Los lagos Ccaracocha y Choclococha se encuentran en la cuenca alta del río Pampas, vertiente del Atlántico, y sus aguas son derivadas hacia la vertiente del Pacífico mediante un túnel transandino. El sistema aporta un caudal medio de 1,81 m³/s (57,08 MMC anuales) al valle de Ica. El volmen de embalse se estima en 80 130 hm³, con un déficit estimado de 370 hm³ reportado por la ANA en 2017. Esta infraestructura permite que el río Ica transporte aguas trasandinas durante los meses de septiembre a noviembre para riego (OECD 2023; ANA 2017; CooperAcción 2018).",
    "ANA / OECD / CooperAcción",
    "https://oecd-ilibrary.org/sites/ca151863-en?itemId=/content/component/ca151863-en",
    variables=[],
    date="2017"
))

# ============================================================
# TEMA 2: Temperatura (4 docs)
# ============================================================

docs.append(doc(
    "temperatura-normales-senamhi",
    "Normales térmicas de Ica (1991-2020) según SENAMHI San Camilo",
    "Las normales de temperatura para la ciudad de Ica (1991-2020), registradas en la estación SENAMHI de San Camilo a unos 3 km del centro, muestran una amplitud térmica notable: la temperatura media mensual oscila entre 18,3 °C en julio (mes más frío) y 22,9 °C en febrero (mes más cálido). Las máximas medias alcanzan 32,1 °C en febrero, mientras las mínimas bajan a 11,0 °C en julio. La temperatura media anual es de 20,8 °C. El régimen térmico responde a un clima desértico subtropical con invierno fresco y verano cálido, típico de la costa sur peruana (climate-zone.com basándose en SENAMHI 1991-2020).",
    "SENAMHI / climate-zone.com",
    "https://www.climate-zone.com/climate/pe/ica",
    variables=["T2M"],
    date="2020"
))

docs.append(doc(
    "temperatura-extremos-ica",
    "Temperaturas extremas y variabilidad en el valle de Ica",
    "En el valle de Ica, la temperatura mínima absoluta registrada puede superar las heladas raras en la zona baja pero ser frecuente en los sectores altos a más de 1 500 m. La temperatura media máxima mensual no supera los 32 °C en la capital, pero en las pampa deserticas adyacentes (Pampa de Villacurí, Pampa de los Castillos) la temperatura de superficie (TS) puede exceder los 45 °C en verano debido a la baja humedad y la exposición directa. La evapotranspiración potencial es muy alta, lo que intensifica el estrés hídrico en cultivos. Los valores de T2M de NASA POWER para la celda 0,5° × 0,625° centrada en Ica (-14,07°, -75,73°) confirman esta tendencia (NASA POWER API).",
    "NASA POWER",
    "https://power.larc.nasa.gov/docs/services/api/temporal/climatology",
    variables=["T2M", "TS"],
    date="2024"
))

docs.append(doc(
    "temperatura-sazonal",
    "Ciclo estacional de la temperatura en Ica",
    "El ciclo estacional térmico en Ica presenta un máximo en febrero-marzo (22-23 °C media) y un mínimo en julio-agosto (18-19 °C). La amplitud térmica intermensual es de aproximadamente 4-5 °C en promedio, pero la amplitud diurna puede superar los 15 °C en días despejados. Los vientos Paracas, que soplan del sur-sureste en la tarde, contribuyen a moderar las temperaturas en enero-febrero. La nubosidad, que alcanza su máximo en enero-febrero (58-60 % según NASA POWER), atenúa ligeramente las máximas en verano, mientras que en junio-agosto el cielo despejado (>75 % de días despejados) produce inviernos frescos con heladas radiativas en zonas altas del departamento (climate-zone.com / NASA POWER).",
    "SENAMHI / NASA POWER",
    "https://www.climate-zone.com/methodology",
    variables=["T2M"],
    date="2020"
))

docs.append(doc(
    "temperatura-en",
    "Temperature normals for Ica, Peru (1991-2020)",
    "The 1991-2020 temperature normals for Ica city, measured at the SENAMHI station in San Camilo (approximately 3 km from downtown), show a notable thermal amplitude: mean monthly temperature ranges from 18.3 °C in July (coldest month) to 22.9 °C in February (warmest month). Mean maximums reach 32.1 °C in February, while minimums drop to 11.0 °C in July. The annual mean temperature is 20.8 °C. The thermal regime responds to a subtropical desert climate with cool winters and warm summers, characteristic of southern Peruvian coast (climate-zone.com based on SENAMHI 1991-2020).",
    "SENAMHI / climate-zone.com",
    "https://www.climate-zone.com/climate/pe/ica",
    variables=["T2M"],
    date="2020",
    lang="en"
))

# ============================================================
# TEMA 3: Lluvia (4 docs)
# ============================================================

docs.append(doc(
    "precipitacion-anual-ica",
    "Precipitación anual mínima en Ica: el desierto más seco del mundo habitado",
    "Ica recibe menos de 5 mm de lluvia al año, lo que la convierte en una de las ciudades más áridas del mundo. La precipitación se concentra entre diciembre y marzo, meses de verano, con enero como el mes más lluvioso (0,2 pulgadas ≈ 5 mm). El resto del año puede registrar cero precipitación durante meses consecutivos. Esta aridez extrema responde a la influencia de la corriente de Humboldt, la inversión térmica y la barrera andina que bloquea la humedad amazónica. Las estaciones hidrometeorológicas de SENAMHI y la reanálisis MERRA-2 de NASA POWER confirman estos valores mínimos (climate-zone.com; SENAMHI DZ 5 Ica).",
    "SENAMHI / climate-zone.com",
    "https://www.senamhi.gob.pe/main.php?dp=ica&p=monitoreo-decadal-precipitacion",
    variables=["PRECTOTCORR"],
    date="2020"
))

docs.append(doc(
    "estacionalidad-lluvias",
    "Estacionalidad de lluvias en Ica y riesgo de inundación",
    "La precipitación en Ica es altamente estacional: más del 90 % de la lluvia anual ocurre entre diciembre y marzo. En condiciones normales, los totales mensuales son inferiores a 1 mm en la mayoría de meses, con apenas 0,2 pulgadas (≈5 mm) en enero. Sin embargo, durante eventos de El Niño Costero, las precipitaciones pueden superar varios cientos de mm en días, como ocurrió en 2017. La baja infiltración natural del suelo desértico y la ausencia de vegetación hacen que cualquier lluvia significativa genere escorrentía rápida y huaicos en las quebradas. El SENAMHI monitorea la precipitación decadal a través del sistema MIDAS (MIDAS; SENAMHI).",
    "SENAMHI / MIDAS",
    "https://www.senamhi.gob.pe/main.php?dp=ica&p=monitoreo-decadal-precipitacion",
    variables=["PRECTOTCORR"],
    date="2024"
))

docs.append(doc(
    "precipitacion-power",
    "Precipitación de NASA POWER para Ica: datos MERRA-2",
    "Los datos de precipitación corregida (PRECTOTCORR) de NASA POWER para el punto -14,07°, -75,73° (MERRA-2, resolución 0,5° × 0,625°) muestran un promedio anual inferior a 3 mm en el valle de Ica, con un pico en los meses de verano (enero-febrero) que no supera los 0,5 mm/día en promedio. El índice de variabilidad interanual es muy alto: los años húmedos pueden registrar hasta 20 mm anuales, mientras que los años secos pueden ser prácticamente cero. Los datos están disponibles para series temporales diarias, mensuales y climatológicas a través de la API de POWER (NASA POWER Power Data Access Viewer).",
    "NASA POWER",
    "https://power.larc.nasa.gov/docs/services/api/temporal/climatology",
    variables=["PRECTOTCORR"],
    date="2024"
))

docs.append(doc(
    "precipitacion-en",
    "Precipitation in Ica: extreme aridity and seasonal risk",
    "Ica receives less than 5 mm of rain per year, making it one of the driest cities in the world. Precipitation is highly seasonal, with over 90 % of annual rainfall occurring between December and March. In normal conditions, monthly totals are under 1 mm in most months, with only about 5 mm in January. However, during Coastal El Niño events, precipitation can exceed several hundred mm in a few days, as occurred in 2017. The extremely low infiltration capacity of the desert soil and the absence of vegetation cause rapid surface runoff during any significant rainfall event (climate-zone.com; SENAMHI).",
    "SENAMHI / climate-zone.com",
    "https://www.climate-zone.com/climate/pe/ica",
    variables=["PRECTOTCORR"],
    date="2020",
    lang="en"
))

# ============================================================
# TEMA 4: Extremos — huaicos (5 docs)
# ============================================================

docs.append(doc(
    "huaicos-cansas",
    "Quebrada Cansas y riesgo de huaicos en la ciudad de Ica",
    "La quebrada Cansas es el principal peligro de huaico (flujo de detritos) para la ciudad de Ica. En 1998, una lluvia torrencial de tres horas generó huaicos que destruyeron el pueblo de San José de los Molinos y causaron inundaciones en Chanchajalla y La Tinguiña. El cauce tiene una capacidad hidrálica de 250-300 m³/s que es sobrepasada durante eventos extremos. En los conos aluviales de Parcona y La Tinguiña, se han asentado aproximadamente 80 000 personas. Los huaicos contienen corrientes de barro espesas con rocas de hasta 40 toneladas. La PUCP identificó que el riesgo aumenta por la ocupación territorial desordenada y el uso de la quebrada como cantera y vertedero (PUCP tesis 2012; SIGRID CENEPRED 2021).",
    "PUCP / SIGRID CENEPRED",
    "https://sigrid.cenepred.gob.pe/sigridv3/documento/13270",
    variables=[],
    date="2021"
))

docs.append(doc(
    "huaicos-indeci",
    "INDECI identifica 69 puntos críticos por huaicos e inundaciones en Ica",
    "El INDECI de Ica identificó 69 puntos críticos ante las lluvias del Fenómeno El Niño, distribuidos en los 37 distritos declarados en emergencia. Los principales riesgos incluyen desborde del río Ica en puentes antiguos como Los Maestros, Socorro y Grau; desbordes constantes en Ocucaje; y flujos de detritos en quebradas urbanas. En 2017, el INDECI registró 1 149 afectados, 23 783 damnificados, 3 muertos y 78 desplazados en Ica. El estado de emergencia se declaró en 37 distritos de Ica ante el peligro inminente de lluvias intensas (INDECI 2023; Andina 2023; Compendio INDECI 2017).",
    "INDECI / Andina",
    "https://andina.pe/agencia/noticia-ica-identifican-69-puntos-criticos-frente-a-lluvias-propiciaria-fenomeno-nino-1090254.aspx",
    variables=[],
    date="2023"
))

docs.append(doc(
    "huaicos-historia",
    "Historia de huaicos e inundaciones en Ica: 1998 y 2017",
    "La ciudad de Ica ha sido afectada recurrentemente por huaicos e inundaciones. En enero de 1998, lluvias torrenciales generaron un huaico en la quebrada Cansas con un caudal estimado de 600 m³/s, desbordando el río Ica e inundando la ciudad por ambas márgenes, destruyendo San José de los Molinos. En 2017, el Niño Costero provocó desbordes del río Ica, inundación de La Tinguiña (convertida en un lago temporalmente), y daños por flujos de detritos. El compendio estadístico del INDECI 2017 registró para Ica: 1 149 damnificados, 3 muertos, 78 desplazados, 94 casas dañadas (INDECI Compendio 2017; PUCP tesis; Perú 21).",
    "INDECI / Perú 21 / PUCP",
    "https://portal.indeci.gob.pe/wp-content/uploads/2019/01/201802271714541.pdf",
    variables=[],
    date="2017"
))

docs.append(doc(
    "huaicos-medidas",
    "Medidas de prevención de huaicos en la quebrada Cansas",
    "Las medidas estructurales para prevenir huaicos en la quebrada Cansas incluyen diques perpendiculares al cauce, encauzamientos y alcantarillas de cruce. Sin embargo, los diques están resquebrados y colmatados, y las alcantarillas tienen capacidad insuficiente (30 m³/s frente a caudales de 600 m³/s). La tesis de la PUCP (2012) propone que las medidas preventivas deben incluir: (a) proteger los márgenes del río Ica de asentamientos humanos, (b) prohibir el uso de la quebrada como cantera y vertedero, y (c) usar los conos aluviales como zonas de disipación naturales. El proyecto Especial Tambo Caracocha del Gobierno Regional de Ica refuerza cauces con fondos del FONDES (PUCP tesis; gob.pe INDECI 2025).",
    "PUCP / gob.pe INDECI",
    "http://www.gob.pe/institucion/indeci/noticias/1087010-jefe-del-indeci-inspecciono-acciones-de-preparacion-ante-temporada-de-lluvias-intensas-en-ica",
    variables=[],
    date="2025"
))

docs.append(doc(
    "huaicos-en",
    "Huaco flood risk in Ica: the Cansas ravine threat",
    "The Cansas ravine is the main debris flow (huaico) threat to the city of Ica. In January 1998, torrential rains generated a huaico with an estimated discharge of 600 m³/s, overflowing the Ica River and flooding the city on both banks, destroying San José de los Molinos. The alluvial cones of Parcona and La Tinguiña house approximately 80,000 people. The INDECI identified 69 critical points across 37 districts of Ica for flooding and debris flows during the 2023 Coastal El Niño. Debris flows carry thick mud currents with rocks weighing up to 40 tons (INDECI 2017; PUCP 2012; SIGRID CENEPRED 2021).",
    "INDECI / PUCP / SIGRID CENEPRED",
    "https://sigrid.cenepred.gob.pe/sigridv3/documento/13270",
    variables=[],
    date="2021",
    lang="en"
))

# ============================================================
# TEMA 5: El Niño y La Niña (5 docs)
# ============================================================

docs.append(doc(
    "elnino-2017-ica",
    "El Niño Costero 2017: impacto en Ica y la costa sur del Perú",
    "El Niño Costero 2017 fue el tercer evento más intenso del siglo XXI para el Perú, confinado a la zona 1+2 del Pacífico oriental. Entre enero y abril de 2017, generó lluvias torrenciales en la costa sur que causaron desbordes del río Ica, inundaciones en La Tinguiña y flujos de detritos. A nivel nacional, el evento afectó a 1,9 millones de personas, causó 169 fallecidos y 194 000 desplazados, con daños estimados en US$ 4 016 millones (1,9 % del PBI). La temperatura superficial del mar en Puerto Chicama subió de 17 °C a 26,9 °C en febrero de 2017. Las descargas medias de enero-marzo superaron el 250 % del normal en la cuenca del Cañete (adyacente a Ica) (PLOS ONE 2023; IGP / ENFEN).",
    "PLOS ONE / IGP / ENFEN",
    "https://pmc.ncbi.nlm.nih.gov/articles/PMC10522041",
    variables=["PRECTOTCORR", "T2M"],
    date="2023"
))

docs.append(doc(
    "elnino-2023-2024",
    "Fenómeno El Niño 2023-2024: monitoreo ENFEN y alertas para Ica",
    "El ENFEN emitió en 2023 una Alerta de El Niño Costero con probabilidad del 77 % de persistencia hasta el verano de 2024. La magnitud más probable se estimó entre fuerte y moderada para el otoño 2023, moderada para invierno-primavera, y débil-moderada para el verano de 2024. Para la región del Pacífico central, se estimó probabilidad del 82 % de El Niño para el verano con magnitud débil-moderada. El estado de emergencia se declaró en 37 distritos de Ica. El INDECI identificó 69 puntos críticos ante las lluvias intensas esperadas (SENAMHI 2023; INDECI 2023).",
    "SENAMHI / ENFEN / INDECI",
    "https://cdn.www.gob.pe/uploads/document/file/4644771/ESCENARIOS%20DE%20LLUVIAS%20ASOCIADOS%20AL%20FEN%C3%93MENO%20EL%20NI%C3%91O%20F%20%20F%20%20F%20%20F%20.pdf",
    variables=["PRECTOTCORR", "T2M"],
    date="2023"
))

docs.append(doc(
    "elnino-impactos-nacionales",
    "Impacto económico y social del El Niño Costero en el Perú",
    "El Niño Costero 2017 tuvo impactos macroeconómicos medibles en el Perú. La análisis econométrico mostró un impacto negativo de 1,5 puntos porcentuales en el crecimiento del PBI en 2017. La estructura de costos de reconstrucción fue: infraestructura de prevención 21,4 % (US$ 1 650 millones), transporte 38,8 % (US$ 2 994 millones), educación 10,6 % (US$ 819 millones), agua y saneamiento 8,1 % (US$ 626 millones), agricultura 5,4 % (US$ 413 millones), vivienda 4,4 % (US$ 342 millones). Los impactos en salud incluyeron aumento de enfermedades infecciosas y transmitidas por vectores. El crecimiento real del PBI en 2017 fue 1,3 % menor al esperado (PLOS ONE 2023).",
    "PLOS ONE / BCRP / BBVA Research",
    "https://app.ingemmet.gob.pe/biblioteca/pdf/PO-0290767.pdf",
    variables=["PRECTOTCORR"],
    date="2023"
))

docs.append(doc(
    "elnino-definicion",
    "El Niño Costero vs. El Niño Global: diferencias climáticas",
    "El Niño Costero se distingue del El Niño Global por estar confinado a la zona 1+2 del Pacífico oriental (la porción norte y centro del mar peruano), afectando principalmente la costa sur del Perú. Mientras que los eventos globales de 1982-83 y 1997-98 calentaron todo el Pacífico ecuatorial, el de 2017 y el de 2023-24 se desarrollaron localmente entre enero y abril. Esto implica que los impactos en precipitación se concentraron en la costa sur (Piura, Lambayeque, Lima, Ica), con efectos mínimos en la Amazonía y la sierra. El monitoreo se realiza en la región Niño 1+2 mediante la temperatura superficial del mar (TSM), y el ENFEN emite comunicados oficiales de alerta con probabilidades de ocurrencia y magnitud (SENAMHI / IGP).",
    "SENAMHI / IGP / ENFEN",
    "https://cdncache.a.gob.pe/f/005/444/005444058:20231115144816/files_atom/escenarios_lluvias_enfen_2023.pdf",
    variables=["T2M", "PRECTOTCORR"],
    date="2023"
))

docs.append(doc(
    "elnino-en",
    "Coastal El Niño 2017: impacts on Ica and southern Peru coast",
    "The 2017 Coastal El Niño was the third most intense event of the 21st century for Peru, confined to the 1+2 region of the eastern Pacific. Between January and April 2017, it caused torrential rains on the southern coast that led to overflow of the Ica River, flooding in La Tinguiña, and debris flows. Nationally, the event affected 1.9 million people, caused 169 deaths and 194,000 displaced, with estimated damages of US$ 4,016 million (1.9% of GDP). Sea surface temperature at Puerto Chicama rose from 17 °C to 26.9 °C in February 2017 (PLOS ONE 2023; IGP / ENFEN).",
    "PLOS ONE / IGP / ENFEN",
    "https://pmc.ncbi.nlm.nih.gov/articles/PMC10522041",
    variables=["PRECTOTCORR", "T2M"],
    date="2023",
    lang="en"
))

# ============================================================
# TEMA 6: Agua — acuífero y ríos (5 docs)
# ============================================================

docs.append(doc(
    "acuifero-sobreexplotacion",
    "Acuífero de Ica: sobreexplotación y descenso de la napa freática",
    "El acuífero de Ica es la principal fuente de agua subterránea para el valle. La ANA reporta que el nivel freático desciende a una velocidad de 1,4 m/año en el acuífero de Ica, 1,5 m/año en Villacurí y 1,85 m/año en Lanchas. La ANA calcula un déficit de 52,17 hm³/año en el acuífero. Existe un desbalance entre la recarga natural (aproximadamente 55,28 MMC con probabilidad del 10 % en marzo) y la extracción de las agroexportadoras. El 71 % de los pozos en la provincia están sin autorización según la ANA. El volumen total de extracción anual supera la recarga potencial en al menos un 20 %, lo que genera una crisis hídrica progresiva (OECD 2023; PUCP repositorio).",
    "OECD / ANA / PUCP",
    "https://oecd-ilibrary.org/sites/ca151863-en?itemId=/content/component/ca151863-en",
    variables=["GWETTOP"],
    date="2023"
))

docs.append(doc(
    "caudal-rio-ica-ana",
    "Caudal del río Ica: datos hidrológicos de la estación La Achirana",
    "La estación hidrométrica La Achirana registra caudales medios del río Ica desde 1922 (serie de 92 años). La media plurianual es de 9,86 m³/s (255,76 MMC anuales), de los cuales 8,11 m³/s (255,76 MMC) corresponden al caudal natural del río y 1,81 m³/s (57,08 MMC) al aporte trasandino de Choclococha. Los caudales varían significativamente: 17,43 m³/s en 1933 (extremo húmedo, 5 % probabilidad) vs. 2,00 m³/s en 1969 (extremo seco, 95 % probabilidad). En 1992, el caudal fue de apenas 0,15 m³/s. Los meses con mayor volumen sobrante para recarga son enero-abril (ANA / PETACC 2017).",
    "ANA / PETACC",
    "https://hdl.handle.net/20.500.12543/2585",
    variables=["PRECTOTCORR"],
    date="2017"
))

docs.append(doc(
    "acuifero-recarga",
    "Recarga artificial del acuífero de Ica y Villacurí",
    "La ANA y las Juntas de Usuarios han implementado programas de recarga artificial del acuífero. La JUASVI (Junta de Usuarios de Aguas Subterráneas del Valle de Ica) limpia canales de recarga y bombea agua nocturna y diurna cuando hay caudal disponible en el río. La recarga se realiza en áreas designadas de la Pampa de Villacurí y Pampa de los Castillos. Sin embargo, la ANA reporta que hasta la fecha no hay fondos para ejecutar el plan de gestión del acuífero diseñado. La Pampa de Villacurí y la Pampa de los Castillos son las dos frentes agrícolas que expanden la desertificación, con grandes fundos que extraen agua subterránea sin control adecuado (PUCP repositorio; CooperAcción 2018).",
    "ANA / JUASVI / CooperAcción",
    "https://cooperaccion.org.pe/wp-content/uploads/2018/02/Diagnostico-Agua-Ica-Pampas.pdf",
    variables=["GWETTOP"],
    date="2018"
))

docs.append(doc(
    "aguas-superficiales-subterraneas",
    "Balance hídrico de la cuenca del río Ica: déficit crónico",
    "El balance hídrico de la cuenca del río Ica (1965-2018) revela un déficit mensual promedio de 79,89 millones de metros cúbicos (MMC). El índice de confiabilidad de volumen fue de 89,45 % y el de tiempo de 75,31 %, ambos por debajo del umbral de 90 % y 80 % respectivamente, indicando estrés hídrico severo. La cuenca tiene un área de 8 063,57 km² (incluyendo el trasvase) y una demanda agrícola que representa el 90 % del uso total de agua. El 90 % del agua se destina a la agricultura, con tres modalidades: subsistencia, tradicional (pequeños productores) y agroindustrial exportadora (UPC tesis 2023; ANA 2017).",
    "UPC / ANA",
    "https://repositorioacademico.upc.edu.pe/handle/10757/670600?show=full",
    variables=["GWETTOP", "PRECTOTCORR"],
    date="2023"
))

docs.append(doc(
    "agua-en",
    "Water resources in Ica: aquifer depletion and river flow",
    "The Ica aquifer is the main groundwater source for the valley. The National Water Authority (ANA) reports that the water table drops at 1.4 m/year in the Ica aquifer, 1.5 m/year in Villacurí, and 1.85 m/year in Lanchas. The ANA calculates a deficit of 52.17 hm³/year. At La Achirana station (1922-2013, 92 years), the mean annual discharge is 9.86 m³/s, with extremes of 17.43 m³/s (1933) and 0.15 m³/s (1992). The annual water balance shows a chronic deficit of 79.89 million cubic meters (MMC) (ANA / OECD / UPC 2023).",
    "ANA / OECD / UPC",
    "https://oecd-ilibrary.org/sites/ca151863-en?itemId=/content/component/ca151863-en",
    variables=["GWETTOP", "PRECTOTCORR"],
    date="2023",
    lang="en"
))

# ============================================================
# TEMA 7: Agricultura (5 docs)
# ============================================================

docs.append(doc(
    "agroexportacion-macroeconomia",
    "Agroexportación en Ica: motor económico y consumo del 90 % del agua",
    "El valle de Ica es una de las áreas económicas más importantes del Perú. Contribuye con más del 3 % del PBI nacional y el 7 % de las exportaciones totales, pese a representar solo el 1,76 % del territorio y el 2,5 % de la población. La tierra cultivada en el valle cubre 1 200 km² (aproximadamente el 17 % de la superficie total del departamento). El 90 % de los recursos hídricos se destina al uso agrícola. Tres tipos de agricultura coexisten: subsistencia, tradicional (pequeños productores) y agroindustrial exportadora. Desde los años 90, Ica transitó de un modelo local a una economía de agroexportación intensiva en agua (OECD 2023).",
    "OECD",
    "https://oecd-ilibrary.org/sites/ca151863-en?itemId=/content/component/ca151863-en",
    variables=["GWETTOP", "PRECTOTCORR", "T2M"],
    date="2023"
))

docs.append(doc(
    "cultivos-clima-ica",
    "Cultivos de Ica: vid, uva y aceituna adaptados al desierto",
    "Los principales cultivos de la región Ica son la vid (uva de mesa), el olivo (aceituna de mesa y para aceite), el espárrago y el algodón. La uva de mesa exportada por Pisco e Ica es reconocida mundialmente, con destinos en Europa, EE.UU. y Asia. Los cultivos se adaptan al clima desértico mediante riego por goteo y uso intensivo de agua subterránea. El SENAMHI emite pronósticos de riesgo agroclimático específicos para el cultivo de la vid en Ica, considerando temperatura, precipitación y humedad del suelo para planificar la siembra y la cosecha. La Pampa de Villacurí y Pampa de los Castillos son las nuevas fronteras agrícolas en zonas desérticas (SENAMHI DZ 5).",
    "SENAMHI DZ 5 Ica",
    "https://www.senamhi.gob.pe/main.php?dp=ica&p=pronostico-climatico-his",
    variables=["GWETTOP", "PRECTOTCORR"],
    date="2024"
))

docs.append(doc(
    "riego-gotero",
    "Riego por goteo y eficiencia hídrica en las agroexportadoras de Ica",
    "Las grandes agroexportadoras de Ica (como Osmont, Glorex, Drokasa) utilizan sistemas de riego por goteo y fertirrigación para maximizar el uso de agua subterránea de pozos tubulares. Sin embargo, la eficiencia del riego por goteo no compensa la expansión de la frontera agrícola hacia las pampas desérticas. Cada fundo maneja el agua de forma independiente, sin coordinación con las Juntas de Usuarios. El sistema de riego tradicional de pequeños productores aún depende mayormente del riego por inundación (pozas) y gravedad desde el río Ica, con menor eficiencia pero mayor acceso comunitario al agua (CooperAcción 2018; PUCP).",
    "CooperAcción / PUCP",
    "https://cooperaccion.org.pe/wp-content/uploads/2018/02/Diagnostico-Agua-Ica-Pampas.pdf",
    variables=["GWETTOP"],
    date="2018"
))

docs.append(doc(
    "frente-agricola",
    "Expansión de la frontera agrícola en las pampas deserticas de Ica",
    "Ica tiene dos frentes de expansión agrícola en zonas deserticas: la Pampa de los Castillos al este (donde se ubican AGROKASA, Agrícola Chapi, El Pedregal, La Maestranza) y la Pampa de Villacurí al noroeste del valle. Estas zonas, antes desérticas, han sido convertidas en fundos agrícolas mediante pozos tubulares profundos que extraen agua del acuífero. La JUASAVI alertó que esta expansión acelera el descenso del nivel freático, poniendo en riesgo la agricultura tradicional del valle inferior. La expansión agrícola en zonas desérticas sin recarga natural genera un déficit hídrico acumulativo que no se revierte (AConsole / PUCP / JUASAVI).",
    "JUASAVI / AConsole / PUCP",
    "https://aconsole-static.s3.amazonaws.com/media/public/cases/06-CompliantfromJUASVI_July16_English.pdf",
    variables=["GWETTOP", "TS"],
    date="2016"
))

docs.append(doc(
    "agricultura-en",
    "Agro-export economy in Ica: water-intensive agriculture in the desert",
    "The Ica Valley is one of Peru's most important economic areas, contributing over 3% of national GDP and 7% of total exports despite representing only 1.76% of territory and 2.5% of the population. Cultivated land covers 1,200 km² (about 17% of the department area). Agriculture uses 90% of total water resources. Three types of agriculture coexist: subsistence, traditional small-scale, and large-scale agro-industrial export. Since the 1990s, Ica has transitioned from a local production model to a booming water-intensive agro-export economy, with two new agricultural frontiers on desert plains (Pampa de los Castillos and Pampa de Villacurí) that deplete the aquifer (OECD 2023; CooperAcción 2018).",
    "OECD / CooperAcción",
    "https://oecd-ilibrary.org/sites/ca151863-en?itemId=/content/component/ca151863-en",
    variables=["GWETTOP", "PRECTOTCORR"],
    date="2023",
    lang="en"
))

# ============================================================
# TEMA 8: Aire y radiación (5 docs)
# ============================================================

docs.append(doc(
    "vientos-paracas",
    "Vientos Paracas: tormentas de polvo en el desierto Pisco-Ica",
    "Los vientos Paracas son vientos intensos de sur-sureste que soplan sobre el desierto costero entre Pisco e Ica (aprox. 14°-15° S), con velocidades típicas superiores a 10-15 m/s. Ocurren en promedio 4-5 veces por año, principalmente en las tardes hacia el final del invierno austral. Generan tormentas de polvo (dust storms) con repercusiones ecológicas, de salud y económicas. Las fuentes de partículas se originan en la zona costera, donde fuertes vientos forzados por gradientes de presión costeros (APG) intensos generan erosión eólica. Las condiciones sinópticas asociadas incluyen el fortalecimiento de condiciones anticiclónicas en el norte de Chile (Atmospheric Chemistry and Physics / IMARPE 2018).",
    "IMARPE / Atmospheric Chemistry and Physics",
    "https://repositorio.imarpe.gob.pe/bitstream/20.500.12958/10350/1/Paracas%20dust%20storms_%20Sources%2C%20trajectories%20and%20associated%20meteorological%20conditions.pdf",
    variables=["AOD_55", "OMI_NO2_TROP"],
    date="2018"
))

docs.append(doc(
    "radiacion-solar-atlas",
    "Atlas de energía solar del Perú: radiación en la costa sur (Ica)",
    "El Atlas de Energía Solar del Perú (SENAMHI/WMO) reporta que la costa sur del Perú, entre los 15°15' y 18°20' (zona de Ica a Tacna), presenta la mayor radiación solar del país debido a la baja nubosidad invernal. La irradiación solar global (GHI) en esta zona supera los 6 kWh/m²/día en promedio anual. La heliofanía (horas de sol efectivo) es de 2 800 a 3 200 horas anuales en Ica. Estos valores hacen de Ica uno de los mejores ubicaciones del Perú para energía solar fotovoltaica (SENAMHI / WMO / Atlas Solar del Perú).",
    "SENAMHI / WMO",
    "https://www.senamhi.gob.pe/pdf/Atlas%20de_Radiacion_Solar.pdf",
    variables=["ALLSKY_SFC_SW_DWN"],
    date="2024"
))

docs.append(doc(
    "radiacion-solar-power",
    "Radiación solar NASA POWER para Ica: datos de irradiancia",
    "Los datos de irradiancia solar (ALLSKY_SFC_SW_DWN) de NASA POWER para la celda -14,07°, -75,73° muestran un promedio anual de 5,5-6,0 kWh/m²/día, con máximo en verano (diciembre-enero, 7,0-7,5 kWh/m²/día) y mínimo en invierno (junio-julio, 4,0-4,5 kWh/m²/día). La baja nubosidad invernal (22-24 % de cobertura) permite una radiación excepcional en los meses de menor insolación, a diferencia de la costa norte donde la nubosidad reduce la radiación en invierno. Los datos están disponibles en formato diario, mensual y climatológico mediante la API de POWER (NASA POWER).",
    "NASA POWER",
    "https://power.larc.nasa.gov/docs/services/api/temporal/climatology",
    variables=["ALLSKY_SFC_SW_DWN", "CLOUD_AMT"],
    date="2024"
))

docs.append(doc(
    "polvo-atmosferico",
    "Material particulado y calidad del aire en Ica por vientos Paracas",
    "Durante los eventos de vientos Paracas, la concentración de material particulado (PM10 y PM2.5) en el aire de Ica y Pisco puede superar los límites máximos diarios de la normativa peruana de calidad del aire. Las tormentas de polvo transportan partículas de 60-100 micrómetros desde los suelos desérticos de la Pampa de Villacurí. La velocidad umbral para la emisión de polvo es de aproximadamente 0,20 m/s para partículas de 60-100 micrómetros. Los eventos de polvo en Ica-Pisco afectan la salud respiratoria de la población y reducen la visibilidad, con impacto en el transporte aéreo del aeropuerto de Pisco (Atmospheric Chemistry and Physics / IMARPE 2018).",
    "IMARPE / Atmospheric Chemistry and Physics",
    "https://repositorio.imarpe.gob.pe/bitstream/20.500.12958/10350/1/Paracas%20dust%20storms_%20Sources%2C%20trajectories%20and%20associated%20meteorological%20conditions.pdf",
    variables=["AOD_55", "OMI_NO2_TROP"],
    date="2018"
))

docs.append(doc(
    "radiacion-en",
    "Solar radiation in Ica: one of Peru's highest solar resource zones",
    "The southern coast of Peru (15°15'-18°20'), including Ica, has the highest solar radiation in Peru due to low winter cloud cover. The global horizontal irradiance (GHI) exceeds 6 kWh/m²/day on average annually, with annual sunshine hours of 2,800 to 3,200. NASA POWER data for the -14.07°, -75.73° cell shows an annual average of 5.5-6.0 kWh/m²/day, with a summer peak of 7.0-7.5 kWh/m²/day and a winter minimum of 4.0-4.5 kWh/m²/day. This makes Ica one of the best locations in Peru for solar photovoltaic energy (SENAMHI/WMO Atlas; NASA POWER).",
    "SENAMHI / WMO / NASA POWER",
    "https://www.senamhi.gob.pe/pdf/Atlas%20de_Radiacion_Solar.pdf",
    variables=["ALLSKY_SFC_SW_DWN"],
    date="2024",
    lang="en"
))

# ============================================================
# TEMA 9: Suelo y vegetación (4 docs)
# ============================================================

docs.append(doc(
    "ndvi-modis",
    "Índice de vegetación (NDVI) MODIS para el valle de Ica",
    "El NDVI (Normalized Difference Vegetation Index) de MODIS para la zona de Ica (-14°, -76°) muestra valores bajos típicos de desierto (0.05-0.15), con picos de 0.3-0.5 en las zonas de cultivo regado (valle del río Ica y pampa de Villacurí). La baja vegetación natural refleja la aridez extrema, mientras que los valores elevados en franjas puntuales corresponden a la agricultura de exportación. Los datos de MODIS Terra/Aqua están disponibles en el catálogo de variables de NASA y en LP DAAC, con resolución de 500 m y periodo desde 2000 (NASA Earthdata / LP DAAC).",
    "NASA Earthdata / LP DAAC",
    "https://earthdata.nasa.gov/data/catalog/lpcloud-mod13a1-061-0",
    variables=["MODIS_NDVI"],
    date="2024"
))

docs.append(doc(
    "uso-suelo",
    "Uso del suelo en Ica: desierto, agricultura y expansión urbana",
    "El uso del suelo en la región Ica se divide en: desierto natural (85 %), agricultura (12 %, principalmente en el valle del río Ica y las pampas), y zona urbana (3 %). La expansión urbana de la ciudad de Ica ha absorbido terrenos agrícolas y zonas de riesgo de huaicos. La Pampa de Villacurí y la Pampa de los Castillos son áreas deserticas que se han convertido en frentes agrícolas, representando una expansión de la frontera agroindustrial sobre ecosistemas desérticos. La clasificación MODIS MCD12Q1 muestra que la mayoría de la región es cropland/natural vegetation mosaic con parches de barren (NASA Earthdata).",
    "NASA Earthdata / MODIS MCD12Q1",
    "https://nasadaacs.eos.nasa.gov/learn/pathfinders/agricultural-and-water-resources-data-pathfinder/vegetation-data",
    variables=["MODIS_NDVI", "TS"],
    date="2024"
))

docs.append(doc(
    "suelo-humedad",
    "Humedad del suelo en Ica: datos GWETTOP de MERRA-2",
    "La humedad de la capa superior del suelo (GWETTOP) de MERRA-2 para la celda de Ica (-14,07°, -75,73°) muestra valores muy bajos, típicamente 0.05-0.15, indicando suelos extremadamente secos durante la mayor parte del año. Los valores suben ligeramente entre enero y marzo tras las escasas lluvias, pero regresan a niveles mínimos rápidamente debido a la alta evaporación (EVLAND). La baja humedad del suelo explica la facilidad de los vientos Paracas para generar tormentas de polvo, ya que las partículas sueltas del desierto se erosionan eolianamente con facilidad (NASA POWER / MERRA-2).",
    "NASA POWER / MERRA-2",
    "https://power.larc.nasa.gov/docs/services/api/temporal/climatology",
    variables=["GWETTOP", "EVLAND"],
    date="2024"
))

docs.append(doc(
    "desertificacion-en",
    "Soil and vegetation in Ica: desertification and agricultural expansion",
    "Land use in Ica region is: natural desert (85%), agriculture (12%, mainly in the Ica River valley and Villacurí plains), and urban area (3%). The expansion of Ica city has absorbed agricultural land and huaico-risk zones. NASA MODIS NDVI data for the -14°, -76° cell shows very low values (0.05-0.15) typical of desert, with peaks of 0.3-0.5 in irrigated crop zones. Soil wetness (GWETTOP) values are extremely low (0.05-0.15) year-round, with slight increases in January-March (NASA Earthdata; NASA POWER).",
    "NASA Earthdata / NASA POWER",
    "https://nasadaacs.eos.nasa.gov/learn/pathfinders/agricultural-and-water-resources-data-pathfinder/vegetation-data",
    variables=["MODIS_NDVI", "GWETTOP"],
    date="2024",
    lang="en"
))

# ============================================================
# TEMA 10: Tendencias (6 docs)
# ============================================================

docs.append(doc(
    "tendencia-aquiifero",
    "Tendencia de descenso del acuífero de Ica: 1,4 m por año",
    "La tendencia del nivel freático en el acuífero de Ica muestra un descenso constante de 1,4 m/año según la ANA, con aceleración en las zonas de mayor extracción. En Villacurí el descenso es de 1,5 m/año y en Lanchas de 1,85 m/año. Este descenso se ha mantenido durante las últimas décadas, agravado por la expansión de la agroexportación. La tasa de extracción supera a la tasa de recarga en un 20 %, generando un déficit acumulativo de 52,17 hm³/año. Si la tendencia continúa, el acuífero podría alcanzar niveles no bombeables en las zonas periféricas en 20-30 años (ANA 2012; OECD 2023).",
    "ANA / OECD",
    "https://oecd-ilibrary.org/sites/ca151863-en?itemId=/content/component/ca151863-en",
    variables=["GWETTOP"],
    date="2023"
))

docs.append(doc(
    "tendencia-temperatura",
    "Tendencia de temperatura en Ica: calentamiento gradual confirmado",
    "Las series temporales de temperatura de MERRA-2/POWER para la celda de Ica (-14,07°, -75,73°) muestran una tendencia de calentamiento de aproximadamente 0,1-0,15 °C por década durante las últimas cuatro décadas, consistente con el calentamiento global en la costa peruana. Los meses de verano (febrero-marzo) muestran el mayor incremento, con anomalías positivas de hasta +0,5 °C en los últimos 10 años respecto a la media 1991-2020. Las noches mínimas han aumentado más que las máximas, indicando reducción de la amplitud térmica diurna (NASA POWER; SENAMHI climatología).",
    "NASA POWER / SENAMHI",
    "https://power.larc.nasa.gov/docs/services/api/temporal/climatology",
    variables=["T2M"],
    date="2024"
))

docs.append(doc(
    "tendencia-precipitacion",
    "Tendencia de precipitación en Ica: aridez persistente",
    "Los datos de PRECTOTCORR de MERRA-2 para Ica muestran una tendencia de ligera disminución de la precipitación en las últimas décadas, aunque la variabilidad interanual es tan alta que la tendencia no es estadísticamente significativa. Los años extremadamente secos (como 1969, con apenas 0,15 m³/s de caudal en el río Ica) se están volviendo más frecuentes. La media anual de precipitación se mantiene alrededor de 3-5 mm/año, sin cambios estructurales en el patrón de aridez. La recarga del acuífero depende de episodios puntuales de lluvias intensas, cuya frecuencia está aumentando con el El Niño Costero (NASA POWER / ANA 2017).",
    "NASA POWER / ANA",
    "https://power.larc.nasa.gov/docs/services/api/temporal/climatology",
    variables=["PRECTOTCORR"],
    date="2024"
))

docs.append(doc(
    "tendencia-agroexportacion",
    "Tendencia de la agroexportación en Ica: crecimiento vs. sostenibilidad",
    "Desde los años 90, la agroexportación en Ica ha crecido de manera exponencial, con la superficie cultivada triplicándose. La inversión en pozos tubulares y sistemas de riego por goteo ha permitido la expansión a las pampas deserticas. Sin embargo, esta tendencia no es sostenible: el descenso del acuífero (1,4 m/año) y el déficit hídrico de 52,17 hm³/año indican que la extracción supera la recarga. Si la tendencia continúa, el colapso del acuífero en las zonas periféricas afectará a la agricultura tradicional y a los 80 000 habitantes de los conos aluviales (OECD 2023; CooperAcción 2018).",
    "OECD / CooperAcción",
    "https://oecd-ilibrary.org/sites/ca151863-en?itemId=/content/component/ca151863-en",
    variables=["GWETTOP"],
    date="2023"
))

docs.append(doc(
    "tendencia-ica-en",
    "Ica trends: aquifer depletion, temperature rise, and aridity",
    "The Ica aquifer water table is declining at 1.4 m/year (ANA), with an annual deficit of 52.17 hm³. Temperature shows a warming trend of 0.1-0.15 °C/decade in the last 40 years, with summer months showing the largest increase. Precipitation shows a slight decreasing trend, though interannual variability is very high. The agro-export economy has tripled cultivated area since the 1990s, but this growth is unsustainable given the aquifer depletion rate and chronic water deficit of 79.89 MMC monthly (ANA; NASA POWER; OECD 2023).",
    "ANA / NASA POWER / OECD",
    "https://power.larc.nasa.gov/docs/services/api/temporal/climatology",
    variables=["GWETTOP", "T2M", "PRECTOTCORR"],
    date="2024",
    lang="en"
))

docs.append(doc(
    "tendencia-igp",
    "Tendencias climáticas y ENSO en Ica según el IGP",
    "El Instituto Geofísico del Perú (IGP) y el ENFEN reportan que los eventos de El Niño Costero se están volviendo más frecuentes e intensos en las últimas décadas. La tendencia histórica muestra que los eventos locales (como 2017 y 2023-24) se concentran en la costa sur, con efectos de lluvias torrenciales en Ica. La temperatura del mar en la zona 1+2 ha mostrado una tendencia de calentamiento que aumenta la probabilidad de eventos de este tipo. El IGP mantiene modelos de previsión estacional para la costa peruana que incluyen la región de Ica (IGP / ENFEN 2023).",
    "IGP / ENFEN / SENAMHI",
    "https://cdn.www.gob.pe/uploads/document/file/4644771/ESCENARIOS%20DE%20LLUVIAS%20ASOCIADOS%20AL%20FEN%C3%93MENO%20EL%20NI%C3%91O%20F%20%20F%20%20F%20%20F%20.pdf",
    variables=["T2M", "PRECTOTCORR"],
    date="2023"
))

# ============================================================
# TEMA 11: Estaciones y datos (4 docs)
# ============================================================

docs.append(doc(
    "estaciones-senamhi-ica",
    "Estaciones meteorológicas SENAMHI en la región Ica",
    "La Dirección Zonal 05 del SENAMHI tiene su sede en Ica y opera múltiples estaciones meteorológicas en la región. La estación principal de la ciudad es San Camilo (a ~3 km del centro), que registra las normales climatológicas 1991-2020. Otras estaciones incluyen: la estación hidrométrica La Achirana en el río Ica (controla 2 505 km² de cuenca), estaciones en Pisco (aeropuerto METAR), y estaciones automáticas en las provincias de Chincha, Nasca y Palpa. El SENAMHI publica pronósticos de caudales, riesgo agroclimático y radiación UV para Ica (SENAMHI DZ 5).",
    "SENAMHI DZ 5 Ica",
    "https://www.senamhi.gob.pe/mapas/descarga-datos/pdf/tutorial-para-la-descarga-de-datos.pdf",
    variables=["T2M", "PRECTOTCORR", "ALLSKY_SFC_SW_DWN"],
    date="2024"
))

docs.append(doc(
    "estacion-la-achirana",
    "Estación hidrométrica La Achirana: 92 años de datos del río Ica",
    "La estación La Achirana es la principal estación hidrométrica del río Ica, ubicada aguas abajo de la ciudad. Opera desde 1922 con una serie de 92 años de caudales medios mensuales. Controla un área de 2 505 km² (2 113 km² de cuenca natural + 392 km² de derivación de Choclococha). Registra caudales medios mensuales desde 1922: media de 9,86 m³/s (8,11 m³/s natural + 1,81 m³/s Choclococha). Los datos incluyen caudales máximos y mínimos históricos, series diarias y pronósticos. La información está disponible en el SNIRH (Sistema Nacional de Información de Recursos Hídricos) y a través de la ALA ICA (ANA / SNIRH).",
    "ANA / SNIRH / ALA Ica",
    "https://hdl.handle.net/20.500.12543/2585",
    variables=["PRECTOTCORR"],
    date="2017"
))

docs.append(doc(
    "senamhi-pronosticos",
    "Pronósticos climáticos y agroclimáticos del SENAMHI para Ica",
    "El SENAMHI DZ 5 Ica emite regularmente: pronóstico hidrológico mensual (caudales del río Ica y tributarios), pronóstico climático estacional (probabilidades de lluvia y temperatura), pronóstico de riesgo agroclimático para vid, cítricos y palto, boletín de radiación UV para la ciudad de Ica, y monitoreo decadal de precipitación (MIDAS). Los pronósticos utilizan el modelo ETA-SENAMHI para lluvia y el GFS de NOAA para temperatura. Los datos de caudal se procesan mediante la plataforma RS MINERVE, que integra modelos hidrológicos calibrados (SENAMHI).",
    "SENAMHI DZ 5",
    "https://www.senamhi.gob.pe/main.php?dp=ica&p=pronostico-caudales",
    variables=["PRECTOTCORR", "T2M"],
    date="2024"
))

docs.append(doc(
    "senamhi-en",
    "Weather stations in Ica: SENAMHI DZ 5 monitoring network",
    "The SENAMHI Zonal Directorate 5, headquartered in Ica, operates a network of meteorological stations including the main San Camilo station (climate normals), the La Achirana hydrometric station on the Ica River (92 years of flow data since 1922), automatic stations in Chincha, Nasca, and Palpa, and the Pisco airport METAR station. SENAMHI issues monthly hydrological forecasts, seasonal climate projections, agroclimatic risk forecasts for grapes/citrus/avocado, UV radiation bulletins, and decadal precipitation monitoring (MIDAS system) (SENAMHI DZ 5 Ica).",
    "SENAMHI DZ 5 Ica",
    "https://www.senamhi.gob.pe/main.php?dp=ica&p=pronostico-caudales",
    variables=["T2M", "PRECTOTCORR", "ALLSKY_SFC_SW_DWN"],
    date="2024",
    lang="en"
))

# ============================================================
# TEMA 12: Población expuesta (4 docs)
# ============================================================

docs.append(doc(
    "poblacion-censo",
    "Población de Ica: censo 2017 y distribución territorial",
    "Según el censo INEI 2017, la región Ica tiene 893 292 habitantes, distribuidos en 5 provincias: Ica (407 286), Chincha (240 884), Pisco (159 111), Nasca (71 930) y Palpa (14 081). La ciudad de Ica tiene 155 247 habitantes, de los cuales 154 552 son urbanos (99,6 %) y solo 695 rurales. La densidad general es de 41,9 hab/km², pero la concentración en el valle y la capital es mucho mayor. El 94,1 % de la población es mestiza, con comunidades quechua (18 862), afoperuana (5 201) y otras minorías (INEI 2017).",
    "INEI",
    "https://citypopulation.de/en/peru/admin/11__ica",
    variables=[],
    date="2017"
))

docs.append(doc(
    "poblacion-expuesta-huaicos",
    "Población expuesta a huaicos e inundaciones en Ica",
    "Aproximadamente 80 000 personas habitan en los conos aluviales de la quebrada Cansas (Parcona y La Tinguiña), directamente expuestas a huaicos con corrientes de barro y rocas de hasta 40 toneladas. Adicionalmente, 37 distritos de la región Ica fueron declarados en emergencia durante el El Niño 2023-24, con 69 puntos críticos identificados por el INDECI. En 2017, el INDECI registró 23 783 damnificados y 94 casas dañadas en Ica por huaicos e inundaciones. La expansión urbana desordenada ha ocupado zonas de riesgo en los márgenes del río Ica y las quebradas urbanas (INDECI 2017; INDECI 2023; SIGRID CENEPRED 2021).",
    "INDECI / SIGRID CENEPRED",
    "https://portal.indeci.gob.pe/wp-content/uploads/2019/01/201802271714541.pdf",
    variables=[],
    date="2023"
))

docs.append(doc(
    "poblacion-vulnerabilidad",
    "Vulnerabilidad de la población de Ica ante desastres naturales",
    "La población de Ica está expuesta a múltiples amenazas: huaicos (quebrada Cansas, Yancay), inundaciones fluviales (río Ica), terremotos (falla de subducción del Pacífico), y sequías. El SIGRID CENEPRED (2021) identificó puntos críticos de inundación, flujo de detritos y erosión en los principales ríos y quebradas del departamento. Los asentamientos humanos en los márgenes del río Ica y en las quebradas urbanas representan el mayor riesgo. La población rural de las provincias de Nasca y Palpa enfrenta vulnerabilidad por sequía y acceso limitado al agua. El 695 habitantes rurales de la región enfrentan condiciones de aridez extrema (SIGRID CENEPRED 2021; INEI 2017).",
    "SIGRID CENEPRED / INEI",
    "https://sigrid.cenepred.gob.pe/sigridv3/documento/13270",
    variables=[],
    date="2021"
))

docs.append(doc(
    "poblacion-en",
    "Population exposure to hazards in Ica, Peru",
    "Approximately 80,000 people live in the alluvial cones of the Cansas ravine (Parcona and La Tinguiña), directly exposed to debris flows carrying mud currents and rocks weighing up to 40 tons. Additionally, 37 districts of Ica were declared in emergency during the 2023-24 El Niño, with 69 critical points identified by INDECI. In 2017, INDECI recorded 23,783 affected people and 94 damaged houses. The INEI 2017 census reports 893,292 inhabitants in the region, with 155,247 in the city of Ica. Uncontrolled urban expansion has occupied hazard zones along the Ica River and urban ravines (INDECI 2017; SIGRID CENEPRED 2021).",
    "INDECI / SIGRID CENEPRED / INEI",
    "https://portal.indeci.gob.pe/wp-content/uploads/2019/01/201802271714541.pdf",
    variables=[],
    date="2023",
    lang="en"
))

# ============================================================
# Escribir el archivo
# ============================================================
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
with open(OUTPUT, "w", encoding="utf-8") as f:
    for d in docs:
        f.write(json.dumps(d, ensure_ascii=False, separators=(",", ":")) + "\n")

print(f"Wrote {len(docs)} documents to {OUTPUT}")

# Show breakdown by topic
topics = {
    "T1 ubicación": [d["id"] for d in docs if "ubicacion" in d["id"] or "cuenca" in d["id"] or "choclococha" in d["id"]],
    "T2 temperatura": [d["id"] for d in docs if "temperatura" in d["id"]],
    "T3 lluvia": [d["id"] for d in docs if "precipitacion" in d["id"] or "estacionalidad" in d["id"]],
    "T4 extremos": [d["id"] for d in docs if "huaico" in d["id"] or "elnino" in d["id"]],
    "T5 El Niño": [d["id"] for d in docs if "elnino" in d["id"]],
    "T6 agua": [d["id"] for d in docs if "acuifero" in d["id"] or "caudal" in d["id"] or "aguas-superficiales" in d["id"]],
    "T7 agricultura": [d["id"] for d in docs if "agroexp" in d["id"] or "cultivos" in d["id"] or "riego" in d["id"] or "frente-agr" in d["id"]],
    "T8 aire/rad": [d["id"] for d in docs if "paracas" in d["id"] or "radiacion" in d["id"] or "polvo" in d["id"]],
    "T9 suelo": [d["id"] for d in docs if "ndvi" in d["id"] or "uso-suelo" in d["id"] or "suelo-humedad" in d["id"] or "desertificacion" in d["id"]],
    "T10 tendencias": [d["id"] for d in docs if "tendencia" in d["id"]],
    "T11 estaciones": [d["id"] for d in docs if "estaciones" in d["id"] or "la-achirana" in d["id"] or "senamhi-pron" in d["id"]],
    "T12 población": [d["id"] for d in docs if "poblacion" in d["id"]],
}
for t, ids in topics.items():
    es = len([i for i in ids if not i.endswith("-en")])
    en = len([i for i in ids if i.endswith("-en")])
    print(f"  {t}: {es} es, {en} en → {ids}")

total_es = len([d for d in docs if d["lang"] == "es"])
total_en = len([d for d in docs if d["lang"] == "en"])
print(f"\nTOTAL: {total_es} español, {total_en} inglés, {len(docs)} total")
