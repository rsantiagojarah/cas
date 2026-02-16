"""Operación de diseño por flexión para vigas (E-060, criterio cuantía máxima)."""

from __future__ import annotations

from axis.core.registry import register
from axis.core.exceptions import InvalidInput
from axis.operations.flexion_calculos import (
    beta1,
    profundidad_bloque_compresion,
    a_max_balanceada,
    acero_vsr,
    acero_vdr,
    asmin,
    asmax_vsr,
    asmax_vdr,
    mcr,
    phi_mn_vsr,
    phi_mn_vdr,
)


def _calcular_flexion(
    nombre: str, fc: float, fy: float, b: float, h: float, rec: float, mu: float
) -> dict:
    """
    Diseño por flexión según E-060 (criterio cuantía máxima). Mu en Tn-m.
    Retorna As, As', Tipo (VSR/VDR), Mcr, Asmin, Asmax, cumple_Asmin, cumple_Asmax, OK (1.2*Mcr).
    """
    if fc <= 0 or fy <= 0 or b <= 0 or h <= 0 or rec <= 0 or mu <= 0:
        raise InvalidInput("Todos los parámetros deben ser positivos")
    if rec >= h:
        raise InvalidInput("El recubrimiento debe ser menor que la altura total")

    d = h - rec
    d_prima = rec
    mu_kgcm = mu * 1000 * 100
    b1 = beta1(fc)
    a_max = a_max_balanceada(d, fy, fc)

    a = profundidad_bloque_compresion(d, mu_kgcm, fc, b)
    tipo = "VSR" if a <= a_max else "VDR"

    if tipo == "VSR":
        as_req, as_prima = acero_vsr(mu_kgcm, d, a, fy)
        fs_prima = 0.0
    else:
        as_req, as_prima, fs_prima = acero_vdr(
            mu_kgcm, fc, fy, b, d, d_prima, a_max, b1
        )

    asmin_val = asmin(fc, b, d, fy)
    as_final = max(as_req, asmin_val)
    cumple_asmin = as_req >= asmin_val

    if tipo == "VSR":
        asmax = asmax_vsr(fc, a_max, fy, b)
    else:
        asmax = asmax_vdr(fc, a_max, b, fy, as_prima, fs_prima)
    cumple_asmax = as_final <= asmax

    mcr_kgcm = mcr(fc, b, h)
    umbral_mcr = 1.2 * mcr_kgcm

    if tipo == "VSR":
        phi_mn = phi_mn_vsr(as_final, fy, fc, b, d)
    else:
        phi_mn = phi_mn_vdr(as_final, as_prima, fc, fy, b, d, d_prima, b1)
    cumple_mcr = phi_mn >= umbral_mcr

    return {
        "nombre": nombre,
        "As": round(as_final, 2),
        "As'": round(as_prima, 2),
        "Tipo": tipo,
        "Mcr": round(mcr_kgcm / (1000 * 100), 2),
        "Asmin": round(asmin_val, 2),
        "Asmax": round(asmax, 2),
        "cumple_Asmin": cumple_asmin,
        "cumple_Asmax": cumple_asmax,
        "OK": cumple_mcr,
    }


def _to_float(val) -> float:
    """Convierte a float, manejando strings con coma."""
    if val is None:
        raise InvalidInput("Parámetro faltante")
    if isinstance(val, (int, float)):
        return float(val)
    return float(str(val).replace(",", "."))


@register("flexion", "viga")
def flexion_viga(data: dict) -> dict:
    """
    Diseño por flexión de viga (E-060, criterio cuantía máxima).
    Data: {fc, fy, b, h, rec, Mu} o {vigas: [{...}, ...]}.
    """
    if "vigas" in data:
        filas = data["vigas"]
    elif all(k in data for k in ("fc", "fy", "b", "h", "rec", "Mu")):
        filas = [data]
    else:
        raise InvalidInput(
            "Data debe tener fc, fy, b, h, rec, Mu o vigas con lista de vigas"
        )

    resultados = []
    for i, fila in enumerate(filas):
        nombre = fila.get("nombre") or f"Viga {i + 1}"
        fc = _to_float(fila.get("fc"))
        fy = _to_float(fila.get("fy"))
        b = _to_float(fila.get("b"))
        h = _to_float(fila.get("h"))
        rec = _to_float(fila.get("rec"))
        mu = _to_float(fila.get("Mu"))
        res = _calcular_flexion(nombre, fc, fy, b, h, rec, mu)
        resultados.append(res)

    return {"resultados": resultados}
