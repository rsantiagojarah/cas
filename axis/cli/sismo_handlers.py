"""Handlers CLI para análisis sísmico E.030. Reglas: ≤200 líneas, ≤150 chars."""

from __future__ import annotations

from axis.core.exceptions import InvalidInput
from axis.core.project import get_active_project_path
from axis.core.database import write_results_csv, read_results_csv
from axis.cli.tables import format_table
from axis.cli.colors import heading, dim
from axis.sismico.tables_e030 import obtener_distorsion_maxima
from axis.sismico import separacion_edificios
from axis.sismico.flujo_sismo import ejecutar_analisis_sismico
from axis.sismico.irregularidades_e030 import (
    calcular_factores_irregularidad,
    tabla_codigos_altura,
    tabla_codigos_planta,
)
from axis.data.etabs_source import EtabsSource
import re


def _get_project_path():
    from axis.cli.handlers import get_base_path
    path = get_active_project_path(get_base_path())
    if not path:
        raise InvalidInput("No hay proyecto activo. Use 'cas use <proyecto>'.")
    return path


R0_VALIDOS = (8, 7, 6, 3)
MATERIAL_MAP = {"concreto": "concreto_armado", "acero": "acero", "albañileria": "albañileria"}


def handle_sismo(args: list[str]) -> str:
    """cas sismo <sentido> Z U perfil R Ia Ip Material [nombre_guardar] | results | report | separacion"""
    if not args:
        return _sismo_help()
    sub = args[0].lower()
    if sub == "results":
        return handle_sismo_results(args[1:])
    if sub == "separacion":
        return handle_sismo_separacion(args[1:])
    if sub in ("irregularidades", "irreg"):
        return handle_sismo_irregularidades(args[1:])
    if sub in ("rapido", "fast"):
        return handle_sismo_rapido(args[1:])
    if sub in ("help", "-h", "--help"):
        return _sismo_help()
    if len(args) >= 8:
        return handle_sismo_calcular(args)
    return _sismo_help()


def _sismo_help() -> str:
    return (
        "Analisis sismico E.030 (un sentido X o Y):\n"
        "  cas sismo <sentido> Z U perfil R Ia Ip Material [nombre_guardar]\n\n"
        "8 parametros obligatorios: sentido=X|Y, Z=1-4, U=A-D, perfil=S0-S4, R=8|7|6|3, Ia, Ip, Material\n"
        "Opcional 9º parametro 'nombre_guardar': guarda en results/ Markdown (.md) y Word (.docx).\n\n"
        "Material: concreto|acero|albañileria. Ej: cas sismo X 3 C S2 8 1 1 concreto\n\n"
        "Atajo rapido (calcula Ia/Ip por codigos):\n"
        "  cas sismo rapido <sentido> Z U perfil R Material <cod_altura> <cod_planta> [nombre_guardar]\n"
        "  Ej: cas sismo rapido X 3 C S2 8 concreto rb,masa tors\n\n"
        "Irregularidades:\n"
        "  cas sismo irregularidades               (muestra tablas de codigos)\n"
        "  cas sismo irregularidades calcular <cod_altura> <cod_planta>\n\n"
        "Otros: cas sismo results | cas sismo separacion <h> [da db]"
    )


_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def _strip_ansi(text: str) -> str:
    """Elimina códigos ANSI de color para generar Markdown limpio (sin ESC)."""
    return _ANSI_RE.sub("", text)


def _paso_a_markdown(bloque: str) -> str:
    """
    Convierte el texto CLI de un paso (incluye encabezado y tablas ASCII, con colores)
    en una seccion Markdown sin códigos ANSI:
    - Primera linea -> titulo '## ...'
    - Resto -> bloque de codigo ```text``` para respetar alineacion.
    """
    limpio = _strip_ansi(bloque)
    lineas = limpio.splitlines()
    if not lineas:
        return ""
    titulo = lineas[0].strip()
    cuerpo = "\n".join(lineas[1:]).strip("\n")
    if not cuerpo:
        return f"## {titulo}\n"
    return f"## {titulo}\n\n```text\n{cuerpo}\n```\n"


