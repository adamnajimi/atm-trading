"""Contrôle anti-biais de lookahead (idée reprise de la commande `lookahead-analysis` de Freqtrade,
GPL-3.0 : seule l'idée est reprise, aucun code copié).

Principe : les décisions prises jusqu'au jour t ne doivent pas changer si l'on ajoute des barres
futures aux données. Si elles changent, une stratégie ou le moteur regarde l'avenir.
"""
import pytest

from atm.backtest.engine import run_backtest
from atm.data.synthetic import random_walk_ohlcv
from atm.strategies.dip import RsiDip
from atm.strategies.trend import TrendSMA

STRATEGIES = [
    TrendSMA(),
    TrendSMA(sma_window=50, momentum_window=30, stop_atr_multiple=2.0),
    RsiDip(),
]


@pytest.mark.parametrize("strategy", STRATEGIES, ids=lambda s: f"{s.name}-{getattr(s, 'sma_window', '')}")
def test_no_lookahead_decisions(cfg, strategy):
    data = random_walk_ohlcv(700, start="2020-01-01", seed=11)
    full = run_backtest(cfg, [strategy], "BTC/EUR", data)
    for cut in (300, 450, 600):
        part = run_backtest(cfg, [strategy], "BTC/EUR", data.iloc[:cut])
        assert part.decisions == full.decisions[: len(part.decisions)], f"lookahead détecté avant la barre {cut}"
        assert part.trades == full.trades[: len(part.trades)]
