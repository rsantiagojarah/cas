"""Gestión de archivos CSV (data) del proyecto."""

from __future__ import annotations

import csv
from pathlib import Path

from axis.core.exceptions import ProjectNotFound


def _get_project_path(project_name: str, base_path: Path) -> Path:
    """Obtiene la ruta del proyecto."""
    path = base_path / project_name
    if not path.exists():
        raise ProjectNotFound(f"Proyecto '{project_name}' no encontrado.")
    return path


def _get_elements_path(project_path: Path) -> Path:
    """Obtiene la ruta de la carpeta elements."""
    return project_path / "elements"


def _get_data_csv_path(project_path: Path) -> Path:
    """Obtiene la ruta del archivo data.csv."""
    return _get_elements_path(project_path) / "data.csv"


def ensure_data_csv_exists(project_path: Path) -> Path:
    """Crea data.csv si no existe. Retorna la ruta del archivo."""
    elements_dir = _get_elements_path(project_path)
    elements_dir.mkdir(parents=True, exist_ok=True)
    csv_path = _get_data_csv_path(project_path)
    if not csv_path.exists():
        csv_path.touch()
    return csv_path


def read_csv(project_path: Path) -> list[dict]:
    """Lee el archivo data.csv del proyecto."""
    csv_path = _get_data_csv_path(project_path)
    ensure_data_csv_exists(project_path)
    rows: list[dict] = []
    if csv_path.stat().st_size == 0:
        return rows
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    return rows


def write_csv(project_path: Path, rows: list[dict], fieldnames: list[str] | None = None) -> None:
    """Guarda datos en data.csv del proyecto."""
    csv_path = ensure_data_csv_exists(project_path)
    if rows and not fieldnames:
        fieldnames = list(rows[0].keys())
    elif not fieldnames:
        fieldnames = []
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def get_data_csv_path(project_path: Path) -> Path:
    """Retorna la ruta del archivo data.csv."""
    return _get_data_csv_path(project_path)


def csv_exists(project_path: Path) -> bool:
    """Verifica si existe el archivo data.csv."""
    return _get_data_csv_path(project_path).exists()
