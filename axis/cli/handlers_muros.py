"""Handlers CLI: muros (predimensión núcleo + diseño completo E.060)."""

from __future__ import annotations

from pathlib import Path
import re

from axis.core.exceptions import NoActiveProject, InvalidInput
from axis.core.project import get_active_project_path
from axis.core.database import (
    write_results_csv, read_results_csv, read_csv, write_csv, ensure_data_csv_exists,
    read_json, write_json, ELEMENT_FIELDNAMES,
)
from axis.engine.engine import run
from axis.cli.tables import format_table
from axis.cli.handlers import get_base_path
from axis.data.etabs_table_reader import get_table, clear_table_cache

try:
    import pandas as pd
except ImportError:
    pd = None


# ═══════════════════════════════════════════════════════════════════════
# Utilidades compartidas
# ═══════════════════════════════════════════════════════════════════════

def _project() -> Path:
    p = get_active_project_path(get_base_path())
    if not p:
        raise NoActiveProject("No hay proyecto activo. Use 'cas use <proyecto>'.")
    return p


def _muros_results_dir(project_path: Path) -> Path:
    d = project_path / "results" / "muros_nucleo"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _sanitize(name: str) -> str:
    name = name.strip()
    return "".join(c for c in name if c.isalnum() or c in ("-", "_")) or "muro"


def _strip_ansi(text: str) -> str:
    """Elimina secuencias ANSI de color/formato del texto."""
    if not text:
        return text
    return re.sub(r"\x1b\[[0-?]*[ -/]*[@-~]", "", text)


# ═══════════════════════════════════════════════════════════════════════
# PREDIMENSIONAMIENTO NÚCLEO (existente)
# ═══════════════════════════════════════════════════════════════════════

def handle_muro_nucleo(args: list[str]) -> str:
    """cas muro nucleo <nombre_muro> <L> <fy> <nivel> <hm> <Mu> [phi]"""
    pp = _project()
    if len(args) < 6:
        raise InvalidInput(
            "Uso: cas muro nucleo <nombre_muro> <L> <fy> <nivel> <hm> <Mu> [phi]\n"
            "  nombre_muro: identificador del muro (ej. Muro_E1)\n"
            "  L          : longitud del núcleo del muro (m)\n"
            "  fy         : fluencia del acero (kg/cm²)\n"
            "  nivel      : etiqueta del nivel (ej. Piso_01)\n"
            "  hm         : altura de tramo (m)\n"
            "  Mu         : momento último (Tn-m)\n"
            "  phi        : φ (opcional, por defecto 0.90)"
        )
    try:
        nombre_muro = args[0]
        L = float(args[1]); fy = float(args[2])
        nivel = args[3]; hm = float(args[4]); mu = float(args[5])
        phi = float(args[6]) if len(args) > 6 else 0.90
    except ValueError:
        raise InvalidInput("L, fy, hm, Mu y phi deben ser numéricos.")
    if L <= 0 or fy <= 0 or hm <= 0 or mu <= 0 or phi <= 0:
        raise InvalidInput("L, fy, hm, Mu y phi deben ser mayores que cero.")

    results_dir = _muros_results_dir(pp)
    file_name = _sanitize(nombre_muro) + ".csv"
    muro_path = results_dir / file_name
    prev_rows = read_results_csv(pp, f"muros_nucleo/{file_name}") if muro_path.exists() else []
    h_inicial = 0.0
    if prev_rows:
        try:
            h_inicial = float(str(prev_rows[-1].get("H_total", "0")).replace(",", "."))
        except ValueError:
            pass

    data = {"L": L, "fy": fy, "phi": phi, "H_inicial": h_inicial,
            "niveles": [{"nivel": nivel, "hm": hm, "Mu": mu}]}
    result = run("predimension", "muro_nucleo", data)
    resultados = result.get("resultados", [])
    if not resultados:
        raise InvalidInput("No se obtuvieron resultados de predimensionamiento.")

    for fila in resultados:
        fila.update({"muro": nombre_muro, "L": L, "fy": fy, "phi": phi})

    todos = prev_rows + resultados
    out_path = write_results_csv(pp, f"muros_nucleo/{file_name}", todos)

    for i, fila in enumerate(todos):
        fila["N"] = str(i + 1)
    cols = ["N", "muro", "nivel", "hm", "H_total", "H_L", "tipo_muro",
            "tipo_falla", "Mu", "z", "As"]
    tabla = format_table(todos, columns=cols)
    return (
        f"Predimensionamiento de acero en núcleo de muro '{nombre_muro}' (niveles acumulados)\n\n"
        + tabla + f"\n\nResultados guardados en: {out_path}"
    )


def handle_muro_list(args: list[str]) -> str:
    """cas muro list  -> Lista muros con resultados y resumen básico."""
    pp = _project()
    results_dir = _muros_results_dir(pp)
    archivos = sorted(p for p in results_dir.glob("*.csv") if p.is_file())
    if not archivos:
        return "No hay muros predimensionados aún."
    resumen: list[dict] = []
    for p in archivos:
        filas = read_results_csv(pp, f"muros_nucleo/{p.name}")
        if not filas:
            continue
        try:
            h_max = float(str(filas[-1].get("H_total", "0")).replace(",", "."))
        except ValueError:
            h_max = 0.0
        resumen.append({"muro": p.stem, "niveles": len(filas),
                "H_total_max": round(h_max, 2),
                        "L": filas[0].get("L", ""), "fy": filas[0].get("fy", "")})
    if not resumen:
        return "No hay muros predimensionados aún."
    for i, f in enumerate(resumen):
        f["N"] = str(i + 1)
    return "Muros predimensionados (núcleo)\n\n" + format_table(
        resumen, columns=["N", "muro", "niveles", "H_total_max", "L", "fy"])


def handle_muro_delete(args: list[str]) -> str:
    """cas muro delete <nombre_muro>  -> Elimina resultados de un muro."""
    pp = _project()
    if not args:
        raise InvalidInput("Uso: cas muro delete <nombre_muro>")
    nombre = args[0]
    results_dir = _muros_results_dir(pp)
    path = results_dir / (_sanitize(nombre) + ".csv")
    if not path.exists():
        raise InvalidInput(f"No existe muro con nombre '{nombre}'.")
    path.unlink()
    return f"Resultados del muro '{nombre}' eliminados."


def handle_muro_etabs(args: list[str]) -> str:
    """cas muro etabs <nombre_muro> <L> <fy> <pier_name> [phi]"""
    pp = _project()
    if len(args) < 4:
        raise InvalidInput(
            "Uso: cas muro etabs <nombre_muro> <L> <fy> <pier_name> [phi]")
    nombre_muro = args[0]
    try:
        L = float(args[1]); fy = float(args[2])
        phi = float(args[4]) if len(args) > 4 else 0.90
    except ValueError:
        raise InvalidInput("L, fy y phi deben ser numéricos.")
    pier_name = args[3]
    if L <= 0 or fy <= 0 or phi <= 0:
        raise InvalidInput("L, fy y phi deben ser mayores que cero.")

    clear_table_cache()
    df = get_table("Pier Forces", log=True)
    if df is None or df.empty:
        raise InvalidInput("No se pudo leer 'Pier Forces' desde ETABS.")
    df = df.copy()
    df.columns = [str(c).strip().lower() for c in df.columns]
    if not {"story", "pier", "outputcase", "m3"}.issubset(df.columns):
        raise InvalidInput("Columnas esperadas (Story, Pier, OutputCase, M3) no encontradas.")

    pier_filtro = str(pier_name).strip()
    df = df[df["pier"].astype(str) == pier_filtro]
    if df.empty:
        raise InvalidInput(f"No se encontraron filas para Pier '{pier_filtro}'.")

    name_upper = pier_filtro.upper()
    tiene_x, tiene_y = "X" in name_upper, "Y" in name_upper
    if tiene_x and not tiene_y:
        caso = "SPX"
    elif tiene_y and not tiene_x:
        caso = "SPY"
    else:
        raise InvalidInput("No se pudo determinar sentido (X/Y) del nombre del Pier.")

    df = df[df["outputcase"].astype(str).str.upper() == caso]
    if df.empty:
        raise InvalidInput(f"Sin filas para Pier='{pier_filtro}' y OutputCase='{caso}'.")

    df["M3_num"] = df["m3"].astype(float)
    df_group = df.groupby("story", as_index=False)["M3_num"].max()

    story_df = get_table("Story Definitions", log=True)
    if story_df is None or story_df.empty:
        raise InvalidInput("No se pudo leer 'Story Definitions' desde ETABS.")
    story_df = story_df.copy()
    story_df.columns = [str(c).strip().lower() for c in story_df.columns]
    if "story" not in story_df.columns or "height" not in story_df.columns:
        raise InvalidInput("'Story Definitions' sin columnas 'Story'/'Height'.")

    alturas: dict[str, float] = {}
    elevaciones: dict[str, float] = {}
    for _, fila in story_df.iterrows():
        sn = str(fila["story"])
        try:
            alturas[sn] = float(fila["height"])
        except (TypeError, ValueError):
            continue
        if "elevation" in story_df.columns:
            try:
                elevaciones[sn] = float(fila["elevation"])
            except (TypeError, ValueError):
                pass

    stories = df_group["story"].astype(str).tolist()
    if elevaciones:
        stories_sorted = sorted(stories, key=lambda s: elevaciones.get(s, 0.0))
    else:
        try:
            stories_sorted = sorted(stories,
                key=lambda s: float("".join(ch for ch in str(s) if ch.isdigit() or ch == ".") or "0"))
        except Exception:
            stories_sorted = sorted(stories)

    niveles = []
    for story in stories_sorted:
        fila = df_group[df_group["story"].astype(str) == story].iloc[0]
        Mu = float(fila["M3_num"])
        hm_val = alturas.get(str(story), 0.0)
        if hm_val <= 0.0:
            raise InvalidInput(f"Sin altura válida para Story '{story}'.")
        niveles.append({"nivel": str(story), "hm": hm_val, "Mu": abs(Mu)})

    if not niveles:
        raise InvalidInput("No se obtuvieron momentos M3 ni alturas.")

    data = {"L": L, "fy": fy, "phi": phi, "H_inicial": 0.0, "niveles": niveles}
    result = run("predimension", "muro_nucleo", data)
    resultados = result.get("resultados", [])
    if not resultados:
        raise InvalidInput("Sin resultados de predimensionamiento desde ETABS.")

    for fila in resultados:
        fila.update({"muro": nombre_muro, "L": L, "fy": fy, "phi": phi})

    results_dir = _muros_results_dir(pp)
    file_name = _sanitize(nombre_muro) + ".csv"
    out_path = write_results_csv(pp, f"muros_nucleo/{file_name}", resultados)

    for i, fila in enumerate(resultados):
        fila["N"] = str(i + 1)
    cols = ["N", "muro", "nivel", "H_total", "H_L", "tipo_muro",
            "tipo_falla", "Mu", "z", "As"]
    tabla = format_table(resultados, columns=cols)
    return (
        f"Predimensionamiento de muro '{nombre_muro}' desde ETABS (Pier '{pier_filtro}', {caso})\n\n"
        + tabla + f"\n\nResultados guardados en: {out_path}"
    )


# ═══════════════════════════════════════════════════════════════════════
# DISEÑO COMPLETO DE MUROS  (RNE E.060)
# ═══════════════════════════════════════════════════════════════════════

_MUROS_FIELDS = [
    "nombre", "hm", "lm", "t", "fc", "fy", "fyt",
    "Pu", "Vu", "Mu", "delta_u", "c", "Mn_manual",
]


def handle_muro_add(args: list[str]) -> str:
    """cas muro add <nombre> <hm> <lm> <t> <fc> <fy> <fyt> <Pu> <Vu> <Mu> [delta_u] [c] [Mn]

    Almacena datos de un muro para diseño posterior.
    Unidades: hm/lm/t en cm, fc/fy/fyt en kg/cm², Pu en Tn, Vu en Tn, Mu en Tn-m
    Opcionales: delta_u en cm, c en cm, Mn en Tn-m
    """
    pp = _project()
    if len(args) < 10:
        raise InvalidInput(
            "Uso: cas muro add <nombre> <hm> <lm> <t> <fc> <fy> <fyt> <Pu> <Vu> <Mu> "
            "[delta_u] [c] [Mn]\n"
            "  Unidades: hm/lm/t(cm) fc/fy/fyt(kg/cm²) Pu(Tn) Vu(Tn) Mu(Tn-m)\n"
            "  Opcionales: delta_u(cm) c(cm) Mn(Tn-m)"
        )
    try:
        nombre = args[0]
        hm = float(args[1]); lm = float(args[2]); t = float(args[3])
        fc = float(args[4]); fy = float(args[5]); fyt = float(args[6])
        Pu = float(args[7]); Vu = float(args[8]); Mu = float(args[9])
        delta_u = float(args[10]) if len(args) > 10 else ""
        c_val = float(args[11]) if len(args) > 11 else ""
        Mn_man = float(args[12]) if len(args) > 12 else ""
    except ValueError:
        raise InvalidInput("Los parámetros numéricos deben ser válidos.")

    if hm <= 0 or lm <= 0 or t <= 0:
        raise InvalidInput("hm, lm y t deben ser positivos.")
    if fc <= 0 or fy <= 0 or fyt <= 0:
        raise InvalidInput("fc, fy y fyt deben ser positivos.")

    row = {
        "nombre": nombre, "hm": hm, "lm": lm, "t": t,
        "fc": fc, "fy": fy, "fyt": fyt,
        "Pu": Pu, "Vu": Vu, "Mu": Mu,
        "delta_u": delta_u, "c": c_val, "Mn_manual": Mn_man,
    }

    existing = read_csv(pp, "muros")
    idx = next((i for i, r in enumerate(existing) if r.get("nombre") == nombre), None)
    if idx is not None:
        existing[idx] = row
        msg = f"Muro '{nombre}' actualizado."
    else:
        existing.append(row)
        msg = f"Muro '{nombre}' agregado."

    write_csv(pp, existing, "muros", _MUROS_FIELDS)

    for i, r in enumerate(existing):
        r["N"] = str(i + 1)
    cols = ["N", "nombre", "hm", "lm", "t", "fc", "fy", "fyt", "Pu", "Vu", "Mu"]
    return msg + "\n\n" + format_table(existing, columns=cols)


def handle_muro_list_data(args: list[str]) -> str:
    """cas muro data  -> Lista muros almacenados para diseño."""
    pp = _project()
    rows = read_csv(pp, "muros")
    if not rows:
        return "No hay muros almacenados. Use 'cas muro add ...' para agregar."
    for i, r in enumerate(rows):
        r["N"] = str(i + 1)
    cols = ["N", "nombre", "hm", "lm", "t", "fc", "fy", "fyt", "Pu", "Vu", "Mu"]
    return "Muros almacenados para diseño\n\n" + format_table(rows, columns=cols)


def handle_muro_delete_data(args: list[str]) -> str:
    """cas muro remove <nombre>  -> Elimina un muro de la lista de datos."""
    pp = _project()
    if not args:
        raise InvalidInput("Uso: cas muro remove <nombre>")
    nombre = args[0]
    rows = read_csv(pp, "muros")
    new_rows = [r for r in rows if r.get("nombre") != nombre]
    if len(new_rows) == len(rows):
        raise InvalidInput(f"No existe muro '{nombre}' en los datos almacenados.")
    write_csv(pp, new_rows, "muros", _MUROS_FIELDS)
    return f"Muro '{nombre}' eliminado de datos."


def _to_f(val, default=None):
    """Convierte a float o devuelve default si vacío."""
    if val is None or val == "" or str(val).strip() == "":
        return default
    return float(str(val).replace(",", "."))


