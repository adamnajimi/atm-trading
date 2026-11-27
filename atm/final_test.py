"""Étape C — test final hors échantillon, exécuté UNE SEULE FOIS.

Spécification figée le 2026-11-27, avant toute exécution sur la période
2024-07-01 → dernière barre close, et après avoir vu uniquement les résultats
d'entraînement et de validation :

- actif : BTC/EUR seulement (ETH rejeté en validation : rendement net < cash) ;
- stratégie : trend_sma avec SMA 100, momentum 50, ATR 14, stop 3×ATR
  (paramètres choisis avant les données ; la grille de sensibilité n'a servi à rien choisir) ;
- capital 20 €, frais Kraken taker 0,80 % + slippage 0,10 % par ordre ;
- critère de réussite, les trois à la fois :
  1. rendement net > 0 (meilleur que le cash) ;
  2. perte maximale < 7 € (limite opérationnelle) ;
  3. aucune suspension par le gestionnaire de risques.
  Buy & hold et achat régulier sont rapportés à titre d'information, pas comme critère.

En cas d'échec, toute nouvelle version devra être évaluée sur une période
nouvelle et indépendante (données postérieures à aujourd'hui, donc paper trading).
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from .backtest.metrics import buy_and_hold, dca, max_drawdown
from .config import Config
from .research import FINAL_TEST_START, SegmentResult  # noqa: F401
from .strategies.trend import TrendSMA
from .backtest.engine import run_backtest
from .backtest.metrics import summarize

FROZEN = {
    "asset": "BTC/EUR",
    "start": FINAL_TEST_START,
    "params": {"sma_window": 100, "momentum_window": 50, "atr_window": 14, "stop_atr_multiple": 3.0},
    "criteria": {"net_return_gt": 0.0, "max_loss_eur_lt": 7.0, "no_suspension": True},
}
DONE_MARKER = Path("results/FINAL_TEST_DONE.json")


class FinalTestRefused(RuntimeError):
    pass


def run_final_test(cfg: Config, data: pd.DataFrame, root: str | Path = ".") -> dict:
    marker = Path(root) / DONE_MARKER
    if marker.exists():
        raise FinalTestRefused(f"test final déjà exécuté : {marker.read_text(encoding='utf-8')[:200]}")
    cfg_params = cfg.strategies.get("trend_sma", {}).get("params", {})
    if cfg_params != FROZEN["params"]:
        raise FinalTestRefused("les paramètres de config diffèrent de la spécification figée")

    strat = TrendSMA(**FROZEN["params"])
    start = pd.Timestamp(FROZEN["start"], tz="UTC")
    seg = data[data.index >= start]
    pre = data[data.index < start].iloc[-(strat.warmup - 1):]
    res = run_backtest(cfg, [strat], FROZEN["asset"], pd.concat([pre, seg]))
    eq = res.equity[res.equity.index >= seg.index[0]]
    st = summarize(eq, res.final_state, cfg)
    bh, d = buy_and_hold(seg, cfg), dca(seg, cfg)
    c = FROZEN["criteria"]
    checks = {
        "rendement_net_superieur_au_cash": st["net_return"] > c["net_return_gt"],
        "perte_max_inferieure_a_7_eur": st["max_loss_eur"] < c["max_loss_eur_lt"],
        "aucune_suspension": not st["suspended"],
    }
    return {
        "spec": FROZEN, "period": [str(seg.index[0].date()), str(seg.index[-1].date())], "n_days": len(seg),
        "stats": st, "checks": checks, "passed": all(checks.values()),
        "benchmarks": {"buy_hold_return": float(bh.iloc[-1] / cfg.risk.initial_eur - 1),
                       "buy_hold_mdd": max_drawdown(bh),
                       "dca_return": float(d.iloc[-1] / cfg.risk.initial_eur - 1), "cash_return": 0.0},
        "trades": res.trades,
    }


def to_markdown(r: dict) -> str:
    st, b = r["stats"], r["benchmarks"]
    L = [f"# Test final ATM — {'RÉUSSI' if r['passed'] else 'ÉCHOUÉ'}", "",
         f"BTC/EUR, {r['period'][0]} → {r['period'][1]} ({r['n_days']} jours), règles figées, exécution unique.", "",
         "| Mesure | Valeur |", "| --- | --- |",
         f"| Rendement net | {st['net_return']:+.1%} ({st['final_eur']:.2f} €) |",
         f"| Max drawdown | {st['max_drawdown']:+.1%} |",
         f"| Perte max | {st['max_loss_eur']:.2f} € |",
         f"| Allers-retours | {st['n_round_trips']} |",
         f"| Frais | {st['fees_eur']:.2f} € |",
         f"| Taux de réussite | {st['win_rate']:.0%} |" if st['n_round_trips'] else "| Taux de réussite | — |",
         f"| Buy & hold | {b['buy_hold_return']:+.1%} (DD {b['buy_hold_mdd']:+.1%}) |",
         f"| Achat régulier 4×5 € | {b['dca_return']:+.1%} |",
         "| Cash | +0.0% |", "", "Critères :"]
    L += [f"- {k} : {'oui' if v else 'NON'}" for k, v in r["checks"].items()]
    return "\n".join(L) + "\n"


def dump(r: dict) -> str:
    return json.dumps(r, indent=2, default=str, ensure_ascii=False)
