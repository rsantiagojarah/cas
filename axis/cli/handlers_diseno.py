"""Handlers CLI: diseño (flexión, cortante) y resultados. Reglas: ≤200 líneas, ≤150 chars.

Flujo diseño losas: losa define [nombre] fc fy b h rec → losa momento add [losa] nombre Mu
(por cada momento) → flexion losa (sin args) → tabla propiedades losa(s) + tabla
diseño a flexión (As req. por momento). Varias losas: nombre por losa y momento add con nombre_losa.
"""

from __future__ import annotations

from axis.core.exceptions import NoActiveProject, InvalidInput
from axis.core.project import get_active_project_path
from axis.core.database import read_csv, write_csv, read_results_csv, write_results_csv
from axis.core.utils import to_float
from axis.engine.engine import run
from axis.cli.tables import format_table, CORTANTE_HEADER_MAP

from axis.cli.handlers import get_base_path
from axis.cli.handlers_vigas import ensure_vu_column
from axis.operations import flexion, cortante  # noqa: F401

# Resumen y fórmulas que se muestran al ejecutar "cas flexion losa"
FLUJO_FLEXION_LOSA = """
Flujo de diseño (E.060, losa simplemente reforzada, sin As'):
  • d = h - rec
  • Bloque Whitney: a = d - √(d² - 2·Mu/(φ·0.85·fc·b))   [Art. 10.2.7.1], φ=0.9
  • Cuantía balanceada: c_bal = εc·d/(εc + fy/Es), a_bal = β1·c_bal, a_max = 0.75·a_bal   [Art. 10.3.4]
  • Si a > a_max → no se calcula As, se indica * en As req.
  • As por momento: As = Mu/(φ·fy·(d - a/2))   [Art. 10.2]
  • As mínima losa: Asmin = 0.0018·b·d
  • As máxima VSR: Asmax = 0.85·fc·a_max·b/fy   [Art. 10.3.5]
  • As req. = max(As, Asmin). Unidades: Mu en Tn-m, fc/fy kg/cm², b/h/rec cm.

"""

# Resumen y fórmulas que se muestran al ejecutar "cas cortante losa"
FLUJO_CORTANTE_LOSA = """
Flujo de diseño cortante losa (E.060, sin estribos; todo el cortante lo absorbe el concreto):
  • d = h - rec
  • Vc = 0.53·√(fc)·b·d   [Art. 11.3.1], unidades kg (fc kg/cm², b y d cm)
  • φ = 0.85   [Art. 9.3.2.1]
  • Verificación: Vu ≤ φ·Vc  → Cumple (Sí/No). Si Vu > φ·Vc se debe aumentar peralte o fc.
  • Unidades: Vu en Tn, fc kg/cm², b/h/rec cm.

"""


def handle_losa_define(args: list[str]) -> str:
    """cas losa define <nombre> <fc> <fy> <b> <h> <rec>"""
    project_path = get_active_project_path(get_base_path())
    if not project_path:
        raise NoActiveProject("No hay proyecto activo. Use 'cas use <proyecto>'.")
    if len(args) < 5:
        raise InvalidInput("Uso: cas losa define [nombre] <fc> <fy> <b> <h> <rec>")
    if len(args) >= 6:
        nombre, fc, fy, b, h, rec = args[0], args[1], args[2], args[3], args[4], args[5]
    else:
        nombre, fc, fy, b, h, rec = "", args[0], args[1], args[2], args[3], args[4]
    row = {"nombre": nombre, "fc": fc, "fy": fy, "b": b, "h": h, "rec": rec}
    rows = read_csv(project_path, "losa")
    if rows and "nombre" not in rows[0]:
        rows = []
    idx = next((i for i, r in enumerate(rows) if r.get("nombre") == nombre), None)
    if idx is not None:
        rows[idx] = row
    else:
        rows.append(row)
    write_csv(project_path, rows, "losa")
    return f"Losa '{nombre or '(sin nombre)'}' definida: fc={fc}, fy={fy}, b={b}, h={h}, rec={rec}."


