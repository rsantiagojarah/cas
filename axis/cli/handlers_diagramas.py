"""Handlers CLI: diagramas de interacción P-M (compartidos por muros y columnas)."""

from __future__ import annotations

import csv
from pathlib import Path

from axis.core.exceptions import NoActiveProject, InvalidInput
from axis.core.project import get_active_project_path
from axis.core.database import read_json, write_json, read_csv, read_results_csv
from axis.cli.tables import format_table
from axis.cli.handlers import get_base_path
from axis.cli.file_picker import seleccionar_archivo_diagrama
from axis.cli.pm_plotter import plot_superficie_interaccion
from axis.data.interaction_parser import import_from_excel


def _project() -> Path:
    p = get_active_project_path(get_base_path())
    if not p:
        raise NoActiveProject("No hay proyecto activo. Use 'cas use <proyecto>'.")
    return p


DIAGRAMAS_JSON = "diagramas.json"


def _sanitize(name: str) -> str:
    s = name.strip()
    return "".join(c for c in s if c.isalnum() or c in ("-", "_")) or "muro"


def handle_diagrama_add(args: list[str]) -> str:
    """cas diagrama add <nombre_seccion> <nominal|ultimo> [archivo]

    Importa un diagrama de interacción en la base de datos del proyecto.
    Si no se pasa archivo, se abre una ventana para elegir Excel o CSV.
    CSV: columnas P, M2, M3, angle. Excel: formato SAP2000 (Curve/ángulo, P, M2, M3).
    """
    pp = _project()
    if len(args) < 2:
        raise InvalidInput(
            "Uso: cas diagrama add <nombre_seccion> <nominal|ultimo> [archivo]\n"
            "  nombre_seccion: identificador (ej. Muro_400x20, Col_50x50)\n"
            "  tipo: nominal | ultimo\n"
            "  archivo: opcional; si no se indica, se abre ventana para seleccionar Excel o CSV.")
    nombre = args[0].strip()
    tipo = args[1].lower()
    if tipo not in ("nominal", "ultimo"):
        raise InvalidInput("tipo debe ser 'nominal' o 'ultimo'.")

    if len(args) >= 3:
        path = Path(args[2])
    else:
        path = seleccionar_archivo_diagrama(
            titulo=f"Diagrama {tipo} - {nombre} (Excel o CSV)"
        )
        if path is None:
            raise InvalidInput("No se seleccionó ningún archivo.")
    if not path.is_absolute():
        path = Path.cwd() / path
    if not path.exists():
        raise InvalidInput(f"Archivo no encontrado: {path}")

    suf = path.suffix.lower()
    if suf in (".xlsx", ".xls"):
        try:
            puntos = import_from_excel(path)
        except ValueError as e:
            raise InvalidInput(str(e)) from e
        if not puntos:
            raise InvalidInput("Excel sin puntos válidos (formato SAP2000 esperado).")
    else:
        puntos = []
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                puntos.append({
                    "p": float(row.get("P", row.get("p", 0))),
                    "m2": float(row.get("M2", row.get("m2", 0))),
                    "m3": float(row.get("M3", row.get("m3", 0))),
                    "angle": float(row.get("angle", row.get("Angle", 0))),
                })
        if not puntos:
            raise InvalidInput("CSV sin datos válidos (se esperan columnas P, M2, M3, angle).")

    diagramas = read_json(pp, DIAGRAMAS_JSON) or {}
    key = f"{nombre}_{tipo}"
    diagramas[key] = puntos
    write_json(pp, DIAGRAMAS_JSON, diagramas)
    return f"Diagrama '{nombre}' ({tipo}) importado: {len(puntos)} puntos. Base de datos actualizada."


def handle_diagrama_list(args: list[str]) -> str:
    """cas diagrama list  -> Lista todas las secciones y diagramas (muros y columnas)."""
    pp = _project()
    diagramas = read_json(pp, DIAGRAMAS_JSON) or {}
    if not diagramas:
        return "No hay diagramas de interacción. Use 'cas diagrama add <nombre> <nominal|ultimo> <archivo.csv>'."

    secciones: dict[str, dict] = {}
    for key, puntos in diagramas.items():
        if "_nominal" in key:
            sec = key.replace("_nominal", "")
            tipo = "nominal"
        elif "_ultimo" in key:
            sec = key.replace("_ultimo", "")
            tipo = "ultimo"
        else:
            sec = key
            tipo = "?"
        if sec not in secciones:
            secciones[sec] = {"nombre": sec, "nominal": "-", "ultimo": "-"}
        n_pts = len(puntos) if isinstance(puntos, list) else 0
        secciones[sec][tipo] = f"{n_pts} pts"

    rows = []
    for sec in sorted(secciones.keys()):
        s = secciones[sec]
        rows.append({
            "Sección": s["nombre"],
            "Nominal": s["nominal"],
            "Último": s["ultimo"],
        })
    return "Diagramas de interacción (muros y columnas)\n\n" + format_table(rows, columns=["Sección", "Nominal", "Último"])