def handle_muro_diseno(args: list[str]) -> str:
    """cas muro diseno [nombre] [DEFORMACION|ESFUERZO]

    Ejecuta el diseño completo RNE E.060 de un muro almacenado (o todos).
    """
    pp = _project()
    rows = read_csv(pp, "muros")
    if not rows:
        raise InvalidInput(
            "No hay muros almacenados. Use 'cas muro add ...' primero.")

    nombre_filtro = None
    boundary_method = None
    for a in args:
        au = a.upper()
        if au in ("DEFORMACION", "ESFUERZO"):
            boundary_method = au
        elif nombre_filtro is None:
            nombre_filtro = a

    if nombre_filtro:
        rows = [r for r in rows if r.get("nombre") == nombre_filtro]
        if not rows:
            raise InvalidInput(f"Muro '{nombre_filtro}' no encontrado.")

    all_results: list[dict] = []
    outputs: list[str] = []

    for row in rows:
        nombre = row["nombre"]
        hm = _to_f(row["hm"]); lm = _to_f(row["lm"]); t = _to_f(row["t"])
        fc = _to_f(row["fc"]); fy = _to_f(row["fy"]); fyt = _to_f(row["fyt"])
        Pu_tn = _to_f(row["Pu"]); Vu_tn = _to_f(row["Vu"]); Mu_tnm = _to_f(row["Mu"])
        delta_u = _to_f(row.get("delta_u"))
        c_val = _to_f(row.get("c"))
        Mn_tnm = _to_f(row.get("Mn_manual"))

        # Conversiones: Tn→kg, Tn-m→kg·cm
        Pu_kg = Pu_tn * 1000.0
        Vu_kg = abs(Vu_tn) * 1000.0
        Mu_kgcm = abs(Mu_tnm) * 100000.0
        Mn_kgcm = Mn_tnm * 100000.0 if Mn_tnm else None

        data = {
            "nombre": nombre, "hm": hm, "lm": lm, "t": t,
            "fc": fc, "fy": fy, "fyt": fyt,
            "Pu": Pu_kg, "Vu": Vu_kg, "Mu": Mu_kgcm,
        }
        if delta_u is not None:
            data["delta_u"] = delta_u
        if c_val is not None:
            data["c"] = c_val
        if Mn_kgcm is not None:
            data["Mn_manual"] = Mn_kgcm
        if boundary_method:
            data["boundary_method"] = boundary_method

        result = run("diseno", "muro", data)
        all_results.append(result)
        outputs.append(_format_design_output(result, Pu_tn, Vu_tn, Mu_tnm))

    # Guardar resultados
    results_dir = pp / "results" / "muros_diseno"
    results_dir.mkdir(parents=True, exist_ok=True)
    for res in all_results:
        fname = _sanitize(res["nombre"]) + ".csv"
        write_results_csv(pp, f"muros_diseno/{fname}", [res])

    return "\n\n".join(outputs) + f"\n\nResultados guardados en: {results_dir}"


def _format_design_output(r: dict, Pu_tn: float, Vu_tn: float, Mu_tnm: float) -> str:
    """Formatea la salida del diseño de un muro para el CLI."""
    nombre = r["nombre"]
    ok_global = r.get("diseno_ok", False)
    estado = "CUMPLE" if ok_global else "NO CUMPLE"

    # Convertir de vuelta a Tn / Tn-m para mostrar
    Mn_tnm = r["Mn"] / 100000.0
    phi_Mn_tnm = r["phi_Mn"] / 100000.0
    Mua_tnm = r["Mua"] / 100000.0
    Mcr_tnm = r["Mcr"] / 100000.0 if r.get("Mcr") else 0.0

    Vu_cap_tn = r["Vu_cap"] / 1000.0
    Vc_tn = r["Vc"] / 1000.0
    Vs_tn = r["Vs"] / 1000.0
    Vn_tn = r["Vn"] / 1000.0
    phi_Vn_tn = r["phi_Vn"] / 1000.0

    lines = [
        f"{'=' * 60}",
        f"  DISENO DE MURO: {nombre}   ->   {estado}",
        f"{'=' * 60}",
        "",
        "  1. ESPESOR",
        f"     {r['thickness_msg']}",
        "",
        "  2. SOLICITACIONES",
        f"     Pu = {Pu_tn:.2f} Tn   |   Vu = {Vu_tn:.2f} Tn   |   Mu = {Mu_tnm:.2f} Tn-m",
        "",
        "  3. REFUERZO PRELIMINAR",
        f"     rho_h = {r['rho_h']:.4f}   |   rho_v = {r['rho_v']:.4f}",
        "",
        "  4. FLEXION",
        f"     Mn  = {Mn_tnm:.2f} Tn-m   |   phi*Mn = {phi_Mn_tnm:.2f} Tn-m",
        f"     Mua = {Mua_tnm:.2f} Tn-m   ->   {'CUMPLE' if r['flexion_ok'] else 'NO CUMPLE'}",
        "",
        "  5. AGRIETAMIENTO",
        f"     Mcr = {Mcr_tnm:.2f} Tn-m   |   1.2*Mcr = {1.2 * Mcr_tnm:.2f} Tn-m",
        f"     Mn >= 1.2*Mcr   ->   {'CUMPLE' if r.get('cracking_ok') else 'NO CUMPLE'}",
        "",
        "  6. CORTE (con amplificacion por capacidad)",
        f"     Vu_cap = {Vu_cap_tn:.2f} Tn   (amplificado Mn/Mua)",
        f"     Vc = {Vc_tn:.2f} Tn   |   Vs = {Vs_tn:.2f} Tn   |   Vn = {Vn_tn:.2f} Tn",
        f"     phi*Vn = {phi_Vn_tn:.2f} Tn   ->   {'CUMPLE' if r['corte_ok'] else 'NO CUMPLE'}",
        f"     Vs <= 0.75Vn: {'Si' if r['vs_limit_ok'] else 'No'}   |   "
        f"Vn <= 2.6*sqrt(f'c)*Acw: {'Si' if r['vn_limit_ok'] else 'No'}",
        "",
        "  7. ELEMENTOS DE BORDE",
        f"     Metodo: {r.get('borde_metodo', '-')}",
        f"     Requiere: {'SI' if r.get('borde_requiere') else 'NO'}",
    ]

    bd = r.get("borde_detalle", "")
    if r.get("borde_requiere") and bd:
        lines.append(_format_boundary_detail(r.get("borde_metodo", ""), bd))

    if r.get("junta_ok") is not None:
        lines += [
            "",
            "  8. JUNTAS DE CONSTRUCCION",
            f"     ->   {'CUMPLE' if r['junta_ok'] else 'NO CUMPLE'}",
        ]

    lines += ["", f"{'-' * 60}"]
    return "\n".join(lines)


def _format_boundary_detail(method: str, detail_str: str) -> str:
    """Formatea el detalle de elementos de borde en texto legible."""
    try:
        import ast
        d = ast.literal_eval(detail_str) if isinstance(detail_str, str) else detail_str
    except Exception:
        return f"     Detalle: {detail_str}"

    lines = []
    if method == "DEFORMACION":
        lines.append(f"     c_base = {d.get('c_base', '-')} cm")
        lines.append(f"     C_lim  = {d.get('C_lim', '-')} cm   "
                     f"(c_base {'>=  ' if d.get('c_base', 0) >= d.get('C_lim', 0) else '<   '}C_lim)")
        lines.append(f"     du/H   = {d.get('ratio_du_H', '-')}   "
                     f"(>= 0.005: {'Si' if d.get('ratio_min_ok') else 'No'})")
        if d.get("L_ext"):
            lines.append(f"     L_ext  = {d.get('L_ext')} cm")
        if d.get("largo_borde"):
            lines.append(f"     Largo borde = {d.get('largo_borde')} cm")
    elif method == "ESFUERZO":
        lines.append(f"     sigma_max = {d.get('sigma_max', '-')} kg/cm2")
        lines.append(f"     Limite ON  = {d.get('limit_ON', '-')} kg/cm2  (0.20 f'c)")
        lines.append(f"     Limite OFF = {d.get('limit_OFF', '-')} kg/cm2  (0.15 f'c)")
        if d.get("largo_borde"):
            lines.append(f"     Largo borde = {d.get('largo_borde')} cm")
    else:
        lines.append(f"     Detalle: {detail_str}")
    return "\n".join(lines)


def handle_muro_results(args: list[str]) -> str:
    """cas muro results [nombre]  -> Muestra resultados de diseño."""
    pp = _project()
    results_dir = pp / "results" / "muros_diseno"
    if not results_dir.exists():
        return "No hay resultados de diseño de muros. Use 'cas muro diseno' primero."

    nombre = args[0] if args else None
    if nombre:
        fname = _sanitize(nombre) + ".csv"
        rows = read_results_csv(pp, f"muros_diseno/{fname}")
        if not rows:
            raise InvalidInput(f"Sin resultados para muro '{nombre}'.")
    else:
        rows = []
        for p in sorted(results_dir.glob("*.csv")):
            rows.extend(read_results_csv(pp, f"muros_diseno/{p.name}"))
        if not rows:
            return "No hay resultados de diseño de muros."

    summary: list[dict] = []
    for i, r in enumerate(rows):
        summary.append({
            "N": str(i + 1),
            "nombre": r.get("nombre", ""),
            "flexion": "OK" if r.get("flexion_ok") in (True, "True") else "FALLA",
            "agriet.": "OK" if r.get("cracking_ok") in (True, "True") else "FALLA",
            "corte": "OK" if r.get("corte_ok") in (True, "True") else "FALLA",
            "borde": "SI" if r.get("borde_requiere") in (True, "True") else "NO",
            "rho_h": r.get("rho_h", ""),
            "rho_v": r.get("rho_v", ""),
            "diseno": "OK" if r.get("diseno_ok") in (True, "True") else "FALLA",
        })

    cols = ["N", "nombre", "flexion", "agriet.", "corte", "borde", "rho_h", "rho_v", "diseno"]
    tabla = format_table(summary, columns=cols)
    return "Resultados de diseno de muros (RNE E.060)\n\n" + tabla


def _generar_docx_muros(
    md_partes: list[str],
    docx_path: str,
    imagenes: list[tuple[str, str]] | None = None,
) -> str | None:
    """Genera el Word (.docx) de muros reutilizando el generador estándar de sismo.

    Usa `generar_docx_sismo` (igual estilo que sismo/irregularidades) y luego
    agrega, si existen, las imágenes de superficie de interacción al final.
    Retorna la ruta si se generó exitosamente, None si no.
    """
    try:
        from axis.reportes.docx_sismo import generar_docx_sismo
        from docx import Document
        from docx.shared import Cm
    except ImportError:
        return None

    ruta = generar_docx_sismo(md_partes, docx_path)
    if not ruta:
        return None

    if imagenes:
        try:
            doc = Document(ruta)
            for nombre_muro, img in imagenes:
                doc.add_page_break()
                p = doc.add_paragraph()
                run = p.add_run(f"Superficie de interacción – {nombre_muro}")
                run.bold = True
                doc.add_paragraph()
                doc.add_picture(img, width=Cm(15))
            doc.save(ruta)
        except Exception:
            # Si algo falla con las imágenes, dejamos el docx base igual.
            pass

    return ruta


def handle_muro_report(args: list[str]) -> str:
    """
    cas muro report [nombre] [DEFORMACION|ESFUERZO] [delta_u] [joint_Av] [R]

    Genera un reporte consolidado de diseño multipiso de muros (RNE E.060),
    en formato Markdown y Word, usando muros_def/muros_pisos. Si no se pasa
    nombre, incluye TODOS los muros definidos (tipicamente los analizados con
    'cas muro etabs-diseno ...').
    """
    from axis.cli.pm_plotter import save_superficie_interaccion

    pp = _project()
    defs = read_csv(pp, "muros_def")
    if not defs:
        return "No hay muros definidos para diseño multipiso. Use 'cas muro etabs-diseno ...' o 'cas muro def ...' primero."

    # Parsear argumentos
    nombre_filtro: str | None = None
    b_method: str | None = None
    delta_u: float | None = None
    j_Av: float | None = None
    R_val: float | None = None

    for a in args:
        au = a.upper()
        if au in ("DEFORMACION", "ESFUERZO"):
            b_method = au
        elif nombre_filtro is None:
            nombre_filtro = a
        elif delta_u is None:
            try:
                delta_u = float(a)
            except ValueError:
                pass
        elif j_Av is None:
            try:
                j_Av = float(a)
            except ValueError:
                pass
        elif R_val is None:
            try:
                R_val = float(a)
            except ValueError:
                pass

    # Filtrar muros
    if nombre_filtro:
        defs = [d for d in defs if d.get("nombre") == nombre_filtro]
        if not defs:
            raise InvalidInput(f"Muro '{nombre_filtro}' no definido en muros_def.")

    salidas: list[str] = []
    md_partes: list[str] = ["# REPORTE DE DISEÑO MULTIPISO DE MUROS (RNE E.060)\n"]
    imagenes: list[tuple[str, str]] = []

    for muro_def in defs:
        nombre = muro_def.get("nombre", "")
        if not nombre:
            continue

        pisos_raw = [r for r in read_csv(pp, "muros_pisos") if r.get("muro") == nombre]
        if not pisos_raw:
            continue

        lm = float(muro_def["lm"]); t_val = float(muro_def["t"])
        fc = float(muro_def["fc"]); fy = float(muro_def["fy"]); fyt = float(muro_def["fyt"])

        pisos_data = []
        for p in pisos_raw:
            Pu_tn = float(p["Pu"]); Vu_tn = float(p["Vu"]); Mu_tnm = float(p["Mu"])
            mn_str = str(p.get("Mn_manual", "")).strip()
            c_str = str(p.get("c", "")).strip()
            mn_kgcm = float(mn_str) * 100000.0 if mn_str and mn_str not in ("", "None") else None
            c_cm = float(c_str) if c_str and c_str not in ("", "None") else None

            pisos_data.append({
                "piso": int(p["piso"]),
                "hm": float(p["hm"]),
                "Pu": Pu_tn * 1000.0,
                "Vu": abs(Vu_tn) * 1000.0,
                "Mu": abs(Mu_tnm) * 100000.0,
                "Mn_manual": mn_kgcm,
                "c": c_cm,
            })

        data = {
            "nombre": nombre, "lm": lm, "t": t_val,
            "fc": fc, "fy": fy, "fyt": fyt,
            "pisos": pisos_data,
        }
        if b_method:
            data["boundary_method"] = b_method
        if delta_u is not None:
            data["delta_u"] = delta_u
        if j_Av is not None:
            data["joint_Av"] = j_Av
        if R_val is not None:
            data["R"] = R_val

        result = run("diseno", "muro_multi", data)
        sismo_dir = "SY" if ("Y" in nombre.upper() and "X" not in nombre.upper()) else "SX"
        etabs_rows = read_results_csv(pp, f"muros_multi/{_sanitize(nombre)}_etabs.csv")
        df_etabs = None
        if etabs_rows and pd is not None:
            try:
                df_etabs = pd.DataFrame(etabs_rows)
                for c in ("P", "V2", "V3", "T", "M2", "M3"):
                    if c in df_etabs.columns:
                        df_etabs[c] = pd.to_numeric(df_etabs[c], errors="coerce")
                if "Story" in df_etabs.columns:
                    df_etabs["Story"] = df_etabs["Story"].astype(str)
                if "Output Case" in df_etabs.columns:
                    df_etabs["Output Case"] = df_etabs["Output Case"].astype(str)
            except Exception:
                df_etabs = None
        elif pd is not None:
            # Fallback: si no hay CSV persistido, intentar leer ETABS en vivo.
            try:
                df_etabs, _ = _filtrar_pier_forces(nombre)
            except Exception:
                df_etabs = None
        texto = _strip_ansi(
            _format_multi_output(
                result,
                pisos_raw,
                muro_def,
                df_etabs=df_etabs,
                pier_f=nombre,
                pp=pp,
                sismo_dir=sismo_dir,
            )
        )
        md_partes.append(f"## Muro {nombre}\n```text\n{texto}\n```")

        # Imagen de superficie de interacción
        try:
            diagramas = read_json(pp, "diagramas.json") or {}
            asignaciones = read_csv(pp, "muro_asignaciones")
            asig_muro = next((a for a in asignaciones if (a.get("muro") or "").strip() == nombre), None)
            if asig_muro:
                nom_sec = (asig_muro.get("Diagrama_Nominal") or "").strip()
                ult_sec = (asig_muro.get("Diagrama_Ultimo") or "").strip() or nom_sec
                section_name = ult_sec or nom_sec
            else:
                section_name = nombre
            key = f"{section_name}_ultimo"
            puntos = diagramas.get(key) or diagramas.get(f"{section_name}_nominal")

            puntos_esfuerzo = None
            comb_path = f"muros_multi/{_sanitize(nombre)}_combinaciones.csv"
            comb_rows = read_results_csv(pp, comb_path)
            if comb_rows:
                puntos_esfuerzo = [
                    {"P": float(r.get("P", 0)), "M2": float(r.get("M2", 0)), "M3": float(r.get("M3", 0))}
                    for r in comb_rows
                ]

            if puntos:
                from pathlib import Path as _P
                results_dir = _P(pp) / "results"
                img_path = results_dir / f"muro_multi_{_sanitize(nombre)}_pm.png"
                subtit = f"{nombre} — diagrama {section_name}, {len(puntos)} pts"
                if puntos_esfuerzo:
                    subtit += f" — {len(puntos_esfuerzo)} combinaciones"
                save_superficie_interaccion(
                    puntos,
                    str(img_path),
                    titulo="Superficie de Interacción P-M2-M3",
                    subtitulo=subtit,
                    puntos_esfuerzo=puntos_esfuerzo,
                )
                imagenes.append((nombre, str(img_path)))
                md_partes.append(f"## Superficie de interacción – {nombre}\n```text\nImagen: {img_path.name}\n```")
        except Exception:
            pass

    # Guardar reporte en results/
    from pathlib import Path

    results_dir = Path(pp) / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    if nombre_filtro:
        base = f"muros_multi_reporte_{_sanitize(nombre_filtro)}"
    else:
        base = "muros_multi_reporte_general"

    md_path = results_dir / f"{base}.md"
    docx_path = results_dir / f"{base}.docx"

    md_path.write_text("\n\n".join(md_partes), encoding="utf-8")

    docx_ok = _generar_docx_muros(md_partes, str(docx_path), imagenes)

    msg = f"Reporte guardado en results/: '{base}.md'"
    if docx_ok:
        msg += f", '{base}.docx'"
    salidas.append(msg)

    return "\n\n".join(salidas)


