"""Agent 2 — inspection des anomalies signalées par la validation.

Pour chaque variation > 50 % en une barre et chaque trou, affiche les barres
voisines, la variation du même jour sur l'autre actif et, si disponible, la
barre correspondante d'une seconde source (Kraken).
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def find_anomalies(df: pd.DataFrame, max_jump: float = 0.5) -> dict:
    lr = np.log(df["close"]).diff()
    jumps = df.index[lr.abs() > np.log1p(max_jump)]
    gaps = df.index.to_series().diff()
    gap_rows = gaps[gaps > pd.Timedelta("1D")]
    intrabar = (df["high"] / df["low"] - 1)
    return {"jumps": list(jumps), "gaps": [(t - g, t) for t, g in gap_rows.items()],
            "max_intrabar_range": float(intrabar.max()), "max_intrabar_date": intrabar.idxmax()}


def describe(asset: str, df: pd.DataFrame, others: dict[str, pd.DataFrame], second_source: pd.DataFrame | None = None) -> str:
    a = find_anomalies(df)
    L = [f"### {asset}", ""]
    for t in a["jumps"]:
        i = df.index.get_loc(t)
        win = df.iloc[max(0, i - 2): i + 3][["open", "high", "low", "close", "volume"]]
        chg = df["close"].iloc[i] / df["close"].iloc[i - 1] - 1
        L.append(f"- Variation {chg:+.1%} le {t.date()} (clôture {df['close'].iloc[i-1]:.2f} → {df['close'].iloc[i]:.2f})")
        for name, o in others.items():
            if t in o.index and o.index.get_loc(t) > 0:
                j = o.index.get_loc(t)
                L.append(f"  - {name} le même jour : {o['close'].iloc[j] / o['close'].iloc[j-1] - 1:+.1%}")
        if second_source is not None and t in second_source.index:
            L.append(f"  - seconde source, clôture : {second_source.loc[t, 'close']:.2f}")
        L.append("```")
        L.append(win.round(2).to_string())
        L.append("```")
    for start, end in a["gaps"]:
        L.append(f"- Trou : aucune barre entre {start.date()} et {end.date()} ({(end - start).days - 1} jour(s) manquant(s))")
    L.append(f"- Plus grande amplitude intrajournalière : {a['max_intrabar_range']:.1%} le {a['max_intrabar_date'].date()}")
    return "\n".join(L) + "\n"
