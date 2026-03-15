"""Handlers CLI: diseño de columnas de concreto armado E.060.

En columnas solo se trabaja con esfuerzos en Station 0 (los demas se ignoran).
 DATOS:
  columna props          - Agregar/editar propiedades de columna
  columna props-list     - Listar propiedades
  columna esfuerzos      - Agregar esfuerzo de elemento
  columna esfuerzos-list - Listar esfuerzos (solo Station 0)
  columna story-forces   - Agregar story forces
  columna drifts         - Agregar story drifts
  columna alturas        - Agregar alturas de entrepiso
  columna factor-r       - Configurar factor R
  columna diagrama       - Agregar diagrama de interacción (CSV)
  columna asignar        - Asignar diagramas a columnas
 ANÁLISIS:
  columna q              - Paso 1: Índice de estabilidad Q
  columna esbeltez       - Paso 2: Momentos extremos M1/M2
  columna segundo-orden  - Paso 3: Evaluar efectos de segundo orden
  columna cm             - Paso 4: Factor Cm
  columna delta          - Paso 5: Factor de amplificación delta
  columna esfuerzos-fin  - Paso 6: Esfuerzos finales amplificados
  columna mn             - Paso 7: Momentos nominales Mn2/Mn3
  columna estados        - Paso 8: Estados sísmicos combinados
  columna verificacion   - Paso 9: Verificación P-M
  columna resumen        - Resumen de verificación P-M
"""

from __future__ import annotations

import csv
import math
from pathlib import Path

# Ec según E.060: Ec = 15000 * sqrt(f'c) en kg/cm²
def _ec_from_fc(fc: float) -> float:
    if fc <= 0:
        return 0.0
    return 15000.0 * math.sqrt(fc)
from typing import Optional

try:
    import pandas as pd
except ImportError:
    pd = None

from axis.core.exceptions import NoActiveProject, InvalidInput
from axis.core.project import get_active_project_path
from axis.core.database import (
    read_csv,
    write_csv,
    read_results_csv,
    write_results_csv,
    read_json,
    write_json,
    ELEMENT_FIELDNAMES,
)
from axis.cli.tables import format_table
from axis.cli.handlers import get_base_path
from axis.data.etabs_table_reader import get_table, clear_table_cache


# ═══════════════════════════════════════════════════════════════════════
# Utilidades
# ═══════════════════════════════════════════════════════════════════════

def _project() -> Path:
    p = get_active_project_path(get_base_path())
    if not p:
        raise NoActiveProject("No hay proyecto activo. Use 'cas use <proyecto>'.")
    return p


def _col_results_dir(pp: Path) -> Path:
    d = pp / "results" / "columnas"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _to_f(val, default=None):
    if val is None or str(val).strip() in ("", "None"):
        return default
    return float(str(val).replace(",", "."))


def _is_station_0(station) -> bool:
    """True si Station es 0 (solo trabajamos con Station 0 en columnas)."""
    if station is None:
        return False
    s = str(station).strip()
    if s == "0":
        return True
    try:
        return float(s) == 0.0
    except ValueError:
        return False


def _esfuerzos_station_0(esfuerzos: list[dict]) -> list[dict]:
    """Filtra esfuerzos dejando solo los que tienen Station 0."""
    return [r for r in esfuerzos if _is_station_0(r.get("Station"))]


# ═══════════════════════════════════════════════════════════════════════
# DATOS: Propiedades de columnas
# ═══════════════════════════════════════════════════════════════════════

def _story_from_esfuerzos(pp: Path, unique_name: str) -> str:
    """Obtiene Story del primer registro en col_esfuerzos (Station 0) para ese Unique_Name."""
    esfuerzos = _esfuerzos_station_0(read_csv(pp, "col_esfuerzos"))
    for r in esfuerzos:
        if str(r.get("Unique_Name", "")).strip() == str(unique_name).strip():
            return str(r.get("Story", "")).strip()
    return ""


def _is_numeric(s: str) -> bool:
    try:
        float(s)
        return True
    except ValueError:
        return False


def _normalize_col_props_rows(rows: list[dict], fieldnames: list[str]) -> None:
    """Migra columna antigua 'I' a Ix/Iy y deja solo claves en fieldnames (in-place)."""
    for r in rows:
        if "I" in r:
            try:
                i_val = float(r["I"])
            except (TypeError, ValueError):
                i_val = 0
            if not str(r.get("Ix") or "").strip():
                r["Ix"] = i_val
            if not str(r.get("Iy") or "").strip():
                r["Iy"] = i_val
            del r["I"]
        for k in list(r.keys()):
            if k not in fieldnames:
                del r[k]


