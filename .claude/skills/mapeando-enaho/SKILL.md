---
name: mapeando-enaho
description: Hace un mapa de la pobreza monetaria de la ENAHO del INEI por departamento del Perú, unido por código de ubigeo. Úsala cuando pidan un mapa de la pobreza, o la pobreza por departamento o región del Perú en un mapa.
argument-hint: [año]
---

# Mapeando la ENAHO

Si el pedido o los argumentos ($ARGUMENTS) mencionan un año de 4 dígitos, úsalo; si no, usa 2024 y dilo en la respuesta.

1. **Datos.** Si no existe `salidas/personas_<año>.parquet`, usa primero la skill `limpiando-enaho` para ese año. Si falta `datos/peru_departamental_simple.geojson`, pide al usuario bajarlo de https://raw.githubusercontent.com/d2cml-ai/Data-Science-Python/main/sessions/06-geoespacial/lab/Data/peru_departamental_simple.geojson

2. **Mapa.** Corre exactamente:

   ```bash
   uv run ${CLAUDE_SKILL_DIR}/scripts/mapear.py --anio <año>
   ```

   El script ya fija las reglas: une `ubigeo[:2]` con `FIRST_IDDP` como texto (nunca por nombre), exige 25 departamentos con dato, Lima (15) y Callao (07) separados, un solo color de claro a oscuro desde 0, leyenda en % de personas, y valida contra `referencias/pobreza_departamento_<año>.csv`.

3. **Si falla un assert**, detente y muestra el error. No dibujes otro mapa ni cambies la unión a nombres.

4. **Respuesta.** Da la ruta `mapas/pobreza_departamento.png`, los tres departamentos con más y con menos pobreza, y aclara que las cifras están ponderadas con `facpob07`. Callao es muy pequeño en el mapa: si lo preguntan, usa la tabla que imprime el script.