def handle_losa_list(args: list[str]) -> str:
    """cas losa list"""
    project_path = get_active_project_path(get_base_path())
    if not project_path:
        raise NoActiveProject("No hay proyecto activo. Use 'cas use <proyecto>'.")
    rows = read_csv(project_path, "losa")
    if not rows:
        return "No hay losas. Use: cas losa define [nombre] <fc> <fy> <b> <h> <rec>"
    for i, r in enumerate(rows):
        r["N"] = str(i + 1)
    cols = ["N", "nombre", "fc", "fy", "b", "h", "rec"] if "nombre" in rows[0] else ["N", "fc", "fy", "b", "h", "rec"]
    return "Losas\n\n" + format_table(rows, columns=cols)


def handle_losa_delete(args: list[str]) -> str:
    """cas losa delete <nombre|índice>"""
    project_path = get_active_project_path(get_base_path())
    if not project_path:
        raise NoActiveProject("No hay proyecto activo. Use 'cas use <proyecto>'.")
    if not args:
        raise InvalidInput("Uso: cas losa delete <nombre>  o  cas losa delete <índice>")
    ident = args[0]
    rows = read_csv(project_path, "losa")
    if not rows:
        raise InvalidInput("No hay losas.")
    try:
        idx = int(ident)
        if idx < 1 or idx > len(rows):
            raise InvalidInput(f"Índice {idx} inválido. Hay {len(rows)} losa(s). Use 'cas losa list'.")
        nombre_borrar = rows[idx - 1].get("nombre", "")
        pop_idx = idx - 1
    except ValueError:
        nombre_borrar = ident
        pop_idx = next((i for i, r in enumerate(rows) if r.get("nombre") == nombre_borrar), None)
        if pop_idx is None:
            raise InvalidInput(f"No hay losa con nombre '{nombre_borrar}'. Use 'cas losa list'.")
    rows.pop(pop_idx)
    write_csv(project_path, rows, "losa")
    momentos = read_csv(project_path, "losa_momentos")
    n_antes = len(momentos)
    if momentos and "losa" in momentos[0]:
        momentos = [m for m in momentos if m.get("losa", "") != nombre_borrar]
        write_csv(project_path, momentos, "losa_momentos")
    quitar_m = n_antes - len(momentos)
    cortantes = read_csv(project_path, "losa_cortante")
    n_c = len(cortantes)
    if cortantes and "losa" in cortantes[0]:
        cortantes = [c for c in cortantes if c.get("losa", "") != nombre_borrar]
        write_csv(project_path, cortantes, "losa_cortante")
    quitar_c = n_c - len(cortantes)
    msg = f"Losa '{nombre_borrar or ident}' eliminada."
    if quitar_m > 0 or quitar_c > 0:
        msg += f" {quitar_m} momento(s), {quitar_c} cortante(s) de esa losa también eliminados."
    return msg


