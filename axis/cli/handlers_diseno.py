"""Handlers CLI: diseño (flexión, cortante) y resultados. Reglas: ≤200 líneas, ≤150 chars."""

from __future__ import annotations

from axis.core.exceptions import NoActiveProject, InvalidInput
from axis.core.project import get_active_project_path
from axis.core.database import read_csv, read_results_csv, write_results_csv
from axis.engine.engine import run
from axis.cli.tables import format_table, CORTANTE_HEADER_MAP

from axis.cli.handlers import get_base_path
from axis.cli.handlers_vigas import ensure_vu_column
from axis.operations import flexion, cortante  # noqa: F401


def handle_flexion_viga(args: list[str]) -> str:
    """cas flexion viga"""
    project_path = get_active_project_path(get_base_path())
    if not project_path:
        raise NoActiveProject("No hay proyecto activo. Use 'cas use <proyecto>'.")
    rows = read_csv(project_path, "vigas")
    if not rows:
        raise InvalidInput("elements/vigas.csv está vacío. Añada vigas con fc, fy, b, h, rec, Mu")
    required = ("fc", "fy", "b", "h", "rec", "Mu")
    for row in rows:
        missing = [k for k in required if k not in row or row[k] == ""]
        if missing:
            raise InvalidInput(f"Faltan columnas en vigas.csv: {missing}")
    result = run("flexion", "viga", {"vigas": rows})
    resultados = result.get("resultados", [])
    out_path = write_results_csv(project_path, "flexion_viga.csv", resultados)
    return f"Flexión calculada: {len(resultados)} viga(s).\nResultados: {out_path}"


def handle_results_flexion(args: list[str]) -> str:
    """cas results flexion"""
    project_path = get_active_project_path(get_base_path())
    if not project_path:
        raise NoActiveProject("No hay proyecto activo. Use 'cas use <proyecto>'.")
    rows = read_results_csv(project_path, "flexion_viga.csv")
    if not rows:
        raise InvalidInput("No hay resultados de flexión. Ejecute 'cas flexion viga' primero.")
    for i, row in enumerate(rows):
        row["N"] = str(i + 1)
    cols = ["N"] + [k for k in rows[0].keys() if k != "N"]
    return "Flexión\n\n" + format_table(rows, columns=cols)


def handle_cortante_viga(args: list[str]) -> str:
    """cas cortante viga"""
    project_path = get_active_project_path(get_base_path())
    if not project_path:
        raise NoActiveProject("No hay proyecto activo. Use 'cas use <proyecto>'.")
    rows = read_csv(project_path, "vigas")
    if not rows:
        raise InvalidInput("elements/vigas.csv está vacío. Añada vigas con fc, fy, b, h, rec, Vu")
    required = ("fc", "fy", "b", "h", "rec")
    for row in rows:
        missing = [k for k in required if k not in row or row[k] == ""]
        if missing:
            raise InvalidInput(f"Faltan columnas en vigas.csv: {missing}")
    ensure_vu_column(rows)
    result = run("cortante", "viga", {"vigas": rows})
    resultados = result.get("resultados", [])
    out_path = write_results_csv(project_path, "cortante_viga.csv", resultados)
    return f"Cortante calculada: {len(resultados)} viga(s).\nResultados: {out_path}"


def handle_results_cortante(args: list[str]) -> str:
    """cas results cortante"""
    project_path = get_active_project_path(get_base_path())
    if not project_path:
        raise NoActiveProject("No hay proyecto activo. Use 'cas use <proyecto>'.")
    rows = read_results_csv(project_path, "cortante_viga.csv")
    if not rows:
        raise InvalidInput("No hay resultados de cortante. Ejecute 'cas cortante viga' primero.")
    for i, row in enumerate(rows):
        row["N"] = str(i + 1)
    cols = ["N"] + [k for k in rows[0].keys() if k != "N"]
    return "Cortante\n\n" + format_table(rows, columns=cols, header_map=CORTANTE_HEADER_MAP)
