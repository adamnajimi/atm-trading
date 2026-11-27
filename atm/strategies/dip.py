"""Stratégie candidate : achat de repli dans une tendance haussière (RSI).

Hypothèse (non démontrée) : dans une tendance longue haussière (clôture > SMA200),
un repli court (RSI14 < 30) tend à être suivi d'un rebond qui couvre les frais
d'aller-retour (~1,8 %). Sortie quand le RSI repasse au-dessus de 55, après
`max_hold` jours, ou au stop.

Statut : CANDIDATE, évaluée uniquement en paper trading fantôme sur des données
postérieures au 2026-11-26 (le test final historique est consommé).
"""
from __future__ import annotations

from datetime import datetime

import pandas as pd

from ..models import Action, Proposal
from .base import Strategy
from .trend import atr


def rsi(close: pd.Series, window: int = 14) -> pd.Series:
    delta = close.diff()
    gain = delta.clip(lower=0).ewm(alpha=1 / window, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1 / window, adjust=False).mean()
    rs = gain / loss.replace(0, float("nan"))
    return (100 - 100 / (1 + rs)).fillna(100)


class RsiDip(Strategy):
    name = "rsi_dip"

    def __init__(self, trend_window: int = 200, rsi_window: int = 14, entry_rsi: float = 30.0,
                 exit_rsi: float = 55.0, max_hold: int = 10, atr_window: int = 14, stop_atr_multiple: float = 2.0):
        self.trend_window, self.rsi_window = trend_window, rsi_window
        self.entry_rsi, self.exit_rsi, self.max_hold = entry_rsi, exit_rsi, max_hold
        self.atr_window, self.stop_atr_multiple = atr_window, stop_atr_multiple

    @property
    def warmup(self) -> int:
        return max(self.trend_window, self.rsi_window, self.atr_window) + 1

    def propose(self, asset: str, history: pd.DataFrame, now: datetime, in_position: bool,
                held_days: int | None = None) -> Proposal:
        asof = history.index[-1].to_pydatetime()
        base = dict(asset=asset, timestamp=now, strategy=self.name, horizon="jours", data_asof=asof)
        if len(history) < self.warmup:
            return Proposal(action=Action.REQUEST_MORE_DATA, rationale="historique insuffisant", **base)
        close = history["close"]
        last = float(close.iloc[-1])
        sma = float(close.rolling(self.trend_window).mean().iloc[-1])
        r = float(rsi(close, self.rsi_window).iloc[-1])
        stop_pct = float(self.stop_atr_multiple * atr(history, self.atr_window).iloc[-1] / last)
        info = f"close={last:.2f} sma{self.trend_window}={sma:.2f} rsi={r:.1f} stop={stop_pct:.2%}"
        if in_position:
            if r > self.exit_rsi or (held_days is not None and held_days >= self.max_hold) or last < sma:
                return Proposal(action=Action.SELL, rationale="sortie : " + info, **base)
            return Proposal(action=Action.HOLD, rationale=info, **base)
        if last > sma and r < self.entry_rsi:
            return Proposal(action=Action.BUY, rationale="repli en tendance haussière : " + info, target_weight=1.0,
                            stop_loss_pct=stop_pct, invalidation=f"RSI > {self.exit_rsi}, {self.max_hold} jours, ou stop",
                            arguments_for=["tendance longue haussière", "survente courte"],
                            arguments_against=["avantage non démontré", "frais aller-retour ~1,8 %"], **base)
        return Proposal(action=Action.NO_TRADE, rationale=info, **base)
