"""Étape C — protocole de recherche figé avant de voir les données réelles.

Découpage (fixé le 2026-11-27, avant tout téléchargement de données réelles) :
- entraînement : début de l'historique -> 2021-12-31 ;
- validation   : 2022-01-01 -> 2024-06-30 ;
- test final   : 2024-07-01 -> aujourd'hui. RÉSERVÉ : non exécuté par ce module.

Le test final ne sera lancé qu'une fois, après avoir figé les règles sur
entraînement + validation (commande séparée, à ajouter à l'étape D).
"""
from __future__ import annotations

import itertools
import json
import math
from dataclasses import dataclass

import pandas as pd

from .backtest.engine import run_backtest
from .backtest.metrics import buy_and_hold, dca, max_drawdown, summarize
from .config import Config
from .data.validate import validate_ohlcv
from .strategies.trend import TrendSMA

SEGMENTS = {
    "entrainement": ("2000-01-01", "2021-12-31"),
    "validation": ("2022-01-01", "2024-06-30"),
}
FINAL_TEST_START = "2024-07-01"  # ne jamais utiliser dans ce module

SENSITIVITY_GRID = {
    "sma_window": [50, 100, 150, 200],
    "stop_atr_multiple": [2.0, 3.0, 4.0],
}


@dataclass
class SegmentResult:
    asset: str
    segment: str
    start: str
    end: str
    n_days: int
    stats: dict
    buy_hold_return: float
    buy_hold_mdd: float
    dca_return: float = float("nan")


def _segment(cfg: Config, strategy: TrendSMA, asset: str, data: pd.DataFrame, start: str, end: str) -> SegmentResult | None:
    s, e = pd.Timestamp(start, tz="UTC"), pd.Timestamp(end, tz="UTC")
    if e >= pd.Timestamp(FINAL_TEST_START, tz="UTC"):
        raise ValueError("période de test final interdite dans la recherche")
    seg = data[(data.index >= s) & (data.index <= e)]
    if len(seg) < 60:
        return None
    # Préchauffage : les barres avant `start` servent aux indicateurs, sans trading compté.
    # warmup - 1 barres : la première décision tombe à la clôture du premier jour du segment.
    pre = data[data.index < seg.index[0]].iloc[-(strategy.warmup - 1):]
    sliced = pd.concat([pre, seg])
    res = run_backtest(cfg, [strategy], asset, sliced)
    eq = res.equity[res.equity.index >= seg.index[0]]
    stats = summarize(eq, res.final_state, cfg)
    bh = buy_and_hold(seg, cfg)
    d = dca(seg, cfg)
    return SegmentResult(asset, "", str(seg.index[0].date()), str(seg.index[-1].date()), len(seg),
                         stats, float(bh.iloc[-1] / cfg.risk.initial_eur - 1), max_drawdown(bh),
                         float(d.iloc[-1] / cfg.risk.initial_eur - 1))


def run_research(cfg: Config, datasets: dict[str, pd.DataFrame]) -> dict:
    out: dict = {"protocol": {"segments": SEGMENTS, "final_test_start": FINAL_TEST_START,
                              "final_test_run": False}, "data": {}, "segments": [], "candidates": [], "sensitivity": []}
    base_params = cfg.strategies.get("trend_sma", {}).get("params", {})
    for asset, df in datasets.items():
        rep = validate_ohlcv(df)
        out["data"][asset] = {"first": str(df.index[0].date()), "last": str(df.index[-1].date()),
                              "rows": len(df), "ok": rep.ok, "errors": rep.errors, "warnings": rep.warnings}
        if not rep.ok:
            continue
        research_df = df[df.index < pd.Timestamp(FINAL_TEST_START, tz="UTC")]
        for name, (start, end) in SEGMENTS.items():
            r = _segment(cfg, TrendSMA(**base_params), asset, research_df, start, end)
            if r:
                r.segment = name
                out["segments"].append({**r.__dict__, "strategy": "trend_sma"})
            # Candidates : même protocole (entraînement + validation), jamais le test final.
            from .strategies.dip import RsiDip
            types = {"trend_sma": TrendSMA, "rsi_dip": RsiDip}
            for cname, spec in cfg.shadow_strategies.items():
                rc = _segment(cfg, types[spec["type"]](**spec.get("params", {})), asset, research_df, start, end)
                if rc:
                    rc.segment = name
                    out["candidates"].append({**rc.__dict__, "strategy": cname})
        # Sensibilité aux paramètres : sur l'entraînement uniquement (Challenger)
        start, end = SEGMENTS["entrainement"]
        for sma, stop in itertools.product(SENSITIVITY_GRID["sma_window"], SENSITIVITY_GRID["stop_atr_multiple"]):
            params = {**base_params, "sma_window": sma, "stop_atr_multiple": stop}
            r = _segment(cfg, TrendSMA(**params), asset, research_df, start, end)
            if r:
                out["sensitivity"].append({"asset": asset, "sma_window": sma, "stop_atr_multiple": stop,
                                           "net_return": r.stats["net_return"], "max_drawdown": r.stats["max_drawdown"],
                                           "n_round_trips": r.stats["n_round_trips"], "fees_eur": r.stats["fees_eur"]})
    return out


