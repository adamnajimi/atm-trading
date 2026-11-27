"""Arrêt d'urgence.

Trois façons d'arrêter le système, chacune suffit :
1. un fichier `KILL_SWITCH` à la racine du projet ;
2. la variable d'environnement `ATM_KILL_SWITCH=1` (variable GitHub Actions) ;
3. l'état `suspended` du portefeuille, posé par le gestionnaire de risques.
"""
from __future__ import annotations

import os
from pathlib import Path

KILL_FILE = "KILL_SWITCH"


def is_active(root: str | Path = ".") -> bool:
    if Path(root, KILL_FILE).exists():
        return True
    return os.environ.get("ATM_KILL_SWITCH", "").strip().lower() in ("1", "true", "yes", "on")


def activate(root: str | Path = ".", reason: str = "manuel") -> None:
    Path(root, KILL_FILE).write_text(f"{reason}\n", encoding="utf-8")
