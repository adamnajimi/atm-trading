from datetime import datetime, timedelta, timezone

from atm.models import Action, Proposal
from atm.portfolio import PortfolioState, Position
from atm.risk import RiskManager

NOW = datetime(2026, 1, 10, tzinfo=timezone.utc)


def buy(stop=0.08, age_h=1, weight=1.0, asset="BTC/EUR"):
    return Proposal(asset=asset, timestamp=NOW, action=Action.BUY, strategy="t", horizon="j",
                    data_asof=NOW - timedelta(hours=age_h), rationale="", target_weight=weight, stop_loss_pct=stop)


def fresh(cfg):
    return PortfolioState(cash_eur=cfg.risk.initial_eur, initial_eur=cfg.risk.initial_eur)


def test_buy_sized_so_stop_loss_fits_per_trade_cap(cfg):
    v = RiskManager(cfg).evaluate(buy(), fresh(cfg), {"BTC/EUR": 100.0}, NOW)
    assert v.approved
    worst = v.notional_eur * (0.08 * cfg.risk.gap_safety_factor + cfg.venue.round_trip_cost)
    assert worst <= cfg.risk.max_loss_per_trade_eur + 1e-9
    assert v.notional_eur >= cfg.venue.min_order_eur


def test_wide_stop_makes_order_too_small(cfg):
    v = RiskManager(cfg).evaluate(buy(stop=0.4), fresh(cfg), {"BTC/EUR": 100.0}, NOW)
    assert not v.approved and "minimum" in v.reason


def test_stale_data_rejected(cfg):
    v = RiskManager(cfg).evaluate(buy(age_h=48), fresh(cfg), {"BTC/EUR": 100.0}, NOW)
    assert not v.approved and v.action == Action.REQUEST_MORE_DATA


def test_missing_stop_rejected(cfg):
    v = RiskManager(cfg).evaluate(buy(stop=None), fresh(cfg), {"BTC/EUR": 100.0}, NOW)
    assert not v.approved


def test_kill_switch_blocks_buys(cfg):
    v = RiskManager(cfg).evaluate(buy(), fresh(cfg), {"BTC/EUR": 100.0}, NOW, kill_switch=True)
    assert not v.approved and v.suspend


def test_operational_loss_limit_suspends_and_is_sticky(cfg):
    s = fresh(cfg)
    s.cash_eur = cfg.risk.initial_eur - cfg.risk.operational_loss_limit_eur  # 7 € de perte
    rm = RiskManager(cfg)
    v = rm.evaluate(buy(), s, {"BTC/EUR": 100.0}, NOW)
    assert not v.approved and v.action == Action.SUSPEND_TRADING and s.suspended
    s.cash_eur = cfg.risk.initial_eur  # même si la perte disparaît, la suspension reste
    assert not rm.evaluate(buy(), s, {"BTC/EUR": 100.0}, NOW).approved


def test_unrealized_loss_counts(cfg):
    s = fresh(cfg)
    s.cash_eur = 2.0
    s.positions["ETH/EUR"] = Position(quantity=1.0, avg_price=18.0)
    # ETH tombe à 10 € : perte latente de ~8 € > 7 €
    v = RiskManager(cfg).evaluate(buy(), s, {"BTC/EUR": 100.0, "ETH/EUR": 10.0}, NOW)
    assert not v.approved and s.suspended


def test_daily_loss_limit(cfg):
    s = fresh(cfg)
    s.day_start_equity_eur = 20.0
    s.cash_eur = 17.5  # -2,5 € dans la journée
    v = RiskManager(cfg).evaluate(buy(), s, {"BTC/EUR": 100.0}, NOW)
    assert not v.approved and "journalière" in v.reason


def test_no_leverage_notional_never_exceeds_cash(cfg):
    s = PortfolioState(cash_eur=6.0, initial_eur=6.0)
    v = RiskManager(cfg).evaluate(buy(stop=0.02), s, {"BTC/EUR": 100.0}, NOW)
    assert v.approved and v.notional_eur * (1 + cfg.venue.one_way_cost) <= 6.0 + 1e-9


def test_sell_always_allowed_when_position_exists(cfg):
    s = fresh(cfg)
    s.suspended = True
    s.positions["BTC/EUR"] = Position(0.1, 100.0)
    p = buy()
    p.action = Action.SELL
    assert RiskManager(cfg).evaluate(p, s, {"BTC/EUR": 100.0}, NOW, kill_switch=True).approved
