# References and Space Agency Partner Resources
## NASA Space Apps Challenge 2026 — EarthTrend Detective

This document compiles all primary Earth science datasets, satellite missions, reanalysis models, scientific papers, and open-source tools utilized by the **EarthTrend Detective** platform, fulfilling the official challenge requirements under *"Space Agency Partner Data and Other References"*.

---

### 1. Primary Space Agency Earth Observation Data Sources

| Mission / Model | Operating Agency | Data Type | Temporal Coverage | Access Endpoint & Documentation | License |
|---|---|---|---|---|---|
| **NASA POWER v2.10.0** (MERRA-2, CERES SYN1deg, SRB) | NASA Langley Research Center | Surface Meteorology & Solar Fluxes (T2M, TS, PRECTOTCORR, GWETTOP, EVLAND, SNODP, RH2M, TO3) | 1981-01 to 2025-12 (Monthly) | [NASA POWER API](https://power.larc.nasa.gov/) | NASA Public Domain |
| **NASA GISTEMP v4** | NASA Goddard Institute for Space Studies (GISS) | Global Surface Temperature Anomalies (1200 km smoothing) | 1880-01 to present (Monthly) | [GISS GISTEMP](https://data.giss.nasa.gov/gistemp/) | NASA Public Domain |
| **NSIDC Sea Ice Index v4** | NOAA / NSIDC | Arctic & Antarctic Sea Ice Extent & Concentration | 1978-11 to present (Monthly) | [NSIDC Data](https://nsidc.org/data/seaice_index) | Public Domain (NOAA/NSIDC) |
| **NASA Giovanni** | NASA Goddard Earth Sciences Data & Information Services Center (GES DISC) | Area-Averaged Time Series (GPM IMERG, GLDAS v2.1, AIRS v7, OMI v3, MODIS Terra/Aqua) | Variable (2000-present) | [GES DISC Giovanni](https://giovanni.gsfc.nasa.gov/giovanni/) | NASA Public Domain |
| **NASA GIBS** (Global Imagery Browse Services) | NASA EOSDIS | Blue Marble Shaded Relief Bathymetry Basemap | Global Daily Mosaic | [NASA GIBS WMTS](https://gibs.earthdata.nasa.gov/) | NASA Public Domain |
| **SWOT** (Surface Water & Ocean Topography) | NASA / CNES / CSA / UKSA | Water Surface Elevation (KaRIn Altimeter) | 2022-12 to present | [CSA SWOT](https://www.asc-csa.gc.ca/eng/satellites/swot/) | Public / Open Data |
| **NOAA CDO** (Climate Data Online) | NOAA NCEI | In-Situ Ground Weather Observations | Historical archives | [NOAA CDO](https://www.ncei.noaa.gov/cdo-web/) | US Government Public Domain |

---

### 2. Methodological & Statistical References

1. **Weatherhead, E. C., et al. (1998)**. *Factors affecting the detection of trends: Statistical considerations and applications to environmental data*. Journal of Geophysical Research: Atmospheres, 103(D14), 17149–17161. DOI: [10.1029/98JD00995](https://doi.org/10.1029/98JD00995).
2. **Mann, H. B. (1945)**. *Nonparametric tests against trend*. Econometrica, 13(3), 245–259. DOI: [10.2307/1907187](https://doi.org/10.2307/1907187).
3. **Kendall, M. G. (1975)**. *Rank Correlation Methods*. Charles Griffin, London.
4. **Sen, P. K. (1968)**. *Estimates of the regression coefficient based on Kendall's tau*. Journal of the American Statistical Association, 63(324), 1379–1389. DOI: [10.1080/01621459.1968.10480934](https://doi.org/10.1080/01621459.1968.10480934).
5. **Hamed, K. H., & Rao, A. R. (1998)**. *A modified Mann-Kendall trend test for autocorrelated data*. Journal of Hydrology, 204(1–4), 182–196. DOI: [10.1016/S0022-1694(97)00125-X](https://doi.org/10.1016/S0022-1694(97)00125-X).
6. **Santer, B. D., et al. (2000)**. *Accounting for the effects of surface temperature anomalies in climate signal detection*. Journal of Geophysical Research: Atmospheres, 105(D6), 7337–7356. DOI: [10.1029/1999JD901105](https://doi.org/10.1029/1999JD901105).
7. **Wilks, D. S. (2016)**. *“The Stippling Shows Statistically Significant Grid Points”: How Research Results are Unrealistically Fabricated When Simultaneous Inference Is Ignored*. Bulletin of the American Meteorological Society, 97(12), 2263–2270. DOI: [10.1175/BAMS-D-15-00267.1](https://doi.org/10.1175/BAMS-D-15-00267.1).
8. **Gelaro, R., et al. (2017)**. *The Modern-Era Retrospective Analysis for Research and Applications, Version 2 (MERRA-2)*. Journal of Climate, 30(14), 5419–5454. DOI: [10.1175/JCLI-D-16-0758.1](https://doi.org/10.1175/JCLI-D-16-0758.1).

---

### 3. Open-Source Tools & Libraries

- **FastAPI** (MIT License): High-performance asynchronous REST backend.
- **Uvicorn** (BSD-3-Clause): ASGI web server.
- **NumPy & SciPy** (BSD-3-Clause): Numerical arrays, non-parametric distributions, and linear algebra.
- **Leaflet.js** (BSD-2-Clause): Interactive mapping engine.
- **Chart.js** (MIT License): Accessible, responsive canvas-based data visualizations.
- **Certifi** (MPL-2.0): Root TLS certificate validation for NASA API endpoints.
