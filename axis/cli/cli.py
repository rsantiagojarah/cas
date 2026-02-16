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

from axis.operations import placeholder, flexion, cortante  # noqa: F401


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
    """cas add viga <nombre> <fc> <fy> <b> <h> <rec> <Mu> [Vu]"""
    project_path = get_active_project_path(_get_base_path())
    if not project_path:
        raise NoActiveProject("No hay proyecto activo. Use 'cas use <proyecto>'.")
    if len(args) < 7:
        raise InvalidInput(
            "Uso: cas add viga <nombre> <fc> <fy> <b> <h> <rec> <Mu> [Vu]"
        )
    nombre, fc, fy, b, h, rec, mu = args[0], args[1], args[2], args[3], args[4], args[5], args[6]
    vu = args[7] if len(args) > 7 else "0"
    nueva_fila = {
        "nombre": nombre, "fc": fc, "fy": fy, "b": b, "h": h, "rec": rec, "Mu": mu,
        "Vu": vu
    }
    rows = read_csv(project_path)
    fieldnames = ["nombre", "fc", "fy", "b", "h", "rec", "Mu", "Vu"]
    _ensure_vu_column(rows)
    for i, row in enumerate(rows):
        row["nombre"] = row.get("nombre") or f"Viga {i + 1}"
    rows.append(nueva_fila)
    write_csv(project_path, rows, fieldnames)
    return f"Viga '{nombre}' añadida correctamente."


_PARAMS_VIGA = ("nombre", "fc", "fy", "b", "h", "rec", "Mu", "Vu")
_FIELDNAMES_VIGA = ["nombre", "fc", "fy", "b", "h", "rec", "Mu", "Vu"]


def _ensure_vu_column(rows: list[dict]) -> None:
    """Añade Vu=0 a filas que no lo tienen (compatibilidad)."""
    for row in rows:
        if "Vu" not in row or row["Vu"] == "":
            row["Vu"] = "0"


def _handle_edit_viga(args: list[str]) -> str:
    """cas edit viga <índice> <parámetro> <valor> | cas edit viga <índice> <nombre> <fc> ..."""
    project_path = get_active_project_path(_get_base_path())
    if not project_path:
        raise NoActiveProject("No hay proyecto activo. Use 'cas use <proyecto>'.")
    if len(args) < 3:
        raise InvalidInput(
            "Uso:\n"
            "  Editar un parámetro: cas edit viga <índice> <param> <valor>\n"
            "    Parámetros: nombre, fc, fy, b, h, rec, Mu\n"
            "  Editar todo: cas edit viga <índice> <nombre> <fc> <fy> <b> <h> <rec> <Mu>"
        )
    try:
        idx = int(args[0])
    except ValueError:
        raise InvalidInput("El índice debe ser un número entero.")
    rows = read_csv(project_path)
    if idx < 1 or idx > len(rows):
        raise InvalidInput(
            f"Índice {idx} inválido. Hay {len(rows)} viga(s) (use 1 a {len(rows)})."
        )
    if len(args) == 3:
        param = args[1].lower()
        if param == "mu":
            param = "Mu"
        if param == "vu":
            param = "Vu"
        if param not in _PARAMS_VIGA:
            raise InvalidInput(
                f"Parámetro '{args[1]}' inválido. Use: {', '.join(_PARAMS_VIGA)}"
            )
        _ensure_vu_column(rows)
        rows[idx - 1][param] = args[2]
    else:
        if len(args) < 9:
            raise InvalidInput(
                "Edición completa: cas edit viga <índice> <nombre> <fc> <fy> <b> "
                "<h> <rec> <Mu> <Vu>"
            )
        nombre, fc, fy, b, h, rec, mu, vu = (
            args[1], args[2], args[3], args[4], args[5], args[6], args[7], args[8]
        )
        rows[idx - 1] = {
            "nombre": nombre, "fc": fc, "fy": fy, "b": b, "h": h, "rec": rec,
            "Mu": mu, "Vu": vu
        }
    fieldnames = _FIELDNAMES_VIGA
    write_csv(project_path, rows, fieldnames)
    return f"Viga {idx} actualizada."


