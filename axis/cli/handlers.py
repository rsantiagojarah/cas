"""Handlers de comandos del CLI. Proyectos, vigas, resultados. Reglas: ≤200 líneas, ≤150 chars."""

from __future__ import annotations

from pathlib import Path

from axis.core.project import (
    create_project,
    set_active_project,
    get_active_project,
    list_projects,
    get_active_project_path,
)
from axis.core.tree import get_project_tree, format_tree
from axis.core.context import get_global_config
from axis.core.exceptions import ProjectNotFound, NoActiveProject, InvalidInput
from axis.core.database import (
    read_csv,
    read_results_csv,
    write_csv,
    write_results_csv,
)
from axis.engine.engine import run

from axis.operations import flexion, cortante  # noqa: F401
from axis.cli.tables import (
    format_table,
    VIGAS_HEADER_MAP,
    CORTANTE_HEADER_MAP,
    FLEXION_HEADER_MAP,
)
from axis.cli.help_text import get_help_text

PARAMS_VIGA = ("nombre", "fc", "fy", "b", "h", "rec", "Mu", "Vu")
FIELDNAMES_VIGA = ["nombre", "fc", "fy", "b", "h", "rec", "Mu", "Vu"]


def get_base_path() -> Path:
    """Directorio base para proyectos (cwd)."""
    return Path.cwd()


def ensure_vu_column(rows: list[dict]) -> None:
    """Añade Vu=0 a filas que no lo tienen (compatibilidad)."""
    for row in rows:
        if "Vu" not in row or row["Vu"] == "":
            row["Vu"] = "0"


def handle_new(args: list[str]) -> str:
    """cas new <project>"""
    if len(args) < 1:
        raise InvalidInput("Especifique el nombre del proyecto: cas new <project>")
    name = args[0]
    path = create_project(name, get_base_path())
    set_active_project(name, get_base_path())
    return f"Proyecto '{name}' creado y activado.\nRuta: {path}"


def handle_use(args: list[str]) -> str:
    """cas use <project>"""
    if len(args) < 1:
        raise InvalidInput("Especifique el proyecto: cas use <project>")
    set_active_project(args[0], get_base_path())
    return f"Proyecto activo: {args[0]}"


def handle_tree() -> str:
    """cas tree"""
    return format_tree(get_project_tree(get_base_path()))


def handle_info() -> str:
    """axis info"""
    config = get_global_config()
    active = config.get("active_project") or "Ninguno"
    path = config.get("project_path") or "-"
    return f"Proyecto activo: {active}\nRuta: {path}"


def handle_help(args: list[str]) -> str:
    """cas help [command]"""
    topic = args[0] if args else None
    return get_help_text(topic)


def handle_list_projects() -> str:
    """cas list-projects"""
    projects = list_projects(get_base_path())
    if not projects:
        return "No hay proyectos. Use 'cas new <project>' para crear uno."
    return "Proyectos:\n  " + "\n  ".join(projects)


def handle_sessions_ls() -> str:
    """cas sessions ls"""
    return handle_list_projects()


def handle_resume(args: list[str]) -> str:
    """cas resume [project]"""
    if len(args) >= 1:
        return handle_use(args)
    active = get_active_project(get_base_path())
    if not active:
        raise NoActiveProject(
            "No hay sesión para reanudar. Use 'cas use <proyecto>' o 'cas new <proyecto>'."
        )
    return f"Sesión activa: {active}\nRuta: {get_active_project_path(get_base_path())}"


def handle_add_viga(args: list[str]) -> str:
    """cas add viga <nombre> <fc> <fy> <b> <h> <rec> <Mu> [Vu]"""
    project_path = get_active_project_path(get_base_path())
    if not project_path:
        raise NoActiveProject("No hay proyecto activo. Use 'cas use <proyecto>'.")
    if len(args) < 7:
        raise InvalidInput("Uso: cas add viga <nombre> <fc> <fy> <b> <h> <rec> <Mu> [Vu]")
    nombre, fc, fy, b, h, rec, mu = args[0], args[1], args[2], args[3], args[4], args[5], args[6]
    vu = args[7] if len(args) > 7 else "0"
    nueva_fila = {
        "nombre": nombre, "fc": fc, "fy": fy, "b": b, "h": h, "rec": rec, "Mu": mu, "Vu": vu
    }
    rows = read_csv(project_path)
    ensure_vu_column(rows)
    for i, row in enumerate(rows):
        row["nombre"] = row.get("nombre") or f"Viga {i + 1}"
    rows.append(nueva_fila)
    write_csv(project_path, rows, FIELDNAMES_VIGA)
    return f"Viga '{nombre}' añadida correctamente."


