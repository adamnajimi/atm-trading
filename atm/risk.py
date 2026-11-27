"""Agent 10 — Chief Risk Officer.

Module déterministe avec droit de veto absolu. Aucun autre module ne peut
approuver un ordre : l'exécution n'accepte que des `RiskVerdict` approuvés
produits ici. Les limites viennent d'une configuration figée et validée.
"""
from __future__ import annotations

import math
from datetime import datetime, timedelta

from .config import Config
from .models import Action, Proposal, RiskVerdict
from .portfolio import PortfolioState


class RiskManager:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.r = cfg.risk
        self.v = cfg.venue

    # ------------------------------------------------------------------
    def check_portfolio(self, state: PortfolioState, prices: dict[str, float]) -> RiskVerdict | None:
        """Contrôles globaux. Retourne un verdict de suspension si une limite est atteinte."""
        loss = state.loss_eur(prices, self.v.one_way_cost)
        if loss >= self.r.operational_loss_limit_eur:
            state.suspended = True
            state.suspend_reason = (
                f"perte cumulée {loss:.2f} € >= limite opérationnelle "
                f"{self.r.operational_loss_limit_eur:.2f} €"
            )
        if state.suspended:
            return RiskVerdict(False, Action.SUSPEND_TRADING, state.suspend_reason, suspend=True)
        return None

    # ------------------------------------------------------------------
    def evaluate(
        self,
        proposal: Proposal,
        state: PortfolioState,
        prices: dict[str, float],
        now: datetime,
        kill_switch: bool = False,
    ) -> RiskVerdict:
        a = proposal.action

        # Les ventes réduisent le risque : toujours autorisées si une position existe.
        if a == Action.SELL:
            if proposal.asset in state.positions:
                return RiskVerdict(True, Action.SELL, "réduction d'exposition")
            return RiskVerdict(False, Action.NO_TRADE, "aucune position à vendre")

        if a != Action.BUY:
            return RiskVerdict(False, a, "aucun ordre à autoriser")

        if kill_switch:
            return RiskVerdict(False, Action.SUSPEND_TRADING, "kill switch actif", suspend=True)

        suspended = self.check_portfolio(state, prices)
        if suspended:
            return suspended

        price = prices.get(proposal.asset)
        if price is None or price <= 0:
            return RiskVerdict(False, Action.REQUEST_MORE_DATA, "prix indisponible")

        if now - proposal.data_asof > timedelta(hours=self.r.max_data_age_hours):
            return RiskVerdict(False, Action.REQUEST_MORE_DATA, "données obsolètes")

        if proposal.asset in state.positions:
            return RiskVerdict(False, Action.HOLD, "position déjà ouverte sur cet actif")

        if proposal.stop_loss_pct is None or not 0 < proposal.stop_loss_pct < 0.5:
            return RiskVerdict(False, Action.NO_TRADE, "stop absent ou invalide")

        equity = state.liquidation_equity(prices, self.v.one_way_cost)
        loss_now = max(0.0, state.initial_eur - equity)

        # Limite journalière
        if state.day_start_equity_eur is not None:
            daily_loss = state.day_start_equity_eur - equity
            if daily_loss >= self.r.max_daily_loss_eur:
                return RiskVerdict(False, Action.NO_TRADE, "limite de perte journalière atteinte")

        # Budget de perte restant avant la limite opérationnelle
        remaining = self.r.operational_loss_limit_eur - loss_now
        per_trade_cap = min(self.r.max_loss_per_trade_eur, remaining)
        if per_trade_cap <= 0:
            return RiskVerdict(False, Action.SUSPEND_TRADING, "budget de perte épuisé", suspend=True)

        # Perte par euro investi si le stop est touché, gaps et frais aller-retour inclus
        loss_per_eur = proposal.stop_loss_pct * self.r.gap_safety_factor + self.v.round_trip_cost
        max_notional_risk = per_trade_cap / loss_per_eur
        max_notional_weight = max(0.0, proposal.target_weight) * equity * self.r.max_position_weight
        # Pas de levier : jamais plus que le cash disponible, frais d'entrée compris
        max_notional_cash = state.cash_eur / (1 + self.v.one_way_cost)

        notional = min(max_notional_risk, max_notional_weight, max_notional_cash)
        if notional < self.v.min_order_eur:
            return RiskVerdict(
                False,
                Action.NO_TRADE,
                f"taille autorisée {notional:.2f} € < minimum d'ordre {self.v.min_order_eur:.2f} €",
            )
        notional = math.floor(notional * 100) / 100  # arrondi vers le bas : jamais au-dessus des limites
        return RiskVerdict(True, Action.BUY, "dans les limites", notional_eur=notional)
