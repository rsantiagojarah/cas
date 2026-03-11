"""
Etapa 4 – Validación de la estructura E.030.
Clasificación del sistema (pórtico/dual/muros), distorsión admisible y separación.
"""

from __future__ import annotations

from typing import Optional, Any

import pandas as pd

from axis.data.etabs_table_reader import get_table
from axis.sismico.tables_e030 import obtener_distorsion_maxima, DISTORSION_MAXIMA

NOMBRE_TABLA_STORY_DRIFTS = "Story Drifts"
NOMBRE_TABLA_ELEMENT_FORCES = "Element Forces - Columns"
ALTERNATE_TABLAS_ELEMENT_FORCES = ["Element Forces - Frames", "Frame Forces", "Section Cut Forces"]
STORY_PISO_1 = "Story1"
ESTACION_BASE = "0"


def _normalizar_columnas(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).strip().lower() for c in df.columns]
    return df


def _obtener_tabla_element_forces(log: bool = True) -> Optional[pd.DataFrame]:
    """Obtiene tabla de fuerzas en elementos (columnas/frames) probando nombres alternativos."""
    df = get_table(
        NOMBRE_TABLA_ELEMENT_FORCES,
        log=log,
        alternate_names=ALTERNATE_TABLAS_ELEMENT_FORCES,
    )
    if df is None or df.empty:
        return None
    return _normalizar_columnas(df)


def _columna_elemento(df: pd.DataFrame) -> str:
    """Nombre de columna que identifica el elemento (Column, Frame, Element)."""
    for c in ("column", "frame", "element", "name"):
        if c in df.columns:
            return c
    return "column"


def clasificar_sistema_estructural_etabs(
    cortante_basal_x: Optional[float] = None,
    cortante_basal_y: Optional[float] = None,
    story_cortante: str = STORY_PISO_1,
    log: bool = True,
) -> Optional[dict[str, Any]]:
    """
    Paso 12 E.030: Tabla ETABS Story=Story1, OutputCase=SPX/SPY, Station=0.
    Columnas: Story, Column, OutputCase, V3 (X) o V2 (Y). Suma V3 y V2; % de cortante basal paso 10.
    Clasifica: Pórtico (<20% muros), Dual (20-70%), Muros estructurales (≥70%).
    Si cortante_basal_x/y no se pasan, se obtienen de Story Forces SISMOX/SISMOY en Story1 (paso 10).
    """
    from axis.sismico.etapa3_analisis import cortante_basal_paso10_etabs
    if cortante_basal_x is None or cortante_basal_y is None:
        basal = cortante_basal_paso10_etabs(story_name=story_cortante, log=log)
        if basal:
            if cortante_basal_x is None:
                cortante_basal_x = basal["cortante_basal_x"]
            if cortante_basal_y is None:
                cortante_basal_y = basal["cortante_basal_y"]
        if cortante_basal_x is None:
            cortante_basal_x = 0.0
        if cortante_basal_y is None:
            cortante_basal_y = 0.0
    cortante_basal_x = float(cortante_basal_x)
    cortante_basal_y = float(cortante_basal_y)
    df = _obtener_tabla_element_forces(log=log)
    if df is None or df.empty:
        return None
    col_elem = _columna_elemento(df)
    for c in ("story", "outputcase", "v2", "v3"):
        if c not in df.columns:
            if log:
                print(f"⚠ Tabla Element Forces sin columna '{c}'")
            return None
    station_col = "station" if "station" in df.columns else next(
        (x for x in ["sta", "objsta", "elmsta"] if x in df.columns), "station"
    )
    if station_col not in df.columns:
        if log:
            print("⚠ Tabla sin columna Station/Sta. Se asume Station=0.")
        mask_station = pd.Series(True, index=df.index)
    else:
        mask_station = df[station_col].astype(str) == ESTACION_BASE
    df_x = df[
        (df["story"].astype(str) == story_cortante)
        & (df["outputcase"].astype(str).str.upper() == "SPX")
        & mask_station
    ].copy()
    df_y = df[
        (df["story"].astype(str) == story_cortante)
        & (df["outputcase"].astype(str).str.upper() == "SPY")
        & mask_station
    ].copy()
    sum_v3 = pd.to_numeric(df_x["v3"], errors="coerce").sum()
    sum_v2 = pd.to_numeric(df_y["v2"], errors="coerce").sum()
    abs_basal_x = abs(cortante_basal_x)
    abs_basal_y = abs(cortante_basal_y)
    abs_col_x = abs(sum_v3)
    abs_col_y = abs(sum_v2)
    pct_columnas_x = min(100.0, (abs_col_x / abs_basal_x * 100.0)) if abs_basal_x else 0.0
    pct_columnas_y = min(100.0, (abs_col_y / abs_basal_y * 100.0)) if abs_basal_y else 0.0
    pct_muros_x = 100.0 - pct_columnas_x
    pct_muros_y = 100.0 - pct_columnas_y
    cortante_muros_x = max(0.0, abs_basal_x - abs_col_x)
    cortante_muros_y = max(0.0, abs_basal_y - abs_col_y)
    sistema_x = _clasificar_porcentaje(pct_muros_x)
    sistema_y = _clasificar_porcentaje(pct_muros_y)
    tabla_x_out = df_x[["story", col_elem, "outputcase", "v3"]].copy()
    tabla_x_out.columns = ["Story", "Column", "OutputCase", "V3"]
    tabla_y_out = df_y[["story", col_elem, "outputcase", "v2"]].copy()
    tabla_y_out.columns = ["Story", "Column", "OutputCase", "V2"]
    tabla_clasif = _tabla_clasificacion_e030(pct_muros_x, pct_muros_y, sistema_x, sistema_y)
    return {
        "porcentaje_muros_x": pct_muros_x,
        "porcentaje_muros_y": pct_muros_y,
        "pct_porticos_x": pct_columnas_x,
        "pct_porticos_y": pct_columnas_y,
        "sistema_x": sistema_x,
        "sistema_y": sistema_y,
        "tabla_x": tabla_x_out,
        "tabla_y": tabla_y_out,
        "tabla_clasificacion": tabla_clasif,
        "sum_v3": float(sum_v3),
        "sum_v2": float(sum_v2),
        "cortante_basal_x": abs_basal_x,
        "cortante_basal_y": abs_basal_y,
        "cortante_columnas_x": abs_col_x,
        "cortante_columnas_y": abs_col_y,
        "cortante_muros_x": cortante_muros_x,
        "cortante_muros_y": cortante_muros_y,
    }


