import copy
from pathlib import Path

import pytest
import yaml

from atm.config import from_dict

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def raw_cfg():
    return yaml.safe_load((ROOT / "config" / "config.yaml").read_text(encoding="utf-8"))


@pytest.fixture
def cfg(raw_cfg):
    return from_dict(copy.deepcopy(raw_cfg))
