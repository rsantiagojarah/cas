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


def _nombres_momentos_estructurados(tramos: int, secciones: int, momentos_por_seccion: int) -> list[str]:
    """Genera nombres en orden: tramo -> sección -> momento (neg, pos si hay 2)."""
    nombres = []
    sufijos = ("_neg", "_pos") if momentos_por_seccion == 2 else ("",)
    for t in range(1, tramos + 1):
        for s in range(1, secciones + 1):
            for k in range(momentos_por_seccion):
                suf = sufijos[k] if momentos_por_seccion == 2 else ""
                if tramos == 1 and secciones == 1:
                    nom = ("neg", "pos")[k] if momentos_por_seccion == 2 else "M1"
                elif tramos == 1:
                    nom = f"S{s}{suf}"
                elif secciones == 1:
                    nom = f"T{t}{suf}"
                else:
                    nom = f"T{t}_S{s}{suf}"
                nombres.append(nom)
    return nombres

# Procedimiento de diseño que se muestra al ejecutar "cas flexion viga"
FLUJO_FLEXION_VIGA = """
Procedimiento de diseño a flexión vigas (E.060, criterio cuantía máxima):
  • d = h - rec; se usa |Mu| (momento en valor absoluto). Mu = 0 → As req. = Asmin.
  • Bloque Whitney: a = d - √(d² - 2·Mu/(φ·0.85·fc·b))   [Art. 10.2.7.1], φ=0.9
  • a_max = 0.75·a_bal (cuantía balanceada)   [Art. 10.3.4]
  • Si a ≤ a_max → VSR: As = Mu/(φ·fy·(d - a/2)), As' = 0   [Art. 10.2]
  • Si a > a_max → VDR: As y As' por equilibrio (acero en compresión)
  • Asmin vigas: max(0.7√fc·b·d/fy, 1.4·b·d/fy)   [Art. 10.5.1]
  • As_colocar = max(As por momento, Asmin). Unidades: Mu Tn-m, fc/fy kg/cm², b/h/rec cm.

"""

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
# Procedimiento que se muestra al ejecutar "cas cortante viga"
FLUJO_CORTANTE_VIGA = """
Procedimiento de diseño a cortante vigas (E.060):
  • d = h - rec; Vu en Tn. Vc = 0.53·√(fc)·b·d   [Art. 11.3.1], φ = 0.85
  • Si Vu ≤ φ·Vc/2: no se requiere refuerzo por cortante (Av/s = 0)
  • Si φ·Vc/2 < Vu ≤ φ·Vn_max: Vs = Vu/φ - Vc; Av/s = Vs/(fy·d)   [Art. 11.3.1]
  • Si Vu > φ·Vn_max: aumentar peralte o fc (sección insuficiente)
  • Vs_max = 2.1·√(fc)·b·d; Vn_max = Vc + Vs_max. s_max según Art. 11.3.1.

"""

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


def handle_viga_define(args: list[str]) -> str:
    """cas viga define [nombre] fc fy b h rec"""
    project_path = get_active_project_path(get_base_path())
    if not project_path:
        raise NoActiveProject("No hay proyecto activo. Use 'cas use <proyecto>'.")
    if len(args) < 5:
        raise InvalidInput("Uso: cas viga define [nombre] <fc> <fy> <b> <h> <rec>")
    if len(args) >= 6:
        nombre, fc, fy, b, h, rec = args[0], args[1], args[2], args[3], args[4], args[5]
    else:
        nombre, fc, fy, b, h, rec = "", args[0], args[1], args[2], args[3], args[4]
    row = {"nombre": nombre, "fc": fc, "fy": fy, "b": b, "h": h, "rec": rec}
    rows = read_csv(project_path, "viga")
    if rows and "nombre" not in rows[0]:
        rows = []
    idx = next((i for i, r in enumerate(rows) if r.get("nombre") == nombre), None)
    if idx is not None:
        rows[idx] = row
    else:
        rows.append(row)
    write_csv(project_path, rows, "viga")
    return f"Viga '{nombre or '(sin nombre)'}' definida: fc={fc}, fy={fy}, b={b}, h={h}, rec={rec}."


