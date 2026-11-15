# REFERENCES — data, tools and licences (for the submission form)

<!-- SI-assisted: claude-omni-1b (Claude Sonnet 5.5) -->

Everything listed here is used by this project. Every URL in this file was
re-checked live on **2026-11-15**; the only ones that answer 4xx to an automated
client are the publisher pages listed in “What the validator checks”, and each of
those is resolved through Crossref or DataCite instead. This file answers the
submission-form sections «Space Agency Partner Data» and «Other References»
(`docs/KIT_ENTREGA.md` §4).

What the app's seven frozen cases and fifteen available variables actually draw
on is stated in §1–§2; nothing is listed “for looks”.

## 1. Data sources used by the seven cases and the fifteen variables

| Variable(s) in the app | Source | What we take | Access | Citation the source asks for |
|---|---|---|---|---|
| `T2M`, `TS`, `PRECTOTCORR`, `GWETTOP`, `EVLAND`, `SNODP`, `RH2M`, `TQV`, `TO3` | **NASA POWER** (power.larc.nasa.gov), MERRA-2 | Monthly point and regional series, 1981–2025 | Public REST API, no account | NASA Langley Research Center (LaRC) POWER Project. *Prediction Of Worldwide Energy Resources.* https://power.larc.nasa.gov/ · Methodology: https://power.larc.nasa.gov/docs/methodology/ · MERRA-2: Gelaro et al. (2017), doi:10.1175/JCLI-D-16-0758.1 |
| `AOD_55`, `CLOUD_AMT`, `ALLSKY_SFC_SW_DWN` | **NASA POWER** (CERES SYN1deg; GEWEX SRB 4-IP for radiation and cloud amount up to 2000) | Monthly series, 1984/2001 onward | Public REST API, no account | As above. Product pages: https://power.larc.nasa.gov/docs/methodology/data/sources_fluxes/ and https://power.larc.nasa.gov/docs/methodology/data/sources_clds_aerosols/ |
| `GISTEMP_TANOM` | **NASA GISS Surface Temperature Analysis (GISTEMP v4)** | Global surface temperature anomaly, 1880–present | Public files, no account | Lenssen et al. (2024), *A NASA GISTEMPv4 Observational Uncertainty Ensemble*, J. Geophys. Res. Atmos., doi:10.1029/2023JD040179 · https://data.giss.nasa.gov/gistemp/ |
| `SEAICE_EXTENT_N`, `SEAICE_EXTENT_S` | **NSIDC Sea Ice Index, Version 4** (G02135) | Monthly Arctic and Antarctic sea ice extent, 1978–present | Public files, no account | Fetterer, F., Knowles, K., Meier, W. N., Savoie, M., Windnagel, A. K. & Stafford, T. (2025). *Sea Ice Index, Version 4.* NSIDC. doi:10.7265/a98x-0f50 · https://nsidc.org/data/g02135/versions/4 |
| `amazonia-t2m`, `amazonia-prectotcorr` (cases) | **NASA GES DISC — Giovanni**, MERRA-2 products `M2SMNXSLV_5_12_4_T2MMEAN` and `M2TMNXFLX_5_12_4_PRECTOTCORR` | Area-averaged monthly time series for the Amazon box, exported as CSV by the team | Earthdata account (the user exports the CSV) | NASA GES DISC. *Giovanni — the bridge between data and science.* https://giovanni.gsfc.nasa.gov/giovanni/ · Each CSV carries its product name, version and a “URL to Reproduce Results” that the app stores verbatim in the result's `provenance` |

The exact request URL, retrieval timestamp and sha256 of every download are
stored in the `provenance` field of each series and shown in the app under
“Where this comes from”.

## 2. Data and resources used for the knowledge corpus and the gazetteer

| Source | What we take | Licence | Link |
|---|---|---|---|
| **NASA Earth Observatory** (science.nasa.gov/earth/earth-observatory) | 40 articles used in the cited corpus | NASA content is generally public domain; attribution given per document (`publisher`, `url`, `license` in `data/knowledge/docs.jsonl`) | https://science.nasa.gov/earth/earth-observatory/ |
| **NASA Science** (science.nasa.gov) | 12 articles about Peru / South America and the *Mission: Biomes* pages used by 16 biome profiles and by the glossary term *biome* | As above | https://science.nasa.gov/ · https://science.nasa.gov/kids/earth/mission-biomes/ |
| **NASA POWER parameter dictionary** (power.larc.nasa.gov) | 24 variable cards (one per variable, in English and Spanish) | NASA open data | https://power.larc.nasa.gov/api/website/metadata/parameters |
| **AMS Glossary of Meteorology** (glossary.ametsoc.org) | Definitions for 31 of the 32 glossary terms (English text; Spanish entries are our translations, marked as such) | American Meteorological Society; check the glossary's terms of use before redistributing the text | https://glossary.ametsoc.org/wiki/anomaly/ (one page per term) |
| **NASA Technical Reports Server (NTRS)** | Acker et al. (2009), method note on trend detection in remotely-sensed time series | NASA open data | https://ntrs.nasa.gov/citations/20090042747 |
| **Canadian Space Agency** | The SWOT mission page: launch date (16 December 2022), partner agencies and instrument coverage | Government of Canada; cited with attribution | https://www.asc-csa.gc.ca/eng/satellites/swot/ |
| **Journal abstracts** (via Crossref, for the method notes) | Published abstracts of the method papers listed in §3, quoted only where the publisher offers them openly | Each publisher's terms; only openly available abstracts are stored | See DOIs in §3 |
| **GeoNames — cities15000** | 8 109 cities (every Peruvian city in the dump is kept) | CC BY 4.0 | https://www.geonames.org/export/ · https://download.geonames.org/export/dump/cities15000.zip |
| **Wikidata** | Centre coordinates of 67 natural regions (P625) and, where stated, their N/S/E/W extremes (P1332–P1335) | CC0 | https://www.wikidata.org/ |
| **OpenStreetMap Nominatim** | Bounding boxes for regions, accepted only when they agree with the Wikidata centre | ODbL — © OpenStreetMap contributors | https://nominatim.openstreetmap.org/ |

