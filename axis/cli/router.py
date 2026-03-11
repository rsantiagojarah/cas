"""Router CLI declarativo: despacha args al handler registrado. Reglas: ≤200 líneas, ≤150 chars."""

from __future__ import annotations

from typing import Any, Callable

from axis.core.context import is_direct_calculation_mode
from axis.engine.engine import run
from axis.cli.help_text import get_help_text


def dispatch(args: list[str], handlers: dict[str | tuple[str, ...], Callable[..., Any]]) -> str:
    """
    Despacha args al handler registrado en handlers.
    handlers: dict que mapea clave (str o tuple de 2 str) -> función.
    Si la clave es tuple ("add", "viga"), args deben empezar con ["add", "viga", ...].
    Retorna el resultado del handler o lanza si no hay match.
    """
    from axis.core.exceptions import InvalidInput
    if not args:
        return get_help_text()
    # Intentar dos palabras
    if len(args) >= 2:
        key2 = (args[0].lower(), args[1].lower())
        if key2 in handlers:
            fn = handlers[key2]
            return fn(args[2:]) if callable(fn) else str(fn(args[2:]))
    # Una palabra
    key1 = args[0].lower()
    if key1 in handlers:
        fn = handlers[key1]
        return fn(args[1:]) if callable(fn) else str(fn(args[1:]))
    if is_direct_calculation_mode(args):
        operation = args[1] if len(args) > 1 else ""
        return str(run(key1, operation, {}))
    raise InvalidInput(f"Comando desconocido: {key1}")
