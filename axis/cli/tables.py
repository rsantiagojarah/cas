"""Formateo de tablas y mapas de cabeceras para el CLI. Reglas: ≤200 líneas, ≤150 chars/línea."""

from __future__ import annotations

from tabulate import tabulate

from axis.cli.colors import colorize_table

VIGAS_HEADER_MAP = {
    "N": "Nº",
    "nombre": "Nombre",
    "fc": "fc\n(kg/cm²)",
    "Vu": "Vu\n(Tn)",
    "fy": "fy\n(kg/cm²)",
    "b": "b\n(cm)",
    "h": "h\n(cm)",
    "rec": "rec\n(cm)",
    "Mu": "Mu\n(Tn-m)",
}

CORTANTE_HEADER_MAP = {
    "N": "Nº",
    "nombre": "Nombre",
    "Vu": "Vu\n(Tn)",
    "d": "d\n(cm)",
    "Vc": "Vc\n(Tn)",
    "As/s req.": "As/s req.\n(cm²/cm)",
    "Error": "Error",
    "phi_Vc_2": "φ·Vc/2\n(Tn)",
    "Vs_max": "Vs_max\n(Tn)",
    "phi_Vn_max": "φ·Vn_max\n(Tn)",
    "Vs": "Vs\n(Tn)",
    "cumple_Vs_max": "cumple\nVs_max",
    "Av_s": "Av/s\n(cm²/cm)",
    "s_max": "s_max\n(cm)",
    "Av_s_min": "Av/s_min\n(cm²/cm)",
}

FLEXION_HEADER_MAP = {
    "N": "Nº",
    "nombre": "Nombre",
    "Mu": "Mu\n(Tn-m)",
    "As": "As\n(cm²)",
    "As'": "As'\n(cm²)",
    "Asmin": "Asmin\n(cm²)",
    "Asmax": "Asmax\n(cm²)",
    "As_colocar": "As col.\n(cm²)",
    "As_prima_colocar": "As' col.\n(cm²)",
}

