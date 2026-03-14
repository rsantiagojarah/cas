"""Handlers CLI: elementos Ie ponderado E.060 (deflexiones)."""

from __future__ import annotations

from axis.core.exceptions import NoActiveProject, InvalidInput
from axis.core.project import get_active_project_path
from axis.core.database import read_csv, write_csv
from axis.core.utils import to_float
from axis.engine.engine import run
from axis.cli.tables import format_table
from axis.cli.handlers import get_base_path
from axis.operations.inercia_fisurada_calculos import (
    CASOS_IE,
    ie_promedio,
    n_from_fc,
    ig_bruta_cm4,
    mcr_tnm,
    CM4_A_M4,
)

# Comentario que se muestra al dar el resultado (cas inercia calcular)
FLUJO_IE_PROMEDIO = """
Cálculo Ie ponderado (E.060, deflexiones):
  Por elemento (b, h, d, d', fc): Ig = b*h³/12; Ec = 15000*sqrt(fc); n = Es/Ec (Es=2e6);
  Mcr = fr*Ig/y, fr = 2*sqrt(fc), y = h/2 (Mcr en Tn·m).
  Por sección (As, As', Ma): Icr con sección transformada (duplicando aporte As');
  si Ma <= Mcr -> Ie = Ig; si Ma > Mcr -> Ie = (Mcr/Ma)³*Ig + [1-(Mcr/Ma)³]*Icr.
  Ie promedio: continuo_ambos = (Ie1+Ie2+2*Ie3)/4; continuo_uno = (Ie2+2*Ie3)/3;
  simplemente_apoyado = Ie(centro); voladizo = Ie(apoyo).

"""


def _datos_ie_desde_elemento(elem: dict) -> dict:
    """Obtiene b, d, d_prima, n, Ig_m4, Mcr desde elemento (b, h, d, d_prima, fc)."""
    b = to_float(elem.get("b"))
    h = to_float(elem.get("h"))
    d = to_float(elem.get("d"))
    d_prima = to_float(elem.get("d_prima"))
    fc = to_float(elem.get("fc"))
    ig_cm4 = ig_bruta_cm4(b, h)
    ig_m4 = ig_cm4 * CM4_A_M4
    n = n_from_fc(fc)
    mcr = mcr_tnm(fc, b, h)
    return {"b": b, "d": d, "d_prima": d_prima, "n": n, "ig_m4": ig_m4, "mcr": mcr}


def handle_ie_define(args: list[str]) -> str:
    """cas inercia define <nombre> <caso> <b> <h> <d> <d'> <fc>"""
    project_path = get_active_project_path(get_base_path())
    if not project_path:
        raise NoActiveProject("No hay proyecto activo. Use 'cas use <proyecto>'.")
    if len(args) < 7:
        raise InvalidInput(
            "Uso: cas inercia define <nombre> <caso> <b> <h> <d> <d'> <fc>\n"
            "  b,h,d,d' cm; fc kg/cm². Se calculan Ig, Ec, n, Mcr."
        )
    nombre, caso = args[0].strip(), args[1].strip().lower()
    if caso not in CASOS_IE:
        raise InvalidInput(f"Caso no válido: {caso}. Use: {list(CASOS_IE)}")
    b, h, d, d_prima, fc = to_float(args[2]), to_float(args[3]), to_float(args[4]), to_float(args[5]), to_float(args[6])
    rows = read_csv(project_path, "ie_elementos")
    idx = next((i for i, r in enumerate(rows) if r.get("nombre") == nombre), None)
    row = {"nombre": nombre, "caso": caso, "b": b, "h": h, "d": d, "d_prima": d_prima, "fc": fc}
    if idx is not None:
        rows[idx] = row
    else:
        rows.append(row)
    write_csv(project_path, rows, "ie_elementos")
    secciones = ", ".join(CASOS_IE[caso]["secciones"])
    return f"Elemento '{nombre}' definido: caso={caso}, b={b}, h={h}, d={d}, d'={d_prima}, fc={fc}. Secciones: {secciones}."


def handle_ie_list(args: list[str]) -> str:
    """cas inercia list"""
    project_path = get_active_project_path(get_base_path())
    if not project_path:
        raise NoActiveProject("No hay proyecto activo. Use 'cas use <proyecto>'.")
    rows = read_csv(project_path, "ie_elementos")
    if not rows:
        return "No hay elementos. Use: cas inercia define <nombre> <caso> <b> <h> <d> <d'> <fc>"
    for i, r in enumerate(rows):
        r["N"] = str(i + 1)
    return "Elementos Ie\n\n" + format_table(rows, columns=["N", "nombre", "caso", "b", "h", "d", "d_prima", "fc"])


