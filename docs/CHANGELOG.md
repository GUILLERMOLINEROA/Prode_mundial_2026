# Registro de cambios — PRODE Mundial 2026

## 2026-06-24 (más tarde) — Reversión: 16avos suma solo con el cuadro real de la API

**Cambio de criterio respecto de la entrada anterior.** Se revirtió el +1 de 16avos
**provisional desde standings** que se había introducido en `7a0e30a`. Ese mecanismo
hacía que durante la fase de grupos la columna "16avos" mostrara ~23/24 puntos
(1º y 2º de cada grupo), lo cual era **confuso** (parecía puntaje ganado cuando
todavía no se jugó ninguna eliminatoria).

Decisión de producto: **el +1 de 16avos suma solo cuando la API ya publicó el cuadro
real de la Round of 32** (es decir, al cerrar grupos). Efecto aceptado: durante la
fase de grupos la columna 16avos queda en **0 para todos**, y vuelve —ya como puntaje
real— cuando aparece el cuadro de la API.

Commits incluidos en este push:

- `9e56b8b` — fix(scoring): 16avos suma solo con cuadro real de la API (sin provisional);
  penalidades de 16avos atadas al cuadro real.
- `d22d69a` — style(mundial): empate bajo el segundo país + separador antes de
  "pasa a 16avos" en Próximos Partidos.
- (este) — docs: registro de la reversión.

### Qué cambió respecto del modelo provisional

- **Leaderboard / scoring:** `data_loader.construir_puntajes` ya **no inyecta** el set de
  standings en `equipos_reales_por_ronda["16vos"]`. Ese set sale **solo** del cuadro real
  (`extraer_equipos_reales_por_ronda`). Se eliminó el flag `grupos_cerrados` (quedó sin uso)
  de `construir_puntajes`, `calcular_penalidades` y `calcular_puntuacion_total`.
- **Penalidades de 16avos** (revelación −20, peor equipo −10): ahora disparan solo cuando
  el set **real** de 16avos NO está vacío (cuadro publicado), en lugar de `grupos_cerrados`.
  Esto evita falsos −20/−10 en la ventana "grupos cerrados pero la API aún no publicó el
  cuadro" (set vacío → el código creería que todos se quedaron en grupos).
- **Tarjeta "pasa a 16avos" en Últimos Resultados:** pasa a leer del **cuadro real** (misma
  fuente que el scoring), se le sacó la etiqueta "provisional" y solo aparece cuando el
  cuadro existe. Así la tarjeta no promete un +1 que el leaderboard no está sumando.
- **Próximos Partidos:** la predicción "pasa a 16avos" (que sale de los Excel, sin standings
  ni puntos) se mantiene; solo cambió el layout (empate debajo del segundo país + separador).

### Asimetría intencional (sigue vigente)

- **Decepción** sigue resolviéndose desde **standings** (`obtener_equipos_clasificados_16avos`,
  con su guard de 12 grupos completos), NO desde el cuadro real, porque debe cerrarse justo
  al terminar grupos cuando el bracket real puede no estar publicado todavía.
- El **+1 y las penalidades** de 16avos usan el **cuadro real**. No unificar las dos fuentes.

### Validación

- Validado con fixtures/standings mockeados: 16avos=0 durante grupos; +1 con cuadro real;
  sin penalidades con cuadro vacío; penalidades con cuadro poblado; Decepción intacta desde
  standings; TAREA 2 y 8vos+ intactos; smoke (server HTTP 200, `obtener_leaderboard` corre).
- **Pendiente con datos reales 2026:** que la API publique la Round of 32 con nombres mapeados
  al cerrar grupos, y que ahí el +1 y las penalidades disparen con datos reales.

---

## 2026-06-24 — "pasa a 16avos" en vivo, Decepción post-grupos, consistencia de mails

> ⚠️ El "+1 de 16avos provisional en vivo" descripto en esta entrada fue **revertido** en la
> entrada de arriba (2026-06-24 más tarde). Se conserva el registro del criterio original.

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
