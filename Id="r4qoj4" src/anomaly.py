from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple
import math
import time

from seasonal import SeasonalModel


@dataclass
class Thresholds:
    # EWMA spike
    ewma_alpha: float = 0.2
    ewma_z_spike: float = 4.0

    # seasonal spike
    seasonal_z_spike: float = 4.0

    # min flow to consider spike
    flow_min_spike: float = 2.0

    # one-sided crowding
    one_sided_ratio_hi: float = 0.85
    one_sided_flow_min: float = 4.0

    # low-demand window "should be quiet"
    low_demand_flow: float = 3.0
    low_demand_hours: Tuple[int, int] = (0, 5) # local hours inclusive


@dataclass
class EwmaState:
    n: int = 0
    mean: float = 0.0
    var: float = 1.0

    def update(self, x: float, alpha: float) -> None:
        x = float(x)
        if self.n == 0:
            self.mean = x
            self.var = 1.0
            self.n = 1
            return
        prev = self.mean
        self.mean = alpha * x + (1 - alpha) * self.mean
        resid = x - prev
        self.var = alpha * (resid ** 2) + (1 - alpha) * self.var
        self.n += 1

    def z(self, x: float) -> float:
        sd = math.sqrt(max(self.var, 1e-6))
        return (float(x) - self.mean) / sd


# global per-site states (simple demo implementation)
SEASONAL: Dict[str, SeasonalModel] = {}
EWMA: Dict[str, EwmaState] = {}
THR = Thresholds()


def _get_seasonal(site_id: str) -> SeasonalModel:
    if site_id not in SEASONAL:
        SEASONAL[site_id] = SeasonalModel()
    return SEASONAL[site_id]


def _get_ewma(site_id: str) -> EwmaState:
    if site_id not in EWMA:
        EWMA[site_id] = EwmaState()
    return EWMA[site_id]


def detect(
    site_id: str,
    steps1: int,
    steps2: int,
    window_s: int,
    ts: int,
    thr: Thresholds = THR,
) -> Tuple[List[dict], dict]:
    """
    Anomali tespiti.
    Inputlar pencere toplamlarıdır (genelde 1 saniyelik).
    Returns: (alerts, debug)
    """
    s1 = max(int(steps1), 0)
    s2 = max(int(steps2), 0)
    flow = (s1 + s2) / max(int(window_s), 1)
    ratio = s1 / max(s1 + s2, 1)

    alerts: List[dict] = []
    dbg = {"flow": flow, "ratio": ratio}

    sm = _get_seasonal(site_id)
    z_seas = sm.zscore(ts, flow)
    sm.update(ts, flow)
    dbg["z_seasonal"] = z_seas

    ew = _get_ewma(site_id)
    ew.update(flow, thr.ewma_alpha)
    z_ew = ew.z(flow)
    dbg["z_ewma"] = z_ew

    if flow >= thr.flow_min_spike and z_ew >= thr.ewma_z_spike:
        alerts.append({"type": "SPIKE_EWMA", "z": float(z_ew), "flow": float(flow)})

    if flow >= thr.flow_min_spike and z_seas >= thr.seasonal_z_spike:
        alerts.append({"type": "SPIKE_SEASONAL", "z": float(z_seas), "flow": float(flow)})

    if flow >= thr.one_sided_flow_min and (ratio >= thr.one_sided_ratio_hi or ratio <= (1 - thr.one_sided_ratio_hi)):
        alerts.append({"type": "ONE_SIDED", "ratio": float(ratio), "flow": float(flow)})

    lt = time.localtime(ts)
    if thr.low_demand_hours[0] <= lt.tm_hour <= thr.low_demand_hours[1] and flow >= thr.low_demand_flow:
        alerts.append({"type": "LOW_DEMAND_CROWD", "hour": int(lt.tm_hour), "flow": float(flow)})

    return alerts, dbg