## 3. Reference literature (method)

| Reference | DOI |
|---|---|
| Mann, H. B. (1945). Nonparametric tests against trend. *Econometrica* 13(3). | 10.2307/1907187 |
| Sen, P. K. (1968). Estimates of the regression coefficient based on Kendall's tau. *JASA* 63(324). | 10.1080/01621459.1968.10480934 |
| Hamed, K. H. & Rao, A. R. (1998). A modified Mann-Kendall trend test for autocorrelated data. *J. Hydrology* 204. | 10.1016/S0022-1694(97)00125-X |
| Weatherhead, E. C. et al. (1998). Factors affecting the detection of trends: statistical considerations and applications to environmental data. *J. Geophys. Res.* 103(D14). | 10.1029/98JD00995 |
| Santer, B. D. et al. (2000). Statistical significance of trends and trend differences in layer-average atmospheric temperature time series. *J. Geophys. Res.* 105(D6). | 10.1029/1999JD901105 |
| Wilks, D. S. (2016). “The stippling shows statistically significant grid points”: How research results are routinely overstated and overinterpreted, and what to do about it. *BAMS* 97(12). | 10.1175/BAMS-D-15-00267.1 |
| Gelaro, R. et al. (2017). The Modern-Era Retrospective Analysis for Research and Applications, Version 2 (MERRA-2). *J. Climate* 30. | 10.1175/JCLI-D-16-0758.1 |
| Rodell, M. et al. (2004). The Global Land Data Assimilation System. *BAMS* 85(3). | 10.1175/BAMS-85-3-381 |
| Lenssen, N. et al. (2024). A NASA GISTEMPv4 Observational Uncertainty Ensemble. *J. Geophys. Res. Atmos.* | 10.1029/2023JD040179 |
| Hussain, M. M. & Mahmud, I. (2019). pyMannKendall: a python package for non parametric Mann Kendall family of trend tests. *JOSS* 4(39). | 10.21105/joss.01556 |
| Acker, J. G. et al. (2009). Time-series analysis of remotely-sensed SeaWiFS chlorophyll in river-influenced coastal regions. *EARSeL eProceedings* 8(2). | NTRS record 20090042747 |

## 4. Tools and libraries actually used

| Tool | Where | Licence |
|---|---|---|
| Python 3.12 | Runtime | PSF-2.0 |
| FastAPI, Starlette, Uvicorn, Pydantic | API service | MIT / BSD-3-Clause |
| NumPy, SciPy | Statistics | BSD-3-Clause |
| requests + certifi | HTTP with TLS verification | Apache-2.0 / MPL-2.0 |
| pymannkendall | Mann-Kendall tests | MIT |
| pytest, httpx | Test suite only (`requirements-dev.txt`) | MIT / BSD-3-Clause |
| **Leaflet 1.9.4** (CDN) | Interactive map | BSD-2-Clause — https://leafletjs.com/ |
| **Chart.js 4.4.1** (CDN) | Charts | MIT — https://www.chartjs.org/ |
| **NASA GIBS Blue Marble** tiles | Default map basemap | NASA open data — https://gibs.earthdata.nasa.gov/ |
| **OpenStreetMap** tiles | Fallback basemap (used when GIBS tiles fail) | ODbL — © OpenStreetMap contributors, https://www.openstreetmap.org/copyright |
| **Google Fonts**: Schibsted Grotesk, Source Serif 4 | UI typography | SIL Open Font License 1.1 — https://fonts.google.com/ |
| **Hugging Face `SmolLM2-1.7B-Instruct`** | Base model of the optional local planner adapter | Apache-2.0 — https://huggingface.co/HuggingFaceTB/SmolLM2-1.7B-Instruct |
| **PEFT (LoRA)**, PyTorch, Transformers, bitsandbytes | Optional local LoRA planner only (`requirements-ml.txt`) | Apache-2.0 / BSD-3-Clause / MIT |
| **`etd-planner-lora`** adapter (trained by this team) | Optional local planner | We release it with the repository; details in `src/ml/MODEL_CARD.md` |

The public deployment plans with rules and explains with cited excerpts; the
LoRA adapter is an optional local mode and is never loaded on the public server.

## 5. How references are validated

`docs/KIT_ENTREGA.md` §1 requires listing every data source, tool and licence,
so this file is part of the deliverable, not a nicety. The corpus that the app
quotes is checked by the same command the README publishes:

```bash
python -X utf8 -I scripts/validate_knowledge.py --max-url-checks 100
```

It confirms that every catalog id has its card, both languages are complete,
every DOI resolves (redirect + Crossref/DataCite metadata record), every non-DOI
corpus URL answers 200, the stored title appears in the page (for external
articles), text length is 300–1200 characters, there are no duplicate ids and
every document carries a sha256. It exits non-zero on any failure.

Last full online run: **catalog: 15 available + 10 planned; corpus: 168
documents (64 glossary entries = 32 terms in two languages, 35 articles, 30
variable cards, 16 biome profiles, 13 method notes, 10 paper abstracts);
0 failures** (2026-11-15).

Some publisher sites answer **403 to any automated client** even for real
articles (Wiley, Taylor & Francis, JSTOR, the AMS glossary landing page). For
those the validator checks the DOI redirect and the metadata record from
Crossref or DataCite instead of the publisher's HTML, and for the glossary it
quotes only individual term pages, which do answer 200.
