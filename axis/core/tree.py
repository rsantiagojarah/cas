"""Visualización de la estructura del proyecto activo."""

from __future__ import annotations

from pathlib import Path

from axis.core.exceptions import NoActiveProject
from axis.core.project import get_active_project_path
from axis.core.database import read_csv, get_data_csv_path


def _collect_results(project_path: Path) -> list[str]:
    """Recopila archivos en results/."""
    results_dir = project_path / "results"
    if not results_dir.exists():
        return []
    return [f.name for f in results_dir.iterdir() if f.is_file()]


def _collect_reports(project_path: Path) -> list[str]:
    """Recopila archivos en reports/."""
    reports_dir = project_path / "reports"
    if not reports_dir.exists():
        return []
    return [f.name for f in reports_dir.iterdir() if f.is_file()]


def get_project_tree(base_path: Path | None = None) -> dict:
    """
    Lee la estructura del proyecto activo.
    Retorna: proyecto, archivos de data, resultados, reportes.
    """
    project_path = get_active_project_path(base_path)
    if not project_path:
        raise NoActiveProject("No hay proyecto activo. Use 'axis use <proyecto>'.")
    data_rows = read_csv(project_path)
    data_file = get_data_csv_path(project_path).name
    return {
        "project": project_path.name,
        "path": str(project_path),
        "data_files": [data_file],
        "data_rows_count": len(data_rows),
        "results": _collect_results(project_path),
        "reports": _collect_reports(project_path),
    }


def format_tree(tree: dict) -> str:
    """Formatea el árbol del proyecto para mostrar en CLI."""
    lines = [
        f"Proyecto: {tree['project']}",
        f"Ruta: {tree['path']}",
        "",
        "Data:",
    ]
    for f in tree["data_files"]:
        count = tree.get("data_rows_count", 0)
        lines.append(f"  - {f} ({count} filas)")
    lines.extend(["", "Resultados:"])
    for r in tree.get("results", []) or ["(ninguno)"]:
        lines.append(f"  - {r}")
    lines.extend(["", "Reportes:"])
    for r in tree.get("reports", []) or ["(ninguno)"]:
        lines.append(f"  - {r}")
    return "\n".join(lines)