def handle_losa_momento(args: list[str]) -> str:
    """cas losa momento add <nombre_losa> <nombre> <Mu>  |  list [losa]  |  delete <i>"""
    project_path = get_active_project_path(get_base_path())
    if not project_path:
        raise NoActiveProject("No hay proyecto activo. Use 'cas use <proyecto>'.")
    if not args:
        raise InvalidInput("Uso: cas losa momento add <nombre_losa> <nombre> <Mu>  |  list  |  delete <i>")
    sub = args[0].lower()
    if sub == "add":
        if len(args) < 3:
            raise InvalidInput(
                "Uso: cas losa momento add [nombre_losa] <nombre> <Mu>  (nombre puede ser varias palabras)"
            )
        if len(args) == 3:
            nombre_losa = (read_csv(project_path, "losa") or [{}])[0].get("nombre", "")
            nombre_mom = args[1]
            mu_val = args[2]
        else:
            nombre_losa = args[1]
            mu_val = args[-1]
            nombre_mom = " ".join(args[2:-1]).strip() or "—"
        try:
            to_float(mu_val)
        except (ValueError, TypeError):
            raise InvalidInput(f"Mu debe ser numérico: {mu_val}")
        rows = read_csv(project_path, "losa_momentos")
        nueva = {"losa": nombre_losa, "nombre": nombre_mom, "Mu": mu_val}
        idx = next((i for i, r in enumerate(rows) if r.get("losa", "") == nombre_losa and r.get("nombre", "") == nombre_mom), None)
        if idx is not None:
            rows[idx] = nueva
            msg = "Momento actualizado"
        else:
            rows.append(nueva)
            msg = "Momento añadido"
        write_csv(project_path, rows, "losa_momentos")
        return f"{msg} a '{nombre_losa}': '{nombre_mom}' Mu={mu_val}."
    if sub == "list":
        rows = read_csv(project_path, "losa_momentos")
        if not rows:
            return "No hay momentos. Use: cas losa momento add <nombre_losa> <nombre> <Mu>"
        filtro = args[1] if len(args) > 1 else None
        if filtro and "losa" in rows[0]:
            rows = [r for r in rows if r.get("losa") == filtro]
        if not rows:
            return f"No hay momentos para la losa '{filtro}'."
        for i, r in enumerate(rows):
            r["N"] = str(i + 1)
        cols = ["N", "losa", "nombre", "Mu"] if rows and "losa" in rows[0] else ["N", "nombre", "Mu"]
        return "Momentos\n\n" + format_table(rows, columns=cols)
    if sub == "delete":
        if len(args) < 2:
            raise InvalidInput("Uso: cas losa momento delete <indice>")
        try:
            idx = int(args[1])
        except ValueError:
            raise InvalidInput("El índice debe ser un número.")
        rows = read_csv(project_path, "losa_momentos")
        if idx < 1 or idx > len(rows):
            raise InvalidInput(f"Índice {idx} inválido. Hay {len(rows)} momento(s).")
        rows.pop(idx - 1)
        write_csv(project_path, rows, "losa_momentos")
        return f"Momento {idx} eliminado."
    raise InvalidInput("Uso: cas losa momento add <nombre_losa> <nombre> <Mu>  |  list  |  delete <i>")


def handle_losa_cortante(args: list[str]) -> str:
    """cas losa cortante add <nombre_losa> <nombre> <Vu>  |  list [losa]  |  delete <i>"""
    project_path = get_active_project_path(get_base_path())
    if not project_path:
        raise NoActiveProject("No hay proyecto activo. Use 'cas use <proyecto>'.")
    if not args:
        raise InvalidInput("Uso: cas losa cortante add <nombre_losa> <nombre> <Vu>  |  list  |  delete <i>")
    sub = args[0].lower()
    if sub == "add":
        if len(args) < 3:
            raise InvalidInput("Uso: cas losa cortante add [nombre_losa] <nombre> <Vu>")
        if len(args) == 3:
            nombre_losa = (read_csv(project_path, "losa") or [{}])[0].get("nombre", "")
            nombre_v = args[1]
            vu_val = args[2]
        else:
            nombre_losa = args[1]
            vu_val = args[-1]
            nombre_v = " ".join(args[2:-1]).strip() or "—"
        try:
            to_float(vu_val)
        except (ValueError, TypeError):
            raise InvalidInput(f"Vu debe ser numérico: {vu_val}")
        rows = read_csv(project_path, "losa_cortante")
        nueva = {"losa": nombre_losa, "nombre": nombre_v, "Vu": vu_val}
        idx = next((i for i, r in enumerate(rows) if r.get("losa", "") == nombre_losa and r.get("nombre", "") == nombre_v), None)
        if idx is not None:
            rows[idx] = nueva
            msg = "Cortante actualizado"
        else:
            rows.append(nueva)
            msg = "Cortante añadido"
        write_csv(project_path, rows, "losa_cortante")
        return f"{msg} a '{nombre_losa}': '{nombre_v}' Vu={vu_val}."
    if sub == "list":
        rows = read_csv(project_path, "losa_cortante")
        if not rows:
            return "No hay cortantes. Use: cas losa cortante add <nombre_losa> <nombre> <Vu>"
        filtro = args[1] if len(args) > 1 else None
        if filtro and "losa" in rows[0]:
            rows = [r for r in rows if r.get("losa") == filtro]
        if not rows:
            return f"No hay cortantes para la losa '{filtro}'."
        for i, r in enumerate(rows):
            r["N"] = str(i + 1)
        cols = ["N", "losa", "nombre", "Vu"] if rows and "losa" in rows[0] else ["N", "nombre", "Vu"]
        return "Cortantes\n\n" + format_table(rows, columns=cols)
    if sub == "delete":
        if len(args) < 2:
            raise InvalidInput("Uso: cas losa cortante delete <indice>")
        try:
            idx = int(args[1])
        except ValueError:
            raise InvalidInput("El índice debe ser un número.")
        rows = read_csv(project_path, "losa_cortante")
        if idx < 1 or idx > len(rows):
            raise InvalidInput(f"Índice {idx} inválido. Hay {len(rows)} cortante(s).")
        rows.pop(idx - 1)
        write_csv(project_path, rows, "losa_cortante")
        return f"Cortante {idx} eliminado."
    raise InvalidInput("Uso: cas losa cortante add <nombre_losa> <nombre> <Vu>  |  list  |  delete <i>")