def handle_viga_list(args: list[str]) -> str:
    """cas viga list"""
    project_path = get_active_project_path(get_base_path())
    if not project_path:
        raise NoActiveProject("No hay proyecto activo. Use 'cas use <proyecto>'.")
    rows = read_csv(project_path, "viga")
    if not rows:
        return "No hay vigas. Use: cas viga define [nombre] <fc> <fy> <b> <h> <rec>"
    for i, r in enumerate(rows):
        r["N"] = str(i + 1)
    cols = ["N", "nombre", "fc", "fy", "b", "h", "rec"] if "nombre" in rows[0] else ["N", "fc", "fy", "b", "h", "rec"]
    return "Vigas\n\n" + format_table(rows, columns=cols)


def handle_viga_delete(args: list[str]) -> str:
    """cas viga delete <nombre|índice>"""
    project_path = get_active_project_path(get_base_path())
    if not project_path:
        raise NoActiveProject("No hay proyecto activo. Use 'cas use <proyecto>'.")
    if not args:
        raise InvalidInput("Uso: cas viga delete <nombre>  o  cas viga delete <índice>")
    ident = args[0]
    rows = read_csv(project_path, "viga")
    if not rows:
        raise InvalidInput("No hay vigas.")
    try:
        idx = int(ident)
        if idx < 1 or idx > len(rows):
            raise InvalidInput(f"Índice {idx} inválido. Hay {len(rows)} viga(s). Use 'cas viga list'.")
        nombre_borrar = rows[idx - 1].get("nombre", "")
        pop_idx = idx - 1
    except ValueError:
        nombre_borrar = ident
        pop_idx = next((i for i, r in enumerate(rows) if r.get("nombre") == nombre_borrar), None)
        if pop_idx is None:
            raise InvalidInput(f"No hay viga con nombre '{nombre_borrar}'. Use 'cas viga list'.")
    rows.pop(pop_idx)
    write_csv(project_path, rows, "viga")
    momentos = read_csv(project_path, "viga_momentos")
    n_antes = len(momentos)
    if momentos and "viga" in momentos[0]:
        momentos = [m for m in momentos if m.get("viga", "") != nombre_borrar]
        write_csv(project_path, momentos, "viga_momentos")
    quitar_m = n_antes - len(momentos)
    cortantes = read_csv(project_path, "viga_cortante")
    n_c = len(cortantes)
    if cortantes and "viga" in cortantes[0]:
        cortantes = [c for c in cortantes if c.get("viga", "") != nombre_borrar]
        write_csv(project_path, cortantes, "viga_cortante")
    quitar_c = n_c - len(cortantes)
    msg = f"Viga '{nombre_borrar or ident}' eliminada."
    if quitar_m > 0 or quitar_c > 0:
        msg += f" {quitar_m} momento(s), {quitar_c} cortante(s) de esa viga también eliminados."
    return msg


def _es_entero_positivo(s: str) -> bool:
    return s.isdigit() and int(s) >= 1


def _filas_momentos_orden_flexion(project_path) -> list[dict]:
    """Lista (viga, nombre, Mu...) en el mismo orden que la tabla de cas flexion viga."""
    viga_rows = read_csv(project_path, "viga")
    momentos = read_csv(project_path, "viga_momentos")
    if not viga_rows or not momentos or "viga" not in (momentos[0] or {}):
        return []
    tiene_col = "viga" in momentos[0]
    una_sola = len(viga_rows) == 1
    out = []
    for beam in viga_rows:
        nom_viga = beam.get("nombre", "")
        for m in momentos:
            if tiene_col and m.get("viga", "") != nom_viga:
                continue
            if not una_sola and not tiene_col:
                continue
            out.append({"viga": nom_viga, "nombre": m.get("nombre", "—")})
    return out


