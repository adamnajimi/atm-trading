from datetime import timedelta

import numpy as np

from atm.data.synthetic import random_walk_ohlcv
from atm.data.validate import validate_ohlcv
from atm.models import Action
from atm.strategies.trend import TrendSMA


def test_synthetic_data_is_valid():
    assert validate_ohlcv(random_walk_ohlcv(300)).ok


def test_validator_catches_errors():
    df = random_walk_ohlcv(50)
    bad = df.copy()
    bad.iloc[5, bad.columns.get_loc("close")] = np.nan
    assert not validate_ohlcv(bad).ok
    bad = df.copy()
    bad.iloc[7, bad.columns.get_loc("high")] = bad["low"].iloc[7] / 2
    assert not validate_ohlcv(bad).ok
    assert not validate_ohlcv(df.iloc[::-1]).ok
    assert not validate_ohlcv(df.tz_localize(None)).ok
    assert validate_ohlcv(df.drop(df.index[10])).warnings  # trou détecté


def test_strategy_needs_warmup():
    df = random_walk_ohlcv(50)
    p = TrendSMA().propose("BTC/EUR", df, df.index[-1].to_pydatetime(), False)
    assert p.action == Action.REQUEST_MORE_DATA


def test_strategy_does_not_look_ahead():
    """Modifier le futur ne doit changer aucune décision passée."""
    df = random_walk_ohlcv(400, seed=3)
    s = TrendSMA()
    future_changed = df.copy()
    future_changed.iloc[300:] *= 3.0
    for i in range(s.warmup, 300):
        now = (df.index[i] + timedelta(days=1)).to_pydatetime()
        a = s.propose("X", df.iloc[: i + 1], now, False)
        b = s.propose("X", future_changed.iloc[: i + 1], now, False)
        assert a.action == b.action and a.stop_loss_pct == b.stop_loss_pct