def handle_ie_delete(args: list[str]) -> str:
    """cas inercia delete <nombre>"""
    project_path = get_active_project_path(get_base_path())
    if not project_path:
        raise NoActiveProject("No hay proyecto activo. Use 'cas use <proyecto>'.")
    if not args:
        raise InvalidInput("Uso: cas inercia delete <nombre>")
    nombre = args[0]
    rows = read_csv(project_path, "ie_elementos")
    idx = next((i for i, r in enumerate(rows) if r.get("nombre") == nombre), None)
    if idx is None:
        raise InvalidInput(f"No existe elemento '{nombre}'. Use: cas inercia list.")
    rows.pop(idx)
    write_csv(project_path, rows, "ie_elementos")
    secs = read_csv(project_path, "ie_secciones")
    n_antes = len(secs)
    secs = [s for s in secs if s.get("elemento") != nombre]
    write_csv(project_path, secs, "ie_secciones")
    quitar = n_antes - len(secs)
    msg = f"Elemento '{nombre}' eliminado."
    if quitar > 0:
        msg += f" {quitar} sección(es) eliminada(s)."
    return msg


def handle_ie_seccion(args: list[str]) -> str:
    """cas inercia seccion add <elemento> <seccion> <As> <As'> <Ma> | list | delete <i>"""
    project_path = get_active_project_path(get_base_path())
    if not project_path:
        raise NoActiveProject("No hay proyecto activo. Use 'cas use <proyecto>'.")
    if not args:
        raise InvalidInput("Uso: cas inercia seccion add <elemento> <seccion> <As> <As'> <Ma> | list | delete <i>")
    sub = args[0].lower()
    if sub == "add":
        if len(args) < 6:
            raise InvalidInput(
                "Uso: cas inercia seccion add <elemento> <seccion> <As> <As'> <Ma>\n"
                "  As=acero en tracción, As'=en compresión. Apoyos: As=arriba; centro: As=abajo."
            )
        elemento, seccion = args[1], args[2]
        elementos = read_csv(project_path, "ie_elementos")
        elem = next((e for e in elementos if e.get("nombre") == elemento), None)
        if not elem:
            raise InvalidInput(f"No existe elemento '{elemento}'. Use: cas inercia define <nombre> <caso> <b> <h> <d> <d'> <fc>")
        if not all(elem.get(k) for k in ("b", "h", "d", "d_prima", "fc")):
            raise InvalidInput(f"Elemento '{elemento}' sin b,h,d,d',fc. Redefina con: cas inercia define <nombre> <caso> <b> <h> <d> <d'> <fc>")
        caso = elem.get("caso", "")
        if caso not in CASOS_IE or seccion not in CASOS_IE[caso]["secciones"]:
            raise InvalidInput(f"Sección debe ser una de: {CASOS_IE.get(caso, {}).get('secciones', [])}")
        as_t, as_c, ma = to_float(args[3]), to_float(args[4], 0), to_float(args[5])
        rows = read_csv(project_path, "ie_secciones")
        nueva = {"elemento": elemento, "seccion": seccion, "as_traccion": as_t, "as_compresion": as_c, "Ma": ma}
        idx = next((i for i, r in enumerate(rows) if r.get("elemento") == elemento and r.get("seccion") == seccion), None)
        if idx is not None:
            rows[idx] = nueva
            msg = "Sección actualizada"
        else:
            rows.append(nueva)
            msg = "Sección añadida"
        write_csv(project_path, rows, "ie_secciones")
        return f"{msg}: '{elemento}' / {seccion}."
    if sub == "list":
        rows = read_csv(project_path, "ie_secciones")
        elementos = read_csv(project_path, "ie_elementos")
        filtro = args[1] if len(args) > 1 else None
        if filtro:
            rows = [r for r in rows if r.get("elemento") == filtro]
        if not rows:
            return "No hay secciones. Use: cas inercia seccion add <elemento> <seccion> <As> <As'> <Ma>"
        for i, r in enumerate(rows):
            r["N"] = str(i + 1)
            r["As"] = r.get("as_traccion", "")
            r["As'"] = r.get("as_compresion", "")
            elem = next((e for e in elementos if e.get("nombre") == r.get("elemento")), None)
            if elem and all(elem.get(k) for k in ("b", "h", "fc")):
                try:
                    r["n"] = round(n_from_fc(to_float(elem["fc"])), 4)
                    r["Mcr"] = round(mcr_tnm(to_float(elem["fc"]), to_float(elem["b"]), to_float(elem["h"])), 4)
                except (InvalidInput, ValueError, KeyError):
                    r["n"] = r.get("n", "")
                    r["Mcr"] = r.get("Mcr", "")
            else:
                r["n"] = r.get("n", "")
                r["Mcr"] = r.get("Mcr", "")
        return "Secciones Ie\n\n" + format_table(rows, columns=["N", "elemento", "seccion", "As", "As'", "n", "Mcr", "Ma"])
    if sub == "delete":
        if len(args) < 2:
            raise InvalidInput("Uso: cas inercia seccion delete <indice>")
        try:
            idx = int(args[1])
        except ValueError:
            raise InvalidInput("El índice debe ser un número.")
        rows = read_csv(project_path, "ie_secciones")
        if idx < 1 or idx > len(rows):
            raise InvalidInput(f"Índice {idx} inválido. Hay {len(rows)} sección(es).")
        rows.pop(idx - 1)
        write_csv(project_path, rows, "ie_secciones")
        return f"Sección {idx} eliminada."
    raise InvalidInput("Uso: cas inercia seccion add | list | delete <i>")


