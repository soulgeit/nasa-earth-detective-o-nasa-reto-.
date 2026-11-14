# Referencias — NASA EarthTrend Detective

## Fuentes de datos verificadas

### NASA POWER (MERRA-2)
- **URL principal**: https://power.larc.nasa.gov/
- **Parameter Dictionary**: https://power.larc.nasa.gov/parameters/
- **API documentation**: https://power.larc.nasa.gov/docs/api/
- **Reanalysis paper**: Gelman et al. (2021), "MERRA-2: NASA's Reanalysis Dataset", https://doi.org/10.21752/JCLI-D-16-0758.1
- **Citation**: https://power.larc.nasa.gov/documentation/citation/
- **Variables live**: 15 variables (T2M, TS, PRECTOTCORR, RH2M, TQV, TO3, AOD_55, CLOUD_AMT, ALLSKY_SFC_SW_DWN, GWETTOP, EVLAND, SNODP, etc.)
- **Resolución**: 0.5° x 0.625°
- **Período**: 1981-01 a presente
- **Formato**: JSON, HTTP GET/POST
- **Licencia**: NASA (dominio público)

### NASA GISS GISTEMP
- **URL**: https://data.giss.nasa.gov/gistemp/
- **Paper**: Hansen et al. (2010), "Global surface temperature change", https://doi.org/10.1029/2010JD014316
- **Version**: GISTEMP v4
- **Resolución**: 1° x 1°
- **Período**: 1880-01 a presente
- **Anomalía vs**: 1951-1980 base period
- **Licencia**: NASA (dominio público)

### NSIDC Sea Ice Index
- **URL**: https://nsidc.org/data/seaice_index/
- **Paper**: Fetterer et al. (2017), "Sea Ice Index", https://doi.org/10.7265/N5-DI2E-4904
- **Resolución**: 25 km grid
- **Período**: 1978-11 a presente
- **Fuentes de datos**: SSMI, SSMIS, AMSR-E, AMSR2, QuikSCAT, WindSat
- **Licencia**: NSIDC (dominio público)

### NASA Giovanni
- **URL**: https://giovanni.gsfc.nasa.gov/giovanni/
- **API**: https://giovanni.gsfc.nasa.gov/giovanni/faq/
- **Variable set**: GPM/IMERG, GLDAS, MODIS, AIRS, OMI, MERRA-2
- **Formato de descarga**: CSV
- **Caveat**: Algunos datasets requieren cuenta NASA Earthdata

## Estadística

### Mann-Kendall
- Mann (1945), "Index of correlation", https://doi.org/10.2307/1907187
- Kendall (1975), "Rank correlation methods", Griffin, London
- Hamed & Rao (2002), "A modified Mann-Kendall trend test for autocorrelated data", https://doi.org/10.1016/S0022-1694(97)00125-X
- Conover (1980), "Practical nonparametric statistics", Wiley

### Theil-Sen
- Sen (1968), "Estimates of the regression coefficient based on Kendall's tau", https://doi.org/10.1080/01621459.1968.10480934

### Regresión OLS con IC
- Cramer (2003), "The Mathematics of Statistics", D. Van Nostrand
- Wilks (2016), "Statistical Methods in the Atmospheric Sciences", 3rd ed., Academic Press

### Control de falsos positivos
- Benjamini & Hochberg (1995), "Controlling the false discovery rate", JASA
- Wilks (2016), "Significance testing with discrete data", https://doi.org/10.1175/JCLI-D-15-0677.1

## UI/GIS
- NASA GIBS: https://gibs.earthdata.nasa.gov/
- GIBS WMTS: https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/default/
- Leaflet: https://leafletjs.com/
- D3.js: https://d3js.org/

## Ciencias de la tierra
- NASA Earth Observatory: https://earthobservatory.nasa.gov/
- NASA Earth Science Data System: https://earthdata.nasa.gov/
- IPCC AR6 WG1 (2021): https://www.ipcc.ch/report/ar6/wg1/
- NOAA Climate.gov: https://www.climate.gov/

## Entrega Space Apps Challenge
- NASA Earth Science/Climate Change: https://challenges.nasa.gov/challenges/earth-science-and-climate-change-2024
- GISTEMP data (dominio público)
- NSIDC Sea Ice Index (dominio público)
- POWER API (dominio público)
