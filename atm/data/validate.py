"""Agent 2 — contrôle qualité des données OHLCV.

Format attendu : DataFrame indexé par horodatage UTC (début de barre), colonnes
open, high, low, close, volume.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

REQUIRED = ("open", "high", "low", "close", "volume")


@dataclass
class DataReport:
    ok: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def validate_ohlcv(df: pd.DataFrame, expected_freq: str = "1D", max_jump: float = 0.5) -> DataReport:
    errors: list[str] = []
    warnings: list[str] = []

    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        return DataReport(False, [f"colonnes manquantes : {missing}"])
    if df.empty:
        return DataReport(False, ["aucune donnée"])
    if not isinstance(df.index, pd.DatetimeIndex):
        return DataReport(False, ["index non temporel"])
    if df.index.tz is None:
        errors.append("horodatages sans fuseau (UTC exigé)")
    if not df.index.is_monotonic_increasing:
        errors.append("horodatages non croissants")
    if df.index.has_duplicates:
        errors.append("horodatages dupliqués")

    vals = df[list(REQUIRED)]
    if vals.isna().any().any():
        errors.append("valeurs manquantes (NaN)")
    if (df[["open", "high", "low", "close"]] <= 0).any().any():
        errors.append("prix nuls ou négatifs")
    if (df["volume"] < 0).any():
        errors.append("volume négatif")
    bad_hl = (df["high"] < df[["open", "close"]].max(axis=1)) | (df["low"] > df[["open", "close"]].min(axis=1))
    if bad_hl.any():
        errors.append(f"bougies incohérentes (high/low) : {int(bad_hl.sum())}")

    if len(df) > 1:
        step = pd.Timedelta(expected_freq)
        gaps = df.index.to_series().diff().dropna()
        n_gaps = int((gaps > step).sum())
        if n_gaps:
            warnings.append(f"{n_gaps} trou(s) dans la série")
        rets = np.log(df["close"]).diff().abs()
        n_jumps = int((rets > np.log1p(max_jump)).sum())
        if n_jumps:
            warnings.append(f"{n_jumps} variation(s) > {max_jump:.0%} en une barre : à vérifier (manipulation ou erreur)")
        if (df["volume"] == 0).mean() > 0.05:
            warnings.append("plus de 5 % de barres sans volume")

    return DataReport(not errors, errors, warnings)
