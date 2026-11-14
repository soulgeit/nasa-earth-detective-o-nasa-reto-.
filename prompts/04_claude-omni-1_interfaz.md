# 04 · Claude Omni 1 — Interfaz: el detective que el juez va a tocar

**Rama:** `feature/ui` · **Carpeta:** `src/ui/`
**Antes:** lee `prompts/00_LEER_PRIMERO.md` y `docs/CONTRATOS.md` (§3, §4, §5, §7).

## Tu misión
La rúbrica puntúa usabilidad dentro de Validez y la historia dentro de Presentación. Un estudiante de secundaria debe poder investigar un lugar en menos de un minuto, entender el veredicto y confiar en él.
Mantén la pila actual (HTML + JS sin framework + Chart.js); añade Leaflet por CDN. No migres a React: no hay tiempo.

## Tareas, en orden

### U1 — Limpieza de lo falso (P0, 20 min)
Borra `calculateStatsClientSide`, el catálogo embebido y todo valor por defecto inventado (`'0.82'`, `0.00001`, «Valor Observado (Satélite)»).
Si la API no responde: estado de error claro + botón para abrir un caso real congelado (`/api/cases`). **La UI nunca genera datos.**
Evidencia: `git grep -nE "Math\.sin|Math\.random|0\.82|0\.00001" -- src/ui` sin resultados.

### U2 — Pantalla principal (P0)
Hasta que la API esté lista, desarrolla contra las muestras reales de `tests/fixtures/real/` (cárgalas tal cual; no las edites).
Una sola página, tres zonas:
1. **Mapa** (Leaflet). Clic = punto; arrastrar con Mayús = caja. Buscador de lugares (`/api/geocode`). Capa base: prueba primero un mosaico de NASA GIBS
   (comprueba la plantilla de URL en la documentación de GIBS y que una tesela cargue); si falla, OpenStreetMap con su atribución.
2. **Panel de investigación**: selector de variable con definición sencilla al lado, periodo, botón «Investigar».
3. **Resultado**:
   - Gráfica con conmutador: valores mensuales · anomalías · medias anuales. Recta de Sen + **banda de confianza**. Unidades en el eje. Línea vertical si hay `homogeneous_since`.
   - **Cuatro tarjetas**: Qué · Dónde · Cuánto (por década, con IC 95 %) · ¿Es significativo? con sello según `verdict_code` (5 estados, no 2).
     `SUGGESTIVE` y `NOT_SIGNIFICANT` se muestran con dignidad: «todavía no se puede afirmar» también es un hallazgo.
   - **Tarjeta «¿Cuántos años faltan?»** con una barra: años disponibles frente a años necesarios (`detectability`).
   - **«Cómo lo sabemos»** desplegable: las tres pruebas con sus valores p, autocorrelación, referencias y `warnings` en lenguaje llano.
   - **Procedencia** siempre visible: fuente, resolución, fecha de descarga, enlace a la consulta exacta, cita.
   - Aviso rojo si `provenance.kind` no es `nasa_api`, `nasa_file` ni `user_upload`.
- Glosario emergente para: tendencia, anomalía, valor p, significancia, intervalo de confianza, autocorrelación.

### U3 — Dónde cambia (P1)
- **Mapa de tendencias** (`/api/trendmap`): un rectángulo por celda, paleta divergente apta para daltónicos y simétrica alrededor de 0, **punto central en las celdas con `significant_fdr`**, leyenda con unidades por década y el porcentaje de celdas significativas.
- **Comparar**: dos regiones, dos gráficas con el mismo eje, y la frase de `compare` destacada cuando las tendencias sean opuestas.
- Atlas global (`/api/atlas/{id}`) si existe: clic en una zona → investiga ese punto.

### U4 — El detective (P1; la lógica es de Claude Omni 2)
- Caja «Pregúntale al detective» → `/api/ai/plan` → muestra el plan («Voy a investigar *lluvia* en *Piura*») con botón para corregir antes de ejecutar.
- Tras un clic en el mapa: «¿Qué investigo aquí?» → `/api/ai/scout` → 3 variables sugeridas con el porqué y **sus fuentes enlazadas**.
- Bajo el veredicto: «Explicación del detective» (`/api/ai/explain`) con citas numeradas, selector de nivel (escolar / universitario) y una etiqueta visible «Generado con IA a partir de las fuentes citadas».
- Con `ai_mode` `extractive` u `off` (lo dice `/api/health`) la interfaz se adapta sin romperse.

### U5 — Casos para mirar (P0)
Modo demostración de 3–4 casos reales (`/api/cases`): avanza solo, paso a paso, con texto narrado en pantalla y botón de pausa. Los casos los elige el humano.

### U6 — Bilingüe, informe y accesibilidad (P0)
- Todas las cadenas en `i18n.js` (`es`, `en`); idioma por navegador, inglés por defecto, conmutador visible.
- «Descargar informe» → `/api/report` imprimible (PDF desde el navegador), con procedencia, método y cita.
- Teclado, foco visible, contraste AA, textos alternativos, sin depender solo del color, usable en móvil (360 px).
- **Sin marca NASA**: ni logotipos ni insignias; revisa la paleta para que no imite la identidad de la NASA. Atribución en texto: «Data: NASA POWER…».
- Nombre visible: «EarthTrend Detective» (el humano puede cambiarlo); nunca «de la NASA».

### U7 — Material para la entrega (P0, domingo por la mañana)
Seis capturas (1600×900, en inglés, con datos reales) en `docs/media/`: pantalla principal, veredicto, mapa de tendencias, comparar, detective con fuentes, caso no significativo. Y un GIF de 10 s (< 10 MB) del flujo completo.
No aparece ninguna persona. Nada generado con IA de imágenes.

## Aceptación
- Abrir la página, hacer clic en Lima, elegir temperatura, «Investigar» → veredicto con datos reales en menos de 5 s. Captura en tu reporte.
- Las mismas acciones en inglés. Navegación completa con teclado.
- Consola del navegador sin errores.

Reporta en `reports/claude-omni-1.md`.
