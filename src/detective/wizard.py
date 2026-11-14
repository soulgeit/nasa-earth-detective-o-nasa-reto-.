"""
Wizard interactivo para convertir preguntas simples de estudiantes
en consultas formales de datos de la NASA.
"""

from typing import Dict, Any, List

QUESTIONS_FLOW = [
    {
        "step": 1,
        "question": "¿Qué fenómeno del planeta Tierra te preocupa o deseas investigar?",
        "options": [
            {
                "label": "Deforestación y pérdida de vegetación",
                "target_variable": "MODIS_NDVI",
                "recommended_region": "amazon_deforestation_arc"
            },
            {
                "label": "Calentamiento global y olas de calor",
                "target_variable": "MERRA2_T2M",
                "recommended_region": "arctic_svalbard"
            },
            {
                "label": "Desaparición de lagos o embalses",
                "target_variable": "SWOT_WATER_ELEV",
                "recommended_region": "aral_sea"
            },
            {
                "label": "Sequías y pérdida de humedad en cultivos",
                "target_variable": "GLDAS_SOILM",
                "recommended_region": "california_central_valley"
            }
        ]
    }
]


def resolve_detective_intent(phenomenon_choice: str) -> Dict[str, str]:
    """Mapea la opción seleccionada por el usuario a los IDs técnicos."""
    mapping = {
        "vegetacion": {"variable_id": "MODIS_NDVI", "region_id": "amazon_deforestation_arc"},
        "calor": {"variable_id": "MERRA2_T2M", "region_id": "arctic_svalbard"},
        "agua": {"variable_id": "SWOT_WATER_ELEV", "region_id": "aral_sea"},
        "sequia": {"variable_id": "GLDAS_SOILM", "region_id": "california_central_valley"},
    }
    return mapping.get(phenomenon_choice.lower(), mapping["vegetacion"])


def generate_school_investigation_report(analysis_result: Dict[str, Any]) -> str:
    """Genera un reporte en Markdown listo para entrega académica o escolar."""
    var = analysis_result["variable"]
    reg = analysis_result["region"]
    det = analysis_result["detective_answers"]
    summary = analysis_result["summary"]

    md = f"""# 🌍 Informe de Investigación: Data Detective de la NASA

**Misión Científica:** {var['name']} ({var['satellite_instrument']})
**Región de Estudio:** {reg['name']}
**Periodo Evaluado:** {summary['period']} ({summary['total_observations']} observaciones mensuales)

---

## 🔍 Conclusiones del Detective

1. **¿Qué está cambiando?**
   {det['what']}

2. **¿Dónde está ocurriendo el cambio?**
   {det['where']}

3. **¿A qué velocidad y en qué magnitud?**
   {det['how_much']}

4. **¿El cambio es estadísticamente significativo?**
   **{summary['significance_label']}**
   {det['is_significant']}

---

## 📊 Resumen Técnico
- **Tasa de cambio por década:** {summary['decadal_rate']} {var.get('unit', '')}/década
- **Variación total en el periodo:** {summary['percent_change_total']}%
- **Valor p (Mann-Kendall):** {summary['p_value']}
- **Bondad de ajuste (R² OLS):** {summary['r_squared']}

*Generado automáticamente por el sistema de análisis EarthTrend Detective.*
"""
    return md
