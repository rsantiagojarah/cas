"""
Etapa 3 – Análisis estructural E.030.
Periodo fundamental, masa participante, peso, story forces y cortante mínima (ETABS).
"""

from __future__ import annotations

from typing import Optional, Any

import pandas as pd

from axis.data.etabs_table_reader import get_table

NOMBRE_TABLA_MODAL = "Modal Participating Mass Ratios"
NOMBRE_TABLA_MASA = "Mass Summary by Story"
NOMBRE_TABLA_STORY_FORCES = "Story Forces"
NOMBRE_TABLA_BASE_REACTIONS = "Base Reactions"
GRAVEDAD = 9.80665
UMBRAL_MASA_PARTICIPANTE = 0.90
UMBRAL_CORTANTE_MINIMA = 0.80


def _normalizar_columnas(df: pd.DataFrame) -> pd.DataFrame:
    """Estandariza nombres de columnas a minúsculas sin espacios extra."""
    df = df.copy()
    df.columns = [str(c).strip().lower() for c in df.columns]
    return df


def periodo_fundamental_etabs(log: bool = True) -> Optional[dict[str, Any]]:
    """
    Obtiene periodo fundamental en X e Y desde 'Modal Participating Mass Ratios'.
    Ubica el modo con mayor UX (Period T para X) y mayor UY (Period T para Y).
    Retorna dict con periodo_x, periodo_y, tabla Case/Period (y opcionalmente filas UX/UY máximas).
    """
    df = get_table(
        NOMBRE_TABLA_MODAL,
        log=log,
        alternate_names=["Modal Participating Mass Ratio"],
    )
    if df is None or df.empty:
        return None
    df = _normalizar_columnas(df)
    for col in ("case", "period", "ux", "uy"):
        if col not in df.columns:
            if log:
                print(f"⚠ Tabla modal sin columna '{col}'")
            return None
    df["ux"] = pd.to_numeric(df["ux"], errors="coerce")
    df["uy"] = pd.to_numeric(df["uy"], errors="coerce")
    idx_max_ux = df["ux"].idxmax()
    idx_max_uy = df["uy"].idxmax()
    periodo_x = float(df.loc[idx_max_ux, "period"])
    periodo_y = float(df.loc[idx_max_uy, "period"])
    tabla_reducida = df[["case", "period"]].copy()
    return {
        "periodo_x": periodo_x,
        "periodo_y": periodo_y,
        "tabla_case_period": tabla_reducida,
    }


