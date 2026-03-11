"""
Genera la salida por pasos del análisis sísmico E.030.
Cada función retorna el texto/tablas para un paso.
Reglas: <=200 líneas, <=150 chars por línea.
"""

from __future__ import annotations

from typing import Optional, Any

import pandas as pd

from axis.cli.tables import format_table
from axis.cli.colors import heading, arrow, ok, fail, table_label, dim, bold
from axis.sismico.tables_e030 import (
    TABLA_ZONA,
    TABLA_PERFIL_DESC,
    TABLA_FACTOR_SUELO_S,
    TABLA_PERIODOS_TP_TL,
    TABLA_CATEGORIA,
    TABLA_SISTEMA,
    TABLA_CLASIFICACION,
    TABLA_MATERIAL_DISTORSION,
)


def _df_a_filas(df: Optional[pd.DataFrame]) -> list[dict]:
    if df is None or df.empty:
        return []
    return df.to_dict("records")


def paso1_zona(zona: int, z: float) -> str:
    """Paso 1: Tabla zona sísmica + factor Z usado."""
    salida = heading("1 - Factor de Zona Sismica (Z)\n")
    salida += table_label("Tabla - Zona Sismica | Factor de Zona (Z):\n") + format_table(TABLA_ZONA)
    salida += "\n\n" + arrow(f"Zona ingresada: {zona} | Factor Z tomado: {z}")
    return salida


def paso2_perfil_desc(perfil: str) -> str:
    """Paso 2: Tabla perfil (descripción) + factor suelo usado."""
    salida = heading("2 - Factor de Suelo (S) - Perfil\n")
    salida += table_label("Tabla N° 2 - Perfil | Descripcion | Vs (m/s) | N60 | Su (kPa):\n") + format_table(TABLA_PERFIL_DESC)
    salida += "\n\n" + arrow(f"Perfil ingresado: {perfil.upper()}")
    return salida


def paso3_perfil_stptl(zona: int, perfil: str, s_val: Any, tp: Any, tl: Any) -> str:
    """Paso 3: Tablas N° 3 (Factor S) y N° 4 (Tp, Tl) + valores usados."""
    salida = heading("3 - Parametros de sitio S, Tp, Tl\n")
    salida += table_label("Tabla N° 3 - Factor de Suelo S (Zona x Perfil):\n") + format_table(TABLA_FACTOR_SUELO_S)
    salida += "\n" + table_label("Tabla N° 4 - Períodos Tp y Tl (s):\n") + format_table(TABLA_PERIODOS_TP_TL)
    salida += "\n\n" + arrow(f"Zona {zona}, Perfil {perfil.upper()}: S={s_val}, Tp={tp} s, Tl={tl} s")
    return salida


def paso4_categoria_c_spectrum(categoria: str, u: float, filas_ct: list[dict]) -> str:
    """Paso 4: Tabla categoría + U usado (sin tabla C vs T)."""
    salida = heading("4 - Categoria y espectro C vs T\n")
    salida += table_label("Tabla - Categoria | Tipo | U:\n") + format_table(TABLA_CATEGORIA)
    salida += "\n\n" + arrow(f"Categoria ingresada: {categoria} | Factor U tomado: {u}\n")
    return salida


def paso6_sistema(r0: float) -> str:
    """Paso 6: Tabla sistema estructural + R0 usado."""
    salida = heading("5 - Factor de reduccion R0\n")
    salida += table_label("Tabla - Sistema Estructural | R0:\n") + format_table(TABLA_SISTEMA)
    salida += "\n\n" + arrow(f"R0 tomado: {r0}")
    return salida


def paso7_irregularidad(ia: float, ip: float) -> str:
    """Paso 7: Tabla factores de irregularidad Ia, Ip."""
    salida = heading("6 - Factores de irregularidad\n")
    tabla = [{"Factor": "Ia (altura)", "Valor": ia}, {"Factor": "Ip (planta)", "Valor": ip}]
    salida += table_label("Tabla - Factores:\n") + format_table(tabla)
    return salida


def paso8_coeficiente_r(r0: float, ia: float, ip: float, r: float) -> str:
    """Paso 8: Cálculo R = R0 * Ia * Ip."""
    salida = heading("7 - Coeficiente de Reduccion R\n")
    salida += bold(f"R = R0 * Ia * Ip = {r0} * {ia} * {ip} = {r}")
    return salida


def paso9_periodo(
    sentido: str,
    periodo: float,
    tabla_etabs: Optional[pd.DataFrame],
    tabla_modal_periods: Optional[pd.DataFrame],
) -> str:
    """Paso 9: Periodo fundamental + (opcional) tabla Modal Periods And Frequencies."""
    salida = heading(f"8 - Periodo fundamental (sentido {sentido})\n")
    salida += arrow(f"Periodo T tomado: {periodo:.4f} s\n")
    # Ya no se muestra la tabla Case/Period para no saturar la salida CLI.
    if tabla_modal_periods is not None and not tabla_modal_periods.empty:
        salida += "\n" + table_label("Tabla ETABS - Modal Periods And Frequencies:\n")
        salida += format_table(_df_a_filas(tabla_modal_periods))
    return salida


