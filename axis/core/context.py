"""Manejo de contexto y configuración global."""

from __future__ import annotations

from pathlib import Path

from axis.core.project import get_active_project, get_active_project_path


def has_active_project(base_path: Path | None = None) -> bool:
    """Determina si existe un proyecto activo."""
    return get_active_project(base_path) is not None


def is_direct_calculation_mode(args: list[str]) -> bool:
    """
    Detecta si estamos en modo cálculo directo (parámetros pasados).
    Modo directo: cuando se pasan scope y operation explícitos.
    """
    if len(args) < 2:
        return False
    scope = args[0].lower()
    reserved = (
        "new", "use", "tree", "info", "list-projects", "add", "list", "edit",
        "flexion", "results"
    )
    return scope not in reserved


def get_global_config() -> dict:
    """Centraliza la configuración global del sistema."""
    return {
        "active_project": get_active_project(),
        "project_path": str(get_active_project_path()) if get_active_project_path() else None,
    }