def _construir_salida_pasos(result: dict, sentido: str, zona: int, perfil: str,
                            categoria: str, r0: float, ia: float, ip: float,
                            material: str) -> tuple[list[str], list[str]]:
    """Construye listas salidas y md_partes desde el dict de ejecutar_analisis_sismico."""
    from axis.sismico.salida_pasos import (
        paso1_zona, paso2_perfil_desc, paso3_perfil_stptl, paso4_categoria_c_spectrum,
        paso6_sistema, paso7_irregularidad, paso8_coeficiente_r, paso9_periodo,
        paso10_masa, paso11_peso, paso12_estatico, paso12_dinamico, paso13_espectro,
        paso14_cortante_minima, paso15_hipotesis, paso16_distorsion,
    )
    z, u = result["z"], result["u"]
    filas_ct, filas_espectro = result["filas_ct"], result["filas_espectro"]
    s_val, tp, tl = result["s_val"], result["tp"], result["tl"]
    sep = "\n\n" + dim("-" * 50) + "\n\n"
    salidas = [heading(f"ANALISIS SISMICO E.030 - SENTIDO {sentido}\n") + dim("=" * 50) + "\n"]
    md_partes = [f"# ANALISIS SISMICO E.030 - SENTIDO {sentido}\n"]
    for paso_fn, *paso_args in [
        (paso1_zona, zona, z),
        (paso2_perfil_desc, perfil),
        (paso3_perfil_stptl, zona, perfil, s_val, tp, tl),
        (paso4_categoria_c_spectrum, categoria, u, filas_ct),
        (paso6_sistema, r0),
        (paso7_irregularidad, ia, ip),
        (paso8_coeficiente_r, r0, ia, ip, result["r"]),
        (paso9_periodo, sentido, result["periodo"], result["tbl_per"], result["tbl_modal"]),
        (paso10_masa, sentido, result["tbl_masa"], result["cumple_masa"]),
        (paso11_peso, result["df_peso"]),
        (paso12_estatico, sentido, result["tbl_est"]),
        (paso12_dinamico, sentido, result["tbl_din"]),
        (paso13_espectro, z, u, s_val, result["r"], filas_espectro),
    ]:
        txt = paso_fn(*paso_args)
        salidas.append(sep + txt if len(salidas) > 1 else txt)
        md_partes.append(_paso_a_markdown(txt))
    datos_cort = result["datos_cort"]
    tbl_base = datos_cort.get("tabla") if datos_cort else None
    p14 = paso14_cortante_minima(sentido, datos_cort, tbl_base)
    salidas.append(sep + p14)
    md_partes.append(_paso_a_markdown(p14))
    cl, k = result["cl"], result["k"]
    if cl:
        p15 = paso15_hipotesis(
            sentido,
            cl["cortante_basal_x"] if k == "x" else cl["cortante_basal_y"],
            cl["cortante_columnas_x"] if k == "x" else cl["cortante_columnas_y"],
            cl["cortante_muros_x"] if k == "x" else cl["cortante_muros_y"],
            cl["pct_porticos_x"] if k == "x" else cl["pct_porticos_y"],
            cl["porcentaje_muros_x"] if k == "x" else cl["porcentaje_muros_y"],
            cl["sistema_x"] if k == "x" else cl["sistema_y"],
        )
        salidas.append(sep + p15)
        md_partes.append(_paso_a_markdown(p15))
    dr = result["dr"]
    tbl_d = (dr["tabla_x"] if sentido == "X" else dr.get("tabla_y")) if dr else None
    tbl_v = (dr["tabla_verificacion_x"] if sentido == "X" else dr.get("tabla_verificacion_y")) if dr else None
    cumple_d = (dr["cumple_x"] if sentido == "X" else dr["cumple_y"]) if dr else False
    p16 = paso16_distorsion(
        sentido, material, obtener_distorsion_maxima(material),
        result["r"], tbl_d, tbl_v, cumple_d
    )
    salidas.append(sep + p16)
    md_partes.append(_paso_a_markdown(p16))
    salidas.append(sep + dim("Resultados: ") + "%s/results/" % result["path"])
    return salidas, md_partes