def paso10_masa(sentido: str, tabla: Optional[pd.DataFrame], cumple: bool) -> str:
    """Paso 10: Tabla % masa participante."""
    salida = heading(f"9 - Porcentaje masa participante (sentido {sentido})\n")
    if tabla is not None and not tabla.empty:
        salida += table_label("Tabla - Case, Period, UX, UY, UZ, SumUX, SumUY, SumUZ:\n")
        salida += format_table(_df_a_filas(tabla))
        val = ok("Si") if cumple else fail("No")
        salida += "\n" + arrow(f"Cumple >= 90%: {val}")
    else:
        salida += dim("(Requiere ETABS)")
    return salida


def paso11_peso(tabla: Optional[pd.DataFrame]) -> str:
    """Paso 11: Tabla estimación peso (Story, Peso X, Peso Y)."""
    salida = heading("10 - Estimacion de Peso de la edificacion\n")
    if tabla is not None and not tabla.empty:
        salida += table_label("Tabla - Story | Peso X | Peso Y:\n") + format_table(_df_a_filas(tabla))
    else:
        salida += dim("(Requiere ETABS Mass Summary by Story)")
    return salida


def paso12_estatico(sentido: str, tabla: Optional[pd.DataFrame]) -> str:
    """Paso 12: Tabla análisis estático (Story Forces SISMOX o SISMOY)."""
    caso = "SISMOX" if sentido.upper() == "X" else "SISMOY"
    col = "VX" if sentido.upper() == "X" else "VY"
    salida = heading(f"11 - Analisis estatico (sentido {sentido})\n")
    salida += table_label(f"Tabla - Story Forces OutputCase={caso} Location=Bottom ({col}):\n")
    if tabla is not None and not tabla.empty:
        salida += format_table(_df_a_filas(tabla))
    else:
        salida += dim("(Requiere ETABS)")
    return salida


def paso12_dinamico(sentido: str, tabla: Optional[pd.DataFrame]) -> str:
    """Paso 12: Tabla análisis dinámico (Story Forces SPX o SPY)."""
    caso = "SPX" if sentido.upper() == "X" else "SPY"
    col = "VX" if sentido.upper() == "X" else "VY"
    salida = heading(f"12 - Analisis dinamico (sentido {sentido})\n")
    salida += table_label(f"Tabla - Story Forces OutputCase={caso} Location=Bottom ({col}):\n")
    if tabla is not None and not tabla.empty:
        salida += format_table(_df_a_filas(tabla))
    else:
        salida += dim("(Requiere ETABS)")
    return salida


def _ascii_plot_sa(filas_espectro: list[dict]) -> str:
    """Grafico CLI del espectro Sa vs T tipo plot ASCII (estilo plotext con '*')."""
    if not filas_espectro:
        return dim("(sin datos para grafico)")
    # Extraer T y Sa
    ts: list[float] = []
    sas: list[float] = []
    for fila in filas_espectro:
        try:
            t = float(fila.get("T", 0.0))
            sa = float(fila.get("Sa", 0.0))
        except (TypeError, ValueError):
            continue
        ts.append(t)
        sas.append(sa)
    if not ts or not sas:
        return dim("(sin datos numericos para grafico)")
    t_min, t_max = min(ts), max(ts)
    sa_min, sa_max = 0.0, max(sas)
    if t_max <= t_min:
        t_max = t_min + 1.0
    if sa_max <= sa_min:
        sa_max = sa_min + 1.0
    # Tamaño del grafico (ancho x alto en celdas) – mayor resolución
    width, height = 60, 10
    grid = [[" " for _ in range(width)] for _ in range(height)]
    # Mapear puntos Sa(T) a la grilla usando '*'
    for t, sa in zip(ts, sas):
        x = int((t - t_min) / (t_max - t_min) * (width - 1))
        x = max(0, min(width - 1, x))
        frac_y = (sa - sa_min) / (sa_max - sa_min) if sa_max > sa_min else 0.0
        y = height - 1 - int(round(frac_y * (height - 1)))
        y = max(0, min(height - 1, y))
        grid[y][x] = "*"
    # Construir lineas con etiquetas Sa a la izquierda
    label_width = 6
    lines: list[str] = [bold("Sa (g)\n")]
    for row in range(height):
        # Etiquetas Sa(g) tipo 1.0, 0.8, 0.6, ...
        nivel = sa_max * (height - row) / (height + 0)  # evita 0 exacto en ultima fila
        label = f"{nivel:4.3g}".rjust(label_width - 1) + " "
        lines.append(f"{label}|{''.join(grid[row])}")
    # Eje T en la base
    axis = " " * label_width + "+" + "-" * width
    lines.append(axis)
    # Marcas de T(s) aproximadas (5 marcas equiespaciadas)
    ratios = [0.0, 0.25, 0.5, 0.75, 1.0]
    tick_vals = [t_min + (t_max - t_min) * r for r in ratios]
    tick_line = [" " for _ in range(width)]
    for r, val in zip(ratios, tick_vals):
        txt = f"{val:.2f}"
        pos = int(r * (width - 1))
        pos = max(0, min(width - len(txt), pos))
        for i, ch in enumerate(txt):
            tick_line[pos + i] = ch
    lines.append(" " * (label_width + 1) + "".join(tick_line) + "  T (s)")
    return "\n".join(lines)


