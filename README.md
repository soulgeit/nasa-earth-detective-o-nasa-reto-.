# EarthTrend Detective

<!-- SI-assisted: claude-omni-1b (Claude Sonnet 5.5) -->

> A tool that helps students find out whether a climate trend in a place they care
> about is real — and how sure we can be. Built for the **NASA Space Apps Challenge 2026**
> (challenge: *select Earth-science variables, visualise how they change over time,
> and determine what is changing, where, how much, and whether the change is significant*).

**Public site:** <https://soulgeit.github.io/nasa-earth-detective-o-nasa-reto-./>  
**Live Interactive App & API (Railway):** <https://huiracochaia.soulgeit.com>

The public site is a **static, no-server backup**: it opens the seven frozen cases
and the two precomputed trend maps, in English and Spanish, on desktop and phone.
Live analysis, the detective, the trend map for new variables and Giovanni CSV
upload need the full app, which you run locally with the steps below; the backup
says so in both languages instead of failing.

---

## What it does

EarthTrend Detective fetches **real NASA data** for a point or a box on Earth,
measures the trend with robust statistics, and answers the four questions of the
challenge in plain language: **what** is changing, **where**, **how much**, and
**is it significant** — including the honest answer *"not yet, and here is how
many more years of data we need"*.

- **Live NASA data**, no account required: NASA POWER (MERRA-2; CERES SYN1deg and
  GEWEX SRB for radiation and aerosol), NASA GISTEMP v4 and the NSIDC Sea Ice
  Index v4.
- **A trend you can defend**: Theil–Sen slope with a 95 % confidence interval,
  Mann–Kendall with the Hamed–Rao autocorrelation correction, an annual
  Mann–Kendall test, and a least-squares t-test adjusted for autocorrelation
  (Santer et al. 2000). When the tests disagree, the warning `TESTS_DISAGREE`
  drops the verdict one level; it is never silently averaged away.
- **"How many years are still missing?"** from Weatherhead et al. (1998).
- **Trend maps** with false-discovery-rate control (Benjamini–Hochberg), so a
  single significant cell among hundreds is not sold as a finding.
- **A conversational detective that cites (Huiracocha IA)**: it answers in plain
  language, remembers the place and variable of the conversation, and retrieves from a
  verified corpus of about 1,000 documents (NASA, NOAA, SENAMHI, peer-reviewed papers;
  five Peruvian cities documented in depth). Every claim carries a title, a publisher
  and a URL, and the assistant never produces numbers or coordinates. "What is
  changing in Huancayo?" tests all 32 point variables at once, with the
  Benjamini–Hochberg correction across them.
- **Visible provenance** on every result: source, exact request URL, retrieval
  date and the sha256 of the raw response.
- **English and Spanish**, English first; the public site opens in English.

### The seven frozen cases

| Case | Variable | Verdict |
|---|---|---|
| Lima, Peru | 2 m air temperature (`T2M`) | Significant trend |
| Svalbard, Norway | 2 m air temperature (`T2M`) | Clear, strong trend |
| Piura, Peru | Precipitation (`PRECTOTCORR`) | Suggestive, not yet certain |
| Arctic sea ice | Sea ice extent (`SEAICE_EXTENT_N`) | Clear, strong trend |
| Antarctic sea ice | Sea ice extent (`SEAICE_EXTENT_S`) | No trend detectable so far |
| Amazon basin (Giovanni CSV) | 2 m air temperature (`T2M`) | Clear, strong trend |
| Amazon basin (Giovanni CSV) | Precipitation (`PRECTOTCORR`) | No trend detectable so far |

The cases are frozen snapshots with their own `series.json`, `analysis.json` and
`case.json`; the app shows them without recalculating, so everyone sees the same
numbers and the same provenance. Regenerate them with
`python scripts/regenerate_cases_v2.py`.

## Quick start

Requires **Python 3.12**. On Windows, if `python` opens the Microsoft Store
instead of running (the `WindowsApps` stub), use `py -3.12` or the interpreter
you installed, in place of `python` in the commands below.

```bash
python -m venv .venv
.venv\Scripts\activate            # Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt

python -m uvicorn src.api.main:app --host 127.0.0.1 --port 8791
# open http://127.0.0.1:8791/  ·  API docs at /docs
```

The app works with **no language model**: the planner uses rules and the
explanation quotes the cited sources (`AI_MODE=extractive`, the default and the mode the
public server runs; the "how it works" panel of the app reports the mode it is in).

### How to check it

```bash
pip install -r requirements-dev.txt     # pytest + httpx, only needed for the checks
python -m pytest -q                     # the full suite
python scripts/gate.py                  # one command: suite, smoke, datasets, knowledge
python scripts/smoke_api.py http://127.0.0.1:8791
python scripts/validate_datasets.py data/cases/*/series.json
python -X utf8 -I scripts/validate_knowledge.py --max-url-checks 100
```

`scripts/gate.py` runs the whole quality gate and exits non-zero if anything
fails; it is the command the team used at every integration window.

### The optional local planner (LoRA)

