import pytest

from atm.events import emit, read_events, span


def test_span_records_success_and_error(tmp_path):
    p = tmp_path / "ev.jsonl"
    with span(p, "donnees", "telechargement", "x") as sp:
        sp.result = {"api_key": "abc", "n": 3}
    with pytest.raises(RuntimeError):
        with span(p, "donnees", "telechargement", "y"):
            raise RuntimeError("panne")
    a, b = read_events(p)
    assert a["status"] == "termine" and a["result"]["api_key"] == "***"  # jamais de secret
    assert b["status"] == "erreur" and "panne" in b["errors"][0]


def test_bad_status_and_corrupt_line(tmp_path):
    p = tmp_path / "ev.jsonl"
    with pytest.raises(ValueError):
        emit(p, "a", "t", "x", "en_cours_invente")
    emit(p, "a", "t", "x", "termine")
    with open(p, "a") as f:
        f.write("{abîmé\n")
    assert len(read_events(p)) == 1


def test_dashboard_without_data(tmp_path):
    from atm.dashboard import build
    page = build(tmp_path)
    assert "aucun" in page and "<script" in page
