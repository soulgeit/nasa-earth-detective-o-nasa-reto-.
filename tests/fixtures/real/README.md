# Muestras reales (no editar)

Respuestas crudas de servicios de la NASA, guardadas tal cual para desarrollar y probar parsers sin red.
No son datos de demostración para la interfaz: los casos que ve el usuario se congelan con `scripts/freeze_case.py` y llevan su `provenance`.

| Archivo | Consulta | Descargado |
|---|---|---|
| `power_monthly_point_lima.json` | `https://power.larc.nasa.gov/api/temporal/monthly/point?parameters=T2M,PRECTOTCORR,GWETTOP,TO3,AOD_55,TS,ALLSKY_SFC_SW_DWN,EVLAND,SNODP,TQV,CLOUD_AMT,RH2M&community=AG&longitude=-77.03&latitude=-12.05&start=1981&end=2025&format=JSON` | 2026-11-14 ~17:22 UTC, HTTP 200, 2,1 s |
| `power_monthly_regional_piura_T2M.json` | `https://power.larc.nasa.gov/api/temporal/monthly/regional?parameters=T2M&community=AG&latitude-min=-7&latitude-max=-3&longitude-min=-82&longitude-max=-78&start=1981&end=2025&format=JSON` | 2026-11-14 ~17:25 UTC, HTTP 200, 1,6 s |
| `power_monthly_point_lima_ws2m.json` | `https://power.larc.nasa.gov/api/temporal/monthly/point?parameters=WS2M&community=AG&longitude=-77.03&latitude=-12.05&start=1981&end=2025&format=JSON` | 2026-11-14 ~23:49 UTC, HTTP 200 |
| `power_monthly_point_lima_t2m_max.json` | `https://power.larc.nasa.gov/api/temporal/monthly/point?parameters=T2M_MAX&community=AG&longitude=-77.03&latitude=-12.05&start=1981&end=2025&format=JSON` | 2026-11-14 ~23:50 UTC, HTTP 200 |
| `power_monthly_point_lima_t2m_min.json` | `https://power.larc.nasa.gov/api/temporal/monthly/point?parameters=T2M_MIN&community=AG&longitude=-77.03&latitude=-12.05&start=1981&end=2025&format=JSON` | 2026-11-14 ~23:50 UTC, HTTP 200 |

Observado en estas respuestas:
- Claves `YYYYMM`; la clave `YYYY13` es el valor anual (hay que descartarla). 45 años × 13 claves = 585 por parámetro.
- Valor de relleno: `-999.0`. `AOD_55` tiene 240 meses de relleno; `ALLSKY_SFC_SW_DWN` y `CLOUD_AMT`, 36.
- `header.api.version` = `v2.10.0`; `header.sources` = `SRB, SYN1DEG, MERRA2, POWER`.
- Primeros valores en Lima (1981-01): `T2M` 18.41 °C, `PRECTOTCORR` 0.26 mm/día.
- Regional 4°×4°: 63 celdas (9 latitudes cada 0,5° × 7 longitudes cada 0,625°), coordenadas `[lon, lat, elevación]`.

Para añadir una muestra: guarda la respuesta sin tocar y añade una fila con la URL exacta y la fecha.
