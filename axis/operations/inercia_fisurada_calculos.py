"""
Cálculo de inercia de sección fisurada (sección transformada) e inercia efectiva.
Unidades: cm, cm², cm⁴. Referencia: E.060, inercia fisurada.
"""

from __future__ import annotations

import math

from axis.core.exceptions import InvalidInput

ES_ACERO = 2_000_000  # kg/cm²
CM4_A_M4 = 1e-8


def ec_e060(fc: float) -> float:
    """Módulo de elasticidad del concreto E.060: Ec = 15000*sqrt(fc) kg/cm²."""
    if fc <= 0:
        raise InvalidInput("fc debe ser positivo.")
    return 15000.0 * math.sqrt(fc)


def n_from_fc(fc: float) -> float:
    """Relación modular n = Es/Ec con Es=2e6 kg/cm²."""
    return ES_ACERO / ec_e060(fc)


def ig_bruta_cm4(b: float, h: float) -> float:
    """Inercia de sección bruta rectangular: Ig = b*h³/12 (cm⁴)."""
    return b * (h ** 3) / 12.0


def mcr_tnm(fc: float, b: float, h: float) -> float:
    """Mcr en Tn·m: fr=2*sqrt(fc), y=h/2, Mcr=fr*Ig/y; Ig=b*h³/12 (E.060 Art. 9.6.2.3)."""
    fr = 2.0 * math.sqrt(fc)
    ig = ig_bruta_cm4(b, h)
    y = h / 2.0
    mcr_kgcm = fr * ig / y
    return mcr_kgcm / 100000.0  # Tn·m


def modulo_relativo_elasticidad(es: float, ec: float) -> float:
    """n = Es / Ec."""
    if ec == 0:
        raise InvalidInput("Ec no puede ser cero.")
    return es / ec


def eje_neutro_c(
    b: float,
    as_traccion: float,
    as_compresion: float,
    d: float,
    d_prima: float,
    n: float,
) -> float:
    """
    Eje neutro c (bloque comprimido) de la sección fisurada.
    b·c·(c/2) + (n-1)·As'·(c-d') = n·As·(d-c). Se toma la raíz con 0 < c < d.
    """
    a_coef = b / 2.0
    b_coef = (n - 1.0) * as_compresion + n * as_traccion
    c_coef = -(n - 1.0) * as_compresion * d_prima - n * as_traccion * d
    disc = b_coef**2 - 4 * a_coef * c_coef
    if disc < 0:
        raise InvalidInput(
            "La ecuación para c no tiene solución real (discriminante < 0). Revise los datos."
        )
    raiz = math.sqrt(disc)
    c1 = (-b_coef + raiz) / (2 * a_coef)
    c2 = (-b_coef - raiz) / (2 * a_coef)
    candidatas = [c for c in (c1, c2) if 0 < c < d]
    if not candidatas:
        candidatas = [c for c in (c1, c2) if c > 0]
    if not candidatas:
        raise InvalidInput(f"No se encontró raíz positiva para c. Raíces: c1={c1}, c2={c2}.")
    return max(candidatas)


def inercia_seccion_fisurada(
    b: float,
    as_traccion: float,
    as_compresion: float,
    d: float,
    d_prima: float,
    n: float,
    duplicar_acero_compresion: bool = False,
) -> float:
    """
    Inercia de la sección fisurada Icr (cm⁴).
    as_traccion = As (acero en tracción); as_compresion = As' (acero en compresión).
    En apoyos: tracción arriba (As=arriba, As'=abajo). En centro: tracción abajo (As=abajo, As'=arriba).
    Icr = b·c³/3 + n·As·(d-c)² + (n-1)·As'·(c-d')²; si duplicar: coef. As' = (2n-1).
    """
    c = eje_neutro_c(b, as_traccion, as_compresion, d, d_prima, n)
    coef = (2.0 * n - 1.0) if duplicar_acero_compresion else (n - 1.0)
    return (
        b * c**3 / 3.0
        + n * as_traccion * (d - c) ** 2
        + coef * as_compresion * (c - d_prima) ** 2
    )


def inercia_efectiva(ma: float, mcr: float, ig: float, icr: float) -> float:
    """
    Inercia efectiva E.060: si Ma <= Mcr (no fisurada) Ie = Ig;
    si Ma > Mcr: Ie = (Mcr/Ma)³·Ig + [1 - (Mcr/Ma)³]·Icr (Icr <= Ie <= Ig).
    """
    if ma == 0:
        raise InvalidInput("Ma no puede ser cero.")
    if mcr <= 0:
        raise InvalidInput("Mcr debe ser positivo.")
    if ma <= mcr:
        return ig  # Sección no fisurada
    f = (mcr / ma) ** 3
    return f * ig + (1.0 - f) * icr


# Casos E.060 para Ie ponderado (deflexiones)
CASOS_IE = {
    "continuo_ambos": {"secciones": ["apoyo1", "apoyo2", "centro"], "formula": "(Ie1+Ie2+2*Ie3)/4"},
    "continuo_uno": {"secciones": ["apoyo_continuo", "centro"], "formula": "(Ie2+2*Ie3)/3"},
    "simplemente_apoyado": {"secciones": ["centro"], "formula": "Ie3"},
    "voladizo": {"secciones": ["apoyo"], "formula": "Ie1"},
}


def ie_promedio(caso: str, valores: dict[str, float]) -> float:
    """
    Ie ponderado según E.060. valores: dict etiqueta_seccion -> Ie (m4).
    continuo_ambos: (Ie1+Ie2+2*Ie3)/4; continuo_uno: (Ie2+2*Ie3)/3;
    simplemente_apoyado: Ie centro; voladizo: Ie apoyo.
    """
    if caso not in CASOS_IE:
        raise InvalidInput(f"Caso no válido: {caso}. Use: {list(CASOS_IE)}")
    req = CASOS_IE[caso]["secciones"]
    for s in req:
        if s not in valores:
            raise InvalidInput(f"Falta sección '{s}' para caso {caso}.")
    if caso == "continuo_ambos":
        return (valores["apoyo1"] + valores["apoyo2"] + 2 * valores["centro"]) / 4.0
    if caso == "continuo_uno":
        return (valores["apoyo_continuo"] + 2 * valores["centro"]) / 3.0
    if caso == "simplemente_apoyado":
        return valores["centro"]
    return valores["apoyo"]
