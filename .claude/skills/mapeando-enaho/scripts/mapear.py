"""Mapa de la pobreza monetaria de la ENAHO por departamento.

Uso:
    uv run .claude/skills/mapeando-enaho/scripts/mapear.py --anio 2024

Lee salidas/personas_<anio>.parquet (creado por la skill limpiando-enaho),
calcula el % de personas pobres por departamento ponderado con facpob07,
lo une al GeoJSON de departamentos POR CÓDIGO (ubigeo[:2] = FIRST_IDDP, como
texto) y guarda mapas/pobreza_departamento.png a 200 dpi.

Validación (asserts): 25 departamentos, ninguno sin dato, y cada cifra a menos
de 0.5 puntos de referencias/pobreza_departamento_<anio>.csv. La referencia de
la clase se calculó con la sumaria (factor07 x mieperho); aquí se pondera con
facpob07, por eso hay diferencias de hasta 0.5 puntos (Huánuco).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd

SKILL = Path(__file__).resolve().parents[1]
RAIZ = Path(__file__).resolve().parents[4]
SALIDAS = RAIZ / "salidas"
MAPAS = RAIZ / "mapas"
GEOJSON = RAIZ / "datos" / "peru_departamental_simple.geojson"
GEOJSON_URL = (
    "https://raw.githubusercontent.com/d2cml-ai/Data-Science-Python/main/"
    "sessions/06-geoespacial/lab/Data/peru_departamental_simple.geojson"
)

N_DEPARTAMENTOS = 25
TOLERANCIA_PP = 0.5
CMAP = "Blues"  # un solo tono, de claro a oscuro; nunca arcoíris


def pobreza_por_departamento(origen: Path) -> pd.DataFrame:
    df = pd.read_parquet(origen, columns=["departamento", "pobre", "facpob07"])
    df["departamento"] = df["departamento"].astype("string").str.zfill(2)
    df = df.assign(pobre_pond=df["pobre"].astype(float) * df["facpob07"])
    tabla = df.groupby("departamento").agg(pobres=("pobre_pond", "sum"), poblacion=("facpob07", "sum"))
    tabla["pobreza_pct"] = 100 * tabla["pobres"] / tabla["poblacion"]
    return tabla[["pobreza_pct"]].reset_index()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--anio", type=int, default=2024)
    anio = parser.parse_args().anio

    origen = SALIDAS / f"personas_{anio}.parquet"
    if not origen.exists():
        sys.exit(f"No existe {origen.relative_to(RAIZ)}. Corre primero la skill limpiando-enaho para {anio}.")
    if not GEOJSON.exists():
        sys.exit(f"No existe {GEOJSON.relative_to(RAIZ)}. Descárgalo de {GEOJSON_URL}")

    pobreza = pobreza_por_departamento(origen)

    # Unión POR CÓDIGO, nunca por nombre («APURIMAC» no es «Apurímac»).
    geo = gpd.read_file(GEOJSON)
    geo["departamento"] = geo["FIRST_IDDP"].astype("string").str.zfill(2)
    mapa = geo.merge(pobreza, on="departamento", how="left", validate="1:1")

    # Validación
    assert len(mapa) == N_DEPARTAMENTOS, f"Se esperaban {N_DEPARTAMENTOS} departamentos y hay {len(mapa)}"
    sin_dato = mapa.loc[mapa["pobreza_pct"].isna(), "NOMBDEP"].tolist()
    assert not sin_dato, f"Departamentos sin dato (la unión falló): {sin_dato}"
    assert {"07", "15"} <= set(mapa["departamento"]), "Lima (15) y Callao (07) deben ir separados"

    tabla = mapa[["departamento", "NOMBDEP", "pobreza_pct"]].copy()
    ref_csv = SKILL / "referencias" / f"pobreza_departamento_{anio}.csv"
    if ref_csv.exists():
        ref = pd.read_csv(ref_csv, dtype={"ccdd": str})[["ccdd", "pobreza_pct"]]
        ref = ref.rename(columns={"ccdd": "departamento", "pobreza_pct": "referencia"})
        tabla = tabla.merge(ref[["departamento", "referencia"]], on="departamento", how="left", validate="1:1")
        tabla["diferencia"] = tabla["pobreza_pct"].round(1) - tabla["referencia"]
        fuera = tabla.loc[tabla["diferencia"].abs() > TOLERANCIA_PP + 1e-9]
        assert fuera.empty, f"Difieren más de {TOLERANCIA_PP} pts de la referencia:\n{fuera.to_string(index=False)}"
    else:
        print(f"Aviso: no hay referencia para {anio}; las cifras no están validadas.", file=sys.stderr)

    # Mapa
    fig, ax = plt.subplots(figsize=(7, 9))
    mapa.plot(
        column="pobreza_pct", cmap=CMAP, vmin=0, vmax=mapa["pobreza_pct"].max(),
        edgecolor="white", linewidth=0.6, ax=ax, legend=True,
        legend_kwds={"label": "% de personas en pobreza monetaria", "shrink": 0.6},
    )
    ax.set_axis_off()
    ax.set_title(f"Pobreza monetaria por departamento, Perú {anio}", loc="left", fontsize=13, fontweight="bold")
    fig.text(0.02, 0.02, f"Fuente: INEI, ENAHO {anio}. Ponderado con facpob07.", fontsize=8, color="#555555")

    MAPAS.mkdir(exist_ok=True)
    destino = MAPAS / "pobreza_departamento.png"
    fig.savefig(destino, dpi=200, bbox_inches="tight")
    plt.close(fig)

    tabla = tabla.sort_values("pobreza_pct", ascending=False)
    print(f"Pobreza monetaria por departamento, Perú {anio} (ponderado con facpob07)")
    print(tabla.to_string(index=False, float_format=lambda v: f"{v:.1f}"))
    print(f"\n[OK] {len(mapa)} departamentos, ninguno sin dato; unión por código (FIRST_IDDP)")
    if "referencia" in tabla:
        print(f"[OK] Todas las cifras a menos de {TOLERANCIA_PP} pts de la referencia")
    print(f"Mapa: {destino.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
