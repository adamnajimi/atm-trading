"""Agent 0 — orchestrateur et comité de décision.

Un cycle : données validées -> propositions des stratégies -> agrégation ->
veto du risque -> ordre pour l'exécution. Le même code sert au backtest et au
paper trading, pour que ce qui est testé soit exactement ce qui tourne.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime

import pandas as pd

from .config import Config
from .models import Action, Order, Proposal, RiskVerdict
from .portfolio import PortfolioState
from .risk import RiskManager
from .strategies.base import Strategy


@dataclass
class CycleResult:
    asset: str
    proposals: list[Proposal]
    decision: Proposal
    verdict: RiskVerdict
    order: Order | None
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "asset": self.asset,
            "proposals": [p.to_dict() for p in self.proposals],
            "decision": self.decision.to_dict(),
            "verdict": {"approved": self.verdict.approved, "action": self.verdict.action.value,
                        "reason": self.verdict.reason, "notional_eur": self.verdict.notional_eur},
            "order": None if self.order is None else vars(self.order),
            "notes": self.notes,
        }


def aggregate(proposals: list[Proposal], weights: dict[str, float]) -> Proposal:
    """Vote pondéré. Les poids doivent venir de performances hors échantillon,
    jamais de la confiance déclarée. Sans poids validé, un agent pèse 0."""
    if len(proposals) == 1:
        return proposals[0]
    total = sum(weights.get(p.strategy, 0.0) for p in proposals)
    if total <= 0:
        return proposals[0].__class__(**{**proposals[0].__dict__, "action": Action.NO_TRADE,
                                         "rationale": "aucun agent n'a de poids validé"})
    score: dict[Action, float] = {}
    for p in proposals:
        score[p.action] = score.get(p.action, 0.0) + weights.get(p.strategy, 0.0) / total
    best = max(score, key=score.get)
    if score[best] < 0.5:
        best = Action.NO_TRADE
    chosen = next((p for p in proposals if p.action == best), proposals[0])
    return chosen if chosen.action == best else Proposal(**{**chosen.__dict__, "action": best})


def order_id(asset: str, side: str, asof: datetime, strategy: str) -> str:
    """Identifiant déterministe : relancer le même cycle produit le même id, donc pas de doublon."""
    raw = f"{asset}|{side}|{asof.isoformat()}|{strategy}"
    return "atm-" + hashlib.sha256(raw.encode()).hexdigest()[:16]


def run_cycle(
    cfg: Config,
    strategies: list[Strategy],
    asset: str,
    history: pd.DataFrame,
    state: PortfolioState,
    now: datetime,
    kill_switch: bool = False,
    weights: dict[str, float] | None = None,
) -> CycleResult:
    risk = RiskManager(cfg)
    # Garde-fou anti-fuite : une barre qui commence à `now` ou après n'est pas close.
    history = history[history.index < pd.Timestamp(now)]
    last_price = float(history["close"].iloc[-1])
    prices = {asset: last_price}
    in_pos = asset in state.positions

    held_days = None
    if in_pos and state.positions[asset].opened_at:
        opened = datetime.fromisoformat(state.positions[asset].opened_at)
        held_days = (now - opened).days
    proposals = [s.propose(asset, history, now, in_pos, held_days=held_days) for s in strategies]
    decision = aggregate(proposals, weights or {s.name: 1.0 for s in strategies})

    # Suspension : on ne propose plus d'achat, on liquide les positions.
    suspended = risk.check_portfolio(state, prices) or (
        RiskVerdict(False, Action.SUSPEND_TRADING, "kill switch actif", suspend=True) if kill_switch else None
    )
    if suspended and in_pos:
        decision = Proposal(**{**decision.__dict__, "action": Action.SELL, "rationale": "procédure de sécurité : " + suspended.reason})

    verdict = risk.evaluate(decision, state, prices, now, kill_switch=kill_switch)
    order = None
    if verdict.approved and verdict.action == Action.BUY:
        order = Order(order_id(asset, "buy", decision.data_asof, decision.strategy), asset, "buy",
                      notional_eur=verdict.notional_eur, stop_pct=decision.stop_loss_pct)
    elif verdict.approved and verdict.action == Action.SELL:
        order = Order(order_id(asset, "sell", decision.data_asof, decision.strategy), asset, "sell",
                      quantity=state.positions[asset].quantity)
    return CycleResult(asset, proposals, decision, verdict, order)