def handle_flexion_viga(args: list[str]) -> str:
    """cas flexion viga"""
    project_path = get_active_project_path(get_base_path())
    if not project_path:
        raise NoActiveProject("No hay proyecto activo. Use 'cas use <proyecto>'.")
    rows = read_csv(project_path, "vigas")
    if not rows:
        raise InvalidInput("elements/vigas.csv está vacío. Añada vigas con fc, fy, b, h, rec, Mu")
    required = ("fc", "fy", "b", "h", "rec", "Mu")
    for row in rows:
        missing = [k for k in required if k not in row or row[k] == ""]
        if missing:
            raise InvalidInput(f"Faltan columnas en vigas.csv: {missing}")
    result = run("flexion", "viga", {"vigas": rows})
    resultados = result.get("resultados", [])
    out_path = write_results_csv(project_path, "flexion_viga.csv", resultados)
    for i, r in enumerate(resultados):
        r["N"] = str(i + 1)
    cols = ["N"] + [k for k in resultados[0].keys() if k != "N"] if resultados else []
    tabla = format_table(resultados, columns=cols) if cols else ""
    return f"Flexión calculada: {len(resultados)} viga(s).\nResultados: {out_path}\n\n{tabla}"


def handle_flexion_losa(args: list[str]) -> str:
    """cas flexion losa [nombre fc fy b h rec Mu] o usa losa + losa_momentos."""
    project_path = get_active_project_path(get_base_path())
    if not project_path:
        raise NoActiveProject("No hay proyecto activo. Use 'cas use <proyecto>'.")
    slab_rows_para_tabla = []
    if len(args) >= 8 and args[0].lower() == "add":
        rows = [{"nombre": args[1], "fc": args[2], "fy": args[3], "b": args[4],
                 "h": args[5], "rec": args[6], "Mu": args[7]}]
    elif len(args) >= 7:
        rows = [{"nombre": args[0], "fc": args[1], "fy": args[2], "b": args[3],
                 "h": args[4], "rec": args[5], "Mu": args[6]}]
    else:
        slab_rows = read_csv(project_path, "losa")
        momentos = read_csv(project_path, "losa_momentos")
        if slab_rows and momentos:
            for s in slab_rows:
                for k in ("fc", "fy", "b", "h", "rec"):
                    if k not in s or s[k] == "":
                        raise InvalidInput(f"Losa incompleta en elements/losa.csv: falta {k}.")
            tiene_col_losa = momentos and "losa" in momentos[0]
            una_sola_losa = len(slab_rows) == 1
            rows = []
            for slab in slab_rows:
                nom_slab = slab.get("nombre", "")
                for m in momentos:
                    if tiene_col_losa:
                        if m.get("losa", "") != nom_slab:
                            continue
                    elif not una_sola_losa:
                        continue
                    rows.append({
                        **slab, "nombre": m.get("nombre", "—"), "Mu": m.get("Mu", ""),
                        "losa": nom_slab,
                    })
            if not rows:
                raise InvalidInput(
                    "Ningún momento coincide con una losa. Use: cas losa momento add <nombre_losa> <nombre> <Mu>."
                )
            slab_rows_para_tabla = slab_rows
        else:
            rows = read_csv(project_path, "losas")
            if not rows:
                raise InvalidInput(
                    "Defina la losa con 'cas losa define' y 'cas losa momento add', o use: "
                    "cas flexion losa <nombre> <fc> <fy> <b> <h> <rec> <Mu>"
                )
            required = ("fc", "fy", "b", "h", "rec", "Mu")
            for row in rows:
                missing = [k for k in required if k not in row or row[k] == ""]
                if missing:
                    raise InvalidInput(f"Faltan columnas en losas.csv: {missing}")
    result = run("flexion", "losa", {"losas": rows})
    resultados = result.get("resultados", [])
    out_path = write_results_csv(project_path, "flexion_losa.csv", resultados)
    for i, r in enumerate(resultados):
        r["N"] = str(i + 1)
    base_cols = [k for k in resultados[0].keys() if k != "N"] if resultados else []
    cols = (["N", "losa"] + [k for k in base_cols if k != "losa"]) if resultados and "losa" in resultados[0] else ["N"] + base_cols
    tabla_diseno = format_table(resultados, columns=cols) if cols else ""
    resumen = f"Flexión calculada: {len(resultados)} momento(s). Resultados: {out_path}"
    encabezado = FLUJO_FLEXION_LOSA
    if slab_rows_para_tabla:
        slab_cols = ["nombre", "fc", "fy", "b", "h", "rec"] if slab_rows_para_tabla[0].get("nombre") else ["fc", "fy", "b", "h", "rec"]
        tabla_losa = format_table(slab_rows_para_tabla, columns=slab_cols)
        return f"{encabezado}Losa (propiedades)\n\n{tabla_losa}\n\nDiseño a flexión\n\n{tabla_diseno}\n\n{resumen}"
    return f"{encabezado}{resumen}\n\n{tabla_diseno}"