def _handle_edit_columna(args: list[str]) -> str:
    """cas edit columna <param> <valor> [índice1 índice2 ...] - editar columna para todas o seleccionadas"""
    project_path = get_active_project_path(_get_base_path())
    if not project_path:
        raise NoActiveProject("No hay proyecto activo. Use 'cas use <proyecto>'.")
    if len(args) < 2:
        raise InvalidInput(
            "Uso: cas edit columna <param> <valor> [índice1 índice2 ...]\n"
            "  Sin índices: aplica a TODAS las vigas.\n"
            "  Con índices: aplica solo a las vigas indicadas.\n"
            "  Parámetros: nombre, fc, fy, b, h, rec, Mu"
        )
    param = args[0].lower()
    if param == "mu":
        param = "Mu"
    if param == "vu":
        param = "Vu"
    if param not in _PARAMS_VIGA:
        raise InvalidInput(
            f"Parámetro '{args[0]}' inválido. Use: {', '.join(_PARAMS_VIGA)}"
        )
    valor = args[1]
    rows = read_csv(project_path)
    n = len(rows)
    if len(args) == 2:
        indices = list(range(1, n + 1))
    else:
        try:
            indices = [int(a) for a in args[2:]]
        except ValueError:
            raise InvalidInput("Los índices deben ser números enteros.")
        indices = sorted(set(indices))
        invalidos = [i for i in indices if i < 1 or i > n]
        if invalidos:
            raise InvalidInput(
                f"Índice(s) inválido(s): {invalidos}. Hay {n} viga(s)."
            )
    _ensure_vu_column(rows)
    for i in indices:
        rows[i - 1][param] = valor
    fieldnames = _FIELDNAMES_VIGA
    write_csv(project_path, rows, fieldnames)
    if len(indices) == n:
        return f"Columna '{param}' actualizada en las {n} viga(s)."
    return f"Columna '{param}' actualizada en {len(indices)} viga(s): {indices}."


def _handle_delete_viga(args: list[str]) -> str:
    """cas delete viga <índice> [índice2 índice3 ...]"""
    project_path = get_active_project_path(_get_base_path())
    if not project_path:
        raise NoActiveProject("No hay proyecto activo. Use 'cas use <proyecto>'.")
    if len(args) < 1:
        raise InvalidInput(
            "Uso: cas delete viga <índice> [índice2 índice3 ...]\n"
            "     Índices: números de fila (1, 2, 3...). Use 'cas list vigas' para ver."
        )
    try:
        indices = [int(a) for a in args]
    except ValueError:
        raise InvalidInput("Los índices deben ser números enteros.")
    indices = sorted(set(indices), reverse=True)
    rows = read_csv(project_path)
    n = len(rows)
    invalidos = [i for i in indices if i < 1 or i > n]
    if invalidos:
        raise InvalidInput(
            f"Índice(s) inválido(s): {invalidos}. Hay {n} viga(s) (use 1 a {n})."
        )
    _ensure_vu_column(rows)
    eliminadas = [rows[i - 1].get("nombre", f"Viga {i}") for i in sorted(indices)]
    nuevos_rows = [row for i, row in enumerate(rows) if (i + 1) not in indices]
    fieldnames = _FIELDNAMES_VIGA
    write_csv(project_path, nuevos_rows, fieldnames)
    if len(indices) == 1:
        return f"Viga {indices[0]} ('{eliminadas[0]}') eliminada."
    return f"{len(indices)} viga(s) eliminada(s): {', '.join(eliminadas)}"


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
    "Vu": "Vu\n(Tn)",
    "fy": "fy\n(kg/cm²)",
    "b": "b\n(cm)",
    "h": "h\n(cm)",
    "rec": "rec\n(cm)",
    "Mu": "Mu\n(Tn-m)",
}

# Cortante: flujo de diseño; fuerzas en Tn (sin d, Vu, Vn_max)
_CORTANTE_HEADER_MAP = {
    "N": "Nº",
    "nombre": "Nombre",
    "Vc": "Vc\n(Tn)",
    "phi_Vc_2": "φ·Vc/2\n(Tn)",
    "Vs_max": "Vs_max\n(Tn)",
    "phi_Vn_max": "φ·Vn_max\n(Tn)",
    "Vs": "Vs\n(Tn)",
    "cumple_Vs_max": "cumple\nVs_max",
    "Av_s": "Av/s\n(cm²/cm)",
    "s_max": "s_max\n(cm)",
    "Av_s_min": "Av/s_min\n(cm²/cm)",
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
    "Asmax": "Asmax\n(cm²)",
    "cumple_Asmin": "cumple\nAsmin",
    "cumple_Asmax": "cumple\nAsmax",
    "Cumple Mcr": "1.2 Mcr",
    "OK": "1.2\nMcr",
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
    cort_map = _CORTANTE_HEADER_MAP
    headers = [
        m.get(c, vigas_map.get(c, flex_map.get(c, cort_map.get(c, c)))) for c in cols
    ]
    def _cell_str(val):
        if val is None or (isinstance(val, str) and val.lower() == "none"):
            return "-"
        if val is True or (isinstance(val, str) and val.lower() == "true"):
            return "Si"
        if val is False or (isinstance(val, str) and val.lower() == "false"):
            return "No"
        return str(val)
    table_rows = [[_cell_str(row.get(c, "")) for c in cols] for row in rows]
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
            "No hay vigas. Use 'cas add viga <nombre> <fc> <fy> <b> <h> <rec> <Mu> [Vu]'."
        )
    _ensure_vu_column(rows)
    for i, row in enumerate(rows):
        row["N"] = str(i + 1)
    cols = ["N", "nombre", "fc", "fy", "b", "h", "rec", "Mu", "Vu"]
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