def handle_viga_momento(args: list[str]) -> str:
    """cas viga momento add ... | list | delete <i> | delete <viga> <nombre>"""
    project_path = get_active_project_path(get_base_path())
    if not project_path:
        raise NoActiveProject("No hay proyecto activo. Use 'cas use <proyecto>'.")
    if not args:
        raise InvalidInput("Uso: cas viga momento add [nombre_viga|índice] <nombre> <Mu>  |  Mu1 Mu2...  |  T S M Mu...")
    sub = args[0].lower()
    if sub == "add":
        if len(args) < 3:
            raise InvalidInput("Uso: cas viga momento add [nombre_viga|índice] <nombre> <Mu>  |  Mu1 Mu2...  |  T S M Mu...")
        if len(args) == 3:
            vigas = read_csv(project_path, "viga") or [{}]
            nombre_viga = vigas[0].get("nombre", "") if vigas else ""
            nombre_mom = args[1]
            mu_val = args[2]
            to_float(mu_val)
            rows = read_csv(project_path, "viga_momentos")
            nueva = {"viga": nombre_viga, "nombre": nombre_mom, "Mu": mu_val}
            idx = next((i for i, r in enumerate(rows) if r.get("viga", "") == nombre_viga and r.get("nombre", "") == nombre_mom), None)
            if idx is not None:
                rows[idx] = nueva
            else:
                rows.append(nueva)
            write_csv(project_path, rows, "viga_momentos")
            return f"Momento añadido a '{nombre_viga}': '{nombre_mom}' Mu={mu_val}."
        ident_viga = args[1]
        rest = args[2:]
        vigas = read_csv(project_path, "viga") or []
        if ident_viga.isdigit():
            idx_v = int(ident_viga)
            if idx_v < 1 or idx_v > len(vigas):
                raise InvalidInput(f"Índice {idx_v} inválido. Hay {len(vigas)} viga(s). Use 'cas viga list'.")
            nombre_viga = vigas[idx_v - 1].get("nombre", "")
        else:
            nombre_viga = ident_viga
        try:
            to_float(rest[0])
            primer_es_num = True
        except (ValueError, TypeError, InvalidInput):
            primer_es_num = False
        if not primer_es_num:
            nombre_mom = " ".join(rest[:-1]).strip() or "—"
            mu_val = rest[-1]
            to_float(mu_val)
            rows = read_csv(project_path, "viga_momentos")
            nueva = {"viga": nombre_viga, "nombre": nombre_mom, "Mu": mu_val}
            idx = next((i for i, r in enumerate(rows) if r.get("viga", "") == nombre_viga and r.get("nombre", "") == nombre_mom), None)
            if idx is not None:
                rows[idx] = nueva
            else:
                rows.append(nueva)
            write_csv(project_path, rows, "viga_momentos")
            return f"Momento añadido a '{nombre_viga}': '{nombre_mom}' Mu={mu_val}."
        if len(rest) >= 4 and _es_entero_positivo(rest[0]) and _es_entero_positivo(rest[1]) and _es_entero_positivo(rest[2]):
            t, s, m = int(rest[0]), int(rest[1]), int(rest[2])
            n = t * s * m
            if len(rest) == 3 + n:
                mu_vals = rest[3:3 + n]
                for v in mu_vals:
                    to_float(v)
                nombres = _nombres_momentos_estructurados(t, s, m)
                rows = read_csv(project_path, "viga_momentos")
                for i, nom in enumerate(nombres):
                    nueva = {"viga": nombre_viga, "nombre": nom, "Mu": mu_vals[i]}
                    idx = next((j for j, r in enumerate(rows) if r.get("viga", "") == nombre_viga and r.get("nombre", "") == nom), None)
                    if idx is not None:
                        rows[idx] = nueva
                    else:
                        rows.append(nueva)
                write_csv(project_path, rows, "viga_momentos")
                return f"{n} momento(s) añadido(s) a '{nombre_viga}' (estructura {t}×{s}×{m})."
        nombres = [f"M{i + 1}" for i in range(len(rest))]
        for v in rest:
            to_float(v)
        rows = read_csv(project_path, "viga_momentos")
        for i, mu_val in enumerate(rest):
            nom = nombres[i]
            nueva = {"viga": nombre_viga, "nombre": nom, "Mu": mu_val}
            idx = next((j for j, r in enumerate(rows) if r.get("viga", "") == nombre_viga and r.get("nombre", "") == nom), None)
            if idx is not None:
                rows[idx] = nueva
            else:
                rows.append(nueva)
        write_csv(project_path, rows, "viga_momentos")
        return f"{len(rest)} momento(s) añadido(s) a '{nombre_viga}' (M1, M2, ...)."
    if sub == "list":
        rows = read_csv(project_path, "viga_momentos")
        if not rows:
            return "No hay momentos. Use: cas viga momento add [viga|i] <nombre> <Mu>  |  Mu1 Mu2...  |  T S M Mu..."
        filtro = args[1] if len(args) > 1 else None
        if filtro and "viga" in rows[0]:
            rows = [r for r in rows if r.get("viga") == filtro]
        if not rows:
            return f"No hay momentos para la viga '{filtro}'."
        for i, r in enumerate(rows):
            r["N"] = str(i + 1)
        cols = ["N", "viga", "nombre", "Mu"] if rows and "viga" in rows[0] else ["N", "nombre", "Mu"]
        return "Momentos\n\n" + format_table(rows, columns=cols)
    if sub == "delete":
        if len(args) < 2:
            raise InvalidInput("Uso: cas viga momento delete <nº fila>  |  delete <viga> <nombre>")
        rows = read_csv(project_path, "viga_momentos")
        if len(args) >= 3 and "viga" in (rows[0] if rows else {}):
            nombre_viga_del = args[1]
            nombre_mom_del = " ".join(args[2:]).strip()
            idx = next((i for i, r in enumerate(rows) if r.get("viga", "") == nombre_viga_del and r.get("nombre", "") == nombre_mom_del), None)
            if idx is None:
                raise InvalidInput(f"No hay momento '{nombre_mom_del}' en la viga '{nombre_viga_del}'.")
            rows.pop(idx)
            write_csv(project_path, rows, "viga_momentos")
            return f"Momento '{nombre_mom_del}' de la viga '{nombre_viga_del}' eliminado."
        try:
            idx = int(args[1])
        except ValueError:
            raise InvalidInput("El índice debe ser un número (nº de fila en 'cas flexion viga'), o use: delete <viga> <nombre>")
        orden_flexion = _filas_momentos_orden_flexion(project_path)
        if orden_flexion:
            if idx < 1 or idx > len(orden_flexion):
                raise InvalidInput(f"Fila {idx} inválida. Hay {len(orden_flexion)} filas (mismo orden que 'cas flexion viga').")
            viga_nom = orden_flexion[idx - 1]["viga"]
            mom_nom = orden_flexion[idx - 1]["nombre"]
            pos = next((i for i, r in enumerate(rows) if r.get("viga", "") == viga_nom and r.get("nombre", "") == mom_nom), None)
            if pos is not None:
                rows.pop(pos)
                write_csv(project_path, rows, "viga_momentos")
            return f"Momento fila {idx} ('{mom_nom}' de '{viga_nom}') eliminado."
        if idx < 1 or idx > len(rows):
            raise InvalidInput(f"Índice {idx} inválido. Hay {len(rows)} momento(s).")
        rows.pop(idx - 1)
        write_csv(project_path, rows, "viga_momentos")
        return f"Momento {idx} eliminado."
    raise InvalidInput("Uso: cas viga momento add ...  |  list  |  delete <i>  |  delete <viga> <nombre>")


