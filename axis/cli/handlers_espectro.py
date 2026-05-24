"""CLI: cas espectro — exportar espectro E.030 2026 para ETABS."""

from __future__ import annotations

from pathlib import Path

from axis.core.exceptions import InvalidInput
from axis.cli.file_picker import seleccionar_ruta_guardado
from axis.cli.tables import format_table
from axis.cli.colors import heading, dim, yellow
from axis.sismico.espectro_etabs_2026 import generar_filas_sa, serializar_tabla_etabs
from axis.sismico.etapa2_edificio import coeficiente_reduccion_r

R0_VALIDOS = (8, 7, 6, 5, 4, 3.5, 3)


def handle_espectro(args: list[str]) -> str:
    """
  cas espectro Z U S Tp Tl Ia Ip R

  Genera archivo ETABS (Periodo, Sa/g) con Sa = Z*U*S*C/R.
  R = R0 estructural; R_ef = R0*Ia*Ip.
  """
    if not args or args[0].lower() in ("help", "-h", "--help"):
        return _espectro_help()
    if len(args) != 8:
        raise InvalidInput(
            "Uso: cas espectro Z U S Tp Tl Ia Ip R\n"
            "Ej: cas espectro 0.35 1.0 1.15 0.6 3.0 1.0 1.0 8"
        )
    try:
        z, u, s, tp, tl, ia, ip, r0 = (float(args[i]) for i in range(8))
    except ValueError:
        raise InvalidInput("Todos los parametros deben ser numericos.")
    if r0 not in R0_VALIDOS:
        raise InvalidInput("R debe ser 8, 7, 6, 5, 4, 3.5 o 3 (R0 estructural).")
    if z <= 0 or u <= 0 or s <= 0:
        raise InvalidInput("Z, U y S deben ser mayores que 0.")
    if ia <= 0 or ip <= 0:
        raise InvalidInput("Ia e Ip deben ser mayores que 0.")
    if tl <= tp:
        raise InvalidInput("Tl debe ser mayor que Tp (Tabla 6 E.030 2026).")
    r_ef = coeficiente_reduccion_r(r0, ia, ip)
    try:
        filas = generar_filas_sa(z, u, s, tp, tl, r_ef)
    except ValueError as exc:
        raise InvalidInput(str(exc)) from exc
    ruta = seleccionar_ruta_guardado(
        titulo="Guardar espectro ETABS E.030 2026",
        archivo_inicial="espectro_etabs_2026.txt",
        extension_defecto=".txt",
        tipos_archivo=[("Texto Unicode", "*.txt"), ("Todos los archivos", "*.*")],
    )
    salidas = [
        heading("ESPECTRO E.030 2026 — EXPORTACION ETABS\n") + dim("=" * 50),
        dim(
            f"Z={z:.4f}, U={u:.4f}, S={s:.4f}, Tp={tp:.4f}, Tl={tl:.4f}, "
            f"Ia={ia:.4f}, Ip={ip:.4f}, R0={r0:g}, R_ef={r_ef:.4f}"
        ),
        dim("Sa/g = Z * U * S * C(T) / R_ef  |  Archivo: 2 columnas sin cabecera (Header Lines to Skip = 0)."),
        format_table(filas),
    ]
    if ruta is None:
        salidas.append(yellow("Guardado cancelado. No se genero archivo."))
        return "\n\n".join(salidas)
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(serializar_tabla_etabs(filas), encoding="ascii")
    salidas.append(dim(f"Archivo ETABS guardado en: {ruta}"))
    return "\n\n".join(salidas)


def _espectro_help() -> str:
    return (
        "Espectro de diseno E.030 2026 para importar en ETABS:\n"
        "  cas espectro Z U S Tp Tl Ia Ip R\n\n"
        "  Z   factor de zona (ej. 0.35 zona 3)\n"
        "  U   factor de uso (ej. 1.0 categoria C)\n"
        "  S   factor de suelo\n"
        "  Tp  periodo del perfil de suelo (s)\n"
        "  Tl  periodo largo del perfil (s)\n"
        "  Ia  irregularidad en altura\n"
        "  Ip  irregularidad en planta\n"
        "  R   R0 estructural: 8 | 7 | 6 | 5 | 4 | 3.5 | 3\n\n"
        "  R_ef = R * Ia * Ip\n"
        "  Sa/g = Z * U * S * C(T) / R_ef\n\n"
        "  Periodos (s): 0, 0.1, ..., 1, 1.2, 1.5, 1.7, 2, 2.5, 3, 3.5, 4, 5, 8, 11, 15\n\n"
        "Ej: cas espectro 0.35 1.0 1.15 0.6 3.0 1.0 1.0 8"
    )
