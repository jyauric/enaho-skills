# enaho-skills

Tres skills de Claude Code que limpian, grafican y mapean la **ENAHO 2024** del INEI. Basta clonar el repositorio,
bajar los datos y pedirle a Claude «un mapa de la pobreza por departamento»: Claude usa las skills en cadena y
replica la pobreza oficial.

| Skill | Entra | Sale |
|---|---|---|
| [`limpiando-enaho`](.claude/skills/limpiando-enaho/SKILL.md) | Zips de los módulos 34 (sumaria) y 02 (miembros) | `salidas/personas_2024.parquet`, `salidas/validacion.txt` |
| [`graficando-enaho`](.claude/skills/graficando-enaho/SKILL.md) | Base limpia + pobreza por área, sexo o edad | `figuras/pobreza_por_<area\|sexo\|edad>_2024.png` |
| [`mapeando-enaho`](.claude/skills/mapeando-enaho/SKILL.md) | Base limpia + GeoJSON de departamentos | `mapas/pobreza_departamento.png` |

Si la base limpia no existe, `graficando-enaho` y `mapeando-enaho` usan primero `limpiando-enaho`: un solo pedido
activa dos skills seguidas.

## 1. Requisitos

- [uv](https://docs.astral.sh/uv/) y [Claude Code](https://code.claude.com/docs).
- Clonar e instalar dependencias (pandas, pyarrow, geopandas, matplotlib):

```bash
git clone https://github.com/jyauric/enaho-skills.git
cd enaho-skills
uv sync
```

## 2. Bajar los datos

Los microdatos no se suben al repositorio (`datos/` está en `.gitignore`). Bájelos desde el navegador a una carpeta
`datos/` en la raíz, **sin descomprimir los zip**:

| Archivo | Enlace | Qué es |
|---|---|---|
| `datos/966-Modulo34.zip` | [INEI · Módulo 34](https://proyectos.inei.gob.pe/iinei/srienaho/descarga/STATA/966-Modulo34.zip) (16 MB) | Sumaria: una fila por hogar, con `pobreza` y `factor07` |
| `datos/966-Modulo02.zip` | [INEI · Módulo 02](https://proyectos.inei.gob.pe/iinei/srienaho/descarga/STATA/966-Modulo02.zip) (6 MB) | Miembros del hogar: una fila por persona, con `facpob07` |
| `datos/peru_departamental_simple.geojson` | [Límites departamentales](https://raw.githubusercontent.com/d2cml-ai/Data-Science-Python/main/sessions/06-geoespacial/lab/Data/peru_departamental_simple.geojson) (140 KB) | 25 departamentos, código `FIRST_IDDP` |

`966` es el código de la ENAHO 2024 en el portal de microdatos del INEI.

## 3. Correr todo

**Con Claude Code** (abrir `claude` en la raíz del repo y pedir en lenguaje natural):

```text
¿Cuál fue la pobreza en Cusco en 2024?        → limpiando-enaho
Grafica la pobreza urbana y rural             → graficando-enaho (+ limpiando-enaho)
Haz un mapa de la pobreza por departamento    → mapeando-enaho (+ limpiando-enaho)
```

También se pueden invocar a mano: `/limpiando-enaho 2024`, `/graficando-enaho sexo`, `/mapeando-enaho`.

**Sin Claude, solo los scripts** (en este orden):

```bash
uv run .claude/skills/limpiando-enaho/scripts/limpiar.py --anio 2024
uv run .claude/skills/graficando-enaho/scripts/graficar.py --por area    # también: sexo, edad
uv run .claude/skills/mapeando-enaho/scripts/mapear.py --anio 2024
```

## 4. Validación

`limpiar.py` termina con asserts y escribe [`salidas/validacion.txt`](salidas/validacion.txt):

| Chequeo | Resultado |
|---|---|
| Hogares en la sumaria | 33,691 |
| Residentes habituales (`(p204==1 & p205==2) \| (p204==2 & p206==1)`) | 108,664 de 117,721 |
| Llaves únicas y unión `validate="m:1"` sin perder ni duplicar filas | OK |
| Pobreza monetaria (`pobreza <= 2`, ponderada con `facpob07`) | **27.53 %** (oficial INEI: 27.6 %) |
| Pobreza extrema (`pobreza == 1`) | 5.50 % (oficial: 5.5 %) |

`mapear.py` exige 25 departamentos con dato, unidos por código (`ubigeo[:2]` = `FIRST_IDDP`), y compara cada uno con
[`referencias/pobreza_departamento_2024.csv`](.claude/skills/mapeando-enaho/referencias/pobreza_departamento_2024.csv).

### Sobre el factor de expansión

Todas las cifras se ponderan con **`facpob07`** (factor de personas), la regla fijada en las skills. Las cifras de
referencia de la clase se calcularon con la sumaria y **`factor07 × mieperho`**. Por eso hay diferencias pequeñas:

| Cifra | `facpob07` (este repo) | `factor07 × mieperho` (referencia) |
|---|---|---|
| Pobreza nacional | 27.53 % (34.1 M de personas) | 27.58 % (34.5 M) |
| Urbano / rural | 24.7 % / 39.4 % | 24.8 % / 39.3 % |
| Ica | 5.9 % | 6.0 % |
| Mayor diferencia por departamento | Puno y Huánuco, 0.5 pts | — |

Ambas pobrezas nacionales redondean al 27.6 % oficial; el mapa tolera hasta 0.5 puntos frente a la referencia.

## 5. Evaluación con y sin skills

Los tres pedidos se corrieron con `claude -p` con skills y con `--disallowedTools Skill`, cada uno en un clon limpio
del repositorio. Resultados en [`evaluacion.md`](evaluacion.md).

## Estructura

```text
.claude/skills/
  limpiando-enaho/   SKILL.md, reference.md, scripts/limpiar.py
  graficando-enaho/  SKILL.md, scripts/graficar.py
  mapeando-enaho/    SKILL.md, scripts/mapear.py, referencias/pobreza_departamento_2024.csv
salidas/validacion.txt
figuras/  mapas/
evaluacion.md  evaluacion/   (figuras de la línea base sin skills)
README.md  pyproject.toml
```

Fuente de los datos: INEI, Encuesta Nacional de Hogares (ENAHO) 2024.
