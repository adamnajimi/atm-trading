"""Agent 11 — moteur de backtest chronologique, indépendant des stratégies.

Règles anti-biais appliquées :
- décision à la clôture de la barre t avec les seules barres <= t ;
- exécution à l'ouverture de la barre t+1 (jamais au prix qui a servi à décider) ;
- stop vérifié en intrajournalier ; en cas de gap, sortie au prix d'ouverture ;
- frais taker, slippage, minimum d'ordre et veto du risque identiques au paper trading.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta

import pandas as pd

from ..config import Config
from ..execution.paper import PaperBroker
from ..models import Action, Order, RiskVerdict
from ..orchestrator import run_cycle
from ..portfolio import PortfolioState
from ..strategies.base import Strategy
from .metrics import summarize


@dataclass
class BacktestResult:
    equity: pd.Series
    trades: list[dict]
    decisions: list[dict] = field(default_factory=list)
    final_state: PortfolioState | None = None
    stats: dict = field(default_factory=dict)


def run_backtest(cfg: Config, strategies: list[Strategy], asset: str, data: pd.DataFrame, bar: timedelta = timedelta(days=1)) -> BacktestResult:
    state = PortfolioState(cash_eur=cfg.risk.initial_eur, initial_eur=cfg.risk.initial_eur)
    broker = PaperBroker(cfg.venue)
    warmup = max(s.warmup for s in strategies)
    exit_cost = cfg.venue.one_way_cost
    pending: Order | None = None
    equity: dict[pd.Timestamp, float] = {}
    decisions: list[dict] = []

    for i in range(len(data)):
        ts = data.index[i]
        row = data.iloc[i]
        state.roll_day(ts.date().isoformat(), {asset: float(row["open"])}, exit_cost)

        # 1. Exécution de l'ordre décidé à la clôture précédente
        if pending is not None:
            ok = RiskVerdict(True, Action.BUY if pending.side == "buy" else Action.SELL, "décidé à t-1")
            if pending.side == "buy" and pending.notional_eur and pending.notional_eur * (1 + cfg.venue.taker_fee) > state.cash_eur:
                pending.notional_eur = state.cash_eur / (1 + cfg.venue.taker_fee) - 1e-6
            if pending.side == "sell" or (pending.notional_eur or 0) >= cfg.venue.min_order_eur:
                broker.execute(pending, ok, state, float(row["open"]), ts.to_pydatetime())
            pending = None

        # 2. Stop intrajournalier
        pos = state.positions.get(asset)
        if pos and pos.stop_price and float(row["low"]) <= pos.stop_price:
            px = min(float(row["open"]), pos.stop_price)
            stop_order = Order(f"stop-{asset}-{ts.isoformat()}", asset, "sell", quantity=pos.quantity)
            broker.execute(stop_order, RiskVerdict(True, Action.SELL, "stop"), state, px, ts.to_pydatetime())

        # 3. Décision à la clôture (now = fin de la barre)
        close_time = (ts + bar).to_pydatetime()
        if i + 1 >= warmup:
            res = run_cycle(cfg, strategies, asset, data.iloc[: i + 1], state, close_time)
            decisions.append({"ts": ts.isoformat(), "action": res.decision.action.value,
                              "approved": res.verdict.approved, "reason": res.verdict.reason})
            pending = res.order

        equity[ts] = state.liquidation_equity({asset: float(row["close"])}, exit_cost)

    eq = pd.Series(equity, name="equity")
    return BacktestResult(eq, state.trades, decisions, state, summarize(eq, state, cfg))