def handle_muro_results_delete(args: list[str]) -> str:
    """cas muro results-delete <nombre>  -> Elimina resultados de diseño (piso único)."""
    pp = _project()
    if not args:
        raise InvalidInput("Uso: cas muro results-delete <nombre>")
    nombre = args[0]
    results_dir = pp / "results" / "muros_diseno"
    if not results_dir.exists():
        raise InvalidInput("No hay resultados de diseño de muros para borrar.")
    fname = _sanitize(nombre) + ".csv"
    path = results_dir / fname
    if not path.exists():
        raise InvalidInput(f"No existe archivo de resultados para muro '{nombre}'.")
    path.unlink()
    return f"Resultados de diseño de muro '{nombre}' eliminados."


# ===================================================================
# DISENO MULTIPISO  (RNE E.060)
# ===================================================================

_DEF_FIELDS = ["nombre", "lm", "t", "fc", "fy", "fyt"]
_PISOS_FIELDS = ["muro", "piso", "hm", "Pu", "Vu", "Mu", "Mn_manual", "c"]


def handle_muro_def(args: list[str]) -> str:
    """cas muro def <nombre> <lm> <t> <fc> <fy> <fyt>

    Define geometria y materiales de un muro para diseno multipiso.
    Unidades: lm/t(cm), fc/fy/fyt(kg/cm2).
    """
    pp = _project()
    if len(args) < 6:
        raise InvalidInput(
            "Uso: cas muro def <nombre> <lm> <t> <fc> <fy> <fyt>\n"
            "  lm/t en cm, fc/fy/fyt en kg/cm2")
    try:
        nombre = args[0]
        lm = float(args[1]); t_val = float(args[2])
        fc = float(args[3]); fy = float(args[4]); fyt = float(args[5])
    except ValueError:
        raise InvalidInput("Parametros numericos invalidos.")
    if lm <= 0 or t_val <= 0 or fc <= 0 or fy <= 0 or fyt <= 0:
        raise InvalidInput("Todos los valores deben ser positivos.")

    row = {"nombre": nombre, "lm": lm, "t": t_val, "fc": fc, "fy": fy, "fyt": fyt}
    existing = read_csv(pp, "muros_def")
    idx = next((i for i, r in enumerate(existing) if r.get("nombre") == nombre), None)
    if idx is not None:
        existing[idx] = row
        msg = f"Muro '{nombre}' actualizado."
    else:
        existing.append(row)
        msg = f"Muro '{nombre}' definido."
    write_csv(pp, existing, "muros_def", _DEF_FIELDS)
    for i, r in enumerate(existing):
        r["N"] = str(i + 1)
    return msg + "\n\n" + format_table(existing, columns=["N"] + _DEF_FIELDS)


def handle_muro_piso(args: list[str]) -> str:
    """cas muro piso <nombre_muro> <N_piso> <hm> <Pu> <Vu> <Mu> [Mn] [c]

    Agrega un piso al muro. Unidades: hm(cm), Pu(Tn), Vu(Tn), Mu(Tn-m), Mn(Tn-m), c(cm).
    """
    pp = _project()
    if len(args) < 6:
        raise InvalidInput(
            "Uso: cas muro piso <nombre_muro> <N_piso> <hm> <Pu> <Vu> <Mu> [Mn] [c]\n"
            "  hm(cm), Pu(Tn), Vu(Tn), Mu(Tn-m), Mn(Tn-m), c(cm)")
    try:
        muro = args[0]; piso = int(args[1])
        hm = float(args[2]); Pu = float(args[3])
        Vu = float(args[4]); Mu = float(args[5])
        Mn = float(args[6]) if len(args) > 6 else ""
        c_v = float(args[7]) if len(args) > 7 else ""
    except ValueError:
        raise InvalidInput("Parametros numericos invalidos.")

    defs = read_csv(pp, "muros_def")
    if not any(r.get("nombre") == muro for r in defs):
        raise InvalidInput(
            f"Muro '{muro}' no definido. Use 'cas muro def {muro} ...' primero.")

    row = {"muro": muro, "piso": piso, "hm": hm, "Pu": Pu, "Vu": Vu,
           "Mu": Mu, "Mn_manual": Mn, "c": c_v}

    existing = read_csv(pp, "muros_pisos")
    idx = next((i for i, r in enumerate(existing)
                if r.get("muro") == muro and str(r.get("piso")) == str(piso)), None)
    if idx is not None:
        existing[idx] = row
        msg = f"Piso {piso} de '{muro}' actualizado."
    else:
        existing.append(row)
        msg = f"Piso {piso} agregado a '{muro}'."
    write_csv(pp, existing, "muros_pisos", _PISOS_FIELDS)

    pisos_muro = [r for r in existing if r.get("muro") == muro]
    for i, r in enumerate(pisos_muro):
        r["N"] = str(i + 1)
    cols = ["N", "muro", "piso", "hm", "Pu", "Vu", "Mu", "Mn_manual", "c"]
    return msg + "\n\n" + format_table(pisos_muro, columns=cols)


def handle_muro_pisos(args: list[str]) -> str:
    """cas muro pisos [nombre]  -> Lista pisos de un muro (o todos)."""
    pp = _project()
    rows = read_csv(pp, "muros_pisos")
    if not rows:
        return "No hay pisos definidos. Use 'cas muro piso ...' para agregar."
    nombre = args[0] if args else None
    if nombre:
        rows = [r for r in rows if r.get("muro") == nombre]
        if not rows:
            raise InvalidInput(f"Sin pisos para muro '{nombre}'.")
    for i, r in enumerate(rows):
        r["N"] = str(i + 1)
    cols = ["N", "muro", "piso", "hm", "Pu", "Vu", "Mu", "Mn_manual", "c"]
    return "Pisos definidos\n\n" + format_table(rows, columns=cols)


def handle_muro_del_piso(args: list[str]) -> str:
    """cas muro del-piso <nombre> <N_piso>  -> Elimina un piso."""
    pp = _project()
    if len(args) < 2:
        raise InvalidInput("Uso: cas muro del-piso <nombre> <N_piso>")
    muro = args[0]; piso = args[1]
    rows = read_csv(pp, "muros_pisos")
    new = [r for r in rows if not (r.get("muro") == muro and str(r.get("piso")) == piso)]
    if len(new) == len(rows):
        raise InvalidInput(f"No existe piso {piso} de muro '{muro}'.")
    write_csv(pp, new, "muros_pisos", _PISOS_FIELDS)
    return f"Piso {piso} de '{muro}' eliminado."


# ═══════════════════════════════════════════════════════════════════════
# Asignación de diagramas a muros (base de datos compartida: diagramas.json)
# ═══════════════════════════════════════════════════════════════════════

def handle_muro_asignar(args: list[str]) -> str:
    """cas muro asignar <nombre_muro> <Diagrama_Nominal> [Diagrama_Ultimo]

    Asigna diagramas de interacción a un muro. El muro debe existir en muros_def.
    """
    pp = _project()
    if len(args) < 2:
        raise InvalidInput(
            "Uso: cas muro asignar <nombre_muro> <Diagrama_Nominal> [Diagrama_Ultimo]\n"
            "  nombre_muro: mismo que en 'cas muro def'\n"
            "  Diagrama_Nominal: nombre de sección con diagrama nominal cargado\n"
            "  Diagrama_Ultimo: opcional; si se omite se usa el nominal")
    nombre_muro = args[0].strip()
    nom = args[1].strip()
    ult = args[2].strip() if len(args) > 2 else nom

    defs = read_csv(pp, "muros_def")
    if not any(r.get("nombre") == nombre_muro for r in defs):
        raise InvalidInput(f"Muro '{nombre_muro}' no definido. Use 'cas muro def ...' primero.")

    diagramas = read_json(pp, "diagramas.json") or {}
    if f"{nom}_nominal" not in diagramas and f"{nom}_ultimo" not in diagramas:
        raise InvalidInput(
            f"No existe diagrama con nombre '{nom}'. Use 'cas diagrama list' para ver secciones disponibles.")
    if ult != nom and f"{ult}_ultimo" not in diagramas and f"{ult}_nominal" not in diagramas:
        raise InvalidInput(f"No existe diagrama con nombre '{ult}'.")

    fieldnames = ELEMENT_FIELDNAMES.get("muro_asignaciones", ["muro", "Diagrama_Nominal", "Diagrama_Ultimo"])
    ensure_data_csv_exists(pp, "muro_asignaciones", fieldnames)
    existing = read_csv(pp, "muro_asignaciones")
    idx = next((i for i, r in enumerate(existing) if r.get("muro") == nombre_muro), None)
    row = {"muro": nombre_muro, "Diagrama_Nominal": nom, "Diagrama_Ultimo": ult}
    if idx is not None:
        existing[idx] = row
        msg = f"Asignación del muro '{nombre_muro}' actualizada."
    else:
        existing.append(row)
        msg = f"Asignación del muro '{nombre_muro}' creada."

    write_csv(pp, existing, "muro_asignaciones", fieldnames)

    rows_fmt = [{"N": i + 1, **r} for i, r in enumerate(existing)]
    return msg + "\n\n" + format_table(rows_fmt, columns=["N", "muro", "Diagrama_Nominal", "Diagrama_Ultimo"])


def handle_muro_multi(args: list[str]) -> str:
    """cas muro multi <nombre> [DEFORMACION|ESFUERZO] [delta_u] [joint_Av]

    Ejecuta diseno multipiso completo RNE E.060.
    """
    pp = _project()
    if not args:
        raise InvalidInput(
            "Uso: cas muro multi <nombre> [DEFORMACION|ESFUERZO] [delta_u] [joint_Av] [R]")

    nombre = args[0]
    defs = read_csv(pp, "muros_def")
    muro_def = next((r for r in defs if r.get("nombre") == nombre), None)
    if not muro_def:
        raise InvalidInput(f"Muro '{nombre}' no definido. Use 'cas muro def ...'.")

    pisos_raw = [r for r in read_csv(pp, "muros_pisos") if r.get("muro") == nombre]
    if not pisos_raw:
        raise InvalidInput(f"Sin pisos para '{nombre}'. Use 'cas muro piso ...'.")

    b_method = None; delta_u = None; j_Av = None; R_val = None
    for a in args[1:]:
        au = a.upper()
        if au in ("DEFORMACION", "ESFUERZO"):
            b_method = au
        elif delta_u is None:
            try:
                delta_u = float(a)
            except ValueError:
                pass
        elif j_Av is None:
            try:
                j_Av = float(a)
            except ValueError:
                pass
        elif R_val is None:
            try:
                R_val = float(a)
            except ValueError:
                pass

    lm = float(muro_def["lm"]); t_val = float(muro_def["t"])
    fc = float(muro_def["fc"]); fy = float(muro_def["fy"]); fyt = float(muro_def["fyt"])

    pisos_data = []
    for p in pisos_raw:
        Pu_tn = float(p["Pu"]); Vu_tn = float(p["Vu"]); Mu_tnm = float(p["Mu"])
        mn_str = str(p.get("Mn_manual", "")).strip()
        c_str = str(p.get("c", "")).strip()
        mn_kgcm = float(mn_str) * 100000.0 if mn_str and mn_str not in ("", "None") else None
        c_cm = float(c_str) if c_str and c_str not in ("", "None") else None

        pisos_data.append({
            "piso": int(p["piso"]),
            "hm": float(p["hm"]),
            "Pu": Pu_tn * 1000.0,
            "Vu": abs(Vu_tn) * 1000.0,
            "Mu": abs(Mu_tnm) * 100000.0,
            "Mn_manual": mn_kgcm,
            "c": c_cm,
        })

    data = {
        "nombre": nombre, "lm": lm, "t": t_val,
        "fc": fc, "fy": fy, "fyt": fyt,
        "pisos": pisos_data,
    }
    if b_method:
        data["boundary_method"] = b_method
    if delta_u is not None:
        data["delta_u"] = delta_u
    if j_Av is not None:
        data["joint_Av"] = j_Av
    if R_val is not None:
        data["R"] = R_val

    result = run("diseno", "muro_multi", data)

    # Guardar
    res_dir = pp / "results" / "muros_multi"
    res_dir.mkdir(parents=True, exist_ok=True)
    for p_res in result["pisos"]:
        fname = _sanitize(nombre) + f"_P{p_res['piso']}.csv"
        write_results_csv(pp, f"muros_multi/{fname}", [p_res])

    return _format_multi_output(result, pisos_raw, muro_def, pp=pp)


