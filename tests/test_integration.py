"""Tests d'intégration : backtest complet, scénarios de sécurité (étape F, partiel)."""
from datetime import timedelta

import numpy as np
import pytest

from atm.backtest.engine import run_backtest
from atm.data.synthetic import random_walk_ohlcv
from atm.orchestrator import run_cycle
from atm.portfolio import PortfolioState
from atm.strategies.trend import TrendSMA


@pytest.mark.parametrize("seed", range(5))
def test_backtest_never_breaches_hard_loss_limit(cfg, seed):
    data = random_walk_ohlcv(1200, vol=0.05, seed=seed)
    res = run_backtest(cfg, [TrendSMA()], "BTC/EUR", data)
    assert res.stats["max_loss_eur"] < cfg.risk.hard_loss_limit_eur
    assert res.final_state.cash_eur >= 0


def test_crash_scenario_triggers_stop_and_keeps_loss_bounded(cfg):
    data = random_walk_ohlcv(400, drift=0.004, vol=0.01, seed=1)  # tendance haussière -> position ouverte
    # Krach : gap de -60 % à l'ouverture de la barre 350, puis baisse continue
    i = 350
    for col in ("open", "high", "low", "close"):
        data.iloc[i:, data.columns.get_loc(col)] *= 0.4
    data.iloc[i, data.columns.get_loc("high")] = max(data["open"].iloc[i], data["close"].iloc[i]) * 1.001
    res = run_backtest(cfg, [TrendSMA()], "BTC/EUR", data)
    assert any(t["side"] == "buy" for t in res.trades), "le scénario doit ouvrir une position"
    assert res.stats["max_loss_eur"] < cfg.risk.hard_loss_limit_eur


def test_rerun_same_cycle_creates_no_duplicate(cfg):
    from atm.execution.paper import PaperBroker
    data = random_walk_ohlcv(400, drift=0.004, vol=0.01, seed=1)
    state = PortfolioState(cash_eur=20.0, initial_eur=20.0)
    now = (data.index[-1] + timedelta(days=1)).to_pydatetime()
    broker = PaperBroker(cfg.venue)
    ids = []
    for _ in range(2):  # GitHub Actions relance le même job
        res = run_cycle(cfg, [TrendSMA()], "BTC/EUR", data, state, now)
        if res.order:
            ids.append(res.order.client_order_id)
            broker.execute(res.order, res.verdict, state, float(data["close"].iloc[-1]), now)
    assert len(state.trades) <= 1
    # le même cycle recalculé donne le même identifiant d'ordre
    again = run_cycle(cfg, [TrendSMA()], "BTC/EUR", data, PortfolioState(20.0, 20.0), now)
    if ids and again.order:
        assert again.order.client_order_id == ids[0]


def test_incomplete_bar_is_ignored(cfg):
    data = random_walk_ohlcv(300, seed=2)
    now = data.index[-1].to_pydatetime()  # la dernière barre commence à `now` : pas close
    res = run_cycle(cfg, [TrendSMA()], "BTC/EUR", data, PortfolioState(20.0, 20.0), now)
    assert res.decision.data_asof < now


def test_kill_switch_liquidates(cfg):
    from atm.execution.paper import PaperBroker
    from atm.portfolio import Position
    data = random_walk_ohlcv(300, seed=2)
    state = PortfolioState(cash_eur=10.0, initial_eur=20.0)
    state.positions["BTC/EUR"] = Position(10.0 / float(data["close"].iloc[-1]), float(data["close"].iloc[-1]))
    now = (data.index[-1] + timedelta(days=1)).to_pydatetime()
    res = run_cycle(cfg, [TrendSMA()], "BTC/EUR", data, state, now, kill_switch=True)
    assert res.order is not None and res.order.side == "sell"
    PaperBroker(cfg.venue).execute(res.order, res.verdict, state, float(data["close"].iloc[-1]), now)
    assert not state.positions


def test_cli_backtest_synthetic(capsys, monkeypatch):
    from pathlib import Path
    from atm.cli import main
    monkeypatch.chdir(Path(__file__).resolve().parents[1])
    assert main(["backtest", "--synthetic"]) == 0
    assert "synthétiques" in capsys.readouterr().out
