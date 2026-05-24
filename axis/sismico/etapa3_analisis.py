"""
Etapa 3 – Análisis estructural E.030.
Periodo fundamental, masa participante, peso, story forces y cortante mínima (ETABS).
"""

from __future__ import annotations

import math
from typing import Optional, Any

import pandas as pd

from axis.data.etabs_table_reader import get_table

NOMBRE_TABLA_MODAL = "Modal Participating Mass Ratios"
NOMBRE_TABLA_MODAL_PERIODS = "Modal Periods And Frequencies"
NOMBRE_TABLA_MASA = "Mass Summary by Story"
NOMBRE_TABLA_STORY_FORCES = "Story Forces"
NOMBRE_TABLA_BASE_REACTIONS = "Base Reactions"
GRAVEDAD = 9.80665
UMBRAL_MASA_PARTICIPANTE = 0.90
UMBRAL_CORTANTE_MINIMA_REGULAR = 0.80
UMBRAL_CORTANTE_MINIMA_IRREGULAR = 0.90
DECIMALES_CORTANTE_TN = 2


def cortante_minima_requerida(abs_estatico: float, umbral: float) -> float:
    """Cortante dinamica minima (Tn), redondeada como en tablas de salida."""
    return round(umbral * abs(abs_estatico), DECIMALES_CORTANTE_TN)


def cortante_cumple_umbral(abs_dinamico: float, abs_estatico: float, umbral: float) -> bool:
    """
    True si |Vdin| >= umbral * |Vest| usando la misma precision que la salida CLI (2 decimales).
    Evita falsos 'No cumple' por error de punto flotante tras escalar con gamma.
    """
    abs_est = abs(abs_estatico)
    if abs_est <= 0:
        return True
    return round(abs(abs_dinamico), DECIMALES_CORTANTE_TN) >= cortante_minima_requerida(abs_est, umbral)


def _normalizar_columnas(df: pd.DataFrame) -> pd.DataFrame:
    """Estandariza nombres de columnas a minúsculas sin espacios extra."""
    df = df.copy()
    df.columns = [str(c).strip().lower() for c in df.columns]
    return df