# Cabeceras compactas para reporte multipiso (ancho mínimo de columnas)
_MUROS_REPORT_HEADER_MAP = {
    "Piso": "Piso",
    "Placa": "Placa",
    "Combinación de Carga": "Comb.",
    "Pu (Tn)": "Pu",
    "V2 (Tn)": "V2",
    "M3 (Tn·m)": "M3",
    "V3 (Tn)": "V3",
    "M2 (Tn·m)": "M2",
    "T (Tn·m)": "T",
    "Combinación": "Comb.",
    "Mu Equiv. (Tn.m)": "Mu Eq.",
    "Cap.ultima (Tn.m)": "Cap.",
    "Ratio": "Ratio",
    "Cumple": "Cumple",
    "Vua (Tn)": "Vua",
    "Mua (Tn·m)": "Mua",
    "H (m) = Mua/(4·Vua)": "H(m)",
    "lm (m)": "lm",
    "2 pisos (m)": "2p",
    "L (m) = max(H,lm,2 pisos)": "L(m)",
    "L (m) = max(H,lm)": "L(m)",
    "Mn (Tn·m)": "Mn",
    "Mn/Mua": "Mn/Mua",
    "R": "R",
    "min(Mn/Mua,R)": "min(Mn/Mua,R)",
    "Vu capac. (Tn)": "Vu cap.",
    "Nivel": "Niv",
    "Vu_cap (Tn)": "Vu_cap",
    "Vc (Tn)": "Vc",
    "Vs (Tn)": "Vs",
    "Vn (Tn)": "Vn",
    "φVn (Tn)": "φVn",
    "φVn≥Vu_cap": "≥Vu_cap",
    "Vs≤0.75Vn": "Vs≤0.75Vn",
    "Vn≤2.6√f'c·Acw": "Vn≤2.6√f'c",
    "Acw (cm²)": "Acw",
    "f'c (kg/cm²)": "f'c",
    "hm (cm)": "hm",
    "lm (cm)": "lm",
    "hm/lm": "hm/lm",
    "αc": "αc",
    "Vc inicial (Tn)": "Vc ini",
    "Factor tracción": "Factor",
    "Vc final (Tn)": "Vc fin",
    "Vs = Acw×ρh×fyt (Tn)": "Vs(Tn)",
    "epsilon_s": "εs",
    "εs": "εs",
    "c (m)": "c",
    "delta_u (m)": "δu",
    "Clim (m)": "Clim",
    "Requiere Confinamiento": "Conf.",
    "c_max (m)": "c_max",
    "c - 0.1·lm (m)": "c-0.1lm",
    "c/2 (m)": "c/2",
    "L (m) = max(c-0.1·lm, c/2)": "L(m)",
    "H (cm)": "H",
    "t = H/25 (cm)": "t H/25",
    "t mín (cm)": "t mín",
    "t actual (cm)": "t",
    "t ≥ H/25": "≥H/25",
    "t ≥ t mín": "≥t mín",
    "Verificación": "Verif.",
    "Pu acumulado (Tn)": "Pu ac.",
    "Ag (cm²)": "Ag",
    "lc (cm)": "lc",
    "h (cm)": "h",
    "φPn (Tn)": "φPn",
    "Vu (Tn)": "Vu",
    "0.27√f'c·Acw (Tn)": "0.27√f'c·Acw",
    "Caso": "Caso",
    "ρh mín.": "ρh mín",
    "ρv mín.": "ρv mín",
    "ρh adopt.": "ρh ad.",
    "ρv adopt.": "ρv ad.",
    "φVn_junta (Tn)": "φVn_j",
    "Av (cm²)": "Av",
    "ρv junta": "ρv j.",
    "Junta OK": "OK?",
    "Area (cm²)": "Area",
    "Inercia (cm⁴)": "Ig",
    "y (cm)": "y",
    "Mcr (Tn·m)": "Mcr",
    "phi*Mn (Tn·m)": "φMn",
    "phi*Mn≥Mcr": "≥Mcr",
}


