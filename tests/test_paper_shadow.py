from datetime import timedelta

import pandas as pd

from atm.data.synthetic import random_walk_ohlcv
from atm.execution.paper import PaperBroker
from atm.portfolio import PortfolioState, Position
from atm.strategies.dip import RsiDip, rsi


def recent(n=320, seed=1, drift=0.0):
    start = (pd.Timestamp.now(tz="UTC").normalize() - pd.Timedelta(days=n)).strftime("%Y-%m-%d")
    return random_walk_ohlcv(n, start=start, seed=seed, drift=drift)


def test_paper_cycle_runs_main_and_shadows(tmp_path, monkeypatch):
    import atm.data.fetch as fetch
    from atm.cli import main
    monkeypatch.setattr(fetch, "fetch_daily_ohlcv", lambda *a, **k: recent())
    root = tmp_path
    (root / "config").mkdir()
    cfg_text = open("config/config.yaml", encoding="utf-8").read().replace('since: "2026-11-28"', 'since: "2000-01-01"')
    (root / "config" / "config.yaml").write_text(cfg_text, encoding="utf-8")
    rc = main(["--config", str(root / "config" / "config.yaml"), "--root", str(root), "paper"])
    assert rc == 0
    assert (root / "state" / "portfolio.json").exists()
    assert (root / "state" / "shadow" / "trend_sma_fast.json").exists()
    assert (root / "state" / "shadow" / "trend_sma_risk15.json").exists()
    assert not (root / "state" / "shadow" / "rsi_dip.json").exists()  # rejetée au backtest
    report = next((root / "state" / "reports").glob("*.md")).read_text(encoding="utf-8")
    assert "portefeuilles fantômes" in report
    # relancer le même jour ne crée aucun ordre en double
    before = PortfolioState.from_json((root / "state" / "portfolio.json").read_text()).trades
    main(["--config", str(root / "config" / "config.yaml"), "--root", str(root), "paper"])
    after = PortfolioState.from_json((root / "state" / "portfolio.json").read_text()).trades
    assert len(after) == len(before)


def test_apply_stop_sells_at_stop_or_gap(cfg):
    from atm.cli import apply_stop
    df = recent(30)
    bar = df.iloc[-1].copy()
    st = PortfolioState(cash_eur=10.0, initial_eur=20.0)
    st.positions["BTC/EUR"] = Position(0.001, 10000.0, stop_price=float(bar["low"]) * 1.01)
    fill = apply_stop(st, "BTC/EUR", bar, PaperBroker(cfg.venue), df.index[-1].to_pydatetime() + timedelta(days=1))
    assert fill is not None and not st.positions
    assert fill.price <= min(float(bar["open"]), float(bar["low"]) * 1.01)


def test_rsi_bounds_and_dip_no_lookahead():
    df = random_walk_ohlcv(500, seed=9)
    r = rsi(df["close"])
    assert r.between(0, 100).all()
    s = RsiDip()
    changed = df.copy()
    changed.iloc[400:] *= 0.3
    for i in range(s.warmup, 400, 7):
        now = (df.index[i] + timedelta(days=1)).to_pydatetime()
        assert s.propose("X", df.iloc[: i + 1], now, False).action == s.propose("X", changed.iloc[: i + 1], now, False).action
