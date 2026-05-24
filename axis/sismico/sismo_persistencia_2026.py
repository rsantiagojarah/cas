"""Persistencia de analisis sismicos E.030 2026."""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path

STORE_SISMO_2026 = "sismo_analisis_2026.json"


def _get_store_path(project_path: Path) -> Path:
    return project_path / "results" / STORE_SISMO_2026


def _load_store(project_path: Path) -> list[dict]:
    p = _get_store_path(project_path)
    if not p.exists():
        return []
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return data.get("analisis", [])
    except (json.JSONDecodeError, TypeError):
        return []


def _save_store(project_path: Path, analisis: list[dict]) -> None:
    p = _get_store_path(project_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"analisis": analisis}, indent=2, ensure_ascii=False), encoding="utf-8")


def _nuevo_registro(
    parametros: dict,
    md_partes: list[str],
    texto_consola: str,
    aid: str | None = None,
) -> dict:
    rec = {
        "id": aid or str(uuid.uuid4())[:8],
        "parametros": parametros,
        "md_partes": md_partes,
        "texto_consola": texto_consola,
        "timestamp": datetime.now().isoformat(),
    }
    nombre = (parametros.get("nombre") or "").strip()
    if nombre:
        rec["nombre"] = nombre
    return rec


def guardar_analisis_sismo(
    project_path: Path,
    parametros: dict,
    md_partes: list[str],
    texto_consola: str,
) -> str:
    """Guarda un analisis. Retorna id."""
    analisis = _load_store(project_path)
    rec = _nuevo_registro(parametros, md_partes, texto_consola)
    analisis.append(rec)
    _save_store(project_path, analisis)
    return rec["id"]


def actualizar_analisis_sismo(
    project_path: Path,
    aid: str,
    parametros: dict,
    md_partes: list[str],
    texto_consola: str,
) -> bool:
    """Reemplaza un analisis por id."""
    analisis = _load_store(project_path)
    for i, a in enumerate(analisis):
        if a.get("id") == aid:
            analisis[i] = _nuevo_registro(parametros, md_partes, texto_consola, aid=aid)
            _save_store(project_path, analisis)
            return True
    return False


def listar_analisis_sismo(
    project_path: Path,
    sentido: str | None = None,
) -> list[dict]:
    analisis = _load_store(project_path)
    if sentido:
        analisis = [a for a in analisis if a.get("parametros", {}).get("sentido", "").upper() == sentido.upper()]
    return analisis


def obtener_analisis_sismo(project_path: Path, aid: str) -> dict | None:
    for a in _load_store(project_path):
        if a.get("id") == aid:
            return a
    return None


def eliminar_analisis_sismo(project_path: Path, aid: str) -> bool:
    analisis = _load_store(project_path)
    nuevo = [a for a in analisis if a.get("id") != aid]
    if len(nuevo) == len(analisis):
        return False
    _save_store(project_path, nuevo)
    return True
