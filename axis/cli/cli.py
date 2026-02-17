"""CLI minimalista: cas <scope> <operation>. Flujo estilo Cursor CLI."""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Comandos que cierran el REPL
_REPL_EXIT = frozenset({"exit", "quit", "q"})

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.layout.controls import UIContent
from prompt_toolkit.layout.menus import CompletionsMenuControl
from prompt_toolkit.shortcuts import CompleteStyle
from prompt_toolkit.styles import Style

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


def _handle_sessions_ls() -> str:
    """cas sessions ls - listar proyectos/sesiones (estilo Cursor)"""
    return _handle_list_projects()


def _handle_resume(args: list[str]) -> str:
    """cas resume [project] - reanudar sesión (estilo Cursor)"""
    if len(args) >= 1:
        return _handle_use(args)
    active = get_active_project(_get_base_path())
    if not active:
        raise NoActiveProject(
            "No hay sesión para reanudar. Use 'cas use <proyecto>' o 'cas new <proyecto>'."
        )
    return f"Sesión activa: {active}\nRuta: {get_active_project_path(_get_base_path())}"


def _get_help_text(topic: str | None = None) -> str:
    """Texto de ayuda general o por comando."""
    help_map = {
        "new": "cas new <project>\n  Crear y activar un nuevo proyecto.",
        "use": "cas use <project>\n  Activar un proyecto existente.",
        "sessions": "cas sessions ls\n  Listar todos los proyectos (sesiones disponibles).",
        "resume": "cas resume [project]\n  Reanudar sesión. Sin args: muestra la actual. Con proyecto: la activa.",
        "tree": "cas tree\n  Mostrar estructura del proyecto actual.",
        "info": "cas info\n  Información del proyecto activo.",
        "add": "cas add viga <nombre> <fc> <fy> <b> <h> <rec> <Mu> [Vu]\n  Añadir una viga al proyecto activo.",
        "list": "cas list vigas\n  Ver todas las vigas (datos de entrada).",
        "edit": (
            "cas edit viga <i> <param> <valor>  - Editar un parámetro\n"
            "cas edit viga <i> <nombre> <fc> <fy> <b> <h> <rec> <Mu> [Vu]  - Editar toda la viga\n"
            "cas edit columna <param> <valor> [i1 i2 ...]  - Editar columna en varias vigas"
        ),
        "delete": "cas delete viga <i> [i2 i3 ...]\n  Eliminar viga(s) por índice.",
        "flexion": "cas flexion viga\n  Diseño por flexión de vigas (usa elements/data.csv).",
        "results": "cas results flexion | cas results cortante\n  Ver resultados en tabla.",
        "cortante": "cas cortante viga\n  Diseño por cortante de vigas.",
        "clear": "clear | cls\n  Limpiar la pantalla del REPL (solo en modo interactivo).",
    }
    if topic:
        t = topic.lower()
        if t in help_map:
            return help_map[t]
        return f"Comando desconocido: {topic}\n\nComandos: {', '.join(help_map)}"
    # Ayuda general
    lines = [
        "CAS - Motor de diseño estructural",
        "",
        "Uso: cas <comando> [args]",
        "     cas                    Entrar en modo interactivo (REPL)",
        "",
        "Proyectos y sesiones:",
        "  new <project>             Crear y activar proyecto",
        "  use <project>             Activar proyecto",
        "  sessions ls               Listar proyectos (sesiones)",
        "  resume [project]          Reanudar sesión actual o activar otra",
        "  tree                      Estructura del proyecto",
        "  info                      Proyecto activo",
        "",
        "Vigas:",
        "  add viga <nombre> <fc> <fy> <b> <h> <rec> <Mu> [Vu]",
        "  list vigas                Ver vigas",
        "  edit viga <i> <param> <valor>",
        "  edit columna <param> <valor> [i1 i2 ...]",
        "  delete viga <i> [i2 i3 ...]",
        "",
        "Cálculos:",
        "  flexion viga              Diseño por flexión",
        "  cortante viga             Diseño por cortante",
        "  results flexion           Ver resultados flexión",
        "  results cortante          Ver resultados cortante",
        "",
        "REPL: clear, cls            Limpiar pantalla",
        "",
        "Ayuda: cas help [comando]",
    ]
    return "\n".join(lines)