def handle_ie_calcular(args: list[str]) -> str:
    """cas inercia calcular [nombre]  -> tabla elementos, tabla Ie por sección, Ie_promedio."""
    project_path = get_active_project_path(get_base_path())
    if not project_path:
        raise NoActiveProject("No hay proyecto activo. Use 'cas use <proyecto>'.")
    elementos = read_csv(project_path, "ie_elementos")
    secciones_raw = read_csv(project_path, "ie_secciones")
    if not elementos:
        raise InvalidInput("No hay elementos. Use: cas inercia define <nombre> <caso>")
    filtro = args[0] if args else None
    if filtro:
        elementos = [e for e in elementos if e.get("nombre") == filtro]
        if not elementos:
            raise InvalidInput(f"No existe elemento '{filtro}'.")
    tabla_elementos = []
    for i, e in enumerate(elementos):
        e["N"] = str(i + 1)
        tabla_elementos.append({
            "N": e["N"], "nombre": e.get("nombre", ""), "caso": e.get("caso", ""),
            "b": e.get("b", ""), "h": e.get("h", ""), "d": e.get("d", ""),
            "d_prima": e.get("d_prima", ""), "fc": e.get("fc", ""),
        })
    tabla_ie = []
    ie_promedios = []
    for elem in elementos:
        nombre_e = elem.get("nombre", "")
        caso = elem.get("caso", "")
        if not all(elem.get(k) for k in ("b", "h", "d", "d_prima", "fc")):
            raise InvalidInput(f"Elemento '{nombre_e}' sin b,h,d,d',fc. Redefina con: cas inercia define <nombre> <caso> <b> <h> <d> <d'> <fc>")
        datos = _datos_ie_desde_elemento(elem)
        req_secciones = CASOS_IE.get(caso, {}).get("secciones", [])
        secciones_elem = [s for s in secciones_raw if s.get("elemento") == nombre_e]
        valores_ie = {}
        for s in secciones_elem:
            sec = s.get("seccion", "")
            data = {
                "b": datos["b"], "d": datos["d"], "d_prima": datos["d_prima"],
                "as_traccion": to_float(s.get("as_traccion")), "as_compresion": to_float(s.get("as_compresion"), 0),
                "n": datos["n"], "ma": to_float(s.get("Ma")), "mcr": datos["mcr"], "ig": datos["ig_m4"],
            }
            out = run("inercia", "fisurada", data)
            ie_m4 = out.get("Ie_m4")
            if ie_m4 is None:
                raise InvalidInput(f"Sección {nombre_e}/{sec}: no se obtuvo Ie (revise Ma).")
            valores_ie[sec] = ie_m4
            tabla_ie.append({
                "elemento": nombre_e, "seccion": sec, "Ie_m4": round(ie_m4, 6),
                "Mcr": round(datos["mcr"], 4), "Ma": round(to_float(s.get("Ma")), 4),
                "n": round(datos["n"], 4), "As": round(to_float(s.get("as_traccion")), 2),
                "As'": round(to_float(s.get("as_compresion"), 0), 2),
            })
        for sec in req_secciones:
            if sec not in valores_ie:
                raise InvalidInput(f"Falta sección '{sec}' para elemento '{nombre_e}'.")
        prom = ie_promedio(caso, valores_ie)
        ig_m4 = datos["ig_m4"]
        ratio = round(prom / ig_m4, 4) if ig_m4 and ig_m4 > 0 else ""
        ie_promedios.append({
            "elemento": nombre_e, "caso": caso,
            "Ig_m4": round(ig_m4, 6), "Ie_promedio_m4": round(prom, 6), "Ie/Ig": ratio,
        })
    cols_elem = ["N", "nombre", "caso", "b", "h", "d", "d_prima", "fc"]
    cols_ie = ["elemento", "seccion", "Mcr", "Ma", "n", "As", "As'", "Ie_m4"]
    cols_prom = ["elemento", "caso", "Ig_m4", "Ie_promedio_m4", "Ie/Ig"]
    out_text = FLUJO_IE_PROMEDIO + "Elementos (Ie ponderado E.060)\n\n"
    out_text += format_table(tabla_elementos, columns=cols_elem) + "\n\n"
    out_text += "Ie por sección (m4)\n\n"
    out_text += format_table(tabla_ie, columns=cols_ie) + "\n\n"
    out_text += "Ie promedio (m4)\n\n"
    out_text += format_table(ie_promedios, columns=cols_prom)
    return out_text