MUROS_HEADER_MAP = {
    "N": "No",
    "nombre": "Nombre",
    "hm": "hm\n(cm)",
    "lm": "lm\n(cm)",
    "t": "t\n(cm)",
    "fc": "f'c\n(kg/cm2)",
    "fy": "fy\n(kg/cm2)",
    "fyt": "fyt\n(kg/cm2)",
    "Pu": "Pu\n(Tn)",
    "Vu": "Vu\n(Tn)",
    "flexion": "Flexion",
    "agriet.": "Agriet.",
    "corte": "Corte",
    "borde": "Borde",
    "diseno": "Diseno",
    "rho_h": "rho_h",
    "rho_v": "rho_v",
    # Muros multipiso / ETABS – encabezados compactos en 2 líneas
    "Piso": "Piso",
    "Placa": "Placa",
    "Combinación de Carga": "Comb.\nde Carga",
    "Combinación": "Comb.",
    "Pu (Tn)": "Pu\n(Tn)",
    "V2 (Tn)": "V2\n(Tn)",
    "V3 (Tn)": "V3\n(Tn)",
    "T (Tn·m)": "T\n(Tn·m)",
    "M2 (Tn·m)": "M2\n(Tn·m)",
    "M3 (Tn·m)": "M3\n(Tn·m)",
    "Mu Equiv. (Tn.m)": "Mu\nEquiv.\n(Tn·m)",
    "Cap.ultima (Tn.m)": "Cap.\núltima\n(Tn·m)",
    "Mu Equiv. (Tn·m)": "Mu\nEquiv.\n(Tn·m)",
    "Cap.ultima (Tn·m)": "Cap.\núltima\n(Tn·m)",
    "Mu (Tn·m)": "Mu\n(Tn·m)",
    "Vu_cap (Tn)": "Vu_cap\n(Tn)",
    "Vua (Tn)": "Vua\n(Tn)",
    "Mn (Tn·m)": "Mn\n(Tn·m)",
    "Mn/Mua": "Mn/\nMua",
    "min(Mn/Mua,R)": "min(\nMn/Mua,R)",
    "Vu capac. (Tn)": "Vu\ncapac.\n(Tn)",
    "H (m) = Mua/(4·Vua)": "H (m)\n=Mua/(4·Vua)",
    "lm (m)": "lm\n(m)",
    "2 pisos (m)": "2 pisos\n(m)",
    "L (m) = max(H,lm,2 pisos)": "L (m)\n=max(H,lm,2p)",
    "L (m) = max(H,lm)": "L (m)\n=max(H,lm)",
    "Nivel": "Nivel",
    "Vu_cap (Tn)": "Vu_cap\n(Tn)",
    "Vc (Tn)": "Vc\n(Tn)",
    "Vs (Tn)": "Vs\n(Tn)",
    "Vn (Tn)": "Vn\n(Tn)",
    "φVn (Tn)": "φVn\n(Tn)",
    "φVn≥Vu_cap": "φVn\n≥Vu_cap",
    "Vn≤2.6√f'c·Acw": "Vn≤2.6\n√f'c·Acw",
    "Acw (cm²)": "Acw\n(cm²)",
    "f'c (kg/cm²)": "f'c\n(kg/cm²)",
    "hm (cm)": "hm\n(cm)",
    "lm (cm)": "lm\n(cm)",
    "hm/lm": "hm/\nlm",
    "αc": "αc",
    "Vc inicial (Tn)": "Vc\ninicial\n(Tn)",
    "Factor tracción": "Factor\ntracción",
    "Vc final (Tn)": "Vc\nfinal\n(Tn)",
    "ρh": "ρh",
    "Vs = Acw×ρh×fyt (Tn)": "Vs = Acw\n×ρh×fyt\n(Tn)",
    "epsilon_s": "εs",
    "εs": "εs",
    "c (m)": "c\n(m)",
    "delta_u (m)": "δu\n(m)",
    "Clim (m)": "Clim\n(m)",
    "Requiere Confinamiento": "Requiere\nconf.",
    "sigma(kg/cm2)": "σ\n(kg/cm²)",
    "0.20f'c": "0.20\nf'c",
    "0.15f'c": "0.15\nf'c",
    "Estado": "Estado",
    "H (cm)": "H\n(cm)",
    "t = H/25 (cm)": "t = H/25\n(cm)",
    "t mín (cm)": "t mín\n(cm)",
    "t actual (cm)": "t act.\n(cm)",
    "t ≥ H/25": "t ≥\nH/25",
    "t ≥ t mín": "t ≥\nt mín",
    "Pu acumulado (Tn)": "Pu\nacum.\n(Tn)",
    "Ag (cm²)": "Ag\n(cm²)",
    "lc (cm)": "lc\n(cm)",
    "h (cm)": "h\n(cm)",
    "φPn (Tn)": "φPn\n(Tn)",
    "Pcm (Tn)": "Pcm\n(Tn)",
    "Nu (Tn)": "Nu\n(Tn)",
    "0.27√f'c·Acw (Tn)": "0.27√f'c\n·Acw\n(Tn)",
    "Caso": "Caso",
    "ρh mín.": "ρh\nmín.",
    "ρv mín.": "ρv\nmín.",
    "ρh adopt.": "ρh\nadopt.",
    "ρv adopt.": "ρv\nadopt.",
    "Area (cm²)": "Area\n(cm²)",
    "Inercia (cm⁴)": "Inercia\n(cm⁴)",
    "y (cm)": "y\n(cm)",
    "Mcr (Tn·m)": "Mcr\n(Tn·m)",
    "phi*Mn (Tn·m)": "φMn\n(Tn·m)",
    "phi*Mn≥Mcr": "φMn\n≥Mcr",
}

