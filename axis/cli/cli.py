"""CLI minimalista: cas <scope> <operation>."""

from __future__ import annotations

import sys
from pathlib import Path

from axis.core.project import create_project, set_active_project, get_active_project, list_projects
from axis.core.tree import get_project_tree, format_tree
from axis.core.context import has_active_project, is_direct_calculation_mode, get_global_config
from axis.core.exceptions import (
    ProjectNotFound,
    NoActiveProject,
    OperationNotRegistered,
    InvalidInput,
)
from axis.engine.engine import run
from axis.core.database import read_csv, read_results_csv, write_csv, write_results_csv
from axis.core.project import get_active_project_path
from axis.core.exceptions import NoActiveProject
from tabulate import tabulate

from axis.operations import placeholder, flexion  # noqa: F401


def _get_base_path() -> Path:
    """Directorio base para proyectos (cwd)."""
    return Path.cwd()


def _handle_new(args: list[str]) -> str:
    """cas new <project>"""
    if len(args) < 1:
        raise InvalidInput("Especifique el nombre del proyecto: cas new <project>")
    name = args[0]
    path = create_project(name, _get_base_path())
    set_active_project(name, _get_base_path())
    return f"Proyecto '{name}' creado y activado.\nRuta: {path}"


def _handle_use(args: list[str]) -> str:
    """cas use <project>"""
    if len(args) < 1:
        raise InvalidInput("Especifique el proyecto: cas use <project>")
    name = args[0]
    set_active_project(name, _get_base_path())
    return f"Proyecto activo: {name}"


def _handle_tree() -> str:
    """cas tree"""
    tree = get_project_tree(_get_base_path())
    return format_tree(tree)


def _handle_info() -> str:
    """axis info"""
    config = get_global_config()
    active = config.get("active_project") or "Ninguno"
    path = config.get("project_path") or "-"
    return f"Proyecto activo: {active}\nRuta: {path}"


def _handle_list_projects() -> str:
    """cas list-projects"""
    projects = list_projects(_get_base_path())
    if not projects:
        return "No hay proyectos. Use 'cas new <project>' para crear uno."
    return "Proyectos:\n  " + "\n  ".join(projects)


def _handle_add_viga(args: list[str]) -> str:
    """cas add viga <nombre> <fc> <fy> <b> <h> <rec> <Mu>"""
    project_path = get_active_project_path(_get_base_path())
    if not project_path:
        raise NoActiveProject("No hay proyecto activo. Use 'cas use <proyecto>'.")
    if len(args) < 7:
        raise InvalidInput(
            "Uso: cas add viga <nombre> <fc> <fy> <b> <h> <rec> <Mu>"
        )
    nombre, fc, fy, b, h, rec, mu = args[0], args[1], args[2], args[3], args[4], args[5], args[6]
    nueva_fila = {"nombre": nombre, "fc": fc, "fy": fy, "b": b, "h": h, "rec": rec, "Mu": mu}
    rows = read_csv(project_path)
    fieldnames = ["nombre", "fc", "fy", "b", "h", "rec", "Mu"]
    for i, row in enumerate(rows):
        row["nombre"] = row.get("nombre") or f"Viga {i + 1}"
    rows.append(nueva_fila)
    write_csv(project_path, rows, fieldnames)
    return f"Viga '{nombre}' añadida correctamente."


