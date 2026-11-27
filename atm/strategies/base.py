"""Contrat commun des agents de stratégie."""
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

import pandas as pd

from ..models import Proposal


class Strategy(ABC):
    name: str = "base"

    @property
    def warmup(self) -> int:
        """Nombre de barres nécessaires avant la première décision."""
        return 1

    @abstractmethod
    def propose(self, asset: str, history: pd.DataFrame, now: datetime, in_position: bool) -> Proposal:
        """`history` ne contient que des barres closes à `now` (garanti par l'appelant)."""
