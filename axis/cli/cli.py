"""CLI minimalista: cas <scope> <operation>. Router declarativo. Reglas: ≤200 líneas, ≤150 chars."""

from __future__ import annotations

import sys

from axis.core.exceptions import (
    ProjectNotFound,
    NoActiveProject,
    OperationNotRegistered,
    InvalidInput,
)

from axis.cli.handlers import (
    handle_new,
    handle_use,
    handle_tree,
    handle_info,
    handle_help,
    handle_list_projects,
    handle_sessions_ls,
    handle_resume,
)
from axis.cli.handlers_vigas import (
    handle_add_viga,
    handle_edit_viga,
    handle_edit_columna,
    handle_delete_viga,
    handle_list_vigas,
)
from axis.cli.handlers_diseno import (
    handle_flexion_viga,
    handle_results_flexion,
    handle_cortante_viga,
    handle_results_cortante,
)
from axis.cli.sismo_handlers import handle_sismo
from axis.cli.handlers_irregular import handle_irregular
from axis.cli.handlers_muros import (
    handle_muro_nucleo,
    handle_muro_list,
    handle_muro_delete,
    handle_muro_etabs,
)
from axis.cli.router import dispatch
from axis.cli.repl import run_repl, get_slash_commands_text
from axis.cli.help_text import get_help_text

HANDLERS = {
    "new": handle_new,
    "use": handle_use,
    "tree": handle_tree,
    "info": handle_info,
    "list-projects": handle_list_projects,
    "help": handle_help,
    ("sessions", "ls"): handle_sessions_ls,
    "resume": handle_resume,
    ("add", "viga"): handle_add_viga,
    ("list", "vigas"): handle_list_vigas,
    ("edit", "viga"): handle_edit_viga,
    ("edit", "columna"): handle_edit_columna,
    ("delete", "viga"): handle_delete_viga,
    ("flexion", "viga"): handle_flexion_viga,
    ("results", "flexion"): handle_results_flexion,
    ("cortante", "viga"): handle_cortante_viga,
    ("results", "cortante"): handle_results_cortante,
    "sismo": handle_sismo,
    "irregular": handle_irregular,
    ("muro", "nucleo"): handle_muro_nucleo,
    ("muro", "list"): handle_muro_list,
    ("muro", "delete"): handle_muro_delete,
    ("muro", "etabs"): handle_muro_etabs,
}


def parse_and_execute(argv: list[str]) -> str:
    """Parsea argumentos y ejecuta el comando vía router declarativo."""
    args = argv[1:] if len(argv) > 1 else []
    return dispatch(args, HANDLERS)


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