def handle_edit_viga(args: list[str]) -> str:
    """cas edit viga <índice> <param> <valor> | cas edit viga <índice> <nombre> ..."""
    project_path = get_active_project_path(get_base_path())
    if not project_path:
        raise NoActiveProject("No hay proyecto activo. Use 'cas use <proyecto>'.")
    if len(args) < 3:
        raise InvalidInput(
            "Editar un parámetro: cas edit viga <índice> <param> <valor>\n"
            "Editar todo: cas edit viga <índice> <nombre> <fc> <fy> <b> <h> <rec> <Mu>"
        )
    try:
        idx = int(args[0])
    except ValueError:
        raise InvalidInput("El índice debe ser un número entero.")
    rows = read_csv(project_path)
    if idx < 1 or idx > len(rows):
        raise InvalidInput(f"Índice {idx} inválido. Hay {len(rows)} viga(s) (use 1 a {len(rows)}).")
    if len(args) == 3:
        param = args[1].lower()
        if param == "mu":
            param = "Mu"
        if param == "vu":
            param = "Vu"
        if param not in PARAMS_VIGA:
            raise InvalidInput(f"Parámetro '{args[1]}' inválido. Use: {', '.join(PARAMS_VIGA)}")
        ensure_vu_column(rows)
        rows[idx - 1][param] = args[2]
    else:
        if len(args) < 9:
            raise InvalidInput(
                "Edición completa: cas edit viga <índice> <nombre> <fc> <fy> <b> <h> <rec> <Mu> <Vu>"
            )
        rows[idx - 1] = {
            "nombre": args[1], "fc": args[2], "fy": args[3], "b": args[4], "h": args[5],
            "rec": args[6], "Mu": args[7], "Vu": args[8],
        }
    write_csv(project_path, rows, FIELDNAMES_VIGA)
    return f"Viga {idx} actualizada."


def handle_edit_columna(args: list[str]) -> str:
    """cas edit columna <param> <valor> [índice1 índice2 ...]"""
    project_path = get_active_project_path(get_base_path())
    if not project_path:
        raise NoActiveProject("No hay proyecto activo. Use 'cas use <proyecto>'.")
    if len(args) < 2:
        raise InvalidInput(
            "Uso: cas edit columna <param> <valor> [índice1 índice2 ...]\n"
            "Sin índices: aplica a TODAS. Parámetros: nombre, fc, fy, b, h, rec, Mu"
        )
    param = args[0].lower()
    if param == "mu":
        param = "Mu"
    if param == "vu":
        param = "Vu"
    if param not in PARAMS_VIGA:
        raise InvalidInput(f"Parámetro '{args[0]}' inválido. Use: {', '.join(PARAMS_VIGA)}")
    valor = args[1]
    rows = read_csv(project_path)
    n = len(rows)
    indices = list(range(1, n + 1)) if len(args) == 2 else _parse_indices(args[2:], n)
    ensure_vu_column(rows)
    for i in indices:
        rows[i - 1][param] = valor
    write_csv(project_path, rows, FIELDNAMES_VIGA)
    if len(indices) == n:
        return f"Columna '{param}' actualizada en las {n} viga(s)."
    return f"Columna '{param}' actualizada en {len(indices)} viga(s): {indices}."


def _parse_indices(args: list[str], n: int) -> list[int]:
    try:
        indices = sorted(set(int(a) for a in args))
    except ValueError:
        raise InvalidInput("Los índices deben ser números enteros.")
    invalidos = [i for i in indices if i < 1 or i > n]
    if invalidos:
        raise InvalidInput(f"Índice(s) inválido(s): {invalidos}. Hay {n} viga(s).")
    return indices


