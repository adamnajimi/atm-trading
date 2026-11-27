"""Format de communication standardisé entre agents."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class Action(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"
    NO_TRADE = "NO_TRADE"
    REQUEST_MORE_DATA = "REQUEST_MORE_DATA"
    SUSPEND_TRADING = "SUSPEND_TRADING"


@dataclass
class Proposal:
    """Proposition émise par un agent de stratégie (section 5 du cahier des charges)."""

    asset: str
    timestamp: datetime
    action: Action
    strategy: str
    horizon: str
    data_asof: datetime
    rationale: str
    target_weight: float = 0.0          # fraction du capital visée (0 = à plat)
    stop_loss_pct: float | None = None  # distance du stop en fraction du prix
    expected_return: float | None = None  # None tant qu'aucune estimation hors échantillon n'existe
    uncertainty: str = "non estimée"
    estimated_risk_eur: float | None = None
    estimated_costs_eur: float | None = None
    invalidation: str = ""
    arguments_for: list[str] = field(default_factory=list)
    arguments_against: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["action"] = self.action.value
        d["timestamp"] = self.timestamp.isoformat()
        d["data_asof"] = self.data_asof.isoformat()
        return d


@dataclass
class RiskVerdict:
    approved: bool
    action: Action
    reason: str
    notional_eur: float = 0.0
    suspend: bool = False


@dataclass
class Order:
    client_order_id: str
    asset: str
    side: str  # "buy" | "sell"
    notional_eur: float | None = None  # pour un achat
    quantity: float | None = None      # pour une vente
    stop_price: float | None = None
    stop_pct: float | None = None  # stop relatif au prix d'exécution réel


@dataclass
class Fill:
    client_order_id: str
    asset: str
    side: str
    quantity: float
    price: float
    fee_eur: float
    timestamp: datetime
