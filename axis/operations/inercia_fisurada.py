"""Operación: cálculo de inercia fisurada e inercia efectiva."""

from __future__ import annotations

from axis.core.registry import register
from axis.core.exceptions import InvalidInput
from axis.core.utils import to_float
from axis.operations.inercia_fisurada_calculos import (
    modulo_relativo_elasticidad,
    eje_neutro_c,
    inercia_seccion_fisurada,
    inercia_efectiva,
)

CM4_A_M4 = 1e-8  # 1 cm⁴ = 1e-8 m⁴


@register("inercia", "fisurada")
def inercia_fisurada(data: dict) -> dict:
    """
    Inercia de sección fisurada Icr e inercia efectiva Ie (opcional).
    Siempre se duplica el aporte del acero en compresión (2n-1).
    Data: b, d, d_prima, as_traccion, as_compresion, n (o es, ec). Opcional: ma, mcr, ig → Ie.
    """
    b = to_float(data.get("b"))
    d = to_float(data.get("d"))
    d_prima = to_float(data.get("d_prima"))
    as_t = to_float(data.get("as_traccion"))
    as_c = to_float(data.get("as_compresion"), default=0.0)
    if "n" in data and data.get("n") not in (None, ""):
        n = to_float(data.get("n"))
    elif "es" in data and "ec" in data:
        n = modulo_relativo_elasticidad(to_float(data["es"]), to_float(data["ec"]))
    else:
        raise InvalidInput("Indique 'n' o bien 'es' y 'ec'.")

    c = eje_neutro_c(b, as_t, as_c, d, d_prima, n)
    icr_cm4 = inercia_seccion_fisurada(b, as_t, as_c, d, d_prima, n, duplicar_acero_compresion=True)
    icr_m4 = icr_cm4 * CM4_A_M4

    out = {
        "c": round(c, 4),
        "Icr_cm4": round(icr_cm4, 4),
        "Icr_m4": round(icr_m4, 6),
        "n": round(n, 4),
    }
    ma = data.get("ma")
    mcr = data.get("mcr")
    ig = data.get("ig")
    if ma is not None and mcr is not None and ig is not None:
        ma_f = to_float(ma)
        mcr_f = to_float(mcr)
        ig_f = to_float(ig)
        ie = inercia_efectiva(ma_f, mcr_f, ig_f, icr_m4)
        out["Ie_m4"] = round(ie, 6)
        out["Ma"] = ma_f
        out["Mcr"] = mcr_f
    return out
