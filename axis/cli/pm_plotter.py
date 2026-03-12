"""
Graficación 3D de la superficie de interacción P-M2-M3.
Idéntico a Diseño_Columnas/src/utils/pm_plotter.py: ConvexHull + puntos de esfuerzo (combinaciones).
"""

from __future__ import annotations

from typing import List, Optional

try:
    import numpy as np
    import matplotlib
    matplotlib.use("TkAgg")
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection
    from scipy.spatial import ConvexHull
    _PLOT_AVAILABLE = True
except ImportError:
    _PLOT_AVAILABLE = False

from axis.cli.pm_plotter_utils import filter_points


def plot_superficie_interaccion(
    puntos_diagrama: List[dict],
    titulo: str = "Superficie de Interacción",
    subtitulo: Optional[str] = None,
    puntos_esfuerzo: Optional[List[dict]] = None,
) -> None:
    """
    Grafica la superficie de interacción 3D con ConvexHull y opcionalmente
    los puntos de todas las combinaciones (P, M2, M3).

    puntos_diagrama: lista de dicts con "p", "m2", "m3", "angle" (P Tn, M Tn·m).
    titulo: título principal del gráfico.
    subtitulo: línea opcional bajo el título (ej. "[Story] UniqueName").
    puntos_esfuerzo: opcional, lista de dicts con "P", "M2", "M3" (combinaciones de carga).
    """
    if not _PLOT_AVAILABLE:
        raise RuntimeError(
            "Para graficar se necesitan matplotlib y scipy. Instale: pip install matplotlib scipy"
        ) from None

    if not puntos_diagrama:
        raise ValueError("No hay puntos del diagrama para graficar.")

    puntos_clean = filter_points(puntos_diagrama)
    m3_all = np.array([float(p["m3"]) for p in puntos_clean])
    m2_all = np.array([float(p["m2"]) for p in puntos_clean])
    pu_all = np.array([float(p["p"]) for p in puntos_clean])

    fig = plt.figure(figsize=(12, 9))
    ax = fig.add_subplot(111, projection="3d")

    # Superficie con ConvexHull (igual que Diseño_Columnas)
    if len(puntos_clean) >= 4:
        try:
            puntos = np.column_stack([m3_all, m2_all, -pu_all])
            hull = ConvexHull(puntos)
            triangulos = []
            for simplex in hull.simplices:
                triangulo = [
                    [puntos[simplex[i]][0], puntos[simplex[i]][1], puntos[simplex[i]][2]]
                    for i in range(3)
                ]
                triangulos.append(triangulo)
            collection = Poly3DCollection(
                triangulos, alpha=0.3, edgecolor="navy", linewidths=0.3
            )
            colores = []
            for triangulo in triangulos:
                z_inv = np.mean([v[2] for v in triangulo])
                colores.append(-z_inv)
            collection.set_array(np.array(colores))
            collection.set_cmap("viridis_r")
            ax.add_collection3d(collection)
        except Exception:
            ax.scatter(
                m3_all, m2_all, -pu_all,
                c=pu_all, cmap="viridis_r", s=30, alpha=0.4,
                edgecolors="none", label="Puntos del Diagrama",
            )

    # Ejes y título (igual que referencia)
    ax.set_xlabel("M3 (Momento en Z)", fontsize=12, fontweight="bold")
    ax.set_ylabel("M2 (Momento en Y)", fontsize=12, fontweight="bold")
    ax.set_zlabel("P (Carga Axial)", fontsize=12, fontweight="bold")
    title_str = titulo
    if subtitulo:
        title_str += f"\n{subtitulo}"
    ax.set_title(title_str, fontsize=14, fontweight="bold", pad=20)
    ax.grid(True, alpha=0.3)
    ax.set_xlim([m3_all.min(), m3_all.max()])
    ax.set_ylim([m2_all.min(), m2_all.max()])
    ax.set_zlim([-pu_all.max(), -pu_all.min()])

    # Puntos de todas las combinaciones (esfuerzos)
    p_esf = []
    m2_esf = []
    m3_esf = []
    if puntos_esfuerzo:
        for row in puntos_esfuerzo:
            p_esf.append(float(row.get("P", row.get("p", 0))))
            m2_esf.append(float(row.get("M2", row.get("m2", 0))))
            m3_esf.append(float(row.get("M3", row.get("m3", 0))))
    if p_esf:
        ax.scatter(
            m3_esf, m2_esf, [-p for p in p_esf],
            color="red", marker="o", s=100, zorder=10, alpha=0.9,
            label="Puntos de Esfuerzo (combinaciones)",
            edgecolors="darkred", linewidths=2.0,
        )
        z_min = min(pu_all.min(), min(p_esf))
        z_max = max(pu_all.max(), max(p_esf))
        ax.set_zlim([-z_max, -z_min])

    ax.view_init(elev=20, azim=45)
    if p_esf:
        ax.legend(loc="best", fontsize=9)
    plt.tight_layout()
    plt.show()


