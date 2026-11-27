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


def cmd_paper(args) -> int:
    cfg = load(args.config)
    from .data.fetch import fetch_daily_ohlcv
    root = Path(args.root)
    state_path, log_path = root / "state" / "portfolio.json", root / "state" / "audit.jsonl"
    state = PortfolioState.load_or_new(state_path, cfg.risk.initial_eur)
    now = datetime.now(timezone.utc)
    kill = killswitch.is_active(root)
    broker, risk = PaperBroker(cfg.venue), RiskManager(cfg)
    strategies = build_strategies(cfg)
    cycles, errors, prices = [], [], {}

    from .orchestrator import run_cycle
    for asset in cfg.universe:
        try:
            data = fetch_daily_ohlcv(asset, cfg.venue.name)
            rep = validate_ohlcv(data)
            if not rep.ok:
                errors.append(f"{asset} : données refusées {rep.errors}")
                continue
            prices[asset] = float(data["close"].iloc[-1])
            state.roll_day(now.date().isoformat(), prices, cfg.venue.one_way_cost)
            res = run_cycle(cfg, strategies, asset, data, state, now, kill_switch=kill)
            if res.order:
                broker.execute(res.order, res.verdict, state, prices[asset], now)
            cycles.append(res.to_dict())
            log_event(log_path, "cycle", res.to_dict())
        except Exception as e:  # une erreur sur un actif ne doit pas bloquer la suite
            errors.append(f"{asset} : {type(e).__name__}: {e}")
            log_event(log_path, "error", {"asset": asset, "error": str(e)})

    risk.check_portfolio(state, prices)
    state.save(state_path)
    eq = state.liquidation_equity(prices, cfg.venue.one_way_cost)
    summary = {"initial_eur": state.initial_eur, "equity_eur": eq, "fees_eur": state.fees_paid_eur,
               "distance_to_stop_eur": cfg.risk.operational_loss_limit_eur - max(0.0, state.initial_eur - eq),
               "positions": {k: round(v.quantity, 8) for k, v in state.positions.items()},
               "suspended": state.suspended, "suspend_reason": state.suspend_reason}
    report = daily_report(cycles, summary, errors)
    (root / "state" / "reports").mkdir(parents=True, exist_ok=True)
    (root / "state" / "reports" / f"{now:%Y-%m-%d}.md").write_text(report, encoding="utf-8")
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
    sub.add_parser("paper")
    sub.add_parser("status")
    args = ap.parse_args(argv)
    return {"backtest": cmd_backtest, "fetch": cmd_fetch, "research": cmd_research, "check": cmd_check, "final-test": cmd_final_test,
            "paper": cmd_paper, "status": cmd_status}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
