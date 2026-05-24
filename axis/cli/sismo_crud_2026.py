"""Comandos list | show | delete | edit | report para sismo E.030 2026."""

from __future__ import annotations

from pathlib import Path

from axis.core.exceptions import InvalidInput
from axis.cli.colors import heading, dim, ok
from axis.cli.tables import format_table
from axis.sismico.sismo_persistencia_2026 import (
    eliminar_analisis_sismo,
    listar_analisis_sismo,
    obtener_analisis_sismo,
)


def _resumen_parametros(p: dict) -> str:
    modo = p.get("modo", "manual")
    base = (
        f"Sentido {p.get('sentido', '?')} | Z={p.get('zona')} U={p.get('categoria')} "
        f"perfil={p.get('perfil')} R={p.get('r0')} Ia={p.get('ia')} Ip={p.get('ip')} "
        f"Material={p.get('material')}"
    )
    if modo == "rapido":
        base += f" | cod_alt={p.get('cod_altura', '')} cod_planta={p.get('cod_planta', '')}"
    return base


def cmd_sismo_list(path: Path, args: list[str]) -> str:
    sentido = None
    if args:
        s = args[0].upper()
        if s not in ("X", "Y"):
            raise InvalidInput("Filtro de sentido debe ser X o Y.")
        sentido = s
    items = listar_analisis_sismo(path, sentido)
    if not items:
        return "No hay analisis sismicos 2026 guardados."
    filas = []
    for a in items:
        p = a.get("parametros", {})
        filas.append({
            "ID": a["id"],
            "Nombre": a.get("nombre") or p.get("nombre") or "-",
            "Sentido": p.get("sentido", ""),
            "Z": p.get("zona", ""),
            "U": p.get("categoria", ""),
            "Perfil": p.get("perfil", ""),
            "R": p.get("r0", ""),
            "Modo": p.get("modo", "manual"),
            "Fecha": str(a.get("timestamp", ""))[:19],
        })
    return heading("Analisis sismicos E.030 2026 guardados\n") + format_table(filas)


def cmd_sismo_show(path: Path, args: list[str]) -> str:
    aid = args[0] if args else None
    if not aid:
        items = listar_analisis_sismo(path)
        if not items:
            return "No hay analisis sismicos 2026 guardados."
        aid = items[-1]["id"]
    a = obtener_analisis_sismo(path, aid)
    if not a:
        return f"Analisis '{aid}' no encontrado."
    p = a.get("parametros", {})
    cab = heading(f"Analisis {a['id']}")
    if a.get("nombre") or p.get("nombre"):
        cab += f" — {a.get('nombre') or p.get('nombre')}"
    cab += f"\n{_resumen_parametros(p)}\n\n"
    texto = a.get("texto_consola", "")
    if not texto and a.get("md_partes"):
        texto = "\n\n".join(a["md_partes"])
    return cab + texto


def cmd_sismo_delete(path: Path, args: list[str]) -> str:
    if not args:
        raise InvalidInput("Uso: cas sismo 2026 delete <id>")
    if eliminar_analisis_sismo(path, args[0]):
        return f"Analisis '{args[0]}' eliminado."
    return f"Analisis '{args[0]}' no encontrado."


def cmd_sismo_edit(path: Path, args: list[str], ejecutar_manual, ejecutar_rapido) -> str:
    """
    cas sismo 2026 edit <id> <sentido> Z U perfil R Ia Ip Material [nombre]
    cas sismo 2026 edit <id> rapido <sentido> Z U perfil R Material <cod_alt> <cod_planta> [nombre]
    """
    if len(args) < 2:
        raise InvalidInput(
            "Uso: cas sismo 2026 edit <id> <sentido> Z U perfil R Ia Ip Material [nombre]\n"
            "  o: cas sismo 2026 edit <id> rapido <sentido> Z U perfil R Material <cod_alt> <cod_planta>"
        )
    aid = args[0]
    if not obtener_analisis_sismo(path, aid):
        return f"Analisis '{aid}' no encontrado."
    resto = args[1:]
    if resto[0].lower() == "rapido":
        return ejecutar_rapido(resto[1:], edit_id=aid)
    return ejecutar_manual(resto, edit_id=aid)


def cmd_sismo_report(path: Path, args: list[str]) -> str:
    from axis.reportes.docx_sismo import generar_docx_sismo

    items = listar_analisis_sismo(path)
    if not items:
        return "No hay analisis sismicos 2026 guardados para generar reporte."

    ultimos: dict[str, dict] = {}
    for a in items:
        sentido = a.get("parametros", {}).get("sentido", "X").upper()
        t_new = a.get("timestamp", "")
        t_old = ultimos.get(sentido, {}).get("timestamp", "")
        if sentido not in ultimos or t_new >= t_old:
            ultimos[sentido] = a
    analisis = [ultimos[s] for s in sorted(ultimos.keys())]

    sep = "\n\n" + dim("-" * 50) + "\n\n"
    titulo_rep = "REPORTE DE ANALISIS SISMICO E.030 2026"
    salidas = [heading(f"{titulo_rep}\n") + dim("=" * 50) + "\n"]
    md_partes = [f"# {titulo_rep}\n"]

    resumen = [
        {
            "ID": a["id"],
            "Nombre": a.get("nombre") or a.get("parametros", {}).get("nombre") or "-",
            "Sentido": a.get("parametros", {}).get("sentido", ""),
            "Parametros": _resumen_parametros(a.get("parametros", {})),
            "Fecha": str(a.get("timestamp", ""))[:19],
        }
        for a in analisis
    ]
    txt_resumen = heading("Resumen de analisis incluidos\n") + format_table(resumen)
    salidas.append(txt_resumen)
    md_partes.append(f"## Resumen de analisis incluidos\n\n```text\n{txt_resumen}\n```\n")

    for a in analisis:
        p = a.get("parametros", {})
        sentido = p.get("sentido", "?")
        bloque_titulo = heading(f"Analisis sentido {sentido} (id: {a['id']})\n") + dim(_resumen_parametros(p))
        texto = a.get("texto_consola", "")
        bloque = bloque_titulo + "\n\n" + texto if texto else bloque_titulo
        salidas.append(sep + bloque)
        md_partes.extend(a.get("md_partes", []))

    nombre = args[0].strip() if args else "general"
    nombre_limpio = "".join(c for c in nombre if c.isalnum() or c in ("-", "_")).strip() or "general"
    base = f"sismo_reporte_2026_{nombre_limpio}"
    results_dir = path / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    md_path = results_dir / f"{base}.md"
    docx_path = results_dir / f"{base}.docx"

    try:
        md_path.write_text("\n".join(md_partes), encoding="utf-8")
        docx_ok = generar_docx_sismo(md_partes, str(docx_path))
        msg = f"Reporte guardado en results/: '{base}.md'" + (f", '{base}.docx'" if docx_ok else "")
        salidas.append(sep + dim(msg))
    except Exception as e:
        salidas.append(sep + dim(f"No se pudo guardar reporte: {e}"))

    return "\n".join(salidas)
