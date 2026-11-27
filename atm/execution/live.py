"""Exécution réelle — DÉSACTIVÉE.

Ce module ne contient volontairement aucun appel d'ordre réel. Il sera écrit
à l'étape G, après validation des étapes C à F et accord explicite d'Adam.
Même alors, il exigera : `execution.live_trading_enabled: true`, `mode: live`
et la variable `ATM_LIVE_CONFIRM` égale à la phrase ci-dessous.
"""
from __future__ import annotations

import os

from ..config import Config

CONFIRM_PHRASE = "J'AUTORISE LE TRADING REEL AVEC 20 EUR"


class LiveTradingDisabled(RuntimeError):
    pass


class LiveBroker:
    def __init__(self, cfg: Config):
        if not cfg.live_trading_enabled or cfg.mode != "live":
            raise LiveTradingDisabled("trading réel désactivé dans la configuration")
        if os.environ.get("ATM_LIVE_CONFIRM") != CONFIRM_PHRASE:
            raise LiveTradingDisabled("confirmation explicite absente")
        raise LiveTradingDisabled("exécution réelle non implémentée avant l'étape G")
