"""
Graficación 3D de la superficie de interacción P-M2-M3.
ConvexHull (envolvente) + esfuerzos con tooltip al pasar el mouse (Pu, Mu, etc.).
"""

from __future__ import annotations

import math
from typing import List, Optional, Tuple

try:
    import numpy as np
    import matplotlib
    matplotlib.use("TkAgg")
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d import proj3d
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    from scipy.spatial import ConvexHull
    _PLOT_AVAILABLE = True
except ImportError:
    _PLOT_AVAILABLE = False

from axis.cli.pm_plotter_utils import filter_points

P_RANGO = Tuple[float, float]

try:
    import mplcursors
    _MPLCURSORS_AVAILABLE = True
except ImportError:
    _MPLCURSORS_AVAILABLE = False


def _split_esfuerzos_p(
    puntos_esfuerzo: List[dict],
    p_rango: Optional[P_RANGO],
) -> tuple[List[dict], List[dict]]:
    if not p_rango:
        return list(puntos_esfuerzo), []
    p_min, p_max = p_rango
    dentro: List[dict] = []
    fuera: List[dict] = []
    for row in puntos_esfuerzo:
        p = float(row.get("P", row.get("p", 0)))
        if (p_min - 1e-4) <= p <= (p_max + 1e-4):
            dentro.append(row)
        else:
            fuera.append(row)
    return dentro, fuera


def _mu_equiv(row: dict) -> float:
    m2 = float(row.get("M2", row.get("m2", 0)))
    m3 = float(row.get("M3", row.get("m3", 0)))
    return math.sqrt(m2 ** 2 + m3 ** 2)


def _tooltip_esfuerzo(row: dict) -> str:
    """Texto del tooltip: columna, caso, Pu, Mu, M2, M3 (y Ratio si viene en row)."""
    p = float(row.get("P", row.get("p", 0)))
    m2 = float(row.get("M2", row.get("m2", 0)))
    m3 = float(row.get("M3", row.get("m3", 0)))
    mu = _mu_equiv(row)
    lineas: List[str] = []
    un = str(row.get("Unique_Name", "")).strip()
    caso = str(row.get("Load_Case", "")).strip()
    story = str(row.get("Story", "")).strip()
    if story or un or caso:
        pref = " | ".join(x for x in (story, f"Col {un}" if un else "", caso) if x)
        lineas.append(pref)
    lineas.append(f"Pu = {p:.4f} Tn")
    lineas.append(f"Mu = {mu:.4f} Tn·m")
    lineas.append(f"M2 = {m2:.4f} Tn·m  |  M3 = {m3:.4f} Tn·m")
    ratio = row.get("Ratio")
    if ratio is not None and str(ratio).strip() not in ("", "None"):
        lineas.append(f"Ratio = {ratio}")
    return "\n".join(lineas)


def _scatter_esfuerzos(
    ax,
    rows: List[dict],
    *,
    color: str,
    label: str,
    size: int = 100,
):
    """Dibuja esfuerzos; retorna (artist, rows) para tooltips."""
    if not rows:
        return None, []
    p_esf = [float(r.get("P", r.get("p", 0))) for r in rows]
    m2_esf = [float(r.get("M2", r.get("m2", 0))) for r in rows]
    m3_esf = [float(r.get("M3", r.get("m3", 0))) for r in rows]
    artist = ax.scatter(
        m3_esf, m2_esf, [-p for p in p_esf],
        color=color, marker="o", s=size, zorder=10, alpha=0.9,
        label=label, picker=True, pickradius=12,
        edgecolors="black" if color == "darkorange" else "darkred",
        linewidths=1.5,
    )
    return artist, rows


def _cursor_sobre_punto(capas: List[tuple], event) -> bool:
    """True si el mouse está sobre algún punto de esfuerzo."""
    if event.x is None or event.y is None:
        return False
    for artist, rows in capas:
        if artist is None or not rows:
            continue
        try:
            cont, ind = artist.contains(event)
            if cont and ind is not None and len(ind.get("ind", [])) > 0:
                return True
        except Exception:
            pass
    return False