def save_superficie_interaccion(
    puntos_diagrama: List[dict],
    output_path: str,
    titulo: str = "Superficie de Interacción",
    subtitulo: Optional[str] = None,
    puntos_esfuerzo: Optional[List[dict]] = None,
) -> str:
    """
    Genera la misma grafica 3D que plot_superficie_interaccion, pero la guarda
    en 'output_path' (PNG) en lugar de mostrarla en pantalla.
    Retorna la ruta de salida si se pudo generar.
    """
    if not _PLOT_AVAILABLE:
        raise RuntimeError(
            "Para graficar se necesitan matplotlib y scipy. Instale: pip install matplotlib scipy"
        ) from None
    if not puntos_diagrama:
        raise ValueError("No hay puntos del diagrama para graficar.")

    puntos_clean = filter_points(puntos_diagrama)
    m3_all = np.array([float(p["m3"]) for p in puntos_clean])
    m2_all = np.array([float(p["m2"]) for p in puntos_clean])
    pu_all = np.array([float(p["p"]) for p in puntos_clean])

    fig = plt.figure(figsize=(12, 9))
    ax = fig.add_subplot(111, projection="3d")

    if len(puntos_clean) >= 4:
        try:
            puntos = np.column_stack([m3_all, m2_all, -pu_all])
            hull = ConvexHull(puntos)
            triangulos = []
            for simplex in hull.simplices:
                triangulo = [
                    [puntos[simplex[i]][0], puntos[simplex[i]][1], puntos[simplex[i]][2]]
                    for i in range(3)
                ]
                triangulos.append(triangulo)
            collection = Poly3DCollection(
                triangulos, alpha=0.3, edgecolor="navy", linewidths=0.3
            )
            colores = []
            for triangulo in triangulos:
                z_inv = np.mean([v[2] for v in triangulo])
                colores.append(-z_inv)
            collection.set_array(np.array(colores))
            collection.set_cmap("viridis_r")
            ax.add_collection3d(collection)
        except Exception:
            ax.scatter(
                m3_all, m2_all, -pu_all,
                c=pu_all, cmap="viridis_r", s=30, alpha=0.4,
                edgecolors="none", label="Puntos del Diagrama",
            )

    ax.set_xlabel("M3 (Momento en Z)", fontsize=12, fontweight="bold")
    ax.set_ylabel("M2 (Momento en Y)", fontsize=12, fontweight="bold")
    ax.set_zlabel("P (Carga Axial)", fontsize=12, fontweight="bold")
    title_str = titulo
    if subtitulo:
        title_str += f"\n{subtitulo}"
    ax.set_title(title_str, fontsize=14, fontweight="bold", pad=20)
    ax.grid(True, alpha=0.3)
    ax.set_xlim([m3_all.min(), m3_all.max()])
    ax.set_ylim([m2_all.min(), m2_all.max()])
    ax.set_zlim([-pu_all.max(), -pu_all.min()])

    p_esf = []
    m2_esf = []
    m3_esf = []
    if puntos_esfuerzo:
        for row in puntos_esfuerzo:
            p_esf.append(float(row.get("P", row.get("p", 0))))
            m2_esf.append(float(row.get("M2", row.get("m2", 0))))
            m3_esf.append(float(row.get("M3", row.get("m3", 0))))
    if p_esf:
        ax.scatter(
            m3_esf, m2_esf, [-p for p in p_esf],
            color="red", marker="o", s=100, zorder=10, alpha=0.9,
            label="Puntos de Esfuerzo (combinaciones)",
            edgecolors="darkred", linewidths=2.0,
        )
        z_min = min(pu_all.min(), min(p_esf))
        z_max = max(pu_all.max(), max(p_esf))
        ax.set_zlim([-z_max, -z_min])

    ax.view_init(elev=20, azim=45)
    if p_esf:
        ax.legend(loc="best", fontsize=9)
    plt.tight_layout()
    fig.savefig(output_path, dpi=200)
    plt.close(fig)
    return output_path
