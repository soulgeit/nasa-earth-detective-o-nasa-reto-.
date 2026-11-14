# SI-assisted: claude-omni-3 (Claude Opus 5.5)
"""
Modelos Pydantic de la API v2 con los esquemas del contrato (§3, §4, §5, §10).

Se declaran con los campos del contrato y validación estricta de las
invariantes que la API promete a sus clientes. Los cálculos viven en
`src/stats`; aquí solo se describe y se valida la forma.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

Lang = Literal["es", "en"]
RegionKind = Literal["point", "bbox", "named"]
Aggregation = Literal["point", "area_mean_coslat"]
ProvenanceKind = Literal["nasa_api", "nasa_file", "user_upload", "fixture"]
VerdictCode = Literal[
    "SIGNIFICANT_STRONG",
    "SIGNIFICANT",
    "SUGGESTIVE",
    "NOT_SIGNIFICANT",
    "INSUFFICIENT_DATA",
]
WarningCode = Literal[
    "SHORT_RECORD",
    "LOW_COVERAGE",
    "HIGH_AUTOCORRELATION",
    "SOURCE_SPLICE",
    "TESTS_DISAGREE",
    "REANALYSIS_CAVEAT",
]
Sphere = Literal["atmosphere", "land", "ocean", "cryosphere", "biosphere"]
Intent = Literal["investigate", "compare", "define", "out_of_scope", "no_match"]
Hypothesis = Literal["up", "down", "unknown"]


class Provenance(BaseModel):
    """§3 — de dónde sale cada número."""

    model_config = ConfigDict(extra="allow")

    kind: ProvenanceKind
    source: str
    underlying: str | None = None
    request_url: str
    retrieved_at: str = Field(description="ISO 8601 en UTC")
    sha256: str = Field(min_length=8)
    native_resolution: str | None = None
    citation: str | None = None


class Region(BaseModel):
    model_config = ConfigDict(extra="allow")

    kind: RegionKind
    name: str | None = None
    lat: float | None = Field(default=None, ge=-90.0, le=90.0)
    lon: float | None = Field(default=None, ge=-180.0, le=180.0)
    bbox: list[float] | None = None

    @field_validator("bbox")
    @classmethod
    def _bbox_valid(cls, v: list[float] | None) -> list[float] | None:
        if v is None:
            return v
        if len(v) != 4:
            raise ValueError("bbox must be [west, south, east, north]")
        west, south, east, north = v
        if not (-180.0 <= west <= 180.0 and -180.0 <= east <= 180.0):
            raise ValueError("bbox longitudes out of range")
        if not (-90.0 <= south <= 90.0 and -90.0 <= north <= 90.0):
            raise ValueError("bbox latitudes out of range")
        if west >= east:
            raise ValueError("bbox requires west < east")
        if south >= north:
            raise ValueError("bbox requires south < north")
        return v


class TimeSeriesPoint(BaseModel):
    date: str = Field(pattern=r"^\d{4}-\d{2}$")
    value: float | None = None


class TimeSeries(BaseModel):
    """§3 — TimeSeries v2."""

    model_config = ConfigDict(extra="allow")

    schema: Literal["timeseries/2"] = "timeseries/2"
    variable_id: str
    unit: str
    cadence: Literal["monthly"] = "monthly"
    region: Region
    aggregation: Aggregation
    data: list[TimeSeriesPoint]
    provenance: Provenance

    @model_validator(mode="after")
    def _dates_increasing(self) -> "TimeSeries":
        dates = [p.date for p in self.data]
        if dates != sorted(dates):
            raise ValueError("data dates must be strictly increasing")
        if len(set(dates)) != len(dates):
            raise ValueError("data dates must not contain duplicates")
        return self


class TrendBlock(BaseModel):
    direction: Literal["up", "down", "flat"]
    sen_slope_per_decade: float | None = None
    sen_ci95_per_decade: list[float] | None = None
    ols_slope_per_decade: float | None = None
    ols_ci95_per_decade: list[float] | None = None
    r_squared: float | None = None
    total_change: float | None = None
    percent_per_decade: float | None = None


class MKTest(BaseModel):
    tau: float | None = None
    z: float | None = None
    p_value: float | None = None
    p_value_autocorr: float | None = None
    correction: str | None = None


class MKAnnualTest(BaseModel):
    n: int
    tau: float | None = None
    p_value: float | None = None


class TTestOLS(BaseModel):
    t: float | None = None
    df: int | None = None
    p_value: float | None = None
    adjusted_for_autocorrelation: bool | None = None


class Tests(BaseModel):
    mann_kendall: MKTest
    mann_kendall_annual: MKAnnualTest | None = None
    t_test_ols: TTestOLS


class Significance(BaseModel):
    is_significant: bool
    verdict_code: VerdictCode
    level: str | None = None
    tests_agree: bool | None = None


class Detectability(BaseModel):
    years_needed: float | None = None
    years_available: float | None = None
    more_years_needed: float | None = None
    method: str | None = None


class AnnualPoint(BaseModel):
    year: int
    value: float | None = None
    n_months: int


class SeriesBlock(BaseModel):
    dates: list[str]
    raw: list[float | None]
    climatology: list[float | None]
    anomalies: list[float | None]
    trend_line: list[float | None]
    trend_ci_low: list[float | None]
    trend_ci_high: list[float | None]
    annual: list[AnnualPoint]


class Answers(BaseModel):
    """§4 — plantillas deterministas, bilingües, nunca afirman causa."""

    what: dict[str, str]
    where: dict[str, str]
    how_much: dict[str, str]
    significant: dict[str, str]
    detectability: dict[str, str]


class AnalysisResult(BaseModel):
    """§4 — AnalysisResult v2. La `variable` la añade la API."""

    model_config = ConfigDict(extra="allow")

    schema: Literal["analysis/2"] = "analysis/2"
    variable: dict[str, Any] | None = None
    region: Region
    period: dict[str, Any]
    method: dict[str, Any]
    trend: TrendBlock
    tests: Tests
    significance: Significance
    detectability: Detectability
    series: SeriesBlock
    answers: Answers
    warnings: list[WarningCode] = Field(default_factory=list)
    provenance: Provenance


class TrendMapSummary(BaseModel):
    share_up_significant: float = 0.0
    share_down_significant: float = 0.0


class TrendMap(BaseModel):
    """§5 — TrendMap v2."""

    model_config = ConfigDict(extra="allow")

    schema: Literal["trendmap/2"] = "trendmap/2"
    variable_id: str
    unit_per_decade: str
    bbox: list[float]
    lats: list[float]
    lons: list[float]
    slope_per_decade: list[list[float | None]]
    p_value: list[list[float | None]]
    significant_fdr: list[list[bool | None]]
    fdr_q: float = 0.10
    n_cells: int
    n_significant: int
    period: dict[str, str]
    summary: TrendMapSummary
    provenance: dict[str, Any]


class ComparisonStatement(BaseModel):
    es: str
    en: str


class Comparison(BaseModel):
    opposite: bool
    difference_significant: bool
    z: float | None = None
    statement: ComparisonStatement


class CompareResult(BaseModel):
    a: AnalysisResult
    b: AnalysisResult
    compare: Comparison


class InvestigationPlan(BaseModel):
    """§10 — plan del detective. La IA no produce más que estructura."""

    intent: Intent
    variable_ids: list[str] = Field(default_factory=list)
    place: str | None = None
    place_b: str | None = None
    start_year: int | None = None
    end_year: int | None = None
    last_n_years: int | None = None
    hypothesis: Hypothesis = "unknown"
    lang: Lang = "es"
    mode: Literal["lora", "llm", "rules"] | None = None


class Explanation(BaseModel):
    text: str
    citations: list[dict[str, Any]]
    guard: dict[str, Any]
    mode: Literal["llm", "extractive"]
    lang: Lang = "es"


class ScoutResult(BaseModel):
    lat: float
    lon: float
    profile: dict[str, Any] = Field(default_factory=dict)
    candidates: list[dict[str, Any]] = Field(default_factory=list)
    mode: Literal["llm", "extractive", "rules"]