def _filas_cortante_orden_flexion(project_path) -> list[dict]:
    """Lista (viga, nombre) en el mismo orden que la tabla de cas cortante viga."""
    viga_rows = read_csv(project_path, "viga")
    cortantes = read_csv(project_path, "viga_cortante")
    if not viga_rows or not cortantes or "viga" not in (cortantes[0] or {}):
        return []
    tiene_col = "viga" in cortantes[0]
    una_sola = len(viga_rows) == 1
    out = []
    for beam in viga_rows:
        nom_viga = beam.get("nombre", "")
        for c in cortantes:
            if tiene_col and c.get("viga", "") != nom_viga:
                continue
            if not una_sola and not tiene_col:
                continue
            out.append({"viga": nom_viga, "nombre": c.get("nombre", "—")})
    return out


def handle_viga_cortante(args: list[str]) -> str:
    """cas viga cortante add ... | list | delete <nº fila> | delete <viga> <nombre>"""
    project_path = get_active_project_path(get_base_path())
    if not project_path:
        raise NoActiveProject("No hay proyecto activo. Use 'cas use <proyecto>'.")
    if not args:
        raise InvalidInput("Uso: cas viga cortante add [viga|i] <nombre> <Vu>  |  Vu1 Vu2...  |  T S M Vu...  |  list  |  delete")
    sub = args[0].lower()
    if sub == "add":
        if len(args) < 3:
            raise InvalidInput("Uso: cas viga cortante add [viga|i] <nombre> <Vu>  |  Vu1 Vu2...  |  T S M Vu...")
        if len(args) == 3:
            vigas = read_csv(project_path, "viga") or [{}]
            nombre_viga = vigas[0].get("nombre", "") if vigas else ""
            nombre_v = args[1]
            vu_val = args[2]
            to_float(vu_val)
            rows = read_csv(project_path, "viga_cortante")
            nueva = {"viga": nombre_viga, "nombre": nombre_v, "Vu": vu_val}
            idx = next((i for i, r in enumerate(rows) if r.get("viga", "") == nombre_viga and r.get("nombre", "") == nombre_v), None)
            if idx is not None:
                rows[idx] = nueva
            else:
                rows.append(nueva)
            write_csv(project_path, rows, "viga_cortante")
            return f"Cortante añadido a '{nombre_viga}': '{nombre_v}' Vu={vu_val}."
        ident_viga = args[1]
        rest = args[2:]
        vigas = read_csv(project_path, "viga") or []
        if ident_viga.isdigit():
            idx_v = int(ident_viga)
            if idx_v < 1 or idx_v > len(vigas):
                raise InvalidInput(f"Índice {idx_v} inválido. Hay {len(vigas)} viga(s). Use 'cas viga list'.")
            nombre_viga = vigas[idx_v - 1].get("nombre", "")
        else:
            nombre_viga = ident_viga
        try:
            to_float(rest[0])
            primer_es_num = True
        except (ValueError, TypeError, InvalidInput):
            primer_es_num = False
        if not primer_es_num:
            nombre_v = " ".join(rest[:-1]).strip() or "—"
            vu_val = rest[-1]
            to_float(vu_val)
            rows = read_csv(project_path, "viga_cortante")
            nueva = {"viga": nombre_viga, "nombre": nombre_v, "Vu": vu_val}
            idx = next((i for i, r in enumerate(rows) if r.get("viga", "") == nombre_viga and r.get("nombre", "") == nombre_v), None)
            if idx is not None:
                rows[idx] = nueva
            else:
                rows.append(nueva)
            write_csv(project_path, rows, "viga_cortante")
            return f"Cortante añadido a '{nombre_viga}': '{nombre_v}' Vu={vu_val}."
        if len(rest) >= 4 and _es_entero_positivo(rest[0]) and _es_entero_positivo(rest[1]) and _es_entero_positivo(rest[2]):
            t, s, m = int(rest[0]), int(rest[1]), int(rest[2])
            n = t * s * m
            if len(rest) == 3 + n:
                vu_vals = rest[3:3 + n]
                for v in vu_vals:
                    to_float(v)
                nombres = _nombres_momentos_estructurados(t, s, m)
                rows = read_csv(project_path, "viga_cortante")
                for i, nom in enumerate(nombres):
                    nueva = {"viga": nombre_viga, "nombre": nom, "Vu": vu_vals[i]}
                    idx = next((j for j, r in enumerate(rows) if r.get("viga", "") == nombre_viga and r.get("nombre", "") == nom), None)
                    if idx is not None:
                        rows[idx] = nueva
                    else:
                        rows.append(nueva)
                write_csv(project_path, rows, "viga_cortante")
                return f"{n} cortante(s) añadido(s) a '{nombre_viga}' (estructura {t}×{s}×{m})."
        nombres = [f"V{i + 1}" for i in range(len(rest))]
        for v in rest:
            to_float(v)
        rows = read_csv(project_path, "viga_cortante")
        for i, vu_val in enumerate(rest):
            nom = nombres[i]
            nueva = {"viga": nombre_viga, "nombre": nom, "Vu": vu_val}
            idx = next((j for j, r in enumerate(rows) if r.get("viga", "") == nombre_viga and r.get("nombre", "") == nom), None)
            if idx is not None:
                rows[idx] = nueva
            else:
                rows.append(nueva)
        write_csv(project_path, rows, "viga_cortante")
        return f"{len(rest)} cortante(s) añadido(s) a '{nombre_viga}' (V1, V2, ...)."
    if sub == "list":
        rows = read_csv(project_path, "viga_cortante")
        if not rows:
            return "No hay cortantes. Use: cas viga cortante add [viga|i] <nombre> <Vu>  |  Vu1 Vu2...  |  T S M Vu..."
        filtro = args[1] if len(args) > 1 else None
        if filtro and "viga" in rows[0]:
            rows = [r for r in rows if r.get("viga") == filtro]
        if not rows:
            return f"No hay cortantes para la viga '{filtro}'."
        for i, r in enumerate(rows):
            r["N"] = str(i + 1)
        cols = ["N", "viga", "nombre", "Vu"] if rows and "viga" in rows[0] else ["N", "nombre", "Vu"]
        return "Cortantes\n\n" + format_table(rows, columns=cols)
    if sub == "delete":
        if len(args) < 2:
            raise InvalidInput("Uso: cas viga cortante delete <nº fila>  |  delete <viga> <nombre>")
        rows = read_csv(project_path, "viga_cortante")
        if len(args) >= 3 and "viga" in (rows[0] if rows else {}):
            nombre_viga_del = args[1]
            nombre_cort_del = " ".join(args[2:]).strip()
            idx = next((i for i, r in enumerate(rows) if r.get("viga", "") == nombre_viga_del and r.get("nombre", "") == nombre_cort_del), None)
            if idx is None:
                raise InvalidInput(f"No hay cortante '{nombre_cort_del}' en la viga '{nombre_viga_del}'.")
            rows.pop(idx)
            write_csv(project_path, rows, "viga_cortante")
            return f"Cortante '{nombre_cort_del}' de la viga '{nombre_viga_del}' eliminado."
        try:
            idx = int(args[1])
        except ValueError:
            raise InvalidInput("El índice debe ser un número (nº de fila en 'cas cortante viga'), o use: delete <viga> <nombre>")
        orden_cortante = _filas_cortante_orden_flexion(project_path)
        if orden_cortante:
            if idx < 1 or idx > len(orden_cortante):
                raise InvalidInput(f"Fila {idx} inválida. Hay {len(orden_cortante)} filas (mismo orden que 'cas cortante viga').")
            viga_nom = orden_cortante[idx - 1]["viga"]
            cort_nom = orden_cortante[idx - 1]["nombre"]
            pos = next((i for i, r in enumerate(rows) if r.get("viga", "") == viga_nom and r.get("nombre", "") == cort_nom), None)
            if pos is not None:
                rows.pop(pos)
                write_csv(project_path, rows, "viga_cortante")
            return f"Cortante fila {idx} ('{cort_nom}' de '{viga_nom}') eliminado."
        if idx < 1 or idx > len(rows):
            raise InvalidInput(f"Índice {idx} inválido. Hay {len(rows)} cortante(s).")
        rows.pop(idx - 1)
        write_csv(project_path, rows, "viga_cortante")
        return f"Cortante {idx} eliminado."
    raise InvalidInput("Uso: cas viga cortante add ...  |  list  |  delete <nº fila>  |  delete <viga> <nombre>")


