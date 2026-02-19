"""Handlers CLI para análisis sísmico E.030. Reglas: ≤200 líneas, ≤150 chars."""

from __future__ import annotations

from axis.core.exceptions import InvalidInput
from axis.core.project import get_active_project_path
from axis.core.database import write_results_csv, read_results_csv
from axis.cli.tables import format_table
from axis.sismico.tables_e030 import (
    obtener_z,
    obtener_parametros_sitio,
    obtener_u,
    obtener_r0,
    obtener_distorsion_maxima,
)
from axis.sismico.etapa1_peligro import tabla_c_vs_t
from axis.sismico.etapa2_edificio import coeficiente_reduccion_r
from axis.sismico import (
    periodo_fundamental_etabs,
    masa_participante_etabs,
    peso_edificio_etabs,
    story_forces_estatico_etabs,
    story_forces_dinamico_etabs,
    verificar_cortante_minima_etabs,
    clasificar_sistema_estructural_etabs,
    distorsion_admisible_etabs,
    separacion_edificios,
)


def _get_project_path():
    from axis.cli.handlers import get_base_path
    path = get_active_project_path(get_base_path())
    if not path:
        raise InvalidInput("No hay proyecto activo. Use 'cas use <proyecto>'.")
    return path


def handle_sismo(args: list[str]) -> str:
    """cas sismo <etapa> [args]. Etapas: etapa1, etapa2, etapa3, etapa4."""
    if not args:
        return (
            "Uso: cas sismo etapa1 <zona> <perfil> | etapa2 ... | etapa3 | etapa4 <r0> <material> [Vx Vy] [h [Δa Δb]] | "
            "separacion <h> [Δa Δb] | results"
        )
    sub = args[0].lower()
    if sub == "etapa1":
        return handle_sismo_etapa1(args[1:])
    if sub == "etapa2":
        return handle_sismo_etapa2(args[1:])
    if sub == "etapa3":
        return handle_sismo_etapa3()
    if sub == "etapa4":
        return handle_sismo_etapa4(args[1:])
    if sub == "results":
        return handle_sismo_results()
    if sub == "separacion":
        return handle_sismo_separacion(args[1:])
    return f"Subcomando desconocido: {sub}. Use etapa1, etapa2, etapa3, etapa4, separacion o results."


def handle_sismo_etapa1(args: list[str]) -> str:
    """cas sismo etapa1 <zona> <perfil>. Zona 1-4, perfil s0-s4."""
    if len(args) < 2:
        raise InvalidInput("Uso: cas sismo etapa1 <zona> <perfil>. Ej: etapa1 3 s2")
    try:
        zona = int(args[0])
        perfil = args[1].strip().lower()
    except ValueError:
        raise InvalidInput("Zona debe ser 1, 2, 3 o 4.")
    z = obtener_z(zona)
    params = obtener_parametros_sitio(perfil)
    if params.get("tp") is None:
        raise InvalidInput("Perfil s4 requiere estudio específico (Tp, Tl).")
    tp, tl = params["tp"], params["tl"]
    datos_ct = tabla_c_vs_t(tp, tl)
    filas = [{"T": round(t, 4), "C": round(c, 4)} for t, c in datos_ct]
    path = _get_project_path()
    out = write_results_csv(path, "sismo_peligro_espectro.csv", filas)
    titulo = f"Etapa 1 – Peligro sísmico\nZ={z}, S={params['s']}, Tp={tp} s, Tl={tl} s\n"
    tabla_str = format_table(filas, columns=["T", "C"])
    return titulo + "Factor de amplificación C vs T\n\n" + tabla_str + f"\n\n({len(filas)} puntos). Resultados guardados: {out}"


