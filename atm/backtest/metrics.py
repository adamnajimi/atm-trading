"""Agent 12 — statistiques de performance (calculées, jamais supposées)."""
from __future__ import annotations

import math

import numpy as np
import pandas as pd

from ..config import Config
from ..portfolio import PortfolioState


def max_drawdown(equity: pd.Series) -> float:
    if equity.empty:
        return 0.0
    peak = equity.cummax()
    return float(((equity - peak) / peak).min())


def round_trips(trades: list[dict]) -> list[float]:
    """PnL net de chaque aller-retour (frais d'entrée et de sortie inclus)."""
    pnls, entry = [], {}
    for t in trades:
        if t["side"] == "buy":
            entry[t["asset"]] = t
        elif t["asset"] in entry:
            b = entry.pop(t["asset"])
            pnls.append(t["qty"] * t["price"] - t["fee"] - (b["qty"] * b["price"] + b["fee"]))
    return pnls


def summarize(equity: pd.Series, state: PortfolioState, cfg: Config, periods_per_year: int = 365) -> dict:
    initial = cfg.risk.initial_eur
    final = float(equity.iloc[-1]) if len(equity) else initial
    rets = equity.pct_change().dropna()
    sd = float(rets.std()) if len(rets) > 1 else 0.0
    downside = float(rets[rets < 0].std()) if (rets < 0).sum() > 1 else 0.0
    pnls = round_trips(state.trades)
    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p <= 0]
    years = len(equity) / periods_per_year if len(equity) else 0
    mdd = max_drawdown(equity)
    cagr = (final / initial) ** (1 / years) - 1 if years > 0 and final > 0 else float("nan")
    return {
        "initial_eur": initial,
        "final_eur": round(final, 4),
        "net_return": final / initial - 1,
        "cagr": cagr,
        "max_drawdown": mdd,
        "max_loss_eur": round(initial - float(equity.min()), 4) if len(equity) else 0.0,
        "sharpe": float(rets.mean() / sd * math.sqrt(periods_per_year)) if sd > 0 else float("nan"),
        "sortino": float(rets.mean() / downside * math.sqrt(periods_per_year)) if downside > 0 else float("nan"),
        "calmar": cagr / abs(mdd) if mdd < 0 and not math.isnan(cagr) else float("nan"),
        "n_round_trips": len(pnls),
        "win_rate": len(wins) / len(pnls) if pnls else float("nan"),
        "avg_win_eur": float(np.mean(wins)) if wins else float("nan"),
        "avg_loss_eur": float(np.mean(losses)) if losses else float("nan"),
        "profit_factor": sum(wins) / -sum(losses) if losses and sum(losses) < 0 else float("nan"),
        "expectancy_eur": float(np.mean(pnls)) if pnls else float("nan"),
        "fees_eur": round(state.fees_paid_eur, 4),
        "suspended": state.suspended,
        # pour le Sharpe déflaté (non annualisés)
        "sr_period": float(rets.mean() / sd) if sd > 0 else float("nan"),
        "skew": float(rets.skew()) if len(rets) > 2 else float("nan"),
        "kurtosis": float(rets.kurt() + 3) if len(rets) > 3 else float("nan"),
        "n_obs": int(len(rets)),
    }


EULER_GAMMA = 0.5772156649015329


def expected_max_sharpe(n_trials: int, sr_variance: float) -> float:
    """Sharpe maximal attendu par hasard parmi n essais (Bailey & López de Prado, 2014)."""
    from statistics import NormalDist
    if n_trials < 2 or sr_variance <= 0:
        return 0.0
    z = NormalDist().inv_cdf
    return math.sqrt(sr_variance) * ((1 - EULER_GAMMA) * z(1 - 1 / n_trials)
                                     + EULER_GAMMA * z(1 - 1 / (n_trials * math.e)))


def deflated_sharpe(sr: float, n_obs: int, skew: float, kurtosis: float, n_trials: int, sr_variance: float) -> float:
    """Probabilité que le vrai Sharpe (par période) dépasse celui qu'on obtiendrait par hasard
    en gardant le meilleur de n essais. Sharpe déflaté de Bailey & López de Prado (2014)."""
    from statistics import NormalDist
    if any(math.isnan(x) for x in (sr, skew, kurtosis)) or n_obs < 3:
        return float("nan")
    sr0 = expected_max_sharpe(n_trials, sr_variance)
    denom = 1 - skew * sr + (kurtosis - 1) / 4 * sr ** 2
    if denom <= 0:
        return float("nan")
    return NormalDist().cdf((sr - sr0) * math.sqrt(n_obs - 1) / math.sqrt(denom))


def buy_and_hold(data: pd.DataFrame, cfg: Config) -> pd.Series:
    """Benchmark : achat à la première ouverture, frais d'entrée et de sortie inclus."""
    c = cfg.venue.one_way_cost
    qty = cfg.risk.initial_eur * (1 - c) / float(data["open"].iloc[0])
    return data["close"] * qty * (1 - c)


def dca(data: pd.DataFrame, cfg: Config, n_buys: int | None = None) -> pd.Series:
    """Benchmark achat régulier : le capital est investi en parts égales, à intervalles
    réguliers, à l'ouverture. Avec 20 € et 5 € minimum par ordre, 4 achats au plus."""
    initial, c = cfg.risk.initial_eur, cfg.venue.one_way_cost
    n = n_buys or int(initial // cfg.venue.min_order_eur)
    n = max(1, min(n, len(data)))
    idx = [int(round(k * (len(data) - 1) / n)) for k in range(n)]
    part = initial / n
    qty = pd.Series(0.0, index=data.index)
    cash = pd.Series(initial, index=data.index)
    for k in idx:
        qty.iloc[k:] += part * (1 - c) / float(data["open"].iloc[k])
        cash.iloc[k:] -= part
    return cash + qty * data["close"] * (1 - c)
