# Suite de tests del scoring

Red de seguridad **autocontenida** del scoring del PRODE. **Cero dependencia** de la
API, de la `API_FOOTBALL_KEY`, de los Excels reales o de datos de producción: cada test
arma sus propios datos sintéticos (`tests/_builders.py`). Determinística, sin red, corre
en frío.

## Cómo correrla

Desde la raíz del repo:

```
python -m unittest discover -s tests -v
```

## Qué cubre

- **`test_grupos.py`** — `calcular_puntos_grupos` (ganador/exacto, NS, pendiente, en vivo).
- **`test_eliminatorias.py`** — `calcular_puntos_eliminatorias` por ronda y acumulado.
- **`test_campeon_tercero.py`** — `calcular_puntos_campeon_y_tercero` (+20 / +5).
- **`test_categorias.py`** — `calcular_puntos_categorias` y `_es_no_apuesta`.
- **`test_penalidades.py`** — las 4 penalidades y sus gatillos.
- **`test_total_y_leaderboard.py`** — `calcular_puntuacion_total` (con ajuste manual) y `generar_leaderboard`.
- **`test_special_categories.py`** — grupos/torneo finalizados, fase máxima, tabla, Decepción/Revelación/Mejor/Peor, `calcular_todas_las_categorias`.
- **`test_data_loader.py`** — ganador de eliminatoria, `extraer_equipos_reales_por_ronda`, campeón/3ero, `construir_puntajes`.

## Tests de regresión (bugs ya arreglados; cada uno falla si vuelve el bug)

1. Centinela "No hay Revelación" / "No hay Peor Equipo" no penaliza — `test_penalidades.py`.
2. Decepción desde el cuadro real (no conteo de standings) — `test_special_categories.py`.
3. Decepción no degenerada (elige el clase-1 eliminado) — `test_special_categories.py`.
4. Penalidades de 16avos no disparan con el cuadro real vacío — `test_penalidades.py`.
5. Ganador de eliminatoria propaga a la ronda siguiente (penales por tanda; grupos/en-vivo no) — `test_data_loader.py`.
6. Anti-doble-conteo: ganador temprano + fixture de la API → +N una vez — `test_data_loader.py`.
7. App y mail consistentes vía `construir_puntajes` — `test_data_loader.py`.

> Nota: los tests de penalidades reflejan el gatillo vigente por ronda completa exacta
> (`len==32 / ==8 / ==4`), que está anotado como pendiente en `docs/CHANGELOG.md`.
