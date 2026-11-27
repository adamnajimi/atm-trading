"""Agent 13 — exécution simulée (mode par défaut).

N'exécute que des ordres accompagnés d'un `RiskVerdict` approuvé, refuse les
doublons (identifiant d'ordre déjà traité) et applique frais, slippage et minimums.
"""
from __future__ import annotations

from datetime import datetime

from ..config import VenueConfig
from ..models import Fill, Order, RiskVerdict
from ..portfolio import PortfolioState, Position


class ExecutionError(RuntimeError):
    pass


class PaperBroker:
    def __init__(self, venue: VenueConfig):
        self.v = venue

    def execute(self, order: Order, verdict: RiskVerdict, state: PortfolioState, price: float, ts: datetime) -> Fill | None:
        if not verdict.approved:
            raise ExecutionError("ordre sans autorisation du risque")
        if order.client_order_id in state.processed_order_ids:
            return None  # doublon : ignoré, idempotence
        if price <= 0:
            raise ExecutionError("prix invalide")

        if order.side == "buy":
            fill = self._buy(order, state, price, ts)
        elif order.side == "sell":
            fill = self._sell(order, state, price, ts)
        else:
            raise ExecutionError(f"côté inconnu : {order.side}")

        state.processed_order_ids.append(order.client_order_id)
        state.processed_order_ids[:] = state.processed_order_ids[-500:]
        if fill:
            state.trades.append({
                "id": fill.client_order_id, "asset": fill.asset, "side": fill.side,
                "qty": fill.quantity, "price": fill.price, "fee": fill.fee_eur, "ts": ts.isoformat(),
            })
        return fill

    def _buy(self, order: Order, state: PortfolioState, price: float, ts: datetime) -> Fill:
        notional = float(order.notional_eur or 0)
        if notional < self.v.min_order_eur:
            raise ExecutionError("montant inférieur au minimum d'ordre")
        fee = notional * self.v.taker_fee
        if notional + fee > state.cash_eur + 1e-9:
            raise ExecutionError("solde insuffisant")
        exec_price = price * (1 + self.v.slippage)
        qty = notional / exec_price
        state.cash_eur -= notional + fee
        state.fees_paid_eur += fee
        stop = exec_price * (1 - order.stop_pct) if order.stop_pct else order.stop_price
        state.positions[order.asset] = Position(qty, exec_price, stop, ts.isoformat())
        return Fill(order.client_order_id, order.asset, "buy", qty, exec_price, fee, ts)

    def _sell(self, order: Order, state: PortfolioState, price: float, ts: datetime) -> Fill:
        pos = state.positions.get(order.asset)
        if pos is None:
            raise ExecutionError("aucune position à vendre")
        exec_price = price * (1 - self.v.slippage)
        gross = pos.quantity * exec_price
        fee = gross * self.v.taker_fee
        state.cash_eur += gross - fee
        state.fees_paid_eur += fee
        state.realized_pnl_eur += gross - fee - pos.quantity * pos.avg_price
        del state.positions[order.asset]
        return Fill(order.client_order_id, order.asset, "sell", pos.quantity, exec_price, fee, ts)