def handle_flexion_viga(args: list[str]) -> str:
    """cas flexion viga [viga|índice]: flujo viga+viga_momentos o vigas.csv; opcional filtrar por viga."""
    project_path = get_active_project_path(get_base_path())
    if not project_path:
        raise NoActiveProject("No hay proyecto activo. Use 'cas use <proyecto>'.")
    filtro_viga = args[0] if args else None
    viga_rows = read_csv(project_path, "viga")
    momentos = read_csv(project_path, "viga_momentos")
    viga_rows_para_tabla = []
    if viga_rows and momentos:
        for s in viga_rows:
            for k in ("fc", "fy", "b", "h", "rec"):
                if k not in s or s[k] == "":
                    raise InvalidInput(f"Viga incompleta en elements/viga.csv: falta {k}.")
        tiene_col_viga = "viga" in momentos[0]
        una_sola_viga = len(viga_rows) == 1
        rows = []
        for beam in viga_rows:
            nom_viga = beam.get("nombre", "")
            for m in momentos:
                if tiene_col_viga and m.get("viga", "") != nom_viga:
                    continue
                if not una_sola_viga and not tiene_col_viga:
                    continue
                rows.append({
                    **beam, "nombre": m.get("nombre", "—"), "Mu": m.get("Mu", ""),
                    "viga": nom_viga,
                })
        if rows:
            viga_rows_para_tabla = viga_rows
    if not viga_rows_para_tabla:
        rows = read_csv(project_path, "vigas")
        if not rows:
            raise InvalidInput(
                "Defina vigas con 'cas viga define' y 'cas viga momento add', o use "
                "'cas add viga <nombre> <fc> <fy> <b> <h> <rec> <Mu> [Vu]'."
            )
        required = ("fc", "fy", "b", "h", "rec", "Mu")
        for row in rows:
            missing = [k for k in required if k not in row or row[k] == ""]
            if missing:
                raise InvalidInput(f"Faltan columnas en vigas.csv: {missing}")
    result = run("flexion", "viga", {"vigas": rows})
    resultados = result.get("resultados", [])
    if filtro_viga and resultados:
        if "viga" in resultados[0]:
            if filtro_viga.isdigit():
                idx = int(filtro_viga)
                vigas_unicas = list(dict.fromkeys(r.get("viga", "") for r in resultados))
                if idx < 1 or idx > len(vigas_unicas):
                    raise InvalidInput(f"Índice {idx} inválido. Hay {len(vigas_unicas)} viga(s).")
                nombre_filtro = vigas_unicas[idx - 1]
            else:
                nombre_filtro = filtro_viga
            resultados = [r for r in resultados if r.get("viga", "") == nombre_filtro]
            if not resultados:
                raise InvalidInput(f"No hay momentos para la viga '{nombre_filtro}'.")
            if viga_rows_para_tabla:
                viga_rows_para_tabla = [b for b in viga_rows_para_tabla if b.get("nombre", "") == nombre_filtro]
        else:
            if filtro_viga.isdigit():
                idx = int(filtro_viga)
                if idx < 1 or idx > len(resultados):
                    raise InvalidInput(f"Índice {idx} inválido. Hay {len(resultados)} viga(s).")
                resultados = [resultados[idx - 1]]
            else:
                resultados = [r for r in resultados if r.get("nombre", "") == filtro_viga]
            if not resultados:
                raise InvalidInput(f"No hay resultados para la viga '{filtro_viga}'.")
    out_path = write_results_csv(project_path, "flexion_viga.csv", result.get("resultados", []))
    for i, r in enumerate(resultados):
        r["N"] = str(i + 1)
    base_cols = [k for k in resultados[0].keys() if k != "N"] if resultados else []
    cols = (["N", "viga"] + [k for k in base_cols if k != "viga"]) if resultados and "viga" in resultados[0] else ["N"] + base_cols
    tabla_diseno = format_table(resultados, columns=cols) if cols else ""
    resumen = f"Flexión calculada: {len(resultados)} momento(s). Resultados: {out_path}"
    encabezado = FLUJO_FLEXION_VIGA
    if viga_rows_para_tabla:
        viga_cols = ["nombre", "fc", "fy", "b", "h", "rec"] if viga_rows_para_tabla[0].get("nombre") else ["fc", "fy", "b", "h", "rec"]
        tabla_viga = format_table(viga_rows_para_tabla, columns=viga_cols)
        return f"{encabezado}Viga (propiedades)\n\n{tabla_viga}\n\nDiseño a flexión\n\n{tabla_diseno}\n\n{resumen}"
    return f"{encabezado}{resumen}\n\n{tabla_diseno}"


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
    """cas cortante viga [viga|índice]: flujo viga+viga_cortante o vigas.csv; opcional filtrar por viga."""
    project_path = get_active_project_path(get_base_path())
    if not project_path:
        raise NoActiveProject("No hay proyecto activo. Use 'cas use <proyecto>'.")
    filtro_viga = args[0] if args else None
    viga_rows = read_csv(project_path, "viga")
    cortantes = read_csv(project_path, "viga_cortante")
    viga_rows_para_tabla = []
    if viga_rows and cortantes:
        for s in viga_rows:
            for k in ("fc", "b", "h", "rec"):
                if k not in s or s[k] == "":
                    raise InvalidInput(f"Viga incompleta en elements/viga.csv: falta {k}.")
        tiene_col_viga = "viga" in cortantes[0]
        una_sola_viga = len(viga_rows) == 1
        rows = []
        for beam in viga_rows:
            nom_viga = beam.get("nombre", "")
            for c in cortantes:
                if tiene_col_viga and c.get("viga", "") != nom_viga:
                    continue
                if not una_sola_viga and not tiene_col_viga:
                    continue
                rows.append({
                    **beam, "nombre": c.get("nombre", "—"), "Vu": c.get("Vu", ""),
                    "viga": nom_viga,
                })
        if rows:
            viga_rows_para_tabla = viga_rows
    if not viga_rows_para_tabla:
        rows = read_csv(project_path, "vigas")
        if not rows:
            raise InvalidInput(
                "Defina vigas con 'cas viga define' y 'cas viga cortante add', o use "
                "'cas add viga <nombre> <fc> <fy> <b> <h> <rec> <Mu> [Vu]'."
            )
        required = ("fc", "fy", "b", "h", "rec")
        for row in rows:
            missing = [k for k in required if k not in row or row[k] == ""]
            if missing:
                raise InvalidInput(f"Faltan columnas en vigas.csv: {missing}")
        ensure_vu_column(rows)
    result = run("cortante", "viga", {"vigas": rows})
    resultados = result.get("resultados", [])
    if filtro_viga and resultados:
        if "viga" in resultados[0]:
            if filtro_viga.isdigit():
                idx = int(filtro_viga)
                vigas_unicas = list(dict.fromkeys(r.get("viga", "") for r in resultados))
                if idx < 1 or idx > len(vigas_unicas):
                    raise InvalidInput(f"Índice {idx} inválido. Hay {len(vigas_unicas)} viga(s).")
                nombre_filtro = vigas_unicas[idx - 1]
            else:
                nombre_filtro = filtro_viga
            resultados = [r for r in resultados if r.get("viga", "") == nombre_filtro]
            if not resultados:
                raise InvalidInput(f"No hay cortantes para la viga '{nombre_filtro}'.")
            if viga_rows_para_tabla:
                viga_rows_para_tabla = [b for b in viga_rows_para_tabla if b.get("nombre", "") == nombre_filtro]
        else:
            if filtro_viga.isdigit():
                idx = int(filtro_viga)
                if idx < 1 or idx > len(resultados):
                    raise InvalidInput(f"Índice {idx} inválido. Hay {len(resultados)} viga(s).")
                resultados = [resultados[idx - 1]]
            else:
                resultados = [r for r in resultados if r.get("nombre", "") == filtro_viga]
            if not resultados:
                raise InvalidInput(f"No hay resultados para la viga '{filtro_viga}'.")
    out_path = write_results_csv(project_path, "cortante_viga.csv", result.get("resultados", []))
    for i, r in enumerate(resultados):
        r["N"] = str(i + 1)
    base_cols = [k for k in resultados[0].keys() if k != "N"] if resultados else []
    cols = (["N", "viga"] + [k for k in base_cols if k != "viga"]) if resultados and "viga" in resultados[0] else ["N"] + base_cols
    tabla_diseno = format_table(resultados, columns=cols) if cols else ""
    resumen = f"Cortante calculado: {len(resultados)} sección(es). Resultados: {out_path}"
    encabezado = FLUJO_CORTANTE_VIGA
    if viga_rows_para_tabla:
        viga_cols = ["nombre", "fc", "fy", "b", "h", "rec"] if viga_rows_para_tabla[0].get("nombre") else ["fc", "fy", "b", "h", "rec"]
        tabla_viga = format_table(viga_rows_para_tabla, columns=viga_cols)
        return f"{encabezado}Viga (propiedades)\n\n{tabla_viga}\n\nDiseño a cortante\n\n{tabla_diseno}\n\n{resumen}"
    return f"{encabezado}{resumen}\n\n{tabla_diseno}"


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


