"""Persistencia de analisis de irregularidades E.030."""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path


DEFAULT_STORE = "irregularidades.json"
STORE_2026 = "irregularidades_2026.json"


def _get_store_path(project_path: Path, store_name: str = DEFAULT_STORE) -> Path:
    return project_path / "results" / store_name


def _load_store(project_path: Path, store_name: str = DEFAULT_STORE) -> list[dict]:
    p = _get_store_path(project_path, store_name)
    if not p.exists():
        return []
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return data.get("analisis", [])
    except (json.JSONDecodeError, TypeError):
        return []


def _save_store(project_path: Path, analisis: list[dict], store_name: str = DEFAULT_STORE) -> None:
    p = _get_store_path(project_path, store_name)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"analisis": analisis}, indent=2, ensure_ascii=False), encoding="utf-8")


def guardar_analisis(
    project_path: Path,
    tipo: str,
    sentido: str,
    datos: list,
    factor: float,
    factor_tipo: str,
    filas: list[dict],
    metadata: dict | None = None,
    store_name: str = DEFAULT_STORE,
) -> str:
    """Guarda un analisis. Retorna id. metadata: dict opcional (ej. material para torsional)."""
    analisis = _load_store(project_path, store_name)
    aid = str(uuid.uuid4())[:8]
    rec = {
        "id": aid,
        "tipo": tipo,
        "sentido": sentido,
        "datos": datos,
        "factor": factor,
        "factor_tipo": factor_tipo,
        "filas": filas,
        "timestamp": datetime.now().isoformat(),
    }
    if metadata:
        rec["metadata"] = metadata
    analisis.append(rec)
    _save_store(project_path, analisis, store_name)
    return aid


def listar_analisis(
    project_path: Path,
    tipo: str | None = None,
    sentido: str | None = None,
    store_name: str = DEFAULT_STORE,
) -> list[dict]:
    """Lista analisis guardados, opcionalmente filtrados."""
    analisis = _load_store(project_path, store_name)
    if tipo:
        analisis = [a for a in analisis if a.get("tipo") == tipo]
    if sentido:
        analisis = [a for a in analisis if a.get("sentido", "").upper() == sentido.upper()]
    return analisis


def obtener_analisis(project_path: Path, aid: str, store_name: str = DEFAULT_STORE) -> dict | None:
    """Obtiene un analisis por id."""
    for a in _load_store(project_path, store_name):
        if a.get("id") == aid:
            return a
    return None


def eliminar_analisis(project_path: Path, aid: str, store_name: str = DEFAULT_STORE) -> bool:
    """Elimina un analisis. Retorna True si existia."""
    analisis = _load_store(project_path, store_name)
    nuevo = [a for a in analisis if a.get("id") != aid]
    if len(nuevo) == len(analisis):
        return False
    _save_store(project_path, nuevo, store_name)
    return True


def actualizar_analisis(
    project_path: Path,
    aid: str,
    tipo: str,
    sentido: str,
    datos: list,
    factor: float,
    factor_tipo: str,
    filas: list[dict],
    metadata: dict | None = None,
    store_name: str = DEFAULT_STORE,
) -> bool:
    """Reemplaza un analisis por id. Retorna True si existia."""
    analisis = _load_store(project_path, store_name)
    for i, a in enumerate(analisis):
        if a.get("id") == aid:
            rec = {
                "id": aid,
                "tipo": tipo,
                "sentido": sentido,
                "datos": datos,
                "factor": factor,
                "factor_tipo": factor_tipo,
                "filas": filas,
                "timestamp": datetime.now().isoformat(),
            }
            if metadata:
                rec["metadata"] = metadata
            analisis[i] = rec
            _save_store(project_path, analisis, store_name)
            return True
    return False