def handle_sismo_etapa2(args: list[str]) -> str:
    """cas sismo etapa2 <categoria> <sistema> <Ia> <Ip>. Categoría A-D, sistema ver tables_e030."""
    if len(args) < 4:
        raise InvalidInput(
            "Uso: cas sismo etapa2 <categoria> <sistema> <Ia> <Ip>. "
            "Sistema: portico_concreto, muros_estructurales, dual, albañileria_confinada"
        )
    cat, sistema, ia_str, ip_str = args[0], args[1], args[2], args[3]
    try:
        ia, ip = float(ia_str), float(ip_str)
    except ValueError:
        raise InvalidInput("Ia e Ip deben ser números.")
    u = obtener_u(cat)
    r0 = obtener_r0(sistema)
    r = coeficiente_reduccion_r(r0, ia, ip)
    path = _get_project_path()
    fila = {"U": u, "R0": r0, "Ia": ia, "Ip": ip, "R": round(r, 4)}
    write_results_csv(path, "sismo_edificio.csv", [fila])
    titulo = "Etapa 2 – Caracterización del edificio\n\n"
    return titulo + format_table([fila], columns=["U", "R0", "Ia", "Ip", "R"]) + f"\n\nResultados guardados: {path}/results/sismo_edificio.csv"


def _df_a_filas(df):
    """Convierte DataFrame a list[dict] para format_table."""
    if df is None or df.empty:
        return []
    return df.to_dict("records")


def handle_sismo_etapa3() -> str:
    """cas sismo etapa3. Requiere ETABS. Periodo, masa, peso, story forces, cortante mínima."""
    _get_project_path()
    salidas = ["Etapa 3 – Análisis estructural\n"]
    res_per = periodo_fundamental_etabs(log=True)
    if res_per:
        salidas.append(
            f"Periodo fundamental X: {res_per['periodo_x']:.4f} s, Y: {res_per['periodo_y']:.4f} s"
        )
        tbl = res_per.get("tabla_case_period")
        if tbl is not None and not tbl.empty:
            filas = _df_a_filas(tbl)
            salidas.append("\nTabla Case / Period (modal):\n" + format_table(filas[:15]))
            if len(filas) > 15:
                salidas.append(f"… y {len(filas) - 15} filas más.")
    else:
        salidas.append("Periodo: no disponible (revisar ETABS/Modal Participating Mass Ratios).")
    res_masa = masa_participante_etabs(log=True)
    if res_masa:
        salidas.append(
            f"\nMasa participante ≥90%: X={res_masa['cumple_90_x']}, Y={res_masa['cumple_90_y']}"
        )
        if res_masa.get("tabla") is not None and not res_masa["tabla"].empty:
            salidas.append("\nMasa participante:\n"
                          + format_table(_df_a_filas(res_masa["tabla"].head(12))))
    df_peso = peso_edificio_etabs(log=True)
    if df_peso is not None and not df_peso.empty:
        salidas.append("\nPeso por piso (Story, Peso X, Peso Y):\n" + format_table(_df_a_filas(df_peso)))
    est = story_forces_estatico_etabs(log=True)
    if est and est.get("SISMOX") is not None and not est["SISMOX"].empty:
        salidas.append("\nStory Forces estático SISMOX (VX):\n" + format_table(_df_a_filas(est["SISMOX"])))
    if est and est.get("SISMOY") is not None and not est["SISMOY"].empty:
        salidas.append("\nStory Forces estático SISMOY (VY):\n" + format_table(_df_a_filas(est["SISMOY"])))
    din = story_forces_dinamico_etabs(log=True)
    if din and din.get("SPX") is not None and not din["SPX"].empty:
        salidas.append("\nStory Forces dinámico SPX (VX):\n" + format_table(_df_a_filas(din["SPX"])))
    if din and din.get("SPY") is not None and not din["SPY"].empty:
        salidas.append("\nStory Forces dinámico SPY (VY):\n" + format_table(_df_a_filas(din["SPY"])))
    cort = verificar_cortante_minima_etabs(log=True)
    if cort:
        rx, ry = cort["x"], cort["y"]
        salidas.append(
            f"\nCortante mínima 80%: X cumple={rx['cumple_80']} (ratio={rx['ratio']:.2%}), "
            f"Y cumple={ry['cumple_80']} (ratio={ry['ratio']:.2%})"
        )
    return "\n".join(salidas)