def _clasificar_porcentaje(pct_muros: float) -> str:
    if pct_muros < 20:
        return "portico"
    if pct_muros < 70:
        return "dual"
    return "muros_estructurales"


def _tabla_clasificacion_e030(
    pct_muros_x: float,
    pct_muros_y: float,
    sistema_x: str,
    sistema_y: str,
) -> list[dict]:
    """Tabla E.030: Sistema | % Cortante Muros | % Cortante Pórticos | Aplica X | Aplica Y."""
    filas = [
        {"Sistema": "Pórtico", "% Cortante Muros": "< 20%", "% Cortante Pórticos": "≥ 80%",
         "Aplica X": sistema_x == "portico", "Aplica Y": sistema_y == "portico"},
        {"Sistema": "Dual", "% Cortante Muros": "> 20% y < 70%", "% Cortante Pórticos": "Complementario",
         "Aplica X": sistema_x == "dual", "Aplica Y": sistema_y == "dual"},
        {"Sistema": "Muros estructurales", "% Cortante Muros": "≥ 70%", "% Cortante Pórticos": "≤ 30%",
         "Aplica X": sistema_x == "muros_estructurales", "Aplica Y": sistema_y == "muros_estructurales"},
    ]
    return filas


def distorsion_admisible_etabs(
    r: float,
    material: str,
    log: bool = True,
) -> Optional[dict[str, Any]]:
    """
    Story Drifts: SPX/Direction=X -> DriftX; SPY/Direction=Y -> DriftY.
    Usa R = R0*Ia*Ip. Drift ponderado = 0.75 * R * drift.
    Verifica que cada drift * (0.75*R) <= distorsión admisible del material.
    """
    df = get_table(
        NOMBRE_TABLA_STORY_DRIFTS,
        log=log,
        alternate_names=["Story Drift", "Drifts"],
    )
    if df is None or df.empty:
        return None
    df = _normalizar_columnas(df)
    drift_max_material = obtener_distorsion_maxima(material)
    resultado = {"drift_admisible": drift_max_material, "material": material, "r": r}
    df_x = df[
        (df["outputcase"].astype(str).str.upper() == "SPX")
        & (df["direction"].astype(str).str.upper() == "X")
    ].copy()
    df_y = df[
        (df["outputcase"].astype(str).str.upper() == "SPY")
        & (df["direction"].astype(str).str.upper() == "Y")
    ].copy()
    col_drift_x = "driftx" if "driftx" in df_x.columns else ("drift" if "drift" in df_x.columns else None)
    if col_drift_x and not df_x.empty:
        df_x[col_drift_x] = pd.to_numeric(df_x[col_drift_x], errors="coerce")
        df_x["drift_ponderado"] = df_x[col_drift_x] * 0.75 * r
        df_x["cumple"] = df_x["drift_ponderado"] <= drift_max_material
        tabla_x_display = df_x[["story", "outputcase", "direction", col_drift_x]].copy()
        tabla_x_display.columns = ["Story", "OutputCase", "Direction", "DriftX"]
        resultado["tabla_x"] = tabla_x_display
        verif_x = df_x[["story", "drift_ponderado"]].copy()
        verif_x["Distorsión_Admisible"] = drift_max_material
        verif_x["Cumple"] = df_x["cumple"]
        verif_x.columns = [
            "Story",
            "Drift_ponderado\n(0.75·R·Drift)",
            "Distorsión\nAdmisible",
            "Cumple",
        ]
        resultado["tabla_verificacion_x"] = verif_x
        resultado["cumple_x"] = bool(df_x["cumple"].all())
    else:
        resultado["tabla_x"] = None
        resultado["tabla_verificacion_x"] = None
        resultado["cumple_x"] = None
    col_drift_y = "drifty" if "drifty" in df_y.columns else ("drift" if "drift" in df_y.columns else None)
    if col_drift_y and not df_y.empty:
        df_y[col_drift_y] = pd.to_numeric(df_y[col_drift_y], errors="coerce")
        df_y["drift_ponderado"] = df_y[col_drift_y] * 0.75 * r
        df_y["cumple"] = df_y["drift_ponderado"] <= drift_max_material
        tabla_y_display = df_y[["story", "outputcase", "direction", col_drift_y]].copy()
        tabla_y_display.columns = ["Story", "OutputCase", "Direction", "DriftY"]
        resultado["tabla_y"] = tabla_y_display
        verif_y = df_y[["story", "drift_ponderado"]].copy()
        verif_y["Distorsión_Admisible"] = drift_max_material
        verif_y["Cumple"] = df_y["cumple"]
        verif_y.columns = [
            "Story",
            "Drift_ponderado\n(0.75·R·Drift)",
            "Distorsión\nAdmisible",
            "Cumple",
        ]
        resultado["tabla_verificacion_y"] = verif_y
        resultado["cumple_y"] = bool(df_y["cumple"].all())
    else:
        resultado["tabla_y"] = None
        resultado["tabla_verificacion_y"] = None
        resultado["cumple_y"] = None
    resultado["tabla_material"] = _tabla_distorsion_material_e030(material, drift_max_material)
    return resultado


