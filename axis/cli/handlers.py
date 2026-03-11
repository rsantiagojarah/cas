"""Handlers CLI: proyecto (new, use, tree, info, help, list-projects, sessions, resume). ≤200 líneas."""

from __future__ import annotations

from pathlib import Path

from axis.core.project import (
    create_project,
    set_active_project,
    get_active_project,
    list_projects,
    get_active_project_path,
)
from axis.core.tree import get_project_tree, format_tree
from axis.core.context import get_global_config
from axis.core.exceptions import NoActiveProject, InvalidInput
from axis.cli.help_text import get_help_text


def get_base_path() -> Path:
    """Directorio base para proyectos (cwd)."""
    return Path.cwd()


def handle_new(args: list[str]) -> str:
    """cas new <project>"""
    if len(args) < 1:
        raise InvalidInput("Especifique el nombre del proyecto: cas new <project>")
    name = args[0]
    path = create_project(name, get_base_path())
    set_active_project(name, get_base_path())
    return f"Proyecto '{name}' creado y activado.\nRuta: {path}"


def handle_use(args: list[str]) -> str:
    """cas use <project>"""
    if len(args) < 1:
        raise InvalidInput("Especifique el proyecto: cas use <project>")
    set_active_project(args[0], get_base_path())
    return f"Proyecto activo: {args[0]}"


def handle_tree(args: list[str]) -> str:
    """cas tree"""
    return format_tree(get_project_tree(get_base_path()))


def handle_info(args: list[str]) -> str:
    """cas info"""
    config = get_global_config()
    active = config.get("active_project") or "Ninguno"
    path = config.get("project_path") or "-"
    return f"Proyecto activo: {active}\nRuta: {path}"


def handle_help(args: list[str]) -> str:
    """cas help [command]"""
    topic = args[0] if args else None
    return get_help_text(topic)


def handle_list_projects(args: list[str]) -> str:
    """cas list-projects"""
    projects = list_projects(get_base_path())
    if not projects:
        return "No hay proyectos. Use 'cas new <project>' para crear uno."
    return "Proyectos:\n  " + "\n  ".join(projects)


def handle_sessions_ls(args: list[str]) -> str:
    """cas sessions ls"""
    return handle_list_projects([])


def handle_resume(args: list[str]) -> str:
    """cas resume [project]"""
    if len(args) >= 1:
        return handle_use(args)
    active = get_active_project(get_base_path())
    if not active:
        raise NoActiveProject(
            "No hay sesión para reanudar. Use 'cas use <proyecto>' o 'cas new <proyecto>'."
        )
    return f"Sesión activa: {active}\nRuta: {get_active_project_path(get_base_path())}"
