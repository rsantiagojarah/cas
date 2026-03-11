"""Handlers CLI: muros (predimension núcleo). Reglas: ≤200 líneas, ≤150 chars."""

from __future__ import annotations

from axis.core.exceptions import NoActiveProject, InvalidInput
from axis.core.project import get_active_project_path
from axis.core.database import write_results_csv, read_results_csv
from axis.engine.engine import run
from axis.cli.tables import format_table
from axis.cli.handlers import get_base_path
from pathlib import Path
from axis.data.etabs_table_reader import get_table, clear_table_cache


def _get_muros_results_dir(project_path: Path) -> Path:
    """Directorio de resultados por muro: results/muros_nucleo/."""
    results_dir = project_path / "results" / "muros_nucleo"
    results_dir.mkdir(parents=True, exist_ok=True)
    return results_dir


def _sanitize_name(name: str) -> str:
    """Sanitiza nombre de muro para usarlo como nombre de archivo."""
    name = name.strip()
    if not name:
        return "muro"
    allowed = "".join(c for c in name if c.isalnum() or c in ("-", "_"))
    return allowed or "muro"


def handle_muro_nucleo(args: list[str]) -> str:
    """
    cas muro nucleo <nombre_muro> <L> <fy> <nivel> <hm> <Mu> [phi]

    Permite ingresar nivel por nivel, sin usar Excel:
      - nombre_muro : identificador del muro (ej. Muro_E1)
      - L           : longitud del núcleo del muro (m)
      - fy          : fluencia del acero (kg/cm²)
      - nivel       : etiqueta del nivel (ej. Piso_01)
      - hm          : altura de ese tramo (m)
      - Mu          : momento último en el núcleo (Tn-m)
      - phi         : factor φ de flexión (opcional, por defecto 0.90)

    Cada llamada agrega el resultado del nivel al muro indicado,
    guarda/actualiza results/muros_nucleo/<nombre_muro>.csv y
    muestra la tabla completa acumulada de ese muro.
    """
    project_path = get_active_project_path(get_base_path())
    if not project_path:
        raise NoActiveProject("No hay proyecto activo. Use 'cas use <proyecto>'.")

    if len(args) < 6:
        raise InvalidInput(
            "Uso: cas muro nucleo <nombre_muro> <L> <fy> <nivel> <hm> <Mu> [phi]\n"
            "  nombre_muro: identificador del muro (ej. Muro_E1)\n"
            "  L          : longitud del núcleo del muro (m)\n"
            "  fy         : fluencia del acero (kg/cm²)\n"
            "  nivel      : etiqueta del nivel (ej. Piso_01)\n"
            "  hm         : altura de tramo (m)\n"
            "  Mu         : momento último (Tn-m)\n"
            "  phi        : φ (opcional, por defecto 0.90)"
        )

    try:
        nombre_muro = args[0]
        L = float(args[1])
        fy = float(args[2])
        nivel = args[3]
        hm = float(args[4])
        mu = float(args[5])
        phi = float(args[6]) if len(args) > 6 else 0.90
    except ValueError:
        raise InvalidInput("L, fy, hm, Mu y phi deben ser numéricos.")

    if L <= 0 or fy <= 0 or hm <= 0 or mu <= 0 or phi <= 0:
        raise InvalidInput("L, fy, hm, Mu y phi deben ser mayores que cero.")

    # Leer resultados previos del muro (si existen) para acumular H_total
    results_dir = _get_muros_results_dir(project_path)
    file_name = _sanitize_name(nombre_muro) + ".csv"
    muro_path = results_dir / file_name

    prev_rows = read_results_csv(project_path, f"muros_nucleo/{file_name}") if muro_path.exists() else []
    h_inicial = 0.0
    if prev_rows:
        try:
            last = prev_rows[-1]
            h_inicial = float(str(last.get("H_total", "0")).replace(",", "."))
        except ValueError:
            h_inicial = 0.0

    niveles = [{"nivel": nivel, "hm": hm, "Mu": mu}]

    data = {"L": L, "fy": fy, "phi": phi, "H_inicial": h_inicial, "niveles": niveles}
    result = run("predimension", "muro_nucleo", data)
    resultados = result.get("resultados", [])
    if not resultados:
        raise InvalidInput("No se obtuvieron resultados de predimensionamiento.")

    # Agregar meta de muro a las filas nuevas
    for fila in resultados:
        fila["muro"] = nombre_muro
        fila["L"] = L
        fila["fy"] = fy
        fila["phi"] = phi

    # Acumular con resultados previos y guardar tabla completa del muro
    todos = prev_rows + resultados

    out_path = write_results_csv(
        project_path, f"muros_nucleo/{file_name}", todos
    )

    # Añadir columna de índice para la tabla CLI
    for i, fila in enumerate(todos):
        fila["N"] = str(i + 1)
    cols = [
        "N",
        "muro",
        "nivel",
        "hm",
        "H_total",
        "H_L",
        "tipo_muro",
        "tipo_falla",
        "Mu",
        "z",
        "As",
    ]

    tabla = format_table(todos, columns=cols)

    return (
        f"Predimensionamiento de acero en núcleo de muro '{nombre_muro}' (niveles acumulados)\n\n"
        + tabla
        + f"\n\nResultados guardados en: {out_path}"
    )