COLUMNAS_HEADER_MAP = {
    "N": "No",
    "Story": "Story",
    "Unique_Name": "Unique\nName",
    "Direction": "Dir.",
    "Arriostrado": "Arriost.",
    "k": "k",
    "r": "r\n(cm)",
    "lu": "lu\n(cm)",
    "I": "I\n(cm4)",
    "Ag": "Ag\n(cm2)",
    "Ec": "Ec\n(kg/cm2)",
    "Bd": "Bd",
    "M1/M2": "M1/M2",
    "34-12(M1/M2)": "34-12\n(M1/M2)",
    "(k*lu)/r": "(k*lu)\n/r",
    "Ignorar_2do_Orden": "Ignorar\n2do Ord.",
    "M1_X": "M1_X",
    "M2_X": "M2_X",
    "M1_Y": "M1_Y",
    "M2_Y": "M2_Y",
    "Curvatura_X": "Curv.\nX",
    "Curvatura_Y": "Curv.\nY",
    "Cm_X": "Cm_X",
    "Cm_Y": "Cm_Y",
    "EI": "EI\n(kg·cm²)",
    "EI_X": "EI_X\n(kg·cm²)",
    "EI_Y": "EI_Y\n(kg·cm²)",
    "Pc": "Pc\n(kg)",
    "Pc_X": "Pc_X\n(kg)",
    "Pc_Y": "Pc_Y\n(kg)",
    "Delta_X": "Delta\nX",
    "Delta_Y": "Delta\nY",
    "Station": "Station",
    "Output_Case": "Caso\nCarga",
    "Step_Type": "Step\nType",
    "P": "P\n(Tn)",
    "M2": "M2\n(Tn-m)",
    "M3": "M3\n(Tn-m)",
    "Q": "Q",
    "Classification": "Clasif.",
    "Drift_R": "Drift_R",
    "Vus": "Vus\n(Tn)",
    "Load_Case": "Caso\nCarga",
    "Mn2_Inf": "Mn2 Inf\n(Tn-m)",
    "Mn3_Inf": "Mn3 Inf\n(Tn-m)",
    "Mn2_Sup": "Mn2 Sup\n(Tn-m)",
    "Mn3_Sup": "Mn3 Sup\n(Tn-m)",
    "Mu_Equiv": "Mu Equiv.\n(Tn-m)",
    "Cap_Ultima": "Cap. Ult.\n(Tn-m)",
    "Ratio": "Ratio",
    "Ratio_Max": "Ratio\nMax.",
    "Cumple": "Cumple",
    "Diagrama_Nominal": "Diag.\nNominal",
    "Diagrama_Ultimo": "Diag.\nUltimo",
    "R_X": "R_X",
    "R_Y": "R_Y",
    "Height": "Altura\n(m)",
    "Drift": "Drift",
    "VX": "VX\n(Tn)",
    "VY": "VY\n(Tn)",
    "Selected_Case": "Caso\nSelec.",
    "Delta_o": "Delta_o",
    "he": "he\n(m)",
}


def _cell_str(val: object, decimal_places: int | None = None) -> str:
    if val is None or (isinstance(val, str) and val.lower() == "none"):
        return "-"
    if val == "-" or (isinstance(val, str) and val.strip() == "-"):
        return "-"
    if val is True or (isinstance(val, str) and val.lower() == "true"):
        return "Si"
    if val is False or (isinstance(val, str) and val.lower() == "false"):
        return "No"
    if decimal_places is not None:
        try:
            f = float(val)
            return f"{f:.{decimal_places}f}"
        except (TypeError, ValueError):
            pass
    return str(val)


def format_table(
    rows: list[dict],
    columns: list[str] | None = None,
    header_map: dict[str, str] | None = None,
    decimal_places: int | None = None,
) -> str:
    """Formatea filas en tabla minimalista, centrada. DRY: un solo lugar para tablas."""
    if not rows:
        return "(sin datos)"
    cols = columns or list(rows[0].keys())
    m = header_map or {}
    headers = [
        m.get(c) or VIGAS_HEADER_MAP.get(c) or FLEXION_HEADER_MAP.get(c)
        or CORTANTE_HEADER_MAP.get(c) or MUROS_HEADER_MAP.get(c)
        or COLUMNAS_HEADER_MAP.get(c) or c
        for c in cols
    ]
    table_rows = [[_cell_str(row.get(c, ""), decimal_places) for c in cols] for row in rows]
    n = len(headers)
    raw = tabulate(
        table_rows,
        headers=headers,
        tablefmt="grid",
        colalign=("center",) * n,
    )
    return colorize_table(raw)
