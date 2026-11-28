"""Tableau de bord statique (mode « Command Center ») généré depuis les fichiers réels du dépôt.

Sources : state/portfolio.json, state/shadow/*.json, state/events.jsonl, state/reports/*.md.
Aucune donnée inventée : un panneau sans donnée affiche « aucune donnée ».
Sortie : docs/dashboard/index.html (publiable par GitHub Pages, lisible sur Mac et iPhone).
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from .events import read_events

AGENTS = ["superviseur", "donnees", "strategie:trend_sma", "strategie:trend_sma_fast",
          "strategie:trend_sma_risk15", "risque", "execution", "portefeuille", "rapporteur"]


def _portfolios(root: Path) -> list[dict]:
    out = []
    files = [("principal", root / "state" / "portfolio.json")] + \
            [(p.stem, p) for p in sorted((root / "state" / "shadow").glob("*.json"))]
    for name, p in files:
        if p.exists():
            s = json.loads(p.read_text(encoding="utf-8"))
            out.append({"nom": name, "initial": s.get("initial_eur"), "cash": s.get("cash_eur"),
                        "positions": s.get("positions", {}), "frais": s.get("fees_paid_eur"),
                        "pnl_realise": s.get("realized_pnl_eur"), "ordres": len(s.get("trades", [])),
                        "suspendu": s.get("suspended"), "jour": s.get("day")})
    return out


def build(root: str | Path = ".") -> str:
    root = Path(root)
    events = read_events(root / "state" / "events.jsonl")
    reports = sorted((root / "state" / "reports").glob("*.md"))
    last_by_agent = {}
    for e in events:
        last_by_agent[e["agent"]] = e
    data = {
        "genere_le": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "portefeuilles": _portfolios(root),
        "agents": [{"agent": a, "dernier": last_by_agent.get(a)} for a in
                   AGENTS + sorted(set(last_by_agent) - set(AGENTS))],
        "evenements": events[-300:],
        "incidents": [e for e in events if e["status"] == "erreur"][-50:],
        "rapports": [{"date": r.stem, "texte": r.read_text(encoding="utf-8")} for r in reports[-14:]],
    }
    # JSON dans <script> : on échappe < > & en \uXXXX (le contenu d'un script n'est pas décodé comme du HTML)
    payload = (json.dumps(data, ensure_ascii=False, default=str)
               .replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026"))
    return TEMPLATE.replace("__DATA__", payload)


def write(root: str | Path = ".") -> Path:
    out = Path(root) / "docs" / "dashboard" / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(build(root), encoding="utf-8")
    return out


TEMPLATE = r"""<!doctype html>
<html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>ATM Command Center</title>
<style>
:root{--bg:#f6f7f9;--panel:#fff;--ink:#16181d;--muted:#5d6470;--line:#e2e5ea;--ok:#1a7f4b;--err:#c0362c;--warn:#a86b00;--acc:#2856c4}
@media (prefers-color-scheme:dark){:root{--bg:#0f1115;--panel:#171a21;--ink:#e8eaee;--muted:#9aa1ad;--line:#272b35;--ok:#4cc38a;--err:#ff6b5e;--warn:#e0a63a;--acc:#7aa2ff}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:14px/1.45 system-ui,-apple-system,Segoe UI,sans-serif}
header{padding:16px;border-bottom:1px solid var(--line);display:flex;flex-wrap:wrap;gap:8px;align-items:baseline;justify-content:space-between}
h1{font-size:18px;margin:0}h2{font-size:14px;margin:0 0 10px;color:var(--muted);text-transform:uppercase;letter-spacing:.04em}
main{display:grid;gap:12px;padding:12px 16px;grid-template-columns:repeat(auto-fit,minmax(320px,1fr))}
section{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:14px;min-width:0}
.wide{grid-column:1/-1}table{width:100%;border-collapse:collapse;font-variant-numeric:tabular-nums}
td,th{padding:6px 4px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}th{color:var(--muted);font-weight:600}
.scroll{overflow-x:auto}.ok{color:var(--ok)}.err{color:var(--err)}.muted{color:var(--muted)}
.pill{display:inline-block;padding:1px 8px;border-radius:99px;border:1px solid var(--line);font-size:12px}
.tl{max-height:420px;overflow:auto}.tl div{padding:6px 0;border-bottom:1px solid var(--line)}
pre{white-space:pre-wrap;font-size:12px;margin:0}details{margin:4px 0}
.banner{background:var(--panel);border:1px solid var(--line);border-left:4px solid var(--warn);padding:8px 12px;margin:12px 16px 0;border-radius:6px}
</style></head><body>
<header><h1>ATM — Command Center (simulation)</h1><span class="muted" id="gen"></span></header>
<div class="banner">Simulation uniquement. Aucun compte, aucune clé, aucun ordre réel. Toutes les données viennent des fichiers du dépôt.</div>
<main>
<section><h2>Portefeuilles fictifs</h2><div class="scroll"><table id="pf"></table></div></section>
<section><h2>Agents (dernière activité réelle)</h2><div class="scroll"><table id="ag"></table></div></section>
<section class="wide"><h2>Chronologie des événements</h2><div class="tl" id="tl"></div></section>
<section><h2>Incidents</h2><div id="inc"></div></section>
<section><h2>Rapports quotidiens</h2><div id="rp"></div></section>
</main>
<script id="data" type="application/json">__DATA__</script>
<script>
const D=JSON.parse(document.getElementById('data').textContent);
const esc=s=>String(s??'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const eur=x=>x==null?'—':Number(x).toFixed(2)+' €';
const loc=t=>t?new Date(t).toLocaleString('fr-FR',{timeZone:'Europe/Paris'}):'—';
document.getElementById('gen').textContent='Généré le '+loc(D.genere_le)+' (heure de Paris)';
const pf=D.portefeuilles;
document.getElementById('pf').innerHTML=pf.length?'<tr><th>Portefeuille</th><th>Initial</th><th>Cash</th><th>Positions</th><th>Ordres</th><th>Frais</th><th>État</th></tr>'+
 pf.map(p=>`<tr><td>${esc(p.nom)}</td><td>${eur(p.initial)}</td><td>${eur(p.cash)}</td><td>${Object.keys(p.positions||{}).length||'aucune'}</td><td>${p.ordres}</td><td>${eur(p.frais)}</td><td class="${p.suspendu?'err':'ok'}">${p.suspendu?'suspendu':'actif'}</td></tr>`).join(''):'<tr><td class="muted">aucune donnée</td></tr>';
document.getElementById('ag').innerHTML='<tr><th>Agent</th><th>Statut</th><th>Dernière tâche</th><th>Quand</th></tr>'+
 D.agents.map(a=>{const e=a.dernier;return `<tr><td>${esc(a.agent)}</td><td>${e?`<span class="pill ${e.status==='erreur'?'err':'ok'}">${e.status==='erreur'?'erreur':'inactif, tâche terminée'}</span>`:'<span class="pill muted">jamais actif</span>'}</td><td>${e?esc(e.type+' — '+e.task):'—'}</td><td>${e?loc(e.ts):'—'}</td></tr>`}).join('');
const ev=[...D.evenements].reverse();
document.getElementById('tl').innerHTML=ev.length?ev.map(e=>`<div><span class="muted">${loc(e.ts)}</span> · <b>${esc(e.agent)}</b> · ${esc(e.type)} · ${esc(e.task)} <span class="${e.status==='erreur'?'err':'ok'}">${esc(e.status)}</span>${e.duration_s?` <span class="muted">(${e.duration_s}s)</span>`:''}
<details><summary class="muted">détails</summary><pre>${esc(JSON.stringify({resultat:e.result,sources:e.sources,erreurs:e.errors},null,1))}</pre></details></div>`).join(''):'<p class="muted">aucun événement enregistré pour l\'instant (le journal démarre au prochain cycle)</p>';
document.getElementById('inc').innerHTML=D.incidents.length?D.incidents.reverse().map(e=>`<p class="err">${loc(e.ts)} · ${esc(e.agent)} : ${esc((e.errors||[]).join('; '))}</p>`).join(''):'<p class="ok">aucun incident enregistré</p>';
document.getElementById('rp').innerHTML=D.rapports.length?[...D.rapports].reverse().map(r=>`<details><summary>${esc(r.date)}</summary><pre>${esc(r.texte)}</pre></details>`).join(''):'<p class="muted">aucun rapport</p>';
</script></body></html>
"""