def handle_sismo_calcular(args: list[str]) -> str:
    """Flujo E.030: orquestación en flujo_sismo, presentación aquí."""
    from axis.data.etabs_table_reader import clear_table_cache
    clear_table_cache()
    if len(args) < 8:
        raise InvalidInput(
            "8 args obligatorios: sentido Z U perfil R Ia Ip Material "
            "(+ opcional 9º nombre_guardar). Ej: cas sismo X 3 C S2 8 1 1 concreto"
        )
    sentido = args[0].strip().upper()
    if sentido not in ("X", "Y"):
        raise InvalidInput("Sentido debe ser X o Y.")
    try:
        zona = int(args[1])
    except ValueError:
        raise InvalidInput("Z debe ser 1, 2, 3 o 4.")
    categoria = args[2].strip().upper()
    perfil = args[3].strip().lower()
    try:
        r0, ia, ip = float(args[4]), float(args[5]), float(args[6])
    except ValueError:
        raise InvalidInput("R, Ia, Ip deben ser numeros.")
    if r0 not in R0_VALIDOS:
        raise InvalidInput("R debe ser 8, 7, 6 o 3.")
    mat_in = args[7].strip().lower()
    material = MATERIAL_MAP.get(mat_in, mat_in)
    if material not in MATERIAL_MAP.values():
        raise InvalidInput("Material: concreto, acero o albañileria.")
    save_name = args[8].strip() if len(args) > 8 else ""
    path = _get_project_path()
    source = EtabsSource()
    result = ejecutar_analisis_sismico(
        source, sentido, zona, categoria, perfil, r0, ia, ip, material, path, log=False
    )
    salidas, md_partes = _construir_salida_pasos(
        result, sentido, zona, perfil, categoria, r0, ia, ip, material
    )
    resultado = "\n".join(salidas)
    if save_name:
        from pathlib import Path
        from axis.reportes.docx_sismo import generar_docx_sismo
        nombre_limpio = "".join(c for c in save_name if c.isalnum() or c in ("-", "_")).strip() or "analisis"
        base = f"sismo_analisis_{sentido}_{nombre_limpio}"
        try:
            results_dir = Path(path) / "results"
            results_dir.mkdir(parents=True, exist_ok=True)
            (results_dir / (base + ".md")).write_text("\n".join(md_partes), encoding="utf-8")
            docx_ok = generar_docx_sismo(md_partes, str(results_dir / (base + ".docx")))
            msg = f"Analisis guardado en results/: '{base}.md'" + (f", '{base}.docx'" if docx_ok else "")
            resultado += "\n\n" + dim(msg)
        except Exception as e:  # pragma: no cover
            resultado += "\n\n" + dim(f"No se pudo guardar analisis: {e}")
    return resultado


def handle_sismo_separacion(args: list[str]) -> str:
    """Paso 14 E.030: cas sismo separacion <h> [da db]. s = 0.006·h >= 0.03; s >= (2/3)·(da+db)."""
    if not args:
        raise InvalidInput("Uso: cas sismo separacion <h> [despl_a despl_b]. h en m.")
    try:
        h = float(args[0])
    except ValueError:
        raise InvalidInput("h debe ser un número (altura en m).")
    despl_a = float(args[1]) if len(args) > 1 else 0.0
    despl_b = float(args[2]) if len(args) > 2 else 0.0
    sep = separacion_edificios(h, despl_a, despl_b)
    salidas = [
        "Paso 14 – Separación de edificios (E.030)",
        "s ≥ 2/3 de la suma de los desplazamientos máximos de edificios adyacentes.",
        "s = 0.006·h ≥ 0.03. El mayor de todos estos valores será el valor de s.",
        "",
        "Tabla – Criterios y valor de s (m):",
        format_table(sep["tabla"]),
        "",
        f"→ Separación mínima a usar: s = {sep['s_final']:.4f} m",
    ]
    return "\n".join(salidas)