# ξ por tiempo de carga sostenida (deflexión diferida)
XI_TIEMPO = {"3meses": 1.0, "6meses": 1.2, "12meses": 1.4, "5anos": 2.0}

FLUJO_LAMBDA = """
Factor deflexión diferida (λΔ): λΔ = ξ / (1 + 50·ρ')
  ρ' = As'/(b·d)  cuantía acero compresión (en centro del tramo o en apoyo para voladizo).
  ξ: 3meses=1.0, 6meses=1.2, 12meses=1.4, 5anos o más=2.0.
  Deflexión adicional a largo plazo = λΔ × deflexión inmediata (carga sostenida).

"""


def _parse_xi(val: str) -> float:
    """Convierte 3meses|6meses|12meses|5anos o número a ξ."""
    v = val.strip().lower()
    if v in XI_TIEMPO:
        return XI_TIEMPO[v]
    try:
        x = to_float(val)
        if x in (1.0, 1.2, 1.4, 2.0):
            return x
    except (InvalidInput, ValueError):
        pass
    raise InvalidInput("xi debe ser: 3meses, 6meses, 12meses, 5anos o 1.0, 1.2, 1.4, 2.0")


def handle_ie_lambda(args: list[str]) -> str:
    """cas inercia lambda <b> <d> <As'> <xi>  o  cas inercia lambda <elemento> <xi>"""
    if len(args) == 4:
        b = to_float(args[0])
        d = to_float(args[1])
        as_p = to_float(args[2], 0)
        xi = _parse_xi(args[3])
        b_d = b * d
        rho_p = as_p / b_d if b_d > 0 else 0.0
        lambda_D = xi / (1.0 + 50.0 * rho_p)
        return (
            FLUJO_LAMBDA
            + f"b={b} cm, d={d} cm, As'={as_p} cm², ξ={xi}\n"
            + f"ρ' = {rho_p:.6f}\n"
            + f"λΔ = {lambda_D:.4f}\n"
            + "Deflexión adicional = λΔ × deflexión inmediata (carga sostenida)."
        )
    if len(args) == 2:
        project_path = get_active_project_path(get_base_path())
        if not project_path:
            raise NoActiveProject("No hay proyecto activo. Use 'cas use <proyecto>'.")
        elemento, xi_val = args[0], args[1]
        xi = _parse_xi(xi_val)
        elementos = read_csv(project_path, "ie_elementos")
        elem = next((e for e in elementos if e.get("nombre") == elemento), None)
        if not elem or not all(elem.get(k) for k in ("b", "d")):
            raise InvalidInput(f"Elemento '{elemento}' no existe o no tiene b, d. Use: cas inercia list.")
        caso = elem.get("caso", "")
        sec_rho = "apoyo" if caso == "voladizo" else "centro"
        secciones = read_csv(project_path, "ie_secciones")
        s = next((s for s in secciones if s.get("elemento") == elemento and s.get("seccion") == sec_rho), None)
        if not s:
            raise InvalidInput(f"Falta sección '{sec_rho}' para elemento '{elemento}'.")
        b = to_float(elem["b"])
        d = to_float(elem["d"])
        as_p = to_float(s.get("as_compresion"), 0)
        b_d = b * d
        rho_p = as_p / b_d if b_d > 0 else 0.0
        lambda_D = xi / (1.0 + 50.0 * rho_p)
        return (
            FLUJO_LAMBDA
            + f"Elemento: {elemento}, ξ={xi}, sección para ρ': {sec_rho}\n"
            + f"b={b} cm, d={d} cm, As'={as_p} cm²\n"
            + f"ρ' = {rho_p:.6f}\n"
            + f"λΔ = {lambda_D:.4f}\n"
            + "Deflexión adicional = λΔ × deflexión inmediata (carga sostenida)."
        )
    raise InvalidInput(
        "Uso: cas lambda <b> <d> <As'> <xi>  o  cas lambda <elemento> <xi>\n"
        "  xi: 3meses|6meses|12meses|5anos"
    )