def handle_sismo_etapa4(args: list[str]) -> str:
    """cas sismo etapa4 <r0> <material> [cortante_x cortante_y] [h [despl_a despl_b]]. Output según E.030."""
    if len(args) < 2:
        raise InvalidInput(
            "Uso: cas sismo etapa4 <r0> <material> [Vx Vy] [h [Δa Δb]]. "
            "Material: concreto_armado, acero, albañileria, madera, concreto_ductilidad_limitada"
        )
    try:
        r0 = float(args[0])
    except ValueError:
        raise InvalidInput("r0 debe ser un número.")
    material = args[1]
    cortante_x = float(args[2]) if len(args) > 2 else None
    cortante_y = float(args[3]) if len(args) > 3 else None
    h_sep = float(args[4]) if len(args) > 4 else None
    despl_a = float(args[5]) if len(args) > 5 else 0.0
    despl_b = float(args[6]) if len(args) > 6 else 0.0
    salidas = ["ETAPA 4 – VALIDACIÓN DE LA ESTRUCTURA (E.030)\n" + "=" * 50]
    cl = clasificar_sistema_estructural_etabs(
        cortante_basal_x=cortante_x,
        cortante_basal_y=cortante_y,
        log=True,
    )
    if cl:
        salidas.append("\n--- Paso 12: Revisión hipótesis de análisis (R adecuado) ---")
        salidas.append(
            f"Cortante basal (paso 10, Story1): VX = {cl.get('cortante_basal_x', 0):.2f}, "
            f"VY = {cl.get('cortante_basal_y', 0):.2f}"
        )
        salidas.append(
            f"Suma V3 (X) = {cl.get('sum_v3', 0):.2f} → "
            f"{cl.get('pct_porticos_x', 0):.1f}% pórticos, {cl['porcentaje_muros_x']:.1f}% muros."
        )
        salidas.append(
            f"Suma V2 (Y) = {cl.get('sum_v2', 0):.2f} → "
            f"{cl.get('pct_porticos_y', 0):.1f}% pórticos, {cl['porcentaje_muros_y']:.1f}% muros."
        )
        salidas.append("\nTabla – Sentido X (Story=Story1, OutputCase=SPX, Station=0). Columnas: Story, Column, OutputCase, V3:")
        if cl.get("tabla_x") is not None and not cl["tabla_x"].empty:
            salidas.append(format_table(_df_a_filas(cl["tabla_x"])))
        salidas.append("\nTabla – Sentido Y (Story=Story1, OutputCase=SPY, Station=0). Columnas: Story, Column, OutputCase, V2:")
        if cl.get("tabla_y") is not None and not cl["tabla_y"].empty:
            salidas.append(format_table(_df_a_filas(cl["tabla_y"])))
        salidas.append("\nClasificación (E.030): % Cortante tomado por Muros | % Cortante tomado por Pórticos:")
        if cl.get("tabla_clasificacion"):
            salidas.append(format_table(cl["tabla_clasificacion"]))
    else:
        salidas.append("\n--- Paso 12: Revisión hipótesis de análisis ---")
        salidas.append("Requiere ETABS con tabla Element Forces (Story=Story1, OutputCase=SPX/SPY, Station=0).")
    salidas.append("\n--- Paso 13: Distorsión admisible ---")
    drift_adm = obtener_distorsion_maxima(material)
    salidas.append(f"Distorsión máxima admisible (Δ/h) para material '{material}': {drift_adm}. R0={r0}.")
    from axis.sismico.etapa4_validacion import _tabla_distorsion_material_e030
    tabla_mat = _tabla_distorsion_material_e030(material, drift_adm)
    salidas.append("\nTabla – Material predominante | Distorsión Máxima Admisible (Δ/h):")
    salidas.append(format_table(tabla_mat))
    dr = distorsion_admisible_etabs(r0, material, log=True)
    if dr:
        salidas.append("\nTabla – Story Drifts X (OutputCase=SPX, Direction=X): Story, OutputCase, Direction, DriftX:")
        if dr.get("tabla_x") is not None and not dr["tabla_x"].empty:
            salidas.append(format_table(_df_a_filas(dr["tabla_x"])))
        salidas.append("\nTabla – Verificación X (Drift·0.75·R0 vs admisible):")
        if dr.get("tabla_verificacion_x") is not None and not dr["tabla_verificacion_x"].empty:
            salidas.append(format_table(_df_a_filas(dr["tabla_verificacion_x"])))
        salidas.append("\nTabla – Story Drifts Y (OutputCase=SPY, Direction=Y): Story, OutputCase, Direction, DriftY:")
        if dr.get("tabla_y") is not None and not dr["tabla_y"].empty:
            salidas.append(format_table(_df_a_filas(dr["tabla_y"])))
        salidas.append("\nTabla – Verificación Y (Drift·0.75·R0 vs admisible):")
        if dr.get("tabla_verificacion_y") is not None and not dr["tabla_verificacion_y"].empty:
            salidas.append(format_table(_df_a_filas(dr["tabla_verificacion_y"])))
        salidas.append(f"\nCumple drift X: {dr.get('cumple_x')}, Y: {dr.get('cumple_y')}.")
    else:
        salidas.append("\nTablas de drift: requiere ETABS abierto con análisis (Story Drifts).")
    if h_sep is not None:
        salidas.append("\n--- Paso 14: Separación de edificios ---")
        sep = separacion_edificios(h_sep, despl_a, despl_b)
        salidas.append("Tabla – s = max(0.006·h, 0.03) y s ≥ 2/3·(Δa+Δb):")
        salidas.append(format_table(sep["tabla"]))
    return "\n".join(salidas)


