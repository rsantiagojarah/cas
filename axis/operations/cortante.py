"""Operación de diseño por cortante para vigas (E-060)."""

from __future__ import annotations

from axis.core.registry import register
from axis.core.exceptions import InvalidInput
from axis.core.utils import to_float
from axis.operations.cortante_calculos import (
    PHI_CORTANTE,
    vc,
    vs_max,
    vn_max,
    vs_requerido,
    av_s_requerido,
    s_max_base,
    s_max_reducido,
    av_s_min,
)


def _calcular_cortante(
    nombre: str, fc: float, fy: float, b: float, h: float, rec: float, vu_tn: float
) -> dict:
    """
    Diseño por cortante E-060. Vu en Tn (se convierte a kg).
    Retorna: d, Vu, Vc, Vs_max, Vn_max, Vs, cumple_Vs_max, Av_s, s_max, Av_s_min, Error.
    """
    vu_kg = vu_tn * 1000
    if fc <= 0 or fy <= 0 or b <= 0 or h <= 0 or rec <= 0 or vu_tn < 0:
        raise InvalidInput("Parámetros inválidos: verifique unidades y signos")
    if rec >= h:
        raise InvalidInput("El recubrimiento debe ser menor que la altura total")

    d = h - rec
    vc_kg = vc(fc, b, d)
    vs_max_kg = vs_max(fc, b, d)
    vn_max_kg = vn_max(vc_kg, vs_max_kg)

    umbral_sin_refuerzo = (vc_kg / 2) * PHI_CORTANTE
    umbral_maximo = PHI_CORTANTE * vn_max_kg

    if vu_kg <= umbral_sin_refuerzo:
        av_s_req = 0.0
        vs_kg = 0.0
        error_msg = None
    elif vu_kg <= umbral_maximo:
        vs_kg = vs_requerido(vu_kg, vc_kg)
        vs_kg = max(0.0, vs_kg)
        av_s_req = av_s_requerido(vs_kg, fy, d)
        error_msg = None
    else:
        vs_kg = vs_requerido(vu_kg, vc_kg)
        av_s_req = None
        error_msg = "Vu > phi*Vn_max: aumentar peralte o fc"

    cumple_vs_max = (vs_kg <= vs_max_kg) if av_s_req is not None else None

    s_max_base_cm = s_max_base(d)
    s_max_cm = s_max_reducido(s_max_base_cm, vs_kg, fc, b, d)
    av_s_min_ratio = av_s_min(fc, b, fy)
    if av_s_req is not None and av_s_req > 0:
        av_s_req = max(av_s_req, av_s_min_ratio)

    # Fuerzas en Tn; sin columnas d, Vu, Vn_max. Orden: flujo de diseño.
    return {
        "nombre": nombre,
        "Vc": round(vc_kg / 1000, 2),
        "phi_Vc_2": round(umbral_sin_refuerzo / 1000, 2),
        "Vs_max": round(vs_max_kg / 1000, 2),
        "phi_Vn_max": round(umbral_maximo / 1000, 2),
        "Vs": round(vs_kg / 1000, 2) if av_s_req is not None else round(vs_kg / 1000, 2),
        "cumple_Vs_max": cumple_vs_max,
        "Av_s": round(av_s_req, 4) if av_s_req is not None else None,
        "s_max": round(s_max_cm, 2),
        "Av_s_min": round(av_s_min_ratio, 4),
    }


@register("cortante", "viga")
def cortante_viga(data: dict) -> dict:
    """
    Diseño por cortante E-060. Data: {vigas: [{fc, fy, b, h, rec, Vu}, ...]}.
    Vu en Tn.
    """
    if "vigas" not in data:
        raise InvalidInput("Data debe tener 'vigas' con lista de vigas")

    resultados = []
    for i, fila in enumerate(data["vigas"]):
        nombre = fila.get("nombre") or f"Viga {i + 1}"
        fc = to_float(fila.get("fc"))
        fy = to_float(fila.get("fy"))
        b = to_float(fila.get("b"))
        h = to_float(fila.get("h"))
        rec = to_float(fila.get("rec"))
        vu = to_float(fila.get("Vu"), default=0.0)
        res = _calcular_cortante(nombre, fc, fy, b, h, rec, vu)
        resultados.append(res)

    return {"resultados": resultados}
