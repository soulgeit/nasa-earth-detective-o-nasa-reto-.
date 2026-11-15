# EarthTrend Detective

> NASA Space Apps Challenge 2026 · a tool that helps students find out whether a
> climate trend in a place they care about is real, and how sure we can be.

EarthTrend Detective fetches **real NASA data** for any point or box on Earth,
measures the trend with robust statistics, and answers four questions in plain
language: **what** is changing, **where**, **how much**, and **is it significant** —
including the honest answer "not yet, and here is how many more years we need".

## What it does

- **Live NASA data**, no account required: NASA POWER (MERRA-2, CERES SYN1deg),
  NASA GISTEMP v4 and the NSIDC Sea Ice Index v4.
- **A trend you can defend**: Theil-Sen slope with a 95 % confidence interval,
  Mann-Kendall (with the Hamed-Rao autocorrelation correction), an annual
  Mann-Kendall test, and an ordinary least-squares t-test adjusted for
  autocorrelation (Santer et al. 2000). One warning, `TESTS_DISAGREE`, fires when
  the tests do not agree, and the verdict drops a level.
- **"How many years are still missing?"** from Weatherhead et al. (1998).
- **Trend maps** with false-discovery-rate control (Benjamini-Hochberg, Wilks 2016),
  so a single significant cell among hundreds is not sold as a finding.
- **A detective that cites**: retrieval over a verified corpus of NASA articles,
  method notes and glossary entries; every claim carries a title, a publisher and
  a URL, and the assistant never produces numbers or coordinates.
- **Visible provenance** on every result: source, exact request URL, retrieval
  date and the sha256 of the raw response.
- **English and Spanish**, with English first.

## Quick start

Requires **Python 3.12**. On Windows, if `python` opens the Microsoft Store
instead of running (the `WindowsApps` stub), use `py -3.12` or the interpreter
you installed, in place of `python` in the commands below.

```bash
python -m venv .venv
.venv\Scripts\activate            # Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt

python -m uvicorn src.api.main:app --host 127.0.0.1 --port 8791
# open http://127.0.0.1:8791/  · API docs at /docs
```

Run the checks:

```bash
pip install -r requirements-dev.txt     # pytest + httpx: only the checks need them
python -m pytest -q
python scripts/smoke_api.py http://127.0.0.1:8791
python scripts/validate_datasets.py data/cases/*/series.json
python scripts/validate_knowledge.py            # catalog + knowledge corpus
```

With `AI_MODE=extractive` (the default for public deployments) everything works
without a language model: retrieval uses BM25, the planner uses rules and the
explanation quotes the cited sources.

## Data sources

| Source | What we take | Access |
|---|---|---|
| **NASA POWER** | Monthly point and regional series for 12 atmospheric, land and cryosphere variables (MERRA-2; CERES SYN1deg and GEWEX SRB 4-IP for radiation and aerosol) | Public REST API |
| **NASA GISTEMP v4** | Global surface temperature anomaly, 1880–present | Public files |
| **NSIDC Sea Ice Index v4** | Arctic and Antarctic monthly sea ice extent | Public files |
| **Giovanni (GES DISC)** | GPM, GLDAS, AIRS, OMI and MODIS series, exported as CSV and uploaded by the user | Earthdata account |
| **NASA Earth Observatory / NASA Science** | Articles and biome profiles for the knowledge corpus | Public pages |
| **Canadian Space Agency** | SWOT mission page (launch date and partners) | Public page |

The catalogue lists **15 available variables** and **10 planned Giovanni
variables**. The planned ones are declared with `available: false`: they are never
counted as available and never offered for analysis. When a student asks for one,
the detective answers `no_match` and explains that it is loaded by uploading the
Giovanni CSV.

Every source, tool and licence is listed in [`docs/REFERENCES.md`](docs/REFERENCES.md).

## Statistical method

| Step | Method | Reference |
|---|---|---|
| Slope | Theil-Sen (median of pairwise slopes) + 95 % CI | Sen (1968) |
| Monthly trend | Mann-Kendall with Hamed-Rao autocorrelation correction | Mann (1945), Hamed & Rao (1998) |
| Annual trend | Mann-Kendall on annual means | Mann (1945) |
| Linear fit | OLS with a t-test adjusted for autocorrelation | Santer et al. (2000) |
| Years needed | Weatherhead detectability | Weatherhead et al. (1998) |
| Grid maps | Benjamini-Hochberg false discovery rate | Wilks (2016) |