def handle_muro_list(args: list[str]) -> str:
    """cas muro list  -> Lista muros con resultados y resumen básico."""
    project_path = get_active_project_path(get_base_path())
    if not project_path:
        raise NoActiveProject("No hay proyecto activo. Use 'cas use <proyecto>'.")
    results_dir = _get_muros_results_dir(project_path)
    archivos = sorted(p for p in results_dir.glob("*.csv") if p.is_file())
    if not archivos:
        return "No hay muros predimensionados aún."
    resumen: list[dict] = []
    for p in archivos:
        nombre = p.stem
        filas = read_results_csv(project_path, f"muros_nucleo/{p.name}")
        if not filas:
            continue
        n_niveles = len(filas)
        try:
            h_max = float(str(filas[-1].get("H_total", "0")).replace(",", "."))
        except ValueError:
            h_max = 0.0
        L = filas[0].get("L", "")
        fy = filas[0].get("fy", "")
        resumen.append(
            {
                "muro": nombre,
                "niveles": n_niveles,
                "H_total_max": round(h_max, 2),
                "L": L,
                "fy": fy,
            }
        )
    if not resumen:
        return "No hay muros predimensionados aún."
    for i, fila in enumerate(resumen):
        fila["N"] = str(i + 1)
    cols = ["N", "muro", "niveles", "H_total_max", "L", "fy"]
    tabla = format_table(resumen, columns=cols)
    return "Muros predimensionados (núcleo)\n\n" + tabla


def handle_muro_delete(args: list[str]) -> str:
    """cas muro delete <nombre_muro>  -> Elimina resultados de un muro."""
    project_path = get_active_project_path(get_base_path())
    if not project_path:
        raise NoActiveProject("No hay proyecto activo. Use 'cas use <proyecto>'.")
    if not args:
        raise InvalidInput("Uso: cas muro delete <nombre_muro>")
    nombre = args[0]
    results_dir = _get_muros_results_dir(project_path)
    file_name = _sanitize_name(nombre) + ".csv"
    path = results_dir / file_name
    if not path.exists():
        raise InvalidInput(f"No existe muro con nombre '{nombre}'.")
    path.unlink()
    return f"Resultados del muro '{nombre}' eliminados."