def handle_columna_props(args: list[str]) -> str:
    """cas columna props <Unique_Name> <k> <lu> <Ix> <Iy> <Ag> <Bd> [fc] [fy]
    Ec se calcula segun E.060: Ec = 15000*sqrt(fc). Default fc=210 kg/cm2.
    Story desde esfuerzos (etabs-import). Forma antigua: <Story> <Unique_Name> ...
    Si solo se pasa una inercia (6 numeros tras UN), se usa Ix=Iy.
    """
    pp = _project()
    if len(args) < 6:
        raise InvalidInput(
            "Uso: cas columna props <Unique_Name> <k> <lu> <Ix> <Iy> <Ag> <Bd> [fc] [fy]\n"
            "  Ec = 15000*sqrt(fc) (E.060). fc por defecto 210 kg/cm2.\n"
            "  k, lu: cm; Ix/Iy: cm4; Ag: cm2; Bd: adimensional.\n"
            "  Una sola inercia: <UN> <k> <lu> <I> <Ag> <Bd> [fc] [fy].")
    try:
        # Forma con Story explícito: Story, UN, k, lu, ...
        if len(args) >= 8 and not _is_numeric(args[1]) and _is_numeric(args[2]):
            story = args[0]
            un = args[1]
            k = float(args[2])
            lu = float(args[3])
            if len(args) >= 10:
                # Story, UN, k, lu, Ix, Iy, Ag, Bd, fc, [fy]
                Ix = float(args[4])
                Iy = float(args[5])
                Ag = float(args[6])
                Bd = float(args[7])
                fc = float(args[8]) if len(args) > 8 else 210.0
                fy = float(args[9]) if len(args) > 9 else 4200.0
            elif len(args) >= 9:
                # Story, UN, k, lu, Ix, Iy, Ag, Bd, fc
                Ix = float(args[4])
                Iy = float(args[5])
                Ag = float(args[6])
                Bd = float(args[7])
                fc = float(args[8])
                fy = float(args[9]) if len(args) > 9 else 4200.0
            elif len(args) == 8:
                # Story, UN, k, lu, Ix, Iy, Ag, Bd (fc=210)
                Ix = float(args[4])
                Iy = float(args[5])
                Ag = float(args[6])
                Bd = float(args[7])
                fc = 210.0
                fy = 4200.0
            else:
                # 7 args: Story, UN, k, lu, I, Ag, Bd
                I_val = float(args[4])
                Ix = I_val
                Iy = I_val
                Ag = float(args[5])
                Bd = float(args[6])
                fc = 210.0
                fy = 4200.0
            Ec = _ec_from_fc(fc)
        else:
            # Forma sin Story: UN, k, lu, ...
            un = args[0]
            story = _story_from_esfuerzos(pp, un)
            if len(args) >= 9:
                # UN, k, lu, Ix, Iy, Ag, Bd, fc, [fy]
                k = float(args[1])
                lu = float(args[2])
                Ix = float(args[3])
                Iy = float(args[4])
                Ag = float(args[5])
                Bd = float(args[6])
                fc = float(args[7]) if len(args) > 7 else 210.0
                fy = float(args[8]) if len(args) > 8 else 4200.0
            elif len(args) >= 8:
                # UN, k, lu, Ix, Iy, Ag, Bd, [fc]
                k = float(args[1])
                lu = float(args[2])
                Ix = float(args[3])
                Iy = float(args[4])
                Ag = float(args[5])
                Bd = float(args[6])
                fc = float(args[7]) if len(args) > 7 else 210.0
                fy = float(args[8]) if len(args) > 8 else 4200.0
            elif len(args) >= 7:
                # UN, k, lu, I, Ag, Bd, fc (una inercia)
                k = float(args[1])
                lu = float(args[2])
                I_val = float(args[3])
                Ix = I_val
                Iy = I_val
                Ag = float(args[4])
                Bd = float(args[5])
                fc = float(args[6]) if len(args) > 6 else 210.0
                fy = float(args[7]) if len(args) > 7 else 4200.0
            else:
                # 6 args: UN, k, lu, I, Ag, Bd
                k = float(args[1])
                lu = float(args[2])
                I_val = float(args[3])
                Ix = I_val
                Iy = I_val
                Ag = float(args[4])
                Bd = float(args[5])
                fc = 210.0
                fy = 4200.0
            Ec = _ec_from_fc(fc)
    except ValueError:
        raise InvalidInput("Parametros numericos invalidos.")

    row = {
        "Story": story,
        "Unique_Name": un,
        "k": k,
        "lu": lu,
        "Ix": Ix,
        "Iy": Iy,
        "Ag": Ag,
        "Ec": Ec,
        "Bd": Bd,
        "fc": fc,
        "fy": fy,
    }

    existing = read_csv(pp, "col_props")
    fieldnames = ELEMENT_FIELDNAMES["col_props"]
    _normalize_col_props_rows(existing, fieldnames)
    idx = next((i for i, r in enumerate(existing)
                if r.get("Unique_Name") == un and r.get("Story") == story), None)
    row_clean = {k: row.get(k) for k in fieldnames}
    if idx is not None:
        existing[idx] = row_clean
        msg = f"Propiedades de '{un}' (Story={story or '(sin story)'}) actualizadas."
    else:
        existing.append(row_clean)
        msg = f"Propiedades de '{un}' (Story={story or '(sin story)'}) agregadas."
    if not story:
        msg += " (Story no hallado en esfuerzos; importe con etabs-import o agregue esfuerzos primero.)"

    write_csv(pp, existing, "col_props", fieldnames)

    for i, r in enumerate(existing):
        r["N"] = str(i + 1)
    cols = ["N", "Story", "Unique_Name", "k", "lu", "Ix", "Iy", "Ag", "Ec", "Bd"]
    return msg + "\n\n" + format_table(existing, columns=cols)


def handle_columna_props_remove(args: list[str]) -> str:
    """cas columna props-remove <Unique_Name> -> Borra las propiedades de esa columna."""
    pp = _project()
    if not args:
        raise InvalidInput("Uso: cas columna props-remove <Unique_Name>")
    un = args[0].strip()
    existing = read_csv(pp, "col_props")
    fieldnames = ELEMENT_FIELDNAMES["col_props"]
    _normalize_col_props_rows(existing, fieldnames)
    new_rows = [r for r in existing if str(r.get("Unique_Name", "")).strip() != un]
    if len(new_rows) == len(existing):
        raise InvalidInput(f"No hay propiedades para la columna '{un}'.")
    write_csv(pp, new_rows, "col_props", fieldnames)
    return f"Propiedades de la columna '{un}' eliminadas."


def handle_columna_props_list(args: list[str]) -> str:
    """cas columna props-list -> Listar propiedades."""
    pp = _project()
    rows = read_csv(pp, "col_props")
    if not rows:
        return "No hay propiedades de columnas. Use 'cas columna props ...'."
    for i, r in enumerate(rows):
        r["N"] = str(i + 1)
    cols = ["N", "Story", "Unique_Name", "k", "lu", "Ix", "Iy", "Ag", "Ec", "Bd", "fc", "fy"]
    return "Propiedades de columnas\n\n" + format_table(rows, columns=cols)


# ═══════════════════════════════════════════════════════════════════════
# DATOS: Esfuerzos de elementos
# ═══════════════════════════════════════════════════════════════════════

def handle_columna_esfuerzos(args: list[str]) -> str:
    """cas columna esfuerzos <Story> <Unique_Name> <Station> <Output_Case> <Step_Type> <P> <M2> <M3>"""
    pp = _project()
    if len(args) < 8:
        raise InvalidInput(
            "Uso: cas columna esfuerzos <Story> <Unique_Name> <Station> "
            "<Output_Case> <Step_Type> <P> <M2> <M3>\n"
            "  P en Tn, M2/M3 en Tn-m. Step_Type: Max/Min o '-' si no aplica.")
    try:
        story = args[0]; un = args[1]; station = args[2]
        oc = args[3]; st = args[4] if args[4] != "-" else ""
        P = float(args[5]); M2 = float(args[6]); M3 = float(args[7])
    except ValueError:
        raise InvalidInput("P, M2 y M3 deben ser numericos.")

    row = {
        "Story": story, "Unique_Name": un, "Station": station,
        "Output_Case": oc, "Step_Type": st,
        "P": P, "M2": M2, "M3": M3,
    }

    existing = read_csv(pp, "col_esfuerzos")
    existing.append(row)

    write_csv(pp, existing, "col_esfuerzos", ELEMENT_FIELDNAMES["col_esfuerzos"])
    return f"Esfuerzo agregado ({un}, {oc}). Total: {len(existing)} registros."


def handle_columna_esfuerzos_list(args: list[str]) -> str:
    """cas columna esfuerzos-list [Unique_Name] -> Listar esfuerzos (solo Station 0)."""
    pp = _project()
    rows = _esfuerzos_station_0(read_csv(pp, "col_esfuerzos"))
    if not rows:
        return "No hay esfuerzos de columnas con Station 0."
    nombre = args[0] if args else None
    if nombre:
        rows = [r for r in rows if r.get("Unique_Name") == nombre]
        if not rows:
            raise InvalidInput(f"Sin esfuerzos para '{nombre}'.")
    for i, r in enumerate(rows):
        r["N"] = str(i + 1)
    cols = ["N", "Story", "Unique_Name", "Station", "Output_Case", "Step_Type", "P", "M2", "M3"]
    return "Esfuerzos de columnas\n\n" + format_table(rows, columns=cols)


# ═══════════════════════════════════════════════════════════════════════
# DATOS: Story Forces
# ═══════════════════════════════════════════════════════════════════════

