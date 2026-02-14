"""Motor central que ejecuta operaciones registradas."""

from __future__ import annotations

from axis.core.registry import REGISTRY
from axis.core.exceptions import OperationNotRegistered


def run(scope: str, operation: str, data: dict | None = None) -> dict:
    """
    Ejecuta la operación registrada para (scope, operation).
    Recibe: scope, operation, data.
    Retorna el resultado de la función registrada.
    """
    key = (scope, operation)
    if key not in REGISTRY:
        raise OperationNotRegistered(
            f"Operación no registrada: scope='{scope}', operation='{operation}'"
        )
    func = REGISTRY[key]
    payload = data if data is not None else {}
    return func(payload)
