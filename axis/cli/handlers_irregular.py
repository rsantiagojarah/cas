"""Handlers CLI para verificacion de irregularidades E.030 (Tablas 8 y 9 / 2026: 11 y 12)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from types import ModuleType

from axis.core.exceptions import InvalidInput, NoActiveProject
from axis.core.project import get_active_project_path
from axis.cli.handlers import get_base_path
from axis.cli.colors import heading, arrow, ok, fail, dim
from axis.cli.tables import format_table
from axis.sismico import irregularidades_verificacion as _verif_legacy
from axis.sismico import irregularidades_verificacion_2026 as _verif_2026
from axis.sismico.irregularidades_persistencia import (
    DEFAULT_STORE,
    STORE_2026,
    guardar_analisis,
    listar_analisis,
    obtener_analisis,
    eliminar_analisis,
    actualizar_analisis,
)
from axis.sismico.irregularidades_etabs import (
    obtener_rigidez_cortante_etabs,
    obtener_alturas_entrepiso,
    obtener_masa_etabs,
)


def _parse_float(s: str, nombre: str) -> float:
    try:
        return float(s.replace(",", "."))
    except ValueError:
        raise InvalidInput(f"{nombre} debe ser un numero. Recibido: {s}")


def _salida_verificacion(existe: bool) -> str:
    """existe=True -> hay irregularidad; existe=False -> no hay."""
    return fail("Existe") if existe else ok("No existe")


@dataclass(frozen=True)
class IrregularConfig:
    norma_label: str
    cmd_prefix: str
    store_file: str
    verif: ModuleType
    tabla_altura: str
    tabla_planta: str


CFG_LEGACY = IrregularConfig(
    norma_label="E.030",
    cmd_prefix="cas irregular",
    store_file=DEFAULT_STORE,
    verif=_verif_legacy,
    tabla_altura="Tabla 8",
    tabla_planta="Tabla 9",
)

CFG_2026 = IrregularConfig(
    norma_label="E.030 2026",
    cmd_prefix="cas irregular 2026",
    store_file=STORE_2026,
    verif=_verif_2026,
    tabla_altura="Tabla 11",
    tabla_planta="Tabla 12",
)

_active_cfg: IrregularConfig = CFG_LEGACY


def _V() -> ModuleType:
    return _active_cfg.verif


def _store() -> str:
    return _active_cfg.store_file


def _cmd() -> str:
    return _active_cfg.cmd_prefix


def _diafragma_criterio_txt() -> str:
    if _active_cfg is CFG_2026:
        return (
            "Criterio 1: abertura > 50% area bruta. "
            "Criterio 2: seccion neta < 50% area bruta equivalente.\n"
        )
    return "Criterio 1: abertura > 50% area bruta. Criterio 2: seccion neta < 25% seccion total.\n"


def _extraer_sentido(args: list[str]) -> tuple[str, list[str]]:
    """Si args[0] es X o Y, retorna (sentido, resto). Si no, lanza."""
    if not args:
        raise InvalidInput(f"Indique sentido X o Y. Ej: {_cmd()} rigidez X 500 800 750")
    s = args[0].upper()
    if s not in ("X", "Y"):
        raise InvalidInput("Primer argumento debe ser X o Y (sentido de analisis).")
    return s, args[1:]


def _get_project_path() -> Path:
    path = get_active_project_path(get_base_path())
    if not path:
        raise NoActiveProject("No hay proyecto activo. Use 'cas use <proyecto>'.")
    return Path(path)


def handle_irregular(args: list[str]) -> str:
    """cas irregular <tipo> ... (E.030 legacy)."""
    return dispatch_irregular(args, CFG_LEGACY)


def dispatch_irregular(args: list[str], cfg: IrregularConfig) -> str:
    """
    cas irregular [2026] <tipo> <args...>
    Tipos: torsional, rigidez, resistencia, masa, geometrica-vertical,
           esquinas-entrantes, diafragma, sistemas-no-paralelos, discontinuidad
    """
    global _active_cfg
    prev = _active_cfg
    _active_cfg = cfg
    try:
        return _dispatch_irregular_impl(args)
    finally:
        _active_cfg = prev


def _dispatch_irregular_impl(args: list[str]) -> str:
    if not args:
        return _irregular_help()
    sub = args[0].lower()
    if sub in ("help", "-h", "--help"):
        return _irregular_help()
    if sub == "list":
        return _cmd_list(args[1:])
    if sub == "show":
        return _cmd_show(args[1:])
    if sub == "delete":
        return _cmd_delete(args[1:])
    if sub == "report":
        return _cmd_report(args[1:])
    if sub == "edit":
        return _cmd_edit(args[1:])
    if sub == "torsional":
        return _cmd_torsional(args[1:])
    if sub in ("rigidez", "piso-blando", "extrema-rigidez"):
        return _cmd_rigidez(args[1:])
    if sub in ("resistencia", "piso-debil", "extrema-resistencia"):
        return _cmd_resistencia(args[1:])
    if sub == "masa":
        return _cmd_masa(args[1:])
    if sub == "geometrica-vertical":
        return _cmd_geometrica_vertical(args[1:])
    if sub == "esquinas-entrantes":
        return _cmd_esquinas_entrantes(args[1:])
    if sub == "diafragma":
        return _cmd_diafragma(args[1:])
    if sub == "sistemas-no-paralelos":
        return _cmd_sistemas_no_paralelos(args[1:])
    if sub in ("discontinuidad", "discontinuidad-extrema"):
        return _cmd_discontinuidad(args[1:])
    raise InvalidInput(f"Tipo desconocido: {sub}. Use: {_cmd()} help")


def _irregular_help() -> str:
    ta, tp = _active_cfg.tabla_altura, _active_cfg.tabla_planta
    p = _cmd()
    return (
        heading(f"Verificacion de irregularidades {_active_cfg.norma_label} ({ta} y {tp})\n")
        + dim("Datos manuales o importar desde ETABS. Requiere proyecto activo. Analisis por sentido X e Y.\n\n")
        + f"Todos los comandos: {p} <tipo> <X|Y> <datos...>  (sentido obligatorio salvo tipos de planta indicados)\n\n"
        + f"Persistencia: {p} list | show [id] | delete <id> | edit <id> <tipo> X|Y datos... | report [nombre]\n\n"
        + f"Planta ({tp}):\n"
        + f"  {p} torsional X|Y no-aplica | u_a1 u_b1 u_a2 u_b2 ...\n"
        + f"  {p} esquinas-entrantes no-aplica | ea1 eb1 ta1 tb1 ...\n"
        + f"  {p} diafragma no-aplica | ab1 br1 sn1 st1 ab2 br2 sn2 st2 ...\n"
        + f"  {p} sistemas-no-paralelos no-aplica | angulo\n\n"
        + f"Altura ({ta}):\n"
        + f"  {p} rigidez X|Y no-aplica | etabs | k1 k2 k3 ... kn\n"
        + f"  {p} resistencia X|Y no-aplica | etabs | V1 V2 V3 ... Vn\n"
        + f"  {p} masa X|Y [sotano|no-sotano] no-aplica | etabs | P1 P2 ...\n"
        + f"  {p} geometrica-vertical X|Y no-aplica | D1 D2 D3 ... Dn\n"
        + f"  {p} discontinuidad no-aplica | L1 d1 L2 d2 ...\n\n"
        + f"Ej: {p} rigidez X 500 800 750 | {p} list"
        + (
            dim(
                f"\n\nTras verificar, use: cas sismo 2026 irregularidades calcular <cod_alt> <cod_planta>\n"
                f"  o: cas sismo 2026 rapido <sentido> Z U perfil R Material <cod_alt> <cod_planta>\n"
            )
            if _active_cfg is CFG_2026
            else ""
        )
    )


def _cmd_list(args: list[str]) -> str:
    path = _get_project_path()
    tipo = args[0].lower() if args and args[0].lower() not in ("x", "y") else None
    sentido = args[1].upper() if len(args) > 1 and args[1].upper() in ("X", "Y") else None
    if args and args[0].upper() in ("X", "Y") and not tipo:
        sentido = args[0].upper()
    items = listar_analisis(path, tipo, sentido, store_name=_store())
    if not items:
        return "No hay analisis guardados."
    filas = [{"ID": a["id"], "Tipo": a["tipo"], "Sentido": a["sentido"],
             "Factor": a["factor"], "Fecha": a.get("timestamp", "")[:19]} for a in items]
    return heading("Analisis de irregularidades guardados\n") + format_table(filas)


def _cmd_show(args: list[str]) -> str:
    path = _get_project_path()
    aid = args[0] if args else None
    if not aid:
        items = listar_analisis(path, store_name=_store())
        if not items:
            return "No hay analisis guardados."
        aid = items[-1]["id"]
    a = obtener_analisis(path, aid, store_name=_store())
    if not a:
        return f"Analisis '{aid}' no encontrado."
    lineas = [
        heading(f"Analisis {a['id']} - {a['tipo']} sentido {a['sentido']}\n"),
        f"Factor {a.get('factor_tipo', 'Ia')}: {a['factor']}",
        "",
        format_table(a.get("filas", []), decimal_places=1),
    ]
    return "\n".join(lineas)


def _cmd_delete(args: list[str]) -> str:
    if not args:
        raise InvalidInput(f"Uso: {_cmd()} delete <id>")
    path = _get_project_path()
    if eliminar_analisis(path, args[0], store_name=_store()):
        return f"Analisis '{args[0]}' eliminado."
    return f"Analisis '{args[0]}' no encontrado."


def _cmd_edit(args: list[str]) -> str:
    if len(args) < 3:
        raise InvalidInput(f"Uso: {_cmd()} edit <id> <tipo> [X|Y] <datos...>")
    aid, tipo, resto = args[0], args[1].lower(), args[2:]
    mapeo = {
        "rigidez": _cmd_rigidez, "piso-blando": _cmd_rigidez, "extrema-rigidez": _cmd_rigidez,
        "resistencia": _cmd_resistencia, "piso-debil": _cmd_resistencia, "extrema-resistencia": _cmd_resistencia,
        "torsional": _cmd_torsional,
        "masa": _cmd_masa,
        "geometrica-vertical": _cmd_geometrica_vertical,
    }
    if tipo == "esquinas-entrantes":
        return _cmd_esquinas_entrantes(resto, edit_id=aid)
    if tipo == "diafragma":
        return _cmd_diafragma(resto, edit_id=aid)
    if tipo == "sistemas-no-paralelos":
        return _cmd_sistemas_no_paralelos(resto, edit_id=aid)
    if tipo in ("discontinuidad", "discontinuidad-extrema"):
        return _cmd_discontinuidad(resto, edit_id=aid)
    fn = mapeo.get(tipo)
    if fn:
        sentido, datos_args = _extraer_sentido(resto)
        return fn([sentido] + datos_args, edit_id=aid)
    raise InvalidInput(f"Edicion no soportada para tipo: {tipo}")


_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def _strip_ansi(text: str) -> str:
    return _ANSI_RE.sub("", text)


def _paso_a_markdown(bloque: str) -> str:
    limpio = _strip_ansi(bloque)
    lineas = limpio.splitlines()
    if not lineas:
        return ""
    titulo = lineas[0].strip()
    cuerpo = "\n".join(lineas[1:]).strip("\n")
    if not cuerpo:
        return f"## {titulo}\n"
    return f"## {titulo}\n\n```text\n{cuerpo}\n```\n"


TIPOS_SIN_SENTIDO = frozenset({"esquinas-entrantes", "diafragma", "sistemas-no-paralelos", "discontinuidad"})


def _orden_analisis(a: dict) -> tuple:
    orden_tipo = {
        "rigidez": 1, "resistencia": 2, "masa": 3, "geometrica-vertical": 4, "discontinuidad": 5,
        "torsional": 6, "esquinas-entrantes": 7, "diafragma": 8, "sistemas-no-paralelos": 9,
    }
    return (a.get("sentido", "X"), orden_tipo.get(a.get("tipo", ""), 99), a.get("tipo", ""))


def _cmd_report(args: list[str]) -> str:
    """
    Genera reporte consolidado de irregularidades en formato similar a sismo.
    Uso: {_cmd()} report [nombre]
    """
    from axis.reportes.docx_sismo import generar_docx_sismo

    path = _get_project_path()
    items = listar_analisis(path, store_name=_store())
    if not items:
        return "No hay analisis guardados para generar reporte."

    # Consolidar: por (tipo, sentido). Para tipos sin sentido, una sola entrada por tipo
    # y se prefiere el registro con sentido "-" (no aplica / sin direccion).
    ultimos: dict[tuple, dict] = {}
    for a in items:
        tipo = a.get("tipo", "")
        sentido = a.get("sentido", "")
        t_new = a.get("timestamp", "")
        if tipo in TIPOS_SIN_SENTIDO:
            key = (tipo,)
            existing = ultimos.get(key)
            if existing is None:
                ultimos[key] = a
            else:
                t_old = existing.get("timestamp", "")
                # Preferir sentido "-" (nuevo formato sin X/Y); si empate, el mas reciente
                if sentido == "-" and existing.get("sentido") != "-":
                    ultimos[key] = a
                elif (sentido == "-") == (existing.get("sentido") == "-") and t_new >= t_old:
                    ultimos[key] = a
        else:
            key = (tipo, sentido)
            t_old = ultimos.get(key, {}).get("timestamp", "")
            if key not in ultimos or t_new >= t_old:
                ultimos[key] = a
    analisis = sorted(ultimos.values(), key=_orden_analisis)

    sep = "\n\n" + dim("-" * 50) + "\n\n"
    titulo_rep = f"REPORTE DE IRREGULARIDADES {_active_cfg.norma_label}"
    salidas = [heading(f"{titulo_rep}\n") + dim("=" * 50) + "\n"]
    md_partes = [f"# {titulo_rep}\n"]

    resumen = [
        {
            "Tipo": a.get("tipo", ""),
            "Sentido": "-" if a.get("tipo") in TIPOS_SIN_SENTIDO else a.get("sentido", ""),
            "Factor": f"{a.get('factor_tipo', '')}={a.get('factor', 1.0)}",
            "ID": a.get("id", ""),
            "Fecha": str(a.get("timestamp", ""))[:19],
        }
        for a in analisis
    ]
    txt_resumen = heading("Resumen de analisis incluidos\n") + format_table(resumen, decimal_places=1)
    salidas.append(txt_resumen)
    md_partes.append(_paso_a_markdown(txt_resumen))

    for a in analisis:
        tipo = str(a.get("tipo", "")).replace("-", " ").title()
        sentido = a.get("sentido", "")
        factor_tipo = a.get("factor_tipo", "Ia")
        factor = a.get("factor", 1.0)
        filas = a.get("filas", [])
        titulo_bloque = f"{tipo}\n" if a.get("tipo") in TIPOS_SIN_SENTIDO else f"{tipo} - Sentido {sentido}\n"
        bloque = (
            heading(titulo_bloque)
            + arrow(f"Factor {factor_tipo}: ")
            + str(factor)
            + "\n\n"
            + format_table(filas, decimal_places=1)
        )
        salidas.append(sep + bloque)
        md_partes.append(_paso_a_markdown(bloque))

    factores_ia = [float(a.get("factor", 1.0)) for a in analisis if a.get("factor_tipo") == "Ia"]
    factores_ip = [float(a.get("factor", 1.0)) for a in analisis if a.get("factor_tipo") == "Ip"]
    ia_rep = min(factores_ia) if factores_ia else 1.0
    ip_rep = min(factores_ip) if factores_ip else 1.0
    bloque_fact = heading("Factores de irregularidad consolidados\n") + format_table(
        [{"Factor": "Ia (altura)", "Valor": ia_rep}, {"Factor": "Ip (planta)", "Valor": ip_rep}],
        decimal_places=2,
    )
    salidas.append(sep + bloque_fact)
    md_partes.append(_paso_a_markdown(bloque_fact))
    if _active_cfg is CFG_2026:
        bloque_sig = dim(
            f"Siguiente paso: cas sismo 2026 irregularidades calcular <cod_alt> <cod_planta>\n"
            f"  o cas sismo 2026 rapido <sentido> Z U perfil R Material <cod_alt> <cod_planta>\n"
            f"  (Ia consolidado={ia_rep:g}, Ip consolidado={ip_rep:g})"
        )
        salidas.append(sep + bloque_sig)
        md_partes.append(_paso_a_markdown(bloque_sig))

    nombre = args[0].strip() if args else "general"
    nombre_limpio = "".join(c for c in nombre if c.isalnum() or c in ("-", "_")).strip() or "general"
    suf = "_2026" if _active_cfg is CFG_2026 else ""
    base = f"irregularidades_reporte{suf}_{nombre_limpio}"
    results_dir = path / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    md_path = results_dir / f"{base}.md"
    docx_path = results_dir / f"{base}.docx"

    try:
        md_path.write_text("\n".join(md_partes), encoding="utf-8")
        docx_ok = generar_docx_sismo(md_partes, str(docx_path))
        msg = f"Reporte guardado en results/: '{base}.md'" + (f", '{base}.docx'" if docx_ok else "")
        salidas.append(sep + dim(msg))
    except Exception as e:
        salidas.append(sep + dim(f"No se pudo guardar reporte: {e}"))

    return "\n".join(salidas)


def _no_aplica_generico(
    tipo: str, sentido: str, factor_tipo: str, factor: float, edit_id: str | None
) -> str:
    """Salida generica para no-aplica en cualquier tipo de irregularidad."""
    path = _get_project_path()
    filas = [{"Irregular": "No aplica"}]
    datos = [["no-aplica"]]
    if edit_id:
        actualizar_analisis(
            path, edit_id, tipo, sentido, datos, factor, factor_tipo, filas, store_name=_store()
        )
        msg_guardado = ""
    else:
        aid = guardar_analisis(
            path, tipo, sentido, datos, factor, factor_tipo, filas, store_name=_store()
        )
        msg_guardado = "\n" + ok(f"Guardado (id: {aid})")
    titulo = f"{tipo.replace('-', ' ').title()}" + (f" - Sentido {sentido}\n" if sentido != "-" else "\n")
    return (
        heading(titulo)
        + dim("No aplica: no existe irregularidad de este tipo.\n")
        + format_table(filas)
        + "\n\n" + arrow(f"Factor {factor_tipo} a usar: ") + str(factor)
        + msg_guardado
    )


def _cmd_torsional(args: list[str], edit_id: str | None = None) -> str:
    sentido, resto = _extraer_sentido(args)
    # Caso 1: no-aplica (Delta_max <= 50% Delta_perm en todo el edificio)
    if len(resto) == 1 and resto[0].lower() in ("no-aplica", "no_aplica"):
        path = _get_project_path()
        filas = [{"Piso": "-", "Delta_max": "-", "Delta_prom": "-",
                  "Ratio": "-", "Irregular": "No aplica", "Extrema": "-"}]
        datos = [["no-aplica"]]
        if edit_id:
            actualizar_analisis(path, edit_id, "torsional", sentido, datos, 1.0, "Ip", filas, store_name=_store())
            msg_guardado = ""
        else:
            aid = guardar_analisis(path, "torsional", sentido, datos, 1.0, "Ip", filas, store_name=_store())
            msg_guardado = "\n" + ok(f"Guardado (id: {aid})")
        return (
            heading(f"Irregularidad torsional ({_active_cfg.tabla_planta}) - Sentido {sentido}\n")
            + dim("No aplica: desplazamiento relativo de entrepiso <= 50% del permisible (Tabla 11).\n")
            + format_table(filas)
            + "\n\n" + arrow("Factor Ip a usar: ") + "1.0"
            + msg_guardado
        )
    # u_a u_b por piso (desplazamientos absolutos por nivel)
    if len(resto) < 2 or len(resto) % 2 != 0:
        raise InvalidInput(
            f"Uso: {_cmd()} torsional X|Y no-aplica\n"
            f"  O: {_cmd()} torsional X|Y u_a1 u_b1 u_a2 u_b2 ..."
        )
    abs_a, abs_b = [], []
    for i in range(0, len(resto), 2):
        ua = _parse_float(resto[i], f"u_a{i//2+1}")
        ub = _parse_float(resto[i + 1], f"u_b{i//2+1}")
        abs_a.append(ua)
        abs_b.append(ub)
    pares = _V().calcular_relativos_desde_absolutos(abs_a, abs_b)
    resultados = _V().verificar_torsional_todos(pares)
    filas = []
    for i, r in enumerate(resultados):
        irregular = "Si" if r["existe"] else "No"
        extrema = "Si" if r["extrema"] else "No"
        ratio = r["ratio"] if r["ratio"] is not None else "-"
        filas.append({
            "Piso": r["piso"],
            "da": round(pares[i][0], 6),
            "db": round(pares[i][1], 6),
            "Delta_max": r["delta_max"],
            "Delta_prom": r["delta_prom"],
            "Ratio": ratio,
            "Irregular": irregular,
            "Extrema": extrema,
        })
    existe_alguna = any(r["existe"] for r in resultados)
    extrema_alguna = any(r["extrema"] for r in resultados)
    ip = 0.60 if extrema_alguna else (0.75 if existe_alguna else 1.0)
    path = _get_project_path()
    datos = [[da, db] for (da, db) in pares]
    if edit_id:
        actualizar_analisis(path, edit_id, "torsional", sentido, datos, ip, "Ip", filas, store_name=_store())
        msg_guardado = ""
    else:
        aid = guardar_analisis(path, "torsional", sentido, datos, ip, "Ip", filas, store_name=_store())
        msg_guardado = "\n" + ok(f"Guardado (id: {aid})")
    lineas = [
        heading(f"Irregularidad torsional ({_active_cfg.tabla_planta}) - Sentido {sentido}\n"),
        dim("Criterio solo aplica si desplazamiento relativo de entrepiso > 50% del permisible (Tabla 11).\n"),
        dim("Calculados desde absolutos. da, db = relativos por piso. Ratio = Delta_max/Delta_prom.\n"),
        format_table(filas),
        "",
        arrow("Existe irregularidad en algun piso: ") + _salida_verificacion(existe_alguna),
        arrow("Existe irregularidad extrema en algun piso: ") + _salida_verificacion(extrema_alguna),
        "",
        arrow("Factor Ip a usar: ") + str(ip),
    ]
    return "\n".join(lineas) + msg_guardado


def _cmd_rigidez(args: list[str], edit_id: str | None = None) -> str:
    sentido, resto = _extraer_sentido(args)
    if len(resto) == 1 and resto[0].lower() in ("no-aplica", "no_aplica"):
        return _no_aplica_generico("rigidez", sentido, "Ia", 1.0, edit_id)
    if len(resto) == 1 and resto[0].lower() == "etabs":
        datos_etabs = obtener_rigidez_cortante_etabs(sentido)
        if datos_etabs is None or not datos_etabs.get("ks"):
            raise InvalidInput("No se pudieron obtener rigideces desde ETABS (Story Stiffness).")
        ks = datos_etabs["ks"]
        resto = [str(k) for k in ks]
    if len(resto) < 2:
        raise InvalidInput(f"Uso: {_cmd()} rigidez X|Y no-aplica | etabs | k1 k2 k3 ... kn")
    ks = [_parse_float(a, f"k{i+1}") for i, a in enumerate(resto)]
    resultados = _V().verificar_rigidez_unificado(ks)
    def _fmt1(x):
        if x is None:
            return x
        try:
            return f"{float(x):.1f}"
        except (TypeError, ValueError):
            return x

    filas = []
    for r in resultados:
        prom3 = _fmt1(r["ratio_prom3"]) if r["ratio_prom3"] is not None else "-"
        ratio_sup = _fmt1(r["ratio_sup"]) if r["ratio_sup"] is not None else "-"
        k_sup_display = "-" if r["clasificacion"] == "N/A" else _fmt1(r["k_sup"])
        filas.append({
            "Piso": r["piso"],
            "k_i": _fmt1(r["k_i"]),
            "k_sup": k_sup_display,
            "k_i/k_sup": ratio_sup,
            "k_i/prom3": prom3,
            "Clasificacion": r["clasificacion"],
            "Ia": r["Ia"],
        })
    ia_edificio = min(r["Ia"] for r in resultados)
    path = _get_project_path()
    if edit_id:
        actualizar_analisis(path, edit_id, "rigidez", sentido, ks, ia_edificio, "Ia", filas, store_name=_store())
        msg_guardado = ""
    else:
        aid = guardar_analisis(path, "rigidez", sentido, ks, ia_edificio, "Ia", filas, store_name=_store())
        msg_guardado = "\n" + ok(f"Guardado (id: {aid})")
    lineas = [
        heading(f"Rigidez - Piso blando / Extrema ({_active_cfg.tabla_altura}) - Sentido {sentido}\n"),
        dim("Rigideces de abajo a arriba: ") + ", ".join(f"{k:.1f}" for k in ks),
        "",
        format_table(filas, decimal_places=1),
        "",
        arrow("Factor Ia a usar (el mas desfavorable): ") + str(ia_edificio),
    ]
    return "\n".join(lineas) + msg_guardado


def _cmd_resistencia(args: list[str], edit_id: str | None = None) -> str:
    sentido, resto = _extraer_sentido(args)
    if len(resto) == 1 and resto[0].lower() in ("no-aplica", "no_aplica"):
        return _no_aplica_generico("resistencia", sentido, "Ia", 1.0, edit_id)
    if len(resto) == 1 and resto[0].lower() == "etabs":
        datos_etabs = obtener_rigidez_cortante_etabs(sentido)
        if datos_etabs is None or not datos_etabs.get("vs"):
            raise InvalidInput("No se pudieron obtener cortantes desde ETABS (Story Stiffness/Forces).")
        vs_raw = datos_etabs["vs"]
        resto = [str(v) for v in vs_raw]
    if len(resto) < 2:
        raise InvalidInput(f"Uso: {_cmd()} resistencia X|Y no-aplica | etabs | V1 V2 V3 ... Vn")
    vs = [_parse_float(a, f"V{i+1}") for i, a in enumerate(resto)]
    resultados = _V().verificar_resistencia_unificado(vs)

    def _fmt1(x):
        if x is None:
            return x
        try:
            return f"{float(x):.1f}"
        except (TypeError, ValueError):
            return x

    filas = []
    for r in resultados:
        ratio_display = _fmt1(r["ratio"]) if r["ratio"] is not None else "-"
        v_sup_display = "-" if r["clasificacion"] == "N/A" else _fmt1(r["V_res_sup"])
        filas.append({
            "Piso": r["piso"],
            "V_res_i": _fmt1(r["V_res_i"]),
            "V_res_sup": v_sup_display,
            "V_i/V_sup": ratio_display,
            "Clasificacion": r["clasificacion"],
            "Ia": r["Ia"],
        })
    ia_edificio = min(r["Ia"] for r in resultados)
    path = _get_project_path()
    if edit_id:
        actualizar_analisis(path, edit_id, "resistencia", sentido, vs, ia_edificio, "Ia", filas, store_name=_store())
        msg_guardado = ""
    else:
        aid = guardar_analisis(path, "resistencia", sentido, vs, ia_edificio, "Ia", filas, store_name=_store())
        msg_guardado = "\n" + ok(f"Guardado (id: {aid})")
    lineas = [
        heading(f"Resistencia - Piso debil / Extrema ({_active_cfg.tabla_altura}) - Sentido {sentido}\n"),
        dim("Resistencias de abajo a arriba: ") + ", ".join(f"{v:.1f}" for v in vs),
        "",
        format_table(filas, decimal_places=1),
        "",
        arrow("Factor Ia a usar (el mas desfavorable): ") + str(ia_edificio),
    ]
    return "\n".join(lineas) + msg_guardado


def _cmd_masa(args: list[str], edit_id: str | None = None) -> str:
    sentido, resto = _extraer_sentido(args)
    hay_sotano = False
    if resto and resto[0].lower() in ("sotano", "con-sotano", "sótano"):
        hay_sotano = True
        resto = resto[1:]
    elif resto and resto[0].lower() in ("no-sotano", "sin-sotano"):
        hay_sotano = False
        resto = resto[1:]
    if len(resto) == 1 and resto[0].lower() in ("no-aplica", "no_aplica"):
        return _no_aplica_generico("masa", sentido, "Ia", 1.0, edit_id)
    if len(resto) == 1 and resto[0].lower() == "etabs":
        datos_etabs = obtener_masa_etabs(sentido)
        if datos_etabs is None or not datos_etabs.get("ps"):
            raise InvalidInput("No se pudieron obtener pesos desde ETABS (Mass Summary by Story).")
        resto = [str(p) for p in datos_etabs["ps"]]
    if len(resto) < 2:
        raise InvalidInput(
            f"Uso: {_cmd()} masa X|Y [sotano|no-sotano] no-aplica | etabs | P1 P2 P3 ... Pn"
        )
    ps = [_parse_float(a, f"P{i+1}") for i, a in enumerate(resto)]
    resultados = _V().verificar_masa_todos(ps, hay_sotano=hay_sotano)
    filas = [{
        "Piso": r["piso"],
        "Peso": r["peso"],
        "Ratio": r["ratio"] or "-",
        "Irregular": "No aplica" if not r.get("aplica", True) else ("Si" if r["existe"] else "No"),
    } for r in resultados]
    existe_alguna = any(r["existe"] for r in resultados)
    ia = 0.90 if existe_alguna else 1.0
    path = _get_project_path()
    metadata = {"hay_sotano": hay_sotano}
    if edit_id:
        actualizar_analisis(path, edit_id, "masa", sentido, ps, ia, "Ia", filas, metadata=metadata, store_name=_store())
        msg_guardado = ""
    else:
        aid = guardar_analisis(path, "masa", sentido, ps, ia, "Ia", filas, metadata=metadata, store_name=_store())
        msg_guardado = "\n" + ok(f"Guardado (id: {aid})")
    nota_sotano = (
        dim(f"Con sótano: criterio no aplica en primer piso ({_active_cfg.tabla_altura}).\n")
        if hay_sotano
        else ""
    )
    lineas = [
        heading(f"Irregularidad de masa o peso ({_active_cfg.tabla_altura}) - Sentido {sentido}\n"),
        nota_sotano,
        format_table(filas),
        "",
        arrow("Factor Ia a usar: ") + str(ia),
    ]
    return "\n".join(lineas) + msg_guardado


def _cmd_geometrica_vertical(args: list[str], edit_id: str | None = None) -> str:
    sentido, resto = _extraer_sentido(args)
    if len(resto) == 1 and resto[0].lower() in ("no-aplica", "no_aplica"):
        return _no_aplica_generico("geometrica-vertical", sentido, "Ia", 1.0, edit_id)
    if len(resto) < 2:
        raise InvalidInput(f"Uso: {_cmd()} geometrica-vertical X|Y no-aplica  O  X|Y D1 D2 D3 ... Dn")
    ds = [_parse_float(a, f"D{i+1}") for i, a in enumerate(resto)]
    resultados = _V().verificar_geometrica_vertical_todos(ds)
    filas = [{
        "Piso": r["piso"],
        "Dim": r["dim"],
        "Ratio": r["ratio"] or "-",
        "Irregular": "No aplica" if not r.get("aplica", True) else ("Si" if r["existe"] else "No"),
    } for r in resultados]
    existe_alguna = any(r["existe"] for r in resultados)
    ia = 0.90 if existe_alguna else 1.0
    path = _get_project_path()
    if edit_id:
        actualizar_analisis(path, edit_id, "geometrica-vertical", sentido, ds, ia, "Ia", filas, store_name=_store())
        msg_guardado = ""
    else:
        aid = guardar_analisis(path, "geometrica-vertical", sentido, ds, ia, "Ia", filas, store_name=_store())
        msg_guardado = "\n" + ok(f"Guardado (id: {aid})")
    lineas = [
        heading(f"Irregularidad geometrica vertical ({_active_cfg.tabla_altura}) - Sentido {sentido}\n"),
        format_table(filas),
        "",
        arrow("Factor Ia a usar: ") + str(ia),
    ]
    return "\n".join(lineas) + msg_guardado


def _criterio_esquinas_txt() -> str:
    return (
        f"Criterio {_active_cfg.norma_label} {_active_cfg.tabla_planta}: existe irregularidad cuando "
        "la dimension del entrante es mayor al 20% de la dimension total en planta en AMBAS "
        "direcciones (A y B). %A = (ea/ta)*100; %B = (eb/tb)*100."
    )


def _cmd_esquinas_entrantes(args: list[str], edit_id: str | None = None) -> str:
    # Esquinas entrantes no depende del sentido sísmico; no se pide X|Y.
    resto = args
    sentido = "-"
    if len(resto) == 1 and resto[0].lower() in ("no-aplica", "no_aplica"):
        path = _get_project_path()
        filas = [{"Irregular": "No aplica"}]
        datos = [["no-aplica"]]
        if edit_id:
            actualizar_analisis(path, edit_id, "esquinas-entrantes", sentido, datos, 1.0, "Ip", filas, store_name=_store())
            msg_guardado = ""
        else:
            aid = guardar_analisis(path, "esquinas-entrantes", sentido, datos, 1.0, "Ip", filas, store_name=_store())
            msg_guardado = "\n" + ok(f"Guardado (id: {aid})")
        return (
            heading(f"Esquinas entrantes ({_active_cfg.tabla_planta})\n")
            + dim(_criterio_esquinas_txt() + "\n")
            + dim("No aplica: no existe irregularidad de este tipo.\n")
            + format_table(filas)
            + "\n\n" + arrow("Factor Ip a usar: ") + "1.0"
            + msg_guardado
        )
    if len(resto) < 4 or len(resto) % 4 != 0:
        raise InvalidInput(
            f"Uso: {_cmd()} esquinas-entrantes no-aplica  O  ea1 eb1 ta1 tb1 ea2 eb2 ta2 tb2 ..."
        )
    datos = []
    for i in range(0, len(resto), 4):
        datos.append((
            _parse_float(resto[i], f"ea{i//4+1}"),
            _parse_float(resto[i+1], f"eb{i//4+1}"),
            _parse_float(resto[i+2], f"ta{i//4+1}"),
            _parse_float(resto[i+3], f"tb{i//4+1}"),
        ))
    resultados = _V().verificar_esquinas_entrantes_todos(datos)
    filas = []
    for i, r in enumerate(resultados):
        ea, eb, ta, tb = datos[i]
        filas.append({
            "Piso": r["piso"],
            "ea": round(ea, 4),
            "eb": round(eb, 4),
            "ta": round(ta, 4),
            "tb": round(tb, 4),
            "%A": r["pct_a"],
            "%B": r["pct_b"],
            "Irregular": "Si" if r["existe"] else "No",
        })
    existe_alguna = any(r["existe"] for r in resultados)
    ip = 0.90 if existe_alguna else 1.0
    path = _get_project_path()
    if edit_id:
        actualizar_analisis(path, edit_id, "esquinas-entrantes", sentido, [list(d) for d in datos], ip, "Ip", filas, store_name=_store())
        msg_guardado = ""
    else:
        aid = guardar_analisis(path, "esquinas-entrantes", sentido, [list(d) for d in datos], ip, "Ip", filas, store_name=_store())
        msg_guardado = "\n" + ok(f"Guardado (id: {aid})")
    lineas = [
        heading(f"Esquinas entrantes ({_active_cfg.tabla_planta})\n"),
        dim(_criterio_esquinas_txt() + "\n"),
        format_table(filas),
        "",
        arrow("Factor Ip a usar: ") + str(ip),
    ]
    return "\n".join(lineas) + msg_guardado


def _cmd_diafragma(args: list[str], edit_id: str | None = None) -> str:
    # Discontinuidad del diafragma no depende del sentido; no se pide X|Y.
    resto = args
    sentido = "-"
    if len(resto) == 1 and resto[0].lower() in ("no-aplica", "no_aplica"):
        return _no_aplica_generico("diafragma", sentido, "Ip", 1.0, edit_id)
    if len(resto) < 4 or len(resto) % 4 != 0:
        raise InvalidInput(
            f"Uso: {_cmd()} diafragma no-aplica  O  ab1 br1 sn1 st1 ab2 br2 sn2 st2 ...\n"
            "  ab=abertura, br=area bruta. sn,st=seccion neta y total (0 0 si no aplica criterio 2)."
        )
    datos = []
    for i in range(0, len(resto), 4):
        ab = _parse_float(resto[i], f"ab{i//4+1}")
        br = _parse_float(resto[i + 1], f"br{i//4+1}")
        sn = _parse_float(resto[i + 2], f"sn{i//4+1}")
        st = _parse_float(resto[i + 3], f"st{i//4+1}")
        if st == 0:
            sn, st = None, None
        datos.append((ab, br, sn, st))
    resultados = _V().verificar_diafragma_todos(datos)
    filas = []
    for i, r in enumerate(resultados):
        ab, br, sn, st = datos[i]
        pct_sec = r.get("pct_seccion")
        filas.append({
            "Piso": r["piso"],
            "ab": round(ab, 4),
            "br": round(br, 4),
            "sn": round(sn, 4) if sn is not None else "-",
            "st": round(st, 4) if st is not None else "-",
            "%Abertura": r["pct_abertura"],
            "%Seccion": pct_sec if pct_sec is not None else "-",
            "Irregular": "Si" if r["existe"] else "No",
        })
    existe_alguna = any(r["existe"] for r in resultados)
    ip = 0.85 if existe_alguna else 1.0
    path = _get_project_path()
    datos_guardar = [[d[0], d[1], d[2], d[3]] for d in datos]
    if edit_id:
        actualizar_analisis(path, edit_id, "diafragma", sentido, datos_guardar, ip, "Ip", filas, store_name=_store())
        msg_guardado = ""
    else:
        aid = guardar_analisis(path, "diafragma", sentido, datos_guardar, ip, "Ip", filas, store_name=_store())
        msg_guardado = "\n" + ok(f"Guardado (id: {aid})")
    lineas = [
        heading(f"Discontinuidad del diafragma ({_active_cfg.tabla_planta})\n"),
        dim(_diafragma_criterio_txt()),
        format_table(filas),
        "",
        arrow("Factor Ip a usar: ") + str(ip),
    ]
    return "\n".join(lineas) + msg_guardado


def _cmd_sistemas_no_paralelos(args: list[str], edit_id: str | None = None) -> str:
    # Sistemas no paralelos no depende del sentido; no se pide X|Y.
    resto = args
    sentido = "-"
    if len(resto) == 1 and resto[0].lower() in ("no-aplica", "no_aplica"):
        return _no_aplica_generico("sistemas-no-paralelos", sentido, "Ip", 1.0, edit_id)
    if len(resto) != 1:
        raise InvalidInput(f"Uso: {_cmd()} sistemas-no-paralelos no-aplica  O  angulo")
    angulo = _parse_float(resto[0], "angulo")
    existe = angulo >= 30
    ip = 0.90 if existe else 1.0
    filas = [{"Angulo": angulo, "Irregular": "Si" if existe else "No"}]
    path = _get_project_path()
    datos = [angulo]
    if edit_id:
        actualizar_analisis(path, edit_id, "sistemas-no-paralelos", sentido, datos, ip, "Ip", filas, store_name=_store())
        msg_guardado = ""
    else:
        aid = guardar_analisis(path, "sistemas-no-paralelos", sentido, datos, ip, "Ip", filas, store_name=_store())
        msg_guardado = "\n" + ok(f"Guardado (id: {aid})")
    nota = ""
    if existe:
        nota = "\n" + dim("Verificar que los elementos no paralelos resistan mas del 10% de la cortante del piso.")
    lineas = [
        heading(f"Sistemas no paralelos ({_active_cfg.tabla_planta})\n"),
        dim("No aplica si angulo < 30 grados o si elementos no paralelos resisten < 10% cortante.\n"),
        format_table(filas),
        "",
        arrow("Factor Ip a usar: ") + str(ip),
    ]
    return "\n".join(lineas) + nota + msg_guardado


def _cmd_discontinuidad(args: list[str], edit_id: str | None = None) -> str:
    # Discontinuidad en sistemas resistentes no depende del sentido; no se pide X|Y.
    resto = args
    sentido = "-"
    if len(resto) == 1 and resto[0].lower() in ("no-aplica", "no_aplica"):
        path = _get_project_path()
        filas = [{"Piso": "-", "L": "-", "d": "-", "d/L%": "-", "Clasificacion": "No aplica", "Ia": "1.0"}]
        datos = [["no-aplica"]]
        if edit_id:
            actualizar_analisis(path, edit_id, "discontinuidad", sentido, datos, 1.0, "Ia", filas, store_name=_store())
            msg_guardado = ""
        else:
            aid = guardar_analisis(path, "discontinuidad", sentido, datos, 1.0, "Ia", filas, store_name=_store())
            msg_guardado = "\n" + ok(f"Guardado (id: {aid})")
        return (
            heading(f"Discontinuidad sistemas resistentes ({_active_cfg.tabla_altura})\n")
            + dim("No aplica: solo aplica cuando el elemento resiste mas del 10% de la fuerza cortante del piso.\n")
            + format_table(filas)
            + "\n\n" + arrow("Factor Ia a usar: ") + "1.0"
            + msg_guardado
        )
    if len(resto) < 2 or len(resto) % 2 != 0:
        raise InvalidInput(f"Uso: {_cmd()} discontinuidad no-aplica  O  L1 d1 L2 d2 ...")
    pares = [(resto[i], resto[i + 1]) for i in range(0, len(resto), 2)]
    datos = [(_parse_float(L, f"L{i+1}"), _parse_float(d, f"d{i+1}")) for i, (L, d) in enumerate(pares)]
    resultados = _V().verificar_discontinuidad_unificado_desalineamiento(datos)
    filas = [{"Piso": r["piso"], "L": r["L"], "d": r["d"], "d/L%": r["d/L%"],
              "Clasificacion": r["clasificacion"], "Ia": r["Ia"]} for r in resultados]
    ia_edificio = min(r["Ia"] for r in resultados)
    path = _get_project_path()
    datos_guardar = [[L, d] for L, d in datos]
    if edit_id:
        actualizar_analisis(path, edit_id, "discontinuidad", sentido, datos_guardar, ia_edificio, "Ia", filas, store_name=_store())
        msg_guardado = ""
    else:
        aid = guardar_analisis(path, "discontinuidad", sentido, datos_guardar, ia_edificio, "Ia", filas, store_name=_store())
        msg_guardado = "\n" + ok(f"Guardado (id: {aid})")
    lineas = [
        heading(f"Discontinuidad sistemas resistentes ({_active_cfg.tabla_altura})\n"),
        dim("Solo aplica cuando el elemento resiste mas del 10% de la fuerza cortante del piso.\n"),
        dim("L=longitud elemento, d=distancia desalineamiento. Calcula d/L%. Si d/L>25% -> Discontinuidad (Ia=0.80).\n"),
        format_table(filas),
        "",
        arrow("Factor Ia a usar (el mas desfavorable): ") + str(ia_edificio),
    ]
    return "\n".join(lineas) + msg_guardado
