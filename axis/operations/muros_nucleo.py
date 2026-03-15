"""Predimensionamiento de acero en núcleos de muros de concreto armado.

Implementa las fórmulas del Excel de predimensionamiento:

- Clasificación del muro con la esbeltez H/L.
- H = altura desde el nivel actual hasta la punta del edificio (decrece en pisos superiores).
- Brazo interno z según H/L.
- As requerida por nivel: As = Mu / (φ · fy · z).

Convenciones de unidades:
- Mu en Tn·m
- fy en kg/cm²
- z en m
- As resultante en cm² (por núcleo).
"""

from __future__ import annotations

from typing import Iterable

from axis.core.registry import register
from axis.core.exceptions import InvalidInput
from axis.core.utils import to_float


def _clasificar_muro_y_z(h_total: float, l_muro: float) -> tuple[str, float]:
    """
    Clasifica el tipo de muro (esbelto / no esbelto) y calcula z.

    Fórmulas según imágenes de usuario:
      - Si H/L > 1.00  -> z = 0.90·L
      - Si 0.50 ≤ H/L ≤ 1.00 -> z = 0.40·L·(1 + H/L)
      - Si H/L < 0.50  -> z = 1.20·H
    """
    if l_muro <= 0 or h_total <= 0:
        raise InvalidInput("H_total y L deben ser positivos para calcular H/L y z.")

    relacion = h_total / l_muro

    if relacion > 1.0:
        z = 0.90 * l_muro
        tipo = "Muro Esbelto"
    elif relacion >= 0.50:
        z = 0.40 * l_muro * (1.0 + relacion)
        tipo = "Muro No Esbelto"
    else:
        z = 1.20 * h_total
        tipo = "Muro No Esbelto"

    return tipo, z


def _as_requerida(mu_ton_m: float, fy: float, phi: float, z_m: float) -> float:
    """
    Calcula As (cm²) a partir de Mu (Tn·m), fy (kg/cm²), φ y z (m).

    Partiendo de Mu en kg·cm:
      Mu[kg·cm] = Mu[Tn·m] · 1000 kg/Tn · 100 cm/m
    y z en cm:
      z[cm] = z[m] · 100

    Entonces:
      As[cm²] = Mu[kg·cm] / (φ · fy · z[cm])
               = Mu[Tn·m] · 1000 / (φ · fy · z[m])
    """
    if phi <= 0 or fy <= 0 or z_m <= 0:
        raise InvalidInput("φ, fy y z deben ser positivos para calcular As.")
    if mu_ton_m <= 0:
        raise InvalidInput("Mu debe ser positivo (Tn·m).")

    return mu_ton_m * 1000.0 / (phi * fy * z_m)


@register("predimension", "muro_nucleo")
def predimension_muro_nucleo(data: dict) -> dict:
    """
    Predimensionamiento de acero en núcleos de muros de concreto armado.

    Entradas (data):
      - L: longitud del núcleo del muro (m)
      - fy: esfuerzo de fluencia del acero (kg/cm²)
      - phi: factor de reducción por flexión (φ). Opcional, por defecto 0.90.
      - H_inicial: altura acumulada previa (m). Opcional, por defecto 0.0.
      - niveles: iterable de dicts con:
          - nivel: etiqueta del nivel (ej. 'Piso 01')
          - hm: altura de piso a piso para ese nivel (m)
          - Mu: momento último en el núcleo para ese nivel (Tn·m)

    El algoritmo usa H_total = altura desde la base del nivel actual hasta la
    punta del edificio (decrece hacia pisos superiores). Con eso calcula H/L,
    z y As, y clasifica el muro como esbelto o no esbelto.

    Retorna:
      {
        "L": float,
        "fy": float,
        "phi": float,
        "resultados": [
          {
            "nivel": str,
            "hm": float,
            "H_total": float,
            "H_L": float,
            "tipo_muro": str,
            "tipo_falla": "Por Flexión",
            "Mu": float,
            "z": float,
            "As": float,
          },
          ...
        ]
      }
    """
    if "L" not in data or "fy" not in data or "niveles" not in data:
        raise InvalidInput("Data debe incluir 'L', 'fy' y 'niveles'.")

    l_muro = to_float(data.get("L"))
    fy = to_float(data.get("fy"))
    phi = to_float(data.get("phi"), default=0.90)

    if l_muro <= 0 or fy <= 0 or phi <= 0:
        raise InvalidInput("L, fy y phi deben ser positivos.")

    niveles: Iterable[dict] = data.get("niveles") or []
    niveles = list(niveles)
    if not niveles:
        raise InvalidInput("Debe proporcionarse al menos un nivel en 'niveles'.")

    h_inicial = to_float(data.get("H_inicial"), default=0.0)
    # Altura total del edificio (desde la base del primer nivel hasta la punta)
    altura_total_edificio = h_inicial + sum(to_float(f.get("hm")) for f in niveles)

    resultados: list[dict] = []
    # Altura desde la base hasta el inicio del nivel actual (va creciendo)
    h_desde_base = h_inicial

    for i, fila in enumerate(niveles):
        nombre_nivel = str(fila.get("nivel") or f"Nivel {i + 1}")
        hm = to_float(fila.get("hm"))
        mu = to_float(fila.get("Mu"))

        if hm <= 0:
            raise InvalidInput(f"hm debe ser > 0 (nivel '{nombre_nivel}').")
        if mu <= 0:
            raise InvalidInput(f"Mu debe ser > 0 (nivel '{nombre_nivel}').")

        # H = altura desde el nivel actual hasta la punta del edificio (decrece hacia arriba)
        h_total_nivel = altura_total_edificio - h_desde_base
        tipo_muro, z = _clasificar_muro_y_z(h_total_nivel, l_muro)
        relacion_hl = h_total_nivel / l_muro
        as_cm2 = _as_requerida(mu, fy, phi, z)

        resultados.append(
            {
                "nivel": nombre_nivel,
                "hm": round(hm, 2),
                "H_total": round(h_total_nivel, 2),
                "H_L": round(relacion_hl, 3),
                "tipo_muro": tipo_muro,
                "tipo_falla": "Por Flexión",
                "Mu": round(mu, 2),
                "z": round(z, 2),
                "As": round(as_cm2, 2),
            }
        )
        h_desde_base += hm

    return {
        "L": l_muro,
        "fy": fy,
        "phi": phi,
        "resultados": resultados,
    }