def masa_participante_etabs(log: bool = True) -> Optional[dict[str, Any]]:
    """
    Tabla 'Modal Participating Mass Ratios' con Case, Period, UX, UY, UZ, SumUX, SumUY, SumUZ.
    Verifica que porcentaje de masa participante sea >= 90% en cada dirección.
    """
    df = get_table(
        NOMBRE_TABLA_MODAL,
        log=log,
        alternate_names=["Modal Participating Mass Ratio"],
    )
    if df is None or df.empty:
        return None
    df = _normalizar_columnas(df)
    cols_necesarias = ["case", "period", "ux", "uy", "uz", "sumux", "sumuy", "sumuz"]
    faltan = [c for c in cols_necesarias if c not in df.columns]
    if faltan:
        if log:
            print(f"⚠ Tabla modal sin columnas: {faltan}")
        return None
    for c in ("sumux", "sumuy"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    cumple_x = (df["sumux"].max() >= UMBRAL_MASA_PARTICIPANTE) if len(df) else False
    cumple_y = (df["sumuy"].max() >= UMBRAL_MASA_PARTICIPANTE) if len(df) else False
    tabla = df[cols_necesarias].copy()
    return {
        "tabla": tabla,
        "cumple_90_x": cumple_x,
        "cumple_90_y": cumple_y,
    }


def peso_edificio_etabs(log: bool = True) -> Optional[pd.DataFrame]:
    """
    'Mass Summary by Story': todos los pisos excepto base; Peso X = UX*9.80665, Peso Y = UY*9.80665.
    Salida: Story, Peso X, Peso Y (sin UX, UY).
    """
    df = get_table(NOMBRE_TABLA_MASA, log=log)
    if df is None or df.empty:
        return None
    df = _normalizar_columnas(df)
    if "story" not in df.columns or "ux" not in df.columns or "uy" not in df.columns:
        if log:
            print("⚠ Mass Summary sin columnas story, ux, uy")
        return None
    df = df[df["story"].astype(str).str.lower() != "base"].copy()
    df["ux"] = pd.to_numeric(df["ux"], errors="coerce")
    df["uy"] = pd.to_numeric(df["uy"], errors="coerce")
    df["Peso X"] = df["ux"] * GRAVEDAD
    df["Peso Y"] = df["uy"] * GRAVEDAD
    return df[["story", "Peso X", "Peso Y"]].copy()


def _story_forces_filtrado(
    output_case: str,
    col_force: str,
    log: bool = True,
) -> Optional[pd.DataFrame]:
    """Obtiene Story Forces filtrado por OutputCase y Location=Bottom."""
    df = get_table(NOMBRE_TABLA_STORY_FORCES, log=log)
    if df is None or df.empty:
        return None
    df = _normalizar_columnas(df)
    if "outputcase" not in df.columns or "location" not in df.columns:
        return None
    df = df[
        (df["outputcase"].astype(str).str.upper() == output_case.upper())
        & (df["location"].astype(str).str.lower() == "bottom")
    ].copy()
    cols = [c for c in ["story", "outputcase", col_force] if c in df.columns]
    return df[cols].copy() if cols else None


def story_forces_estatico_etabs(log: bool = True) -> Optional[dict[str, pd.DataFrame]]:
    """
    Story Forces: SISMOX/Location=Bottom -> Story, OutputCase, VX;
    SISMOY/Bottom -> Story, OutputCase, VY.
    """
    dx = _story_forces_filtrado("SISMOX", "vx", log=log)
    dy = _story_forces_filtrado("SISMOY", "vy", log=log)
    if dx is None and dy is None:
        return None
    return {"SISMOX": dx, "SISMOY": dy}


def cortante_basal_paso10_etabs(
    story_name: str = "Story1",
    log: bool = True,
) -> Optional[dict[str, float]]:
    """
    Cortante basal del Paso 10 (análisis estático): Story Forces, SISMOX/SISMOY, Location=Bottom.
    Retorna VX en Story1 para SISMOX y VY en Story1 para SISMOY (cortante basal por dirección).
    """
    dx = _story_forces_filtrado("SISMOX", "vx", log=log)
    dy = _story_forces_filtrado("SISMOY", "vy", log=log)
    if dx is None or dy is None:
        return None
    dx = dx[dx["story"].astype(str) == story_name]
    dy = dy[dy["story"].astype(str) == story_name]
    vx = pd.to_numeric(dx["vx"], errors="coerce").sum() if not dx.empty else 0.0
    vy = pd.to_numeric(dy["vy"], errors="coerce").sum() if not dy.empty else 0.0
    return {"cortante_basal_x": float(vx), "cortante_basal_y": float(vy)}


def story_forces_dinamico_etabs(log: bool = True) -> Optional[dict[str, pd.DataFrame]]:
    """
    Story Forces: SPX/Bottom -> Story, OutputCase, VX; SPY/Bottom -> Story, OutputCase, VY.
    """
    dx = _story_forces_filtrado("SPX", "vx", log=log)
    dy = _story_forces_filtrado("SPY", "vy", log=log)
    if dx is None and dy is None:
        return None
    return {"SPX": dx, "SPY": dy}


def verificar_cortante_minima_etabs(log: bool = True) -> Optional[dict[str, Any]]:
    """
    Base Reactions: verifica que cortante dinámico (SPX/SPY) >= 80% del estático (SISMOX/SISMOY).
    Usa columna FX para X y FY para Y (según nomenclatura típica Base Reactions).
    """
    df = get_table(NOMBRE_TABLA_BASE_REACTIONS, log=log)
    if df is None or df.empty:
        return None
    df = _normalizar_columnas(df)
    if "outputcase" not in df.columns or "fx" not in df.columns or "fy" not in df.columns:
        if log:
            print("⚠ Base Reactions sin outputcase, fx o fy")
        return None
    casos = {"x": ("SISMOX", "SPX", "fx"), "y": ("SISMOY", "SPY", "fy")}
    resultado = {}
    for key, (estatico, dinamico, col) in casos.items():
        est = df[df["outputcase"].astype(str).str.upper() == estatico]
        din = df[df["outputcase"].astype(str).str.upper() == dinamico]
        v_est = pd.to_numeric(est[col], errors="coerce").sum()
        v_din = pd.to_numeric(din[col], errors="coerce").sum()
        if v_est == 0:
            cumple = True
            ratio = 0.0
        else:
            ratio = v_din / v_est
            cumple = ratio >= UMBRAL_CORTANTE_MINIMA
        resultado[key] = {
            "cortante_estatico": v_est,
            "cortante_dinamico": v_din,
            "ratio": ratio,
            "cumple_80": cumple,
        }
    return resultado
