---
name: graficando-enaho
description: Grafica la pobreza monetaria de la ENAHO del INEI por área de residencia (urbano/rural), sexo o grupo de edad. Úsala cuando pidan un gráfico, una figura o comparar la pobreza entre grupos.
argument-hint: [area|sexo|edad] [año]
---

# Graficando la ENAHO

Si el pedido o los argumentos ($ARGUMENTS) mencionan un año de 4 dígitos, úsalo; si no, usa 2024.

1. **Datos.** Si no existe `salidas/personas_<año>.parquet`, usa primero la skill `limpiando-enaho` para ese año.

2. **Agrupación.** Elige `--por` según el pedido:
   - `area`: urbano / rural.
   - `sexo`: hombre / mujer.
   - `edad`: grupos 0–14, 15–29, 30–44, 45–64, 65+.

   Si piden otra agrupación (región, departamento, nivel educativo, etc.), dilo claramente: esta skill solo grafica por área, sexo o edad. No improvises otro gráfico.

3. **Gráfico.** Corre exactamente:

   ```bash
   uv run ${CLAUDE_SKILL_DIR}/scripts/graficar.py --por <area|sexo|edad> --anio <año>
   ```

4. **Respuesta.** Responde con la ruta de la figura (`figuras/pobreza_por_<por>_<año>.png`) y las cifras que imprimió el script, mencionando el año y que están ponderadas con `facpob07`.