def _format_multi_output(
    r: dict,
    pisos_raw: list[dict],
    wall_def: dict = None,
    df_etabs=None,
    pier_f: str = None,
    pp: Path = None,
    sismo_dir: str = "SX",
) -> str:
    """Formatea salida multipiso con TODAS las tablas del procedimiento RNE E.060.

    Si df_etabs y pier_f se pasan (flujo etabs-diseno), se anteponen TABLA 1, 2 y 3.
    pp: ruta del proyecto (necesaria para TABLA 2 con diagrama asignado).
    """
    import math
    _h = _MUROS_REPORT_HEADER_MAP

    nombre = r["nombre"]
    ok_global = r.get("diseno_ok", False)
    estado = "CUMPLE" if ok_global else "NO CUMPLE"
    lm = r.get("lm", float(wall_def.get("lm", 0)) if wall_def else 0)
    t = r.get("t", float(wall_def.get("t", 0)) if wall_def else 0)
    fc = float(wall_def.get("fc", 210)) if wall_def else 210
    fy = float(wall_def.get("fy", 4200)) if wall_def else 4200
    fyt = float(wall_def.get("fyt", 4200)) if wall_def else 4200
    H_total = r.get("H_total", 0)
    Acw = lm * t
    sqrt_fc = math.sqrt(fc) if fc > 0 else 0

    lines = [
        f"{'=' * 70}",
        f"  DISENO MULTIPISO: {nombre}   ->   {estado}",
        f"{'=' * 70}",
        "",
        f"  Geometria: lm={lm:.0f} cm  t={t:.0f} cm  Acw={Acw:.0f} cm2",
        f"  Materiales: f'c={fc:.0f}  fy={fy:.0f}  fyt={fyt:.0f} kg/cm2",
        f"  H_total={H_total:.0f} cm  ({H_total/100:.2f} m)",
    ]

    pisos = r.get("pisos")
    if pisos is None:
        pisos = []

    # ── TABLA 1, 2, 3 (solo cuando viene de etabs-diseno) ─────────────
    if df_etabs is not None and not df_etabs.empty and pier_f:
        # TABLA 1: Solicitaciones importadas (igual que referencia)
        tabla1_cols = ["Piso", "Placa", "Combinación de Carga", "Pu (Tn)", "V2 (Tn)", "M3 (Tn·m)", "V3 (Tn)", "M2 (Tn·m)", "T (Tn·m)"]
        tabla1_rows = []
        for _, row in df_etabs.iterrows():
            tabla1_rows.append({
                "Piso": str(row["Story"]),
                "Placa": pier_f,
                "Combinación de Carga": str(row["Output Case"]),
                "Pu (Tn)": round(float(row["P"]), 2),
                "V2 (Tn)": round(float(row["V2"]), 2),
                "M3 (Tn·m)": round(float(row["M3"]), 2),
                "V3 (Tn)": round(float(row["V3"]), 2),
                "M2 (Tn·m)": round(float(row["M2"]), 2),
                "T (Tn·m)": round(float(row["T"]), 2),
            })
        lines += ["", "=" * 70, "  TABLA 1: SOLICITACIONES IMPORTADAS DESDE ETABS", "=" * 70, "", format_table(tabla1_rows, columns=tabla1_cols, header_map=_h)]

        # Mapeo Story -> número de piso (1..n) para coincidir con result["pisos"]
        stories_uniq = sorted(
            df_etabs["Story"].astype(str).unique(),
            key=lambda s: int("".join(c for c in s if c.isdigit()) or 0),
        )
        story_to_piso = {s: i for i, s in enumerate(stories_uniq, 1)}

        # TABLA 2: Verificación P-M con diagrama de interacción asignado
        # surface_ult = capacidad última (TABLA 2). surface_nom = momento nominal (TABLA 3 Mn).
        surface_ult = None
        surface_nom = None
        lines += ["", "=" * 70, "  TABLA 2: VERIFICACIÓN P-M - TODAS LAS COMBINACIONES", "=" * 70, ""]
        asig_muro = None
        if pp is not None:
            asignaciones = read_csv(pp, "muro_asignaciones")
            asig_muro = next((a for a in asignaciones if (a.get("muro") or "").strip() == nombre), None)
        nom_name = (asig_muro.get("Diagrama_Nominal") or "").strip() if asig_muro else ""
        ult_name = (asig_muro.get("Diagrama_Ultimo") or "").strip() if asig_muro else ""
        if not ult_name:
            ult_name = nom_name
        if not nom_name or not asig_muro:
            lines.append("  *** Falta asignar diagrama de interacción para este muro.")
            lines.append("  Use: cas muro asignar <nombre_muro> <Diagrama_Nominal> [Diagrama_Ultimo]")
            lines.append("  No se calcula verificación P-M.")
            lines.append("")
        else:
            diagramas = read_json(pp, "diagramas.json") if pp else {}
            pts_ult = (diagramas or {}).get(f"{ult_name}_ultimo") or (diagramas or {}).get(f"{ult_name}_nominal")
            if not pts_ult:
                lines.append(f"  *** Diagrama '{ult_name}' no encontrado en la base de datos.")
                lines.append("  Cargue el diagrama con: cas diagrama add <nombre> <nominal|ultimo> [archivo]")
                lines.append("  No se calcula verificación P-M.")
                lines.append("")
            else:
                from axis.columnas.analysis import InteractionSurface
                surface_ult = InteractionSurface(pts_ult)
                pts_nom = (diagramas or {}).get(f"{nom_name}_nominal") or (diagramas or {}).get(f"{nom_name}_ultimo")
                if pts_nom:
                    surface_nom = InteractionSurface(pts_nom)
                n_ult = len(pts_ult)
                n_nom = len(pts_nom) if pts_nom else 0
                lines.append(f"  Diagrama asignado: nominal={nom_name} ({n_nom} pts), último={ult_name} ({n_ult} pts)")
                lines.append("")
                tabla2_cols = ["Piso", "Combinación", "Pu (Tn)", "M2 (Tn·m)", "M3 (Tn·m)", "Mu Equiv. (Tn.m)", "Cap.ultima (Tn.m)", "Ratio", "Cumple"]
                tabla2_rows = []
                for _, row in df_etabs.iterrows():
                    Pu = float(row["P"])
                    M2 = float(row["M2"])
                    M3 = float(row["M3"])
                    mu_equiv = math.sqrt(M2 * M2 + M3 * M3)
                    angle_deg = math.degrees(math.atan2(M2, M3))
                    if angle_deg < 0:
                        angle_deg += 360.0
                    try:
                        cap_ultima = surface_ult.get_moment_nominal(Pu, angle_deg)
                    except Exception:
                        cap_ultima = 0.0
                    ratio_pm = (mu_equiv / cap_ultima) if cap_ultima > 0 else (float("inf") if mu_equiv > 0 else 0)
                    cumple = "✓" if ratio_pm <= 1 else "✗"
                    tabla2_rows.append({
                        "Piso": str(row["Story"]),
                        "Combinación": str(row["Output Case"]),
                        "Pu (Tn)": round(Pu, 2),
                        "M2 (Tn·m)": round(M2, 2),
                        "M3 (Tn·m)": round(M3, 2),
                        "Mu Equiv. (Tn.m)": round(mu_equiv, 2),
                        "Cap.ultima (Tn.m)": f"{cap_ultima:,.2f}",
                        "Ratio": round(ratio_pm, 2),
                        "Cumple": cumple,
                    })
                if tabla2_rows:
                    lines.append(format_table(tabla2_rows, columns=tabla2_cols, header_map=_h))

        # TABLA 3: Combinaciones de sismo en la dirección seleccionada (p.ej. SX o SY)
        # Solo se consideran combinaciones con sismo {sismo_dir} y el primer piso.
        # Primero filtramos las combinaciones correspondientes desde el DataFrame de ETABS.
        sismo_tag = str(sismo_dir or "SX").upper()
        sx_cases = [f"1.25(CM+CV)+{sismo_tag}", f"0.9CM+{sismo_tag}"]
        df_sx = df_etabs[df_etabs["Output Case"].astype(str).str.strip().isin(sx_cases)]

        # Geometría global para altura crítica según E.060 21.9.5.3
        sorted_raw = sorted(pisos_raw, key=lambda x: int(x.get("piso", 0)))
        height_2_floors_m = sum(
            float(pr.get("hm", 0)) for pr in sorted_raw[:2]
        ) / 100.0
        lm_m = lm / 100.0

        # Altura acumulada desde la base hasta el tope de cada piso (m)
        cum_height_m_by_piso: dict[int, float] = {}
        acc_cm = 0.0
        for pr in sorted_raw:
            piso_n = int(pr.get("piso", 0))
            acc_cm += float(pr.get("hm", 0))
            cum_height_m_by_piso[piso_n] = acc_cm / 100.0

        # TABLA 3 propiamente dicha (primer piso de cada combinación SX)
        first_story_names = [s for s, num in story_to_piso.items() if num == 1]
        lines += ["", "=" * 70, "  TABLA 3: COMBINACIONES (SX) EN PRIMER PISO - MUA, VUA Y H", "=" * 70, ""]
        tabla3b_cols = [
            "Piso", "Combinación", "Pu (Tn)", "Vua (Tn)", "Mua (Tn·m)",
            "H (m) = Mua/(4·Vua)", "lm (m)", "2 pisos (m)", "L (m) = max(H,lm,2 pisos)",
        ]
        tabla3b_rows = []
        Lcrit_m = 0.0
        for _, row in df_sx.iterrows():
            story_name = str(row["Story"])
            if story_name not in first_story_names:
                continue
            Vua = abs(float(row["V2"]))
            Mua = abs(float(row["M3"]))
            if Vua <= 0:
                continue
            Pu = float(row["P"])
            H_m = Mua / (4.0 * Vua)
            # Para cada fila: L = max(H, lm, 2 pisos)
            L_m = max(H_m, lm_m, height_2_floors_m)
            Lcrit_m = max(Lcrit_m, L_m)
            comb = str(row["Output Case"])
            tabla3b_rows.append({
                "Piso": story_name,
                "Combinación": comb,
                "Pu (Tn)": round(Pu, 2),
                "Vua (Tn)": round(Vua, 2),
                "Mua (Tn·m)": round(Mua, 2),
                "H (m) = Mua/(4·Vua)": f"{H_m:.2f}",
                "lm (m)": f"{lm_m:.2f}",
                "2 pisos (m)": f"{height_2_floors_m:.2f}",
                "L (m) = max(H,lm,2 pisos)": f"{L_m:.2f}",
            })
        piso_limite_amplif = None
        if Lcrit_m > 0.0 and cum_height_m_by_piso:
            # Piso límite: el PRIMER piso cuyo tope alcanza o supera Lcrit (redondeo hacia arriba)
            for piso_n in sorted(cum_height_m_by_piso.keys()):
                if cum_height_m_by_piso[piso_n] + 1e-9 >= Lcrit_m:
                    piso_limite_amplif = piso_n
                    break
            if piso_limite_amplif is None:
                piso_limite_amplif = max(cum_height_m_by_piso.keys())

        if tabla3b_rows:
            lines.append(format_table(tabla3b_rows, columns=tabla3b_cols, header_map=_h))
            if piso_limite_amplif is not None:
                lines.append(
                    f"\n  Altura crítica Lcrit = {Lcrit_m:.2f} m "
                    f"(máximo de L (m) en esta tabla, equivalente hasta el piso {piso_limite_amplif})."
                )

        # TABLA 4: Cortante por capacidad (solo combinaciones SX). Factor = min(Mn/Mua, R)
        from axis.muros.constants import RNE as RNE_MUROS
        R = r.get("R")
        if R is None:
            R = float(getattr(RNE_MUROS, "R", 6.0))
        else:
            R = float(R)
        tabla3_cols = ["Piso", "Combinación", "Pu (Tn)", "Vua (Tn)", "Mua (Tn·m)", "Mn (Tn·m)", "Mn/Mua", "R", "min(Mn/Mua,R)", "Vu capac. (Tn)"]
        tabla3_rows = []
        for _, row in df_sx.iterrows():
            piso_num = story_to_piso.get(str(row["Story"]))
            piso_res = next((x for x in pisos if x.get("piso") == piso_num), None)
            if not piso_res:
                continue
            Vua = abs(float(row["V2"]))
            Mua = abs(float(row["M3"]))
            if surface_nom is not None:
                Pu = float(row["P"])
                M2 = float(row["M2"])
                M3 = float(row["M3"])
                angle_deg = math.degrees(math.atan2(M2, M3))
                if angle_deg < 0:
                    angle_deg += 360.0
                try:
                    Mn_tnm = surface_nom.get_moment_nominal(Pu, angle_deg)
                except Exception:
                    Mn_tnm = (piso_res.get("Mn") or 0) / 100000.0
            else:
                Mn_tnm = (piso_res.get("Mn") or 0) / 100000.0
            mn_mua = (Mn_tnm / Mua) if Mua > 0 else 0
            factor = min(mn_mua, R)  # Mn/Mua ≤ R (E.060 21.9.5.3)

            # Según 21.9.5.3: amplificar solo hasta la altura crítica global,
            # redondeada hacia arriba al piso inmediatamente superior.
            if piso_limite_amplif is not None and piso_num is not None and piso_num > piso_limite_amplif:
                vu_cap = Vua  # por encima de la altura crítica: sin amplificación
            else:
                vu_cap = Vua * factor  # hasta el piso límite (incluido): con capacidad
            tabla3_rows.append({
                "Piso": str(row["Story"]),
                "Combinación": str(row["Output Case"]),
                "Pu (Tn)": round(float(row["P"]), 2),
                "Vua (Tn)": round(Vua, 2),
                "Mua (Tn·m)": round(Mua, 2),
                "Mn (Tn·m)": f"{Mn_tnm:.2f}",
                "Mn/Mua": round(mn_mua, 2),
                "R": R,
                "min(Mn/Mua,R)": round(factor, 2),
                "Vu capac. (Tn)": round(vu_cap, 2),
            })
        lines += ["", "=" * 70, "  TABLA 4: CORTANTE POR CAPACIDAD", "=" * 70, ""]
        if tabla3_rows:
            lines.append(format_table(tabla3_rows, columns=tabla3_cols, header_map=_h))

            # Actualizar Vu_cap por piso usando el MAYOR "Vu capac. (Tn)" de TABLA 4
            max_vu_cap_kg_by_piso: dict[int, float] = {}
            for row in tabla3_rows:
                story_name = str(row.get("Piso", ""))
                piso_num = story_to_piso.get(story_name)
                if piso_num is None:
                    continue
                try:
                    vu_tn = float(row.get("Vu capac. (Tn)", 0) or 0)
                except (TypeError, ValueError):
                    vu_tn = 0.0
                vu_kg = vu_tn * 1000.0
                prev = max_vu_cap_kg_by_piso.get(piso_num, 0.0)
                if vu_kg > prev:
                    max_vu_cap_kg_by_piso[piso_num] = vu_kg

            # Sobrescribir Vu_cap en 'pisos' con el máximo por piso
            if max_vu_cap_kg_by_piso:
                for p in pisos:
                    piso_n = int(p.get("piso", 0) or 0)
                    if piso_n in max_vu_cap_kg_by_piso:
                        p["Vu_cap"] = max_vu_cap_kg_by_piso[piso_n]

        lines.append("")

    # ── TABLA 5: DISEÑO A CORTE POR PISO (columnas como referencia) ──
    lines += ["", "=" * 70, "  TABLA 5: DISEÑO A CORTE POR PISO", "=" * 70, ""]
    t4 = []
    for p in pisos:
        n = p.get("piso", "?")
        # Evaluar cumplimiento de corte con valores redondeados (coherente con la tabla impresa)
        vu_cap_tn = (p.get("Vu_cap") or 0) / 1000.0
        phi_vn_tn = (p.get("phi_Vn") or 0) / 1000.0
        corte_ok_red = round(phi_vn_tn, 2) >= round(vu_cap_tn, 2)
        t4.append({
            "Nivel": n,
            "Vu_cap (Tn)": f"{vu_cap_tn:.2f}",
            "Vc (Tn)": f"{p['Vc']/1000:.2f}",
            "Vs (Tn)": f"{p['Vs']/1000:.2f}",
            "Vn (Tn)": f"{p['Vn']/1000:.2f}",
            "φVn (Tn)": f"{phi_vn_tn:.2f}",
            "φVn≥Vu_cap": "✓" if corte_ok_red else "✗",
            "Vs≤0.75Vn": "✓" if p.get("vs_limit_ok") else "✗",
            "Vn≤2.6√f'c·Acw": "✓" if p.get("vn_limit_ok") else "✗",
        })
    lines.append(format_table(t4, columns=list(t4[0].keys()) if t4 else [], header_map=_h))

    # ── TABLA 5A: DESARROLLO Vc (hm = altura desde el nivel en análisis hasta el tope del muro) ──
    # Para αc (E.060): hm/lm usa la altura total del muro desde la sección en análisis hasta el último piso.
    lines += ["", "=" * 70, "  TABLA 5A: DESARROLLO DEL CÁLCULO DE Vc", "=" * 70, ""]

    def _alpha_c(hm, lm_val):
        r = hm / lm_val if lm_val > 0 else 0
        if r <= 1.5:
            return 0.80
        if r >= 2.0:
            return 0.53
        return 0.80 + (r - 1.5) * (0.53 - 0.80) / 0.5

    sorted_raw = sorted(pisos_raw, key=lambda x: int(x.get("piso", 0)))
    t4a = []
    for p in pisos:
        raw = next((x for x in pisos_raw if str(x.get("piso")) == str(p.get("piso"))), {})
        piso_num = int(p.get("piso", 0))
        # hm = altura desde este nivel hasta el tope (suma de entrepisos desde piso_num hasta el último)
        hm_desde_nivel = sum(float(pr.get("hm", 0)) for pr in sorted_raw if int(pr.get("piso", 0)) >= piso_num)
        ratio_hl = hm_desde_nivel / lm if lm > 0 else 0
        ac = _alpha_c(hm_desde_nivel, lm)
        Vc_inicial = Acw * ac * sqrt_fc
        Pu_kg = float(raw.get("Pu", 0)) * 1000
        factor_t = 1.0
        factor_desc = "1.00 (compresión)"
        if Pu_kg > 0:
            factor_t = max(0, 1 - Pu_kg / (35 * Acw)) if Acw > 0 else 1.0
            factor_desc = f"{factor_t:.4f}"
        Vc_final = Vc_inicial * factor_t
        t4a.append({
            "Nivel": p.get("piso"),
            "Acw (cm²)": f"{Acw:,.0f}",
            "f'c (kg/cm²)": f"{fc:.0f}",
            "hm (cm)": f"{hm_desde_nivel:.0f}",
            "lm (cm)": f"{lm:.0f}",
            "hm/lm": f"{ratio_hl:.2f}",
            "αc": f"{ac:.2f}",
            "Vc inicial (Tn)": f"{Vc_inicial/1000:.2f}",
            "Factor tracción": factor_desc,
            "Vc final (Tn)": f"{Vc_final/1000:.2f}",
        })
    lines.append(format_table(t4a, columns=list(t4a[0].keys()) if t4a else [], header_map=_h))

    # ── TABLA 5B: DESARROLLO Vs (columnas como referencia) ──────────
    lines += ["", "=" * 70, "  TABLA 5B: DESARROLLO DEL CÁLCULO DE Vs", "=" * 70, ""]
    t4b = []
    for p in pisos:
        rho_h = p.get("rho_h", 0)
        vs_tn = p["Vs"] / 1000.0
        t4b.append({
            "Nivel": p.get("piso"),
            "Acw (cm²)": f"{Acw:,.0f}",
            "ρh": f"{rho_h:.4f}",
            "fyt (kg/cm²)": f"{fyt:.0f}",
            "Vs = Acw×ρh×fyt (Tn)": f"{vs_tn:.2f}",
        })
    lines.append(format_table(t4b, columns=list(t4b[0].keys()) if t4b else [], header_map=_h))

    # ── TABLA 6: ELEMENTOS DE BORDE POR PISO (deformación: Piso, Comb., Pu, εs, c, δu, Clim, Conf.) ──
    bg = r.get("borde_global_detalle")
    bm = r.get("borde_global_metodo", "-")
    bg_req = r.get("borde_global_requiere", False)
    lines += ["", "=" * 70, "  TABLA 6: ELEMENTOS DE BORDE POR PISO", "=" * 70, ""]

    # Mostrar siempre la TABLA 6 por deformación cuando hay datos ETABS; si no, cuando método es DEFORMACIÓN y hay bg.
    tiene_etabs = df_etabs is not None and not df_etabs.empty and pier_f
    if tiene_etabs or (bm == "DEFORMACION" and bg):
        def _to_m(v):
            if v is None or v == "" or str(v).strip() == "-":
                return "-"
            try:
                return f"{float(v)/100:.2f}"
            except (TypeError, ValueError):
                return str(v)

        # Datos globales de deformación (desde bg o por defecto)
        delta_u_m = _to_m(bg.get("delta_u")) if bg else "-"
        if not delta_u_m or delta_u_m == "-":
            delta_u_m = f"{(0.005 * H_total) / 100:.2f}" if H_total else "0.01"
        Clim_m = _to_m(bg.get("C_lim")) if bg else "-"
        if not Clim_m or Clim_m == "-":
            ratio = 0.005 if H_total else 0.005
            Clim_m = f"{lm / (600.0 * ratio) / 100:.2f}" if lm else "-"

        # Refuerzo vertical adoptado en el primer piso (para aproximar c)
        base_piso = next((p for p in pisos if int(p.get("piso", 0) or 0) == 1), None)
        rho_v_base = float(base_piso.get("rho_v", 0.0)) if base_piso else 0.0

        t5 = []
        max_c_cm = 0.0
        if df_etabs is not None:
            # Todas las combinaciones de sismo en la dirección seleccionada en el primer piso
            sismo_tag = str(sismo_dir or "SX").upper()
            sx_cases = [f"1.25(CM+CV)+{sismo_tag}", f"0.9CM+{sismo_tag}"]
            df_sx_all = df_etabs[df_etabs["Output Case"].astype(str).str.strip().isin(sx_cases)]
            first_story_names = [s for s, num in story_to_piso.items() if num == 1]
            for _, row in df_sx_all.iterrows():
                story_name = str(row["Story"])
                if story_name not in first_story_names:
                    continue

                Pu_tn = float(row["P"])
                Vu_tn = abs(float(row["V2"]))
                Mu_tnm = abs(float(row["M3"]))

                Pu_kg = Pu_tn * 1000.0
                Mu_kgcm = Mu_tnm * 100000.0  # reservado si luego se quisiera usar

                # Aproximación de c usando el mismo modelo que _c_approx
                As_total = rho_v_base * Acw
                Pu_abs = abs(Pu_kg) if Pu_kg < 0 else Pu_kg
                denom = 0.85 * fc * t if (0.85 * fc * t) != 0 else 1.0
                a_val = (As_total * fy + Pu_abs) / denom
                c_cm = max(0.0, a_val / 0.85)
                if c_cm > lm:
                    c_cm = lm
                if c_cm > max_c_cm:
                    max_c_cm = c_cm

                eps_s = 0.0
                if c_cm > 0 and c_cm < lm:
                    eps_s = 0.003 * (lm - c_cm) / c_cm

                t5.append({
                    "Piso": "1",
                    "Combinación": str(row["Output Case"]),
                    "Pu (Tn)": f"{Pu_tn:.2f}",
                    "εs": f"{eps_s:.2f}",
                    "c (m)": f"{c_cm/100:.2f}",
                    "delta_u (m)": delta_u_m,
                    "Clim (m)": Clim_m,
                    "Requiere Confinamiento": "NO" if not bg_req else "SI",
                })

        # Si no hay filas desde ETABS, mostramos fila global desde bg (solo si hay bg)
        if not t5 and bg:
            c_base_val = bg.get("c_base")
            try:
                c_base_cm = float(c_base_val) if c_base_val is not None else 0.0
            except (TypeError, ValueError):
                c_base_cm = 0.0
            if c_base_cm > max_c_cm:
                max_c_cm = c_base_cm
            t5 = [{
                "Piso": "1",
                "Combinación": "-",
                "Pu (Tn)": f"{bg.get('Pu_tn', 0):.2f}" if isinstance(bg.get('Pu_tn', 0), (int, float)) else str(bg.get('Pu_tn', "-")),
                "εs": f"{bg.get('epsilon_s', 0):.2f}" if isinstance(bg.get('epsilon_s', 0), (int, float)) else str(bg.get('epsilon_s', "-")),
                "c (m)": _to_m(c_base_cm),
                "delta_u (m)": delta_u_m,
                "Clim (m)": Clim_m,
                "Requiere Confinamiento": "NO" if not bg_req else "SI",
            }]

        if t5:
            lines.append(format_table(t5, columns=list(t5[0].keys()), header_map=_h))

        # TABLA 7 nueva: longitud horizontal de elementos de borde (Art. 21.9.7.4(a))
        if max_c_cm > 0:
            c_m = max_c_cm / 100.0
            lm_m = lm / 100.0
            L1_m = max(c_m - 0.10 * lm_m, c_m / 2.0)
            lines += [
                "",
                "=" * 70,
                "  TABLA 7: LONGITUD HORIZONTAL DE ELEMENTOS DE BORDE (Art. 21.9.7.4(a))",
                "=" * 70,
                "",
            ]
            t7_h = [{
                "lm (m)": f"{lm_m:.2f}",
                "c_max (m)": f"{c_m:.2f}",
                "c - 0.1·lm (m)": f"{c_m - 0.10*lm_m:.2f}",
                "c/2 (m)": f"{c_m/2.0:.2f}",
                "L (m) = max(c-0.1·lm, c/2)": f"{L1_m:.2f}",
            }]
            lines.append(format_table(t7_h, columns=list(t7_h[0].keys()), header_map=_h))
        if bg.get("largo_borde"):
            lines.append(f"\n  Largo borde = max(c/2, c-0.10*lm) = {bg['largo_borde']} cm")
    elif bm == "ESFUERZO" and bg:
        # Solo contenido del reporte estándar: no se muestra tabla σ/0.20f'c/0.15f'c.
        pass
    lines.append(f"\n  Requiere elemento de borde: {'SI' if bg_req else 'NO'}")

    # ── TABLA 8: ALTURA DE ELEMENTOS DE BORDE (según Mu/(4·Vu) y lm) ──
    # Se muestran las MISMAS COMBINACIONES que en la TABLA 3,
    # pero solo para el PRIMER piso, y sin usar "2 pisos" en la verificación de L.
    lines += ["", "=" * 70, "  TABLA 8: ALTURA DE ELEMENTOS DE BORDE (H = MUA/(4·VUA))", "=" * 70, ""]

    t7 = []
    max_L_borde_m = 0.0
    lm_m = lm / 100.0

    if df_etabs is not None and not df_etabs.empty and pier_f:
        # Usar exactamente las mismas combinaciones de sismo en la dirección seleccionada que en TABLA 3
        sismo_tag = str(sismo_dir or "SX").upper()
        sx_cases = [f"1.25(CM+CV)+{sismo_tag}", f"0.9CM+{sismo_tag}"]
        df_sx = df_etabs[df_etabs["Output Case"].astype(str).str.strip().isin(sx_cases)]

        # Story -> número de piso como en TABLA 3
        stories_uniq = sorted(
            df_etabs["Story"].astype(str).unique(),
            key=lambda s: int("".join(c for c in s if c.isdigit()) or 0),
        )
        story_to_piso = {s: i for i, s in enumerate(stories_uniq, 1)}

        # Solo primer piso (mismo criterio que TABLA 3)
        first_story_names = [s for s, num in story_to_piso.items() if num == 1]

        # Altura de dos pisos (solo se muestra en columna)
        sorted_raw_2 = sorted(pisos_raw, key=lambda x: int(x.get("piso", 0)))
        height_2_floors_m = (
            sum(float(pr.get("hm", 0)) for pr in sorted_raw_2[:2]) / 100.0 if len(sorted_raw_2) >= 2 else 0.0
        )

        for _, row in df_sx.iterrows():
            story_name = str(row["Story"])
            if story_name not in first_story_names:
                continue

            Pu = float(row["P"])
            Vua = abs(float(row["V2"]))
            Mua = abs(float(row["M3"]))
            if Vua <= 0:
                continue

            H_m = Mua / (4.0 * Vua)
            # L SOLO EN FUNCIÓN DE H Y lm (sin "2 pisos" en la verificación)
            L_borde_m = max(H_m, lm_m)
            max_L_borde_m = max(max_L_borde_m, L_borde_m)

            t7.append({
                "Piso": story_name,
                "Combinación": str(row["Output Case"]),
                "Pu (Tn)": f"{Pu:.2f}",
                "Vua (Tn)": f"{Vua:.2f}",
                "Mua (Tn·m)": f"{Mua:.2f}",
                "H (m) = Mua/(4·Vua)": f"{H_m:.2f}",
                "lm (m)": f"{lm_m:.2f}",
                "2 pisos (m)": f"{height_2_floors_m:.2f}",
                "L (m) = max(H,lm,2 pisos)": f"{L_borde_m:.2f}",
            })
    else:
        # Caso sin df_etabs: se mantiene el comportamiento previo basado en resultados agregados.
        sorted_raw_2 = sorted(pisos_raw, key=lambda x: int(x.get("piso", 0)))
        height_2_floors_m = (
            sum(float(pr.get("hm", 0)) for pr in sorted_raw_2[:2]) / 100.0 if len(sorted_raw_2) >= 2 else 0.0
        )

        # Tomar solo el primer piso definido
        first_piso = None
        if pisos_raw:
            try:
                first_piso = min(int(pr.get("piso", 0)) for pr in pisos_raw)
            except Exception:
                first_piso = 1

        for p in pisos:
            piso_num = p.get("piso")
            if first_piso is not None and int(piso_num or 0) != first_piso:
                continue

            Mu_kgcm_def = p.get("Mua", 0) or 0.0
            Vu_kg_def = p.get("Vu_orig", 0) or 0.0
            H_m = (Mu_kgcm_def / (4 * Vu_kg_def) / 100.0) if Vu_kg_def > 0 else 0.0
            L_borde_m = max(H_m, lm_m)
            max_L_borde_m = max(max_L_borde_m, L_borde_m)

            raw = next((x for x in pisos_raw if str(x.get("piso")) == str(piso_num)), {})
            Pu_tn = float(raw.get("Pu", 0) or 0.0)

            t7.append({
                "Piso": piso_num,
                "Combinación": "-",
                "Pu (Tn)": f"{Pu_tn:.2f}",
                "Vua (Tn)": f"{Vu_kg_def/1000.0:.2f}",
                "Mua (Tn·m)": f"{Mu_kgcm_def/100000.0:.2f}",
                "H (m) = Mua/(4·Vua)": f"{H_m:.2f}",
                "lm (m)": f"{lm_m:.2f}",
                "2 pisos (m)": f"{height_2_floors_m:.2f}",
                "L (m) = max(H,lm,2 pisos)": f"{L_borde_m:.2f}",
            })

    if t7:
        cols_t7 = [
            "Piso",
            "Combinación",
            "Pu (Tn)",
            "Vua (Tn)",
            "Mua (Tn·m)",
            "H (m) = Mua/(4·Vua)",
            "lm (m)",
            "2 pisos (m)",
            "L (m) = max(H,lm,2 pisos)",
        ]
        lines.append(format_table(t7, columns=cols_t7, header_map=_h))
        lines.append(
            f"\n  Altura de elementos de borde adoptada L = {max_L_borde_m:.2f} m "
            "(máximo de L (m) = max(H, lm) en esta tabla)."
        )

    # ── TABLA 9A: VERIFICACIÓN DE ESPESOR (21.9.3.2 y 21.9.3.4; columnas como referencia) ──
    lines += ["", "=" * 70, "  TABLA 9A: VERIFICACIÓN DE ESPESOR POR PISO (21.9.3.2 y 21.9.3.4 RNE E.060)", "=" * 70, ""]
    t_min_ref = 15.0
    t8a = []
    for p in pisos:
        raw = next((x for x in pisos_raw if str(x.get("piso")) == str(p.get("piso"))), {})
        hm_p = float(raw.get("hm", 0))
        t_pred = hm_p / 25.0
        ok_h25 = t >= t_pred
        ok_min = t >= t_min_ref
        t8a.append({
            "Nivel": p.get("piso"),
            "H (cm)": f"{hm_p:.0f}",
            "t = H/25 (cm)": f"{t_pred:.1f}",
            "t mín (cm)": f"{t_min_ref:.0f}",
            "t actual (cm)": f"{t:.0f}",
            "t ≥ H/25": "OK" if ok_h25 else "NO",
            "t ≥ t mín": "OK" if ok_min else "NO",
            "Verificación": "OK" if p.get("geometry_ok") in (True, "True") else "NO",
        })
    lines.append(format_table(t8a, columns=list(t8a[0].keys()), header_map=_h))

    # ── TABLA 9B: COMPRESIÓN PURA (14.5.2) - Pu por piso (ETABS ya da P acumulado en base de cada story) ──
    lines += ["", "=" * 70, "  TABLA 9B: VERIFICACIÓN POR COMPRESIÓN PURA POR PISO (14.5.2 RNE E.060)", "=" * 70, ""]
    t8b = []
    k = r.get("k_buckling", 1.0)
    for p in pisos:
        raw = next((x for x in pisos_raw if str(x.get("piso")) == str(p.get("piso"))), {})
        hm_p = float(raw.get("hm", 0))
        # P en ETABS Pier Forces (Location=Bottom) es ya el axial acumulado en la base de ese story
        pu_acum_tn = abs(float(raw.get("Pu", 0)))
        ratio_kl = (k * hm_p) / (32 * t) if t > 0 else 0
        factor = max(0, 1 - ratio_kl ** 2)
        phi_Pn = 0.55 * 0.70 * fc * Acw * factor
        phi_Pn_tn = phi_Pn / 1000
        ok_comp = pu_acum_tn <= phi_Pn_tn
        t8b.append({
            "Nivel": p.get("piso"),
            "Pu acumulado (Tn)": f"{pu_acum_tn:,.2f}",
            "Ag (cm²)": f"{Acw:,.0f}",
            "k": f"{k:.2f}",
            "lc (cm)": f"{hm_p:.0f}",
            "h (cm)": f"{t:.0f}",
            "φPn (Tn)": f"{phi_Pn_tn:,.2f}",
            "Verificación": "OK" if ok_comp else "NO",
        })
    lines.append(format_table(t8b, columns=list(t8b[0].keys()), header_map=_h))

    # ── TABLA 8C: ACERO MÍNIMO (11.10.7 y 11.10.8); columnas como referencia ──
    lines += ["", "=" * 70, "  TABLA 8C: VERIFICACIÓN DE ACERO DISTRIBUIDO MÍNIMO POR PISO (11.10.7 y 11.10.8 RNE E.060)", "=" * 70, ""]
    umbral = 0.27 * sqrt_fc * Acw
    hm_lm_global = H_total / lm if lm > 0 else 0
    t8c = []
    for p in pisos:
        Vu_cap_kg = p.get("Vu_cap", 0)
        mayor = Vu_cap_kg >= umbral
        if not mayor:
            caso = 1; rh_min = 0.002; rv_min = 0.0015
        else:
            caso = 2; rh_min = 0.0025
            rho_h_adopt_tmp = p.get("rho_h", 0.0025)
            term = 0.5 * (2.5 - hm_lm_global) * (rho_h_adopt_tmp - 0.0025)
            rv_min = max(0.0025, 0.0025 + term)

        rho_h_adopt = p.get("rho_h", 0.0)
        rho_v_raw = p.get("rho_v", 0.0)
        # ρv adoptado no puede ser menor que ρv mínimo normativo
        rho_v_adopt = max(rho_v_raw, rv_min)

        ok_rh = rho_h_adopt >= rh_min
        ok_rv = rho_v_adopt >= rv_min

        # Guardar ρv adoptado efectivo para usarlo luego en TABLA 8D (Av = ρv_adopt·Acw)
        p["_rho_v_eff"] = rho_v_adopt

        t8c.append({
            "Nivel": p.get("piso"),
            "Vu (Tn)": f"{Vu_cap_kg/1000:.2f}",
            "0.27√f'c·Acw (Tn)": f"{umbral/1000:.1f}",
            "Caso": caso,
            "ρh mín.": f"{rh_min:.4f}",
            "ρv mín.": f"{rv_min:.4f}",
            "ρh adopt.": f"{rho_h_adopt:.4f}",
            "ρv adopt.": f"{rho_v_adopt:.4f}",
            "Verificación": "OK" if (ok_rh and ok_rv) else "NO",
        })
    lines.append(format_table(t8c, columns=list(t8c[0].keys()), header_map=_h))

    # ── TABLA 8D: JUNTAS DE CONSTRUCCIÓN (21.9.8 + 11.7.4.3) ───────────
    has_joints = any(p.get("junta_ok") is not None for p in pisos)
    if has_joints:
        lines += ["", "=" * 70, "  TABLA 8D: JUNTAS DE CONSTRUCCIÓN - CORTE POR FRICCIÓN (21.9.8 + 11.7.4.3 RNE E.060)", "=" * 70, ""]
        t8d = []
        for p in pisos:
            if p.get("junta_ok") is not None:
                vu_cap_kg = float(p.get("Vu_cap") or 0.0)
                vu_cap_tn = vu_cap_kg / 1000.0
                raw = next((x for x in pisos_raw if str(x.get("piso")) == str(p.get("piso"))), {})
                Pu_tn = float(raw.get("Pu", 0) or 0.0)
                Pu_kg = Pu_tn * 1000.0
                # ρv adoptado efectivo desde TABLA 8C (o valor original si no existe)
                rho_v_eff = float(p.get("_rho_v_eff", p.get("rho_v", 0.0)) or 0.0)
                # Empezar usando ρv efectivo
                rho_v_joint = rho_v_eff

                def _calc_joint(rho_v_val: float) -> tuple[float, float, float]:
                    """Devuelve (Av_cm2, Vn_kg, phi_Vn_kg) para un ρv dado."""
                    mu_val_local = 1.0
                    Av_local = rho_v_val * Acw
                    Vn_base_local = mu_val_local * (abs(Pu_kg) + Av_local * fy)
                    Vn_lim1_local = 0.2 * fc * Acw
                    Vn_lim2_local = 55.0 * Acw
                    Vn_kg_local = min(Vn_base_local, Vn_lim1_local, Vn_lim2_local)
                    phi_vn_kg_local = 0.75 * Vn_kg_local
                    return Av_local, Vn_kg_local, phi_vn_kg_local

                Av_val, Vn_kg, phi_vn_kg = _calc_joint(rho_v_joint)

                # Si con ρv adoptado no alcanza, subir ρv hasta que (idealmente) φVn ≥ Vu_cap
                if vu_cap_kg > 0 and phi_vn_kg < vu_cap_kg and Acw > 0 and fy > 0:
                    # Ignorando límites de concreto para estimar el ρv requerido:
                    #   0.75 * (|Pu| + ρv * Acw * fy) >= Vu_cap
                    #   => ρv_req >= (Vu_cap/0.75 - |Pu|) / (Acw*fy)
                    num = vu_cap_kg / 0.75 - abs(Pu_kg)
                    den = Acw * fy
                    if den > 0:
                        rho_v_req = max(rho_v_joint, num / den)
                        if rho_v_req > rho_v_joint:
                            rho_v_joint = rho_v_req
                            Av_val, Vn_kg, phi_vn_kg = _calc_joint(rho_v_joint)

                mu_val = 1.0
                phi_vn_joint_tn = phi_vn_kg / 1000.0
                # ratio se mantiene solo para verificación interna, ya no se muestra en tabla
                ratio = (phi_vn_joint_tn / vu_cap_tn) if vu_cap_tn > 0 else 0.0  # noqa: F841
                t8d.append({
                    "Nivel": p.get("piso"),
                    "Vu_cap (Tn)": f"{vu_cap_tn:.2f}",
                    "φVn_junta (Tn)": f"{phi_vn_joint_tn:.2f}",
                    "μ": f"{mu_val:.2f}",
                    "Pu (Tn)": f"{Pu_tn:.2f}",
                    "Av (cm²)": f"{Av_val:.2f}",
                    "ρv junta": f"{rho_v_joint:.4f}",
                    "Junta OK": "✓" if phi_vn_kg >= vu_cap_kg else "✗",
                })
        if t8d:
            lines.append(
                format_table(
                    t8d,
                    columns=[
                        "Nivel",
                        "Vu_cap (Tn)",
                        "φVn_junta (Tn)",
                        "μ",
                        "Pu (Tn)",
                        "Av (cm²)",
                        "ρv junta",
                        "Junta OK",
                    ],
                    header_map=_h,
                )
            )

    # ── TABLA 9: AGRIETAMIENTO (columnas como referencia) ───────────
    lines += ["", "=" * 70, "  TABLA 9: VERIFICACIÓN POR AGRIETAMIENTO (21.9.6.5 RNE E.060)", "=" * 70, ""]
    Ig = (lm * t ** 3) / 12.0 if t else 0
    y_ref = lm / 2.0
    t9 = []
    for p in pisos:
        raw = next((x for x in pisos_raw if str(x.get("piso")) == str(p.get("piso"))), {})
        Pu_tn = abs(float(raw.get("Pu", 0)))
        Mn_tnm = p.get("Mn", 0) / 100000
        Mcr_tnm = (p.get("Mcr", 0) or 0) / 100000
        phi_Mn = 0.9 * Mn_tnm
        phi_mn_ge_mcr = phi_Mn >= Mcr_tnm
        t9.append({
            "Piso": p.get("piso"),
            "Pu (Tn)": f"{Pu_tn:.2f}",
            "Area (cm²)": f"{Acw:,.0f}",
            "Inercia (cm⁴)": f"{Ig:,.2f}",
            "y (cm)": f"{y_ref:.0f}",
            "Mcr (Tn·m)": f"{Mcr_tnm:.2f}",
            "phi*Mn (Tn·m)": f"{phi_Mn:.2f}",
            "phi*Mn≥Mcr": "OK" if phi_mn_ge_mcr else "NO",
        })
    lines.append(format_table(t9, columns=list(t9[0].keys()) if t9 else [], header_map=_h))

    return "\n".join(lines)


