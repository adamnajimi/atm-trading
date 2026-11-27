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
