"""Operación de diseño por cortante para vigas de concreto reforzado."""

from __future__ import annotations

from axis.core.registry import register
from axis.core.exceptions import InvalidInput


def _calcular_cortante(
    nombre: str, fc: float, fy: float, b: float, h: float, rec: float, vu_tn: float
) -> dict:
    """
    Diseño por cortante. Vu en Tn (se convierte a kg).
    Retorna dict con d, phi, Vu, Vc, V_max, Av_s, Vs, s_max, Error.
    """
    vu_kg = vu_tn * 1000
    if fc <= 0 or fy <= 0 or b <= 0 or h <= 0 or rec <= 0 or vu_tn < 0:
        raise InvalidInput("Parámetros inválidos: verifique unidades y signos")
    if rec >= h:
        raise InvalidInput("El recubrimiento debe ser menor que la altura total")

    d = h - rec
    phi = 0.85

    vc = 0.53 * (fc**0.5) * b * d
    v_max = vc + 2 * (fc**0.5) * b * d

    if vu_kg <= (vc / 2) * phi:
        av_s = 0.0
        error_msg = None
    elif (vc / 2) * phi < vu_kg <= v_max:
        av_s_raw = (vu_kg / phi - vc) / (fy * d)
        av_s = max(0.0, av_s_raw)
        error_msg = None
    else:
        av_s = None
        error_msg = "Vu > V_max"

    vs = vu_kg - phi * vc
    s_1 = d / 2
    s_2 = 60
    s_max = min(s_1, s_2) / 2

    return {
        "nombre": nombre,
        "d": round(d, 2),
        "phi": phi,
        "Vu": round(vu_kg, 2),
        "Vc": round(vc, 2),
        "V_max": round(v_max, 2),
        "Av_s": round(av_s, 4) if av_s is not None else None,
        "Vs": round(vs, 2),
        "s_max": round(s_max, 2),
        "Error": error_msg,
    }


@register("cortante", "viga")
def cortante_viga(data: dict) -> dict:
    """
    Diseño por cortante. Data: {vigas: [{fc, fy, b, h, rec, Vu}, ...]}
    Vu en Tn.
    """
    if "vigas" not in data:
        raise InvalidInput("Data debe tener 'vigas' con lista de vigas")

    resultados = []
    for i, fila in enumerate(data["vigas"]):
        nombre = fila.get("nombre") or f"Viga {i + 1}"
        fc = _to_float(fila.get("fc"))
        fy = _to_float(fila.get("fy"))
        b = _to_float(fila.get("b"))
        h = _to_float(fila.get("h"))
        rec = _to_float(fila.get("rec"))
        vu = _to_float(fila.get("Vu", 0))
        res = _calcular_cortante(nombre, fc, fy, b, h, rec, vu)
        resultados.append(res)

    return {"resultados": resultados}


def _to_float(val) -> float:
    """Convierte a float, manejando strings con coma."""
    if val is None or val == "":
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    s = str(val).replace(",", ".")
    return float(s)
