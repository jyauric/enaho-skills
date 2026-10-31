"""Limpia la ENAHO: une personas (módulo 02) con hogares (sumaria, módulo 34).

Uso:
    uv run python .claude/skills/limpiando-enaho/scripts/limpiar.py --anio 2024

Lee los .dta directamente desde los .zip en datos/ (sin descomprimir a disco),
filtra residentes habituales, une con validate="m:1", crea variables derivadas,
corre chequeos de validación y guarda:
    salidas/validacion.txt
    salidas/personas_<anio>.parquet
"""

from __future__ import annotations

import argparse
import sys
import zipfile
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[4]
DATOS = RAIZ / "datos"
SALIDAS = RAIZ / "salidas"

LLAVES_HOGAR = ["conglome", "vivienda", "hogar"]
LLAVE_PERSONA = LLAVES_HOGAR + ["codperso"]
ANCHO = {"conglome": 6, "vivienda": 3, "hogar": 2, "codperso": 2, "ubigeo": 6}

COLS_SUMARIA = LLAVES_HOGAR + ["ubigeo", "dominio", "estrato", "pobreza", "mieperho", "factor07"]
COLS_PERSONAS = LLAVE_PERSONA + ["p204", "p205", "p206", "p207", "p208a", "facpob07"]

COLS_FINALES = LLAVE_PERSONA + [
    "ubigeo", "departamento", "dominio", "estrato", "urbano",
    "p207", "p208a", "pobreza", "pobre", "mieperho", "factor07", "facpob07",
]

# Cifras de referencia (INEI) por año. Si el año no está, esos chequeos se omiten.
ESPERADO = {
    2024: {"hogares": 33_691, "personas": 108_664, "pobreza": 27.6, "pobreza_extrema": 5.5},
}
TOLERANCIA_PP = 0.1


def buscar_miembro(modulo: str, nombre: str) -> tuple[Path, str]:
    """Encuentra el zip de datos/ que contiene `nombre` (p. ej. sumaria-2024.dta)."""
    for zip_path in sorted(DATOS.glob(f"*-{modulo}.zip")):
        with zipfile.ZipFile(zip_path) as zf:
            for miembro in zf.namelist():
                if Path(miembro).name.lower() == nombre.lower():
                    return zip_path, miembro
    sys.exit(f"No se encontró {nombre} en datos/*-{modulo}.zip")


def leer_dta(zip_path: Path, miembro: str, columnas: list[str]) -> pd.DataFrame:
    """Lee solo `columnas` (sin importar mayúsculas) de un .dta dentro de un zip."""
    with zipfile.ZipFile(zip_path) as zf:
        with zf.open(miembro) as f, pd.read_stata(f, iterator=True, convert_categoricals=False) as r:
            nombres = {v.lower(): v for v in r.variable_labels()}
        faltan = [c for c in columnas if c not in nombres]
        if faltan:
            sys.exit(f"{miembro}: faltan columnas {faltan}")
        with zf.open(miembro) as f:
            df = pd.read_stata(
                f, columns=[nombres[c] for c in columnas], convert_categoricals=False
            )
    df.columns = df.columns.str.lower()
    return df


def como_texto(s: pd.Series, ancho: int) -> pd.Series:
    """Convierte una llave a texto conservando ceros a la izquierda."""
    if pd.api.types.is_numeric_dtype(s):
        s = s.astype("Int64").astype("string")
    return s.astype("string").str.strip().str.zfill(ancho)


