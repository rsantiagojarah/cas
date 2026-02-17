"""Formateo de tablas y mapas de cabeceras para el CLI. Reglas: ≤200 líneas, ≤150 chars/línea."""

from __future__ import annotations

from tabulate import tabulate

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
    "Vc": "Vc\n(Tn)",
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


def _cell_str(val: object) -> str:
    if val is None or (isinstance(val, str) and val.lower() == "none"):
        return "-"
    if val is True or (isinstance(val, str) and val.lower() == "true"):
        return "Si"
    if val is False or (isinstance(val, str) and val.lower() == "false"):
        return "No"
    return str(val)


def format_table(
    rows: list[dict],
    columns: list[str] | None = None,
    header_map: dict[str, str] | None = None,
) -> str:
    """Formatea filas en tabla minimalista, centrada. DRY: un solo lugar para tablas."""
    if not rows:
        return "(sin datos)"
    cols = columns or list(rows[0].keys())
    m = header_map or {}
    headers = [
        m.get(c) or VIGAS_HEADER_MAP.get(c) or FLEXION_HEADER_MAP.get(c)
        or CORTANTE_HEADER_MAP.get(c) or c
        for c in cols
    ]
    table_rows = [[_cell_str(row.get(c, "")) for c in cols] for row in rows]
    n = len(headers)
    return tabulate(
        table_rows,
        headers=headers,
        tablefmt="grid",
        colalign=("center",) * n,
    )
