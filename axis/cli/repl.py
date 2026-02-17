"""REPL interactivo estilo Cursor CLI: menú /, flechas, tema transparente. Reglas: ≤200 líneas, ≤150 chars."""

from __future__ import annotations

import os
import sys

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.layout.controls import UIContent
from prompt_toolkit.layout.menus import CompletionsMenuControl
from prompt_toolkit.shortcuts import CompleteStyle
from prompt_toolkit.styles import Style

from axis.core.project import get_active_project
from axis.cli.handlers import get_base_path

REPL_EXIT = frozenset({"exit", "quit", "q"})

SLASH_COMMANDS = [
    ("help", "/help", "Ayuda general o por comando"),
    ("new ", "/new <project>", "Crear y activar proyecto"),
    ("use ", "/use <project>", "Activar proyecto"),
    ("sessions ls", "/sessions ls", "Listar proyectos (sesiones)"),
    ("resume ", "/resume [project]", "Reanudar sesión o activar otra"),
    ("tree", "/tree", "Estructura del proyecto"),
    ("info", "/info", "Proyecto activo"),
    ("add viga ", "/add viga <...>", "Añadir viga: nombre fc fy b h rec Mu [Vu]"),
    ("list vigas", "/list vigas", "Ver vigas del proyecto"),
    ("edit viga ", "/edit viga <i> <param> <valor>", "Editar viga por índice"),
    ("edit columna ", "/edit columna <param> <valor> [i1 i2 ...]", "Editar columna"),
    ("delete viga ", "/delete viga <i> [i2 i3 ...]", "Eliminar viga(s)"),
    ("flexion viga", "/flexion viga", "Diseño por flexión"),
    ("cortante viga", "/cortante viga", "Diseño por cortante"),
    ("results flexion", "/results flexion", "Ver resultados flexión"),
    ("results cortante", "/results cortante", "Ver resultados cortante"),
    ("clear", "/clear", "Limpiar pantalla del REPL"),
    ("exit", "/exit", "Salir del REPL"),
]

CURSOR_STYLE = Style.from_dict({
    "": "#cccccc",
    "completion-menu": "#cccccc bg:default",
    "completion-menu.completion": "#cccccc bg:default",
    "completion-menu.completion.current": "#ffffff bold noreverse bg:default",
    "completion-menu.meta.completion": "#888888 bg:default",
    "completion-menu.meta.completion.current": "#ffffff bold noreverse bg:default",
    "scrollbar.background": "bg:default",
    "scrollbar.button": "bg:default",
})


def _menu_bullet() -> str:
    """Viñeta para cada comando (estilo Cursor)."""
    try:
        enc = (sys.stdout.encoding or "").lower()
        return "→ " if "utf" in enc else "> "
    except Exception:
        return "> "


def get_prompt() -> str:
    """Genera el prompt del REPL (estilo Cursor: →)."""
    try:
        arrow = "→" if sys.stdout.encoding and "utf" in sys.stdout.encoding.lower() else ">"
    except Exception:
        arrow = ">"
    active = get_active_project(get_base_path())
    if active:
        return f"{arrow} CAS ({active}) "
    return f"{arrow} "


class SlashCompleter(Completer):
    """Completer para /: menú vertical estilo Cursor (descripción al costado, viñeta)."""

    def get_completions(self, document, complete_event):
        text = document.text.strip()
        if not text.startswith("/") and not text.startswith("／"):
            return
        frag = text[1:].strip()
        for insert_text, display_text, desc in SLASH_COMMANDS:
            if frag and not insert_text.strip().lower().startswith(frag.lower()):
                continue
            display_with_bullet = f"{_menu_bullet()}{display_text}"
            yield Completion(
                insert_text,
                start_position=-len(text),
                display=display_with_bullet,
                display_meta=desc,
                selected_style="#ffffff bold",
            )


def clear_repl_screen() -> None:
    """Limpia la pantalla del REPL (cross-platform)."""
    os.system("cls" if sys.platform == "win32" else "clear")


def get_slash_commands_text() -> str:
    """Lista formateada de comandos / (estilo Cursor CLI)."""
    lines = ["\nComandos disponibles:\n"]
    for _, display_text, desc in SLASH_COMMANDS:
        lines.append(f"  {display_text:<35} {desc}")
    return "\n".join(lines) + "\n"


def _create_content_no_cursor(original_create_content):
    """Wrapper que oculta cursor en menú de completado (solo resaltar letras)."""
    def wrapper(self, width: int, height: int) -> UIContent:
        content = original_create_content(self, width, height)
        if content.line_count:
            return UIContent(
                get_line=content.get_line,
                line_count=content.line_count,
                cursor_position=content.cursor_position,
                menu_position=content.menu_position,
                show_cursor=False,
            )
        return content
    return wrapper


def run_repl(parse_and_execute_fn):
    """Modo interactivo REPL con menú / y flechas. parse_and_execute_fn(argv) -> str."""
    original = CompletionsMenuControl.create_content
    CompletionsMenuControl.create_content = _create_content_no_cursor(original)
    try:
        _run_repl_loop(parse_and_execute_fn)
    finally:
        CompletionsMenuControl.create_content = original


def _run_repl_loop(parse_and_execute_fn):
    """Bucle principal del REPL."""
    print("CAS - Motor de diseño estructural")
    print("Modo interactivo. Escriba / para ver comandos (navegue con flechas), 'exit' para salir.\n")
    session = PromptSession(
        completer=SlashCompleter(),
        complete_while_typing=True,
        complete_style=CompleteStyle.COLUMN,
        enable_history_search=False,
        reserve_space_for_menu=0,
        show_frame=False,
        style=CURSOR_STYLE,
        bottom_toolbar=None,
    )
    while True:
        try:
            line = session.prompt(get_prompt()).strip()
        except EOFError:
            print()
            break
        if not line:
            continue
        if line.strip() in ("/", "／"):
            continue
        if line.startswith("/") or line.startswith("／"):
            line = line[1:].strip()
            if not line:
                continue
        tokens = line.split()
        cmd = tokens[0].lower()
        if cmd in REPL_EXIT:
            break
        if cmd in ("clear", "cls"):
            clear_repl_screen()
            continue
        argv = ["cas"] + tokens
        try:
            output = parse_and_execute_fn(argv)
            print(output)
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
