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
    "flexion": "cas flexion viga | cas flexion losa\n  Diseño por flexión (vigas o losas; losas: cuantía mín. 0.0018).",
    "losa": (
        "cas losa define [nombre] <fc> <fy> <b> <h> <rec>\n"
        "  Definir una losa (varias si les pone nombre; fc/fy kg/cm², b/h/rec cm).\n"
        "cas losa list\n"
        "  Listar losas definidas.\n"
        "cas losa delete <nombre|índice>\n"
        "  Borrar una losa (y sus momentos).\n"
        "cas losa momento add [nombre_losa] <nombre> <Mu>\n"
        "  Añadir momento a la losa.\n"
        "cas losa momento list [nombre_losa] | delete <i>\n"
        "  Listar momentos (opcional por losa) o eliminar uno por índice.\n"
        "cas losa cortante add [nombre_losa] <nombre> <Vu>  |  list [losa]  |  delete <i>\n"
        "  Añadir/listar/eliminar cortantes por losa (Vu en Tn). Luego: cas cortante losa."
    ),
    "results": "cas results flexion [viga|losa] | cas results cortante\n  Ver resultados en tabla.",
    "cortante": "cas cortante viga | cas cortante losa\n  Cortante vigas (estribos) o losas (solo Vu vs phi*Vc).",
    "muro": (
        "cas muro nucleo <nombre_muro> <L> <fy> <nivel> <hm> <Mu> [phi]\n"
        "  Predimensionamiento de acero en núcleos de muros (ingreso manual).\n"
        "cas muro etabs <nombre_muro> <L> <fy> <pier_name> [phi]\n"
        "  Predimensiona leyendo M3 desde ETABS (Pier Forces).\n"
        "cas muro list          Lista muros predimensionados.\n"
        "cas muro delete <nm>   Elimina resultados predimensionamiento.\n"
        "\n"
        "DISEÑO COMPLETO RNE E.060:\n"
        "cas muro add <nombre> <hm> <lm> <t> <fc> <fy> <fyt> <Pu> <Vu> <Mu> [delta_u] [c] [Mn]\n"
        "  Agrega/actualiza datos de muro (hm/lm/t:cm, fc/fy/fyt:kg/cm²,\n"
        "  Pu:Tn, Vu:Tn, Mu:Tn-m, delta_u:cm, c:cm, Mn:Tn-m).\n"
        "cas muro data          Lista muros almacenados para diseño.\n"
        "cas muro remove <nm>   Elimina un muro de datos.\n"
        "cas muro diseno [nombre] [DEFORMACION|ESFUERZO]\n"
        "  Ejecuta diseño completo: espesor, flexión, agrietamiento, corte,\n"
        "  elementos de borde (método auto o manual).\n"
        "cas muro results [nm]          Ver resumen de resultados de diseno.\n"
        "cas muro report [nm] [metodo]  Generar reporte Markdown/Word de diseno (piso unico).\n"
        "cas muro results-delete <nm>   Borrar resultados de diseno (piso unico).\n"
        "\n"
        "DISENO MULTIPISO RNE E.060:\n"
        "cas muro def <nombre> <lm> <t> <fc> <fy> <fyt>\n"
        "  Definir muro (geometria + materiales) para diseno multipiso.\n"
        "cas muro piso <nombre> <N> <hm> <Pu> <Vu> <Mu> [Mn] [c]\n"
        "  Agregar piso (hm:cm, Pu:Tn, Vu:Tn, Mu:Tn-m, Mn:Tn-m, c:cm).\n"
        "cas muro pisos [nombre]   Listar pisos definidos.\n"
        "cas muro del-piso <nm> <N>  Eliminar un piso.\n"
        "cas muro multi <nombre> [DEFORMACION|ESFUERZO] [delta_u] [joint_Av]\n"
        "  Diseno multipiso completo E.060 (borde global con H_total).\n"
        "cas muro multi-results [nm]  Ver resultados multipiso.\n"
        "cas muro etabs-diseno <nombre> <lm> <t> <fc> <fy> <fyt> <pier> [metodo] [du] [Av]\n"
        "  Importar ETABS (Pier Forces + Story Definitions) y diseno multipiso."
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
    "columna": (
        "DISEÑO DE COLUMNAS DE CONCRETO ARMADO (E.060)\n"
        "\n"
        "DATOS DE ENTRADA:\n"
        "cas columna props <Unique_Name> <k> <lu> <Ix> <Iy> <Ag> <Bd> [fc] [fy]\n"
        "  Ec = 15000*sqrt(fc) (E.060). fc por defecto 210. Una inercia: <UN> <k> <lu> <I> <Ag> <Bd> [fc] [fy].\n"
        "cas columna props-list              Listar propiedades.\n"
        "cas columna props-remove <UN>       Borrar propiedades de una columna.\n"
        "cas columna esfuerzos <Story> <UN> <Station> <OC> <ST> <P> <M2> <M3>\n"
        "  Agregar esfuerzo (P:Tn, M2/M3:Tn-m, ST:Max/Min o '-').\n"
        "cas columna esfuerzos-list [UN]     Listar esfuerzos.\n"
        "cas columna story-forces <Story> <OC> <P> <VX> <VY>\n"
        "  Agregar story forces (Tn).\n"
        "cas columna drifts <Story> <OC> <Drift>\n"
        "  Agregar story drift.\n"
        "cas columna alturas <Story> <Height>\n"
        "  Agregar altura de entrepiso (m).\n"
        "cas columna factor-r <R_X> <R_Y>\n"
        "  Configurar factor de reduccion R.\n"
        "cas diagrama add <nombre> <nominal|ultimo> [archivo]\n"
        "  Cargar diagrama (Excel o CSV). Sin archivo abre ventana para elegir.\n"
        "cas diagrama plot <nombre> [nominal|ultimo] [combinaciones.csv]\n"
        "  Superficie 3D (como Diseno_Columnas) y puntos de combinaciones (CSV/Excel P,M2,M3).\n"
        "cas diagrama check-pm <muro> <Story> <Combinacion>\n"
        "  Verificacion P-M de una combinacion: P, M2, M3, theta, Mu_equiv, Cap, Ratio.\n"
        "cas columna asignar <UN> <Nominal> [Ultimo]\n"
        "  Asignar diagramas a columna.\n"
        "\n"
        "PASOS DE ANALISIS (DETALLADOS):\n"
        "cas columna q                 Paso 1: Indice de estabilidad Q\n"
        "cas columna esbeltez          Paso 2: Momentos extremos M1/M2\n"
        "cas columna segundo-orden     Paso 3: Efectos de segundo orden\n"
        "cas columna cm                Paso 4: Factor Cm\n"
        "cas columna delta             Paso 5: Factor de amplificacion delta\n"
        "cas columna esfuerzos-fin     Paso 6: Esfuerzos finales amplificados\n"
        "cas columna mn                Paso 7: Momentos nominales Mn2/Mn3\n"
        "cas columna estados           Paso 8: Estados sismicos combinados\n"
        "cas columna verificacion      Paso 9: Verificacion P-M\n"
        "cas columna resumen           Resumen de verificacion P-M\n"
        "\n"
        "DISEÑO COMPLETO EN UN SOLO COMANDO:\n"
        "cas columna diseno\n"
        "  Ejecuta internamente los pasos q, esbeltez, segundo-orden, cm, delta,\n"
        "  esfuerzos-fin, mn, estados, verificacion y resumen (mostrando todas\n"
        "  las tablas de cada paso en la consola).\n"
        "\n"
        "IMPORTAR DESDE ETABS:\n"
        "cas columna etabs-import [R_X] [R_Y]\n"
        "  Importa: Element Forces - Columns, Story Forces, Story Drifts,\n"
        "  Story Definitions y factor R. ETABS debe estar abierto con modelo cargado.\n"
        "cas columna etabs-diseno [R_X] [R_Y]\n"
        "  Atajo: importa desde ETABS y luego ejecuta 'cas columna diseno' en un paso."
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
    "Diagramas P-M (muros y columnas):",
    "  diagrama add <nombre> <nominal|ultimo> [archivo]",
    "  diagrama list             Listar diagramas en la base de datos",
    "  diagrama plot <nombre> [nominal|ultimo] [combinaciones.csv]  Superficie 3D + puntos comb.",
    "  diagrama check-pm <muro> <Story> <Combo>  Verificar una combinacion P-M (theta, Cap, Ratio).",
    "",
    "Vigas:",
    "  add viga <nombre> <fc> <fy> <b> <h> <rec> <Mu> [Vu]",
    "  list vigas                Ver vigas",
    "  edit viga <i> <param> <valor>",
    "  edit columna <param> <valor> [i1 i2 ...]",
    "  delete viga <i> [i2 i3 ...]",
    "",
    "Cálculos:",
    "  flexion viga                    Diseño por flexión vigas",
    "  flexion losa                    Diseño por flexión losas (ρ_min=0.0018)",
    "  losa define [nombre] <fc> <fy> <b> <h> <rec>  Definir losa(s)",
    "  losa list | delete <nombre|i>  Listar o borrar losas",
    "  losa momento add [nombre_losa] <nombre> <Mu>  Momentos | list | delete <i>",
    "  losa cortante add [nombre_losa] <nombre> <Vu>  Cortantes | list | delete <i>",
    "  cortante viga | cortante losa  Diseño por cortante (vigas o losas)",
    "  muro nucleo <nombre> <L> <fy> <nivel> <hm> <Mu> [phi]",
    "                                  Predimensionamiento núcleo de muro (manual)",
    "  muro etabs <nombre> <L> <fy> <pier_name> [phi]",
    "                                  Predimensionamiento desde ETABS (Pier Forces)",
    "  muro list                        Listar muros predimensionados",
    "  muro delete <nombre>             Borrar resultados predimensionamiento",
    "  results flexion [viga|losa]      Ver resultados flexión",
    "  results cortante                 Ver resultados cortante",
    "",
    "Diseno de Muros (RNE E.060) - Piso unico:",
    "  muro add <nombre> <hm> <lm> <t> <fc> <fy> <fyt> <Pu> <Vu> <Mu> [delta_u] [c] [Mn]",
    "                                  Agregar/actualizar muro para diseno",
    "  muro data                        Listar muros almacenados",
    "  muro remove <nombre>             Eliminar muro de datos",
    "  muro diseno [nombre] [DEFORMACION|ESFUERZO]",
    "                                  Diseno completo E.060 (flexion, corte, borde)",
    "  muro results [nombre]            Ver resultados de diseno de muros",
    "",
    "Diseno Multipiso (RNE E.060):",
    "  muro def <nombre> <lm> <t> <fc> <fy> <fyt>",
    "                                  Definir muro (geometria + materiales)",
    "  muro piso <nombre> <N> <hm> <Pu> <Vu> <Mu> [Mn] [c]",
    "                                  Agregar piso (Pu:Tn, Vu:Tn, Mu:Tn-m)",
    "  muro pisos [nombre]              Listar pisos definidos",
    "  muro del-piso <nombre> <N>       Eliminar un piso",
    "  muro asignar <muro> <Nom> [Ult] Asignar diagramas a un muro",
    "  muro multi <nombre> [DEFORMACION|ESFUERZO] [delta_u] [joint_Av]",
    "                                  Diseno multipiso completo E.060",
    "  muro multi-results [nombre]      Ver resultados multipiso",
    "  muro multi-report <nombre> [metodo] [du] [Av] [R]\n"
    "                                  Generar reporte multipiso (md/docx + figura P-M2-M3).\n"
    "  muro multi-delete <nombre>       Borrar resultados multipiso y datos asociados",
    "  muro etabs-import <nombre> <lm> <t> <fc> <fy> <fyt> <pier>",
    "                                  PASO 2: Importar ETABS, ver TABLA 1",
    "  muro etabs-diseno <nombre> <lm> <t> <fc> <fy> <fyt> <pier> [metodo] [du] [Av]",
    "                                  Atajo: importar + disenar en un paso",
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
    "Diseno de Columnas (E.060):",
    "  columna props <UN> <k> <lu> <Ix> <Iy> <Ag> <Bd> [fc] [fy]",
    "                                  Propiedades (Ec=15000*sqrt(fc), fc def. 210)",
    "  columna props-list              Listar propiedades",
    "  columna props-remove <UN>       Borrar propiedades de columna",
    "  columna esfuerzos <Story> <UN> <Station> <OC> <ST> <P> <M2> <M3>",
    "                                  Agregar esfuerzo de elemento",
    "  columna esfuerzos-list [UN]     Listar esfuerzos",
    "  columna story-forces <Story> <OC> <P> <VX> <VY>",
    "                                  Story forces",
    "  columna drifts <Story> <OC> <Drift>",
    "                                  Story drifts",
    "  columna alturas <Story> <Height>",
    "                                  Alturas de entrepiso",
    "  columna factor-r <R_X> <R_Y>   Factor R",
    "  columna asignar <UN> <Nom> [Ult] Asignar diagramas a columna",
    "  columna q                       Paso 1: Indice Q",
    "  columna esbeltez                Paso 2: Momentos extremos",
    "  columna segundo-orden           Paso 3: Segundo orden",
    "  columna cm                      Paso 4: Factor Cm",
    "  columna delta                   Paso 5: Factor delta",
    "  columna esfuerzos-fin           Paso 6: Esfuerzos finales",
    "  columna mn                      Paso 7: Momentos nominales",
    "  columna estados                 Paso 8: Estados sismicos",
    "  columna verificacion            Paso 9: Verificacion P-M",
    "  columna resumen                 Resumen P-M",
    "  columna diseno                  Ejecutar todos los pasos de diseño (todas las tablas)",
    "  columna etabs-import [R_X R_Y]  Importar desde ETABS",
    "  columna etabs-diseno [R_X R_Y]  Importar desde ETABS + diseno completo",
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