def periodo_fundamental_etabs(log: bool = True) -> Optional[dict[str, Any]]:
    """
    Obtiene periodo fundamental en X e Y desde 'Modal Participating Mass Ratios'.
    Ubica el modo con mayor UX (Period T para X) y mayor UY (Period T para Y).
    Retorna dict con:
    - periodo_x, periodo_y
    - tabla_case_period (Case, Period de la tabla de masa participante)
    - tabla_modal_periods (tabla ETABS 'Modal Periods And Frequencies' si existe)
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
    # Tabla adicional: Modal Periods And Frequencies
    tabla_modal_periods = None
    try:
        df_mp = get_table(
            NOMBRE_TABLA_MODAL_PERIODS,
            log=log,
            alternate_names=["Modal Periods And Frequencies"],
        )
        if df_mp is not None and not df_mp.empty:
            tabla_modal_periods = _normalizar_columnas(df_mp)
    except Exception:
        if log:
            print("⚠ No se pudo leer tabla 'Modal Periods And Frequencies'")
        tabla_modal_periods = None
    return {
        "periodo_x": periodo_x,
        "periodo_y": periodo_y,
        "tabla_case_period": tabla_reducida,
        "tabla_modal_periods": tabla_modal_periods,
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


def peso_edificio_etabs(log: bool = True, use_cache: bool = True) -> Optional[pd.DataFrame]:
    """
    'Mass Summary by Story': todos los pisos excepto base; Peso X = UX*9.80665, Peso Y = UY*9.80665.
    Salida: Story, Peso X, Peso Y (sin UX, UY).
    """
    df = get_table(NOMBRE_TABLA_MASA, log=log, use_cache=use_cache)
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


def _get_story_forces_df(log: bool = True) -> Optional[pd.DataFrame]:
    """Lee la tabla Story Forces una sola vez (la caché en get_table evita relecturas)."""
    df = get_table(NOMBRE_TABLA_STORY_FORCES, log=log)
    if df is None or df.empty:
        return None
    return _normalizar_columnas(df)


def _filtrar_story_forces(
    df: pd.DataFrame,
    output_case: str,
    col_force: str,
) -> Optional[pd.DataFrame]:
    """Filtra un DataFrame de Story Forces ya cargado por OutputCase y Location=Bottom."""
    if "outputcase" not in df.columns or "location" not in df.columns:
        return None
    filtrado = df[
        (df["outputcase"].astype(str).str.upper() == output_case.upper())
        & (df["location"].astype(str).str.lower() == "bottom")
    ].copy()
    cols = [c for c in ["story", "outputcase", col_force] if c in df.columns]
    return filtrado[cols].copy() if cols else None


def story_forces_estatico_etabs(log: bool = True) -> Optional[dict[str, pd.DataFrame]]:
    """
    Story Forces: SISMOX/Location=Bottom -> Story, OutputCase, VX;
    SISMOY/Bottom -> Story, OutputCase, VY.
    """
    df = _get_story_forces_df(log=log)
    if df is None:
        return None
    dx = _filtrar_story_forces(df, "SISMOX", "vx")
    dy = _filtrar_story_forces(df, "SISMOY", "vy")
    if dx is None and dy is None:
        return None
    return {"SISMOX": dx, "SISMOY": dy}


def _basal_from_df(
    df: Optional[pd.DataFrame],
    col: str,
    story_name: str,
) -> float:
    """Extrae cortante basal de un DataFrame de Story Forces filtrado."""
    if df is None or df.empty:
        return 0.0
    filt = df[df["story"].astype(str) == story_name]
    return float(pd.to_numeric(filt[col], errors="coerce").sum()) if not filt.empty else 0.0


def cortante_basal_paso10_etabs(
    story_name: str = "Story1",
    log: bool = True,
) -> Optional[dict[str, float]]:
    """
    Cortante basal del Paso 10 (análisis estático): Story Forces, SISMOX/SISMOY, Location=Bottom.
    """
    df = _get_story_forces_df(log=log)
    if df is None:
        return None
    dx = _filtrar_story_forces(df, "SISMOX", "vx")
    dy = _filtrar_story_forces(df, "SISMOY", "vy")
    if dx is None or dy is None:
        return None
    return {
        "cortante_basal_x": _basal_from_df(dx, "vx", story_name),
        "cortante_basal_y": _basal_from_df(dy, "vy", story_name),
    }


def story_forces_dinamico_etabs(log: bool = True) -> Optional[dict[str, pd.DataFrame]]:
    """
    Story Forces: SPX/Bottom -> Story, OutputCase, VX; SPY/Bottom -> Story, OutputCase, VY.
    """
    df = _get_story_forces_df(log=log)
    if df is None:
        return None
    dx = _filtrar_story_forces(df, "SPX", "vx")
    dy = _filtrar_story_forces(df, "SPY", "vy")
    if dx is None and dy is None:
        return None
    return {"SPX": dx, "SPY": dy}


def cortante_basal_dinamico_etabs(
    story_name: str = "Story1",
    log: bool = True,
) -> Optional[dict[str, float]]:
    """
    Cortante basal dinámica desde Story Forces (SPX/SPY, Location=Bottom).
    """
    df = _get_story_forces_df(log=log)
    if df is None:
        return None
    dx = _filtrar_story_forces(df, "SPX", "vx")
    dy = _filtrar_story_forces(df, "SPY", "vy")
    if dx is None or dy is None:
        return None
    return {
        "cortante_basal_x": _basal_from_df(dx, "vx", story_name),
        "cortante_basal_y": _basal_from_df(dy, "vy", story_name),
    }


def verificar_cortante_minima_etabs(
    log: bool = True,
    ia: float = 1.0,
    ip: float = 1.0,
) -> Optional[dict[str, Any]]:
    """
    Verifica cortante mínima dinámica respecto a la estática según E.030.
    Cortante estática y dinámica se obtienen de Story Forces (igual que paso 12), no de Base Reactions.
    - Si Ia = 1 e Ip = 1 (edificio regular): Vdin >= 0.80 * Vest.
    - Si Ia != 1 o Ip != 1 (edificio irregular): Vdin >= 0.90 * Vest.
    Retorna, por cada dirección (x, y): cortante_estatico, cortante_dinamico, umbral,
    requiere_escalar, factor_escala, cortante_dinamico_escalado, cumple_con_escalar,
    y tabla = Story Forces cortante dinámica (SPX/SPY, Location=Bottom) por piso.
    """
    basal_est = cortante_basal_paso10_etabs(log=log)
    basal_din = cortante_basal_dinamico_etabs(log=log)
    tbl_din = story_forces_dinamico_etabs(log=log)
    if basal_est is None or basal_din is None:
        return None
    def _es_irregular(valor: Optional[float]) -> bool:
        if valor is None:
            return False
        try:
            return abs(float(valor) - 1.0) > 1e-6
        except (TypeError, ValueError):
            return False
    tiene_irregularidad = _es_irregular(ia) or _es_irregular(ip)
    umbral = UMBRAL_CORTANTE_MINIMA_IRREGULAR if tiene_irregularidad else UMBRAL_CORTANTE_MINIMA_REGULAR
    resultado = {}
    for key, col_force, caso in [("x", "vx", "SPX"), ("y", "vy", "SPY")]:
        v_est = basal_est["cortante_basal_x"] if key == "x" else basal_est["cortante_basal_y"]
        v_din = basal_din["cortante_basal_x"] if key == "x" else basal_din["cortante_basal_y"]
        # Tabla cortante dinámica por piso (Story Forces, igual que paso 12 para estático)
        tbl_out = None
        if tbl_din and caso in tbl_din and tbl_din[caso] is not None and not tbl_din[caso].empty:
            df_t = tbl_din[caso].copy()
            df_t = df_t[["story", "outputcase", col_force]]
            df_t.columns = ["Story", "OutputCase", "VX" if key == "x" else "VY"]
            tbl_out = df_t
        if v_est == 0:
            # Sin cortante estática definida no se puede verificar; se deja sin requerir escalamiento.
            ratio = 0.0
            cortante_minima = 0.0
            requiere_escalar = False
            factor_escala = 1.0
            v_din_escalado = v_din
            ratio_escalado = 0.0
            cumple_sin_escalar = True
            cumple_con_escalar = True
        else:
            abs_est = abs(v_est)
            abs_din = abs(v_din)
            ratio = abs_din / abs_est if abs_est else 0.0
            cortante_minima = cortante_minima_requerida(abs_est, umbral)
            cumple_sin_escalar = cortante_cumple_umbral(abs_din, abs_est, umbral)
            if not cumple_sin_escalar and abs_din > 0:
                factor_escala = cortante_minima / abs_din
                v_din_escalado = math.copysign(cortante_minima, v_din)
            else:
                factor_escala = 1.0
                v_din_escalado = v_din
            abs_din_esc = abs(v_din_escalado)
            ratio_escalado = abs_din_esc / abs_est if abs_est else 0.0
            requiere_escalar = (not cumple_sin_escalar) and abs_din > 0 and abs_est > 0
            cumple_con_escalar = cortante_cumple_umbral(abs_din_esc, abs_est, umbral)
        resultado[key] = {
            "cortante_estatico": v_est,
            "cortante_dinamico": v_din,
            "ratio": ratio,
            "umbral": umbral,
            "cortante_minima_requerida": cortante_minima,
            "requiere_escalar": requiere_escalar,
            "factor_escala": factor_escala,
            "cortante_dinamico_escalado": v_din_escalado,
            "ratio_escalado": ratio_escalado,
            "cumple_sin_escalar": cumple_sin_escalar,
            "cumple_con_escalar": cumple_con_escalar,
            "tabla": tbl_out,
        }
    return resultado
