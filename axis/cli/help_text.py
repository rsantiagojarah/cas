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
    "flexion": "cas flexion viga [viga|índice] | cas flexion losa\n  Diseño por flexión; opcional filtrar por viga (nombre o índice).",
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
    "viga": (
        "cas viga define [nombre] <fc> <fy> <b> <h> <rec>\n"
        "  Definir una viga (varias si les pone nombre; fc/fy kg/cm², b/h/rec cm).\n"
        "cas viga list\n"
        "  Listar vigas definidas.\n"
        "cas viga delete <nombre|índice>\n"
        "  Borrar una viga (y sus momentos/cortantes).\n"
        "cas viga momento add [nombre_viga|índice] <nombre> <Mu>\n"
        "  Añadir momento a la viga (índice = número de fila en cas viga list).\n"
        "cas viga momento list [nombre_viga] | delete <nº fila> | delete <viga> <nombre>\n"
        "  Listar momentos; eliminar por nº de fila (igual que en 'cas flexion viga') o por viga + nombre.\n"
        "cas viga cortante add [viga|i] <nombre> <Vu>  |  Vu1 Vu2...  |  T S M Vu...  |  list  |  delete <nº fila> | <viga> <nombre>\n"
        "  Igual que momento: solo Vu (V1,V2...), estructura T×S×M, o nombre+Vu. Delete por fila (cas cortante viga) o viga+nombre."
    ),
    "results": "cas results flexion [viga|losa] | cas results cortante\n  Ver resultados en tabla.",
    "cortante": "cas cortante viga [viga|i] | cas cortante losa\n  Cortante vigas (estribos; opcional filtrar) o losas (Vu vs phi*Vc).",
    "lambda": (
        "Factor λΔ deflexión diferida (E.060): λΔ = ξ/(1+50·ρ'), ρ'=As'/(b·d).\n"
        "  cas lambda <b> <d> <As'> <xi>  Cálculo directo (b,d cm; As' cm²).\n"
        "  cas lambda <elemento> <xi>  Usa b,d y As' de la sección centro (o apoyo si voladizo).\n"
        "  xi: 3meses|6meses|12meses|5anos (o 1.0, 1.2, 1.4, 2.0)."
    ),
    "inercia": (
        "Ie ponderado E.060 (deflexiones):\n"
        "  cas inercia define <nombre> <caso> <b> <h> <d> <d'> <fc>\n"
        "  cas inercia seccion add <elemento> <seccion> <As> <As'> <Ma>\n"
        "  As = acero en TRACCION, As' = acero en COMPRESION (para esa sección).\n"
        "  Apoyos: tracción arriba -> As=arriba, As'=abajo. Centro: tracción abajo -> As=abajo, As'=arriba.\n"
        "  cas inercia seccion list [elemento] | delete <i> | list | delete <nombre> | calcular [nombre]\n"
        "Verificación rápida: cas inercia fisurada <b> <d> <d'> <As> <As'> <n> [Ma Mcr Ig_m4]"
    ),
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
        "cas muro diseno [nombre] [DEFORMACION|ESFUERZO] [R]\n"
        "  Ejecuta diseño completo: espesor, flexión, agrietamiento, corte,\n"
        "  elementos de borde (método auto o manual). R = factor de ductilidad E.030\n"
        "  para amplificación por capacidad min(Mn/Mua,R); default 6.\n"
        "cas muro results [nm]          Ver resumen de resultados de diseno.\n"
        "cas muro report [nm] [metodo] [du] [Av] [R]\n"
        "  Generar reporte Markdown/Word de diseno multipiso.\n"
        "cas muro results-delete <nm>   Borrar resultados de diseno (piso unico).\n"
        "\n"
        "DISENO MULTIPISO RNE E.060:\n"
        "cas muro def <nombre> <lm> <t> <fc> <fy> <fyt>\n"
        "  Definir muro (geometria + materiales) para diseno multipiso.\n"
        "cas muro piso <nombre> <N> <hm> <Pu> <Vu> <Mu> [Mn] [c]\n"
        "  Agregar piso (hm:cm, Pu:Tn, Vu:Tn, Mu:Tn-m, Mn:Tn-m, c:cm).\n"
        "cas muro pisos [nombre]   Listar pisos definidos.\n"
        "cas muro del-piso <nm> <N>  Eliminar un piso.\n"
        "cas muro multi <nombre> [DEFORMACION|ESFUERZO] [delta_u] [joint_Av] [R]\n"
        "  Diseno multipiso completo E.060 (borde global con H_total).\n"
        "  R = factor de ductilidad E.030 (default 6).\n"
        "cas muro multi-results [nm]  Ver resultados multipiso.\n"
        "cas muro etabs-diseno <nombre> <lm> <t> <fc> <fy> <fyt> <pier> [metodo] [du] [Av] [R] [SOTANO n_pisos]\n"
        "  Importar ETABS (Pier Forces + Story Definitions) y diseno multipiso.\n"
        "  R = factor de ductilidad E.030 (default 6). Si se indica SOTANO n_pisos,\n"
        "  en esos pisos se toma Vu_cap = Vu (cortante de analisis)."
    ),
    "sismo": (
        "cas sismo <sentido> Z U perfil R Ia Ip Material  - Análisis E.030\n"
        "  sentido=X|Y, Z=1-4, U=A-D, perfil=S0-S4, R=8|7|6|3, Material=concreto|acero|albañileria\n"
        "  Ej: cas sismo X 3 C S2 8 1 1 concreto.\n"
        "  Rapido: cas sismo rapido X 3 C S2 8 concreto rb,masa tors\n"
        "  Irregularidades: cas sismo irregularidades | cas sismo irregularidades calcular rb tors\n"
        "  Separacion legacy: cas sismo separacion <h> [da db]\n"
        "  Nuevo flujo: cas sismo 2026 <sentido> Z U perfil R Ia Ip Material\n"
        "  Exportar ETABS 2026: cas sismo 2026 <sentido> Z U perfil R Ia Ip Sa\n"
        "  Persistencia 2026: list | show [id] | delete <id> | edit <id> ... | report [nom]\n"
        "  Espectro directo: cas espectro Z U S Tp Tl Ia Ip R"
    ),
    "irregular": (
        "cas irregular <tipo> X|Y <datos...>  - Verificacion E.030 (Tablas 8 y 9)\n"
        "  Sentido X o Y obligatorio. Tipos: rigidez, resistencia, discontinuidad, etc.\n"
        "  Persistencia: list | show [id] | delete <id> | edit <id> <tipo> X|Y datos...\n"
        "  Ej: cas irregular rigidez X 500 800 750 | cas irregular list\n"
        "  E.030 2026: cas irregular 2026 <tipo> ... (Tablas 11 y 12, store separado)\n"
        "  Ej: cas irregular 2026 rigidez X etabs | cas irregular 2026 report"
    ),
    "columna": (
        "DISEÑO DE COLUMNAS DE CONCRETO ARMADO (E.060)\n"
        "  Solo se usan esfuerzos con Station 0.\n"
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
        "cas columna diagrama [nombre_seccion]\n"
        "  Superficie de interaccion 3D con todos los puntos de esfuerzos finales (Station 0).\n"
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
    "  flexion viga [viga|i]           Diseño por flexión vigas (opcional: filtrar por viga)",
    "  flexion losa                    Diseño por flexión losas (ρ_min=0.0018)",
    "  losa define [nombre] <fc> <fy> <b> <h> <rec>  Definir losa(s)",
    "  losa list | delete <nombre|i>  Listar o borrar losas",
    "  losa momento add [nombre_losa] <nombre> <Mu>  Momentos | list | delete <i>",
    "  losa cortante add [nombre_losa] <nombre> <Vu>  Cortantes | list | delete <i>",
    "  viga define [nombre] <fc> <fy> <b> <h> <rec>  Definir viga(s) (mismo flujo que losa)",
    "  viga list | delete <nombre|i>  Listar o borrar vigas",
    "  viga momento add [nombre_viga|índice] <nombre> <Mu>  Momentos | list | delete <i>",
    "  viga cortante add [viga|i] <nombre> <Vu>  |  Vu1 Vu2...  |  T S M Vu...  |  list | delete <nº fila>|<viga> <nombre>",
    "  cortante viga [viga|i] | cortante losa  Diseño por cortante (vigas o losas; filtro opcional)",
    "  inercia define <nombre> <caso> b h d d' fc  Elemento Ie E.060",
    "  inercia seccion add <elem> <seccion> As As' Ma  (b,h,d,d',fc del elemento)",
    "  inercia calcular [nombre]  Ie por sección e Ie promedio",
    "  lambda <b> <d> <As'> <xi>  o  lambda <elemento> <xi>  λΔ deflexión diferida",
    "  inercia fisurada <b> <d> <d'> <As> <As'> <n> [Ma Mcr Ig_m4]  Verificación rápida Icr/Ie",
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
    "  muro diseno [nombre] [DEFORMACION|ESFUERZO] [R]",
    "                                  Diseno completo E.060 (flexion, corte, borde; R default 6)",
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
    "  muro multi <nombre> [DEFORMACION|ESFUERZO] [delta_u] [joint_Av] [R]",
    "                                  Diseno multipiso completo E.060 (R default 6)",
    "  muro multi-results [nombre]      Ver resultados multipiso",
    "  muro multi-report <nombre> [metodo] [du] [Av] [R]\n"
    "                                  Generar reporte multipiso (md/docx + figura P-M2-M3).\n"
    "  muro multi-delete <nombre>       Borrar resultados multipiso y datos asociados",
    "  muro etabs-import <nombre> <lm> <t> <fc> <fy> <fyt> <pier>",
    "                                  PASO 2: Importar ETABS, ver TABLA 1",
    "  muro etabs-diseno <nombre> <lm> <t> <fc> <fy> <fyt> <pier> [metodo] [du] [Av] [R] [SOTANO n]",
    "                                  Atajo: importar + disenar en un paso (R default 6)",
    "",
    "Irregularidades E.030:",
    "  irregular <tipo> X|Y datos   Verificacion por sentido (rigidez, resistencia, etc.)",
    "  irregular 2026 <tipo> ...    Igual que irregular, criterios E.030 2026 (Tablas 11-12)",
    "  irregular list [tipo] [X|Y]  Listar analisis guardados (legacy)",
    "  irregular 2026 list          Listar analisis 2026",
    "  irregular show [id]          Mostrar analisis",
    "  irregular 2026 show [id]     Mostrar analisis 2026",
    "  irregular delete <id>        Borrar analisis",
    "  irregular 2026 delete <id>   Borrar analisis 2026",
    "  irregular edit <id> tipo X|Y  Editar analisis",
    "  irregular 2026 report [nom]  Reporte consolidado 2026",
    "",
    "Sismo E.030:",
    "  sismo <sentido> Z U perfil R Ia Ip Material     Ej: X 3 C S2 8 1 1 concreto",
    "  sismo 2026 <sentido> Z U perfil R Ia Ip Material",
    "  sismo 2026 <sentido> Z U perfil R Ia Ip Sa      Exportar tabla Unicode ETABS (Periodo, Sa/g)",
    "  sismo rapido <sentido> Z U perfil R Material <cod_altura> <cod_planta>",
    "  sismo 2026 rapido <sentido> Z U perfil R Material <cod_altura> <cod_planta>",
    "  sismo irregularidades                           Ver codigos Ia/Ip (tablas 8 y 9)",
    "  sismo 2026 irregularidades                      Ver codigos Ia/Ip (E.030 2026)",
    "  sismo results                                  Ver resultados",
    "  sismo 2026 results                              Ver resultados 2026",
    "  sismo separacion <h> [da db]                    Separación edificios legacy",
    "  sismo 2026 separacion <h> <Z> <perfil|S> [da db] Separación edificios 2026",
    "  sismo 2026 list [X|Y]                          Listar analisis 2026 guardados",
    "  sismo 2026 show [id]                           Mostrar analisis 2026",
    "  sismo 2026 delete <id>                         Borrar analisis 2026",
    "  sismo 2026 edit <id> <sentido> Z U ...         Recalcular y actualizar analisis",
    "  sismo 2026 report [nombre]                     Reporte consolidado 2026",
    "  espectro Z U S Tp Tl Ia Ip R                   Espectro ETABS 2026 (Sa = Z*U*S*C/R)",
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
    "  columna diagrama [seccion]       Superficie P-M2-M3 + todos esfuerzos finales",
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