def handle_sismo_separacion(args: list[str]) -> str:
    """Paso 14 E.030: cas sismo separacion <h> [Δa Δb]. s = 0.006·h ≥ 0.03; s ≥ (2/3)·(Δa+Δb)."""
    if not args:
        raise InvalidInput("Uso: cas sismo separacion <h> [despl_a despl_b]. h en m.")
    try:
        h = float(args[0])
    except ValueError:
        raise InvalidInput("h debe ser un número (altura en m).")
    despl_a = float(args[1]) if len(args) > 1 else 0.0
    despl_b = float(args[2]) if len(args) > 2 else 0.0
    sep = separacion_edificios(h, despl_a, despl_b)
    salidas = [
        "Paso 14 – Separación de edificios (E.030)",
        "s ≥ 2/3 de la suma de los desplazamientos máximos de edificios adyacentes.",
        "s = 0.006·h ≥ 0.03. El mayor de todos estos valores será el valor de s.",
        "",
        "Tabla – Criterios y valor de s (m):",
        format_table(sep["tabla"]),
        "",
        f"→ Separación mínima a usar: s = {sep['s_final']:.4f} m",
    ]
    return "\n".join(salidas)


def handle_sismo_results() -> str:
    """cas sismo results. Muestra resultados guardados (espectro C vs T y edificio)."""
    path = _get_project_path()
    salidas = ["Resultados sismo (guardados en results/)\n"]
    peligro = read_results_csv(path, "sismo_peligro_espectro.csv")
    if peligro:
        salidas.append("Espectro C vs T (sismo_peligro_espectro.csv):\n" + format_table(peligro))
    else:
        salidas.append("Sin resultados de etapa1. Ejecute: cas sismo etapa1 <zona> <perfil>")
    edificio = read_results_csv(path, "sismo_edificio.csv")
    if edificio:
        salidas.append("\nCaracterización edificio (sismo_edificio.csv):\n" + format_table(edificio))
    return "\n".join(salidas)