def handle_inercia_fisurada(args: list[str]) -> str:
    """cas inercia fisurada <b> <d> <d'> <As> <As'> <n> [Ma] [Mcr] [Ig_m4]"""
    if len(args) < 6:
        raise InvalidInput(
            "Uso: cas inercia fisurada <b> <d> <d'> <As> <As'> <n>  [Ma Mcr Ig_m4]\n"
            "  b,d,d' cm; As,As' cm²; n=Es/Ec. Opcional: Ma,Mcr (misma unidad), Ig_m4 para Ie."
        )
    b, d, d_prima = to_float(args[0]), to_float(args[1]), to_float(args[2])
    as_t, as_c, n_val = to_float(args[3]), to_float(args[4]), to_float(args[5])
    data = {
        "b": b, "d": d, "d_prima": d_prima,
        "as_traccion": as_t, "as_compresion": as_c, "n": n_val,
    }
    if len(args) >= 9:
        data["ma"], data["mcr"], data["ig"] = to_float(args[6]), to_float(args[7]), to_float(args[8])
    out = run("inercia", "fisurada", data)
    lineas = [
        f"Eje neutro c = {out['c']} cm",
        f"Icr = {out['Icr_cm4']} cm4 = {out['Icr_m4']} m4",
    ]
    if "Ie_m4" in out:
        lineas.append(f"Ie = {out['Ie_m4']} m4  (Ma={out.get('Ma')}, Mcr={out.get('Mcr')})")
    return "Inercia fisurada\n\n" + "\n".join(lineas)
