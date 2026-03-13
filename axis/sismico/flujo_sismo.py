"""
Orquestación del análisis sísmico E.030 usando una DataSource.
Centraliza la obtención de datos y escritura de CSVs (DRY, testeable).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from axis.data.source import DataSource
from axis.sismico.etapa2_edificio import coeficiente_reduccion_r
from axis.sismico.etapa1_peligro import tabla_c_vs_t
from axis.sismico.tables_e030 import obtener_z, obtener_parametros_sitio, obtener_u
from axis.core.database import write_results_csv


def ejecutar_pasos_con_fuente(
    source: DataSource,
    sentido: str,
    zona: int,
    categoria: str,
    perfil: str,
    r0: float,
    ia: float,
    ip: float,
    material: str,
    log: bool = False,
) -> dict[str, Any]:
    """
    Obtiene de la fuente todos los datos necesarios para los pasos E.030.
    Retorna un dict con: periodo, tbl_per, tbl_modal, cumple_masa, tbl_masa,
    df_peso, tbl_est, tbl_din, cort, datos_cort, cl, dr, r, k.
    """
    r = coeficiente_reduccion_r(r0, ia, ip)
    # Según E.030 Art. 31: si Ia o Ip son distintos de 1,
    # la edificación se considera irregular para la verificación
    # de desplazamientos laterales.
    irregular = (ia != 1.0) or (ip != 1.0)
    factor_drift = 0.85 if irregular else 0.75
    k = "x" if sentido == "X" else "y"

    res_per = source.get_periodo_fundamental(log=log)
    periodo = (res_per["periodo_x"] if sentido == "X" else res_per["periodo_y"]) if res_per else 0.0
    tbl_per = res_per.get("tabla_case_period") if res_per else None
    tbl_modal = res_per.get("tabla_modal_periods") if res_per else None

    res_masa = source.get_masa_participante(log=log)
    cumple_masa = (
        (res_masa["cumple_90_x"] if sentido == "X" else res_masa["cumple_90_y"])
        if res_masa else False
    )
    tbl_masa = res_masa.get("tabla") if res_masa else None

    df_peso = source.get_peso_edificio(log=log)

    est = source.get_story_forces_estatico(log=log)
    din = source.get_story_forces_dinamico(log=log)
    caso_est = "SISMOX" if sentido == "X" else "SISMOY"
    caso_din = "SPX" if sentido == "X" else "SPY"
    tbl_est = est.get(caso_est) if est else None
    tbl_din = din.get(caso_din) if din else None

    cort = source.get_cortante_minima(ia=ia, ip=ip, log=log)
    datos_cort = cort.get(k) if cort else None

    cl = source.get_clasificacion_sistema(log=log)
    dr = source.get_distorsion(r, material, factor_drift=factor_drift, log=log)

    return {
        "periodo": periodo,
        "tbl_per": tbl_per,
        "tbl_modal": tbl_modal,
        "cumple_masa": cumple_masa,
        "tbl_masa": tbl_masa,
        "df_peso": df_peso,
        "tbl_est": tbl_est,
        "tbl_din": tbl_din,
        "cort": cort,
        "datos_cort": datos_cort,
        "cl": cl,
        "dr": dr,
        "r": r,
        "k": k,
        "factor_drift": factor_drift,
    }


def ejecutar_analisis_sismico(
    source: DataSource,
    sentido: str,
    zona: int,
    categoria: str,
    perfil: str,
    r0: float,
    ia: float,
    ip: float,
    material: str,
    path: Path,
    log: bool = False,
) -> dict[str, Any]:
    """
    Orquesta todo el análisis E.030: parámetros de sitio, escritura de CSVs
    y obtención de datos desde la fuente. Retorna un único dict con todo
    lo necesario para presentación (CLI) o reporte PDF.
    """
    z = obtener_z(zona)
    params = obtener_parametros_sitio(perfil, zona)
    if params.get("tp") is None:
        from axis.core.exceptions import InvalidInput
        raise InvalidInput("Perfil S4 requiere estudio especifico.")
    tp, tl = params["tp"], params["tl"]
    s_val = params["s"]
    u = obtener_u(categoria)
    r = coeficiente_reduccion_r(r0, ia, ip)
    datos_ct = tabla_c_vs_t(tp, tl)
    g = 9.80665
    filas_ct = [{"T": round(t, 4), "C": round(c, 4)} for t, c in datos_ct]
    filas_espectro = [
        {"T": round(t, 4), "C": round(c, 4), "Sa": round((z * u * c * s_val / r) * g, 4)}
        for t, c in datos_ct
    ]
    write_results_csv(path, "sismo_peligro_espectro.csv", filas_ct)
    write_results_csv(path, "sismo_edificio.csv", [
        {"U": u, "R0": r0, "Ia": ia, "Ip": ip, "R": round(r, 4)}
    ])
    datos = ejecutar_pasos_con_fuente(
        source, sentido, zona, categoria, perfil, r0, ia, ip, material, log=log
    )
    return {
        **datos,
        "z": z,
        "u": u,
        "s_val": s_val,
        "tp": tp,
        "tl": tl,
        "filas_ct": filas_ct,
        "filas_espectro": filas_espectro,
        "path": path,
    }
