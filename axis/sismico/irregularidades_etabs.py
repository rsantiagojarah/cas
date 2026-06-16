"""
Importacion de datos desde ETABS para verificacion de irregularidades E.030.

Tablas utilizadas:
- Story Stiffness: rigidez (K) y cortante (V) por entrepiso, por sentido
- Story Definitions: alturas de entrepiso (hei)
- Story Forces: cortante por entrepiso si Story Stiffness no tiene V
"""

from __future__ import annotations

from typing import Optional

import pandas as pd

from axis.data.etabs_table_reader import get_table, clear_table_cache

NOMBRE_STORY_STIFFNESS = "Story Stiffness"
NOMBRE_STORY_DEFINITIONS = "Story Definitions"
NOMBRE_STORY_FORCES = "Story Forces"
NOMBRE_MASS_SUMMARY = "Mass Summary by Story"
GRAVEDAD = 9.80665


def _normalizar_columnas(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).strip().lower() for c in df.columns]
    return df


def _buscar_columna(df: pd.DataFrame, *patrones: str) -> Optional[str]:
    """Busca columna que contenga todos los patrones (case insensitive)."""
    for c in df.columns:
        cl = str(c).lower()
        if all(p.lower() in cl for p in patrones):
            return c
    return None


def _buscar_columna_exacta(df: pd.DataFrame, nombre: str) -> Optional[str]:
    """Busca columna cuyo nombre (sin espacios) coincida exactamente.

    Evita confundir columnas como 'StiffXh' (vacía en ETABS recientes)
    con 'StiffX', que es la que tiene los datos.
    """
    objetivo = nombre.replace(" ", "").lower()
    for c in df.columns:
        if str(c).replace(" ", "").lower() == objetivo:
            return c
    return None


def obtener_alturas_entrepiso(log: bool = True) -> Optional[dict[str, float]]:
    """
    Obtiene alturas de entrepiso desde Story Definitions.
    Retorna dict {story_name: height} ordenado de abajo a arriba.
    Excluye Base.
    """
    df = get_table(
        NOMBRE_STORY_DEFINITIONS,
        log=log,
        alternate_names=["Story Definition"],
    )
    if df is None or df.empty:
        if log:
            print("⚠ No se pudo leer 'Story Definitions' desde ETABS.")
        return None
    df = _normalizar_columnas(df)
    if "story" not in df.columns or "height" not in df.columns:
        if log:
            print("⚠ Story Definitions sin columnas 'Story' y 'Height'.")
        return None
    alturas: dict[str, float] = {}
    for _, row in df.iterrows():
        story = str(row["story"]).strip()
        if story.lower() == "base":
            continue
        try:
            h = float(row["height"])
        except (TypeError, ValueError):
            continue
        alturas[story] = h
    # Ordenar por elevation si existe
    if "elevation" in df.columns:
        elev = {str(r["story"]): float(r.get("elevation", 0) or 0)
                for _, r in df.iterrows() if str(r["story"]).lower() != "base"}
        stories_orden = sorted(alturas.keys(), key=lambda s: elev.get(s, 0))
    else:
        stories_orden = sorted(alturas.keys())
    return {s: alturas[s] for s in stories_orden}


