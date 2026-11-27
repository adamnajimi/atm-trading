import pandas as pd
import pytest

from atm.data.synthetic import random_walk_ohlcv
from atm.research import FINAL_TEST_START, _segment, run_research, to_markdown
from atm.strategies.trend import TrendSMA


def test_research_never_touches_final_test(cfg):
    df = random_walk_ohlcv(3600, start="2016-01-01", seed=4)
    res = run_research(cfg, {"BTC/EUR": df})
    assert res["protocol"]["final_test_run"] is False
    assert all(pd.Timestamp(s["end"]) < pd.Timestamp(FINAL_TEST_START) for s in res["segments"])
    assert {s["segment"] for s in res["segments"]} == {"entrainement", "validation"}
    assert len(res["sensitivity"]) == 12
    assert "non exécuté" in to_markdown(res)


def test_segment_starts_with_initial_capital(cfg):
    df = random_walk_ohlcv(3600, start="2016-01-01", seed=5)
    r = _segment(cfg, TrendSMA(), "BTC/EUR", df, "2022-01-01", "2023-12-31")
    assert r.start == "2022-01-01"


def test_final_test_period_refused(cfg):
    df = random_walk_ohlcv(3600, start="2016-01-01", seed=4)
    with pytest.raises(ValueError):
        _segment(cfg, TrendSMA(), "BTC/EUR", df, "2024-01-01", "2025-01-01")