def _handle_edit_viga(args: list[str]) -> str:
    """cas edit viga <índice> <nombre> <fc> <fy> <b> <h> <rec> <Mu>"""
    project_path = get_active_project_path(_get_base_path())
    if not project_path:
        raise NoActiveProject("No hay proyecto activo. Use 'cas use <proyecto>'.")
    if len(args) < 8:
        raise InvalidInput(
            "Uso: cas edit viga <índice> <nombre> <fc> <fy> <b> <h> <rec> <Mu>\n"
            "     Índice: número de fila (1, 2, 3...). Use 'cas list vigas' para ver."
        )
    try:
        idx = int(args[0])
    except ValueError:
        raise InvalidInput("El índice debe ser un número entero.")
    nombre, fc, fy, b, h, rec, mu = args[1], args[2], args[3], args[4], args[5], args[6], args[7]
    rows = read_csv(project_path)
    if idx < 1 or idx > len(rows):
        raise InvalidInput(
            f"Índice {idx} inválido. Hay {len(rows)} viga(s) (use 1 a {len(rows)})."
        )
    rows[idx - 1] = {"nombre": nombre, "fc": fc, "fy": fy, "b": b, "h": h, "rec": rec, "Mu": mu}
    fieldnames = ["nombre", "fc", "fy", "b", "h", "rec", "Mu"]
    write_csv(project_path, rows, fieldnames)
    return f"Viga {idx} ('{nombre}') actualizada."


def _handle_flexion_viga() -> str:
    """cas flexion viga - diseño por flexión desde elements/data.csv"""
    project_path = get_active_project_path(_get_base_path())
    if not project_path:
        raise NoActiveProject("No hay proyecto activo. Use 'cas use <proyecto>'.")
    rows = read_csv(project_path)
    if not rows:
        raise InvalidInput(
            "elements/data.csv está vacío. Añada vigas con columnas: fc, fy, b, h, rec, Mu"
        )
    required = ("fc", "fy", "b", "h", "rec", "Mu")
    # nombre es opcional para vigas existentes; se usa "Viga N" si falta
    for row in rows:
        missing = [k for k in required if k not in row or row[k] == ""]
        if missing:
            raise InvalidInput(f"Faltan columnas en data.csv: {missing}")
    data = {"vigas": rows}
    result = run("flexion", "viga", data)
    resultados = result.get("resultados", [])
    out_path = write_results_csv(project_path, "flexion_viga.csv", resultados)
    return f"Flexión calculada: {len(resultados)} viga(s).\nResultados: {out_path}"


# Headers para tabla de vigas (datos de entrada)
_VIGAS_HEADER_MAP = {
    "N": "Nº",
    "nombre": "Nombre",
    "fc": "fc\n(kg/cm²)",
    "fy": "fy\n(kg/cm²)",
    "b": "b\n(cm)",
    "h": "h\n(cm)",
    "rec": "rec\n(cm)",
    "Mu": "Mu\n(Tn-m)",
}

# Título en línea 1, unidad en línea 2 (como imagen) para no anchar columnas
_FLEXION_HEADER_MAP = {
    "N": "Nº",
    "nombre": "Nombre",
    "As (cm²)": "As\n(cm²)",
    "As' (cm²)": "As'\n(cm²)",
    "As": "As\n(cm²)",
    "As'": "As'\n(cm²)",
    "Tipo Sección": "Tipo",
    "Tipo": "Tipo",
    "Mcr (Tn-m)": "Mcr\n(Tn-m)",
    "Mcr": "Mcr\n(Tn-m)",
    "Asmin (cm²)": "Asmin\n(cm²)",
    "Asmin": "Asmin\n(cm²)",
    "Cumple Mcr": "OK",
    "OK": "OK",
}


def _format_table(
    rows: list[dict],
    columns: list[str] | None = None,
    header_map: dict[str, str] | None = None,
) -> str:
    """Formatea filas en tabla minimalista, centrada, anchos justos."""
    if not rows:
        return "(sin datos)"
    cols = columns or list(rows[0].keys())
    m = header_map or {}
    flex_map = _FLEXION_HEADER_MAP
    vigas_map = _VIGAS_HEADER_MAP
    headers = [
        m.get(c, vigas_map.get(c, flex_map.get(c, c))) for c in cols
    ]
    table_rows = [[str(row.get(c, "")) for c in cols] for row in rows]
    n = len(headers)
    return tabulate(
        table_rows,
        headers=headers,
        tablefmt="grid",
        colalign=("center",) * n,
    )