def handle_muro_multi_results(args: list[str]) -> str:
    """cas muro multi-results [nombre]  -> Resultados multipiso."""
    pp = _project()
    res_dir = pp / "results" / "muros_multi"
    if not res_dir.exists():
        return "No hay resultados multipiso. Use 'cas muro multi ...' primero."

    nombre = args[0] if args else None
    rows = []
    for p in sorted(res_dir.glob("*.csv")):
        if nombre and not p.stem.startswith(_sanitize(nombre)):
            continue
        rows.extend(read_results_csv(pp, f"muros_multi/{p.name}"))
    if not rows:
        return "No hay resultados multipiso."

    summary = []
    for i, r in enumerate(rows):
        summary.append({
            "N": str(i + 1),
            "nombre": r.get("nombre", ""),
            "piso": r.get("piso", ""),
            "flexion": "OK" if r.get("flexion_ok") in (True, "True") else "FALLA",
            "corte": "OK" if r.get("corte_ok") in (True, "True") else "FALLA",
            "borde": "SI" if r.get("borde_requiere_piso") in (True, "True") else "NO",
            "rho_h": r.get("rho_h", ""),
            "diseno": "OK" if r.get("diseno_ok") in (True, "True") else "FALLA",
        })
    cols = ["N", "nombre", "piso", "flexion", "corte", "borde", "rho_h", "diseno"]
    return "Resultados multipiso (RNE E.060)\n\n" + format_table(summary, columns=cols)


def handle_muro_multi_delete(args: list[str]) -> str:
    """cas muro multi-delete <nombre>  -> Elimina resultados multipiso y datos asociados."""
    pp = _project()
    if not args:
        raise InvalidInput("Uso: cas muro multi-delete <nombre>")
    nombre = args[0]
    name_s = _sanitize(nombre)

    # Borrar resultados multipiso (un archivo por piso + combinaciones)
    res_dir = pp / "results" / "muros_multi"
    if res_dir.exists():
        for p in res_dir.glob("*.csv"):
            if p.stem.startswith(name_s):
                p.unlink()

    # Borrar definicion y pisos asociados
    defs = read_csv(pp, "muros_def")
    defs_new = [r for r in defs if r.get("nombre") != nombre]
    write_csv(pp, defs_new, "muros_def", _DEF_FIELDS)

    pisos = read_csv(pp, "muros_pisos")
    pisos_new = [r for r in pisos if r.get("muro") != nombre]
    write_csv(pp, pisos_new, "muros_pisos", _PISOS_FIELDS)

    return f"Resultados multipiso y datos del muro '{nombre}' eliminados."


