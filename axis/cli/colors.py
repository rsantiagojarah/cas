"""
Formato estilo Git para output del CLI: colores ANSI, bold, dim.
Solo aplica color cuando stdout es TTY (como git).
Reglas: <=200 lineas, <=150 chars por linea.
"""

from __future__ import annotations

import sys

_RESET = "\033[0m"
_BOLD = "\033[1m"
_DIM = "\033[2m"
_RED = "\033[31m"
_GREEN = "\033[32m"
_YELLOW = "\033[33m"
_CYAN = "\033[36m"
_BOLD_CYAN = "\033[1;36m"


def _use_color() -> bool:
    """Activa color solo si la salida va a terminal (estilo git)."""
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


def _wrap(code: str, text: str) -> str:
    return f"{code}{text}{_RESET}" if _use_color() else text


def bold(text: str) -> str:
    return _wrap(_BOLD, text)


def dim(text: str) -> str:
    return _wrap(_DIM, text)


def cyan(text: str) -> str:
    return _wrap(_CYAN, text)


def bold_cyan(text: str) -> str:
    return _wrap(_BOLD_CYAN, text)


def green(text: str) -> str:
    return _wrap(_GREEN, text)


def red(text: str) -> str:
    return _wrap(_RED, text)


def yellow(text: str) -> str:
    return _wrap(_YELLOW, text)


def arrow(text: str) -> str:
    """Resalta línea con flecha tipo '--> valor'."""
    return cyan("--> ") + text


def ok(text: str) -> str:
    """Verde para cumple/si."""
    return green(text)


def fail(text: str) -> str:
    """Rojo para no cumple/no."""
    return red(text)


def heading(text: str) -> str:
    """Titulo de paso: Paso N - ..."""
    return bold_cyan(text)


def table_label(text: str) -> str:
    """Etiqueta de tabla (Tabla - ...)."""
    return dim(text)


def colorize_table(raw: str) -> str:
    """
    Aplica color sobrio: titulos de columnas en cyan, bordes en dim, datos sin alterar.
    """
    if not _use_color():
        return raw
    import re
    lines = raw.split("\n")
    out = []
    for i, line in enumerate(lines):
        is_border = bool(re.match(r"^[\s\+\-\=\|]+$", line))
        if is_border:
            out.append(_wrap(_DIM, line))
        elif i == 1:
            out.append(_wrap(_BOLD_CYAN, line))
        else:
            out.append(line)
    return "\n".join(out)
