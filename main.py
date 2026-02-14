"""Punto de entrada: python main.py <scope> <operation> [args]."""

import sys
from pathlib import Path

# Asegurar que axis esté en el path
_root = Path(__file__).resolve().parent
sys.path.insert(0, str(_root))

from axis.cli.cli import main

if __name__ == "__main__":
    sys.exit(main())
