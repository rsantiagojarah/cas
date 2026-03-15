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
    handle_flexion_losa,
    handle_losa_define,
    handle_losa_list,
    handle_losa_delete,
    handle_losa_momento,
    handle_losa_cortante,
    handle_cortante_losa,
    handle_viga_define,
    handle_viga_list,
    handle_viga_delete,
    handle_viga_momento,
    handle_viga_cortante,
    handle_inercia_fisurada,
    handle_results_flexion,
    handle_cortante_viga,
    handle_results_cortante,
)
from axis.cli.handlers_inercia import (
    handle_ie_define,
    handle_ie_list,
    handle_ie_delete,
    handle_ie_seccion,
    handle_ie_calcular,
    handle_ie_lambda,
)
from axis.cli.sismo_handlers import handle_sismo
from axis.cli.handlers_irregular import handle_irregular
from axis.cli.handlers_diagramas import (
    handle_diagrama_add,
    handle_diagrama_list,
    handle_diagrama_plot,
    handle_diagrama_check_pm,
)
from axis.cli.handlers_muros import (
    handle_muro_nucleo,
    handle_muro_list,
    handle_muro_delete,
    handle_muro_etabs,
    handle_muro_add,
    handle_muro_list_data,
    handle_muro_delete_data,
    handle_muro_diseno,
    handle_muro_results,
    handle_muro_report,
    handle_muro_results_delete,
    handle_muro_def,
    handle_muro_piso,
    handle_muro_pisos,
    handle_muro_del_piso,
    handle_muro_asignar,
    handle_muro_multi,
    handle_muro_multi_results,
    handle_muro_multi_delete,
    handle_muro_multi_report,
    handle_muro_etabs_diseno,
    handle_muro_etabs_import,
)
from axis.cli.handlers_columnas import (
    handle_columna_props,
    handle_columna_props_list,
    handle_columna_props_remove,
    handle_columna_esfuerzos,
    handle_columna_esfuerzos_list,
    handle_columna_story_forces,
    handle_columna_drifts,
    handle_columna_alturas,
    handle_columna_factor_r,
    handle_columna_asignar,
    handle_columna_diagrama,
    handle_columna_q,
    handle_columna_esbeltez,
    handle_columna_segundo_orden,
    handle_columna_cm,
    handle_columna_delta,
    handle_columna_esfuerzos_finales,
    handle_columna_mn,
    handle_columna_estados,
    handle_columna_verificacion,
    handle_columna_resumen,
    handle_columna_etabs_import,
    handle_columna_diseno,
    handle_columna_etabs_diseno,
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
    ("diagrama", "add"): handle_diagrama_add,
    ("diagrama", "list"): handle_diagrama_list,
    ("diagrama", "plot"): handle_diagrama_plot,
    ("diagrama", "check-pm"): handle_diagrama_check_pm,
    ("add", "viga"): handle_add_viga,
    ("list", "vigas"): handle_list_vigas,
    ("edit", "viga"): handle_edit_viga,
    ("edit", "columna"): handle_edit_columna,
    ("delete", "viga"): handle_delete_viga,
    ("flexion", "viga"): handle_flexion_viga,
    ("flexion", "losa"): handle_flexion_losa,
    ("losa", "define"): handle_losa_define,
    ("losa", "list"): handle_losa_list,
    ("losa", "delete"): handle_losa_delete,
    ("losa", "momento"): handle_losa_momento,
    ("losa", "cortante"): handle_losa_cortante,
    ("cortante", "losa"): handle_cortante_losa,
    ("viga", "define"): handle_viga_define,
    ("viga", "list"): handle_viga_list,
    ("viga", "delete"): handle_viga_delete,
    ("viga", "momento"): handle_viga_momento,
    ("viga", "cortante"): handle_viga_cortante,
    ("inercia", "fisurada"): handle_inercia_fisurada,
    ("inercia", "define"): handle_ie_define,
    ("inercia", "list"): handle_ie_list,
    ("inercia", "delete"): handle_ie_delete,
    ("inercia", "seccion"): handle_ie_seccion,
    ("inercia", "calcular"): handle_ie_calcular,
    "lambda": handle_ie_lambda,
    ("results", "flexion"): handle_results_flexion,
    ("cortante", "viga"): handle_cortante_viga,
    ("results", "cortante"): handle_results_cortante,
    "sismo": handle_sismo,
    "irregular": handle_irregular,
    ("muro", "nucleo"): handle_muro_nucleo,
    ("muro", "list"): handle_muro_list,
    ("muro", "delete"): handle_muro_delete,
    ("muro", "etabs"): handle_muro_etabs,
    ("muro", "add"): handle_muro_add,
    ("muro", "data"): handle_muro_list_data,
    ("muro", "remove"): handle_muro_delete_data,
    ("muro", "diseno"): handle_muro_diseno,
    ("muro", "results"): handle_muro_results,
    ("muro", "report"): handle_muro_report,
    ("muro", "results-delete"): handle_muro_results_delete,
    ("muro", "def"): handle_muro_def,
    ("muro", "piso"): handle_muro_piso,
    ("muro", "pisos"): handle_muro_pisos,
    ("muro", "del-piso"): handle_muro_del_piso,
    ("muro", "asignar"): handle_muro_asignar,
    ("muro", "multi"): handle_muro_multi,
    ("muro", "multi-results"): handle_muro_multi_results,
    ("muro", "multi-report"): handle_muro_multi_report,
    ("muro", "multi-delete"): handle_muro_multi_delete,
    ("muro", "etabs-diseno"): handle_muro_etabs_diseno,
    ("muro", "etabs-import"): handle_muro_etabs_import,
    # Columnas - Datos
    ("columna", "props"): handle_columna_props,
    ("columna", "props-list"): handle_columna_props_list,
    ("columna", "props-remove"): handle_columna_props_remove,
    ("columna", "esfuerzos"): handle_columna_esfuerzos,
    ("columna", "esfuerzos-list"): handle_columna_esfuerzos_list,
    ("columna", "story-forces"): handle_columna_story_forces,
    ("columna", "drifts"): handle_columna_drifts,
    ("columna", "alturas"): handle_columna_alturas,
    ("columna", "factor-r"): handle_columna_factor_r,
    ("columna", "asignar"): handle_columna_asignar,
    ("columna", "diagrama"): handle_columna_diagrama,
    # Columnas - Análisis (9 pasos)
    ("columna", "q"): handle_columna_q,
    ("columna", "esbeltez"): handle_columna_esbeltez,
    ("columna", "segundo-orden"): handle_columna_segundo_orden,
    ("columna", "cm"): handle_columna_cm,
    ("columna", "delta"): handle_columna_delta,
    ("columna", "esfuerzos-fin"): handle_columna_esfuerzos_finales,
    ("columna", "mn"): handle_columna_mn,
    ("columna", "estados"): handle_columna_estados,
    ("columna", "verificacion"): handle_columna_verificacion,
    ("columna", "resumen"): handle_columna_resumen,
    ("columna", "etabs-import"): handle_columna_etabs_import,
    ("columna", "diseno"): handle_columna_diseno,
    ("columna", "etabs-diseno"): handle_columna_etabs_diseno,
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
