"""Observabilité : journal d'événements structurés (JSON Lines, ajout seul).

Chaque événement correspond à une action technique réelle du système (téléchargement, décision,
contrôle de risque, ordre fictif, rapport). Rien n'est inventé : le tableau de bord ne lit que ce fichier
et les états du dépôt.
"""
from __future__ import annotations

import json
import time
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from .audit import _scrub

STATUSES = ("termine", "erreur", "ignore")


def emit(path: str | Path, agent: str, type_: str, task: str, status: str, result: Any = None,
         duration_s: float = 0.0, sources: list[str] | None = None, errors: list[str] | None = None,
         run_id: str | None = None) -> dict:
    if status not in STATUSES:
        raise ValueError(f"statut inconnu : {status}")
    ev = {"id": uuid.uuid4().hex[:12], "ts": datetime.now(timezone.utc).isoformat(), "run_id": run_id,
          "agent": agent, "type": type_, "task": task, "status": status, "result": _scrub(result),
          "duration_s": round(duration_s, 3), "sources": sources or [], "errors": errors or []}
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(ev, ensure_ascii=False, default=str) + "\n")
    return ev


class _Span:
    def __init__(self):
        self.result: Any = None
        self.sources: list[str] = []
        self.errors: list[str] = []
        self.status = "termine"


@contextmanager
def span(path, agent: str, type_: str, task: str, run_id: str | None = None) -> Iterator[_Span]:
    """Mesure une étape réelle ; une exception est enregistrée puis relancée."""
    sp, t0 = _Span(), time.monotonic()
    try:
        yield sp
    except Exception as e:
        sp.status, sp.errors = "erreur", sp.errors + [f"{type(e).__name__}: {e}"]
        raise
    finally:
        if sp.errors and sp.status == "termine":
            sp.status = "erreur"
        emit(path, agent, type_, task, sp.status, sp.result, time.monotonic() - t0, sp.sources, sp.errors, run_id)


def read_events(path: str | Path, limit: int | None = None) -> list[dict]:
    p = Path(path)
    if not p.exists():
        return []
    out = []
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue  # ligne abîmée : ignorée, jamais bloquante
    return out[-limit:] if limit else out