def _attach_hover_mplcursors(capas: List[tuple], state: dict) -> list:
    """Tooltips con mplcursors (fiable en 3D). Retorna lista de cursores."""
    if not _MPLCURSORS_AVAILABLE:
        return []
    cursors: list = []
    for artist, rows in capas:
        if artist is None or not rows:
            continue
        labels = [_tooltip_esfuerzo(r) for r in rows]
        cursor = mplcursors.cursor(artist, hover=True)
        cursors.append(cursor)

        @cursor.connect("add")
        def _on_add(sel, labels=labels, cursor=cursor):
            if state.get("suppressed"):
                _quitar_seleccion_mplcursors(cursor, sel)
                return
            i = sel.index
            if i is not None and 0 <= i < len(labels):
                sel.annotation.set_text(labels[i])
            bbox = sel.annotation.get_bbox_patch()
            if bbox is not None:
                bbox.set(facecolor="wheat", edgecolor="gray", alpha=0.95)
            sel.annotation.set_fontsize(9)

    return cursors


def _quitar_seleccion_mplcursors(cursor, sel) -> None:
    """Quita una selección con la API oficial (no tocar annotation.remove)."""
    try:
        cursor.remove_selection(sel)
    except (ValueError, KeyError, RuntimeError):
        pass


def _limpiar_selecciones_mplcursors(cursors: list) -> None:
    """Vacía selecciones sin usar la propiedad .selections (evita RuntimeError)."""
    for cur in cursors:
        for sel in list(getattr(cur, "_selections", ())):
            _quitar_seleccion_mplcursors(cur, sel)


def _es_tecla_escape(event) -> bool:
    k = (getattr(event, "key", None) or "").lower()
    return k in ("escape", "esc")


def _activar_supresion_tooltips(fig, cursors: list, state: dict) -> None:
    """Oculta todos los tooltips y bloquea hover hasta salir de los puntos."""
    state["suppressed"] = True
    _limpiar_selecciones_mplcursors(cursors)
    for cur in cursors:
        cur.enabled = False
    ann = state.get("fallback_annot")
    if ann is not None:
        ann.set_visible(False)
    fig.canvas.draw_idle()


def _attach_esc_dismiss_tooltips(
    fig,
    capas: List[tuple],
    cursors: list,
    state: dict,
) -> None:
    """ESC: oculta datos; se reactiva al alejar el mouse de todos los puntos."""

    def on_key(event):
        if not _es_tecla_escape(event):
            return
        _activar_supresion_tooltips(fig, cursors, state)

    def on_motion_mientras_suprimido(event):
        if not state.get("suppressed"):
            return
        for cur in cursors:
            cur.enabled = False
        ann = state.get("fallback_annot")
        if ann is not None:
            ann.set_visible(False)
        if not _cursor_sobre_punto(capas, event):
            state["suppressed"] = False
            for cur in cursors:
                cur.enabled = True
            fig.canvas.draw_idle()

    fig.canvas.mpl_connect("key_press_event", on_key)
    fig.canvas.mpl_connect("motion_notify_event", on_motion_mientras_suprimido)

    # TkAgg (Windows): ESC aunque el foco no esté en el canvas de matplotlib
    try:
        win = fig.canvas.manager.window
        win.bind("<Escape>", lambda _e: _activar_supresion_tooltips(fig, cursors, state))
    except Exception:
        pass


def _attach_hover_tooltips_fallback(
    fig,
    ax,
    capas: List[tuple],
    state: dict,
) -> None:
    """
    Fallback sin mplcursors: picker + etiqueta junto al cursor (píxeles de figura).
    """
    annot = fig.annotate(
        "",
        xy=(0, 0),
        xycoords="figure pixels",
        xytext=(14, 14),
        textcoords="offset pixels",
        bbox=dict(boxstyle="round,pad=0.45", fc="wheat", ec="gray", alpha=0.95),
        fontsize=9,
        visible=False,
        zorder=200,
    )
    state["fallback_annot"] = annot

    def on_motion(event):
        if event.x is None or event.y is None:
            return
        if state.get("suppressed"):
            if not _cursor_sobre_punto(capas, event):
                state["suppressed"] = False
            if annot.get_visible():
                annot.set_visible(False)
                fig.canvas.draw_idle()
            return
        encontrado = False
        for artist, rows in capas:
            if artist is None or not rows:
                continue
            try:
                cont, ind = artist.contains(event)
            except Exception:
                cont, ind = False, None
            if not cont or ind is None or len(ind.get("ind", [])) == 0:
                continue
            idx = int(ind["ind"][0])
            if idx < 0 or idx >= len(rows):
                continue
            annot.xy = (event.x, event.y)
            annot.set_text(_tooltip_esfuerzo(rows[idx]))
            annot.set_visible(True)
            encontrado = True
            break
        if not encontrado and annot.get_visible():
            annot.set_visible(False)
        fig.canvas.draw_idle()

    fig.canvas.mpl_connect("motion_notify_event", on_motion)


