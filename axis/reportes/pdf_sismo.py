"""
Genera reportes PDF para analisis sismico E.030.
Tipografia Times, tablas profesionales, secciones claras.
Reglas: <=200 lineas, <=150 chars por linea.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Any

from fpdf import FPDF
from fpdf.fonts import FontFace


def _list_to_rows(data: list[dict], cols: Optional[list[str]] = None) -> list[tuple]:
    """Convierte lista de dicts en filas (headers, *rows) para tabla fpdf."""
    if not data:
        return []
    cols = cols or list(data[0].keys())
    headers = tuple(cols)
    rows = [tuple(str(row.get(c, "")) for c in cols) for row in data]
    return [headers] + rows


def _df_to_rows(df, cols: Optional[list] = None) -> list[tuple]:
    """Convierte DataFrame en filas para tabla fpdf."""
    if df is None or (hasattr(df, "empty") and df.empty):
        return []
    df = df.fillna("")
    cols = cols or list(df.columns)
    headers = tuple(str(c) for c in cols)
    rows = [tuple(str(v) for v in row) for row in df[list(cols)].values.tolist()]
    return [headers] + rows


class PDFSismo(FPDF):
    """PDF con tipografia Times, margenes, secciones y tablas."""

    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=20)
        self.set_margins(25, 20, 25)
        self.set_auto_page_break(True, 20)

    def header(self):
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(128)
        self.cell(0, 6, "Analisis Sismico E.030 - CAS", align="R")
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(128)
        self.cell(0, 10, f"Pag. {self.page_no()}", align="C")

    def section(self, titulo: str):
        self.set_font("Times", "B", 11)
        self.set_text_color(30, 60, 90)
        self.ln(6)
        self.cell(0, 8, titulo, ln=True)
        self.set_draw_color(200)
        self.set_line_width(0.3)
        self.ln(2)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(5)
        self.set_font("Times", "", 10)
        self.set_text_color(0)

    def tabla(self, rows: list[tuple], ancho_cols: Optional[tuple] = None):
        if not rows:
            return
        style = FontFace(fill_color=(240, 248, 255))
        with self.table(rows=rows, headings_style=style, text_align="CENTER", col_widths=ancho_cols) as t:
            pass
        self.ln(4)


def reporte_pdf_sismo(
    path_proyecto: str,
    sentido: str,
    zona: int,
    categoria: str,
    perfil: str,
    r0: float,
    ia: float,
    ip: float,
    material: str,
    z: float,
    u: float,
    s_val: float,
    r: float,
    tp: float,
    tl: float,
    periodo: float,
    filas_ct: list[dict],
    filas_espectro: list[dict],
    tbl_periodo: Optional[Any] = None,
    tbl_masa: Optional[Any] = None,
    tbl_peso: Optional[Any] = None,
    tbl_estatico: Optional[Any] = None,
    tbl_base_reactions: Optional[Any] = None,
    cumple_masa: bool = False,
    cort_est: float = 0,
    cort_din: float = 0,
    cumple_cort: bool = False,
    cort_basal: float = 0,
    cort_col: float = 0,
    cort_muros: float = 0,
    pct_col: float = 0,
    pct_muros: float = 0,
    sistema: str = "",
    drift_max: float = 0.007,
    tbl_drift: Optional[Any] = None,
    tbl_verif: Optional[Any] = None,
    cumple_drift: bool = False,
) -> str:
    """
    Genera PDF del analisis sismico E.030. Retorna ruta del archivo creado.
    """
    pdf = PDFSismo()
    pdf.add_page()
    pdf.set_font("Times", "B", 16)
    pdf.set_text_color(20, 50, 80)
    pdf.cell(0, 12, f"ANALISIS SISMICO E.030 - SENTIDO {sentido}", ln=True, align="C")
    pdf.set_font("Times", "", 10)
    pdf.set_text_color(0)
    pdf.ln(4)

    pdf.section("Paso 1 - Factor de Zona Sismica (Z)")
    pdf.cell(0, 6, f"Zona: {zona}  |  Factor Z: {z}", ln=True)
    pdf.ln(2)

    pdf.section("Paso 2 y 3 - Perfil de Suelo y Parametros")
    pdf.cell(0, 6, f"Perfil: {perfil.upper()}  |  S={s_val}  |  Tp={tp} s  |  Tl={tl} s", ln=True)
    pdf.ln(2)

    pdf.section("Paso 4 - Categoria y Espectro C vs T")
    pdf.cell(0, 6, f"Categoria: {categoria}  |  U={u}", ln=True)
    pdf.ln(2)

    pdf.section("Paso 6 a 8 - Sistema Estructural y Coeficiente R")
    pdf.cell(0, 6, f"R0={r0}  |  Ia={ia}  |  Ip={ip}  |  R = R0*Ia*Ip = {r}", ln=True)
    pdf.ln(2)

    pdf.section("Paso 9 - Periodo Fundamental")
    pdf.cell(0, 6, f"Periodo T (sentido {sentido}): {periodo:.4f} s", ln=True)
    if tbl_periodo is not None:
        try:
            rows = _df_to_rows(tbl_periodo)
            if rows:
                pdf.tabla(rows[:8])
        except Exception:
            pass
    pdf.ln(2)

    pdf.section("Paso 10 y 11 - Masa y Peso")
    pdf.cell(0, 6, f"Cumple masa >= 90%: {'Si' if cumple_masa else 'No'}", ln=True)
    if tbl_peso is not None:
        try:
            rows = _df_to_rows(tbl_peso)
            if rows:
                pdf.tabla(rows)
        except Exception:
            pass
    pdf.ln(2)

    pdf.section("Paso 12 - Analisis Estatico")
    if tbl_estatico is not None:
        try:
            rows = _df_to_rows(tbl_estatico)
            if rows:
                pdf.tabla(rows)
        except Exception:
            pass
    pdf.ln(2)

    pdf.section("Paso 13 - Espectro Sa")
    pdf.cell(0, 6, "Sa = (Z * U * C * S / R) * g", ln=True)
    rows_sa = _list_to_rows(filas_espectro[:15], ["T", "C", "Sa"])
    if rows_sa:
        pdf.tabla(rows_sa, ancho_cols=(1, 1, 1))
    pdf.ln(2)

    pdf.section("Paso 14 - Cortante Minima")
    pdf.cell(0, 6, f"Estatico: {abs(cort_est):.2f}  |  Dinamico: {abs(cort_din):.2f}", ln=True)
    pdf.cell(0, 6, f"Cumple >= 80%: {'Si' if cumple_cort else 'No'}", ln=True)
    pdf.ln(2)

    pdf.section("Paso 15 - Revision Hipotesis")
    rows_hip = [
        ("Elemento", "Cortante (Tn)", "% basal"),
        ("Cortante basal", f"{cort_basal:.2f}", "100%"),
        ("Columnas", f"{cort_col:.2f}", f"{pct_col:.1f}%"),
        ("Muros", f"{cort_muros:.2f}", f"{pct_muros:.1f}%"),
    ]
    pdf.tabla(rows_hip)
    pdf.cell(0, 6, f"Sistema clasificado: {sistema}", ln=True)
    pdf.ln(2)

    pdf.section("Paso 16 - Distorsion Admisible")
    pdf.cell(0, 6, f"Material: {material}  |  R: {r}  |  Drift max: {drift_max}", ln=True)
    pdf.cell(0, 6, f"Cumple: {'Si' if cumple_drift else 'No'}", ln=True)
    if tbl_verif is not None:
        try:
            rows = _df_to_rows(tbl_verif)
            if rows:
                pdf.tabla(rows[:12])
        except Exception:
            pass

    out_dir = Path(path_proyecto) / "results"
    out_dir.mkdir(parents=True, exist_ok=True)
    nombre = f"reporte_sismo_{sentido}.pdf"
    ruta = out_dir / nombre
    pdf.output(str(ruta))
    return str(ruta)