def handle_results_flexion(args: list[str]) -> str:
    """cas results flexion [viga|losa]"""
    project_path = get_active_project_path(get_base_path())
    if not project_path:
        raise NoActiveProject("No hay proyecto activo. Use 'cas use <proyecto>'.")
    tipo = (args[0].lower() if args else "viga").strip()
    if tipo == "losa":
        csv_name, titulo = "flexion_losa.csv", "Flexión (losas)"
    else:
        csv_name, titulo = "flexion_viga.csv", "Flexión (vigas)"
    rows = read_results_csv(project_path, csv_name)
    if not rows:
        raise InvalidInput(
            f"No hay resultados de flexión para {tipo}. Ejecute 'cas flexion {tipo}' primero."
        )
    for i, row in enumerate(rows):
        row["N"] = str(i + 1)
    cols = ["N"] + [k for k in rows[0].keys() if k != "N"]
    return f"{titulo}\n\n" + format_table(rows, columns=cols)


def handle_cortante_viga(args: list[str]) -> str:
    """cas cortante viga"""
    project_path = get_active_project_path(get_base_path())
    if not project_path:
        raise NoActiveProject("No hay proyecto activo. Use 'cas use <proyecto>'.")
    rows = read_csv(project_path, "vigas")
    if not rows:
        raise InvalidInput("elements/vigas.csv está vacío. Añada vigas con fc, fy, b, h, rec, Vu")
    required = ("fc", "fy", "b", "h", "rec")
    for row in rows:
        missing = [k for k in required if k not in row or row[k] == ""]
        if missing:
            raise InvalidInput(f"Faltan columnas en vigas.csv: {missing}")
    ensure_vu_column(rows)
    result = run("cortante", "viga", {"vigas": rows})
    resultados = result.get("resultados", [])
    out_path = write_results_csv(project_path, "cortante_viga.csv", resultados)
    return f"Cortante calculada: {len(resultados)} viga(s).\nResultados: {out_path}"