def _handle_cortante_viga() -> str:
    """cas cortante viga - diseño por cortante desde elements/data.csv"""
    project_path = get_active_project_path(_get_base_path())
    if not project_path:
        raise NoActiveProject("No hay proyecto activo. Use 'cas use <proyecto>'.")
    rows = read_csv(project_path)
    if not rows:
        raise InvalidInput(
            "elements/data.csv está vacío. Añada vigas con fc, fy, b, h, rec, Vu"
        )
    required = ("fc", "fy", "b", "h", "rec")
    for row in rows:
        missing = [k for k in required if k not in row or row[k] == ""]
        if missing:
            raise InvalidInput(f"Faltan columnas en data.csv: {missing}")
    _ensure_vu_column(rows)
    data = {"vigas": rows}
    result = run("cortante", "viga", data)
    resultados = result.get("resultados", [])
    out_path = write_results_csv(project_path, "cortante_viga.csv", resultados)
    return f"Cortante calculada: {len(resultados)} viga(s).\nResultados: {out_path}"


def _handle_results_cortante() -> str:
    """cas results cortante - muestra resultados de cortante en tabla"""
    project_path = get_active_project_path(_get_base_path())
    if not project_path:
        raise NoActiveProject("No hay proyecto activo. Use 'cas use <proyecto>'.")
    rows = read_results_csv(project_path, "cortante_viga.csv")
    if not rows:
        raise InvalidInput(
            "No hay resultados de cortante. Ejecute 'cas cortante viga' primero."
        )
    for i, row in enumerate(rows):
        row["N"] = str(i + 1)
    cols = ["N"] + [k for k in rows[0].keys() if k != "N"]
    return "Cortante\n\n" + _format_table(rows, columns=cols, header_map=_CORTANTE_HEADER_MAP)


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
            "  cas add viga <nombre> <fc> <fy> <b> <h> <rec> <Mu> [Vu]\n"
            "                          Añadir viga al proyecto\n"
            "  cas list vigas          Ver todas las vigas (datos de entrada)\n"
            "  cas edit viga <i> <param> <valor>\n"
            "                          Editar un parámetro de una viga\n"
            "  cas edit viga <i> <nombre> <fc> <fy> <b> <h> <rec> <Mu>\n"
            "                          Editar toda la viga\n"
            "  cas edit columna <param> <valor> [i1 i2 ...]\n"
            "                          Editar columna: todas las vigas o las indicadas\n"
            "  cas delete viga <i> [i2 i3 ...]  Eliminar viga(s) por índice\n"
            "  cas flexion viga        Diseño por flexión de vigas\n"
            "  cas results flexion     Ver resultados de flexión en tabla\n"
            "  cas cortante viga       Diseño por cortante de vigas\n"
            "  cas results cortante    Ver resultados de cortante en tabla\n"
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
    if scope == "edit" and len(args) > 1 and args[1].lower() == "columna":
        return _handle_edit_columna(args[2:])
    if scope == "delete" and len(args) > 1 and args[1].lower() == "viga":
        return _handle_delete_viga(args[2:])
    if scope == "flexion" and len(args) > 1 and args[1].lower() == "viga":
        return _handle_flexion_viga()
    if scope == "results" and len(args) > 1 and args[1].lower() == "flexion":
        return _handle_results_flexion()
    if scope == "cortante" and len(args) > 1 and args[1].lower() == "viga":
        return _handle_cortante_viga()
    if scope == "results" and len(args) > 1 and args[1].lower() == "cortante":
        return _handle_results_cortante()
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
