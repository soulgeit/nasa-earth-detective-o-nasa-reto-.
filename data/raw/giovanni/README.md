# CSV de Giovanni (los exporta una persona del equipo)

Giovanni es la herramienta de la NASA (GES DISC) que genera series temporales de una región. Con estos archivos cubrimos las fuentes que el reto nombra
y que no tienen acceso sin cuenta: GPM, GLDAS, AIRS, OMI y MODIS.

## Pasos
1. Crea una cuenta gratuita en https://urs.earthdata.nasa.gov
2. Entra en https://giovanni.gsfc.nasa.gov/giovanni/ e inicia sesión.
3. *Select Plot*: **Time Series → Area-Averaged**.
4. *Select Date Range*: todo el periodo disponible de la variable.
5. *Select Region*: dibuja la caja de la región del caso (anota las coordenadas).
6. *Select Variables*: busca por palabra clave y marca **una** variable. Prefiere productos **mensuales**.
7. *Plot Data* → cuando termine, *Downloads* → **CSV**.
8. Guarda el archivo aquí con este nombre: `<VARIABLE_ID>__<region>.csv` (ejemplo: `GPM_IMERG_PRECIP__piura.csv`).

No edites el archivo: la cabecera trae el producto, la versión, la región y las fechas, y de ahí sale la procedencia.

## Qué exportar (mínimo 5; el primero cuanto antes, sirve de muestra para el parser)

| `variable_id` | Qué buscar en Giovanni | Fuente del reto |
|---|---|---|
| `GPM_IMERG_PRECIP` | precipitación mensual IMERG | GPM |
| `GLDAS_SOILM_0_10` | humedad del suelo 0–10 cm, GLDAS Noah mensual | GLDAS |
| `GLDAS_EVAP` | evapotranspiración, GLDAS mensual | GLDAS |
| `GLDAS_RUNOFF` | escorrentía, GLDAS mensual | GLDAS |
| `AIRS_SURF_AIR_TEMP` | temperatura del aire en superficie, AIRS mensual | AIRS |
| `OMI_NO2_TROP` | columna troposférica de NO₂ | OMI |
| `OMI_O3_TOTAL` | columna total de ozono | OMI |
| `MODIS_NDVI` | NDVI mensual | MODIS |
| `MODIS_LST_DAY` | temperatura de la superficie terrestre, día, mensual | MODIS |
| `MODIS_AOD` | espesor óptico de aerosoles, mensual | MODIS |

Los nombres exactos de los productos cambian con las versiones: elige el mensual más reciente y deja que la cabecera del CSV diga cuál fue.
