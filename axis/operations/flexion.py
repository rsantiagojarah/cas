"""Operación de diseño por flexión para vigas (E-060, criterio cuantía máxima)."""

from __future__ import annotations

from axis.core.registry import register
from axis.core.exceptions import InvalidInput
from axis.core.utils import to_float
from axis.operations.flexion_calculos import (
    beta1,
    profundidad_bloque_compresion,
    a_max_balanceada,
    acero_vsr,
    acero_vdr,
    asmin,
    asmax_vsr,
    asmax_vdr,
)


def _calcular_flexion(
    nombre: str, fc: float, fy: float, b: float, h: float, rec: float, mu: float
) -> dict:
    """
    Diseño por flexión E-060 (criterio cuantía máxima). Mu en Tn-m.
    Retorna: nombre, Tipo, As, As', Asmin, Asmax, As_colocar, As_prima_colocar, Estado.
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
    if tipo == "VSR":
        asmax = asmax_vsr(fc, a_max, fy, b)
    else:
        asmax = asmax_vdr(fc, a_max, b, fy, as_prima, fs_prima)

    as_colocar = max(as_req, asmin_val)
    as_prima_colocar = as_prima

    return {
        "nombre": nombre,
        "Mu": round(mu, 2),
        "As": round(as_req, 2),
        "As'": round(as_prima, 2),
        "Asmin": round(asmin_val, 2),
        "Asmax": round(asmax, 2),
        "As_colocar": round(as_colocar, 2),
        "As_prima_colocar": round(as_prima_colocar, 2),
    }


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
        fc = to_float(fila.get("fc"))
        fy = to_float(fila.get("fy"))
        b = to_float(fila.get("b"))
        h = to_float(fila.get("h"))
        rec = to_float(fila.get("rec"))
        mu = to_float(fila.get("Mu"))
        res = _calcular_flexion(nombre, fc, fy, b, h, rec, mu)
        resultados.append(res)

    return {"resultados": resultados}