def handle_cortante_losa(args: list[str]) -> str:
    """cas cortante losa: usa losa + losa_cortante; muestra flujo, tabla losas y tabla diseño."""
    project_path = get_active_project_path(get_base_path())
    if not project_path:
        raise NoActiveProject("No hay proyecto activo. Use 'cas use <proyecto>'.")
    slab_rows = read_csv(project_path, "losa")
    cortantes = read_csv(project_path, "losa_cortante")
    if not slab_rows or not cortantes:
        raise InvalidInput(
            "Defina losas y cortantes: cas losa define, cas losa cortante add <nombre_losa> <nombre> <Vu>"
        )
    for s in slab_rows:
        for k in ("fc", "b", "h", "rec"):
            if k not in s or s[k] == "":
                raise InvalidInput(f"Losa incompleta en elements/losa.csv: falta {k}.")
    tiene_col_losa = "losa" in cortantes[0]
    una_sola_losa = len(slab_rows) == 1
    rows = []
    for slab in slab_rows:
        nom_slab = slab.get("nombre", "")
        for c in cortantes:
            if tiene_col_losa and c.get("losa", "") != nom_slab:
                continue
            if not una_sola_losa and not tiene_col_losa:
                continue
            rows.append({
                **slab, "nombre": c.get("nombre", "—"), "Vu": c.get("Vu", ""), "losa": nom_slab,
            })
    if not rows:
        raise InvalidInput("Ningún cortante coincide con una losa. Use: cas losa cortante add <nombre_losa> <nombre> <Vu>.")
    result = run("cortante", "losa", {"losas": rows})
    resultados = result.get("resultados", [])
    out_path = write_results_csv(project_path, "cortante_losa.csv", resultados)
    for i, r in enumerate(resultados):
        r["N"] = str(i + 1)
    base_cols = [k for k in resultados[0].keys() if k != "N"] if resultados else []
    cols = (["N", "losa"] + [k for k in base_cols if k != "losa"]) if resultados and "losa" in resultados[0] else ["N"] + base_cols
    tabla_diseno = format_table(resultados, columns=cols) if cols else ""
    resumen = f"Cortante calculado: {len(resultados)} sección(es). Resultados: {out_path}"
    slab_cols = ["nombre", "fc", "fy", "b", "h", "rec"] if slab_rows[0].get("nombre") else ["fc", "fy", "b", "h", "rec"]
    tabla_losa = format_table(slab_rows, columns=slab_cols)
    return f"{FLUJO_CORTANTE_LOSA}Losa (propiedades)\n\n{tabla_losa}\n\nDiseño a cortante\n\n{tabla_diseno}\n\n{resumen}"


def handle_results_cortante(args: list[str]) -> str:
    """cas results cortante"""
    project_path = get_active_project_path(get_base_path())
    if not project_path:
        raise NoActiveProject("No hay proyecto activo. Use 'cas use <proyecto>'.")
    rows = read_results_csv(project_path, "cortante_viga.csv")
    if not rows:
        raise InvalidInput("No hay resultados de cortante. Ejecute 'cas cortante viga' primero.")
    for i, row in enumerate(rows):
        row["N"] = str(i + 1)
    cols = ["N"] + [k for k in rows[0].keys() if k != "N"]
    return "Cortante\n\n" + format_table(rows, columns=cols, header_map=CORTANTE_HEADER_MAP)
