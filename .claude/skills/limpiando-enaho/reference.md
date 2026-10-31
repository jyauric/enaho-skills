# Referencia: base de personas ENAHO

`salidas/personas_<año>.parquet` tiene una fila por **residente habitual**. Las etiquetas vienen de los `.dta` de 2024.

## Diccionario de las 16 columnas

| Columna | Origen | Tipo | Descripción |
|---|---|---|---|
| `conglome` | ambos | texto (6) | Conglomerado. Parte de la llave de hogar. |
| `vivienda` | ambos | texto (3) | Vivienda dentro del conglomerado. |
| `hogar` | ambos | texto (2) | Hogar dentro de la vivienda. |
| `codperso` | 02 | texto (2) | Número de orden de la persona en el hogar. |
| `ubigeo` | 34 | texto (6) | Ubicación geográfica INEI: departamento (2) + provincia (2) + distrito (2). |
| `departamento` | derivada | texto (2) | `ubigeo[:2]`: 01 Amazonas … 25 Ucayali (07 = Callao, 15 = Lima). |
| `dominio` | 34 | entero | 1 costa norte, 2 costa centro, 3 costa sur, 4 sierra norte, 5 sierra centro, 6 sierra sur, 7 selva, 8 Lima Metropolitana. |
| `estrato` | 34 | entero | 1 ≥ 500 000 hab. … 5 de 2 000 a 19 999 hab.; 6 de 500 a 1 999 hab.; 7 AER compuesto; 8 AER simple. |
| `urbano` | derivada | booleano | `estrato <= 5`. |
| `p207` | 02 | entero | Sexo: 1 hombre, 2 mujer. |
| `p208a` | 02 | entero | Edad en años cumplidos. |
| `pobreza` | 34 | entero | 1 pobre extremo, 2 pobre no extremo, 3 no pobre. |
| `pobre` | derivada | booleano | `pobreza <= 2`. |
| `mieperho` | 34 | entero | Total de miembros del hogar. |
| `factor07` | 34 | decimal | Factor de expansión **del hogar** (proyecciones CPV 2007). |
| `facpob07` | 02 | decimal | Factor de expansión **de población** (proyecciones CPV 2007). Es el que se usa para toda cifra de personas. |

## Las trampas de la ENAHO

1. **Ceros a la izquierda.** `conglome`, `vivienda`, `hogar`, `codperso` y `ubigeo` son códigos, no números. Si se leen o guardan como números, `"010651"` pasa a ser `10651`: la unión falla en silencio y `ubigeo[:2]` devuelve un departamento equivocado. Trátalos siempre como texto con su ancho fijo.

2. **Nombres rotos.** Por la codificación de los `.dta`, la columna del año llega como `aÑo`, y en otros años puede haber nombres en mayúscula. Antes de usar cualquier columna, normaliza todos los nombres a minúscula (`df.columns = df.columns.str.lower()`).

3. **No todos son residentes.** En 2024, el módulo 02 tiene 117,721 filas, pero solo 108,664 son residentes habituales; el resto son visitas y miembros ausentes. La población oficial usa solo residentes: `(p204 == 1 & p205 == 2) | (p204 == 2 & p206 == 1)`. Si te saltas el filtro, la población y las tasas cambian.

4. **Uniones que duplican.** Si un hogar está repetido en la tabla de hogares, una unión sin `validate="m:1"` multiplica a sus personas sin avisar. Toda unión lleva `validate` explícito, y después se comprueba que el número de filas no cambió.

5. **Encuestas no son personas.** En 2024, los 33,691 hogares de la muestra representan a 34.5 millones de personas (suma de `factor07 × mieperho`). Toda cifra va ponderada, con el factor que corresponda a la unidad de análisis: `facpob07` para personas y `factor07` para hogares, este último sobre la sumaria, con una fila por hogar. Una tasa sin ponderar, o calculada con el factor equivocado, no coincide con el INEI.

   Las dos formas de expandir a personas no dan la misma población. Con `facpob07` sobre los residentes, la población es ≈ 34.1 millones y la pobreza, 27.53 %; con `factor07 × mieperho` sobre la sumaria, ≈ 34.5 millones y 27.58 %. Ambas tasas redondean al 27.6 % oficial. Esta base usa `facpob07`, que es la regla de las skills.

6. **Códigos, no números.** Con `convert_categoricals=False`, `pobreza`, `p207`, `dominio` y `estrato` llegan como números sin etiquetas, pero son categorías. En `pobreza`, 1, 2 y 3 son categorías: pobre es `pobreza <= 2` (con `== 1` solo se cuenta la pobreza extrema), y su promedio no tiene sentido. En la sumaria está además `pobrezav`, cuya escala tiene 4 categorías: no la confundas con `pobreza`.

7. **Hay dos sumarias.** El zip del módulo 34 trae `sumaria-<año>.dta` y `sumaria-<año>-12g.dta` (agregados con 12 grupos de gasto). La base usa la primera. No mezcles variables de las dos.

8. **«Región» no siempre es departamento.** `dominio` es una región natural (costa, sierra, selva, Lima Metropolitana); `departamento` sale del ubigeo. El código 15 (Lima) junta Lima Metropolitana con Lima Provincias, y Callao (07) va aparte. Si el usuario dice «región», aclara cuál de los dos usas.

## Agregar una variable

1. Confirma su nombre y su módulo en el diccionario del INEI (`Diccionario<año>.pdf`, dentro de los zip).
2. Agrégala a `COLS_SUMARIA` (si es de hogar, módulo 34) o a `COLS_PERSONAS` (si es de persona, módulo 02) en `scripts/limpiar.py`, y también a `COLS_FINALES`.
3. Si viene de otro módulo, únela por `conglome`, `vivienda`, `hogar` (más `codperso` si es de personas), con `validate` explícito.
4. Vuelve a correr el script y revisa que la validación siga sin fallas.
