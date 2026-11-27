"""Téléchargement des prix publics via CCXT (aucune clé API, aucun compte).

Source historique par défaut : Coinbase Exchange (bougies journalières paginées,
historique long). Kraken ne renvoie que les 720 dernières bougies par son
endpoint OHLC : il sert de source de contrôle et de prix courant.

Non exécutable dans le conteneur cloud de développement (proxy bloquant) :
destiné à GitHub Actions ou au Mac d'Adam.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

DAY_MS = 86_400_000


def fetch_daily_ohlcv(symbol: str = "BTC/EUR", exchange_id: str = "coinbaseexchange",
                      since: str | None = None, page_limit: int = 300, max_pages: int = 100) -> pd.DataFrame:
    import ccxt  # dépendance optionnelle pour les tests

    ex = getattr(ccxt, exchange_id)({"enableRateLimit": True})
    now_ms = ex.milliseconds()
    since_ms = ex.parse8601(since) if since else None
    rows: list[list[float]] = []
    if since_ms is None:
        rows = ex.fetch_ohlcv(symbol, timeframe="1d", limit=page_limit)
    else:
        for _ in range(max_pages):
            if since_ms >= now_ms:
                break
            batch = ex.fetch_ohlcv(symbol, timeframe="1d", since=since_ms, limit=page_limit)
            if not batch:
                # aucun échange sur cette fenêtre (avant la cotation) : on avance d'une page
                since_ms += page_limit * DAY_MS
                continue
            rows.extend(batch)
            nxt = batch[-1][0] + DAY_MS
            if nxt <= since_ms:
                break
            since_ms = nxt
    if not rows:
        raise RuntimeError(f"aucune donnée pour {symbol} sur {exchange_id}")
    df = pd.DataFrame(rows, columns=["ts", "open", "high", "low", "close", "volume"]).drop_duplicates("ts").sort_values("ts")
    df.index = pd.to_datetime(df.pop("ts"), unit="ms", utc=True)
    df.index.name = "timestamp"
    # La barre du jour en cours n'est pas close : exclue (pas de donnée future).
    today = pd.Timestamp.now(tz="UTC").normalize()
    return df[df.index < today].astype(float)


def save_csv(df: pd.DataFrame, path: str | Path) -> None:
    df.to_csv(path, index_label="timestamp")


def load_csv(path: str | Path) -> pd.DataFrame:
    df = pd.read_csv(path, index_col="timestamp")
    df.index = pd.to_datetime(df.index, utc=True)
    return df
