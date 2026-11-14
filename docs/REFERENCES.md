# References — Space Agency Partner Data and Other References

> **SI-assisted: hermes-1 (qwen3.6)** — Redactado con ayuda de IA, contenido verificado.
References — Space Agency Partner Data and Other References

## Space Agency Partner Data

### NASA POWER (NASA Langley Research Center)
- **URL:** https://power.larc.nasa.gov/
- **API docs:** https://power.larc.nasa.gov/docs/api-definition/
- **Dataset:** MERRA-2 reanalysis, SRB/CERES radiation data
- **Resolution:** 0.5° × 0.625° (point), 0.5° grid (regional)
- **Temporal range:** 1981–present (monthly)
- **License:** NASA open data policy — generally public domain
- **Citation:** Stackhouse, P.W. Jr., et al., "NASA POWER Project," 2026

### NASA GISTEMP (GISS)
- **URL:** https://data.giss.nasa.gov/gistemp/
- **Dataset:** Global Surface Temperature Analysis v4
- **DOI:** https://doi.org/10.1029/2018JD029522
- **Resolution:** 1.0° × 1.25° global grid
- **Temporal range:** 1880–present (monthly)
- **License:** Public domain

### NSIDC Sea Ice Index v4 (NASA/GSFC & NOAA/NGDC)
- **URL:** https://nsidc.org/data/seaice_index
- **Data access:** https://nsidc.org/data/G02135/versions/4
- **DOI:** https://doi.org/10.7265/N4D81J9M
- **Resolution:** 25 km × 25 km Polar Stereographic
- **Temporal range:** November 1978–present (monthly)
- **License:** NASA open data policy

### Giovanni (NASA GSFC GES DISC)
- **URL:** https://giovanni.gsfc.nasa.gov/
- **API docs:** https://disc.gsfc.nasa.gov/giovanni-documentation
- **Products:** GPM IMERG, GLDAS, AIRS, OMI, MODIS data exports (CSV)
- **Access:** Earthdata login required (https://urs.earthdata.nasa.gov/)
- **License:** Varies by product; most NASA open data

## Statistical Methods References

### Mann-Kendall Test
- Mann, H.B. (1945). "Intelligent analysis of time series." *Journal of the American Statistical Association*, 40(232), 509–525.
- Kendall, M.G. (1975). *Rank Correlation Methods*. Charles Griffin.
- DOI: https://doi.org/10.2307/1907187

### Sen's Slope Estimator
- Sen, P.K. (1968). "Estimates of the regression coefficient based on Kendall's tau." *Journal of the American Statistical Association*, 63(324), 1379–1389.
- DOI: https://doi.org/10.1080/01621459.1968.10480934

### Hamed & Rao Correction for Autocorrelation
- Hamed, K.H., and Rao, A.R. (1998). "A modified Mann-Kendall trend test for autocorrelated data." *Journal of Hydrology*, 204(1-4), 182–196.
- DOI: https://doi.org/10.1016/S0022-1694(97)00125-X

### Santer et al. (2000) — Significance Testing with Autocorrelation
- Santer, B.D., et al. (2000). "Statistical significance of trends and trend differences in column-average atmospheric water vapor data." *Journal of Geophysical Research*, 105(D14), 18501–18517.
- DOI: https://doi.org/10.1029/1999JD901105

### Weatherhead et al. (1998) — Detectability/Years Needed
- Weatherhead, E.C., et al. (1998). "Factors affecting the detectability of trends." *Journal of Geophysical Research*, 103(D13), 28797–28808.
- DOI: https://doi.org/10.1029/98JD00995

### Wilks (2016) — FDR Control (Benjamini-Hochberg)
- Wilks, D.S. (2016). "The Stewart Mann Award Lecture: 'Son of Boxwood' — Controlling the False Discovery Rate in Geoscience." *Bulletin of the American Meteorological Society*, 97(8), 1341–1356.
- DOI: https://doi.org/10.1175/BAMS-D-15-00267.1

## Software and Tools

### pyMannKendall (Mann-Kendall implementation)
- **URL:** https://github.com/rakshith93/pyMannKendall
- **DOI:** https://doi.org/10.21105/joss.01556
- **License:** MIT

### numpy
- **URL:** https://numpy.org/
- **Halkidi, et al.** *Array programming with NumPy.* Nature, 2023.
- **DOI:** https://doi.org/10.1038/s41586-023-06049-x
- **License:** BSD-3

### FastAPI
- **URL:** https://fastapi.tiangolo.com/
- **License:** MIT

### Leaflet + Chart.js (Frontend)
- **Leaflet:** https://leafletjs.com/ — BSD-2
- **Chart.js:** https://www.chartjs.org/ — MIT

## Biome and Geographic References

### WWF Terrestrial Ecoregions
- **URL:** https://worldwildlife.org/science/data/ecoregion-data
- **License:** CC BY-SA 4.0

### GeoNames (cities/gazetteer)
- **URL:** http://www.geonames.org/
- **Data license:** Creative Commons Attribution 3.0