`AI_MODE=full PLANNER_MODEL=local-lora` switches the planner to a small
fine-tuned model that runs **locally only** (the free public server cannot host
it). The adapter is loaded in-process from `models/etd-planner-lora`; it is not
the default and it is not needed to use the app:

```bash
pip install -r requirements.txt -r requirements-ml.txt   # needs a GPU; several GB
AI_MODE=full PLANNER_MODEL=local-lora python -m uvicorn src.api.main:app --port 8791
# or evaluate the planner alone:
AI_MODE=full PLANNER_MODEL=local-lora python -m src.detective.rag.eval_plan --planner local-lora
```

Measured on the 50 hand-written reference questions: **rules 49/50 (0.98)**;
**LoRA 40/50 (0.80)** on a 4-bit GPU (37/50 on CPU), median 2.2 s per question.
On the 200-case templated test set the adapter gets 84.5 % exact variables against
15.5 % for the rules baseline; that set shares its generator with the training
data, which is why it is reported next to the hand-written result, not instead of
it. The model card is in [`src/ml/MODEL_CARD.md`](src/ml/MODEL_CARD.md), the
numbers in [`docs/EVAL_IA.md`](docs/EVAL_IA.md).

## Data sources

| Source | What we take | Access |
|---|---|---|
| **NASA POWER** | Monthly point and regional series for 32 variables (MERRA-2, CERES SYN1deg, GEWEX SRB 4-IP, GEOS-IT) | Public REST API, no account |
| **NASA GISTEMP v4** | Global surface temperature anomaly, 1880–present | Public files |
| **NSIDC Sea Ice Index v4** | Arctic and Antarctic monthly sea ice extent | Public files |
| **Giovanni (GES DISC)** | GPM, GLDAS, AIRS, OMI and MODIS series, exported as CSV and uploaded by the user | Earthdata account |
| **NASA Earth Observatory / NASA Science** | Articles and biome profiles for the knowledge corpus | Public pages |
| **Canadian Space Agency** | SWOT mission page (launch date and partners) | Public page |

The catalogue lists **15 available variables** and **10 planned Giovanni
variables**. The planned ones are declared with `available: false`: they are never
counted as available and never offered for analysis. When a student asks for one,
the detective answers `no_match` and explains that it is loaded by uploading the
Giovanni CSV, rather than approximating it with a different product.

Every source, tool and licence — with URLs and the citation each asks for — is in
[`docs/REFERENCES.md`](docs/REFERENCES.md).

## Statistical method

| Step | Method | Reference |
|---|---|---|
| Slope | Theil–Sen (median of pairwise slopes) + 95 % CI | Sen (1968) |
| Monthly trend | Mann–Kendall with Hamed–Rao autocorrelation correction | Mann (1945), Hamed & Rao (1998) |
| Annual trend | Mann–Kendall on annual means | Mann (1945) |
| Linear fit | OLS with a t-test adjusted for autocorrelation | Santer et al. (2000) |
| Years needed | Weatherhead detectability | Weatherhead et al. (1998) |
| Grid maps | Benjamini–Hochberg false discovery rate | Wilks (2016) |

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
- The LoRA planner runs locally only, and the team's measurement (40/50) is below
  the rules (49/50); that is why the product plans with rules.
- The public static backup cannot analyse new places or variables, run the
  detective, or accept a CSV upload — it shows the frozen cases and maps only.
- If a source is down, the API returns an explicit error code. It never
  substitutes another dataset.

## Repository map

| Path | Contents |
|---|---|
| `src/etl/` | NASA connectors (POWER, GISTEMP, NSIDC, Giovanni CSV), cache and provenance |
| `src/stats/` | Trend engine: Sen, Mann–Kendall, OLS, detectability, grid analysis |
| `src/detective/` | Retrieval, planner and guarded explanation |
| `src/ml/` | Optional LoRA planner: dataset builder, training, evaluation, CLI and model card |
| `src/api/` | FastAPI service implementing the contract in `docs/CONTRATOS.md` |
| `src/ui/` | Static interface (Leaflet + Chart.js), English and Spanish |
| `data/catalog/` | Variable catalogue, gazetteer and regions |
| `data/knowledge/` | Verified corpus, golden questions |
| `data/cases/`, `data/atlas/` | Seven frozen cases and precomputed trend maps |
| `data/lora/` | Planner training dataset (generated by script) and its dataset card |
| `docs/` | Plan, contracts, statistical validation, references, evaluation, submission texts |

## Use of AI

This project was built with AI agents under human direction, and the challenge
requires declaring it: the per-file record is in
[`docs/AI_USE_LOG.md`](docs/AI_USE_LOG.md), and generated code carries an
`SI-assisted:` line. The product also contains a small open-weight language model
fine-tuned with LoRA to turn questions into structured plans; its dataset was
generated by script and is documented in
[`data/lora/DATASET_CARD.md`](data/lora/DATASET_CARD.md). No generative model
produces figures or coordinates: every number comes from the statistical engine
and every place from the gazetteer or a map click.

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