def _f(x, pct=False):
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "—"
    return f"{x:+.1%}" if pct else f"{x:.2f}"


def to_markdown(res: dict) -> str:
    L = ["# Résultats de recherche ATM (étape C, entraînement + validation)", "",
         f"Test final ({FINAL_TEST_START} → aujourd'hui) : **non exécuté**, réservé.", "", "## Données", "",
         "| Actif | Début | Fin | Lignes | Valide | Avertissements |", "| --- | --- | --- | --- | --- | --- |"]
    for a, d in res["data"].items():
        L.append(f"| {a} | {d['first']} | {d['last']} | {d['rows']} | {'oui' if d['ok'] else 'NON ' + str(d['errors'])} | {'; '.join(d['warnings']) or '—'} |")
    L += ["", "## trend_sma (paramètres de config) vs benchmarks, capital 20 €", "",
          "| Actif | Segment | Période | Rendement net | Max DD | Perte max (€) | Allers-retours | Frais (€) | Sharpe | Buy & hold | DD buy & hold | Achat régulier (4×5 €) | Cash |",
          "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for s in res["segments"]:
        st = s["stats"]
        L.append(f"| {s['asset']} | {s['segment']} | {s['start']} → {s['end']} | {_f(st['net_return'], True)} | {_f(st['max_drawdown'], True)} | "
                 f"{_f(st['max_loss_eur'])} | {st['n_round_trips']} | {_f(st['fees_eur'])} | {_f(st['sharpe'])} | "
                 f"{_f(s['buy_hold_return'], True)} | {_f(s['buy_hold_mdd'], True)} | {_f(s.get('dca_return'), True)} | +0.0% |")
    L += ["", "## Stratégies candidates (mêmes segments)", "",
          "| Candidate | Actif | Segment | Rendement net | Max DD | Perte max (€) | Allers-retours | Frais (€) | Buy & hold |",
          "| --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for s in res.get("candidates", []):
        st = s["stats"]
        L.append(f"| {s['strategy']} | {s['asset']} | {s['segment']} | {_f(st['net_return'], True)} | {_f(st['max_drawdown'], True)} | "
                 f"{_f(st['max_loss_eur'])} | {st['n_round_trips']} | {_f(st['fees_eur'])} | {_f(s['buy_hold_return'], True)} |")
    L += ["", "## Sensibilité (entraînement uniquement)", "",
          "| Actif | SMA | Stop (×ATR) | Rendement net | Max DD | Allers-retours | Frais (€) |", "| --- | --- | --- | --- | --- | --- | --- |"]
    for s in res["sensitivity"]:
        L.append(f"| {s['asset']} | {s['sma_window']} | {s['stop_atr_multiple']} | {_f(s['net_return'], True)} | "
                 f"{_f(s['max_drawdown'], True)} | {s['n_round_trips']} | {_f(s['fees_eur'])} |")
    return "\n".join(L) + "\n"


def dump(res: dict) -> str:
    return json.dumps(res, indent=2, default=str, ensure_ascii=False)
