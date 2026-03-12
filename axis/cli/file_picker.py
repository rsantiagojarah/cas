"""
Diálogo para seleccionar archivo de diagrama de interacción (Excel o CSV).
"""

from pathlib import Path
from typing import Optional

try:
    import tkinter as tk
    from tkinter import filedialog
    _TK_AVAILABLE = True
except Exception:
    _TK_AVAILABLE = False


def seleccionar_archivo_diagrama(
    titulo: str = "Seleccionar archivo (Excel o CSV)",
    directorio_inicial: Optional[str] = None,
) -> Optional[Path]:
    """
    Muestra un diálogo para seleccionar un archivo Excel o CSV de diagrama de interacción.

    Returns:
        Path del archivo seleccionado o None si se cancela.
    """
    if not _TK_AVAILABLE:
        return None
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    tipos_archivo = [
        ("Archivos Excel", "*.xlsx *.xls"),
        ("CSV", "*.csv"),
        ("Todos los archivos", "*.*"),
    ]
    try:
        archivo = filedialog.askopenfilename(
            title=titulo,
            initialdir=directorio_inicial,
            filetypes=tipos_archivo,
            defaultextension=".xlsx",
        )
        root.destroy()
        if archivo:
            return Path(archivo)
        return None
    except Exception:
        try:
            root.destroy()
        except Exception:
            pass
        return None
