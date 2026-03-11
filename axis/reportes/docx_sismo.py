"""
Genera reporte Word del análisis sísmico E.030 a partir de las partes Markdown.
Estilo: Arial Narrow títulos, Consolas cuerpo (tablas ASCII), A4, márgenes 1".
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Tuple

try:
    from docx import Document
    from docx.shared import Inches, Pt, Cm
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False


def _parse_md_parte(parte: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Parsea una parte del markdown.
    Retorna (tipo, titulo, cuerpo):
    - tipo "h1": titulo principal (primera parte que empieza con "# ")
    - tipo "h2": titulo "## N - ..." y cuerpo (contenido de ```text...```)
    """
    parte = parte.strip()
    if not parte:
        return None, None, None
    if parte.startswith("# "):
        titulo = parte.split("\n", 1)[0].replace("# ", "").strip()
        return "h1", titulo, None
    if parte.startswith("## "):
        lineas = parte.split("\n", 1)
        titulo = lineas[0].replace("## ", "").strip()
        resto = lineas[1].strip() if len(lineas) > 1 else ""
        # Extraer cuerpo de ```text\n...\n```
        if "```text" in resto:
            idx = resto.index("```text")
            cuerpo = resto[idx + 7:].strip()  # tras ```text
            if cuerpo.endswith("```"):
                cuerpo = cuerpo[: cuerpo.rfind("```")].rstrip()
        else:
            cuerpo = resto
        return "h2", titulo, cuerpo if cuerpo else None
    return None, None, None


def generar_docx_sismo(md_partes: List[str], ruta_salida: str) -> Optional[str]:
    """
    Genera un documento Word a partir de las partes Markdown del análisis sismo.
    Estilo: Arial Narrow (títulos), Consolas 9pt (cuerpo/tablas), A4, márgenes 1".
    Retorna ruta_salida si ok, None si falla (ej. python-docx no instalado).
    """
    if not DOCX_AVAILABLE:
        return None
    if not md_partes:
        return None
    try:
        doc = Document()
        for section in doc.sections:
            section.page_width = Cm(21.0)
            section.page_height = Cm(29.7)
            section.top_margin = Inches(1)
            section.bottom_margin = Inches(1)
            section.left_margin = Inches(1)
            section.right_margin = Inches(1)
        for parte in md_partes:
            tipo, titulo, cuerpo = _parse_md_parte(parte)
            if tipo == "h1":
                p = doc.add_paragraph()
                run = p.add_run(titulo)
                run.font.name = "Arial Narrow"
                run.font.size = Pt(14)
                run.font.bold = True
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            elif tipo == "h2":
                p = doc.add_paragraph()
                run = p.add_run(titulo)
                run.font.name = "Arial Narrow"
                run.font.size = Pt(12)
                run.font.bold = True
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                if cuerpo:
                    p2 = doc.add_paragraph()
                    run2 = p2.add_run(cuerpo)
                    run2.font.name = "Consolas"
                    run2.font.size = Pt(9)
                    p2.alignment = WD_ALIGN_PARAGRAPH.LEFT
        doc.save(ruta_salida)
        return ruta_salida
    except Exception:
        return None
