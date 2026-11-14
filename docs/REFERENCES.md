# REFERENCES — data, tools and licences (for the submission form)

Everything listed here was used in this project and was checked live on
2026-11-14. Sections of the submission form it answers: «Space Agency Partner
Data» and «Other References».

## Space agency data

| Source | What we take | Access | Licence / citation |
|---|---|---|---|
| **NASA POWER** (power.larc.nasa.gov) | Monthly point and regional series for 15 variables (MERRA-2, CERES SYN1deg, GEWEX SRB 4-IP, GEOS-IT) | Public REST API, no account | NASA open data. Cite: NASA Langley Research Center (LaRC) POWER Project, *Prediction Of Worldwide Energy Resources*, https://power.larc.nasa.gov/. Parameter dictionary: https://power.larc.nasa.gov/api/website/metadata/parameters · Methodology: https://power.larc.nasa.gov/docs/methodology/ |
| **NASA GISTEMP v4** (data.giss.nasa.gov/gistemp) | Global surface temperature anomaly, 1880–present | Public files | NASA GISS open data. Cite: Lenssen et al. (2024), *A NASA GISTEMPv4 Observational Uncertainty Ensemble*, J. Geophys. Res. Atmos., doi:10.1029/2023JD040179 |
| **NSIDC Sea Ice Index v4** (nsidc.org/data/g02135) | Monthly Arctic and Antarctic sea ice extent | Public files | Cite: Fetterer, F., Knowles, K., Meier, W. N., Savoie, M., Windnagel, A. K. & Stafford, T. (2025). *Sea Ice Index* (G02135, Version 4). NSIDC. doi:10.7265/a98x-0f50 |
| **NASA Earth Observatory** (science.nasa.gov/earth/earth-observatory) | World of Change features and articles used in the knowledge corpus | Public web pages | NASA content is generally public domain; attribution given per document in `data/knowledge/docs.jsonl` (`publisher`, `url`, `license`) |
| **NASA Science** (science.nasa.gov) | Additional articles about Peru and South America, and the *Mission: Biomes* page used by the glossary | Public web pages | Same as above |
| **Giovanni / GES DISC** (giovanni.gsfc.nasa.gov) | GPM, GLDAS, AIRS, OMI and MODIS series exported as CSV by the team (Earthdata login) | Earthdata account | NASA open data; each CSV carries its product and version in the header |
| **MODIS Land** (modis-land.gsfc.nasa.gov) | MODIS land-product documentation | Public web | NASA open data. (The older host `modis.gsfc.nasa.gov` did not answer from this machine on 2026-11-14 and is therefore not cited.) |
| **NASA Technical Reports Server** (ntrs.nasa.gov) | Acker et al. (2009), method note on trend detection in remotely-sensed time series | Public API/record | NASA open data — https://ntrs.nasa.gov/citations/20090042747 |
| **Canadian Space Agency** (asc-csa.gc.ca) | SWOT mission page: launch date (16 December 2022), partner agencies and instrument coverage | Public web page | Government of Canada; cited with attribution — https://www.asc-csa.gc.ca/eng/satellites/swot/ |

The exact request URL, timestamp and sha256 of every download are stored in the
`provenance` field of each series and in each corpus document.

## Reference literature (method)

| Reference | DOI |
|---|---|
| Mann, H. B. (1945). Nonparametric tests against trend. *Econometrica*. | 10.2307/1907187 |
| Sen, P. K. (1968). Estimates of the regression coefficient based on Kendall's tau. *JASA*. | 10.1080/01621459.1968.10480934 |
| Hamed, K. H. & Rao, A. R. (1998). A modified Mann-Kendall trend test for autocorrelated data. *J. Hydrology*. | 10.1016/S0022-1694(97)00125-X |
| Weatherhead, E. C. et al. (1998). Factors affecting the detection of trends. *J. Geophys. Res.* | 10.1029/98JD00995 |
| Santer, B. D. et al. (2000). Statistical significance of trends… *J. Geophys. Res.* | 10.1029/1999JD901105 |
| Wilks, D. S. (2016). The stippling shows statistically significant grid points. *BAMS*. | 10.1175/BAMS-D-15-00267.1 |
| Gelaro, R. et al. (2017). MERRA-2. *J. Climate*. | 10.1175/JCLI-D-16-0758.1 |
| Rodell, M. et al. (2004). The Global Land Data Assimilation System. *BAMS*. | 10.1175/BAMS-85-3-381 |
| Lenssen, N. et al. (2024). GISTEMPv4 uncertainty ensemble. *JGR Atmos*. | 10.1029/2023JD040179 |
| Hussain, M. M. & Mahmud, I. (2019). pyMannKendall. *JOSS*. | 10.21105/joss.01556 |
| Acker, J. G. et al. (2009). Time-series analysis of remotely-sensed SeaWiFS chlorophyll in river-influenced coastal regions. *EARSeL eProceedings* 8(2). | NTRS 20090042747 |

All DOIs were resolved through DataCite/Crossref on 2026-11-14; abstracts were
used only where the publisher offers them openly (see `summary_by` in the corpus).
Publisher pages (Wiley, Taylor & Francis, JSTOR) answer 403 to automated clients
even for real articles, so the validator checks the DOI redirect and the metadata
record rather than the publisher's HTML.

## Gazetteer and place names

| Source | Use | Licence |
|---|---|---|
| **GeoNames cities15000** (download.geonames.org/export/dump/cities15000.zip) | 8 109 cities (all Peruvian cities kept) | CC BY 4.0 — https://www.geonames.org/export/ |
| **Wikidata** (wikidata.org) | Centre coordinates of 67 natural regions (P625) and, where stated, their N/S/E/W extremes (P1332–P1335) | CC0 |
| **OpenStreetMap Nominatim** (nominatim.openstreetmap.org) | Bounding boxes for regions, accepted only when they agree with the Wikidata centre | ODbL — © OpenStreetMap contributors |

## Glossary

| Source | Use | Licence |
|---|---|---|
| **AMS Glossary of Meteorology** (glossary.ametsoc.org) | Definitions for the 31-term glossary (English text; Spanish entries are translations marked as such) | American Meteorological Society; check terms of use before redistribution |
| **NASA Science — Mission: Biomes** (science.nasa.gov/kids/earth/mission-biomes) | Definition of *biome*, which has no standalone entry in the AMS Glossary | NASA (public domain) |

## Tools and libraries

| Tool | Use | Licence |
|---|---|---|
| Python 3.12 | Runtime | PSF |
| FastAPI / Uvicorn | API service | MIT / BSD |
| NumPy / SciPy | Statistics | BSD |
| requests + certifi | HTTP with TLS verification | Apache-2.0 / MPL-2.0 |
| BeautifulSoup + lxml | HTML extraction | MIT / BSD |
| Leaflet | Interactive map (UI) | BSD-2-Clause |
| Chart.js | Charts (UI) | MIT |
| NASA GIBS | Base map tiles (UI) | NASA open data |

## How the corpus is verified

`python scripts/validate_knowledge.py` checks that every catalog id is present,
both languages are complete, every DOI resolves (redirect + DataCite/Crossref
record), every non-DOI corpus URL answers 200, the stored title appears in the
page (for external articles), text length is 300–1200 characters, there are no
duplicate ids and every document has a sha256. It exits non-zero on any failure
and has been tested with a deliberately broken document.

Last full online run: **168 documents, 0 failures** (2026-11-14, round 2).
