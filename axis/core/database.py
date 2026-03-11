"""Gestión de archivos CSV por tipo de elemento (vigas, columnas)."""

from __future__ import annotations

import csv
from pathlib import Path

from axis.core.exceptions import ProjectNotFound

ELEMENT_FIELDNAMES: dict[str, list[str]] = {
    "vigas": ["nombre", "fc", "fy", "b", "h", "rec", "Mu", "Vu"],
    "columnas": ["nombre", "fc", "fy", "b", "h", "rec", "Pu", "Mux", "Muy"],
    "muros_nucleo": ["nivel", "hm", "Mu"],
}


def _get_project_path(project_name: str, base_path: Path) -> Path:
    path = base_path / project_name
    if not path.exists():
        raise ProjectNotFound(f"Proyecto '{project_name}' no encontrado.")
    return path


def _get_elements_path(project_path: Path) -> Path:
    return project_path / "elements"


def _get_data_csv_path(project_path: Path, element_type: str = "vigas") -> Path:
    """Ruta del CSV del tipo de elemento: elements/vigas.csv o elements/columnas.csv."""
    return _get_elements_path(project_path) / f"{element_type}.csv"


def ensure_data_csv_exists(
    project_path: Path,
    element_type: str = "vigas",
    fieldnames: list[str] | None = None,
) -> Path:
    """Crea el CSV del tipo si no existe; escribe cabecera si está vacío."""
    elements_dir = _get_elements_path(project_path)
    elements_dir.mkdir(parents=True, exist_ok=True)
    csv_path = _get_data_csv_path(project_path, element_type)
    if not csv_path.exists():
        csv_path.touch()
    if fieldnames is None:
        fieldnames = ELEMENT_FIELDNAMES.get(element_type, ELEMENT_FIELDNAMES["vigas"])
    if csv_path.stat().st_size == 0:
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
    return csv_path


def read_csv(
    project_path: Path,
    element_type: str = "vigas",
) -> list[dict]:
    """Lee el CSV del tipo. Si element_type es vigas y no existe vigas.csv, intenta data.csv (migración)."""
    csv_path = _get_data_csv_path(project_path, element_type)
    fallback = _get_elements_path(project_path) / "data.csv" if element_type == "vigas" else None
    path_to_use = csv_path if csv_path.exists() else (fallback if fallback and fallback.exists() else None)
    if path_to_use is None:
        ensure_data_csv_exists(project_path, element_type)
        return []
    rows: list[dict] = []
    if path_to_use.stat().st_size == 0:
        return rows
    with open(path_to_use, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    return rows


def write_csv(
    project_path: Path,
    rows: list[dict],
    element_type: str = "vigas",
    fieldnames: list[str] | None = None,
) -> None:
    """Guarda en elements/<element_type>.csv."""
    if fieldnames is None:
        fieldnames = ELEMENT_FIELDNAMES.get(element_type, (rows[0].keys() if rows else []))
    csv_path = ensure_data_csv_exists(project_path, element_type, fieldnames)
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def get_data_csv_path(project_path: Path, element_type: str = "vigas") -> Path:
    return _get_data_csv_path(project_path, element_type)


def csv_exists(project_path: Path, element_type: str = "vigas") -> bool:
    return _get_data_csv_path(project_path, element_type).exists()


def write_results_csv(
    project_path: Path, filename: str, rows: list[dict], fieldnames: list[str] | None = None
) -> Path:
    """Guarda resultados en project_path/results/filename.csv."""
    results_dir = project_path / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    csv_path = results_dir / filename
    if rows and not fieldnames:
        fieldnames = list(rows[0].keys())
    elif not fieldnames:
        fieldnames = []
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return csv_path


def read_results_csv(project_path: Path, filename: str) -> list[dict]:
    csv_path = project_path / "results" / filename
    if not csv_path.exists():
        return []
    with open(csv_path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))
