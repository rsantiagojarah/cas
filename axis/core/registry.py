"""Sistema de registro dinámico de operaciones."""

from __future__ import annotations

from typing import Callable

REGISTRY: dict[tuple[str, str], Callable] = {}


def register(scope: str, operation: str) -> Callable:
    """Decora una función para registrarla en el REGISTRY."""

    def decorator(func: Callable) -> Callable:
        REGISTRY[(scope, operation)] = func
        return func

    return decorator