def handle_delete_viga(args: list[str]) -> str:
    """cas delete viga <índice> [índice2 índice3 ...]"""
    project_path = get_active_project_path(get_base_path())
    if not project_path:
        raise NoActiveProject("No hay proyecto activo. Use 'cas use <proyecto>'.")
    if len(args) < 1:
        raise InvalidInput(
            "Uso: cas delete viga <índice> [índice2 ...]. Use 'cas list vigas' para ver."
        )
    try:
        indices = sorted(set(int(a) for a in args), reverse=True)
    except ValueError:
        raise InvalidInput("Los índices deben ser números enteros.")
    rows = read_csv(project_path)
    n = len(rows)
    invalidos = [i for i in indices if i < 1 or i > n]
    if invalidos:
        raise InvalidInput(f"Índice(s) inválido(s): {invalidos}. Hay {n} viga(s) (use 1 a {n}).")
    ensure_vu_column(rows)
    eliminadas = [rows[i - 1].get("nombre", f"Viga {i}") for i in sorted(indices)]
    nuevos_rows = [row for i, row in enumerate(rows) if (i + 1) not in indices]
    write_csv(project_path, nuevos_rows, FIELDNAMES_VIGA)
    if len(indices) == 1:
        return f"Viga {indices[0]} ('{eliminadas[0]}') eliminada."
    return f"{len(indices)} viga(s) eliminada(s): {', '.join(eliminadas)}"


def handle_flexion_viga() -> str:
    """cas flexion viga"""
    project_path = get_active_project_path(get_base_path())
    if not project_path:
        raise NoActiveProject("No hay proyecto activo. Use 'cas use <proyecto>'.")
    rows = read_csv(project_path)
    if not rows:
        raise InvalidInput("elements/data.csv está vacío. Añada vigas con fc, fy, b, h, rec, Mu")
    required = ("fc", "fy", "b", "h", "rec", "Mu")
    for row in rows:
        missing = [k for k in required if k not in row or row[k] == ""]
        if missing:
            raise InvalidInput(f"Faltan columnas en data.csv: {missing}")
    data = {"vigas": rows}
    result = run("flexion", "viga", data)
    resultados = result.get("resultados", [])
    out_path = write_results_csv(project_path, "flexion_viga.csv", resultados)
    return f"Flexión calculada: {len(resultados)} viga(s).\nResultados: {out_path}"


def handle_list_vigas() -> str:
    """cas list vigas"""
    project_path = get_active_project_path(get_base_path())
    if not project_path:
        raise NoActiveProject("No hay proyecto activo. Use 'cas use <proyecto>'.")
    rows = read_csv(project_path)
    if not rows:
        raise InvalidInput(
            "No hay vigas. Use 'cas add viga <nombre> <fc> <fy> <b> <h> <rec> <Mu> [Vu]'."
        )
    ensure_vu_column(rows)
    for i, row in enumerate(rows):
        row["N"] = str(i + 1)
    cols = ["N", "nombre", "fc", "fy", "b", "h", "rec", "Mu", "Vu"]
    return "Vigas del proyecto\n\n" + format_table(rows, columns=cols, header_map=VIGAS_HEADER_MAP)


def handle_results_flexion() -> str:
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


def handle_cortante_viga() -> str:
    """cas cortante viga"""
    project_path = get_active_project_path(get_base_path())
    if not project_path:
        raise NoActiveProject("No hay proyecto activo. Use 'cas use <proyecto>'.")
    rows = read_csv(project_path)
    if not rows:
        raise InvalidInput("elements/data.csv está vacío. Añada vigas con fc, fy, b, h, rec, Vu")
    required = ("fc", "fy", "b", "h", "rec")
    for row in rows:
        missing = [k for k in required if k not in row or row[k] == ""]
        if missing:
            raise InvalidInput(f"Faltan columnas en data.csv: {missing}")
    ensure_vu_column(rows)
    data = {"vigas": rows}
    result = run("cortante", "viga", data)
    resultados = result.get("resultados", [])
    out_path = write_results_csv(project_path, "cortante_viga.csv", resultados)
    return f"Cortante calculada: {len(resultados)} viga(s).\nResultados: {out_path}"


def handle_results_cortante() -> str:
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