def paso13_espectro(
    z: float, u: float, s_val: float, r: float,
    filas_espectro: list[dict],
) -> str:
    """Paso 13: Espectro Sa vs T mostrado como grafico CLI (no tabla)."""
    salida = heading("13 - Espectro sismico Sa\n")
    salida += dim("Sa = (Z * U * C * S / R) * g\n")
    salida += table_label("Grafico CLI - Espectro Sa vs T:\n")
    salida += _ascii_plot_sa(filas_espectro)
    return salida


def paso14_cortante_minima(
    sentido: str,
    datos_cortante: Optional[dict[str, Any]],
    tabla_etabs: Optional[pd.DataFrame],
) -> str:
    """Paso 14: Verificación cortante mínima (salida resumida)."""
    salida = heading(f"14 - Verificacion cortante minima (sentido {sentido})\n")
    if not datos_cortante:
        salida += "\n" + dim("(Requiere ETABS Base Reactions para verificar cortante minima)")
        return salida
    estatico = float(datos_cortante.get("cortante_estatico", 0.0))
    dinamico = float(datos_cortante.get("cortante_dinamico", 0.0))
    requiere_escalar = bool(datos_cortante.get("requiere_escalar", False))
    factor_escala = float(datos_cortante.get("factor_escala", 1.0))
    dinamico_esc = float(datos_cortante.get("cortante_dinamico_escalado", dinamico))
    cumple_con = bool(datos_cortante.get("cumple_con_escalar", False))
    tabla_resumen = [
        {"Tipo": "Sismo estatico (Vest)", "Cortante basal (Tn)": round(abs(estatico), 2)},
        {"Tipo": "Sismo dinamico (Vdin)", "Cortante basal (Tn)": round(abs(dinamico), 2)},
    ]
    salida += table_label("Tabla - Cortante en la base:\n")
    salida += format_table(tabla_resumen)
    v_usada = abs(dinamico_esc if requiere_escalar else dinamico)
    necesita_txt = "Si" if requiere_escalar else "No"
    cumple_txt = ok("Si") if cumple_con else fail("No")
    salida += f"\n{bold('Necesita escalar')}: {necesita_txt}"
    if requiere_escalar:
        salida += f" (gamma = {factor_escala:.3f})"
    salida += f"\n{bold('Cortante a considerar Vbas')}: {v_usada:.2f}\n"
    salida += arrow(f"Cumple cortante minima: {cumple_txt}")
    return salida


def paso15_hipotesis(
    sentido: str,
    cortante_basal: float,
    cortante_columnas: float,
    cortante_muros: float,
    pct_columnas: float,
    pct_muros: float,
    sistema_clasificado: str,
) -> str:
    """Paso 15: Tabla cortante columnas y muros con % respecto a basal."""
    salida = heading(f"15 - Revision hipotesis de analisis (sentido {sentido})\n")
    tabla = [
        {"Elemento": "Cortante basal", "Cortante (Tn)": round(cortante_basal, 2), "% del basal": "100%"},
        {"Elemento": "Columnas", "Cortante (Tn)": round(cortante_columnas, 2), "% del basal": f"{pct_columnas:.1f}%"},
        {"Elemento": "Muros", "Cortante (Tn)": round(cortante_muros, 2), "% del basal": f"{pct_muros:.1f}%"},
    ]
    salida += table_label("Tabla - Cortante columnas y muros (% respecto a basal):\n") + format_table(tabla)
    salida += "\n" + table_label("Clasificacion E.030:\n") + format_table(TABLA_CLASIFICACION)
    salida += "\n" + arrow(f"Sistema clasificado: {bold(sistema_clasificado)}")
    return salida


def paso16_distorsion(
    sentido: str,
    material: str,
    drift_max: float,
    r_usado: float,
    tabla_drift: Optional[pd.DataFrame],
    tabla_verif: Optional[pd.DataFrame],
    cumple: bool,
) -> str:
    """Paso 16: Distorsión admisible - tablas."""
    salida = heading(f"16 - Distorsion admisible (sentido {sentido})\n")
    salida += table_label("Tabla - Material | Distorsion Max (d/h):\n") + format_table(TABLA_MATERIAL_DISTORSION)
    salida += "\n" + arrow(f"Material: {material} | R usado: {bold(str(r_usado))} (R0*Ia*Ip) | Distorsion max: {drift_max}\n")
    if tabla_drift is not None and not tabla_drift.empty:
        salida += "\n" + table_label("Tabla - Story Drifts:\n") + format_table(_df_a_filas(tabla_drift))
    if tabla_verif is not None and not tabla_verif.empty:
        salida += "\n" + table_label("Tabla - Verificacion (Drift*0.75*R vs admisible):\n")
        salida += format_table(_df_a_filas(tabla_verif))
    val = ok("Si") if cumple else fail("No")
    salida += "\n" + arrow(f"Cumple: {val}")
    return salida
