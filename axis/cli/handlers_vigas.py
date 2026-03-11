"""Handlers CLI: vigas (add, edit, delete, list). Reglas: <=200 lineas, <=150 chars."""

from __future__ import annotations

from axis.core.exceptions import NoActiveProject, InvalidInput
from axis.core.project import get_active_project_path
from axis.core.database import read_csv, write_csv
from axis.cli.tables import format_table, VIGAS_HEADER_MAP
from axis.cli.handlers import get_base_path

PARAMS_VIGA = ("nombre", "fc", "fy", "b", "h", "rec", "Mu", "Vu")


def ensure_vu_column(rows: list[dict]) -> None:
    for row in rows:
        if "Vu" not in row or row["Vu"] == "":
            row["Vu"] = "0"


def _parse_indices(args: list[str], n: int) -> list[int]:
    try:
        indices = sorted(set(int(a) for a in args))
    except ValueError:
        raise InvalidInput("Los indices deben ser numeros enteros.")
    invalidos = [i for i in indices if i < 1 or i > n]
    if invalidos:
        raise InvalidInput(f"Indice(s) invalido(s): {invalidos}. Hay {n} viga(s).")
    return indices


def handle_add_viga(args: list[str]) -> str:
    project_path = get_active_project_path(get_base_path())
    if not project_path:
        raise NoActiveProject("No hay proyecto activo. Use 'cas use <proyecto>'.")
    if len(args) < 7:
        raise InvalidInput("Uso: cas add viga <nombre> <fc> <fy> <b> <h> <rec> <Mu> [Vu]")
    nombre = args[0]
    nueva_fila = {"nombre": nombre, "fc": args[1], "fy": args[2], "b": args[3], "h": args[4],
                  "rec": args[5], "Mu": args[6], "Vu": args[7] if len(args) > 7 else "0"}
    rows = read_csv(project_path, "vigas")
    ensure_vu_column(rows)
    for i, row in enumerate(rows):
        row["nombre"] = row.get("nombre") or f"Viga {i + 1}"
    rows.append(nueva_fila)
    write_csv(project_path, rows, "vigas")
    return f"Viga '{nombre}' anadida correctamente."


def handle_edit_viga(args: list[str]) -> str:
    project_path = get_active_project_path(get_base_path())
    if not project_path:
        raise NoActiveProject("No hay proyecto activo. Use 'cas use <proyecto>'.")
    if len(args) < 3:
        raise InvalidInput("Editar: cas edit viga <indice> <param> <valor> | <indice> <nombre> ...")
    try:
        idx = int(args[0])
    except ValueError:
        raise InvalidInput("El indice debe ser un numero entero.")
    rows = read_csv(project_path, "vigas")
    if idx < 1 or idx > len(rows):
        raise InvalidInput(f"Indice {idx} invalido. Hay {len(rows)} viga(s).")
    if len(args) == 3:
        param = args[1].lower()
        if param == "mu":
            param = "Mu"
        if param == "vu":
            param = "Vu"
        if param not in PARAMS_VIGA:
            raise InvalidInput(f"Parametro invalido. Use: {', '.join(PARAMS_VIGA)}")
        ensure_vu_column(rows)
        rows[idx - 1][param] = args[2]
    else:
        if len(args) < 9:
            raise InvalidInput("Edicion completa: cas edit viga <i> <nombre> <fc> <fy> <b> <h> <rec> <Mu> <Vu>")
        rows[idx - 1] = {"nombre": args[1], "fc": args[2], "fy": args[3], "b": args[4],
                         "h": args[5], "rec": args[6], "Mu": args[7], "Vu": args[8]}
    write_csv(project_path, rows, "vigas")
    return f"Viga {idx} actualizada."


def handle_edit_columna(args: list[str]) -> str:
    project_path = get_active_project_path(get_base_path())
    if not project_path:
        raise NoActiveProject("No hay proyecto activo. Use 'cas use <proyecto>'.")
    if len(args) < 2:
        raise InvalidInput("Uso: cas edit columna <param> <valor> [indices...]")
    param = args[0].lower()
    if param == "mu":
        param = "Mu"
    if param == "vu":
        param = "Vu"
    if param not in PARAMS_VIGA:
        raise InvalidInput(f"Parametro invalido. Use: {', '.join(PARAMS_VIGA)}")
    valor = args[1]
    rows = read_csv(project_path, "vigas")
    n = len(rows)
    indices = list(range(1, n + 1)) if len(args) == 2 else _parse_indices(args[2:], n)
    ensure_vu_column(rows)
    for i in indices:
        rows[i - 1][param] = valor
    write_csv(project_path, rows, "vigas")
    if len(indices) == n:
        return f"Columna '{param}' actualizada en las {n} viga(s)."
    return f"Columna '{param}' actualizada en {len(indices)} viga(s): {indices}."


def handle_delete_viga(args: list[str]) -> str:
    project_path = get_active_project_path(get_base_path())
    if not project_path:
        raise NoActiveProject("No hay proyecto activo. Use 'cas use <proyecto>'.")
    if len(args) < 1:
        raise InvalidInput("Uso: cas delete viga <indice> [indice2 ...]")
    try:
        indices = sorted(set(int(a) for a in args), reverse=True)
    except ValueError:
        raise InvalidInput("Los indices deben ser numeros enteros.")
    rows = read_csv(project_path, "vigas")
    n = len(rows)
    invalidos = [i for i in indices if i < 1 or i > n]
    if invalidos:
        raise InvalidInput(f"Indice(s) invalido(s): {invalidos}. Hay {n} viga(s).")
    ensure_vu_column(rows)
    eliminadas = [rows[i - 1].get("nombre", f"Viga {i}") for i in sorted(indices)]
    nuevos = [row for i, row in enumerate(rows) if (i + 1) not in indices]
    write_csv(project_path, nuevos, "vigas")
    if len(indices) == 1:
        return f"Viga {indices[0]} ('{eliminadas[0]}') eliminada."
    return f"{len(indices)} viga(s) eliminada(s): {', '.join(eliminadas)}"


def handle_list_vigas(args: list[str]) -> str:
    project_path = get_active_project_path(get_base_path())
    if not project_path:
        raise NoActiveProject("No hay proyecto activo. Use 'cas use <proyecto>'.")
    rows = read_csv(project_path, "vigas")
    if not rows:
        raise InvalidInput("No hay vigas. Use 'cas add viga <nombre> <fc> <fy> <b> <h> <rec> <Mu> [Vu]'.")
    ensure_vu_column(rows)
    for i, row in enumerate(rows):
        row["N"] = str(i + 1)
    cols = ["N", "nombre", "fc", "fy", "b", "h", "rec", "Mu", "Vu"]
    return "Vigas del proyecto\n\n" + format_table(rows, columns=cols, header_map=VIGAS_HEADER_MAP)
