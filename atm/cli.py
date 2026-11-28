"""Point d'entrée : `python -m atm.cli backtest|paper|status`.

- backtest : rejoue une stratégie sur un CSV (ou des données synthétiques de test).
- paper    : un cycle de paper trading ; conçu pour GitHub Actions (idempotent).
- status   : affiche l'état du portefeuille simulé.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from . import killswitch
from .audit import daily_report, log_event
from .backtest.engine import run_backtest
from .backtest.metrics import buy_and_hold, max_drawdown
from .config import load
from .data.validate import validate_ohlcv
from .execution.paper import PaperBroker
from .portfolio import PortfolioState
from .risk import RiskManager
from .strategies.dip import RsiDip
from .strategies.trend import TrendSMA


def build_strategies(cfg):
    out = []
    t = cfg.strategies.get("trend_sma", {})
    if t.get("enabled"):
        out.append(TrendSMA(**t.get("params", {})))
    return out


def cmd_backtest(args) -> int:
    cfg = load(args.config)
    if args.synthetic:
        from .data.synthetic import random_walk_ohlcv
        data = random_walk_ohlcv(n=1500, seed=args.seed)
        print("ATTENTION : données synthétiques, résultats sans valeur de performance.")
    else:
        from .data.fetch import load_csv
        data = load_csv(args.data)
    rep = validate_ohlcv(data)
    if not rep.ok:
        print("Données refusées :", rep.errors)
        return 2
    res = run_backtest(cfg, build_strategies(cfg), args.asset, data)
    bh = buy_and_hold(data, cfg)
    out = {**res.stats, "benchmark_buy_hold_return": float(bh.iloc[-1] / cfg.risk.initial_eur - 1),
           "benchmark_buy_hold_mdd": max_drawdown(bh), "benchmark_cash_return": 0.0,
           "data_warnings": rep.warnings}
    print(json.dumps(out, indent=2, default=str))
    return 0


STRATEGY_TYPES = {"trend_sma": TrendSMA, "rsi_dip": RsiDip}


def apply_stop(state, asset, bar, broker, now, log_path=None):
    """Stop vérifié sur la dernière barre close : si le plus bas l'a touché, sortie au stop
    (ou à l'ouverture en cas de gap). Corrige l'écart backtest/paper relevé le 2026-11-27."""
    pos = state.positions.get(asset)
    if not pos or not pos.stop_price or float(bar["low"]) > pos.stop_price:
        return None
    from .models import Action, Order, RiskVerdict
    px = min(float(bar["open"]), pos.stop_price)
    order = Order(f"stop-{asset}-{bar.name.isoformat()}", asset, "sell", quantity=pos.quantity)
    return broker.execute(order, RiskVerdict(True, Action.SELL, "stop"), state, px, now)


def run_portfolio(cfg, strategies, state_path, log_path, data_by_asset, now, kill, label="principal"):
    from .orchestrator import run_cycle
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state = PortfolioState.load_or_new(state_path, cfg.risk.initial_eur)
    broker, risk = PaperBroker(cfg.venue), RiskManager(cfg)
    cycles, errors, prices = [], [], {}
    for asset, data in data_by_asset.items():
        try:
            prices[asset] = float(data["close"].iloc[-1])
            state.roll_day(now.date().isoformat(), prices, cfg.venue.one_way_cost)
            apply_stop(state, asset, data.iloc[-1], broker, now)
            res = run_cycle(cfg, strategies, asset, data, state, now, kill_switch=kill)
            if res.order:
                broker.execute(res.order, res.verdict, state, prices[asset], now)
            cycles.append(res.to_dict())
            log_event(log_path, "cycle", {"portfolio": label, **res.to_dict()})
        except Exception as e:  # une erreur sur un actif ne doit pas bloquer la suite
            errors.append(f"[{label}] {asset} : {type(e).__name__}: {e}")
            log_event(log_path, "error", {"portfolio": label, "asset": asset, "error": str(e)})
    risk.check_portfolio(state, prices)
    state.save(state_path)
    eq = state.liquidation_equity(prices, cfg.venue.one_way_cost)
    summary = {"initial_eur": state.initial_eur, "equity_eur": eq, "fees_eur": state.fees_paid_eur,
               "distance_to_stop_eur": cfg.risk.operational_loss_limit_eur - max(0.0, state.initial_eur - eq),
               "positions": {k: round(v.quantity, 8) for k, v in state.positions.items()},
               "suspended": state.suspended, "suspend_reason": state.suspend_reason,
               "n_trades": len(state.trades)}
    return cycles, errors, summary


def _emit_portfolio(ev_path, run_id, label, cycles, errs, summary):
    """Un événement par décision de stratégie, par verdict du risque et par ordre fictif réellement passé."""
    from .events import emit
    for c in cycles:
        d, v = c["decision"], c["verdict"]
        emit(ev_path, f"strategie:{d['strategy']}", "decision", f"{label} {c['asset']}", "termine",
             {"action": d["action"], "justification": d["rationale"], "donnees_au": d["data_asof"]}, run_id=run_id)
        emit(ev_path, "risque", "verdict", f"{label} {c['asset']}", "termine",
             {"approuve": v["approved"], "action": v["action"], "raison": v["reason"], "montant_eur": v["notional_eur"]},
             run_id=run_id)
        if c.get("order"):
            emit(ev_path, "execution", "ordre_fictif", f"{label} {c['asset']}", "termine", c["order"], run_id=run_id)
    emit(ev_path, "portefeuille", "etat", label, "erreur" if errs else "termine",
         {k: summary[k] for k in ("equity_eur", "fees_eur", "distance_to_stop_eur", "positions", "suspended", "n_trades")},
         errors=errs, run_id=run_id)


def cmd_paper(args) -> int:
    cfg = load(args.config)
    from .data.fetch import fetch_daily_ohlcv
    root = Path(args.root)
    log_path = root / "state" / "audit.jsonl"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc)
    today_report = root / "state" / "reports" / f"{now:%Y-%m-%d}.md"
    from .events import emit, span
    ev_path = root / "state" / "events.jsonl"
    run_id = f"paper-{now:%Y%m%dT%H%M%S}"
    if today_report.exists() and not getattr(args, "force", False):
        # Le workflow a plusieurs créneaux de secours (GitHub saute parfois un cron) :
        # un seul cycle par jour UTC, les créneaux suivants ne font rien (et n'écrivent rien).
        print(f"cycle du {now:%Y-%m-%d} déjà fait ({today_report.name}) : rien à faire")
        return 0
    kill = killswitch.is_active(root)

    data_by_asset, errors = {}, []
    emit(ev_path, "superviseur", "cycle_debut", "cycle de paper trading", "termine",
         {"kill_switch": kill, "actifs": list(cfg.paper_universe)}, run_id=run_id)
    for asset in cfg.paper_universe:
        try:
            with span(ev_path, "donnees", "telechargement", f"bougies journalières {asset}", run_id) as sp:
                sp.sources = [f"{cfg.venue.name} OHLC public"]
                data = fetch_daily_ohlcv(asset, cfg.venue.name)
                rep = validate_ohlcv(data)
                sp.result = {"barres": len(data), "derniere": str(data.index[-1].date()), "valide": rep.ok,
                             "avertissements": rep.warnings}
                if rep.ok:
                    data_by_asset[asset] = data
                else:
                    sp.errors = [f"données refusées {rep.errors}"]
                    errors.append(f"{asset} : données refusées {rep.errors}")
        except Exception as e:
            errors.append(f"{asset} : {type(e).__name__}: {e}")
            log_event(log_path, "error", {"asset": asset, "error": str(e)})

    cycles, errs, summary = run_portfolio(cfg, build_strategies(cfg), root / "state" / "portfolio.json",
                                          log_path, data_by_asset, now, kill)
    _emit_portfolio(ev_path, run_id, "principal", cycles, errs, summary)
    errors += errs
    report = daily_report(cycles, summary, errors)

    # Portefeuilles fantômes : candidates évaluées sur données nouvelles, sans effet sur le principal.
    shadow_lines, shadow_errors = [], []
    for name, spec in cfg.shadow_strategies.items():
        if now.date().isoformat() < str(spec.get("since", "")):
            continue
        strat = STRATEGY_TYPES[spec["type"]](**spec.get("params", {}))
        strat.name = name
        from .config import with_shadow_overrides
        scfg = with_shadow_overrides(cfg, spec)
        c, e, sm = run_portfolio(scfg, [strat], root / "state" / "shadow" / f"{name}.json",
                                 log_path, data_by_asset, now, kill, label=name)
        errors += e
        shadow_errors += e
        _emit_portfolio(ev_path, run_id, name, c, e, sm)
        acts = ", ".join(f"{x['asset']} {x['decision']['action']}" for x in c) or "—"
        shadow_lines.append(f"| {name} | {sm['initial_eur']:.2f} € | {sm['equity_eur']:.2f} € | {sm['n_trades']} | "
                            f"{sm['fees_eur']:.2f} € | {scfg.venue.name} | {acts} |")
    if shadow_lines:
        report += ("\n## Stratégies candidates (portefeuilles fantômes, argent fictif)\n\n"
                   "| Candidate | Capital fictif | Valeur | Ordres | Frais | Frais supposés | Décision du jour |\n"
                   "| --- | --- | --- | --- | --- | --- | --- |\n"
                   + "\n".join(shadow_lines) + "\n")
    if shadow_errors:
        report += "\n## Erreurs des candidates\n" + "".join(f"- {x}\n" for x in shadow_errors)

    (root / "state" / "reports").mkdir(parents=True, exist_ok=True)
    (root / "state" / "reports" / f"{now:%Y-%m-%d}.md").write_text(report, encoding="utf-8")
    emit(ev_path, "rapporteur", "rapport", f"rapport du {now:%Y-%m-%d}", "erreur" if errors else "termine",
         {"fichier": f"state/reports/{now:%Y-%m-%d}.md"}, errors=errors, run_id=run_id)
    print(report)
    return 1 if errors else 0


def cmd_fetch(args) -> int:
    from .data.fetch import fetch_daily_ohlcv, save_csv
    cfg = load(args.config)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    for asset in cfg.universe:
        df = fetch_daily_ohlcv(asset, args.exchange, since=args.since)
        path = out / (asset.replace("/", "_").lower() + ".csv")
        save_csv(df, path)
        print(f"{asset}: {len(df)} barres {df.index[0].date()} -> {df.index[-1].date()} ({path})")
    return 0


def cmd_research(args) -> int:
    from .data.fetch import load_csv
    from .research import dump, run_research, to_markdown
    cfg = load(args.config)
    datasets = {a: load_csv(Path(args.data) / (a.replace("/", "_").lower() + ".csv")) for a in cfg.universe}
    res = run_research(cfg, datasets)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "research.json").write_text(dump(res), encoding="utf-8")
    md = to_markdown(res)
    (out / "research.md").write_text(md, encoding="utf-8")
    print(md)
    return 0


def _csv(folder, asset):
    return Path(folder) / (asset.replace("/", "_").lower() + ".csv")


def cmd_check(args) -> int:
    from .checks import describe
    from .data.fetch import load_csv
    cfg = load(args.config)
    data = {a: load_csv(_csv(args.data, a)) for a in cfg.universe}
    second = {a: load_csv(_csv(args.second, a)) for a in cfg.universe if args.second and _csv(args.second, a).exists()}
    md = "# Anomalies de données\n\n" + "\n".join(
        describe(a, df, {o: d for o, d in data.items() if o != a}, second.get(a)) for a, df in data.items())
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "data_checks.md").write_text(md, encoding="utf-8")
    print(md)
    return 0


def cmd_final_test(args) -> int:
    from .data.fetch import load_csv
    from .final_test import FROZEN, dump, run_final_test, to_markdown
    cfg = load(args.config)
    r = run_final_test(cfg, load_csv(_csv(args.data, FROZEN["asset"])), root=args.root)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "final_test.json").write_text(dump(r), encoding="utf-8")
    md = to_markdown(r)
    (out / "final_test.md").write_text(md, encoding="utf-8")
    print(md)
    return 0


def cmd_dashboard(args) -> int:
    from .dashboard import write
    print(f"tableau de bord écrit : {write(args.root)}")
    return 0


def cmd_status(args) -> int:
    p = Path(args.root) / "state" / "portfolio.json"
    print(p.read_text(encoding="utf-8") if p.exists() else "aucun état : le paper trading n'a pas encore tourné")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="atm")
    ap.add_argument("--config", default="config/config.yaml")
    ap.add_argument("--root", default=".")
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("backtest")
    b.add_argument("--data")
    b.add_argument("--asset", default="BTC/EUR")
    b.add_argument("--synthetic", action="store_true")
    b.add_argument("--seed", type=int, default=0)
    f = sub.add_parser("fetch")
    f.add_argument("--exchange", default="coinbaseexchange")
    f.add_argument("--since", default="2015-01-01T00:00:00Z")
    f.add_argument("--out", default="data")
    r = sub.add_parser("research")
    r.add_argument("--data", default="data")
    r.add_argument("--out", default="results")
    c = sub.add_parser("check")
    c.add_argument("--data", default="data")
    c.add_argument("--second", default="data_kraken")
    c.add_argument("--out", default="results")
    ft = sub.add_parser("final-test")
    ft.add_argument("--data", default="data")
    ft.add_argument("--out", default="results")
    pp = sub.add_parser("paper")
    pp.add_argument("--force", action="store_true", help="refaire le cycle même si le rapport du jour existe")
    sub.add_parser("status")
    sub.add_parser("dashboard")
    args = ap.parse_args(argv)
    return {"backtest": cmd_backtest, "fetch": cmd_fetch, "research": cmd_research, "check": cmd_check, "final-test": cmd_final_test,
            "paper": cmd_paper, "status": cmd_status, "dashboard": cmd_dashboard}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