def handle_muro_multi_report(args: list[str]) -> str:
    """
    cas muro multi-report <nombre> [DEFORMACION|ESFUERZO] [delta_u] [joint_Av] [R]

    Genera un reporte consolidado de diseño multipiso de un muro (RNE E.060),
    en formato Markdown y Word, usando muros_def/muros_pisos y resultados
    de combinaciones ETABS (si existen) para adjuntar la superficie de
    interacción con puntos de combinaciones.
    """
    if not args:
        raise InvalidInput(
            "Uso: cas muro multi-report <nombre> [DEFORMACION|ESFUERZO] [delta_u] [joint_Av] [R]"
        )

    from axis.cli.pm_plotter import save_superficie_interaccion

    pp = _project()
    nombre = args[0]

    defs = read_csv(pp, "muros_def")
    muro_def = next((r for r in defs if r.get("nombre") == nombre), None)
    if not muro_def:
        raise InvalidInput(f"Muro '{nombre}' no definido. Use 'cas muro def ...' o 'cas muro etabs-diseno ...' primero.")

    pisos_raw = [r for r in read_csv(pp, "muros_pisos") if r.get("muro") == nombre]
    if not pisos_raw:
        raise InvalidInput(f"Sin pisos para '{nombre}'. Use 'cas muro piso ...' o 'cas muro etabs-diseno ...' primero.")

    b_method = None; delta_u = None; j_Av = None; R_val = None
    for a in args[1:]:
        au = a.upper()
        if au in ("DEFORMACION", "ESFUERZO"):
            b_method = au
        elif delta_u is None:
            try:
                delta_u = float(a)
            except ValueError:
                pass
        elif j_Av is None:
            try:
                j_Av = float(a)
            except ValueError:
                pass
        elif R_val is None:
            try:
                R_val = float(a)
            except ValueError:
                pass

    lm = float(muro_def["lm"]); t_val = float(muro_def["t"])
    fc = float(muro_def["fc"]); fy = float(muro_def["fy"]); fyt = float(muro_def["fyt"])

    pisos_data = []
    for p in pisos_raw:
        Pu_tn = float(p["Pu"]); Vu_tn = float(p["Vu"]); Mu_tnm = float(p["Mu"])
        mn_str = str(p.get("Mn_manual", "")).strip()
        c_str = str(p.get("c", "")).strip()
        mn_kgcm = float(mn_str) * 100000.0 if mn_str and mn_str not in ("", "None") else None
        c_cm = float(c_str) if c_str and c_str not in ("", "None") else None

        pisos_data.append({
            "piso": int(p["piso"]),
            "hm": float(p["hm"]),
            "Pu": Pu_tn * 1000.0,
            "Vu": abs(Vu_tn) * 1000.0,
            "Mu": abs(Mu_tnm) * 100000.0,
            "Mn_manual": mn_kgcm,
            "c": c_cm,
        })

    data = {
        "nombre": nombre, "lm": lm, "t": t_val,
        "fc": fc, "fy": fy, "fyt": fyt,
        "pisos": pisos_data,
    }
    if b_method:
        data["boundary_method"] = b_method
    if delta_u is not None:
        data["delta_u"] = delta_u
    if j_Av is not None:
        data["joint_Av"] = j_Av
    if R_val is not None:
        data["R"] = R_val

    # Ejecutar diseño multipiso y formatear salida (todas las tablas)
    result = run("diseno", "muro_multi", data)
    sismo_dir = "SY" if ("Y" in nombre.upper() and "X" not in nombre.upper()) else "SX"
    etabs_rows = read_results_csv(pp, f"muros_multi/{_sanitize(nombre)}_etabs.csv")
    df_etabs = None
    if etabs_rows and pd is not None:
        try:
            df_etabs = pd.DataFrame(etabs_rows)
            for c in ("P", "V2", "V3", "T", "M2", "M3"):
                if c in df_etabs.columns:
                    df_etabs[c] = pd.to_numeric(df_etabs[c], errors="coerce")
            if "Story" in df_etabs.columns:
                df_etabs["Story"] = df_etabs["Story"].astype(str)
            if "Output Case" in df_etabs.columns:
                df_etabs["Output Case"] = df_etabs["Output Case"].astype(str)
        except Exception:
            df_etabs = None
    elif pd is not None:
        # Fallback: si no hay CSV persistido, intentar leer ETABS en vivo.
        try:
            df_etabs, _ = _filtrar_pier_forces(nombre)
        except Exception:
            df_etabs = None
    texto = _strip_ansi(
        _format_multi_output(
            result,
            pisos_raw,
            muro_def,
            df_etabs=df_etabs,
            pier_f=nombre,
            pp=pp,
            sismo_dir=sismo_dir,
        )
    )

    salidas: list[str] = []
    md_partes: list[str] = [
        "# REPORTE DE DISEÑO MULTIPISO DE MUROS (RNE E.060)\n",
        f"## Muro {nombre}\n```text\n{texto}\n```",
    ]
    salidas.append(f"Muro procesado: {nombre}")

    # Intentar generar imagen de superficie de interacción con combinaciones
    imagen_path_str: str | None = None
    try:
        diagramas = read_json(pp, "diagramas.json") or {}
        asignaciones = read_csv(pp, "muro_asignaciones")
        asig_muro = next((a for a in asignaciones if (a.get("muro") or "").strip() == nombre), None)
        if asig_muro:
            nom_sec = (asig_muro.get("Diagrama_Nominal") or "").strip()
            ult_sec = (asig_muro.get("Diagrama_Ultimo") or "").strip() or nom_sec
            section_name = ult_sec or nom_sec
        else:
            section_name = nombre
        key = f"{section_name}_ultimo"
        puntos = diagramas.get(key) or diagramas.get(f"{section_name}_nominal")

        puntos_esfuerzo = None
        comb_path = f"muros_multi/{_sanitize(nombre)}_combinaciones.csv"
        comb_rows = read_results_csv(pp, comb_path)
        if comb_rows:
            puntos_esfuerzo = [
                {"P": float(r.get("P", 0)), "M2": float(r.get("M2", 0)), "M3": float(r.get("M3", 0))}
                for r in comb_rows
            ]

        if puntos:
            from pathlib import Path as _P
            results_dir = _P(pp) / "results"
            img_path = results_dir / f"muro_multi_{_sanitize(nombre)}_pm.png"
            subtit = f"{nombre} — diagrama {section_name}, {len(puntos)} pts"
            if puntos_esfuerzo:
                subtit += f" — {len(puntos_esfuerzo)} combinaciones"
            save_superficie_interaccion(
                puntos,
                str(img_path),
                titulo="Superficie de Interacción P-M2-M3",
                subtitulo=subtit,
                puntos_esfuerzo=puntos_esfuerzo,
            )
            imagen_path_str = str(img_path)
            md_partes.append(f"## Superficie de interacción – {nombre}\n```text\nImagen: {img_path.name}\n```")
    except Exception:
        imagen_path_str = None

    from pathlib import Path

    results_dir = Path(pp) / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    base = f"muros_multi_reporte_{_sanitize(nombre)}"
    md_path = results_dir / f"{base}.md"
    docx_path = results_dir / f"{base}.docx"

    md_path.write_text("\n\n".join(md_partes), encoding="utf-8")

    imgs = [(nombre, imagen_path_str)] if imagen_path_str else []
    docx_ok = _generar_docx_muros(md_partes, str(docx_path), imgs)

    msg = f"Reporte guardado en results/: '{base}.md'"
    if docx_ok:
        msg += f", '{base}.docx'"
    salidas.append(msg)

    return "\n\n".join(salidas)


# ===================================================================
# ETABS -> IMPORTAR SOLICITACIONES (PASO 2)
# ===================================================================

def _filtrar_pier_forces(pier_name: str):
    """Filtra Pier Forces identico al procedimiento de Muros_Estructurales.

    Filtros:
      - Pier = pier_name
      - Location = bottom
      - Output Case: 1.4CM+1.7CV, 1.25(CM+CV)+SX, 1.25(CM+CV)+SY, 0.9CM+SX, 0.9CM+SY

    Columnas retornadas: Story, Output Case, P, V2, V3, T, M2, M3
    """
    df = get_table("Pier Forces", log=True)
    if df is None or df.empty:
        raise InvalidInput("No se pudo leer 'Pier Forces' desde ETABS.")
    df = df.copy()

    # Buscar columnas de forma flexible (igual que etabs_importer.py)
    cols_orig = list(df.columns)
    col_lower = {str(c).strip().lower(): c for c in cols_orig}

    def find_col(preferred, keywords=None):
        for p in preferred:
            if p in cols_orig:
                return p
            if p.lower() in col_lower:
                return col_lower[p.lower()]
        if keywords:
            for c, orig in col_lower.items():
                if any(k in c for k in keywords):
                    return orig
        return None

    c_story = find_col(["Story", "StoryLabel"], ["story"])
    c_pier = find_col(["Pier", "PierLabel"], ["pier"])
    c_case = find_col(["Output Case", "OutputCase"], ["output", "case"])
    c_loc = find_col(["Location", "Loc", "Point"], ["location", "loc"])
    c_p = find_col(["P", "P1"], ["axial"])
    c_v2 = find_col(["V2", 'V"'], ["v2", "shear2"])
    c_v3 = find_col(["V3", "V#"], ["v3", "shear3"])
    c_t = find_col(["T", "T1"], ["torsion"])
    c_m2 = find_col(["M2", "M22"], ["m2", "moment2"])
    c_m3 = find_col(["M3", "M33"], ["m3", "moment3"])

    if not c_story or not c_pier or not c_p or not c_v2 or not c_m3:
        raise InvalidInput(
            "Pier Forces no contiene columnas esperadas (Story, Pier, P, V2, M3).")

    # Filtro 1: Pier
    pier_f = str(pier_name).strip()
    df = df[df[c_pier].astype(str).str.strip() == pier_f]
    if df.empty:
        raise InvalidInput(f"Sin datos para Pier '{pier_f}'.")

    # Filtro 2: Location = bottom
    if c_loc:
        df = df[df[c_loc].astype(str).str.strip().str.lower() == "bottom"]
        if df.empty:
            raise InvalidInput(f"Sin datos con Location='bottom' para Pier '{pier_f}'.")

    # Filtro 3: Combinaciones de carga permitidas
    COMBOS = [
        "1.4CM+1.7CV", "1.4CM +1.7CV",
        "1.25(CM+CV)+SX", "1.25(CM+CV)+SY",
        "0.9CM+SX", "0.9CM+SY",
    ]
    if c_case:
        df["_case_norm"] = df[c_case].astype(str).str.strip().str.replace(" ", "").str.upper()
        combos_norm = [c.replace(" ", "").upper() for c in COMBOS]
        mask = df["_case_norm"].isin(combos_norm)

        if not mask.any():
            # Coincidencia parcial
            for caso in combos_norm:
                if "1.4" in caso and "CM" in caso and "CV" in caso:
                    mask = mask | df["_case_norm"].str.contains("1.4.*CM.*CV", regex=True, na=False)
                elif "1.25" in caso and "SX" in caso:
                    mask = mask | df["_case_norm"].str.contains("1.25.*CM.*CV.*SX", regex=True, na=False)
                elif "1.25" in caso and "SY" in caso:
                    mask = mask | df["_case_norm"].str.contains("1.25.*CM.*CV.*SY", regex=True, na=False)
                elif "0.9" in caso and "SX" in caso:
                    mask = mask | df["_case_norm"].str.contains("0.9.*CM.*SX", regex=True, na=False)
                elif "0.9" in caso and "SY" in caso:
                    mask = mask | df["_case_norm"].str.contains("0.9.*CM.*SY", regex=True, na=False)

        df = df[mask]
        df = df.drop(columns=["_case_norm"], errors="ignore")
        if df.empty:
            raise InvalidInput(
                f"Sin datos para Pier '{pier_f}' con las combinaciones de diseno "
                "(1.4CM+1.7CV, 1.25(CM+CV)+SX/SY, 0.9CM+SX/SY).")

    # Convertir numericas
    for col in [c_p, c_v2, c_v3, c_t, c_m2, c_m3]:
        if col and col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Renombrar a nombres estandar
    rename = {}
    if c_story: rename[c_story] = "Story"
    if c_case: rename[c_case] = "Output Case"
    if c_p: rename[c_p] = "P"
    if c_v2: rename[c_v2] = "V2"
    if c_v3: rename[c_v3] = "V3"
    if c_t: rename[c_t] = "T"
    if c_m2: rename[c_m2] = "M2"
    if c_m3: rename[c_m3] = "M3"
    df = df.rename(columns=rename)

    std_cols = ["Story", "Output Case", "P", "V2", "V3", "T", "M2", "M3"]
    for c in std_cols:
        if c not in df.columns:
            df[c] = 0.0

    return df[std_cols].copy(), pier_f


def _leer_story_definitions():
    """Lee Story Definitions de ETABS y devuelve alturas y elevaciones."""
    story_df = get_table("Story Definitions", log=True)
    if story_df is None or story_df.empty:
        raise InvalidInput("No se pudo leer 'Story Definitions'.")
    story_df = story_df.copy()
    story_df.columns = [str(c).strip().lower() for c in story_df.columns]
    if "story" not in story_df.columns or "height" not in story_df.columns:
        raise InvalidInput("'Story Definitions' sin columnas 'Story'/'Height'.")

    alturas = {}; elevaciones = {}
    for _, fila in story_df.iterrows():
        sn = str(fila["story"])
        try:
            alturas[sn] = float(fila["height"])
        except (TypeError, ValueError):
            continue
        if "elevation" in story_df.columns:
            try:
                elevaciones[sn] = float(fila["elevation"])
            except (TypeError, ValueError):
                pass
    return alturas, elevaciones


