"""Grafica la pobreza monetaria de la ENAHO por área, sexo o grupo de edad.

Uso:
    uv run .claude/skills/graficando-enaho/scripts/graficar.py --por area --anio 2024

Lee salidas/personas_<anio>.parquet (creado por la skill limpiando-enaho),
calcula el % de personas pobres ponderado con facpob07 y guarda:
    figuras/pobreza_por_<por>_<anio>.png  (200 dpi)
Imprime la tabla de valores en la consola.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

RAIZ = Path(__file__).resolve().parents[4]
SALIDAS = RAIZ / "salidas"
FIGURAS = RAIZ / "figuras"

COLOR = "#2a6f97"
GRUPOS_EDAD = ["0–14", "15–29", "30–44", "45–64", "65+"]
TITULOS = {
    "area": "Pobreza monetaria por área de residencia",
    "sexo": "Pobreza monetaria por sexo",
    "edad": "Pobreza monetaria por grupo de edad",
}


def asignar_grupo(df: pd.DataFrame, por: str) -> pd.Series:
    if por == "area":
        return df["urbano"].map({True: "Urbano", False: "Rural"})
    if por == "sexo":
        return df["p207"].map({1: "Hombre", 2: "Mujer"})
    edad = pd.cut(
        df["p208a"].astype("float"),
        bins=[-1, 14, 29, 44, 64, float("inf")],
        labels=GRUPOS_EDAD,
    )
    return edad.astype("string")


def calcular(df: pd.DataFrame, por: str) -> pd.DataFrame:
    df = df.assign(grupo=asignar_grupo(df, por))
    sin_grupo = df["grupo"].isna().sum()
    if sin_grupo:
        print(f"Aviso: {sin_grupo} personas sin valor de agrupación; se excluyen.", file=sys.stderr)
        df = df[df["grupo"].notna()]
    df = df.assign(pobre_pond=df["pobre"].astype(float) * df["facpob07"])
    tabla = df.groupby("grupo").agg(
        pobres=("pobre_pond", "sum"),
        poblacion=("facpob07", "sum"),
        n_muestral=("facpob07", "size"),
    )
    tabla["pct_pobres"] = 100 * tabla["pobres"] / tabla["poblacion"]
    if por == "edad":
        tabla = tabla.reindex(GRUPOS_EDAD)
    else:
        tabla = tabla.sort_values("pct_pobres", ascending=False)
    return tabla


def graficar(tabla: pd.DataFrame, por: str, anio: int, destino: Path) -> None:
    etiquetas = list(tabla.index)
    valores = tabla["pct_pobres"].to_numpy()

    fig, ax = plt.subplots(figsize=(8, 1.2 + 0.6 * len(etiquetas)))
    ax.barh(etiquetas, valores, color=COLOR, height=0.6)
    ax.invert_yaxis()  # primera categoría arriba

    tope = valores.max()
    ax.set_xlim(0, tope * 1.15)
    for y, v in enumerate(valores):
        ax.text(v + tope * 0.01, y, f"{v:.1f} %", va="center", ha="left", fontsize=10)

    ax.set_title(f"{TITULOS[por]}, Perú {anio}", loc="left", fontsize=12, fontweight="bold")
    ax.set_xlabel("% de personas")
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(axis="y", length=0)
    fig.text(0.01, 0.01, f"Fuente: INEI, ENAHO {anio}", fontsize=8, color="#555555", ha="left", va="bottom")

    fig.tight_layout(rect=(0, 0.04, 1, 1))
    destino.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(destino, dpi=200)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--por", required=True, choices=["area", "sexo", "edad"])
    parser.add_argument("--anio", type=int, default=2024)
    args = parser.parse_args()

    origen = SALIDAS / f"personas_{args.anio}.parquet"
    if not origen.exists():
        sys.exit(f"No existe {origen.relative_to(RAIZ)}. Corre primero la skill limpiando-enaho para {args.anio}.")

    df = pd.read_parquet(origen, columns=["urbano", "p207", "p208a", "pobre", "facpob07"])
    tabla = calcular(df, args.por)

    destino = FIGURAS / f"pobreza_por_{args.por}_{args.anio}.png"
    graficar(tabla, args.por, args.anio, destino)

    print(f"{TITULOS[args.por]}, Perú {args.anio} (ponderado con facpob07)")
    print(f"{'Grupo':<10}{'% pobres':>10}{'n muestral':>12}")
    for grupo, fila in tabla.iterrows():
        print(f"{grupo:<10}{fila['pct_pobres']:>9.1f} %{int(fila['n_muestral']):>12,}")
    print(f"Figura: {destino.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