Verdicts are `SIGNIFICANT_STRONG`, `SIGNIFICANT`, `SUGGESTIVE`, `NOT_SIGNIFICANT`
or `INSUFFICIENT_DATA`. `SIGNIFICANT_STRONG` requires **all** tests to agree and
enough years of record. Sensitivity to the analysis choices and agreement with
published values are documented in
[`docs/VALIDACION_ESTADISTICA.md`](docs/VALIDACION_ESTADISTICA.md).

## Known limits

- Gridded reanalysis averages a ~50 km cell: it cannot resolve a single valley,
  a street or a peak.
- Several POWER variables splice two source products (radiation and cloud amount:
  GEWEX SRB up to 2000, CERES SYN1deg from 2001). The catalogue records the splice
  in `homogeneous_since`; a trend across it may be artificial.
- MODIS, GPM, AIRS, OMI and GLDAS data are only available through a CSV the user
  exports from Giovanni; without that file the variable is reported as planned,
  never approximated by a different product.
- The LoRA planner, if trained, runs locally only: the free public server cannot
  run a language model. The public deployment plans with rules and explains with
  cited excerpts.
- If a source is down, the API returns an explicit error code. It never
  substitutes another dataset.

## Repository map

| Path | Contents |
|---|---|
| `src/etl/` | NASA connectors (POWER, GISTEMP, NSIDC, Giovanni CSV), cache and provenance |
| `src/stats/` | Trend engine: Sen, Mann-Kendall, OLS, detectability, grid analysis |
| `src/detective/` | Retrieval, planner and guarded explanation |
| `src/api/` | FastAPI service implementing the contract in `docs/CONTRATOS.md` |
| `src/ui/` | Static interface (Leaflet + Chart.js), English and Spanish |
| `data/catalog/` | Variable catalogue and gazetteer |
| `data/knowledge/` | Verified corpus, golden questions |
| `data/cases/`, `data/atlas/` | Frozen cases and precomputed trend maps |
| `data/lora/` | Planner training dataset (generated by program) |
| `docs/` | Plan, contracts, statistical validation, references, submission texts |

## Use of AI

This project was built with AI agents under human direction; the challenge
requires declaring it. The per-file record is in
[`docs/AI_USE_LOG.md`](docs/AI_USE_LOG.md). Generated code carries an
`SI-assisted:` line. No generative model produces figures or coordinates: every
number comes from the statistical engine and every place from the gazetteer or a
map click.

## Licence and third-party notices

Code: **MIT**, see [`LICENSE`](LICENSE). <<HUMANO: confirm MIT for the code and
decide the licence for our own derived data (proposal: CC BY 4.0).>>

**Our data is not ours to license.** Every series comes from a source with its
own terms, and the application shows that source next to every figure:

| Source | Terms and citation |
|---|---|
| [NASA POWER](https://power.larc.nasa.gov/) (MERRA-2, CERES/SRB) | Public domain. Cite: NASA Prediction Of Worldwide Energy Resources (POWER) project. |
| [NASA GISTEMP v4](https://data.giss.nasa.gov/gistemp/) | Public domain. Cite: GISTEMP Team, *GISS Surface Temperature Analysis*, NASA GISS. |
| [NSIDC Sea Ice Index v4](https://nsidc.org/data/g02135) | Cite: Fetterer et al., *Sea Ice Index*, NSIDC, with the DOI of the version used. |
| Giovanni / GES DISC (GPM, MODIS, OMI, GLDAS, AIRS) | Public domain. Cite the mission and dataset named in the exported CSV header. |

**Libraries and fonts bundled or loaded by the interface:**

- [Leaflet](https://leafletjs.com/) 1.9.4 — BSD-2-Clause.
- [Chart.js](https://www.chartjs.org/) 4.4.1 — MIT.
- [Schibsted Grotesk](https://fonts.google.com/specimen/Schibsted+Grotesk) and
  [Source Serif 4](https://fonts.google.com/specimen/Source+Serif+4) — SIL Open
  Font License 1.1, served by Google Fonts.
- Base map tiles: [NASA GIBS](https://earthdata.nasa.gov/eosdis/science-system-description/eosdis-components/gibs)
  Blue Marble (public domain) with [OpenStreetMap](https://www.openstreetmap.org/copyright)
  contributors (ODbL) as the fallback, each attributed on the map.
- Python packages: see `requirements.txt`; each keeps its own licence
  (FastAPI MIT; Starlette, Uvicorn, NumPy and SciPy BSD-3-Clause;
  pymannkendall MIT). Read from the `LICENSE` file shipped in each
  installed package, not from memory.

NASA does not endorse this project, and no NASA branding is used beyond the
factual citation of its data.

---

*Data: NASA POWER, NASA GISTEMP, NSIDC, NASA Earth Observatory, Giovanni (GES DISC).
NASA does not endorse this project; the name does not use NASA branding.*
