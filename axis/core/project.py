"""Gestión de proyectos AXIS."""

from __future__ import annotations

import json
from pathlib import Path

from axis.core.exceptions import ProjectNotFound
from axis.core.database import ensure_data_csv_exists


def _get_workspace(base_path: Path | None) -> Path:
    """Obtiene la ruta del workspace (proyectos y axis_active_project.json)."""
    return base_path if base_path is not None else Path.cwd()


def _get_active_project_file(base_path: Path | None = None) -> Path:
    """Ruta del archivo axis_active_project.json."""
    return _get_workspace(base_path) / "axis_active_project.json"


def _read_active_project_file(base_path: Path | None = None) -> dict:
    """Lee el archivo de proyecto activo."""
    path = _get_active_project_file(base_path)
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _write_active_project_file(data: dict, base_path: Path | None = None) -> None:
    """Escribe el archivo de proyecto activo."""
    path = _get_active_project_file(base_path)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def create_project(name: str, base_path: Path | None = None) -> Path:
    """Crea un nuevo proyecto con la estructura requerida."""
    root = _get_workspace(base_path)
    project_path = root / name
    project_path.mkdir(parents=True, exist_ok=True)
    (project_path / "results").mkdir(exist_ok=True)
    (project_path / "reports").mkdir(exist_ok=True)
    ensure_data_csv_exists(project_path, "vigas")
    ensure_data_csv_exists(project_path, "columnas")
    config = {"name": name, "version": "1.0"}
    config_path = project_path / "axis_project.json"
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2)
    return project_path


def list_projects(base_path: Path | None = None) -> list[str]:
    """Lista los proyectos disponibles."""
    root = _get_workspace(base_path)
    projects = []
    for item in root.iterdir():
        if item.is_dir() and not item.name.startswith("."):
            config = item / "axis_project.json"
            if config.exists():
                projects.append(item.name)
    return sorted(projects)


def set_active_project(name: str, base_path: Path | None = None) -> None:
    """Establece el proyecto activo."""
    root = _get_workspace(base_path)
    project_path = root / name
    if not project_path.exists() or not (project_path / "axis_project.json").exists():
        raise ProjectNotFound(f"Proyecto '{name}' no encontrado.")
    _write_active_project_file({"active_project": name}, base_path)


def get_active_project(base_path: Path | None = None) -> str | None:
    """Obtiene el nombre del proyecto activo."""
    data = _read_active_project_file(base_path)
    name = data.get("active_project")
    if not name:
        return None
    root = _get_workspace(base_path)
    project_path = root / name
    if not project_path.exists():
        return None
    return name


def get_active_project_path(base_path: Path | None = None) -> Path | None:
    """Obtiene la ruta del proyecto activo."""
    name = get_active_project(base_path)
    if not name:
        return None
    root = _get_workspace(base_path)
    return root / name


def validate_project_structure(project_path: Path) -> bool:
    """Valida que el proyecto tenga la estructura correcta."""
    required = [
        project_path / "axis_project.json",
        project_path / "elements",
        project_path / "results",
        project_path / "reports",
    ]
    return all(p.exists() for p in required)