def handle_sismo_results(args: list[str]) -> str:
    """cas sismo results. Muestra resultados guardados (espectro C vs T y edificio)."""
    path = _get_project_path()
    salidas = ["Resultados sismo (guardados en results/)\n"]
    peligro = read_results_csv(path, "sismo_peligro_espectro.csv")
    if peligro:
        salidas.append("Espectro C vs T (sismo_peligro_espectro.csv):\n" + format_table(peligro))
    else:
        salidas.append("Sin espectro. Ejecute: cas sismo <zona> <perfil> <cat> <sist> <material>")
    edificio = read_results_csv(path, "sismo_edificio.csv")
    if edificio:
        salidas.append("\nCaracterización edificio (sismo_edificio.csv):\n" + format_table(edificio))
    else:
        salidas.append("\nSin sismo_edificio.csv. Ejecute: cas sismo <zona> <perfil> <cat> <sist> <material>")
    return "\n".join(salidas)


def _resumen_factores(factores: dict) -> str:
    ia, ip = float(factores["ia"]), float(factores["ip"])
    det_alt = factores["altura"]["detalles"]
    det_pla = factores["planta"]["detalles"]
    salidas = [
        heading("Factores de irregularidad E.030"),
        "",
        f"Ia (altura) = {ia:.2f}",
        f"Ip (planta) = {ip:.2f}",
        "",
        "Detalle altura:",
    ]
    if det_alt:
        salidas.append(format_table([
            {"Codigo": d["codigo"], "Descripcion": d["nombre"], "Ia": d["factor"]}
            for d in det_alt
        ]))
    else:
        salidas.append("Sin irregularidades en altura (Ia = 1.00).")
    salidas.append("")
    salidas.append("Detalle planta:")
    if det_pla:
        salidas.append(format_table([
            {"Codigo": d["codigo"], "Descripcion": d["nombre"], "Ip": d["factor"]}
            for d in det_pla
        ]))
    else:
        salidas.append("Sin irregularidades en planta (Ip = 1.00).")
    return "\n".join(salidas)


def handle_sismo_irregularidades(args: list[str]) -> str:
    """
    Comandos:
      cas sismo irregularidades
      cas sismo irregularidades calcular <cod_altura> <cod_planta>
    """
    if not args:
        salidas = [
            heading("Irregularidades E.030 - Codigos CLI"),
            "",
            "Altura (Ia):",
            format_table(tabla_codigos_altura()),
            "",
            "Planta (Ip):",
            format_table(tabla_codigos_planta()),
            "",
            "Uso:",
            "  cas sismo irregularidades calcular <cod_altura> <cod_planta>",
            "  <cod_...> = codigos separados por coma; use '-' o 'ninguna' si no aplica.",
            "Ejemplo:",
            "  cas sismo irregularidades calcular rb,masa tors",
        ]
        return "\n".join(salidas)
    sub = args[0].lower()
    if sub in ("help", "-h", "--help"):
        return handle_sismo_irregularidades([])
    if sub in ("calcular", "calc"):
        if len(args) < 3:
            raise InvalidInput(
                "Uso: cas sismo irregularidades calcular <cod_altura> <cod_planta>"
            )
        try:
            factores = calcular_factores_irregularidad(args[1], args[2])
        except ValueError as e:
            raise InvalidInput(str(e))
        return _resumen_factores(factores)
    raise InvalidInput("Subcomando desconocido en irregularidades. Use: calcular")


def handle_sismo_rapido(args: list[str]) -> str:
    """
    cas sismo rapido <sentido> Z U perfil R Material <cod_altura> <cod_planta> [nombre_guardar]
    Convierte codigos E.030 en Ia/Ip y ejecuta el flujo normal.
    """
    if len(args) < 8:
        raise InvalidInput(
            "Uso: cas sismo rapido <sentido> Z U perfil R Material <cod_altura> <cod_planta> [nombre_guardar]"
        )
    sentido, z, u, perfil, r = args[0], args[1], args[2], args[3], args[4]
    material, cod_altura, cod_planta = args[5], args[6], args[7]
    nombre = args[8] if len(args) > 8 else ""
    try:
        factores = calcular_factores_irregularidad(cod_altura, cod_planta)
    except ValueError as e:
        raise InvalidInput(str(e))
    ia_txt = f"{float(factores['ia']):g}"
    ip_txt = f"{float(factores['ip']):g}"
    normales = [sentido, z, u, perfil, r, ia_txt, ip_txt, material]
    if nombre:
        normales.append(nombre)
    cab = _resumen_factores(factores)
    resultado = handle_sismo_calcular(normales)
    return cab + "\n\n" + resultado
