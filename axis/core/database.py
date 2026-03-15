"""Gestión de archivos CSV por tipo de elemento (vigas, columnas)."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from axis.core.exceptions import ProjectNotFound

ELEMENT_FIELDNAMES: dict[str, list[str]] = {
    "vigas": ["nombre", "fc", "fy", "b", "h", "rec", "Mu", "Vu"],
    "viga": ["nombre", "fc", "fy", "b", "h", "rec"],
    "viga_momentos": ["viga", "nombre", "Mu"],
    "viga_cortante": ["viga", "nombre", "Vu"],
    "losas": ["nombre", "fc", "fy", "b", "h", "rec", "Mu"],
    "losa": ["nombre", "fc", "fy", "b", "h", "rec"],
    "losa_momentos": ["losa", "nombre", "Mu"],
    "losa_cortante": ["losa", "nombre", "Vu"],
    "columnas": ["nombre", "fc", "fy", "b", "h", "rec", "Pu", "Mux", "Muy"],
    "muros_nucleo": ["nivel", "hm", "Mu"],
    "muros": [
        "nombre", "hm", "lm", "t", "fc", "fy", "fyt",
        "Pu", "Vu", "Mu", "delta_u", "c", "Mn_manual",
    ],
    "muros_def": ["nombre", "lm", "t", "fc", "fy", "fyt"],
    "muros_pisos": ["muro", "piso", "hm", "Pu", "Vu", "Mu", "Mn_manual", "c"],
    "col_props": [
        "Story", "Unique_Name", "k", "lu", "Ix", "Iy", "Ag", "Ec", "Bd", "fc", "fy",
    ],
    "col_esfuerzos": [
        "Story", "Unique_Name", "Station", "Output_Case", "Step_Type", "P", "M2", "M3",
    ],
    "col_story_forces": ["Story", "Output_Case", "P", "VX", "VY"],
    "col_drifts": ["Story", "Output_Case", "Drift"],
    "col_alturas": ["Story", "Height"],
    "col_factor_r": ["R_X", "R_Y"],
    "col_asignaciones": ["Unique_Name", "Diagrama_Nominal", "Diagrama_Ultimo"],
    "muro_asignaciones": ["muro", "Diagrama_Nominal", "Diagrama_Ultimo"],
    "ie_elementos": ["nombre", "caso", "b", "h", "d", "d_prima", "fc"],
    "ie_secciones": ["elemento", "seccion", "as_traccion", "as_compresion", "Ma"],
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


def write_json(project_path: Path, filename: str, data: object) -> Path:
    """Guarda datos JSON en elements/<filename>."""
    elements_dir = _get_elements_path(project_path)
    elements_dir.mkdir(parents=True, exist_ok=True)
    json_path = elements_dir / filename
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return json_path


def read_json(project_path: Path, filename: str) -> object:
    """Lee datos JSON desde elements/<filename>."""
    json_path = _get_elements_path(project_path) / filename
    if not json_path.exists():
        return None
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)
