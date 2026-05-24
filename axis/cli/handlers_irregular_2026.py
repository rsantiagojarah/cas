"""CLI irregularidades E.030 2026 (Tablas 11 y 12)."""

from __future__ import annotations

from axis.cli.handlers_irregular import CFG_2026, dispatch_irregular


def handle_irregular_2026(args: list[str]) -> str:
    """cas irregular 2026 <tipo> ... — verificacion con criterios E.030 2026."""
    return dispatch_irregular(args, CFG_2026)
