"""Operación placeholder para probar la arquitectura."""

from axis.core.registry import register


@register("test", "run")
def test_operation(data: dict) -> dict:
    """Operación dummy para verificar que el núcleo funciona."""
    return {"status": "ok"}