def _attach_hover_tooltips(
    fig,
    ax,
    capas: List[tuple],
) -> None:
    """Tooltips al pasar el mouse; ESC oculta hasta salir de los puntos."""
    state: dict = {"suppressed": False, "fallback_annot": None}
    cursors = _attach_hover_mplcursors(capas, state)
    if not cursors:
        _attach_hover_tooltips_fallback(fig, ax, capas, state)
    _attach_esc_dismiss_tooltips(fig, capas, cursors, state)


def _dibujar_superficie_pm(
    ax,
    puntos_clean: List[dict],
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    m3_all = np.array([float(p["m3"]) for p in puntos_clean])
    m2_all = np.array([float(p["m2"]) for p in puntos_clean])
    pu_all = np.array([float(p["p"]) for p in puntos_clean])

    if len(puntos_clean) >= 4:
        try:
            pts_hull = np.column_stack([m3_all, m2_all, -pu_all])
            hull = ConvexHull(pts_hull)
            triangulos = []
            for simplex in hull.simplices:
                triangulo = [
                    [pts_hull[simplex[i]][0], pts_hull[simplex[i]][1], pts_hull[simplex[i]][2]]
                    for i in range(3)
                ]
                triangulos.append(triangulo)
            collection = Poly3DCollection(
                triangulos, alpha=0.22, edgecolor="navy", linewidths=0.25
            )
            colores = [-np.mean([v[2] for v in tri]) for tri in triangulos]
            collection.set_array(np.array(colores))
            collection.set_cmap("viridis_r")
            ax.add_collection3d(collection)
        except Exception:
            pass

    return m3_all, m2_all, pu_all


def _ajustar_ejes(
    ax,
    m3_all: np.ndarray,
    m2_all: np.ndarray,
    pu_all: np.ndarray,
    puntos_esfuerzo: Optional[List[dict]],
) -> None:
    ax.set_xlabel("M3 (Momento en Z)", fontsize=12, fontweight="bold")
    ax.set_ylabel("M2 (Momento en Y)", fontsize=12, fontweight="bold")
    ax.set_zlabel("P (Carga Axial)", fontsize=12, fontweight="bold")
    ax.grid(True, alpha=0.3)
    ax.set_xlim([m3_all.min(), m3_all.max()])
    ax.set_ylim([m2_all.min(), m2_all.max()])
    z_min, z_max = -float(pu_all.max()), -float(pu_all.min())
    if puntos_esfuerzo:
        p_esf = [float(r.get("P", r.get("p", 0))) for r in puntos_esfuerzo]
        if p_esf:
            z_min = min(z_min, -max(p_esf))
            z_max = max(z_max, -min(p_esf))
    ax.set_zlim([z_min, z_max])


def _dibujar_esfuerzos_con_hover(
    fig,
    ax,
    puntos_esfuerzo: List[dict],
    p_rango: Optional[P_RANGO],
) -> None:
    dentro, fuera = _split_esfuerzos_p(puntos_esfuerzo, p_rango)
    capas: List[tuple] = []
    art_d, rows_d = _scatter_esfuerzos(
        ax, dentro, color="red",
        label="Esfuerzos dentro del rango P del diagrama",
    )
    if art_d is not None:
        capas.append((art_d, rows_d))
    art_f, rows_f = _scatter_esfuerzos(
        ax, fuera, color="darkorange", size=140,
        label="Esfuerzos con Pu FUERA del rango del diagrama",
    )
    if art_f is not None:
        capas.append((art_f, rows_f))
    if capas:
        _attach_hover_tooltips(fig, ax, capas)


def plot_superficie_interaccion(
    puntos_diagrama: List[dict],
    titulo: str = "Superficie de Interacción",
    subtitulo: Optional[str] = None,
    puntos_esfuerzo: Optional[List[dict]] = None,
    p_rango: Optional[P_RANGO] = None,
) -> None:
    """
    Grafica la superficie de interacción 3D.

    p_rango: (P_min, P_max) del diagrama en Tn; esfuerzos fuera se marcan en naranja.
    Pase el mouse sobre un punto rojo/naranja (Pu, Mu, caso). ESC oculta el cuadro de datos.
    """
    if not _PLOT_AVAILABLE:
        raise RuntimeError(
            "Para graficar se necesitan matplotlib y scipy. Instale: pip install matplotlib scipy"
        ) from None
    if not puntos_diagrama:
        raise ValueError("No hay puntos del diagrama para graficar.")

    puntos_clean = filter_points(puntos_diagrama, remove_outliers=False)
    fig = plt.figure(figsize=(12, 9))
    ax = fig.add_subplot(111, projection="3d")

    m3_all, m2_all, pu_all = _dibujar_superficie_pm(ax, puntos_clean)

    title_str = titulo
    if subtitulo:
        title_str += f"\n{subtitulo}"
    ax.set_title(title_str, fontsize=14, fontweight="bold", pad=20)
    _ajustar_ejes(ax, m3_all, m2_all, pu_all, puntos_esfuerzo)

    if puntos_esfuerzo:
        _dibujar_esfuerzos_con_hover(fig, ax, puntos_esfuerzo, p_rango)

    ax.view_init(elev=20, azim=45)
    if puntos_esfuerzo:
        ax.legend(loc="best", fontsize=9)
    plt.tight_layout()
    try:
        fig.canvas.manager.set_window_title(
            str(fig.canvas.manager.get_window_title() or "Diagrama P-M")
            + "  |  ESC = ocultar datos"
        )
    except Exception:
        pass
    fig.canvas.draw_idle()
    plt.show()


def save_superficie_interaccion(
    puntos_diagrama: List[dict],
    output_path: str,
    titulo: str = "Superficie de Interacción",
    subtitulo: Optional[str] = None,
    puntos_esfuerzo: Optional[List[dict]] = None,
    p_rango: Optional[P_RANGO] = None,
) -> str:
    """Igual que plot_superficie_interaccion pero guarda PNG (sin tooltips)."""
    if not _PLOT_AVAILABLE:
        raise RuntimeError(
            "Para graficar se necesitan matplotlib y scipy. Instale: pip install matplotlib scipy"
        ) from None
    if not puntos_diagrama:
        raise ValueError("No hay puntos del diagrama para graficar.")

    puntos_clean = filter_points(puntos_diagrama, remove_outliers=False)
    fig = plt.figure(figsize=(12, 9))
    ax = fig.add_subplot(111, projection="3d")

    m3_all, m2_all, pu_all = _dibujar_superficie_pm(ax, puntos_clean)

    title_str = titulo
    if subtitulo:
        title_str += f"\n{subtitulo}"
    ax.set_title(title_str, fontsize=14, fontweight="bold", pad=20)
    _ajustar_ejes(ax, m3_all, m2_all, pu_all, puntos_esfuerzo)

    if puntos_esfuerzo:
        dentro, fuera = _split_esfuerzos_p(puntos_esfuerzo, p_rango)
        _scatter_esfuerzos(
            ax, dentro, color="red",
            label="Esfuerzos dentro del rango P del diagrama",
        )
        _scatter_esfuerzos(
            ax, fuera, color="darkorange", size=140,
            label="Esfuerzos con Pu FUERA del rango del diagrama",
        )

    ax.view_init(elev=20, azim=45)
    if puntos_esfuerzo:
        ax.legend(loc="best", fontsize=9)
    plt.tight_layout()
    fig.savefig(output_path, dpi=200)
    plt.close(fig)
    return output_path