def _handle_help(args: list[str]) -> str:
    """cas help [command]"""
    topic = args[0] if args else None
    return _get_help_text(topic)


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

# Flexión: títulos mínimos con unidades
_FLEXION_HEADER_MAP = {
    "N": "Nº",
    "nombre": "Nombre",
    "Mu": "Mu\n(Tn-m)",
    "As": "As\n(cm²)",
    "As'": "As'\n(cm²)",
    "Asmin": "Asmin\n(cm²)",
    "Asmax": "Asmax\n(cm²)",
    "As_colocar": "As col.\n(cm²)",
    "As_prima_colocar": "As' col.\n(cm²)",
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


def _get_prompt() -> str:
    """Genera el prompt del REPL (estilo Cursor: →)."""
    try:
        arrow = "→" if sys.stdout.encoding and "utf" in sys.stdout.encoding.lower() else ">"
    except Exception:
        arrow = ">"
    active = get_active_project(_get_base_path())
    if active:
        return f"{arrow} CAS ({active}) "
    return f"{arrow} "


# Comandos /: (texto, display Cursor-style, descripción)
# Formato display: /comando [params] como en la imagen Cursor
_SLASH_COMMANDS = [
    ("help", "/help", "Ayuda general o por comando"),
    ("new ", "/new <project>", "Crear y activar proyecto"),
    ("use ", "/use <project>", "Activar proyecto"),
    ("sessions ls", "/sessions ls", "Listar proyectos (sesiones)"),
    ("resume ", "/resume [project]", "Reanudar sesión o activar otra"),
    ("tree", "/tree", "Estructura del proyecto"),
    ("info", "/info", "Proyecto activo"),
    ("add viga ", "/add viga <...>", "Añadir viga: nombre fc fy b h rec Mu [Vu]"),
    ("list vigas", "/list vigas", "Ver vigas del proyecto"),
    ("edit viga ", "/edit viga <i> <param> <valor>", "Editar viga por índice"),
    ("edit columna ", "/edit columna <param> <valor> [i1 i2 ...]", "Editar columna"),
    ("delete viga ", "/delete viga <i> [i2 i3 ...]", "Eliminar viga(s)"),
    ("flexion viga", "/flexion viga", "Diseño por flexión"),
    ("cortante viga", "/cortante viga", "Diseño por cortante"),
    ("results flexion", "/results flexion", "Ver resultados flexión"),
    ("results cortante", "/results cortante", "Ver resultados cortante"),
    ("clear", "/clear", "Limpiar pantalla del REPL"),
    ("exit", "/exit", "Salir del REPL"),
]

# Tema transparente: menú con fondo del terminal (bg:default), sin recuadro.
_CURSOR_STYLE = Style.from_dict({
    "": "#cccccc",
    "completion-menu": "#cccccc bg:default",
    "completion-menu.completion": "#cccccc bg:default",
    "completion-menu.completion.current": "#ffffff bold noreverse bg:default",
    "completion-menu.meta.completion": "#888888 bg:default",
    "completion-menu.meta.completion.current": "#ffffff bold noreverse bg:default",
    "scrollbar.background": "bg:default",
    "scrollbar.button": "bg:default",
})


def _menu_bullet() -> str:
    """Viñeta para cada comando (estilo Cursor: flecha pequeña al costado)."""
    try:
        enc = (sys.stdout.encoding or "").lower()
        return "→ " if "utf" in enc else "> "
    except Exception:
        return "> "


class _SlashCompleter(Completer):
    """Completer para /: menú vertical estilo Cursor (descripción al costado, viñeta)."""

    def get_completions(self, document, complete_event):
        text = document.text.strip()
        if not text.startswith("/") and not text.startswith("／"):
            return
        frag = text[1:].strip()
        for insert_text, display_text, desc in _SLASH_COMMANDS:
            if frag and not insert_text.strip().lower().startswith(frag.lower()):
                continue
            # Display con viñeta: "→ /help" (estilo Cursor)
            display_with_bullet = f"{_menu_bullet()}{display_text}"
            yield Completion(
                insert_text,
                start_position=-len(text),
                display=display_with_bullet,
                display_meta=desc,
                selected_style="#ffffff bold",
            )


def _clear_repl_screen() -> None:
    """Limpia la pantalla del REPL (cross-platform)."""
    if sys.platform == "win32":
        os.system("cls")
    else:
        os.system("clear")


def _get_slash_commands_text() -> str:
    """Lista formateada de comandos / (estilo Cursor CLI)."""
    lines = ["\nComandos disponibles:\n"]
    for _, display_text, desc in _SLASH_COMMANDS:
        lines.append(f"  {display_text:<35} {desc}")
    return "\n".join(lines) + "\n"


def _run_repl() -> None:
    """Modo interactivo REPL con menú / y flechas (estilo Cursor CLI)."""
    # Ocultar cursor en el menú de completado para que no aparezca el recuadro blanco
    # sobre el comando seleccionado; solo se resaltan las letras.
    _original_create_content = CompletionsMenuControl.create_content

    def _create_content_no_cursor(self, width: int, height: int) -> UIContent:
        content = _original_create_content(self, width, height)
        if content.line_count:
            return UIContent(
                get_line=content.get_line,
                line_count=content.line_count,
                cursor_position=content.cursor_position,
                menu_position=content.menu_position,
                show_cursor=False,
            )
        return content

    CompletionsMenuControl.create_content = _create_content_no_cursor
    try:
        _run_repl_loop()
    finally:
        CompletionsMenuControl.create_content = _original_create_content


def _run_repl_loop() -> None:
    """Bucle principal del REPL (llamado desde _run_repl)."""
    print("CAS - Motor de diseño estructural")
    print("Modo interactivo. Escriba / para ver comandos (navegue con flechas), 'exit' para salir.\n")
    session = PromptSession(
        completer=_SlashCompleter(),
        complete_while_typing=True,
        complete_style=CompleteStyle.COLUMN,
        enable_history_search=False,
        reserve_space_for_menu=0,
        show_frame=False,
        style=_CURSOR_STYLE,
        bottom_toolbar=None,
    )
    while True:
        try:
            line = session.prompt(_get_prompt()).strip()
        except EOFError:
            print()
            break
        if not line:
            continue
        # / solo sin selección → no ejecutar
        if line.strip() in ("/", "／"):
            continue
        # /comando → ejecutar (quitar /)
        if line.startswith("/") or line.startswith("／"):
            line = line[1:].strip()
            if not line:
                continue
        tokens = line.split()
        cmd = tokens[0].lower()
        if cmd in _REPL_EXIT:
            break
        if cmd in ("clear", "cls"):
            _clear_repl_screen()
            continue
        argv = ["cas"] + tokens
        try:
            output = parse_and_execute(argv)
            print(output)
        except (
            ProjectNotFound,
            NoActiveProject,
            OperationNotRegistered,
            InvalidInput,
        ) as e:
            print(f"Error: {e}", file=sys.stderr)


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
    if scope == "help":
        return _handle_help(args[1:])
    if scope == "sessions" and len(args) > 1 and args[1].lower() == "ls":
        return _handle_sessions_ls()
    if scope == "resume":
        return _handle_resume(args[1:])
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
        if len(sys.argv) == 1:
            _run_repl()
            return 0
        if len(sys.argv) == 2 and sys.argv[1].lower() in ("-h", "--help"):
            print(_get_help_text())
            return 0
        # cas / → mostrar comandos slash (funciona fuera del REPL)
        if len(sys.argv) == 2 and sys.argv[1].strip() in ("/", "／"):
            print(_get_slash_commands_text(), flush=True)
            return 0
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
