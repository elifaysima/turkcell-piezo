from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict
import math
import time


def hour_of_week(ts: int) -> int:
    """
    Unix seconds -> hour-of-week [0..167]
    localtime kullanır (makinenin local saatine göre).
    """
    lt = time.localtime(ts)
    return int(lt.tm_wday) * 24 + int(lt.tm_hour)


@dataclass
class SlotStats:
    n: int = 0
    mean: float = 0.0
    m2: float = 0.0 # Welford

    def update(self, x: float) -> None:
        self.n += 1
        delta = x - self.mean
        self.mean += delta / self.n
        delta2 = x - self.mean
        self.m2 += delta * delta2

    def variance(self) -> float:
        return (self.m2 / (self.n - 1)) if self.n > 1 else 0.0

    def std(self) -> float:
        return math.sqrt(max(self.variance(), 0.0))


@dataclass
class SeasonalModel:
    """
    Site bazında hour-of-week slotları için online mean/std tutar.
    """
    min_n_for_z: int = 20
    slots: Dict[int, SlotStats] = field(default_factory=dict)

    def _slot(self, idx: int) -> SlotStats:
        if idx not in self.slots:
            self.slots[idx] = SlotStats()
        return self.slots[idx]

    def update(self, ts: int, flow: float) -> None:
        idx = hour_of_week(ts)
        self._slot(idx).update(float(flow))

    def zscore(self, ts: int, flow: float) -> float:
        idx = hour_of_week(ts)
        st = self._slot(idx)
        if st.n < self.min_n_for_z:
            return 0.0
        sd = st.std()
        if sd <= 1e-9:
            return 0.0
        return (float(flow) - st.mean) / sd