def handle_columna_story_forces(args: list[str]) -> str:
    """cas columna story-forces <Story> <Output_Case> <P> <VX> <VY>"""
    pp = _project()
    if len(args) < 5:
        raise InvalidInput(
            "Uso: cas columna story-forces <Story> <Output_Case> <P> <VX> <VY>\n"
            "  P, VX, VY en Tn.")
    try:
        story = args[0]; oc = args[1]
        P = float(args[2]); VX = float(args[3]); VY = float(args[4])
    except ValueError:
        raise InvalidInput("P, VX y VY deben ser numericos.")

    row = {"Story": story, "Output_Case": oc, "P": P, "VX": VX, "VY": VY}
    existing = read_csv(pp, "col_story_forces")
    existing.append(row)

    write_csv(pp, existing, "col_story_forces", ELEMENT_FIELDNAMES["col_story_forces"])

    for i, r in enumerate(existing):
        r["N"] = str(i + 1)
    cols = ["N", "Story", "Output_Case", "P", "VX", "VY"]
    return f"Story force agregada. Total: {len(existing)}\n\n" + format_table(existing, columns=cols)


# ═══════════════════════════════════════════════════════════════════════
# DATOS: Story Drifts
# ═══════════════════════════════════════════════════════════════════════

def handle_columna_drifts(args: list[str]) -> str:
    """cas columna drifts <Story> <Output_Case> <Drift>"""
    pp = _project()
    if len(args) < 3:
        raise InvalidInput("Uso: cas columna drifts <Story> <Output_Case> <Drift>")
    try:
        story = args[0]; oc = args[1]; drift = float(args[2])
    except ValueError:
        raise InvalidInput("Drift debe ser numerico.")

    row = {"Story": story, "Output_Case": oc, "Drift": drift}
    existing = read_csv(pp, "col_drifts")
    existing.append(row)

    write_csv(pp, existing, "col_drifts", ELEMENT_FIELDNAMES["col_drifts"])

    for i, r in enumerate(existing):
        r["N"] = str(i + 1)
    return f"Drift agregado. Total: {len(existing)}\n\n" + format_table(
        existing, columns=["N", "Story", "Output_Case", "Drift"])


# ═══════════════════════════════════════════════════════════════════════
# DATOS: Alturas de entrepiso
# ═══════════════════════════════════════════════════════════════════════

def handle_columna_alturas(args: list[str]) -> str:
    """cas columna alturas <Story> <Height>"""
    pp = _project()
    if len(args) < 2:
        raise InvalidInput("Uso: cas columna alturas <Story> <Height(m)>")
    try:
        story = args[0]; height = float(args[1])
    except ValueError:
        raise InvalidInput("Height debe ser numerico.")

    row = {"Story": story, "Height": height}
    existing = read_csv(pp, "col_alturas")
    idx = next((i for i, r in enumerate(existing) if r.get("Story") == story), None)
    if idx is not None:
        existing[idx] = row
        msg = f"Altura de '{story}' actualizada."
    else:
        existing.append(row)
        msg = f"Altura de '{story}' agregada."

    write_csv(pp, existing, "col_alturas", ELEMENT_FIELDNAMES["col_alturas"])

    for i, r in enumerate(existing):
        r["N"] = str(i + 1)
    return msg + "\n\n" + format_table(existing, columns=["N", "Story", "Height"])


# ═══════════════════════════════════════════════════════════════════════
# DATOS: Factor R
# ═══════════════════════════════════════════════════════════════════════

def handle_columna_factor_r(args: list[str]) -> str:
    """cas columna factor-r <R_X> <R_Y>"""
    pp = _project()
    if len(args) < 2:
        raise InvalidInput("Uso: cas columna factor-r <R_X> <R_Y>")
    try:
        r_x = float(args[0]); r_y = float(args[1])
    except ValueError:
        raise InvalidInput("R_X y R_Y deben ser numericos.")

    row = {"R_X": r_x, "R_Y": r_y}
    write_csv(pp, [row], "col_factor_r", ELEMENT_FIELDNAMES["col_factor_r"])
    return f"Factor R configurado: R_X={r_x}, R_Y={r_y}"


# ═══════════════════════════════════════════════════════════════════════
# IMPORTACIÓN DESDE ETABS
# ═══════════════════════════════════════════════════════════════════════

def _find_col(df_cols: list, preferred: list[str], keywords: list[str] | None = None) -> str | None:
    """Busca columna por nombre preferido o por palabras clave."""
    col_lower = {str(c).strip().lower(): c for c in df_cols}
    for p in preferred:
        if p in df_cols:
            return p
        if p.lower() in col_lower:
            return col_lower[p.lower()]
    if keywords:
        for c, orig in col_lower.items():
            if any(k in c for k in keywords):
                return orig
    return None