def handle_diagrama_plot(args: list[str]) -> str:
    """cas diagrama plot <nombre_muro_o_seccion> [nominal|ultimo] [archivo_opcional]

    Muestra la superficie de interacción 3D (igual que Diseño_Columnas).
    Si nombre es un muro con combinaciones importadas de ETABS (TABLA 1), se usan
    automáticamente; si no, puede indicar un archivo CSV/Excel con P, M2, M3.
    Requiere: pip install matplotlib scipy
    """
    pp = _project()
    if len(args) < 1:
        raise InvalidInput(
            "Uso: cas diagrama plot <nombre_muro_o_seccion> [nominal|ultimo] [archivo]\n"
            "  nombre: muro (ej. MEX-1) o sección de diagrama; si es muro se usan combinaciones ETABS.\n"
            "  tipo: nominal | ultimo (por defecto ultimo)\n"
            "  archivo: opcional CSV/Excel con P, M2, M3 si no hay combinaciones guardadas.")
    nombre = args[0].strip()
    tipo = "ultimo"
    archivo_comb = None
    i = 1
    if i < len(args) and args[i].lower() in ("nominal", "ultimo"):
        tipo = args[i].lower()
        i += 1
    if i < len(args):
        archivo_comb = args[i]

    diagramas = read_json(pp, DIAGRAMAS_JSON) or {}
    # Si nombre es un muro con asignación, usar el diagrama asignado
    asignaciones = read_csv(pp, "muro_asignaciones")
    asig_muro = next((a for a in asignaciones if (a.get("muro") or "").strip() == nombre), None)
    if asig_muro:
        nom_sec = (asig_muro.get("Diagrama_Nominal") or "").strip()
        ult_sec = (asig_muro.get("Diagrama_Ultimo") or "").strip() or nom_sec
        if nom_sec or ult_sec:
            section_name = ult_sec if tipo == "ultimo" else (nom_sec or ult_sec)
        else:
            section_name = nombre
    else:
        section_name = nombre
    key = f"{section_name}_{tipo}"
    puntos = diagramas.get(key)
    if not puntos or not isinstance(puntos, list):
        raise InvalidInput(
            f"No existe diagrama para '{nombre}' (sección '{section_name}', tipo '{tipo}'). "
            "Use 'cas diagrama list' y 'cas muro asignar' si es un muro.")

    puntos_esfuerzo = None
    # Combinaciones guardadas de ETABS (TABLA 1) para este muro
    if not archivo_comb:
        comb_path = f"muros_multi/{_sanitize(nombre)}_combinaciones.csv"
        comb_rows = read_results_csv(pp, comb_path)
        if comb_rows:
            puntos_esfuerzo = [
                {"P": float(r.get("P", 0)), "M2": float(r.get("M2", 0)), "M3": float(r.get("M3", 0))}
                for r in comb_rows
            ]
    if archivo_comb:
        path_comb = Path(archivo_comb)
        if not path_comb.is_absolute():
            path_comb = Path.cwd() / path_comb
        if not path_comb.exists():
            raise InvalidInput(f"Archivo de combinaciones no encontrado: {path_comb}")
        suf = path_comb.suffix.lower()
        if suf in (".xlsx", ".xls"):
            try:
                import pandas as pd
                df = pd.read_excel(path_comb)
                col_p = "P" if "P" in df.columns else "p"
                col_m2 = "M2" if "M2" in df.columns else "m2"
                col_m3 = "M3" if "M3" in df.columns else "m3"
                puntos_esfuerzo = []
                for _, row in df.iterrows():
                    p_val = row.get(col_p, 0)
                    m2_val = row.get(col_m2, 0)
                    m3_val = row.get(col_m3, 0)
                    if pd.isna(p_val) and pd.isna(m2_val):
                        continue
                    puntos_esfuerzo.append({
                        "P": float(p_val if not pd.isna(p_val) else 0),
                        "M2": float(m2_val if not pd.isna(m2_val) else 0),
                        "M3": float(m3_val if not pd.isna(m3_val) else 0),
                    })
            except Exception as e:
                raise InvalidInput(f"No se pudo leer combinaciones desde Excel: {e}") from e
        else:
            with open(path_comb, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                puntos_esfuerzo = []
                for row in reader:
                    puntos_esfuerzo.append({
                        "P": float(row.get("P", row.get("p", 0))),
                        "M2": float(row.get("M2", row.get("m2", 0))),
                        "M3": float(row.get("M3", row.get("m3", 0))),
                    })
        if not puntos_esfuerzo:
            raise InvalidInput("El archivo de combinaciones no tiene filas válidas (P, M2, M3).")

    subtit = f"{nombre} — diagrama {section_name} ({tipo}), {len(puntos)} pts"
    if puntos_esfuerzo and not archivo_comb:
        subtit += f" — {len(puntos_esfuerzo)} combinaciones ETABS (TABLA 1)"
    elif puntos_esfuerzo:
        subtit += f" — {len(puntos_esfuerzo)} combinaciones (archivo)"
    try:
        plot_superficie_interaccion(
            puntos,
            titulo="Superficie de Interacción",
            subtitulo=subtit,
            puntos_esfuerzo=puntos_esfuerzo,
        )
    except RuntimeError as e:
        raise InvalidInput(str(e)) from e
    except ValueError as e:
        raise InvalidInput(str(e)) from e

    msg = f"Gráfico mostrado: {nombre} — diagrama {section_name} ({tipo}), {len(puntos)} pts."
    if puntos_esfuerzo:
        msg += f" {len(puntos_esfuerzo)} combinaciones de carga" + (" (ETABS TABLA 1)." if not archivo_comb else " (archivo).")
    return msg


def handle_diagrama_check_pm(args: list[str]) -> str:
    """cas diagrama check-pm <nombre_muro> <Story> <Combinación>

    Verificación P-M para una sola combinación: muestra P, M2, M3, θ, Mu_equiv,
    Cap(P,θ) y Ratio para revisar la interpolación contra la superficie asignada.
    """
    import math
    pp = _project()
    if len(args) < 3:
        raise InvalidInput(
            "Uso: cas diagrama check-pm <nombre_muro> <Story> <Combinación>\n"
            "  Ej: cas diagrama check-pm MEX-1 Story3 \"1.25(CM+CV)+SX\"")
    nombre_muro = args[0].strip()
    story = args[1].strip()
    comb = " ".join(args[2:]).strip()

    asignaciones = read_csv(pp, "muro_asignaciones")
    asig = next((a for a in asignaciones if (a.get("muro") or "").strip() == nombre_muro), None)
    if not asig:
        raise InvalidInput(f"No hay asignación de diagrama para muro '{nombre_muro}'.")
    ult_sec = (asig.get("Diagrama_Ultimo") or "").strip() or (asig.get("Diagrama_Nominal") or "").strip()
    if not ult_sec:
        raise InvalidInput(f"Muro '{nombre_muro}' no tiene diagrama último asignado.")

    diagramas = read_json(pp, DIAGRAMAS_JSON) or {}
    pts = diagramas.get(f"{ult_sec}_ultimo") or diagramas.get(f"{ult_sec}_nominal")
    if not pts or not isinstance(pts, list):
        raise InvalidInput(f"No existe diagrama '{ult_sec}' (ultimo/nominal) en la base de datos.")

    comb_path = f"muros_multi/{_sanitize(nombre_muro)}_combinaciones.csv"
    rows = read_results_csv(pp, comb_path)
    if not rows:
        raise InvalidInput(f"No hay combinaciones guardadas para '{nombre_muro}'. Ejecute 'cas muro etabs-diseno' primero.")

    # Buscar fila que coincida con Story y Combinación (Output Case)
    candidato = None
    for r in rows:
        st = str(r.get("Story", "")).strip()
        oc = str(r.get("Output Case", r.get("Output_Case", ""))).strip()
        if st == story and oc == comb:
            candidato = r
            break
    if not candidato:
        disponibles = [f"{r.get('Story')} | {r.get('Output Case','')}" for r in rows[:5]]
        raise InvalidInput(
            f"No se encontró combinación Story='{story}', Combinación='{comb}'.\n"
            f"Ejemplos en archivo: {disponibles}")

    P = float(candidato.get("P", 0))
    M2 = float(candidato.get("M2", 0))
    M3 = float(candidato.get("M3", 0))
    angle_rad = math.atan2(M2, M3)
    angle_deg = math.degrees(angle_rad)
    if angle_deg < 0:
        angle_deg += 360.0
    mu_equiv = math.sqrt(M2 * M2 + M3 * M3)

    from axis.columnas.analysis import InteractionSurface
    surface = InteractionSurface(pts)
    try:
        cap = surface.get_moment_nominal(P, angle_deg)
    except Exception as e:
        raise InvalidInput(f"Error al interpolar en superficie: {e}") from e
    ratio = mu_equiv / cap if cap > 0 else (float("inf") if mu_equiv > 0 else 0.0)
    cumple = "✓" if ratio <= 1.0 else "✗"

    lines = [
        "",
        "=" * 60,
        "  CHECK P-M — UNA COMBINACIÓN",
        "=" * 60,
        f"  Muro: {nombre_muro}   Diagrama: {ult_sec} (último)   {len(pts)} pts",
        f"  Story: {story}   Combinación: {comb}",
        "",
        "  Entrada (ETABS TABLA 1):",
        f"    P   = {P:+.2f} Tn",
        f"    M2  = {M2:+.2f} Tn·m",
        f"    M3  = {M3:+.2f} Tn·m",
        "",
        "  Cálculo:",
        f"    θ (deg)   = atan2(M2, M3) = {angle_deg:.4f}°  (0°=M3 largo, 90°=M2)",
        f"    Mu_equiv  = √(M2²+M3²)   = {mu_equiv:.4f} Tn·m",
        f"    Cap(P,θ)  = superficie.get_moment_nominal(P, θ) = {cap:.4f} Tn·m",
        f"    Ratio     = Mu_equiv / Cap = {ratio:.4f}  {cumple}",
        "",
        "=" * 60,
    ]
    return "\n".join(lines)
