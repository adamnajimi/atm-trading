"""Agent 15 — journal d'audit horodaté (JSON Lines, ajout seul) et rapport quotidien."""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_SECRET = re.compile(r"(api[_-]?key|secret|token|password|passphrase)", re.I)


def _scrub(obj: Any) -> Any:
    """Retire toute valeur dont la clé ressemble à un identifiant : jamais de secret dans les journaux."""
    if isinstance(obj, dict):
        return {k: ("***" if _SECRET.search(str(k)) else _scrub(v)) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_scrub(v) for v in obj]
    return obj


def log_event(path: str | Path, kind: str, payload: dict[str, Any]) -> None:
    rec = {"logged_at": datetime.now(timezone.utc).isoformat(), "kind": kind, **_scrub(payload)}
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False, default=str) + "\n")


def daily_report(cycles: list[dict], state_summary: dict[str, Any], errors: list[str]) -> str:
    lines = [f"# Rapport ATM du {datetime.now(timezone.utc):%Y-%m-%d} (simulation)", ""]
    s = state_summary
    lines += [
        "## Portefeuille",
        f"- Capital initial : {s['initial_eur']:.2f} €",
        f"- Valeur liquidative : {s['equity_eur']:.2f} €",
        f"- Résultat : {s['equity_eur'] - s['initial_eur']:+.2f} €",
        f"- Frais cumulés : {s['fees_eur']:.2f} €",
        f"- Distance avant l'arrêt opérationnel : {s['distance_to_stop_eur']:.2f} €",
        f"- Positions : {s['positions'] or 'aucune'}",
        f"- État : {'SUSPENDU — ' + s['suspend_reason'] if s['suspended'] else 'actif'}",
        "",
        "## Décisions",
    ]
    for c in cycles:
        d, v = c["decision"], c["verdict"]
        lines.append(f"- **{c['asset']}** : proposition {d['action']} ({d['strategy']}) — "
                     f"risque : {'approuvé' if v['approved'] else 'rejeté'} ({v['reason']})")
        lines.append(f"  - justification : {d['rationale']}")
    lines += ["", "## Erreurs", *(f"- {e}" for e in errors or ["aucune"])]
    return "\n".join(lines) + "\n"