def _max_vu_cap_por_piso_desde_combinaciones_sx(df, pp, nombre, R, pisos_raw, lm_cm, sismo_dir: str = "SX"):
    """Máximo cortante de diseño Vu_cap por piso entre combinaciones SX (para diseño y TABLA 4).

    Lógica:
      1) Usa diagrama nominal para obtener Mn (superficie de interacción).
      2) Para cada combinación SX en el PRIMER piso:
           H = Mua/(4·Vua)       [m]
           L = max(H, lm, 2 pisos)  [m]
         Lcrit = max(L) entre esas combinaciones.
      3) Determina el piso_límite como el PRIMER piso cuyo tope acumulado ≥ Lcrit
         (redondeo hacia arriba).
      4) Para cada combinación SX y piso:
           - Si piso <= piso_límite: Vu_cap = Vua * min(Mn/Mua, R)
           - Si piso > piso_límite: Vu_cap = Vua
      5) Para cada piso: devuelve el MÁXIMO Vu_cap (kg) entre sus combinaciones SX.

    Retorna dict piso_num -> Vu_cap en kg, o {} si falta info.
    """
    import math
    if pp is None:
        return {}

    # Diagrama nominal asignado al muro
    asignaciones = read_csv(pp, "muro_asignaciones")
    asig_muro = next((a for a in asignaciones if (a.get("muro") or "").strip() == nombre), None)
    if not asig_muro:
        return {}
    nom_name = (asig_muro.get("Diagrama_Nominal") or "").strip()
    if not nom_name:
        return {}
    diagramas = read_json(pp, "diagramas.json") or {}
    pts_nom = diagramas.get(f"{nom_name}_nominal") or diagramas.get(f"{nom_name}_ultimo")
    if not pts_nom:
        return {}
    from axis.columnas.analysis import InteractionSurface
    surface_nom = InteractionSurface(pts_nom)

    # Story -> piso (1..n)
    stories_uniq = sorted(
        df["Story"].astype(str).unique(),
        key=lambda s: int("".join(c for c in s if c.isdigit()) or 0),
    )
    story_to_piso = {s: i for i, s in enumerate(stories_uniq, 1)}

    sismo_tag = str(sismo_dir or "SX").upper()
    sx_cases = [f"1.25(CM+CV)+{sismo_tag}", f"0.9CM+{sismo_tag}"]
    df_sx = df[df["Output Case"].astype(str).str.strip().isin(sx_cases)]
    if df_sx.empty:
        return {}

    # Geometría global para altura crítica (usamos pisos_raw para hm)
    sorted_raw = sorted(pisos_raw, key=lambda x: int(x.get("piso", 0)))
    if not sorted_raw:
        return {}
    height_2_floors_m = sum(float(pr.get("hm", 0)) for pr in sorted_raw[:2]) / 100.0
    lm_m = lm_cm / 100.0

    # Altura acumulada desde la base hasta el tope de cada piso (m)
    cum_height_m_by_piso: dict[int, float] = {}
    acc_cm = 0.0
    for pr in sorted_raw:
        piso_n = int(pr.get("piso", 0))
        acc_cm += float(pr.get("hm", 0))
        cum_height_m_by_piso[piso_n] = acc_cm / 100.0

    # 1) Calcular Lcrit a partir del primer piso de cada combinación SX
    first_story_names = [s for s, num in story_to_piso.items() if num == 1]
    Lcrit_m = 0.0
    for _, row in df_sx.iterrows():
        story_name = str(row["Story"])
        if story_name not in first_story_names:
            continue
        Vua = abs(float(row["V2"]))
        Mua = abs(float(row["M3"]))
        if Vua <= 0:
            continue
        H_m = Mua / (4.0 * Vua)  # m
        L_m = max(H_m, lm_m, height_2_floors_m)
        Lcrit_m = max(Lcrit_m, L_m)

    # Piso límite de amplificación (redondeo hacia arriba)
    piso_limite_amplif = None
    if Lcrit_m > 0.0 and cum_height_m_by_piso:
        for piso_n in sorted(cum_height_m_by_piso.keys()):
            if cum_height_m_by_piso[piso_n] + 1e-9 >= Lcrit_m:
                piso_limite_amplif = piso_n
                break
        if piso_limite_amplif is None:
            piso_limite_amplif = max(cum_height_m_by_piso.keys())

    # 2) Para cada combinación SX y piso, obtener Vu_cap con la regla anterior
    max_by_piso: dict[int, float] = {}
    for _, row in df_sx.iterrows():
        story = str(row["Story"])
        piso_num = story_to_piso.get(story)
        if not piso_num:
            continue

        Vua = abs(float(row["V2"]))
        Mua = abs(float(row["M3"]))
        if Mua <= 0:
            continue

        Pu = float(row["P"])
        M2 = float(row["M2"])
        M3 = float(row["M3"])
        angle_deg = math.degrees(math.atan2(M2, M3))
        if angle_deg < 0:
            angle_deg += 360.0
        try:
            Mn_tnm = surface_nom.get_moment_nominal(Pu, angle_deg)
        except Exception:
            continue

        factor = min(Mn_tnm / Mua, R)

        # Hasta el piso límite (incluido): amplificada; arriba: solo Vua
        if piso_limite_amplif is not None and piso_num > piso_limite_amplif:
            vu_cap_tn = Vua
        else:
            vu_cap_tn = Vua * factor

        vu_cap_kg = vu_cap_tn * 1000.0
        prev = max_by_piso.get(piso_num, 0.0)
        if vu_cap_kg > prev:
            max_by_piso[piso_num] = vu_cap_kg

    return max_by_piso


def _envolvente_por_piso(df, nombre, alturas, elevaciones):
    """Calcula envolvente critica por piso a partir del DataFrame filtrado."""
    stories_in_df = df["Story"].astype(str).unique().tolist()
    if elevaciones:
        stories_sorted = sorted(stories_in_df, key=lambda s: elevaciones.get(s, 0.0))
    else:
        try:
            stories_sorted = sorted(stories_in_df,
                key=lambda s: float("".join(ch for ch in s if ch.isdigit() or ch == ".") or "0"))
        except Exception:
            stories_sorted = sorted(stories_in_df)

    pisos_raw = []
    for idx, story in enumerate(stories_sorted, 1):
        sub = df[df["Story"].astype(str) == story]
        hm_val = alturas.get(story, 0.0)
        if hm_val <= 0:
            raise InvalidInput(f"Sin altura para Story '{story}'.")
        # Envolvente: máximo en compresión (min P) y máximos en valor absoluto para V y M de TODAS las combinaciones
        Pu_tn = sub["P"].min()
        Vu_tn = sub["V2"].abs().max()
        Mu_tnm = sub["M3"].abs().max()
        hm_cm = hm_val * 100.0

        pisos_raw.append({
            "muro": nombre, "piso": idx, "hm": hm_cm,
            "Pu": round(float(Pu_tn), 4),
            "Vu": round(float(Vu_tn), 4),
            "Mu": round(float(Mu_tnm), 4),
            "Mn_manual": "", "c": "",
        })
    return pisos_raw


def handle_muro_etabs_import(args: list[str]) -> str:
    """cas muro etabs-import <nombre> <lm> <t> <fc> <fy> <fyt> <pier>

    PASO 2: Importa solicitaciones desde ETABS y muestra TABLA 1.
    Filtros (identico a Muros_Estructurales):
      - Location = bottom
      - Combinaciones: 1.4CM+1.7CV, 1.25(CM+CV)+SX/SY, 0.9CM+SX/SY
    Columnas: Story, Output Case, P, V2, V3, T, M2, M3
    """
    pp = _project()
    if len(args) < 7:
        raise InvalidInput(
            "Uso: cas muro etabs-import <nombre> <lm> <t> <fc> <fy> <fyt> <pier>")
    try:
        nombre = args[0]
        lm = float(args[1]); t_val = float(args[2])
        fc = float(args[3]); fy = float(args[4]); fyt = float(args[5])
        pier_name = args[6]
    except ValueError:
        raise InvalidInput("Parametros numericos invalidos.")

    clear_table_cache()

    # Filtrar Pier Forces (identico a Muros_Estructurales)
    df, pier_f = _filtrar_pier_forces(pier_name)

    # ── TABLA 1: Solicitaciones importadas (igual que referencia: Piso, Placa, Combinación, Pu, V2, M3, V3, M2, T) ──
    tabla1_cols = ["Piso", "Placa", "Combinación de Carga", "Pu (Tn)", "V2 (Tn)", "M3 (Tn·m)", "V3 (Tn)", "M2 (Tn·m)", "T (Tn·m)"]
    tabla1_rows = []
    for _, row in df.iterrows():
        tabla1_rows.append({
            "Piso": str(row["Story"]),
            "Placa": pier_f,
            "Combinación de Carga": str(row["Output Case"]),
            "Pu (Tn)": round(float(row["P"]), 2),
            "V2 (Tn)": round(float(row["V2"]), 2),
            "M3 (Tn·m)": round(float(row["M3"]), 2),
            "V3 (Tn)": round(float(row["V3"]), 2),
            "M2 (Tn·m)": round(float(row["M2"]), 2),
            "T (Tn·m)": round(float(row["T"]), 2),
        })
    tabla1 = format_table(tabla1_rows, columns=tabla1_cols)

    # ── Leer Story Definitions ──
    alturas, elevaciones = _leer_story_definitions()

    # ── Envolvente por piso ──
    pisos_raw = _envolvente_por_piso(df, nombre, alturas, elevaciones)

    # ── Guardar definicion y pisos ──
    row_def = {"nombre": nombre, "lm": lm, "t": t_val, "fc": fc, "fy": fy, "fyt": fyt}
    defs = read_csv(pp, "muros_def")
    idx_d = next((i for i, r in enumerate(defs) if r.get("nombre") == nombre), None)
    if idx_d is not None:
        defs[idx_d] = row_def
    else:
        defs.append(row_def)
    write_csv(pp, defs, "muros_def", _DEF_FIELDS)

    all_pisos = [r for r in read_csv(pp, "muros_pisos") if r.get("muro") != nombre]
    all_pisos.extend(pisos_raw)
    write_csv(pp, all_pisos, "muros_pisos", _PISOS_FIELDS)

    # ── Salida ──
    n_combos = len(df)
    n_pisos = len(pisos_raw)
    lines = [
        f"Importado desde ETABS: Pier '{pier_f}'",
        f"  Filtros: Location=bottom, Combos=1.4CM+1.7CV / 1.25(CM+CV)+SX/SY / 0.9CM+SX/SY",
        f"  Registros: {n_combos} combinaciones en {n_pisos} pisos",
        f"  Muro '{nombre}': lm={lm} cm, t={t_val} cm, f'c={fc}, fy={fy}, fyt={fyt}",
        "",
        "=" * 70,
        "  TABLA 1: SOLICITACIONES IMPORTADAS DESDE ETABS",
        "=" * 70,
        "",
        tabla1,
        "",
        "=" * 70,
        "  ENVOLVENTE POR PISO (Pu=max compresion, Vu=max|V2|, Mu=max|M3|)",
        "=" * 70,
        "",
    ]
    for i, p in enumerate(pisos_raw):
        p["N"] = str(i + 1)
    lines.append(format_table(pisos_raw,
                              columns=["N", "piso", "hm", "Pu", "Vu", "Mu"]))
    lines += [
        "",
        "Siguiente paso: cas muro multi " + nombre + " [DEFORMACION|ESFUERZO] [delta_u] [joint_Av]",
    ]
    return "\n".join(lines)


# ===================================================================
# ETABS -> IMPORTAR + DISENAR (atajo)
# ===================================================================

def handle_muro_etabs_diseno(args: list[str]) -> str:
    """cas muro etabs-diseno <nombre> <lm> <t> <fc> <fy> <fyt> <pier> [DEFORMACION|ESFUERZO] [delta_u] [joint_Av]

    Atajo: importa + disena en un paso (usa mismos filtros que etabs-import).
    """
    pp = _project()
    if len(args) < 7:
        raise InvalidInput(
            "Uso: cas muro etabs-diseno <nombre> <lm> <t> <fc> <fy> <fyt> <pier> "
            "[DEFORMACION|ESFUERZO] [delta_u] [joint_Av] [R]")
    try:
        nombre = args[0]
        lm = float(args[1]); t_val = float(args[2])
        fc = float(args[3]); fy = float(args[4]); fyt = float(args[5])
        pier_name = args[6]
    except ValueError:
        raise InvalidInput("Parametros numericos invalidos.")

    b_method = None; delta_u = None; j_Av = None; R_val = None
    for a in args[7:]:
        au = a.upper()
        if au in ("DEFORMACION", "ESFUERZO"):
            b_method = au
        elif delta_u is None:
            try:
                delta_u = float(a)
            except ValueError:
                pass
        elif j_Av is None:
            try:
                j_Av = float(a)
            except ValueError:
                pass
        elif R_val is None:
            try:
                R_val = float(a)
            except ValueError:
                pass

    # Determinar dirección de sismo predominante a partir del nombre del pier.
    # Por compatibilidad hacia atrás, si no se detecta 'Y' se asume 'SX'.
    pier_upper = str(pier_name).upper()
    if "Y" in pier_upper and "X" not in pier_upper:
        sismo_dir = "SY"
    else:
        sismo_dir = "SX"

    clear_table_cache()

    # Usar misma logica de filtrado que etabs-import
    df, pier_f = _filtrar_pier_forces(pier_name)
    alturas, elevaciones = _leer_story_definitions()
    pisos_raw = _envolvente_por_piso(df, nombre, alturas, elevaciones)

    R = R_val if R_val is not None else 6.0
    max_vu_cap_por_piso_kg = _max_vu_cap_por_piso_desde_combinaciones_sx(
        df, pp, nombre, R, pisos_raw, lm, sismo_dir=sismo_dir
    )

    pisos_data = []
    for p in pisos_raw:
        piso_num = int(p["piso"])
        row = {
            "piso": piso_num,
            "hm": float(p["hm"]),
            "Pu": float(p["Pu"]) * 1000.0,
            "Vu": abs(float(p["Vu"])) * 1000.0,
            "Mu": abs(float(p["Mu"])) * 100000.0,
        }
        if max_vu_cap_por_piso_kg and piso_num in max_vu_cap_por_piso_kg:
            row["Vu_cap"] = max_vu_cap_por_piso_kg[piso_num]
        pisos_data.append(row)

    data = {
        "nombre": nombre, "lm": lm, "t": t_val,
        "fc": fc, "fy": fy, "fyt": fyt,
        "pisos": pisos_data,
    }
    if b_method:
        data["boundary_method"] = b_method
    if delta_u is not None:
        data["delta_u"] = delta_u
    if j_Av is not None:
        data["joint_Av"] = j_Av
    if R_val is not None:
        data["R"] = R_val

    result = run("diseno", "muro_multi", data)

    # Guardar definicion y pisos
    row_def = {"nombre": nombre, "lm": lm, "t": t_val, "fc": fc, "fy": fy, "fyt": fyt}
    defs = read_csv(pp, "muros_def")
    idx_def = next((i for i, r in enumerate(defs) if r.get("nombre") == nombre), None)
    if idx_def is not None:
        defs[idx_def] = row_def
    else:
        defs.append(row_def)
    write_csv(pp, defs, "muros_def", _DEF_FIELDS)

    all_pisos = [r for r in read_csv(pp, "muros_pisos") if r.get("muro") != nombre]
    all_pisos.extend(pisos_raw)
    write_csv(pp, all_pisos, "muros_pisos", _PISOS_FIELDS)

    # Guardar resultados
    res_dir = pp / "results" / "muros_multi"
    res_dir.mkdir(parents=True, exist_ok=True)
    for p_res in result["pisos"]:
        fname = _sanitize(nombre) + f"_P{p_res['piso']}.csv"
        write_results_csv(pp, f"muros_multi/{fname}", [p_res])

    # Guardar combinaciones de ETABS (TABLA 1) para diagrama plot: P, M2, M3 por fila
    comb_rows = []
    etabs_rows = []
    for _, row in df.iterrows():
        comb_rows.append({
            "Story": str(row["Story"]),
            "Output Case": str(row["Output Case"]),
            "P": float(row["P"]),
            "M2": float(row["M2"]),
            "M3": float(row["M3"]),
        })
        etabs_rows.append({
            "Story": str(row["Story"]),
            "Output Case": str(row["Output Case"]),
            "P": float(row["P"]),
            "V2": float(row["V2"]),
            "V3": float(row["V3"]),
            "T": float(row["T"]),
            "M2": float(row["M2"]),
            "M3": float(row["M3"]),
        })
    write_results_csv(
        pp, f"muros_multi/{_sanitize(nombre)}_combinaciones.csv", comb_rows,
        fieldnames=["Story", "Output Case", "P", "M2", "M3"],
    )
    write_results_csv(
        pp, f"muros_multi/{_sanitize(nombre)}_etabs.csv", etabs_rows,
        fieldnames=["Story", "Output Case", "P", "V2", "V3", "T", "M2", "M3"],
    )

    header = (
        f"Importado desde ETABS: Pier '{pier_f}', {len(pisos_data)} pisos\n"
        f"Filtros: Location=bottom, Combos=1.4CM+1.7CV / 1.25(CM+CV)+SX/SY / 0.9CM+SX/SY\n\n"
    )
    wdef = {"lm": lm, "t": t_val, "fc": fc, "fy": fy, "fyt": fyt}
    return header + _format_multi_output(
        result,
        pisos_raw,
        wdef,
        df_etabs=df,
        pier_f=pier_f,
        pp=pp,
        sismo_dir=sismo_dir,
    )
