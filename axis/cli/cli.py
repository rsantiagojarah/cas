"""CLI minimalista: axis <scope> <operation>."""

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
from axis.operations import placeholder  # noqa: F401


def _get_base_path() -> Path:
    """Directorio base para proyectos (cwd)."""
    return Path.cwd()


def _handle_new(args: list[str]) -> str:
    """axis new <project>"""
    if len(args) < 1:
        raise InvalidInput("Especifique el nombre del proyecto: axis new <project>")
    name = args[0]
    path = create_project(name, _get_base_path())
    set_active_project(name, _get_base_path())
    return f"Proyecto '{name}' creado y activado.\nRuta: {path}"


def _handle_use(args: list[str]) -> str:
    """axis use <project>"""
    if len(args) < 1:
        raise InvalidInput("Especifique el proyecto: axis use <project>")
    name = args[0]
    set_active_project(name, _get_base_path())
    return f"Proyecto activo: {name}"


def _handle_tree() -> str:
    """axis tree"""
    tree = get_project_tree(_get_base_path())
    return format_tree(tree)


def _handle_info() -> str:
    """axis info"""
    config = get_global_config()
    active = config.get("active_project") or "Ninguno"
    path = config.get("project_path") or "-"
    return f"Proyecto activo: {active}\nRuta: {path}"


def _handle_list_projects() -> str:
    """axis list-projects"""
    projects = list_projects(_get_base_path())
    if not projects:
        return "No hay proyectos. Use 'axis new <project>' para crear uno."
    return "Proyectos:\n  " + "\n  ".join(projects)


def parse_and_execute(argv: list[str]) -> str:
    """Parsea argumentos y ejecuta el comando correspondiente."""
    args = argv[1:] if len(argv) > 1 else []
    if not args:
        return (
            "AXIS - Motor de diseño estructural\n\n"
            "Uso: axis <scope> <operation> [args]\n\n"
            "Comandos base:\n"
            "  axis new <project>     Crear y activar proyecto\n"
            "  axis use <project>     Activar proyecto\n"
            "  axis tree              Mostrar estructura del proyecto\n"
            "  axis info              Información del proyecto activo\n"
            "  axis list-projects     Listar proyectos\n"
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
