# Registro de cambios — PRODE Mundial 2026

## 2026-06-24 — "pasa a 16avos" en vivo, Decepción post-grupos, consistencia de mails

Rama: `main`. Commits incluidos en este push:

- `75dcab2` — feat(mundial): "pasa a 16avos" (predicción) en tarjetas de Próximos Partidos.
- `7a0e30a` — feat(scoring): +1 de 16avos provisional en vivo desde standings (1º/2º); penalidades de 16avos recién al cerrar grupos.
- `f290c40` — fix(notifications): leaderboard de mails consistente con la app en penalidades/16avos.

> Nota: en un push anterior (commits `4e435df`, `ec6c5d0`, `c2b03ec`) ya habían entrado la
> corrección del comentario de campeón (30→20, constante intacta), las tarjetas
> "pasa a 16avos" en Últimos Resultados y la Decepción post-grupos. Esta entrada resume
> el estado vigente de esas piezas además de lo nuevo de esta sesión.

### Qué hace cada cambio

**Tarjetas "pasa a 16avos"**
- En **Próximos Partidos** (partidos de grupos aún no jugados): es **predicción pura**.
  Sale solo de los Excel (`total_results[part]["equipos_por_ronda"]["16vos"]`), **sin
  standings y sin puntos**. Se ve también en local sin API de resultados. Formato:
  `🎟️ {equipo} pasa a 16avos: {apostadores}` para cada equipo del partido.
- En **Últimos Resultados** (partidos de grupos jugados): es **provisional desde
  standings**, con el `+1` (`PUNTOS["16vos"]`). Muestra `, provisional` mientras los
  grupos no estén cerrados.

**+1 de 16avos provisional en vivo (Parte B)**
- El `+1` de 16avos ahora **sube en vivo** durante la fecha 3: si la API todavía no
  pobló el cuadro real de 16avos (sus fixtures vienen con equipos `null` hasta que se
  arma el cuadro), se rellena `equipos_reales["16vos"]` desde standings.
  - **Solo 1º y 2º** de cada grupo mientras los grupos están en curso (provisional).
  - Los **8 mejores terceros** entran recién con los **12 grupos cerrados**
    (`grupos_finalizados`). Antes de eso no se agregan terceros (un tercero provisional
    que después se cae sería un papelón).
  - Si la API **ya pobló** el cuadro real de 16avos, ese set es **autoritativo** y no se
    pisa. Solo se toca `["16vos"]`; 8vos/4tos/semis/final quedan intactos.
- **Penalidades de 16avos — asimetría intencional:** `revelacion_queda_grupos` (−20) y
  `peor_pasa_grupos` (−10) **NO disparan en provisional**; solo con los grupos 100%
  cerrados (flag `grupos_cerrados`). Así no aparecen y desaparecen penalidades mientras
  la tabla se mueve en la fecha 3. `campeon_no_llega_4tos` y `decepcion_llega_semis`
  usan 4tos/semis y no se tocan.

**Decepción post-grupos**
- Se resuelve al cerrar grupos **solo si existe ≥1 equipo clase‑1 que NO está entre los
  32 clasificados** a 16avos (con guard de que el set de 32 esté completo). Criterio:
  **representatividad** (que la Decepción oficial sea un favorito realmente eliminado).
- La condición vieja basada en `fase_max == 0` era **degenerada** al cerrar grupos
  (apenas terminan los grupos, todos los equipos tienen `fase_max == 0` porque el cuadro
  de 16avos aún no está poblado) → se descartó.
- No se relaciona con la penalidad `decepcion_llega_semis`, que evalúa la decepción
  **pronosticada** por cada participante, no la oficial. Revelación queda intacta (solo
  se cierra a fin de torneo).

**Funciones compartidas (anti-divergencia)**
- `obtener_equipos_clasificados_16avos()` (`utils/special_categories.py`): set de
  clasificados desde standings (12 primeros + 12 segundos + 8 mejores terceros), con
  **fallback** de 8 mejores terceros (orden pts → DG → GF) si la API no emite el ranking
  oficial; nombres mapeados al namespace del Excel; degradación segura sin standings.
  Dos modos según el momento: provisional (1º/2º) / definitivo (32).
- `construir_puntajes()` (`utils/data_loader.py`): **builder único** de puntajes (arma
  `equipos_reales_por_ronda` con la inyección provisional, calcula `grupos_cerrados` y
  puntúa a todos). Lo usan **la app** (`cargar_todo`) **y los mails**
  (`notifications.obtener_leaderboard`), para que el scoring no pueda volver a divergir.

### Reglas de puntaje confirmadas (fuente: `utils/scoring.py`)
- 16vos = 1 punto (`PUNTOS["16vos"]`).
- Comentario de campeón corregido a 20 (la constante `PUNTOS["campeon"]` siempre fue 20;
  solo se corrigió el comentario, sin tocar constantes).

### Estado de validación
- **Validado con standings mockeados:** las 7 invariantes del +1 provisional / penalidades
  / terceros / 8vos+ intactos / standings parciales; la consistencia app ↔ mail (mismos
  puntajes vía `construir_puntajes`); y smoke (server HTTP 200, `obtener_leaderboard()`
  corre sin excepción).
- **Pendiente de validar con standings reales 2026** (marcado en el código con
  `REQUIERE VALIDACIÓN CONTRA STANDINGS REALES DURANTE EL TORNEO 2026`): el camino
  provisional con la API real — que `obtener_clasificados_por_grupo()` emita standings a
  tiempo, el matcheo de nombres reales, el cruce con el cuadro real de 16avos, y el caso
  positivo de Decepción post-grupos en producción.

### Tareas abiertas (no hechas en esta sesión)
- **`pages_hidden/1_Leaderboard.py`**: sigue llamando a `calcular_puntuacion_total` con
  `grupos_cerrados` en default (`False`) y sin la inyección provisional. Está inactiva
  (la carpeta `pages_hidden/` no la auto-carga Streamlit), pero es un landmine si se
  reactiva. Decidir: borrarla (si quedó obsoleta) o migrarla al builder compartido.
- **Categorías especiales de los mails desde simulación**: `obtener_leaderboard()` usa
  `obtener_categorias_reales_simuladas()` de forma **incondicional** (incluso con datos
  reales), así que Mejor 1era Fase / Peor Equipo / Decepción / Figura / Goleador en los
  correos salen de un torneo **simulado**, no del real. Fix propuesto: builder compartido
  de `categorias_reales` (con overrides) usado en app y mails. **Prioridad alta.**
- **Robustez con resultados vacíos**: `calcular_puntos_grupos` (`utils/scoring.py`)
  rompe con `KeyError` si la API devuelve un DataFrame vacío, en vez de degradar limpio
  (bug preexistente).
