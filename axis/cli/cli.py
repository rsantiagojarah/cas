"""CLI minimalista: cas <scope> <operation>. Flujo estilo Cursor CLI. Reglas: ≤200 líneas, ≤150 chars."""

from __future__ import annotations

import sys

from axis.core.context import is_direct_calculation_mode
from axis.core.exceptions import (
    ProjectNotFound,
    NoActiveProject,
    OperationNotRegistered,
    InvalidInput,
)
from axis.engine.engine import run

from axis.cli.handlers import (
    handle_new,
    handle_use,
    handle_tree,
    handle_info,
    handle_help,
    handle_list_projects,
    handle_sessions_ls,
    handle_resume,
    handle_add_viga,
    handle_edit_viga,
    handle_edit_columna,
    handle_delete_viga,
    handle_flexion_viga,
    handle_list_vigas,
    handle_results_flexion,
    handle_cortante_viga,
    handle_results_cortante,
)
from axis.cli.sismo_handlers import handle_sismo
from axis.cli.repl import run_repl, get_slash_commands_text
from axis.cli.help_text import get_help_text


def parse_and_execute(argv: list[str]) -> str:
    """Parsea argumentos y ejecuta el comando correspondiente."""
    args = argv[1:] if len(argv) > 1 else []
    if not args:
        return get_help_text()
    scope = args[0].lower()
    if scope == "new":
        return handle_new(args[1:])
    if scope == "use":
        return handle_use(args[1:])
    if scope == "tree":
        return handle_tree()
    if scope == "info":
        return handle_info()
    if scope == "list-projects":
        return handle_list_projects()
    if scope == "help":
        return handle_help(args[1:])
    if scope == "sessions" and len(args) > 1 and args[1].lower() == "ls":
        return handle_sessions_ls()
    if scope == "resume":
        return handle_resume(args[1:])
    if scope == "add" and len(args) > 1 and args[1].lower() == "viga":
        return handle_add_viga(args[2:])
    if scope == "list" and len(args) > 1 and args[1].lower() == "vigas":
        return handle_list_vigas()
    if scope == "edit" and len(args) > 1 and args[1].lower() == "viga":
        return handle_edit_viga(args[2:])
    if scope == "edit" and len(args) > 1 and args[1].lower() == "columna":
        return handle_edit_columna(args[2:])
    if scope == "delete" and len(args) > 1 and args[1].lower() == "viga":
        return handle_delete_viga(args[2:])
    if scope == "flexion" and len(args) > 1 and args[1].lower() == "viga":
        return handle_flexion_viga()
    if scope == "results" and len(args) > 1 and args[1].lower() == "flexion":
        return handle_results_flexion()
    if scope == "cortante" and len(args) > 1 and args[1].lower() == "viga":
        return handle_cortante_viga()
    if scope == "results" and len(args) > 1 and args[1].lower() == "cortante":
        return handle_results_cortante()
    if scope == "sismo":
        return handle_sismo(args[1:])
    if is_direct_calculation_mode(args):
        operation = args[1] if len(args) > 1 else ""
        return str(run(scope, operation, {}))
    raise InvalidInput(f"Comando desconocido: {scope}")


def main() -> int:
    """Punto de entrada del CLI."""
    try:
        if len(sys.argv) == 1:
            run_repl(parse_and_execute)
            return 0
        if len(sys.argv) == 2 and sys.argv[1].lower() in ("-h", "--help"):
            print(get_help_text())
            return 0
        if len(sys.argv) == 2 and sys.argv[1].strip() in ("/", "／"):
            print(get_slash_commands_text(), flush=True)
            return 0
        print(parse_and_execute(sys.argv))
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
