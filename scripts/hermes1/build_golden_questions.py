# SI-assisted: hermes-1 (Claude Sonnet 5.5)
"""C5 - 50 golden questions (25 Spanish, 25 English) with expected variables.

Written before seeing what the retriever returns, as the prompt requires.
Each line: {"question": ..., "lang": "es|en", "expected_variable_ids": [...]}
"""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hermes1.fetch_common import ROOT, write_jsonl  # noqa: E402

QUESTIONS = [
    # --- Spanish (25)
    ("¿Está lloviendo menos en Piura en los últimos años?", "es", ["PRECTOTCORR"]),
    ("¿Hace más calor ahora en Lima que cuando era niño?", "es", ["T2M"]),
    ("¿El suelo de Ica se está secando?", "es", ["GWETTOP", "EVLAND"]),
    ("¿Cae más nieve en la Cordillera Blanca que antes?", "es", ["SNODP", "PRECTOTCORR"]),
    ("¿El aire de Lima está más sucio que hace veinte años?", "es", ["AOD_55"]),
    ("¿Por qué hay más humo en el cielo de la Amazonía en septiembre?", "es", ["AOD_55", "PRECTOTCORR"]),
    ("¿Las nubes cubren más el cielo de Cusco ahora?", "es", ["CLOUD_AMT"]),
    ("¿Hay más radiación solar en Arequipa en los últimos años?", "es", ["ALLSKY_SFC_SW_DWN"]),
    ("¿El hielo del Ártico está desapareciendo?", "es", ["SEAICE_EXTENT_N"]),
    ("¿El hielo de la Antártida crece o se reduce?", "es", ["SEAICE_EXTENT_S"]),
    ("¿El planeta se está calentando de verdad?", "es", ["GISTEMP_TANOM", "T2M"]),
    ("¿La humedad del aire en Iquitos cambió en las últimas décadas?", "es", ["RH2M", "TQV"]),
    ("¿Cómo va la evaporación en el valle de Ica?", "es", ["EVLAND", "GWETTOP"]),
    ("¿Está aumentando el ozono sobre el Perú?", "es", ["TO3"]),
    ("¿Qué ha pasado con la lluvia en la selva de Madre de Dios?", "es", ["PRECTOTCORR"]),
    ("Temperatura de la superficie del suelo en Puno, tendencia", "es", ["TS"]),
    ("¿El lago Titicaca está perdiendo agua por más evaporación?", "es", ["EVLAND", "GWETTOP"]),
    ("¿La garúa de Lima se está volviendo más frecuente?", "es", ["RH2M", "CLOUD_AMT"]),
    ("¿El vapor de agua sobre la costa peruana está cambiando?", "es", ["TQV"]),
    ("¿Qué variable debo mirar para saber si Piura se desertifica?", "es", ["PRECTOTCORR", "GWETTOP"]),
    ("¿La nieve de los Andes se derrite antes ahora?", "es", ["SNODP", "T2M"]),
    ("¿Las olas de calor en la selva son más largas?", "es", ["T2M"]),
    ("¿El polvo del desierto de Sechura llega más lejos ahora?", "es", ["AOD_55"]),
    ("¿La radiación ultravioleta en la puna ha cambiado?", "es", ["TO3", "ALLSKY_SFC_SW_DWN"]),
    ("¿Las lluvias de El Niño son más intensas en Tumbes?", "es", ["PRECTOTCORR"]),
    # --- English (25)
    ("Is it raining less in Piura than it used to?", "en", ["PRECTOTCORR"]),
    ("Is Lima getting hotter over the decades?", "en", ["T2M"]),
    ("Is the soil in Ica drying out?", "en", ["GWETTOP", "EVLAND"]),
    ("Is there less snow in the Cordillera Blanca now?", "en", ["SNODP", "PRECTOTCORR"]),
    ("Is the air over Lima dirtier than twenty years ago?", "en", ["AOD_55"]),
    ("Why is there more smoke over the Amazon in September?", "en", ["AOD_55", "PRECTOTCORR"]),
    ("Is the sky over Cusco cloudier than before?", "en", ["CLOUD_AMT"]),
    ("Is Arequipa getting more solar radiation?", "en", ["ALLSKY_SFC_SW_DWN"]),
    ("Is Arctic sea ice disappearing?", "en", ["SEAICE_EXTENT_N"]),
    ("Is Antarctic sea ice growing or shrinking?", "en", ["SEAICE_EXTENT_S"]),
    ("Is the planet really warming?", "en", ["GISTEMP_TANOM", "T2M"]),
    ("Has the humidity in Iquitos changed in recent decades?", "en", ["RH2M", "TQV"]),
    ("How is evaporation in the Ica Valley changing?", "en", ["EVLAND", "GWETTOP"]),
    ("Is ozone over Peru increasing?", "en", ["TO3"]),
    ("What is happening to rainfall in the Madre de Dios rainforest?", "en", ["PRECTOTCORR"]),
    ("Ground surface temperature in Puno, trend", "en", ["TS"]),
    ("Is Lake Titicaca losing water to more evaporation?", "en", ["EVLAND", "GWETTOP"]),
    ("Is Lima's drizzle becoming more frequent?", "en", ["RH2M", "CLOUD_AMT"]),
    ("Is the water vapour over the Peruvian coast changing?", "en", ["TQV"]),
    ("Which variable tells me if Piura is turning into desert?", "en", ["PRECTOTCORR", "GWETTOP"]),
    ("Is Andean snow melting earlier now?", "en", ["SNODP", "T2M"]),
    ("Are heat waves in the rainforest getting longer?", "en", ["T2M"]),
    ("Is dust from the Sechura Desert travelling farther now?", "en", ["AOD_55"]),
    ("Has ultraviolet radiation on the high plateau changed?", "en", ["TO3", "ALLSKY_SFC_SW_DWN"]),
    ("Are El Nino rains stronger in Tumbes?", "en", ["PRECTOTCORR"]),
]


def main() -> int:
    rows = [
        {"question": q, "lang": lang, "expected_variable_ids": vids}
        for q, lang, vids in QUESTIONS
    ]
    out = os.path.join(ROOT, "data", "knowledge", "golden_questions.jsonl")
    write_jsonl(out, rows)
    es = sum(1 for r in rows if r["lang"] == "es")
    print(f"wrote {len(rows)} questions ({es} es, {len(rows) - es} en) -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
