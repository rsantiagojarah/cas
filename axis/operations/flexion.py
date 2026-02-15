"""Operación de diseño por flexión para vigas de concreto reforzado."""

from __future__ import annotations

import math

from axis.core.registry import register
from axis.core.exceptions import InvalidInput


def _calcular_flexion(
    nombre: str, fc: float, fy: float, b: float, h: float, rec: float, mu: float
) -> dict:
    """
    Calcula el área de acero requerida para una viga en flexión.
    Mu en Tn-m. Retorna dict con As, As_prima, tipo_seccion, Mcr, Asmin, cumple_Mcr.
    """
    mu_kgcm = mu * 1000 * 100
    if fc <= 0 or fy <= 0 or b <= 0 or h <= 0 or rec <= 0 or mu <= 0:
        raise InvalidInput("Todos los parámetros deben ser positivos")
    if rec >= h:
        raise InvalidInput("El recubrimiento debe ser menor que la altura total")

    d = h - rec
    d_prima = rec
    cb = (6000 * d) / (6000 + fy)
    b1 = 0.85 if fc <= 280 else max(0.65, 0.85 - (0.05 * (fc - 280)) / 70)
    ab = cb * b1
    amax = 0.75 * ab

    discriminante = d**2 - (2 * mu_kgcm) / (0.85 * fc * b)
    if discriminante < 0:
        raise InvalidInput("El momento es demasiado grande para la sección dada")
    a = d - math.sqrt(discriminante)

    es = 2000000
    if a <= amax:
        as_req = mu_kgcm / (0.9 * fy * (d - a / 2))
        as_prima = 0.0
        tipo = "VSR"
    else:
        c = 0.85 * fc * b * amax
        muc = 0.9 * c * (d - amax / 2)
        mus = mu_kgcm - muc
        cmax = amax / b1
        fs = es * 0.003 * ((cmax - d_prima) / cmax)
        fs = fy if fs <= 0 else fs
        as_prima = mus / (0.9 * (fs - 0.85 * fc) * (d - d_prima))
        as1 = muc / (0.9 * fy * (d - amax / 2))
        as2 = mus / (0.9 * fy * (d - d_prima))
        as_req = as1 + as2
        tipo = "VDR"

    ig = (b * h**3) / 12
    yt = h / 2
    fr = 2 * math.sqrt(fc)
    mcr_kgcm = (fr * ig) / yt
    mcr_tnm = mcr_kgcm / (1000 * 100)
    asmin = 0.7 * (fc**0.5) * b * d / fy
    as_final = max(as_req, asmin)

    if tipo == "VSR":
        a_final = (as_final * fy) / (0.85 * fc * b)
        mn = as_final * fy * (d - a_final / 2)
    else:
        tol = 1e-3
        as_prima_iter = as_prima
        for _ in range(100):
            a_final = (as_req * fy - as_prima_iter * fy) / (0.85 * fc * b)
            a_final = min(a_final, d)
            mn = as_req * fy * (d - a_final / 2) + as_prima_iter * fy * (d - d_prima)
            fs = es * 0.003 * ((amax / b1 - d_prima) / (amax / b1))
            fs = fy if fs <= 0 else fs
            denom = 0.9 * (fs - 0.85 * fc) * (d - d_prima)
            as_prima_new = mus / denom if denom != 0 else 0
            if abs(as_prima_new - as_prima_iter) < tol:
                break
            as_prima_iter = as_prima_new
        as_prima = as_prima_iter

    phi = 0.9
    cumple_mcr = phi * mn >= mcr_kgcm
    if not cumple_mcr:
        as_req_mcr = mcr_kgcm / (phi * fy * (d - h / 4))
        as_final = max(as_final, as_req_mcr)

    return {
        "nombre": nombre,
        "As": round(as_final, 2),
        "As'": round(as_prima, 2),
        "Tipo": tipo,
        "Mcr": round(mcr_tnm, 2),
        "Asmin": round(asmin, 2),
        "OK": cumple_mcr,
    }


@register("flexion", "viga")
def flexion_viga(data: dict) -> dict:
    """
    Diseño por flexión de viga de concreto reforzado.
    Data: {fc, fy, b, h, rec, Mu} o {vigas: [{fc, fy, b, h, rec, Mu}, ...]}
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


def _to_float(val) -> float:
    """Convierte a float, manejando strings con coma."""
    if val is None:
        raise InvalidInput("Parámetro faltante")
    if isinstance(val, (int, float)):
        return float(val)
    s = str(val).replace(",", ".")
    return float(s)
