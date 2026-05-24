"""
Verificacion de irregularidades E.030 2026 (Tablas 11 y 12).
Reutiliza la logica base y aplica criterios actualizados donde difieren de la version anterior.
"""

from __future__ import annotations

from axis.sismico.irregularidades_verificacion import (
    calcular_relativos_desde_absolutos,
    verificar_discontinuidad_extrema,
    verificar_discontinuidad_extrema_todos,
    verificar_discontinuidad_por_desalineamiento,
    verificar_discontinuidad_por_longitud_desplazamiento,
    verificar_discontinuidad_sistemas,
    verificar_discontinuidad_sistemas_todos,
    verificar_discontinuidad_unificado,
    verificar_discontinuidad_unificado_desalineamiento,
    verificar_esquinas_entrantes,
    verificar_esquinas_entrantes_todos,
    verificar_extrema_resistencia,
    verificar_extrema_resistencia_todos,
    verificar_extrema_rigidez,
    verificar_extrema_rigidez_todos,
    verificar_geometrica_vertical,
    verificar_geometrica_vertical_todos,
    verificar_masa,
    verificar_masa_todos,
    verificar_piso_blando,
    verificar_piso_blando_todos,
    verificar_piso_debil,
    verificar_piso_debil_todos,
    verificar_resistencia_unificado,
    verificar_rigidez_unificado,
    verificar_sistemas_no_paralelos,
    verificar_sistemas_no_paralelos_todos,
    verificar_torsional,
    verificar_torsional_todos,
)


def verificar_diafragma(
    area_abertura: float,
    area_bruta: float,
    seccion_neta: float | None = None,
    seccion_total: float | None = None,
) -> dict:
    """
    Tabla 12 (2026) - Discontinuidad del diafragma.
    Criterio 1: area_abertura > 50% area_bruta.
    Criterio 2 (opcional): seccion_neta < 50% del area bruta equivalente (seccion_total).
    """
    ab, br = float(area_abertura), float(area_bruta)
    if br <= 0:
        return {"existe": False, "pct_abertura": None, "pct_seccion": None}
    pct_abertura = (ab / br) * 100
    crit1 = pct_abertura > 50
    crit2 = False
    pct_seccion = None
    if seccion_neta is not None and seccion_total is not None:
        sn, st = float(seccion_neta), float(seccion_total)
        if st > 0:
            pct_seccion = (sn / st) * 100
            crit2 = pct_seccion < 50
    existe = crit1 or crit2
    return {
        "existe": existe,
        "pct_abertura": round(pct_abertura, 2),
        "pct_seccion": round(pct_seccion, 2) if pct_seccion is not None else None,
    }


def verificar_diafragma_todos(
    datos: list[tuple[float, float, float | None, float | None]],
) -> list[dict]:
    """Verifica diafragma por piso. datos: [(ab,br,sn?,st?), ...]."""
    resultados: list[dict] = []
    for i, row in enumerate(datos):
        ab, br = row[0], row[1]
        sn = row[2] if len(row) > 2 else None
        st = row[3] if len(row) > 3 else None
        r = verificar_diafragma(ab, br, sn, st)
        resultados.append({"piso": i + 1, "pct_abertura": r["pct_abertura"], **r})
    return resultados