def handle_muro_etabs(args: list[str]) -> str:
    """
    cas muro etabs <nombre_muro> <L> <fy> <pier_name> [phi]

    Lee la tabla 'Pier Forces' de ETABS, filtra por:
      - Pier = <pier_name>
      - OutputCase = SPX o SPY según el nombre del pier:
          * Si el nombre contiene 'X' (may/min) -> SPX
          * Si contiene 'Y'                   -> SPY
          * Si contiene ambos, Error (sea explícito).
      - Para cada Story toma el MAYOR M3 como Mu (Tn-m)

    Luego genera todos los niveles del muro de una vez y
    guarda en results/muros_nucleo/<nombre_muro>.csv.
    """
    project_path = get_active_project_path(get_base_path())
    if not project_path:
        raise NoActiveProject("No hay proyecto activo. Use 'cas use <proyecto>'.")
    if len(args) < 4:
        raise InvalidInput(
            "Uso: cas muro etabs <nombre_muro> <L> <fy> <pier_name> [phi]\n"
            "  nombre_muro: identificador del muro (ej. Muro_E1)\n"
            "  L          : longitud del núcleo del muro (m)\n"
            "  fy         : fluencia del acero (kg/cm²)\n"
            "  pier_name  : nombre del Pier en ETABS\n"
            "  phi        : φ (opcional, por defecto 0.90)"
        )
    nombre_muro = args[0]
    try:
        L = float(args[1])
        fy = float(args[2])
        phi = float(args[4]) if len(args) > 4 else 0.90
    except ValueError:
        raise InvalidInput("L, fy y phi deben ser numéricos.")
    pier_name = args[3]
    if L <= 0 or fy <= 0 or phi <= 0:
        raise InvalidInput("L, fy y phi deben ser mayores que cero.")

    clear_table_cache()
    df = get_table("Pier Forces", log=True)
    if df is None or df.empty:
        raise InvalidInput(
            "No se pudo leer la tabla 'Pier Forces' desde ETABS. "
            "Verifique que ETABS esté abierto, con análisis ejecutado."
        )

    df = df.copy()
    df.columns = [str(c).strip().lower() for c in df.columns]

    cols_necesarias = {"story", "pier", "outputcase", "m3"}
    if not cols_necesarias.issubset(df.columns):
        raise InvalidInput(
            "La tabla 'Pier Forces' no contiene las columnas esperadas "
            "(Story, Pier, OutputCase, M3). Revise configuración de ETABS."
        )

    pier_filtro = str(pier_name).strip()
    df = df[df["pier"].astype(str) == pier_filtro]
    if df.empty:
        raise InvalidInput(f"No se encontraron filas para el Pier '{pier_filtro}'.")

    name_upper = pier_filtro.upper()
    tiene_x = "X" in name_upper
    tiene_y = "Y" in name_upper
    if tiene_x and not tiene_y:
        caso = "SPX"
    elif tiene_y and not tiene_x:
        caso = "SPY"
    else:
        raise InvalidInput(
            "No se pudo determinar el sentido (X/Y) a partir del nombre del Pier. "
            "Use un nombre que contenga solo 'X' o solo 'Y'."
        )

    df = df[df["outputcase"].astype(str).str.upper() == caso]
    if df.empty:
        raise InvalidInput(
            f"No se encontraron filas en 'Pier Forces' para Pier='{pier_filtro}' y OutputCase='{caso}'."
        )

    df["M3_num"] = df["m3"].astype(float)
    df_group = df.groupby("story", as_index=False)["M3_num"].max()

    # Leer alturas reales de entrepiso desde Story Definitions
    story_df = get_table("Story Definitions", log=True)
    if story_df is None or story_df.empty:
        raise InvalidInput(
            "No se pudo leer la tabla 'Story Definitions' desde ETABS para obtener alturas."
        )
    story_df = story_df.copy()
    story_df.columns = [str(c).strip().lower() for c in story_df.columns]
    if "story" not in story_df.columns or "height" not in story_df.columns:
        raise InvalidInput(
            "La tabla 'Story Definitions' no contiene columnas 'Story' y 'Height'. "
            "Revise la configuración de ETABS."
        )

    # Mapa Story -> (height, elevation opcional)
    alturas: dict[str, float] = {}
    elevaciones: dict[str, float] = {}
    for _, fila in story_df.iterrows():
        story_name = str(fila["story"])
        try:
            h_val = float(fila["height"])
        except (TypeError, ValueError):
            continue
        alturas[story_name] = h_val
        if "elevation" in story_df.columns:
            try:
                elevaciones[story_name] = float(fila["elevation"])
            except (TypeError, ValueError):
                pass

    # Ordenar stories por elevación (si existe) o por nombre numérico
    stories = df_group["story"].astype(str).tolist()
    if elevaciones:
        stories_sorted = sorted(
            stories,
            key=lambda s: elevaciones.get(s, 0.0),
        )
    else:
        try:
            stories_sorted = sorted(
                stories,
                key=lambda s: float(
                    "".join(ch for ch in str(s) if (ch.isdigit() or ch == ".")) or "0"
                ),
            )
        except Exception:
            stories_sorted = sorted(stories)

    niveles = []
    for story in stories_sorted:
        fila = df_group[df_group["story"].astype(str) == story].iloc[0]
        Mu = float(fila["M3_num"])
        hm_val = alturas.get(str(story), 0.0)
        if hm_val <= 0.0:
            raise InvalidInput(
                f"No se encontró altura válida para el Story '{story}' en Story Definitions."
            )
        niveles.append({"nivel": str(story), "hm": hm_val, "Mu": abs(Mu)})

    if not niveles:
        raise InvalidInput("No se obtuvieron momentos M3 ni alturas para el Pier indicado.")

    data = {"L": L, "fy": fy, "phi": phi, "H_inicial": 0.0, "niveles": niveles}
    result = run("predimension", "muro_nucleo", data)
    resultados = result.get("resultados", [])
    if not resultados:
        raise InvalidInput("No se generaron resultados de predimensionamiento desde ETABS.")

    for fila in resultados:
        fila["muro"] = nombre_muro
        fila["L"] = L
        fila["fy"] = fy
        fila["phi"] = phi

    results_dir = _get_muros_results_dir(project_path)
    file_name = _sanitize_name(nombre_muro) + ".csv"
    out_path = write_results_csv(
        project_path, f"muros_nucleo/{file_name}", resultados
    )

    for i, fila in enumerate(resultados):
        fila["N"] = str(i + 1)
    cols = [
        "N",
        "muro",
        "nivel",
        "H_total",
        "H_L",
        "tipo_muro",
        "tipo_falla",
        "Mu",
        "z",
        "As",
    ]
    tabla = format_table(resultados, columns=cols)
    return (
        f"Predimensionamiento de muro '{nombre_muro}' desde ETABS (Pier '{pier_filtro}', {caso})\n\n"
        + tabla
        + f"\n\nResultados guardados en: {out_path}"
    )