def _etabs_column_forces() -> tuple[list[dict], str]:
    """
    Lee Element Forces - Columns desde ETABS.
    Filtra por combinaciones de diseño. Retorna list[dict] con keys
    Story, Unique_Name, Station, Output_Case, Step_Type, P, M2, M3.
    """
    if pd is None:
        raise InvalidInput("Se requiere pandas para importar desde ETABS.")
    df = get_table(
        "Element Forces - Columns",
        log=True,
        use_cache=False,
        alternate_names=["Element Forces-Column", "Frame Forces"],
    )
    if df is None or df.empty:
        raise InvalidInput("No se pudo leer 'Element Forces - Columns' desde ETABS.")
    df = df.copy()
    cols = list(df.columns)
    c_story = _find_col(cols, ["Story", "StoryLabel"], ["story"])
    c_un = _find_col(cols, ["Unique Name", "UniqueName", "Name"], ["unique", "name"])
    c_station = _find_col(cols, ["Station", "Loc"], ["station", "loc"])
    c_case = _find_col(cols, ["Output Case", "OutputCase"], ["output", "case"])
    c_step = _find_col(cols, ["Step Type", "StepType"], ["step"])
    c_p = _find_col(cols, ["P", "P1"], ["axial", "p1"])
    c_m2 = _find_col(cols, ["M2", "M22"], ["m2", "moment"])
    c_m3 = _find_col(cols, ["M3", "M33"], ["m3", "moment"])
    if not c_un or not c_p:
        raise InvalidInput("La tabla de columnas no tiene Unique Name o P.")
    if not c_m2:
        c_m2 = c_m3
    if not c_m3:
        c_m3 = c_m2
    if not c_story:
        df["Story"] = ""
        c_story = "Story"
    combos_norm = [
        "1.4CM+1.7CV", "1.4CM +1.7CV",
        "1.25(CM+CV)+SX", "1.25(CM+CV)+SY",
        "0.9CM+SX", "0.9CM+SY",
    ]
    if c_case:
        df["_cn"] = df[c_case].astype(str).str.strip().str.replace(" ", "").str.upper()
        m_14 = df["_cn"].str.contains("1\\.4", regex=True, na=False) & df["_cn"].str.contains("CM", na=False) & df["_cn"].str.contains("CV", na=False)
        m_125 = df["_cn"].str.contains("1\\.25", regex=True, na=False) & (df["_cn"].str.contains("SX", na=False) | df["_cn"].str.contains("SY", na=False))
        m_09 = df["_cn"].str.contains("0\\.9", regex=True, na=False) & (df["_cn"].str.contains("SX", na=False) | df["_cn"].str.contains("SY", na=False))
        df = df[m_14 | m_125 | m_09].copy()
        df = df.drop(columns=["_cn"], errors="ignore")
    rename = {}
    if c_story:
        rename[c_story] = "Story"
    if c_un:
        rename[c_un] = "Unique_Name"
    if c_station:
        rename[c_station] = "Station"
    if c_case:
        rename[c_case] = "Output_Case"
    if c_step:
        rename[c_step] = "Step_Type"
    if c_p:
        rename[c_p] = "P"
    if c_m2:
        rename[c_m2] = "M2"
    if c_m3:
        rename[c_m3] = "M3"
    df = df.rename(columns=rename)
    for col in ["P", "M2", "M3"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    std = ["Story", "Unique_Name", "Station", "Output_Case", "Step_Type", "P", "M2", "M3"]
    for c in std:
        if c not in df.columns:
            df[c] = "" if c in ("Output_Case", "Step_Type") else 0.0
    out = df[[c for c in std if c in df.columns]].copy()
    return out.to_dict("records"), "Element Forces - Columns"


def _etabs_story_forces() -> list[dict]:
    """Lee Story Forces desde ETABS (Location = Bottom, combos de diseño)."""
    if pd is None:
        raise InvalidInput("Se requiere pandas.")
    df = get_table("Story Forces", log=True, use_cache=False)
    if df is None or df.empty:
        raise InvalidInput("No se pudo leer 'Story Forces' desde ETABS.")
    df = df.copy()
    cols = list(df.columns)
    c_story = _find_col(cols, ["Story", "StoryLabel"], ["story"])
    c_case = _find_col(cols, ["Output Case", "OutputCase"], ["output", "case"])
    c_loc = _find_col(cols, ["Location", "Loc"], ["location", "loc"])
    c_p = _find_col(cols, ["P", "P1"], ["axial"])
    c_vx = _find_col(cols, ["VX", "V2", "VX"], ["vx", "v2", "shear"])
    c_vy = _find_col(cols, ["VY", "V3", "VY"], ["vy", "v3", "shear"])
    if not c_story or not c_p:
        raise InvalidInput("Story Forces no tiene Story o P.")
    if c_loc:
        df = df[df[c_loc].astype(str).str.strip().str.lower() == "bottom"].copy()
    if c_case:
        df["_cn"] = df[c_case].astype(str).str.strip().str.replace(" ", "").str.upper()
        mask = df["_cn"].str.contains("SX|SY|1\\.4.*CM.*CV", regex=True, na=False)
        df = df[mask].copy()
        df = df.drop(columns=["_cn"], errors="ignore")
    rename = {c_story: "Story", c_case: "Output_Case", c_p: "P"}
    if c_vx:
        rename[c_vx] = "VX"
    if c_vy:
        rename[c_vy] = "VY"
    df = df.rename(columns=rename)
    for c in ["P", "VX", "VY"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
        else:
            df[c] = 0.0
    return df[["Story", "Output_Case", "P", "VX", "VY"]].to_dict("records")


def _etabs_story_drifts() -> list[dict]:
    """Lee Story Drifts desde ETABS: solo SPX con Direction X y SPY con Direction Y.
    Por cada (Story, Output_Case) se guarda un solo valor: el max(Drift).
    """
    if pd is None:
        raise InvalidInput("Se requiere pandas.")
    df = get_table("Story Drifts", log=True, use_cache=False)
    if df is None or df.empty:
        raise InvalidInput("No se pudo leer 'Story Drifts' desde ETABS.")
    df = df.copy()
    cols = list(df.columns)
    c_story = _find_col(cols, ["Story", "StoryLabel"], ["story"])
    c_case = _find_col(cols, ["Output Case", "OutputCase"], ["output", "case"])
    c_drift = _find_col(cols, ["Drift", "Drift1"], ["drift"])
    c_dir = _find_col(cols, ["Direction", "Dir"], ["direction", "dir"])
    if not c_story or not c_case or not c_drift:
        raise InvalidInput("Story Drifts no tiene Story, Output Case o Drift.")
    df["_oc"] = df[c_case].astype(str).str.strip().str.upper()
    df = df[df["_oc"].isin(["SPX", "SPY"])].copy()
    if c_dir:
        df["_dir"] = df[c_dir].astype(str).str.strip().str.upper()
        df = df[((df["_oc"] == "SPX") & (df["_dir"] == "X")) | ((df["_oc"] == "SPY") & (df["_dir"] == "Y"))].copy()
        df = df.drop(columns=["_dir"], errors="ignore")
    df = df.drop(columns=["_oc"], errors="ignore")
    df = df.rename(columns={c_story: "Story", c_case: "Output_Case", c_drift: "Drift"})
    df["Drift"] = pd.to_numeric(df["Drift"], errors="coerce")
    df = df.groupby(["Story", "Output_Case"], as_index=False).agg({"Drift": "max"}).reset_index(drop=True)
    return df[["Story", "Output_Case", "Drift"]].to_dict("records")


def _etabs_story_definitions() -> list[dict]:
    """Lee Story Definitions desde ETABS (Story, Height en m)."""
    if pd is None:
        raise InvalidInput("Se requiere pandas.")
    df = get_table(
        "Story Definitions",
        log=True,
        use_cache=False,
        alternate_names=["Story Definition"],
    )
    if df is None or df.empty:
        raise InvalidInput("No se pudo leer 'Story Definitions' desde ETABS.")
    df = df.copy()
    df.columns = [str(c).strip().lower() for c in df.columns]
    if "story" not in df.columns or "height" not in df.columns:
        raise InvalidInput("Story Definitions sin columnas Story/Height.")
    df = df[df["story"].astype(str).str.strip().str.lower() != "base"].copy()
    df["Story"] = df["story"].astype(str).str.strip()
    df["Height"] = pd.to_numeric(df["height"], errors="coerce")
    return df[["Story", "Height"]].to_dict("records")


def handle_columna_etabs_import(args: list[str]) -> str:
    """cas columna etabs-import [R_X] [R_Y]

    Importa desde ETABS:
    - Element Forces - Columns -> esfuerzos de columnas
    - Story Forces (Location=Bottom) -> story forces
    - Story Drifts (SPX, SPY) -> drifts
    - Story Definitions -> alturas de entrepiso
    - Factor R (por defecto 8, 8)

    Requiere ETABS abierto con modelo cargado y análisis ejecutado.
    """
    pp = _project()
    if pd is None:
        raise InvalidInput("Se requiere pandas para importar desde ETABS: pip install pandas")
    clear_table_cache()
    r_x = 8.0
    r_y = 8.0
    if len(args) >= 2:
        try:
            r_x = float(args[0])
            r_y = float(args[1])
        except ValueError:
            pass
    lines: list[str] = []
    n_esf = 0
    n_sf = 0
    n_drift = 0
    n_alt = 0
    try:
        esfuerzos, _ = _etabs_column_forces()
        # Guardar todas las stations para Paso 2 (esbeltez) y Cm; Paso 6 usa solo Station 0
        n_esf = len(esfuerzos)
        write_csv(pp, esfuerzos, "col_esfuerzos", ELEMENT_FIELDNAMES["col_esfuerzos"])
        lines.append(f"  Esfuerzos de columnas: {n_esf} registros")
    except Exception as e:
        lines.append(f"  Esfuerzos de columnas: Error - {e}")
    try:
        sf = _etabs_story_forces()
        n_sf = len(sf)
        write_csv(pp, sf, "col_story_forces", ELEMENT_FIELDNAMES["col_story_forces"])
        lines.append(f"  Story Forces: {n_sf} registros")
    except Exception as e:
        lines.append(f"  Story Forces: Error - {e}")
    try:
        dr = _etabs_story_drifts()
        n_drift = len(dr)
        write_csv(pp, dr, "col_drifts", ELEMENT_FIELDNAMES["col_drifts"])
        lines.append(f"  Story Drifts: {n_drift} registros")
    except Exception as e:
        lines.append(f"  Story Drifts: Error - {e}")
    try:
        alt = _etabs_story_definitions()
        n_alt = len(alt)
        write_csv(pp, alt, "col_alturas", ELEMENT_FIELDNAMES["col_alturas"])
        lines.append(f"  Alturas de entrepiso: {n_alt} pisos")
    except Exception as e:
        lines.append(f"  Alturas: Error - {e}")
    write_csv(pp, [{"R_X": r_x, "R_Y": r_y}], "col_factor_r", ELEMENT_FIELDNAMES["col_factor_r"])
    lines.append(f"  Factor R: R_X={r_x}, R_Y={r_y}")
    header = "Importacion desde ETABS\n\n" + "\n".join(lines)
    header += "\n\nSiguiente: defina propiedades por columna (cas columna props ...)"
    header += "\nLuego ejecute los pasos: columna q, esbeltez, segundo-orden, cm, delta, esfuerzos-fin, etc."
    return header


# ═══════════════════════════════════════════════════════════════════════
# DATOS: Diagramas de interacción
# ═══════════════════════════════════════════════════════════════════════

def handle_columna_asignar(args: list[str]) -> str:
    """cas columna asignar <Unique_Name> <Diagrama_Nominal> [Diagrama_Ultimo]"""
    pp = _project()
    if len(args) < 2:
        raise InvalidInput(
            "Uso: cas columna asignar <Unique_Name> <Diagrama_Nominal> [Diagrama_Ultimo]")
    un = args[0]
    nom = args[1]
    ult = args[2] if len(args) > 2 else nom

    row = {"Unique_Name": un, "Diagrama_Nominal": nom, "Diagrama_Ultimo": ult}
    existing = read_csv(pp, "col_asignaciones")
    idx = next((i for i, r in enumerate(existing) if r.get("Unique_Name") == un), None)
    if idx is not None:
        existing[idx] = row
        msg = f"Asignacion de '{un}' actualizada."
    else:
        existing.append(row)
        msg = f"Asignacion de '{un}' creada."

    write_csv(pp, existing, "col_asignaciones", ELEMENT_FIELDNAMES["col_asignaciones"])

    for i, r in enumerate(existing):
        r["N"] = str(i + 1)
    cols = ["N", "Unique_Name", "Diagrama_Nominal", "Diagrama_Ultimo"]
    return msg + "\n\n" + format_table(existing, columns=cols)


def handle_columna_diagrama(args: list[str]) -> str:
    """cas columna diagrama [nombre_seccion]

    Muestra la superficie de interacción 3D con todos los puntos de esfuerzos finales
    (results/columnas/esfuerzos_finales.csv). Si no se indica nombre_seccion, se usa
    el primer diagrama nominal asignado a alguna columna (o el primero disponible).
    Requiere: pip install matplotlib scipy
    """
    pp = _project()
    esfuerzos_fin = read_results_csv(pp, "columnas/esfuerzos_finales.csv")
    if not esfuerzos_fin:
        raise InvalidInput(
            "Sin esfuerzos finales. Ejecute antes 'cas columna esfuerzos-fin' (o 'cas columna diseno')."
        )
    diagramas = read_json(pp, "diagramas.json") or {}
    nominales = {k.replace("_nominal", ""): v for k, v in diagramas.items() if "_nominal" in k}
    if not nominales:
        raise InvalidInput(
            "No hay diagramas nominales. Use 'cas diagrama add <nombre> nominal <archivo>'."
        )
    if args:
        section_name = args[0].strip()
        if section_name not in nominales:
            raise InvalidInput(
                f"No existe diagrama nominal '{section_name}'. Disponibles: {sorted(nominales.keys())}"
            )
    else:
        asignaciones = read_csv(pp, "col_asignaciones")
        asignados = {str(a.get("Diagrama_Nominal", "")).strip() for a in asignaciones if a.get("Diagrama_Nominal")}
        section_name = next((s for s in nominales if s in asignados), None)
        if section_name is None:
            section_name = sorted(nominales)[0]
    puntos = nominales[section_name]
    if not puntos or not isinstance(puntos, list):
        raise InvalidInput(f"El diagrama '{section_name}' no tiene puntos válidos.")
    puntos_esfuerzo = [
        {"P": float(r.get("P", 0)), "M2": float(r.get("M2", 0)), "M3": float(r.get("M3", 0))}
        for r in esfuerzos_fin
    ]
    from axis.cli.pm_plotter import plot_superficie_interaccion
    try:
        plot_superficie_interaccion(
            puntos,
            titulo="Superficie de Interacción P-M2-M3",
            subtitulo=f"Diagrama {section_name} — {len(puntos_esfuerzo)} esfuerzos finales (Station 0)",
            puntos_esfuerzo=puntos_esfuerzo,
        )
    except RuntimeError as e:
        raise InvalidInput(str(e)) from e
    return (
        f"Gráfico mostrado: superficie '{section_name}' con {len(puntos_esfuerzo)} puntos de esfuerzos finales."
    )


# ═══════════════════════════════════════════════════════════════════════
# PASO 1: Índice de estabilidad Q
# ═══════════════════════════════════════════════════════════════════════

def handle_columna_q(args: list[str]) -> str:
    """cas columna q -> Calcula indice de estabilidad Q por piso."""
    pp = _project()
    forces = read_csv(pp, "col_story_forces")
    drifts = read_csv(pp, "col_drifts")
    heights = read_csv(pp, "col_alturas")

    if not forces:
        raise InvalidInput("Sin story forces. Use 'cas columna story-forces ...'.")
    if not drifts:
        raise InvalidInput("Sin story drifts. Use 'cas columna drifts ...'.")
    if not heights:
        raise InvalidInput("Sin alturas. Use 'cas columna alturas ...'.")

    factor_r = read_csv(pp, "col_factor_r")
    r_x = float(factor_r[0]["R_X"]) if factor_r else 8.0
    r_y = float(factor_r[0]["R_Y"]) if factor_r else 8.0

    from axis.columnas.analysis import compute_q_table
    results = compute_q_table(forces, drifts, heights, r_x, r_y)

    if not results:
        return "No se pudieron calcular valores de Q."

    _col_results_dir(pp)
    write_results_csv(pp, "columnas/q_analysis.csv", results)

    for i, r in enumerate(results):
        r["N"] = str(i + 1)
    cols = ["N", "Story", "Direction", "Pu", "Vus", "Drift_R", "Q", "Classification"]
    return (
        "PASO 1: Indice de Estabilidad Q\n\n"
        + format_table(results, columns=cols)
        + f"\n\nResultados guardados en results/columnas/q_analysis.csv"
    )


# ═══════════════════════════════════════════════════════════════════════
# PASO 2: Momentos extremos (esbeltez)
# ═══════════════════════════════════════════════════════════════════════

def handle_columna_esbeltez(args: list[str]) -> str:
    """cas columna esbeltez -> Calcula M1, M2 y curvatura por columna.
    Usa stations extremas (mín y máx) como Diseño_Columnas; resto del flujo igual.
    Solo se listan columnas que tienen propiedades definidas (col_props).
    """
    pp = _project()
    # Paso 2: todas las stations para hallar M1/M2 en extremos (como Diseño_Columnas)
    esfuerzos = read_csv(pp, "col_esfuerzos")
    alturas = read_csv(pp, "col_alturas")
    props = read_csv(pp, "col_props")

    if not esfuerzos:
        raise InvalidInput("Sin esfuerzos. Use 'cas columna esfuerzos ...'.")
    if not alturas:
        raise InvalidInput("Sin alturas. Use 'cas columna alturas ...'.")
    if not props:
        raise InvalidInput("Sin propiedades de columnas. Use 'cas columna props ...'.")

    props_unique = {str(r.get("Unique_Name", "")).strip() for r in props}

    from axis.columnas.analysis import compute_slenderness
    results = compute_slenderness(esfuerzos, alturas)
    results = [r for r in results if str(r.get("Unique_Name", "")).strip() in props_unique]

    if not results:
        return "No se pudieron calcular momentos extremos para columnas con propiedades."

    _col_results_dir(pp)
    write_results_csv(pp, "columnas/esbeltez.csv", results)

    for i, r in enumerate(results):
        r["N"] = str(i + 1)
    cols = ["N", "Story", "Unique_Name", "M1_X", "M2_X", "M1_Y", "M2_Y",
            "Curvatura_X", "Curvatura_Y"]
    return (
        "PASO 2: Momentos Extremos (Esbeltez)\n\n"
        + format_table(results, columns=cols)
        + "\n\nResultados guardados en results/columnas/esbeltez.csv"
    )


# ═══════════════════════════════════════════════════════════════════════
# PASO 3: Evaluación de segundo orden
# ═══════════════════════════════════════════════════════════════════════

def handle_columna_segundo_orden(args: list[str]) -> str:
    """cas columna segundo-orden -> Evalua si se ignoran efectos de 2do orden."""
    pp = _project()
    esbeltez = read_results_csv(pp, "columnas/esbeltez.csv")
    q_results = read_results_csv(pp, "columnas/q_analysis.csv")
    props = read_csv(pp, "col_props")

    if not esbeltez:
        raise InvalidInput("Sin datos de esbeltez. Ejecute 'cas columna esbeltez' primero.")
    if not props:
        raise InvalidInput("Sin propiedades. Use 'cas columna props ...'.")

    if not q_results:
        q_results = []

    from axis.columnas.analysis import compute_second_order
    results = compute_second_order(esbeltez, props, q_results)

    if not results:
        return "No se pudieron evaluar efectos de segundo orden."

    write_results_csv(pp, "columnas/segundo_orden.csv", results)

    for i, r in enumerate(results):
        r["N"] = str(i + 1)
    cols = ["N", "Story", "Unique_Name", "Direction", "Arriostrado",
            "k", "I", "r", "lu", "M1/M2", "34-12(M1/M2)", "(k*lu)/r", "Ignorar_2do_Orden"]
    return (
        "PASO 3: Efectos de Segundo Orden\n"
        "  Arriostrado: (k*lu)/r <= 34-12*(M1/M2) <= 40\n"
        "  No arriostrado: (k*lu)/r < 22\n\n"
        + format_table(results, columns=cols)
        + "\n\nResultados guardados en results/columnas/segundo_orden.csv"
    )


# ═══════════════════════════════════════════════════════════════════════
# PASO 4: Factor Cm
# ═══════════════════════════════════════════════════════════════════════

def handle_columna_cm(args: list[str]) -> str:
    """cas columna cm -> Calcula factor Cm por columna. Solo columnas con propiedades."""
    pp = _project()
    # Todas las stations para M1/M2 en extremos (como Diseño_Columnas)
    esfuerzos = read_csv(pp, "col_esfuerzos")
    segundo_orden = read_results_csv(pp, "columnas/segundo_orden.csv")
    props = read_csv(pp, "col_props")

    if not esfuerzos:
        raise InvalidInput("Sin esfuerzos.")
    if not segundo_orden:
        raise InvalidInput("Sin datos de segundo orden. Ejecute 'cas columna segundo-orden'.")
    if not props:
        raise InvalidInput("Sin propiedades. Use 'cas columna props ...'.")

    props_unique = {str(r.get("Unique_Name", "")).strip() for r in props}
    from axis.columnas.analysis import compute_cm
    results = compute_cm(esfuerzos, segundo_orden)
    results = [r for r in results if str(r.get("Unique_Name", "")).strip() in props_unique]

    if not results:
        return "No se pudieron calcular factores Cm para columnas con propiedades."

    write_results_csv(pp, "columnas/cm.csv", results)

    for i, r in enumerate(results):
        r["N"] = str(i + 1)
    cols = ["N", "Story", "Unique_Name", "M1_X", "M2_X", "Cm_X", "M1_Y", "M2_Y", "Cm_Y"]
    return (
        "PASO 4: Factor Cm\n"
        "  Cm = 0.6 + 0.4*(M1/M2), limitado [0.4, 1.0]\n\n"
        + format_table(results, columns=cols)
        + "\n\nResultados guardados en results/columnas/cm.csv"
    )


# ═══════════════════════════════════════════════════════════════════════
# PASO 5: Factor delta (amplificación)
# ═══════════════════════════════════════════════════════════════════════

def handle_columna_delta(args: list[str]) -> str:
    """cas columna delta -> Calcula factor de amplificacion delta."""
    pp = _project()
    props = read_csv(pp, "col_props")
    cm_results = read_results_csv(pp, "columnas/cm.csv")
    esfuerzos = _esfuerzos_station_0(read_csv(pp, "col_esfuerzos"))
    segundo_orden = read_results_csv(pp, "columnas/segundo_orden.csv")

    if not props:
        raise InvalidInput("Sin propiedades de columnas.")
    if not cm_results:
        raise InvalidInput("Sin datos de Cm. Ejecute 'cas columna cm'.")
    if not esfuerzos:
        raise InvalidInput("Sin esfuerzos.")
    if not segundo_orden:
        segundo_orden = []

    from axis.columnas.analysis import compute_delta
    results = compute_delta(props, cm_results, esfuerzos, segundo_orden)

    if not results:
        return "No se pudieron calcular factores delta."

    write_results_csv(pp, "columnas/delta.csv", results)

    for i, r in enumerate(results):
        r["N"] = str(i + 1)
    cols = ["N", "Story", "Unique_Name", "Pu",
            "EI_X", "Pc_X", "Cm_X", "Delta_X",
            "EI_Y", "Pc_Y", "Cm_Y", "Delta_Y"]
    return (
        "PASO 5: Factor de Amplificacion Delta\n"
        "  EI = (0.4*Ec*I)/(1+Bd)  [Ix para dir X, Iy para dir Y]\n"
        "  Pc = pi^2*EI/(k*lu)^2\n"
        "  delta = Cm/(1-0.75*Pu/Pc) >= 1.0\n\n"
        + format_table(results, columns=cols)
        + "\n\nResultados guardados en results/columnas/delta.csv"
    )


# ═══════════════════════════════════════════════════════════════════════
# PASO 6: Esfuerzos finales amplificados
# ═══════════════════════════════════════════════════════════════════════

def handle_columna_esfuerzos_finales(args: list[str]) -> str:
    """cas columna esfuerzos-fin -> Amplifica momentos con delta. Solo columnas con propiedades."""
    pp = _project()
    esfuerzos = _esfuerzos_station_0(read_csv(pp, "col_esfuerzos"))
    delta_results = read_results_csv(pp, "columnas/delta.csv")
    props = read_csv(pp, "col_props")

    if not esfuerzos:
        raise InvalidInput("Sin esfuerzos.")
    if not delta_results:
        raise InvalidInput("Sin datos de delta. Ejecute 'cas columna delta'.")
    if not props:
        raise InvalidInput("Sin propiedades. Use 'cas columna props ...'.")

    props_unique = {str(r.get("Unique_Name", "")).strip() for r in props}
    from axis.columnas.analysis import compute_final_forces
    results = compute_final_forces(esfuerzos, delta_results)
    results = [r for r in results if str(r.get("Unique_Name", "")).strip() in props_unique]
    # Solo salida Station 0 (por si en algún flujo entraron más stations)
    results = _esfuerzos_station_0(results)

    if not results:
        return "No se pudieron calcular esfuerzos finales para columnas con propiedades (Station 0)."

    write_results_csv(pp, "columnas/esfuerzos_finales.csv", results)

    for i, r in enumerate(results):
        r["N"] = str(i + 1)
    cols = ["N", "Story", "Unique_Name", "Station", "Output_Case", "Step_Type", "P", "M2", "M3"]
    return (
        "PASO 6: Esfuerzos Finales Amplificados\n"
        "  M2_final = M2 * Delta_Y\n"
        "  M3_final = M3 * Delta_X\n\n"
        + format_table(results, columns=cols)
        + "\n\nResultados guardados en results/columnas/esfuerzos_finales.csv"
    )


# ═══════════════════════════════════════════════════════════════════════
# PASO 7: Momentos nominales (Mn2, Mn3)
# ═══════════════════════════════════════════════════════════════════════

def handle_columna_mn(args: list[str]) -> str:
    """cas columna mn -> Calcula momentos nominales Mn2 y Mn3. Solo columnas con propiedades."""
    pp = _project()
    esfuerzos_fin = read_results_csv(pp, "columnas/esfuerzos_finales.csv")
    asignaciones = read_csv(pp, "col_asignaciones")
    diagramas = read_json(pp, "diagramas.json") or {}
    props = read_csv(pp, "col_props")

    if not esfuerzos_fin:
        raise InvalidInput("Sin esfuerzos finales. Ejecute 'cas columna esfuerzos-fin'.")
    if not asignaciones:
        raise InvalidInput("Sin asignaciones de diagramas. Use 'cas columna asignar ...'.")
    if not props:
        raise InvalidInput("Sin propiedades. Use 'cas columna props ...'.")

    props_unique = {str(r.get("Unique_Name", "")).strip() for r in props}
    nominales = {k.replace("_nominal", ""): v for k, v in diagramas.items() if "_nominal" in k}
    if not nominales:
        raise InvalidInput("Sin diagramas nominales. Use 'cas columna diagrama ...'.")

    from axis.columnas.analysis import compute_nominal_moments
    results = compute_nominal_moments(esfuerzos_fin, asignaciones, nominales)
    results = [r for r in results if str(r.get("Unique_Name", "")).strip() in props_unique]

    if not results:
        un_esf = {str(r.get("Unique_Name", "")).strip() for r in esfuerzos_fin}
        un_asig = {str(r.get("Unique_Name", "")).strip() for r in asignaciones}
        nom_asig = {str(r.get("Diagrama_Nominal", "")).strip() for r in asignaciones}
        raise InvalidInput(
            "No se calcularon momentos nominales. Causas posibles:\n"
            "  1) Unique_Name en asignaciones no coincide con los de esfuerzos importados.\n"
            f"     Columnas en esfuerzos: {sorted(un_esf)[:10]}{'...' if len(un_esf) > 10 else ''}\n"
            f"     Columnas en asignaciones: {sorted(un_asig)}\n"
            "  2) Diagrama_Nominal no existe en diagramas cargados.\n"
            f"     Diagramas asignados: {sorted(nom_asig)}\n"
            f"     Diagramas disponibles: {sorted(nominales.keys())}\n"
            "  Solucion: cas columna asignar <Unique_Name> <Diagrama> para cada columna;\n"
            "  cas diagrama add <nombre> nominal <archivo> si falta cargar diagramas."
        )

    write_results_csv(pp, "columnas/momentos_nominales.csv", results)

    for i, r in enumerate(results):
        r["N"] = str(i + 1)
    cols = ["N", "Story", "Unique_Name", "Load_Case", "Step_Type",
            "Mn2_Inf", "Mn3_Inf", "Mn2_Sup", "Mn3_Sup"]
    return (
        "PASO 7: Momentos Nominales\n\n"
        + format_table(results, columns=cols)
        + "\n\nResultados guardados en results/columnas/momentos_nominales.csv"
    )


# ═══════════════════════════════════════════════════════════════════════
# PASO 8: Estados sísmicos combinados
# ═══════════════════════════════════════════════════════════════════════

def handle_columna_estados(args: list[str]) -> str:
    """cas columna estados -> Estados sismicos combinados."""
    pp = _project()
    mn_results = read_results_csv(pp, "columnas/momentos_nominales.csv")

    if not mn_results:
        raise InvalidInput("Sin momentos nominales. Ejecute 'cas columna mn'.")

    from axis.columnas.analysis import compute_seismic_states
    results = compute_seismic_states(mn_results)

    if not results:
        return "No se pudieron generar estados sismicos."

    write_results_csv(pp, "columnas/estados_sismicos.csv", results)

    for i, r in enumerate(results):
        r["N"] = str(i + 1)
    cols = ["N", "Story", "Unique_Name", "Load_Case",
            "Mn2_Inf", "Mn2_Sup", "Mn3_Inf", "Mn3_Sup"]
    return (
        "PASO 8: Estados Sismicos Combinados\n"
        "  Sismicos: Estado 1 (Mn Inf Max + Mn Sup Min) y Estado 2 (inv.)\n"
        "  No sismicos: momentos en valor absoluto\n\n"
        + format_table(results, columns=cols)
        + "\n\nResultados guardados en results/columnas/estados_sismicos.csv"
    )


# ═══════════════════════════════════════════════════════════════════════
# PASO 9: Verificación P-M (flexocompresión)
# ═══════════════════════════════════════════════════════════════════════

def handle_columna_verificacion(args: list[str]) -> str:
    """cas columna verificacion -> Verificacion P-M. Solo columnas con propiedades."""
    pp = _project()
    esfuerzos_fin = read_results_csv(pp, "columnas/esfuerzos_finales.csv")
    asignaciones = read_csv(pp, "col_asignaciones")
    diagramas = read_json(pp, "diagramas.json") or {}
    props = read_csv(pp, "col_props")

    if not esfuerzos_fin:
        raise InvalidInput("Sin esfuerzos finales. Ejecute 'cas columna esfuerzos-fin'.")
    if not asignaciones:
        raise InvalidInput("Sin asignaciones. Use 'cas columna asignar ...'.")
    if not props:
        raise InvalidInput("Sin propiedades. Use 'cas columna props ...'.")

    props_unique = {str(r.get("Unique_Name", "")).strip() for r in props}
    nominales = {k.replace("_nominal", ""): v for k, v in diagramas.items() if "_nominal" in k}
    ultimos = {k.replace("_ultimo", ""): v for k, v in diagramas.items() if "_ultimo" in k}

    if not ultimos and not nominales:
        raise InvalidInput("Sin diagramas. Use 'cas columna diagrama ...'.")

    from axis.columnas.analysis import compute_pm_verification
    results = compute_pm_verification(esfuerzos_fin, asignaciones, nominales, ultimos)
    results = [r for r in results if str(r.get("Unique_Name", "")).strip() in props_unique]

    if not results:
        return "No se pudieron generar resultados de verificacion P-M."

    write_results_csv(pp, "columnas/verificacion_pm.csv", results)

    for i, r in enumerate(results):
        r["N"] = str(i + 1)
    cols = ["N", "Story", "Unique_Name", "Load_Case",
            "Pu", "M2", "M3", "Mu_Equiv", "Cap_Ultima", "Ratio", "Cumple"]
    return (
        "PASO 9: Verificacion P-M (Flexocompresion)\n\n"
        + format_table(results, columns=cols)
        + "\n\nResultados guardados en results/columnas/verificacion_pm.csv"
    )


# ═══════════════════════════════════════════════════════════════════════
# RESUMEN
# ═══════════════════════════════════════════════════════════════════════

def handle_columna_resumen(args: list[str]) -> str:
    """cas columna resumen -> Resumen de verificacion P-M. Solo columnas con propiedades."""
    pp = _project()
    verificacion = read_results_csv(pp, "columnas/verificacion_pm.csv")
    props = read_csv(pp, "col_props")

    if not verificacion:
        raise InvalidInput("Sin resultados de verificacion. Ejecute 'cas columna verificacion'.")
    if not props:
        raise InvalidInput("Sin propiedades. Use 'cas columna props ...'.")

    props_unique = {str(r.get("Unique_Name", "")).strip() for r in props}
    verificacion = [r for r in verificacion if str(r.get("Unique_Name", "")).strip() in props_unique]
    from axis.columnas.analysis import compute_pm_summary
    results = compute_pm_summary(verificacion)

    if not results:
        return "No se pudo generar resumen."

    write_results_csv(pp, "columnas/resumen_pm.csv", results)

    for i, r in enumerate(results):
        r["N"] = str(i + 1)
    cols = ["N", "Story", "Unique_Name", "Ratio_Max", "Cumple"]

    n_ok = sum(1 for r in results if r.get("Cumple") == "Si")
    n_total = len(results)

    return (
        "RESUMEN: Verificacion P-M por Columna\n\n"
        + format_table(results, columns=cols)
        + f"\n\n  {n_ok}/{n_total} columnas cumplen verificacion P-M."
        + "\n\nResultados guardados en results/columnas/resumen_pm.csv"
    )


# ═══════════════════════════════════════════════════════════════════════
# COMANDOS RESUMEN: DISEÑO COMPLETO EN UN PASO
# ═══════════════════════════════════════════════════════════════════════

def handle_columna_diseno(args: list[str]) -> str:
    """cas columna diseno -> Ejecuta todos los pasos de análisis y verificación P-M."""
    pp = _project()

    # TABLA 1: Propiedades de columnas analizadas (solo las que tienen esfuerzos Station 0)
    esfuerzos = _esfuerzos_station_0(read_csv(pp, "col_esfuerzos"))
    props = read_csv(pp, "col_props")
    if props and esfuerzos:
        un_esf = {
            (str(r.get("Story", "")).strip(), str(r.get("Unique_Name", "")).strip())
            for r in esfuerzos
        }
        filas = [
            r for r in props
            if (str(r.get("Story", "")).strip(), str(r.get("Unique_Name", "")).strip()) in un_esf
        ] or props
        for i, r in enumerate(filas):
            r["N"] = str(i + 1)
        cols_tabla1 = [
            "N",
            "Story",
            "Unique_Name",
            "k",
            "lu",
            "Ix",
            "Iy",
            "Ag",
            "Ec",
            "Bd",
            "fc",
            "fy",
        ]
        tabla1 = (
            "TABLA 1: PROPIEDADES DE COLUMNAS ANALIZADAS\n\n"
            + format_table(filas, columns=cols_tabla1)
        )
    else:
        tabla1 = "TABLA 1: PROPIEDADES DE COLUMNAS ANALIZADAS\n\n(no hay propiedades de columnas definidas)\n"

    # Encadenar el resto de pasos para mostrar todas las tablas
    outputs: list[str] = [tabla1]
    outputs.append(handle_columna_q([]))
    outputs.append(handle_columna_esbeltez([]))
    outputs.append(handle_columna_segundo_orden([]))
    outputs.append(handle_columna_cm([]))
    outputs.append(handle_columna_delta([]))
    outputs.append(handle_columna_esfuerzos_finales([]))
    outputs.append(handle_columna_mn([]))
    outputs.append(handle_columna_estados([]))
    outputs.append(handle_columna_verificacion([]))
    outputs.append(handle_columna_resumen([]))
    return "\n\n".join(outputs)


def handle_columna_etabs_diseno(args: list[str]) -> str:
    """cas columna etabs-diseno [R_X] [R_Y] [diagrama_default]

    Atajo: importa desde ETABS y ejecuta diseño completo.
    Si hay diagramas pero faltan asignaciones, asigna 'diagrama_default' (o el primero
    disponible) a todas las columnas importadas.

    Requiere: ETABS abierto, propiedades (columna props), al menos un diagrama cargado.
    """
    msg_import = handle_columna_etabs_import(args)
    pp = _project()

    # Auto-asignar diagramas si faltan: usar diagrama_default o el primer nominal disponible
    esfuerzos = _esfuerzos_station_0(read_csv(pp, "col_esfuerzos"))
    asignaciones = read_csv(pp, "col_asignaciones")
    diagramas = read_json(pp, "diagramas.json") or {}
    nominales = [k.replace("_nominal", "") for k in diagramas if "_nominal" in k]

    if not nominales:
        raise InvalidInput(
            "Sin diagramas nominales. Cargue al menos uno:\n"
            "  cas diagrama add <nombre> nominal <archivo.xlsx|.csv>"
        )

    un_esf = {str(r.get("Unique_Name", "")).strip() for r in esfuerzos if r.get("Unique_Name")}
    un_asig = {str(r.get("Unique_Name", "")).strip().upper() for r in asignaciones}
    diagrama_default = args[2] if len(args) > 2 else nominales[0]
    if diagrama_default not in nominales:
        diagrama_default = nominales[0]

    nuevos = []
    for un in un_esf:
        if not un or str(un).strip().upper() in un_asig:
            continue
        nuevos.append({
            "Unique_Name": un,
            "Diagrama_Nominal": diagrama_default,
            "Diagrama_Ultimo": diagrama_default,
        })

    if nuevos:
        fieldnames = ELEMENT_FIELDNAMES.get("col_asignaciones", ["Unique_Name", "Diagrama_Nominal", "Diagrama_Ultimo"])
        all_asig = asignaciones + nuevos
        write_csv(pp, all_asig, "col_asignaciones", fieldnames)
        msg_import += f"\n\nAuto-asignacion: {len(nuevos)} columnas -> diagrama '{diagrama_default}'"

    msg_diseno = handle_columna_diseno([])
    return msg_import + "\n\n" + msg_diseno
