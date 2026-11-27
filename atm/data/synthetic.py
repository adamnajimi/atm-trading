"""Données SYNTHÉTIQUES pour les tests uniquement.

Ces séries ne représentent aucun marché réel. Aucun résultat obtenu avec elles
ne doit être présenté comme une performance de stratégie.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def random_walk_ohlcv(
    n: int = 1000,
    start: str = "2020-01-01",
    price0: float = 30000.0,
    drift: float = 0.0,
    vol: float = 0.03,
    seed: int = 0,
) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rets = rng.normal(drift, vol, n)
    close = price0 * np.exp(np.cumsum(rets))
    open_ = np.concatenate([[price0], close[:-1]]) * np.exp(rng.normal(0, vol / 4, n))
    hi = np.maximum(open_, close) * np.exp(np.abs(rng.normal(0, vol / 2, n)))
    lo = np.minimum(open_, close) * np.exp(-np.abs(rng.normal(0, vol / 2, n)))
    vol_ = rng.uniform(100, 1000, n)
    idx = pd.date_range(start, periods=n, freq="1D", tz="UTC")
    return pd.DataFrame({"open": open_, "high": hi, "low": lo, "close": close, "volume": vol_}, index=idx)
