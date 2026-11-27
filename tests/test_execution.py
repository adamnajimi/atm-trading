from datetime import datetime, timezone

import pytest

from atm.execution.live import LiveBroker, LiveTradingDisabled
from atm.execution.paper import ExecutionError, PaperBroker
from atm.models import Action, Order, RiskVerdict
from atm.portfolio import PortfolioState

TS = datetime(2026, 1, 1, tzinfo=timezone.utc)
OK_BUY = RiskVerdict(True, Action.BUY, "ok")
OK_SELL = RiskVerdict(True, Action.SELL, "ok")


def state():
    return PortfolioState(cash_eur=20.0, initial_eur=20.0)


def test_unapproved_order_refused(cfg):
    with pytest.raises(ExecutionError):
        PaperBroker(cfg.venue).execute(Order("a", "BTC/EUR", "buy", 6.0), RiskVerdict(False, Action.NO_TRADE, "x"), state(), 100, TS)


def test_duplicate_order_ignored(cfg):
    b, s = PaperBroker(cfg.venue), state()
    assert b.execute(Order("id1", "BTC/EUR", "buy", 6.0, stop_pct=0.1), OK_BUY, s, 100, TS)
    cash = s.cash_eur
    assert b.execute(Order("id1", "BTC/EUR", "buy", 6.0), OK_BUY, s, 100, TS) is None
    assert s.cash_eur == cash and len(s.trades) == 1


def test_fees_and_round_trip(cfg):
    b, s = PaperBroker(cfg.venue), state()
    b.execute(Order("b", "BTC/EUR", "buy", 10.0, stop_pct=0.1), OK_BUY, s, 100, TS)
    assert s.positions["BTC/EUR"].stop_price == pytest.approx(100 * (1 + cfg.venue.slippage) * 0.9)
    b.execute(Order("s", "BTC/EUR", "sell", quantity=s.positions["BTC/EUR"].quantity), OK_SELL, s, 100, TS)
    # prix inchangé : la perte est exactement le coût de l'aller-retour
    assert 20 - s.cash_eur == pytest.approx(s.fees_paid_eur + 10 * (1 - (1 - cfg.venue.slippage) / (1 + cfg.venue.slippage)), rel=1e-6)
    assert s.cash_eur < 20.0


def test_min_order_and_balance(cfg):
    b = PaperBroker(cfg.venue)
    with pytest.raises(ExecutionError):
        b.execute(Order("m", "BTC/EUR", "buy", 4.0), OK_BUY, state(), 100, TS)
    with pytest.raises(ExecutionError):
        b.execute(Order("n", "BTC/EUR", "buy", 25.0), OK_BUY, state(), 100, TS)


def test_live_broker_is_disabled(cfg, monkeypatch):
    monkeypatch.setenv("ATM_LIVE_CONFIRM", "J'AUTORISE LE TRADING REEL AVEC 20 EUR")
    with pytest.raises(LiveTradingDisabled):
        LiveBroker(cfg)
