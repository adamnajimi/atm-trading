import json

import pytest

from atm.backtest.metrics import dca
from atm.checks import describe, find_anomalies
from atm.data.synthetic import random_walk_ohlcv
from atm.final_test import DONE_MARKER, FinalTestRefused, run_final_test


def test_dca_invests_four_parts_and_flat_price_loses_only_costs(cfg):
    df = random_walk_ohlcv(400, vol=0.0, seed=0)
    v = dca(df, cfg)
    c = cfg.venue.one_way_cost
    assert v.iloc[0] == pytest.approx(15 + 5 * (1 - c) ** 2, rel=1e-9)
    assert v.iloc[-1] == pytest.approx(20 * (1 - c) ** 2, rel=1e-9)


def test_final_test_runs_once(cfg, tmp_path):
    df = random_walk_ohlcv(3600, start="2016-01-01", seed=7)
    r = run_final_test(cfg, df, root=tmp_path)
    assert r["period"][0] == "2024-07-01" and set(r["checks"]) and "passed" in r
    (tmp_path / DONE_MARKER).parent.mkdir(parents=True)
    (tmp_path / DONE_MARKER).write_text(json.dumps({"done": True}))
    with pytest.raises(FinalTestRefused):
        run_final_test(cfg, df, root=tmp_path)


def test_final_test_refuses_changed_params(raw_cfg, tmp_path):
    from atm.config import from_dict
    raw_cfg["strategies"]["trend_sma"]["params"]["sma_window"] = 50
    with pytest.raises(FinalTestRefused):
        run_final_test(from_dict(raw_cfg), random_walk_ohlcv(3600, start="2016-01-01"), root=tmp_path)


def test_anomalies_found():
    df = random_walk_ohlcv(200, vol=0.01)
    df.iloc[100:, :4] *= 2.0
    df.iloc[100, df.columns.get_loc("low")] = df[["open", "close"]].iloc[100].min()
    df = df.drop(df.index[150])
    a = find_anomalies(df)
    assert len(a["jumps"]) == 1 and len(a["gaps"]) == 1
    assert "Variation" in describe("X", df, {})
