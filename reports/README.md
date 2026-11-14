# Reportes de los agentes

Un archivo por agente: `antigravity-1.md`, `antigravity-2.md`, `claude-omni-1.md`, `claude-omni-2.md`, `claude-omni-3.md`, `hermes-1.md`, `hermes-2.md`, `_arquitecto.md`.

## 1. Bloque ESTADO (obligatorio, arriba del todo)

Tu archivo **empieza** con este bloque. Se **reescribe** al cerrar cada tarea y antes de parar; no se acumula. Máximo 15 líneas.
El arquitecto lee solo este bloque de cada agente con `bash scripts/estado.sh`.

```
<!-- ESTADO:INICIO -->
## ESTADO — <tu-nombre> — <AAAA-MM-DD HH:MM hora de Perú>
Rama@commit: feature/xxx@abc1234 · empujado: sí|no
VERIFICADO: <tarea> → <comando> → <salida resumida en una línea>
ESCRITO (sin ejecutar de punta a punta): ...
ROTO / NO HECHO: ...
Siguiente paso: ...
Necesito de: <agente o humano>: <qué exactamente>
Avisos para otros carriles: ...
<!-- ESTADO:FIN -->
```

## 2. Historial (debajo del bloque)

Cada tarea cerrada añade una entrada **al final** de tu archivo (no edites las de otros):

```
## <ID de tarea> — VERIFICADO | ESCRITO | BLOQUEADO  (fecha y hora)
Rama@commit: feature/xxx@abc1234
Qué quedó: ...
Evidencia: <comando>  →  <salida real, recortada>
Falta / riesgos: ...
Necesito de otros: ...
```

- `VERIFICADO` = lo ejecuté y pego la salida. `ESCRITO` = código hecho, sin ejecutar de punta a punta.
- Sin el comando y su salida real, la tarea no cuenta como hecha. Nada simulado se presenta como resultado.
- `Rama@commit` lleva un hash real: se rellena **después** de comitear (un segundo commit corto si hace falta).
