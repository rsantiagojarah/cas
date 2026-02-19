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
    "sismo": (
        "cas sismo etapa1 <zona> <perfil>  - Peligro sísmico (C vs T)\n"
        "cas sismo etapa2 <categoria> <sistema> <Ia> <Ip>  - Coeficiente R\n"
        "cas sismo etapa3  - Análisis ETABS (periodo, masa, peso, cortantes)\n"
        "cas sismo etapa4 <r0> <material> [Vx Vy] [h [Δa Δb]]  - Validación (sistema, drift, separación)\n"
        "cas sismo separacion <h> [Δa Δb]  - Paso 14: separación de edificios (s = 0.006·h ≥ 0.03)"
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
    "  flexion viga              Diseño por flexión",
    "  cortante viga             Diseño por cortante",
    "  results flexion           Ver resultados flexión",
    "  results cortante          Ver resultados cortante",
    "",
    "Sismo E.030:",
    "  sismo etapa1 <zona> <perfil>",
    "  sismo etapa2 <categoria> <sistema> <Ia> <Ip>",
    "  sismo etapa3              (ETABS)",
    "  sismo etapa4 <r0> <material> [Vx Vy] [h [Δa Δb]]",
    "  sismo separacion <h> [Δa Δb]",
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