def obtener_rigidez_cortante_etabs(
    sentido: str,
    log: bool = True,
) -> Optional[dict]:
    """
    Obtiene rigidez (K) y cortante (V) por entrepiso desde Story Stiffness.
    X: OutputCase=SPX, columnas Stiff X y Shear X.
    Y: OutputCase=SPY, columnas Stiff Y y Shear Y.
    """
    sent = sentido.upper()
    output_case = "SPX" if sent == "X" else "SPY"

    df = get_table(
        NOMBRE_STORY_STIFFNESS,
        log=log,
        alternate_names=["Storey Stiffness"],
        use_cache=False,
    )
    if df is None or df.empty:
        if log:
            print("⚠ No se pudo leer 'Story Stiffness' desde ETABS.")
        return _obtener_cortante_desde_story_forces(sentido, log)

    df = _normalizar_columnas(df)
    col_story = _buscar_columna(df, "story")
    if col_story is None:
        if log:
            print("⚠ Story Stiffness sin columna 'Story'.")
        return None

    col_output = _buscar_columna(df, "output", "case") or _buscar_columna(df, "load", "case")
    if col_output is not None:
        vals = df[col_output].astype(str).str.upper().str.strip()
        filtrado = (vals == output_case) | vals.str.startswith(output_case) | vals.str.contains(output_case, regex=False)
        df_filt = df[filtrado].copy()
        if not df_filt.empty:
            df = df_filt
        else:
            # Filtro sin filas: usar primera fila por story (evitar fallo intermitente)
            df = df.drop_duplicates(subset=[col_story], keep="first").copy()
            if log:
                print(f"⚠ Story Stiffness: filtro OutputCase={output_case} sin filas, usando primera fila por story.")

    col_k_final = _buscar_columna_exacta(df, f"stiff{sent}")
    if col_k_final is None:
        col_k_final = _buscar_columna(df, "stiff", sent)
    if col_k_final is None:
        col_k_final = next((c for c in df.columns if "stiff" in c.lower()), None)
    if col_k_final is None or col_k_final not in df.columns:
        if log:
            print(f"⚠ Story Stiffness sin columna Stiff X/Y.")
        return _obtener_cortante_desde_story_forces(sentido, log)

    col_v_final = _buscar_columna_exacta(df, f"shear{sent}")
    if col_v_final is None:
        col_v_final = _buscar_columna(df, "shear", sent)
    if col_v_final is None:
        for c in ("shear", "shearx", "sheary", "force", "vx", "vy"):
            if c in df.columns:
                col_v_final = c
                break

    df[col_k_final] = pd.to_numeric(df[col_k_final], errors="coerce")
    df = df.dropna(subset=[col_k_final])
    df = df[df[col_story].astype(str).str.lower().str.strip() != "base"]

    if df.empty:
        if log:
            print(f"⚠ Story Stiffness: la columna '{col_k_final}' no tiene valores numericos validos.")
        return _obtener_cortante_desde_story_forces(sentido, log)

    stories = df[col_story].astype(str).tolist()
    ks = [float(x) for x in df[col_k_final].tolist()]
    vs = None
    if col_v_final in df.columns:
        df[col_v_final] = pd.to_numeric(df[col_v_final], errors="coerce")
        vs = [float(x) if pd.notna(x) else 0.0 for x in df[col_v_final].tolist()]

    if vs is None:
        fuerzas = _obtener_cortante_desde_story_forces(sentido, log)
        vs = fuerzas.get("vs") if fuerzas else None

    # ETABS devuelve Story8..Story1 (arriba a abajo). Invertir para base primero (Piso 1 = base).
    stories = list(reversed(stories))
    ks = list(reversed(ks))
    if vs is not None:
        vs = list(reversed(vs))

    return {"ks": ks, "vs": vs, "stories": stories}


def _obtener_cortante_desde_story_forces(
    sentido: str,
    log: bool = True,
) -> Optional[dict]:
    """Obtiene cortante por entrepiso desde Story Forces (SISMOX/SISMOY)."""
    df = get_table(NOMBRE_STORY_FORCES, log=log, use_cache=False)
    if df is None or df.empty:
        if log:
            print("⚠ No se pudo leer 'Story Forces' desde ETABS.")
        return None
    df = _normalizar_columnas(df)
    if "outputcase" not in df.columns or "location" not in df.columns:
        return None
    caso = "SISMOX" if sentido.upper() == "X" else "SISMOY"
    col_v = "vx" if sentido.upper() == "X" else "vy"
    if col_v not in df.columns:
        return None
    filtrado = df[
        (df["outputcase"].astype(str).str.upper() == caso)
        & (df["location"].astype(str).str.lower() == "bottom")
    ].copy()
    filtrado = filtrado[filtrado["story"].astype(str).str.lower() != "base"]
    filtrado[col_v] = pd.to_numeric(filtrado[col_v], errors="coerce")
    stories = filtrado["story"].astype(str).tolist()
    vs = filtrado[col_v].abs().tolist()
    # ETABS devuelve arriba a abajo. Invertir para base primero.
    return {"vs": list(reversed(vs)), "stories": list(reversed(stories)), "ks": None}


def obtener_masa_etabs(sentido: str, log: bool = True) -> Optional[dict]:
    """
    Obtiene peso por entrepiso usando peso_edificio_etabs (Mass Summary by Story).
    sentido X -> Peso X (UX*g), sentido Y -> Peso Y (UY*g).
    """
    from axis.sismico.etapa3_analisis import peso_edificio_etabs

    df = peso_edificio_etabs(log=log, use_cache=False)
    if df is None or df.empty:
        return None
    df = _normalizar_columnas(df)
    col_peso = "peso x" if sentido.upper() == "X" else "peso y"
    if col_peso not in df.columns:
        if log:
            print(f"⚠ Tabla peso sin columna '{col_peso}'.")
        return None
    stories = df["story"].astype(str).tolist()
    ps = [float(p) for p in pd.to_numeric(df[col_peso], errors="coerce").tolist()]
    # ETABS devuelve arriba a abajo. Invertir para base primero (Piso 1 = base).
    return {"ps": list(reversed(ps)), "stories": list(reversed(stories))}


def limpiar_cache_irregularidades() -> None:
    """Limpia cache de tablas ETABS para irregularidades."""
    clear_table_cache()