def media_ponderada(x: pd.Series, w: pd.Series) -> float:
    return float((x * w).sum() / w.sum())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--anio", type=int, default=2024)
    anio = parser.parse_args().anio

    # 1. Lectura
    hog = leer_dta(*buscar_miembro("Modulo34", f"sumaria-{anio}.dta"), COLS_SUMARIA)
    per = leer_dta(*buscar_miembro("Modulo02", f"enaho01-{anio}-200.dta"), COLS_PERSONAS)

    # 2. Llaves y ubigeo como texto
    for df in (hog, per):
        for c in ANCHO.keys() & set(df.columns):
            df[c] = como_texto(df[c], ANCHO[c])

    # 3. Residentes habituales
    residente = ((per["p204"] == 1) & (per["p205"] == 2)) | ((per["p204"] == 2) & (per["p206"] == 1))
    per = per.loc[residente].drop(columns=["p204", "p205", "p206"])
    # Los no residentes traen vacíos que vuelven float a sexo y edad; se restituyen como enteros.
    per = per.astype({"p207": "Int8", "p208a": "Int16"})

    # 4. Unión personas -> hogares
    base = per.merge(hog, on=LLAVES_HOGAR, how="left", validate="m:1", indicator=True)

    # 5. Variables derivadas
    base["departamento"] = base["ubigeo"].str[:2]
    base["urbano"] = base["estrato"] <= 5
    base["pobre"] = base["pobreza"] <= 2

    # 6. Chequeos
    chequeos: list[tuple[str, bool]] = []

    def chequear(descripcion: str, ok: bool) -> None:
        chequeos.append((descripcion, bool(ok)))

    chequear(f"Llave de hogar única en sumaria ({len(hog):,} filas)",
             not hog.duplicated(LLAVES_HOGAR).any())
    chequear(f"Llave de persona única entre residentes ({len(per):,} filas)",
             not per.duplicated(LLAVE_PERSONA).any())
    chequear(f"La unión no pierde ni duplica filas ({len(per):,} -> {len(base):,})",
             len(base) == len(per))
    sin_hogar = int((base["_merge"] != "both").sum())
    chequear(f"Todas las personas encuentran su hogar (sin hogar: {sin_hogar})", sin_hogar == 0)

    pob = 100 * media_ponderada(base["pobre"], base["facpob07"])
    pob_ext = 100 * media_ponderada(base["pobreza"] == 1, base["facpob07"])

    esp = ESPERADO.get(anio)
    if esp:
        chequear(f"Hogares = {esp['hogares']:,} (obtenido {len(hog):,})", len(hog) == esp["hogares"])
        chequear(f"Personas residentes = {esp['personas']:,} (obtenido {len(base):,})",
                 len(base) == esp["personas"])
        chequear(f"Pobreza ponderada (facpob07) ≈ {esp['pobreza']} % ± {TOLERANCIA_PP} "
                 f"(obtenido {pob:.2f} %)", abs(pob - esp["pobreza"]) < TOLERANCIA_PP)
        chequear(f"Pobreza extrema ponderada (facpob07) ≈ {esp['pobreza_extrema']} % ± {TOLERANCIA_PP} "
                 f"(obtenido {pob_ext:.2f} %)", abs(pob_ext - esp["pobreza_extrema"]) < TOLERANCIA_PP)
    else:
        chequeos.append((f"Sin cifras de referencia para {anio}: pobreza {pob:.2f} %, "
                         f"extrema {pob_ext:.2f} %, hogares {len(hog):,}, personas {len(base):,}", True))

    # 7. Reporte y salida
    SALIDAS.mkdir(exist_ok=True)
    lineas = [f"Validación ENAHO {anio}", ""]
    lineas += [f"[{'OK' if ok else 'FALLA'}] {d}" for d, ok in chequeos]
    (SALIDAS / "validacion.txt").write_text("\n".join(lineas) + "\n", encoding="utf-8")
    print("\n".join(lineas))

    for descripcion, ok in chequeos:
        assert ok, descripcion

    base = base[COLS_FINALES].reset_index(drop=True)
    destino = SALIDAS / f"personas_{anio}.parquet"
    base.to_parquet(destino, index=False)
    print(f"\nGuardado {destino.relative_to(RAIZ)} ({len(base):,} filas, {base.shape[1]} columnas)")


if __name__ == "__main__":
    main()
