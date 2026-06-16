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


def _calcular_cortante_losa(
    nombre: str, fc: float, b: float, h: float, rec: float, vu_tn: float
) -> dict:
    """
    Cortante en losa: sin estribos; solo se verifica Vu <= phi*Vc.
    Vc = 0.53*sqrt(fc)*b*d (Art. 11.3.1), phi = 0.85.
    """
    vu_kg = vu_tn * 1000
    if fc <= 0 or b <= 0 or h <= 0 or rec <= 0 or vu_tn < 0:
        raise InvalidInput("Parámetros inválidos: verifique unidades y signos")
    if rec >= h:
        raise InvalidInput("El recubrimiento debe ser menor que la altura total")
    d = h - rec
    vc_kg = vc(fc, b, d)
    phi_vc_tn = (PHI_CORTANTE * vc_kg) / 1000
    cumple = vu_tn <= phi_vc_tn
    return {
        "nombre": nombre,
        "Vu": round(vu_tn, 2),
        "Vc": round(vc_kg / 1000, 2),
        "phi_Vc": round(phi_vc_tn, 2),
        "Cumple": "Sí" if cumple else "No",
    }


def _evaluar_cortante(
    nombre: str, fc: float, fy: float, b: float, h: float, rec: float, vu_tn: float
) -> tuple[dict, dict]:
    """
    Diseño por cortante E-060. Vu en Tn (se convierte a kg).
    Retorna (resultado resumido, detalle para salida paso a paso).
    """
    vu_kg = vu_tn * 1000
    if fc <= 0 or fy <= 0 or b <= 0 or h <= 0 or rec <= 0 or vu_tn < 0:
        raise InvalidInput("Parámetros inválidos: verifique unidades y signos")
    if rec >= h:
        raise InvalidInput("El recubrimiento debe ser menor que la altura total")

    d = h - rec
    sqrt_fc = fc**0.5
    vc_kg = vc(fc, b, d)
    vs_max_kg = vs_max(fc, b, d)
    vn_max_kg = vn_max(vc_kg, vs_max_kg)
    umbral_sin_refuerzo = (vc_kg / 2) * PHI_CORTANTE
    umbral_maximo = PHI_CORTANTE * vn_max_kg

    if vu_kg <= umbral_sin_refuerzo:
        caso = "sin_refuerzo"
        av_s_req = 0.0
        vs_kg = 0.0
        error_msg = None
    elif vu_kg <= umbral_maximo:
        caso = "con_refuerzo"
        vs_kg = max(0.0, vs_requerido(vu_kg, vc_kg))
        av_s_req = av_s_requerido(vs_kg, fy, d)
        error_msg = None
    else:
        caso = "insuficiente"
        vs_kg = vs_requerido(vu_kg, vc_kg)
        av_s_req = None
        error_msg = "Vu > phi*Vn_max: aumentar peralte o fc"

    s_max_base_cm = s_max_base(d)
    vs_umbral_s = 1.1 * sqrt_fc * b * d
    s_max_cm = s_max_reducido(s_max_base_cm, vs_kg, fc, b, d)
    av_s_min1 = 0.2 * sqrt_fc * b / fy
    av_s_min2 = 3.5 * b / fy
    av_s_min_ratio = max(av_s_min1, av_s_min2)

    if av_s_req is not None and av_s_req > 0:
        as_s_req = max(av_s_req, av_s_min_ratio)
    elif av_s_req is not None:
        as_s_req = av_s_min_ratio
    else:
        as_s_req = None

    resultado = {
        "nombre": nombre,
        "Vu": round(vu_tn, 2),
        "Vc": round(vc_kg / 1000, 2),
        "phi_Vc_2": round(umbral_sin_refuerzo / 1000, 2),
        "Vs_max": round(vs_max_kg / 1000, 2),
        "phi_Vn_max": round(umbral_maximo / 1000, 2),
        "Vs": round(vs_kg / 1000, 2),
        "As/s req.": round(as_s_req, 4) if as_s_req is not None else None,
        "s_max": round(s_max_cm, 2),
    }
    if error_msg:
        resultado["Error"] = error_msg

    detalle = {
        "d": d,
        "sqrt_fc": sqrt_fc,
        "vu_kg": vu_kg,
        "vc_kg": vc_kg,
        "vs_max_kg": vs_max_kg,
        "vn_max_kg": vn_max_kg,
        "umbral_sin_refuerzo_kg": umbral_sin_refuerzo,
        "umbral_maximo_kg": umbral_maximo,
        "vs_kg": vs_kg,
        "av_s_calc": av_s_req,
        "av_s_min1": av_s_min1,
        "av_s_min2": av_s_min2,
        "av_s_min": av_s_min_ratio,
        "as_s_req": as_s_req,
        "s_max_base": s_max_base_cm,
        "s_max": s_max_cm,
        "vs_umbral_s": vs_umbral_s,
        "caso": caso,
        "error_msg": error_msg,
    }
    return resultado, detalle


def _calcular_cortante(
    nombre: str, fc: float, fy: float, b: float, h: float, rec: float, vu_tn: float
) -> dict:
    """Diseño por cortante E-060 (solo resultado resumido)."""
    resultado, _ = _evaluar_cortante(nombre, fc, fy, b, h, rec, vu_tn)
    return resultado


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
        if "viga" in fila and fila.get("viga") != "":
            res["viga"] = fila.get("viga")
        resultados.append(res)

    return {"resultados": resultados}


REC_CORTANTE_DEFAULT_CM = 4.0


@register("cortante", "calc")
def cortante_calc(data: dict) -> dict:
    """
    Diseño a cortante directo (vigas y columnas, mismo procedimiento E-060).
    Data: Vu (Tn), b, h, fc, fy (kg/cm²), rec (cm, opcional, default 4).
    """
    fc = to_float(data.get("fc"))
    fy = to_float(data.get("fy"))
    b = to_float(data.get("b"))
    h = to_float(data.get("h"))
    rec = to_float(data.get("rec"), default=REC_CORTANTE_DEFAULT_CM)
    vu = to_float(data.get("Vu"), default=0.0)
    nombre = (data.get("nombre") or "Sección").strip() or "Sección"
    res, detalle = _evaluar_cortante(nombre, fc, fy, b, h, rec, vu)
    res["d"] = round(h - rec, 2)
    return {
        "entrada": {
            "nombre": nombre, "Vu": vu, "b": b, "h": h, "fc": fc, "fy": fy, "rec": rec, "d": res["d"],
        },
        "resultado": res,
        "detalle": detalle,
    }


@register("cortante", "losa")
def cortante_losa(data: dict) -> dict:
    """
    Cortante en losa: sin estribos; solo Vu vs phi*Vc.
    Data: {losas: [{fc, b, h, rec, nombre, Vu}, ...]}.
    """
    if "losas" not in data:
        raise InvalidInput("Data debe tener 'losas' con lista de filas (fc, b, h, rec, nombre, Vu)")
    resultados = []
    for i, fila in enumerate(data["losas"]):
        nombre = fila.get("nombre") or f"Losa {i + 1}"
        fc = to_float(fila.get("fc"))
        b = to_float(fila.get("b"))
        h = to_float(fila.get("h"))
        rec = to_float(fila.get("rec"))
        vu = to_float(fila.get("Vu"), default=0.0)
        res = _calcular_cortante_losa(nombre, fc, b, h, rec, vu)
        if "losa" in fila and fila.get("losa") != "":
            res["losa"] = fila.get("losa")
        resultados.append(res)
    return {"resultados": resultados}
