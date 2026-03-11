"""Textos de ayuda del CLI. Reglas: ≤200 líneas, ≤150 chars/línea."""

from __future__ import annotations

HELP_MAP = {
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
    "muro": (
        "cas muro nucleo <nombre_muro> <L> <fy> <nivel> <hm> <Mu> [phi]\n"
        "  Predimensionamiento de acero en núcleos de muros de concreto armado (ingreso manual).\n"
        "  Guarda cada muro en results/muros_nucleo/<nombre_muro>.csv.\n"
        "cas muro etabs <nombre_muro> <L> <fy> <pier_name> [phi]\n"
        "  Predimensiona leyendo momentos M3 desde la tabla 'Pier Forces' de ETABS.\n"
        "cas muro list\n"
        "  Lista los muros predimensionados.\n"
        "cas muro delete <nombre_muro>\n"
        "  Elimina los resultados de un muro."
    ),
    "sismo": (
        "cas sismo <sentido> Z U perfil R Ia Ip Material  - Análisis E.030\n"
        "  sentido=X|Y, Z=1-4, U=A-D, perfil=S0-S4, R=8|7|6|3, Material=concreto|acero|albañileria\n"
        "  Ej: cas sismo X 3 C S2 8 1 1 concreto.\n"
        "  Rapido: cas sismo rapido X 3 C S2 8 concreto rb,masa tors\n"
        "  Irregularidades: cas sismo irregularidades | cas sismo irregularidades calcular rb tors"
    ),
    "irregular": (
        "cas irregular <tipo> X|Y <datos...>  - Verificacion E.030 (Tablas 8 y 9)\n"
        "  Sentido X o Y obligatorio. Tipos: rigidez, resistencia, discontinuidad, etc.\n"
        "  Persistencia: list | show [id] | delete <id> | edit <id> <tipo> X|Y datos...\n"
        "  Ej: cas irregular rigidez X 500 800 750 | cas irregular list"
    ),
    "clear": "clear | cls\n  Limpiar la pantalla del REPL (solo en modo interactivo).",
}

HELP_LINES = [
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
    "  flexion viga                    Diseño por flexión",
    "  cortante viga                   Diseño por cortante",
    "  muro nucleo <nombre> <L> <fy> <nivel> <hm> <Mu> [phi]",
    "                                  Predimensionamiento núcleo de muro (manual)",
    "  muro etabs <nombre> <L> <fy> <pier_name> [phi]",
    "                                  Predimensionamiento desde ETABS (Pier Forces)",
    "  muro list                        Listar muros predimensionados",
    "  muro delete <nombre>             Borrar resultados de un muro",
    "  results flexion                  Ver resultados flexión",
    "  results cortante                 Ver resultados cortante",
    "",
    "Irregularidades E.030:",
    "  irregular <tipo> X|Y datos   Verificacion por sentido (rigidez, resistencia, etc.)",
    "  irregular list [tipo] [X|Y]  Listar analisis guardados",
    "  irregular show [id]          Mostrar analisis",
    "  irregular delete <id>        Borrar analisis",
    "  irregular edit <id> tipo X|Y  Editar analisis",
    "",
    "Sismo E.030:",
    "  sismo <sentido> Z U perfil R Ia Ip Material     Ej: X 3 C S2 8 1 1 concreto",
    "  sismo rapido <sentido> Z U perfil R Material <cod_altura> <cod_planta>",
    "  sismo irregularidades                           Ver codigos Ia/Ip (tablas 8 y 9)",
    "  sismo results                                  Ver resultados",
    "  sismo separacion <h> [da db]                    Separación edificios",
    "",
    "REPL: clear, cls            Limpiar pantalla",
    "",
    "Ayuda: cas help [comando]",
]


def get_help_text(topic: str | None = None) -> str:
    """Texto de ayuda general o por comando."""
    if topic:
        t = topic.lower()
        if t in HELP_MAP:
            return HELP_MAP[t]
        return f"Comando desconocido: {topic}\n\nComandos: {', '.join(HELP_MAP)}"
    return "\n".join(HELP_LINES)
