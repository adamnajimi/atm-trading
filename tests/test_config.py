import copy

import pytest

from atm.config import ConfigError, from_dict


def test_default_config_is_valid(cfg):
    assert cfg.risk.hard_loss_limit_eur == 10.0
    assert cfg.risk.operational_loss_limit_eur < cfg.risk.hard_loss_limit_eur
    assert cfg.mode == "paper" and cfg.live_trading_enabled is False


@pytest.mark.parametrize("section,key,value", [
    ("capital", "hard_loss_limit_eur", 15.0),
    ("capital", "operational_loss_limit_eur", 10.0),
    ("capital", "initial_eur", 100.0),
    ("risk", "leverage_allowed", True),
    ("risk", "max_position_weight", 2.0),
    ("risk", "gap_safety_factor", 0.5),
])
def test_relaxed_limits_are_refused(raw_cfg, section, key, value):
    d = copy.deepcopy(raw_cfg)
    d[section][key] = value
    with pytest.raises(ConfigError):
        from_dict(d)


def test_risk_trial_bounds(cfg):
    from atm.config import with_risk_trial
    t = with_risk_trial(cfg, {"max_loss_per_trade_eur": 1.5})
    assert t.risk.max_loss_per_trade_eur == 1.5 and cfg.risk.max_loss_per_trade_eur == 1.0
    assert t.risk.operational_loss_limit_eur == 7.0 and t.risk.hard_loss_limit_eur == 10.0
    for bad in ({"operational_loss_limit_eur": 9.0}, {"hard_loss_limit_eur": 15.0}, {"leverage_allowed": True},
                {"max_loss_per_trade_eur": 5.0}, {"gap_safety_factor": 1.0}):
        with pytest.raises(ConfigError):
            with_risk_trial(cfg, bad)


def test_shadow_overrides_bounded(cfg):
    import pytest
    from atm.config import ConfigError, with_shadow_overrides
    s = with_shadow_overrides(cfg, {"venue": "bitvavo", "shadow_capital": {"initial_eur": 50, "hard_loss_limit_eur": 15,
                                    "operational_loss_limit_eur": 12, "max_loss_per_trade_eur": 1.5, "max_daily_loss_eur": 3}})
    assert s.risk.initial_eur == 50 and s.venue.taker_fee == 0.0025 and s.venue.slippage == cfg.venue.slippage
    assert cfg.risk.initial_eur == 20 and cfg.venue.taker_fee == 0.008  # le principal ne bouge pas
    for bad in ({"shadow_capital": {"initial_eur": 100}}, {"shadow_capital": {"hard_loss_limit_eur": 25}},
                {"shadow_capital": {"leverage_allowed": True}}, {"venue": "xm"},
                {"shadow_capital": {"operational_loss_limit_eur": 12, "hard_loss_limit_eur": 11}}):
        with pytest.raises(ConfigError):
            with_shadow_overrides(cfg, bad)
