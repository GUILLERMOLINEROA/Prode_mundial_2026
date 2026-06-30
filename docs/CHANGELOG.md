# Registro de cambios — PRODE Mundial 2026

## 2026-06-30 — Timeline: reparto suave del +N de eliminatoria por día + aviso de total provisorio durante ronda en curso

Sobre la curva diaria (misma fuente que el leaderboard, un punto por día con partidos
terminados), este ajuste **reparte el +N del pase** a lo largo de los días en que se juega cada
partido, en vez de aplicarlo todo junto al cerrar grupos. Resultado: pendiente suave durante
16avos (la curva que se quería), sin volver al cálculo paralelo.

`utils.timeline.construir_evolucion` separa **dos vistas a propósito** y las suma por día:
total = grupos acumulados (de `detalle_grupos`) + **+N del pase repartido** + **resto correcto
en su día**.

- **Pase (+N) — repartido:** se calcula con `calcular_puntos_eliminatorias` sobre el cuadro
  armado **solo con partidos terminados** hasta el día. Así el +N de un equipo aparece el día
  que juega/gana su partido de esa ronda. Atribución **cosmética**: el +1 de 16avos se gana al
  clasificar (fin de grupos) pero se muestra el día del partido de 16avos, para suavizar.
- **Penalidades / especiales / campeón / 3ero — NO se reparten:** salen de `construir_puntajes`
  sobre el snapshot **con presencia** del cuadro de 16avos (publicado al cerrar grupos). Esto es
  clave: con "solo terminados" la penalidad de revelación/peor (`len(eq_16vos)>=24` + "no está
  en el cuadro") daría **falsos −20 que parpadean** mientras se llena el bracket. Con presencia,
  caen en su día real y sin falsos positivos (revelación/peor en fin de grupos; el −20 del
  campeón el día que pierde su partido). Por día: `total_pase = elim_finished`, `resto =
  total_presencia − elim_presencia`.
- **Aviso en el gráfico:** durante una ronda en curso el extremo de la curva queda por DEBAJO
  del Total de la tabla (por el pase aún no repartido). Una nota (`st.caption`) lo aclara para
  que no se lea como bug; al completarse la ronda vuelven a coincidir.
- **Invariante (cambio a propósito):** antes era "sin vivo, último == Total" siempre. Ahora:
  con la ronda en curso **completa**, último == Total; con la ronda **incompleta**, extremo ==
  Total − (pase no repartido). Reescrito el test de invariante en sus dos casos (no borrado).
- **Costo:** **~1.75 s** (dos vistas por día: presencia para el resto + terminados para el
  pase). Sigue lejísimos de los 112 s del prototipo ingenuo.

Validado con datos reales (16avos en curso, 4 de 16 partidos jugados): 20 puntos-fecha, corta
el 30/06 (no dibuja futuro), grupos suben suave día a día, el bajón de penalidad cae el 28/06
(revelación/peor) y los campeones caen el día que pierden. La diferencia extremo-vs-Total de
cada participante es **exactamente** el +1 de los clasificados cuyo 16avos aún no se jugó
(p.ej. +19 = 19 equipos correctos sin jugar). Suite **108 verde**.

---

## 2026-06-28 — Timeline: corta en la ronda en curso y toma puntos de la misma fuente que el leaderboard

El gráfico de evolución (`pages_hidden/4_Timeline.py`) tenía un "abanico" al final y su extremo
**no coincidía** con el Total del leaderboard. **Raíz única:** calculaba los puntos por una **vía
paralela** (recompute propio de eliminatoria, que iba atrasado respecto del scoring real) y
**volcaba** especiales+penalidades+bonos en **fechas fijas de julio** (19-20), no cuando se ganaban
→ de ahí el salto del extremo derecho (no era proyección de rondas futuras, era el volcado).

**Fix (una sola fuente):** nuevo módulo `utils/timeline.py` con `construir_evolucion(...)`. Por cada
**hito de ronda que ya empezó**, el total sale de **`construir_puntajes`** sobre `resultados`
truncado a esa ronda o anteriores (con su `categorias_reales` recomputada para el corte). El hito
de la ronda **en curso** usa el total del leaderboard (`todos_puntajes`) → el último punto de cada
línea **es exactamente** su Total. Las rondas no jugadas **no se grafican** (el eje completo
Inicio→Final queda visible como referencia, vacío a la derecha). Refleja el provisional en vivo,
igual que el leaderboard. Las secciones "Posición por Fase" y "Movimientos" se restringen a fases
ya jugadas (sin totales en rondas no jugadas).

Validado con datos reales: corta en 16avos (no dibuja 8vos+), y el extremo == Total del leaderboard
para los 26 participantes. Test nuevo de la invariante (`tests/test_timeline.py`): el último punto
de cada participante == su `total` (evita que el cálculo paralelo vuelva). Suite **105 verde**.

---

## 2026-06-28 — Penalidades de revelación/peor/decepción-semis por hecho directo (cierra el pendiente ==N)

Las 3 penalidades que quedaban con conteo exacto `==N` (el landmine que traba en silencio con un
nombre mal mapeado) pasan a **hecho directo + membership**, mismo patrón que ya aplicamos al
campeón. **Cierra el pendiente `==N` de las penalidades.** Siguen leyendo la **vista terminados**
(nunca disparan por un líder en vivo) y son idempotentes (un `if` cada una).

- **`peor_pasa_grupos` (−10):** `peor in eq_16vos` directo, sin conteo. El `in` no da falso
  positivo por bracket incompleto.
- **`decepcion_llega_semis` (−20):** `decepcion in eq_semis` directo. Arregla **dos** cosas: saca
  el `==4` y dispara **apenas la decepción gana su cuarto**, sin esperar a que se definan los
  otros 3 semifinalistas.
- **`revelacion_queda_grupos` (−20):** hecho directo "**jugó grupos y no clasificó**":
  `revelacion in grupos_jugados` (set nuevo en la vista "penalidades", equipos que aparecen en
  fixtures de grupos) **+** bracket poblado `len(eq_16vos) >= 24` **+** `revelacion not in eq_16vos`.
  El guard "jugó grupos" + `>=24` cierra de raíz el falso positivo del `not in`: ni con bracket
  parcial (no evalúa hasta `>=24`) ni con un nombre mal mapeado/typo (si no jugó grupos, no
  penaliza). Y escapa al trap del `==32` (con el bracket en 31 igual evalúa).

**Nota:** este `==N` era sobre los sets de **fixtures** (`16vos`/`semis`), distinto del `==N` de
**standings** (pseudo-grupo de terceros en `obtener_clasificados_por_grupo`) — así que este
arreglo **no arrastra** esa raíz; aquella sigue siendo un tema aparte de standings, que ya no usan
estas penalidades.

Tests: **101 verde**. Discriminantes nuevos (fallarían bajo el `==N` viejo): decepción con semis
incompletas→−20, peor con bracket chico→−10, revelación con bracket a 31→−20 (escapa al trap),
revelación con bracket parcial→0 (el borde) y revelación que no jugó grupos→0 (guard). Actualizados
(comportamiento cambiado a propósito): los que asumían `==32`/`==4` ahora pasan `grupos_jugados` y
prueban `>=`/`in`.

---

## 2026-06-28 — Penalidad del campeón temprana + pase provisional en vivo (asimetría)

Dos cambios en eliminatoria que comparten la misma idea ("el partido terminó, la consecuencia
se aplica ya") pero con una **asimetría intencional**: el **pase** se mueve en vivo, las
**penalidades** solo con el partido terminado.

Commits: `9757214` (penalidad campeón) + el de este push (provisional en vivo).

### Cambio 1 — Penalidad del campeón al quedar eliminado antes de cuartos
`campeon_no_llega_4tos` (−20) se aplicaba recién con cuartos poblado (`len(eq_4tos)==8`). Ahora
se aplica **en cuanto el campeón queda eliminado antes de cuartos**, sin esperar a que la API
arme el cuadro. Hecho directo: el campeón es **perdedor de un 16avos/8vos terminado** (∪
eliminado en grupos, con el bracket poblado `>=24`). Gatillo único por membership en
`eliminados_pre_4tos`, **sin conteo `==N`** (sale del landmine de pendientes para esta penalidad)
e **idempotente** (un solo `if`; cuando la API arme cuartos no se duplica).

### Cambio 2 — Pase provisional EN VIVO
El **+N del pase a la ronda siguiente** se mueve **en vivo** según el marcador y se congela al
pitazo (FT/AET/PEN, incluido alargue y penales). El que va ganando suma provisionalmente; **empate
en vivo = nadie**; durante la tanda de penales (`P`) el marcador está empatado → nadie hasta `PEN`.
Es una **decisión consciente que revierte el criterio anterior de "solo al terminar"** — pero
**solo para el pase**, NO para las penalidades. El parpadeo del leaderboard durante los partidos
es esperado.

### La asimetría (cómo se garantiza)
`extraer_equipos_reales_por_ronda` arma **dos vistas separadas**: las claves de ronda
(`16vos..final`) son la vista del **pase** (incluye líderes en vivo, la lee el scoring del +N), y
la clave **`"penalidades"`** es la vista **TERMINADOS** (solo FT/AET/PEN), que lee
`calcular_penalidades`. Como esa vista se construye filtrando `estado in ESTADOS_FINALIZADO`, un
líder en vivo **físicamente no puede entrar** → un campeón (o una decepción) perdiendo en vivo
**nunca** dispara una penalidad fantasma. Verificado con datos reales (Alemania 1-1 Paraguay en
vivo → nadie suma el pase y Alemania no aparece en `eliminados_pre_4tos`).

### Tests
Suite **94 verde**. Nuevos: `TestProvisionalEnVivo` (líder suma, empate→nadie, cambio de líder,
penales en curso→nadie, congela al FT) y `TestPenalidadCampeon` (eliminado en 16avos, idempotente
con cuartos poblado, llegó a cuartos, clasificó sin jugar, eliminado en grupos, y el crítico
**campeón perdiendo en vivo → 0 hasta el pitazo**). Actualizados (comportamiento cambiado a
propósito): el test de "en curso no propaga" → ahora "el líder en vivo SÍ propaga"; y el gatillo
del campeón (`==8` → `eliminados_pre_4tos`).

---

## 2026-06-28 — En eliminatoria, el ganador suma la ronda siguiente sin esperar el cuadro de la API

En mata-mata el que gana pasa (no hay reglas de clasificación como en grupos), pero el +N
de la ronda siguiente dependía de que la API publicara el fixture de esa ronda, y eso tarda
(p.ej. Canadá ganó su 16avos pero todavía no sumaba el pase a 8vos). Ahora suma apenas
termina el partido.

1. **Qué hace.** En eliminatorias (16avos en adelante), apenas un partido está terminado
   (FT/AET/PEN), el ganador se agrega al set de la **ronda siguiente** en
   `equipos_reales_por_ronda` (`extraer_equipos_reales_por_ronda`), así suma el +N sin
   esperar a que la API publique el cuadro de esa ronda. Mapeo: 16avos→8vos, 8vos→4tos,
   4tos→semis, semis→final. (La final define campeón, que se puntúa por otra vía.)
2. **Ganador correcto.** FT/AET por marcador (ya incluye el alargue); **PEN por la tanda**
   (`penales_local/visitante`), no por el marcador empatado. Si un partido terminado no
   permite determinar ganador (dato faltante) → no se agrega a nadie (degradación segura).
3. **Anti-doble-conteo (estructural).** Se agrega al ganador al **mismo `set`** que ya lee el
   scoring; `calcular_puntos_eliminatorias` hace `pred & real`, así que el ganador agregado
   temprano + el fixture que la API publique después colapsan en el mismo elemento → el +N se
   otorga **una sola vez por equipo**. Una sola fuente, un solo camino de puntaje. El ganador
   se agrega con el nombre mapeado (`mapear_nombre_equipo`), mismo namespace que el resto del
   set y los Excels.
4. **Solo eliminatoria.** La fase de grupos no se toca (ahí ganar no implica pasar). Se gatea
   por ronda y solo con partidos terminados (nada provisional en vivo).
5. **Inconsistencia benigna documentada.** Un equipo puede estar en `["8vos"]`+ (para scoring)
   mientras su `fase_max` sigue en el valor de la ronda actual hasta que la API publique el
   cuadro, porque `calcular_fase_maxima_por_equipo` lee de **fixtures**, no de este set. Hoy no
   afecta nada (la Decepción usa `fase_max`, no el set, y sigue resolviendo 'Uruguay'), pero
   queda anotado: si en el futuro alguien deriva algo nuevo de `fase_max`, tener en cuenta este
   desfase.

### Sin validar (asterisco)

- **AET y PEN con datos reales todavía no ocurrieron** (validados con mocks). La lógica de
  penales es la más delicada: se confirma de verdad cuando se juegue el primer cruce real
  definido por penales (que avance el de la tanda, no el del marcador empatado). Las rondas
  profundas (8vos→4tos→…) ídem, se confirman a medida que se jueguen. Hoy solo hay 1 partido
  de eliminatoria terminado (Canadá, FT) y propaga bien a 8vos.

---

## 2026-06-28 — Fix: Decepción se resuelve desde el cuadro real de 16avos (no standings)

**Bug en producción:** con grupos cerrados y 16avos en curso, la Decepción oficial no se
resolvía (nadie cobraba los +12). Uruguay (clase 1) quedó eliminado en grupos y debía ser la
Decepción, pero `categorias_reales["Decepción"]` quedaba `""`.

**Causa raíz (confirmada con datos reales):** la condición usaba
`obtener_equipos_clasificados_16avos` (standings) con candado `len(...) >= 32`. El endpoint
`/standings` devuelve **13 "grupos"** (el ranking de terceros se cuela como un grupo más y el
filtro de `obtener_clasificados_por_grupo` no lo detecta → `ranking_terceros` queda vacío),
con lo que el set se arma mal y da **31** → el candado `>= 32` nunca se cumple → Decepción
nunca se resolvía. Es el mismo landmine de mapeo/`==N` ya anotado en pendientes.

**Fix:** `calcular_todas_las_categorias` resuelve la Decepción post-grupos desde el **cuadro
real de 16avos** (equipos con `fase_max >= 1`, misma fuente que el scoring de eliminatorias),
no desde standings. Un clase-1 está "eliminado" si NO está en ese cuadro. Se evita el conteo
exacto: solo se exige que el bracket esté **materialmente poblado** (`>= 24`, umbral
defensivo, no `== 32`) para no disparar falsos positivos en la ventana "grupos recién cerrados,
fixtures de 16avos aún sin equipos" (ahí queda pendiente y se resuelve solo al poblarse).
Bordes preservados: grupos sin cerrar → todo vacío; ventana con bracket vacío → sin falso
positivo; cierre de torneo → Revelación/Decepción se cierran igual que antes. `determinar_decepcion`
intacto. Se eliminó la función `obtener_equipos_clasificados_16avos` (quedó sin caller).

Validado con datos reales: `Decepción = 'Uruguay'`, y quien la apostó (7 participantes) cobra +12.

---

## 2026-06-28 — Tarjetas de eliminatoria (avance fiel al scoring, semis/final, sede sin "nan")

Las tarjetas de los cruces de eliminatoria (En vivo / Próximos / Últimos) mostraban
datos confusos heredados de fase de grupos (local/visitante duplicados, "empate" que no
aplica, "pasa a 16avos" redundante, "nan" en la sede). Se rehicieron para que reflejen lo
que efectivamente paga el scoring. Tarjetas de fase de grupos sin cambios. Scoring intacto.

Commit: `a9db1f6` — fix(mundial): tarjetas de eliminatoria.

1. **Líneas de avance fieles al scoring.** En tarjetas de eliminatoria (R32/R16/QF/SF),
   cada equipo muestra `🔜 {equipo} pasa a {ronda siguiente} (+N)` con quienes predijeron
   ese equipo llegando a la ronda siguiente, desde `equipos_por_ronda` (misma fuente que
   `calcular_puntos_eliminatorias`): R32→8vos (+3), R16→4tos (+6), QF→semis (+10),
   SF→final (+15). El overlap es **esperado y NO se deduplica**: si alguien tiene a los dos
   equipos avanzando, cobra por los dos y aparece en ambas líneas. Se descartó la lógica
   "por cruce" porque escondía a participantes que sí cobran (los que predijeron el cruce
   en otra ronda).
2. **Semifinal.** Además de "pasa a la final (+15)", muestra `🥉 quién puso a {equipo}
   3er puesto (+5)` desde `total_results["tercero"]` (misma fuente que el scoring del 3er
   puesto). El wording deja claro que es la predicción del participante, no un pronóstico
   de que el equipo pierde la semi.
3. **Final.** Muestra `🏆 quién puso a {equipo} campeón (+20)` desde
   `total_results["campeon"]`. Subcampeón omitido (no paga: `PUNTOS` no tiene esa clave).
4. **Limpieza visual de eliminatoria.** Se ocultó la línea de empate (no aplica en
   mata-mata) y la sección "pasa a 16avos" (info de grupos). Tarjetas de grupos sin cambios.
5. **Sede sin "nan".** Helper `formato_sede` muestra solo el estadio cuando la ciudad falta
   (cubre `"nan"` / `NaN` de pandas / `None` / vacío), en grupos y eliminatoria.
6. **Limpieza de código.** Eliminada la función muerta `ronda_prediccion_para_match`
   (quedó sin caller tras este cambio).

### Pendiente menor (anotado, sin urgencia)

- La tarjeta del **partido por el 3er puesto** en sí cae al mensaje genérico (sin líneas de
  avance). El dato del 3er puesto ya se expone en la tarjeta de **semifinal**. Cosmético.

### Sin validar

- El render con **cruces reales de la API** (Round of 32+ con nombres mapeados) se confirma
  recién cuando se jueguen. Validado con mocks de ronda + predicciones reales de los Excels.

---

## Pendientes abiertos (al 2026-06-28)

Lista consolidada de temas conocidos sin resolver, para no perderlos de vista.

1. **Decisión del +12 (centinela "No hay Revelación").** Al cierre del torneo, si la
   revelación **real** también resuelve como `"No hay Revelación"` (cuando ningún equipo
   cumple el criterio), un participante que apostó `"No hay Revelación"` matchearía en
   `calcular_puntos_categorias` y sumaría **+12**. Indeciso:
   - **Opción A:** cuenta como predicción válida (acertó que no habría revelación).
   - **Opción B:** el centinela es ausencia de apuesta → no premia ni penaliza (coherente
     con el fix de penalidades de hoy). Implementación: aplicar `_es_no_apuesta` también del
     lado del acierto en `calcular_puntos_categorias`.
   - Inclinación tentativa hacia B por coherencia. Sin urgencia (solo aplica al cierre).

2. **~~`== 32` exacto en `calcular_penalidades`~~ — RESUELTO (2026-06-28).** Las 4 penalidades
   pasaron a hecho directo + membership (`in`/`not in` + guards `>=`/`grupos_jugados`), sin
   ningún conteo `==N`. Ver la entrada "Penalidades ... por hecho directo" arriba. Queda solo,
   como tema **separado de standings**, revisar el filtro del pseudo-grupo de terceros en
   `obtener_clasificados_por_grupo` (que ya NO afecta a estas penalidades — usan fixtures).
   *(Texto original conservado abajo para contexto histórico.)*
   La condición `len(eq_16vos_real) == 32` trababa TODAS las penalidades de 16avos si el set
   quedaba en **31** (un nombre sin mapear o un slot nulo) o en **33** (una variante de nombre
   duplicada tipo `"Türkiye"` + `"Turquia"`). Era la misma familia de bugs de mapeo de nombres.
   - **CAUSA RAÍZ CONFIRMADA (2026-06-28, datos reales):** el endpoint `/standings` devuelve
     **13 "grupos"** durante los 16avos — el *ranking de terceros* entra como un grupo más y
     el filtro de `obtener_clasificados_por_grupo` (`"third-placed"`/`"ranking of third"`) NO
     lo detecta con el nombre real que manda la API → `ranking_terceros` queda vacío y el
     conteo de clasificados da **31** en lugar de 32. Esto fue lo que trababa la Decepción
     (ya resuelto migrándola al cuadro real). **Las penalidades de 16avos en
     `calcular_penalidades` siguen usando `eq_16vos_real` que viene del cuadro real de
     fixtures, NO de standings**, así que probablemente NO sufran este bug puntual — pero el
     `== 32` exacto sigue siendo frágil ante el caso 31/33 de mapeo. Al encararlas: cambiar a
     `>= 32` y/o revisar el filtro del pseudo-grupo de terceros en `obtener_clasificados_por_grupo`.

3. **`pages_hidden/1_Leaderboard.py`.** Página inactiva (carpeta no auto-cargada por
   Streamlit) que llama a `calcular_puntuacion_total` con el scoring viejo. Landmine si se
   activa. Decidir: borrar (si quedó obsoleta) o migrar al builder compartido.

4. **Categorías especiales de los mails desde simulación.** `obtener_leaderboard()` usa
   `obtener_categorias_reales_simuladas()` de forma **incondicional**, incluso con datos
   reales → Mejor 1era Fase / Peor Equipo / Decepción / Figura / Goleador en los correos
   salen de un torneo **simulado**. **Prioridad alta** en cuanto la fase de grupos produzca
   categorías reales. Fix propuesto: builder compartido de `categorias_reales` (con overrides)
   usado en app y mails.

---

## 2026-06-28 — Fix: no penalizar el centinela "No hay Revelación" (no-apuesta)

**Bug en producción (afectaba el leaderboard en vivo).** Participantes que en su Excel
eligieron la opción de **no apostar** en Revelación (literal `"No hay Revelación"`)
recibían un **−20 falso** ("Tu revelación (No hay Revelación) se quedó en grupos"). El
guard de `calcular_penalidades` (`if revelacion and eq_16vos_real`) solo descartaba el
**string vacío**; el centinela de texto es truthy, no está en el cuadro de 16avos, y por
eso disparaba la penalidad.

Commit: `f388121` — fix(scoring): no penalizar a quienes eligieron "no hay revelación/
peor equipo" (centinela de no-apuesta).

### Fix

- Nuevo helper `_es_no_apuesta(valor)` en `utils/scoring.py`: detecta centinelas de
  no-apuesta de forma robusta (case-insensitive, sin acentos): valor vacío, que empiece
  con `"no hay"` o `"sin "`, o ∈ {`ninguno`, `ninguna`, `n/a`, `na`, `-`, `--`}.
- Se aplica el guard a las penalidades de **Revelación** (`revelacion_queda_grupos`, −20)
  y **Peor Equipo** (`peor_pasa_grupos`, −10; defensivo: hoy no hay centinela en esa
  categoría, pero queda cubierto a futuro). Las penalidades de campeón-4tos y
  decepción-semis no se tocan (no tienen opción de no-apuesta).
- Único centinela presente hoy en los Excels (4 grupos): `"No hay Revelación"` (17 casos).
- Puntos especiales (`calcular_puntos_categorias`): ya estaba cubierto para el caso actual
  —exige `pred and real and pred==real`, así que `"No hay Revelación"` vs real vacío no
  suma. Verificado.

### PENDIENTE — decisión de reglas (NO resuelta): el +12 del "No hay Revelación" acertado

Al **cierre del torneo**, `determinar_revelacion` puede setear la revelación **real**
también como `"No hay Revelación"` (cuando ningún equipo cumple el criterio de revelación).
En ese caso, un participante que apostó `"No hay Revelación"` **matchearía** en
`calcular_puntos_categorias` y sumaría **+12**. Hay que decidir:

- **Opción A:** es una predicción válida; acertar que "no habría revelación" suma +12.
- **Opción B:** el centinela es *ausencia de apuesta* → no premia ni penaliza (coherente
  con este fix: si no penaliza, tampoco premia). Implementación: aplicar el mismo guard
  `_es_no_apuesta` del lado del acierto en `calcular_puntos_categorias`.

Estado: **indeciso**, inclinación tentativa hacia **B** por coherencia, pendiente de
confirmación. Solo aplica al cierre del torneo → sin urgencia.

---

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
