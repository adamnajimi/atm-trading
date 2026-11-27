"""Stratégie candidate : suivi de tendance lent (SMA + momentum, stop ATR).

Hypothèse à tester (non démontrée) : les cryptos majeures présentent une
persistance de tendance sur plusieurs semaines suffisante pour couvrir des
frais d'aller-retour de ~1,8 %. Statut : CANDIDATE, non validée.
"""
from __future__ import annotations

from datetime import datetime

import pandas as pd

from ..models import Action, Proposal
from .base import Strategy


def atr(df: pd.DataFrame, window: int) -> pd.Series:
    prev = df["close"].shift(1)
    tr = pd.concat([df["high"] - df["low"], (df["high"] - prev).abs(), (df["low"] - prev).abs()], axis=1).max(axis=1)
    return tr.rolling(window).mean()


class TrendSMA(Strategy):
    name = "trend_sma"

    def __init__(self, sma_window: int = 100, momentum_window: int = 50, atr_window: int = 14, stop_atr_multiple: float = 3.0):
        self.sma_window = sma_window
        self.momentum_window = momentum_window
        self.atr_window = atr_window
        self.stop_atr_multiple = stop_atr_multiple

    @property
    def warmup(self) -> int:
        return max(self.sma_window, self.momentum_window, self.atr_window) + 1

    def propose(self, asset: str, history: pd.DataFrame, now: datetime, in_position: bool,
                held_days: int | None = None) -> Proposal:
        asof = history.index[-1].to_pydatetime()
        base = dict(asset=asset, timestamp=now, strategy=self.name, horizon="semaines", data_asof=asof)
        if len(history) < self.warmup:
            return Proposal(action=Action.REQUEST_MORE_DATA, rationale="historique insuffisant", **base)

        close = history["close"]
        sma = close.rolling(self.sma_window).mean().iloc[-1]
        mom = close.iloc[-1] / close.iloc[-1 - self.momentum_window] - 1
        a = atr(history, self.atr_window).iloc[-1]
        last = close.iloc[-1]
        stop_pct = float(self.stop_atr_multiple * a / last)
        bullish = last > sma and mom > 0
        info = f"close={last:.2f} sma{self.sma_window}={sma:.2f} mom{self.momentum_window}={mom:+.2%} stop={stop_pct:.2%}"

        if bullish and not in_position:
            return Proposal(
                action=Action.BUY, rationale="tendance haussière : " + info, target_weight=1.0,
                stop_loss_pct=stop_pct, invalidation=f"clôture sous SMA{self.sma_window} ou stop touché",
                arguments_for=["prix au-dessus de la moyenne", "momentum positif"],
                arguments_against=["avantage non démontré hors échantillon", "frais aller-retour élevés"], **base,
            )
        if not bullish and in_position:
            return Proposal(action=Action.SELL, rationale="fin de tendance : " + info, **base)
        return Proposal(action=Action.HOLD if in_position else Action.NO_TRADE, rationale=info, **base)
