---
name: limpiando-enaho
description: Limpia los módulos 34 (sumaria) y 02 (miembros) de la ENAHO del INEI y arma una base de personas con pobreza y factor de expansión. Úsala cuando pidan limpiar, unir o analizar la ENAHO, o calcular pobreza por región, departamento, sexo o edad.
argument-hint: [año]
---

# Limpiando la ENAHO

0. **Año.** Si el pedido del usuario o los argumentos ($ARGUMENTS) mencionan un año de 4 dígitos, úsalo. Si no, usa 2024 y empieza la respuesta con «Datos de la ENAHO 2024».

1. **Datos.** Revisa que existan en `datos/` el zip del módulo 34 (`<código>-Modulo34.zip`, con `sumaria-<año>.dta`) y el del módulo 02 (`<código>-Modulo02.zip`, con `enaho01-<año>-200.dta`). Si falta alguno, detente y pide al usuario que lo baje del portal de microdatos del INEI (https://proyectos.inei.gob.pe/microdatos/), en formato STATA. El código de encuesta cambia cada año (966 = 2024).

2. **Limpieza.** Corre exactamente:

   ```bash
   uv run ${CLAUDE_SKILL_DIR}/scripts/limpiar.py --anio <año>
   ```

3. **Validación.** Lee `salidas/validacion.txt`. Si alguna línea dice `FALLA`, o si la pobreza difiere de la cifra oficial del INEI para ese año en más de 0.1 puntos, detente: muestra el reporte al usuario y no calcules nada. Para años sin cifra de referencia en el script, el reporte solo muestra la pobreza obtenida; informa la cifra obtenida y advierte que no está validada contra el INEI.

4. **Respuesta.** Calcula con `salidas/personas_<año>.parquet`. Toda cifra va ponderada con `facpob07` (por ejemplo, `(df.pobre * df.facpob07).sum() / df.facpob07.sum()`) y siempre se menciona el año. No reportes conteos muestrales como si fueran cifras poblacionales.

5. **Variables nuevas.** Antes de usar una variable que no está en la base, lee [reference.md](reference.md).
