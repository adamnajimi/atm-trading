"""État du portefeuille (simulation ou réel), sérialisable en JSON."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class Position:
    quantity: float
    avg_price: float
    stop_price: float | None = None
    opened_at: str = ""


@dataclass
class PortfolioState:
    cash_eur: float
    initial_eur: float
    positions: dict[str, Position] = field(default_factory=dict)
    fees_paid_eur: float = 0.0
    realized_pnl_eur: float = 0.0
    suspended: bool = False
    suspend_reason: str = ""
    day: str = ""
    day_start_equity_eur: float | None = None
    processed_order_ids: list[str] = field(default_factory=list)
    trades: list[dict[str, Any]] = field(default_factory=list)

    # --- valorisation -------------------------------------------------
    def liquidation_equity(self, prices: dict[str, float], exit_cost: float) -> float:
        """Valeur si tout était vendu maintenant, frais et slippage de sortie déduits.

        C'est la base prudente utilisée pour mesurer la perte (réalisée + latente + frais).
        """
        value = self.cash_eur
        for asset, pos in self.positions.items():
            if asset not in prices:
                # prix inconnu : valorisation la plus prudente possible
                continue
            value += pos.quantity * prices[asset] * (1 - exit_cost)
        return value

    def loss_eur(self, prices: dict[str, float], exit_cost: float) -> float:
        return max(0.0, self.initial_eur - self.liquidation_equity(prices, exit_cost))

    def roll_day(self, day: str, prices: dict[str, float], exit_cost: float) -> None:
        if day != self.day:
            self.day = day
            self.day_start_equity_eur = self.liquidation_equity(prices, exit_cost)

    # --- persistance --------------------------------------------------
    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2, ensure_ascii=False)

    @classmethod
    def from_json(cls, text: str) -> "PortfolioState":
        d = json.loads(text)
        d["positions"] = {k: Position(**v) for k, v in d.get("positions", {}).items()}
        return cls(**d)

    def save(self, path: str | Path) -> None:
        p = Path(path)
        tmp = p.with_suffix(p.suffix + ".tmp")
        tmp.write_text(self.to_json(), encoding="utf-8")
        tmp.replace(p)  # écriture atomique

    @classmethod
    def load_or_new(cls, path: str | Path, initial_eur: float) -> "PortfolioState":
        p = Path(path)
        if p.exists():
            return cls.from_json(p.read_text(encoding="utf-8"))
        return cls(cash_eur=initial_eur, initial_eur=initial_eur)
