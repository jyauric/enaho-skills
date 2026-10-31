# Evaluación: tres pedidos con y sin skills

Corrido el 31/10/2026 con Claude Code 2.1.316 en modo no interactivo (`claude -p`). Cada corrida se hizo en una copia
limpia y separada, como quien acaba de clonar el repositorio y bajar los datos: sin la base limpia
(`salidas/personas_2024.parquet`, que no se sube al repo). Las figuras y el mapa versionados sí estaban, así que las
corridas los sobrescribieron.

| Modo | Dónde | Comando |
|---|---|---|
| **Con skills** | Clon del repo | `claude -p "<pedido>"` |
| **Sin skills (repo)** | Clon del repo | `claude -p "<pedido>" --disallowedTools Skill` |
| **Sin skills (línea base)** | Carpeta con solo `datos/` y `pyproject.toml`, sin `.claude/` ni README | `claude -p "<pedido>" --disallowedTools Skill` |

> El pedido va **antes** de `--disallowedTools`: ese flag acepta varios valores y, si va primero, toma el pedido como
> otra herramienta y falla con `Error: Input must be provided…`.

## Resultados

| Pedido | Modo | Skills que se activaron | Cifra | ¿Ponderó? | La figura |
|---|---|---|---|---|---|
| ¿Cuál fue la pobreza en Cusco en 2024? | Con skills | `limpiando-enaho` | **18.5 %** (esperado 18.5 %) | Sí, `facpob07` | — |
| | Sin skills (repo) | Ninguna, pero leyó `SKILL.md` y corrió `limpiar.py` | 18.5 % | Sí, `facpob07` | — |
| | Línea base | Ninguna | 18.5 % (desde la sumaria) | Sí, `factor07 × mieperho` | — |
| Grafica la pobreza urbana y rural | Con skills | `graficando-enaho` → `limpiando-enaho` | **24.7 % / 39.4 %** (esperado 24.8 / 39.3) | Sí, `facpob07` | Barras horizontales, un color, desde 0, valor en cada barra, fuente; `figuras/pobreza_por_area_2024.png` |
| | Sin skills (repo) | Ninguna, pero corrió `limpiar.py` y `graficar.py` | 24.7 % / 39.4 % | Sí, `facpob07` | La misma figura (usó los scripts del repo) |
| | Línea base | Ninguna | 24.8 % / 39.3 % | Sí, `factor07 × mieperho` | Barras apiladas en **dos colores** (extrema / no extrema) y una barra "Nacional" que no se pidió ([ver](evaluacion/sin_skills_grafico_area.png)) |
| Haz un mapa de la pobreza por departamento | Con skills | `mapeando-enaho` → `limpiando-enaho` | **Cajamarca 45.0 %, Ica 5.9 %** (esperado 45.0 / 6.0) | Sí, `facpob07` | Un solo tono (azules) desde 0, 25 departamentos con dato, validado contra la referencia; `mapas/pobreza_departamento.png` |
| | Sin skills (repo) | Ninguna, pero corrió `limpiar.py` y `mapear.py` | Cajamarca 45.0 %, Ica 5.9 % | Sí, `facpob07` | El mismo mapa (usó los scripts del repo) |
| | Línea base | Ninguna | Cajamarca 45.0 %, Ica 6.0 % | Sí, `factor07 × mieperho` | Escala que **no empieza en 0** (arranca en ≈ 6 %), etiquetas encimadas (Cajamarca / Lambayeque), guardado en `salidas/` y no en `mapas/` ([ver](evaluacion/sin_skills_mapa.png)) |

Con skills, los dos últimos pedidos activaron **dos skills seguidas**: como la base limpia no existía,
`graficando-enaho` y `mapeando-enaho` llamaron primero a `limpiando-enaho`, que validó 27.53 % y 108,664 personas
antes de seguir.

## Qué aprendimos

1. **Las skills se activan solas.** Los tres pedidos activaron la skill correcta sin escribir `/nombre`. Las
   `description` con las palabras del pedido (ENAHO, pobreza, gráfico, mapa, departamento) funcionaron a la primera.
2. **`--disallowedTools Skill` no es un "sin skills" real dentro del repo.** Claude no puede *activar* skills, pero
   explora el proyecto, encuentra `.claude/skills/*/SKILL.md` y corre los scripts a mano. Que el resultado sea el mismo
   muestra que el conocimiento quedó en el repositorio, no en la conversación. Para medir la diferencia hizo falta la
   línea base sin `.claude/`.
3. **Sin skills, Claude acierta las cifras pero no sigue las reglas.** En la línea base calculó bien la pobreza (usó
   la sumaria con `factor07 × mieperho`, el método del INEI), pero:
   - el gráfico usa dos colores, apila categorías y agrega una barra que no se pidió;
   - la escala del mapa no empieza en 0, lo que exagera las diferencias;
   - cada corrida eligió otra carpeta y otro nombre de archivo (`figuras/pobreza_area_2024.png`,
     `salidas/mapa_pobreza_departamental_2024.png`) y descomprimió los zip en `/tmp` o en `datos/extraido/`;
   - no dejó una base limpia reutilizable ni un `validacion.txt`; cada pedido rehízo el cálculo desde cero.
4. **Lo que aportan las skills es consistencia, no solo exactitud:** el mismo pipeline, las mismas reglas de diseño,
   las mismas rutas de salida y una validación que se revisa antes de responder, en cualquier máquina y en cada pedido.

## Diferencias frente a las cifras esperadas

Las cifras esperadas de la clase se calcularon con la sumaria y `factor07 × mieperho`. Las skills ponderan siempre con
`facpob07` (regla de la clase para la base de personas), por eso urbano/rural da 24.7 / 39.4 en vez de 24.8 / 39.3 e Ica
5.9 en vez de 6.0. La mayor diferencia por departamento es 0.5 puntos (Puno y Huánuco), dentro de la tolerancia que
exige `mapear.py`. Ver la sección "Sobre el factor de expansión" del [README](README.md).