def _tabla_distorsion_material_e030(material_usado: str, valor_usado: float) -> list[dict]:
    """Tabla E.030: Material Predominante | Distorsión Máxima Admisible (Δ/h) | En uso."""
    nombres = {
        "concreto_armado": "Concreto Armado",
        "acero": "Acero",
        "albañileria": "Albañilería",
        "madera": "Madera",
        "concreto_ductilidad_limitada": "Concreto Armado con Muros de Ductilidad Limitada",
    }
    filas = []
    for clave, valor in DISTORSION_MAXIMA.items():
        filas.append({
            "Material": nombres.get(clave, clave),
            "Distorsión Máxima Admisible (Δ/h)": valor,
            "En uso": "Sí" if clave == material_usado else "",
        })
    return filas


def separacion_edificios(
    altura_nivel_h: float,
    desplazamiento_edif_a: float = 0.0,
    desplazamiento_edif_b: float = 0.0,
) -> dict[str, Any]:
    """
    Paso 14 E.030 – Separación de edificios:
    - s = 0.006*h >= 0.03 (m)
    - s >= 2/3 de la suma de los desplazamientos máximos de los edificios adyacentes (Δa + Δb)
    - El mayor de todos estos valores será el valor de s.
    Retorna dict con s_norma, s_adyacentes, s_final (m) y tabla para output.
    """
    s_norma = max(0.006 * altura_nivel_h, 0.03)
    suma_despl = desplazamiento_edif_a + desplazamiento_edif_b
    s_adyacentes = (2.0 / 3.0) * suma_despl
    s_final = max(s_norma, s_adyacentes)
    return {
        "s_norma": s_norma,
        "s_adyacentes": s_adyacentes,
        "s_final": s_final,
        "h": altura_nivel_h,
        "despl_a": desplazamiento_edif_a,
        "despl_b": desplazamiento_edif_b,
        "tabla": [
            {"Criterio": "s = 0.006·h ≥ 0.03", "Valor s (m)": round(s_norma, 4)},
            {"Criterio": "s ≥ (2/3)·(Δa + Δb) adyacentes", "Valor s (m)": round(s_adyacentes, 4)},
            {"Criterio": "Separación mínima s (el mayor de todos)", "Valor s (m)": round(s_final, 4)},
        ],
    }