def _handle_list_vigas() -> str:
    """cas list vigas - muestra todas las vigas del proyecto (incl. no calculadas)"""
    project_path = get_active_project_path(_get_base_path())
    if not project_path:
        raise NoActiveProject("No hay proyecto activo. Use 'cas use <proyecto>'.")
    rows = read_csv(project_path)
    if not rows:
        raise InvalidInput(
            "No hay vigas. Use 'cas add viga <nombre> <fc> <fy> <b> <h> <rec> <Mu>'."
        )
    for i, row in enumerate(rows):
        row["N"] = str(i + 1)
    cols = ["N", "nombre", "fc", "fy", "b", "h", "rec", "Mu"]
    return "Vigas del proyecto\n\n" + _format_table(rows, columns=cols, header_map=_VIGAS_HEADER_MAP)


def _handle_results_flexion() -> str:
    """cas results flexion - muestra resultados de flexión en tabla"""
    project_path = get_active_project_path(_get_base_path())
    if not project_path:
        raise NoActiveProject("No hay proyecto activo. Use 'cas use <proyecto>'.")
    rows = read_results_csv(project_path, "flexion_viga.csv")
    if not rows:
        raise InvalidInput(
            "No hay resultados de flexión. Ejecute 'cas flexion viga' primero."
        )
    for i, row in enumerate(rows):
        row["N"] = str(i + 1)
    cols = ["N"] + [k for k in rows[0].keys() if k != "N"]
    return "Flexión\n\n" + _format_table(rows, columns=cols)


def parse_and_execute(argv: list[str]) -> str:
    """Parsea argumentos y ejecuta el comando correspondiente."""
    args = argv[1:] if len(argv) > 1 else []
    if not args:
        return (
            "CAS - Motor de diseño estructural\n\n"
            "Uso: cas <scope> <operation> [args]\n\n"
            "Comandos base:\n"
            "  cas new <project>       Crear y activar proyecto\n"
            "  cas use <project>       Activar proyecto\n"
            "  cas tree                Mostrar estructura del proyecto\n"
            "  cas info                Información del proyecto activo\n"
            "  cas list-projects       Listar proyectos\n"
            "  cas add viga <nombre> <fc> <fy> <b> <h> <rec> <Mu>\n"
            "                          Añadir viga al proyecto\n"
            "  cas list vigas          Ver todas las vigas (datos de entrada)\n"
            "  cas edit viga <i> <nombre> <fc> <fy> <b> <h> <rec> <Mu>\n"
            "                          Editar viga por índice (1, 2, 3...)\n"
            "  cas flexion viga        Diseño por flexión de vigas\n"
            "  cas results flexion     Ver resultados de flexión en tabla\n"
        )
    scope = args[0].lower()
    if scope == "new":
        return _handle_new(args[1:])
    if scope == "use":
        return _handle_use(args[1:])
    if scope == "tree":
        return _handle_tree()
    if scope == "info":
        return _handle_info()
    if scope == "list-projects":
        return _handle_list_projects()
    if scope == "add" and len(args) > 1 and args[1].lower() == "viga":
        return _handle_add_viga(args[2:])
    if scope == "list" and len(args) > 1 and args[1].lower() == "vigas":
        return _handle_list_vigas()
    if scope == "edit" and len(args) > 1 and args[1].lower() == "viga":
        return _handle_edit_viga(args[2:])
    if scope == "flexion" and len(args) > 1 and args[1].lower() == "viga":
        return _handle_flexion_viga()
    if scope == "results" and len(args) > 1 and args[1].lower() == "flexion":
        return _handle_results_flexion()
    if is_direct_calculation_mode(args):
        operation = args[1] if len(args) > 1 else ""
        data = {}
        result = run(scope, operation, data)
        return str(result)
    raise InvalidInput(f"Comando desconocido: {scope}")


def main() -> int:
    """Punto de entrada del CLI."""
    try:
        output = parse_and_execute(sys.argv)
        print(output)
        return 0
    except (
        ProjectNotFound,
        NoActiveProject,
        OperationNotRegistered,
        InvalidInput,
    ) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error inesperado: {e}", file=sys.stderr)
        return 1
