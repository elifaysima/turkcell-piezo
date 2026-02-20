from __future__ import annotations

from dataclasses import dataclass, field
from collections import defaultdict, deque
from typing import Dict, List, Optional, Tuple
import numpy as np

from common import StepPacket


@dataclass
class ModuleHealthState:
    last_ts: int = 0
    totals: deque = field(default_factory=lambda: deque(maxlen=120))
    last_flag: Optional[str] = None


# key: (site_id, module_id)
HEALTH: Dict[Tuple[str, str], ModuleHealthState] = defaultdict(ModuleHealthState)


@dataclass(frozen=True)
class HealthThresholds:
    offline_s: int = 10
    stuck_zero_s: int = 30
    stuck_const_s: int = 30
    outlier_window: int = 30
    outlier_mad_k: float = 6.0


def update_health(pkt: StepPacket) -> None:
    st = HEALTH[(pkt.site_id, pkt.module_id)]
    st.last_ts = pkt.ts
    st.totals.append(int(pkt.steps_dir1 + pkt.steps_dir2))


def health_alerts_for_packet(pkt: StepPacket, thr: HealthThresholds = HealthThresholds()) -> List[dict]:
    update_health(pkt)
    return check_stuck(pkt.site_id, pkt.module_id, thr)


def check_offline(now_ts: int, thr: HealthThresholds) -> List[dict]:
    alerts: List[dict] = []
    for (site, mod), st in HEALTH.items():
        if st.last_ts and (now_ts - st.last_ts) >= thr.offline_s:
            alerts.append({"type": "SENSOR_OFFLINE", "site_id": site, "module_id": mod, "last_ts": st.last_ts})
    return alerts


def check_stuck(site_id: str, module_id: str, thr: HealthThresholds) -> List[dict]:
    st = HEALTH[(site_id, module_id)]
    alerts: List[dict] = []

    if len(st.totals) < max(thr.stuck_zero_s, thr.stuck_const_s):
        return alerts

    recent_zero = list(st.totals)[-thr.stuck_zero_s:]
    if all(x == 0 for x in recent_zero):
        alerts.append({"type": "STUCK_ZERO", "site_id": site_id, "module_id": module_id})
        return alerts

    recent_const = np.array(list(st.totals)[-thr.stuck_const_s:], dtype=float)
    if float(np.std(recent_const)) < 1e-6:
        alerts.append({"type": "STUCK_CONST", "site_id": site_id, "module_id": module_id, "value": float(recent_const[-1])})

    return alerts


def check_outliers(site_id: str, thr: HealthThresholds) -> List[dict]:
    """
    Site içindeki modüllerin medyan akışına göre uç modülleri yakalar.
    """
    modules = [(s, m) for (s, m) in HEALTH.keys() if s == site_id]
    if len(modules) < 3:
        return []

    vals = []
    mod_vals = []
    for (s, m) in modules:
        st = HEALTH[(s, m)]
        if len(st.totals) < thr.outlier_window:
            continue
        v = float(np.median(list(st.totals)[-thr.outlier_window:]))
        vals.append(v)
        mod_vals.append((m, v))

    if len(vals) < 3:
        return []

    med = float(np.median(vals))
    mad = float(np.median([abs(v - med) for v in vals]))
    mad = max(mad, 1e-6)

    alerts: List[dict] = []
    for m, v in mod_vals:
        score = abs(v - med) / mad
        if score >= thr.outlier_mad_k:
            alerts.append(
                {"type": "OUTLIER_MODULE", "site_id": site_id, "module_id": m, "median": med, "value": v, "score": float(score)}
            )
    return alerts
